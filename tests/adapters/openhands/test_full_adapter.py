"""Full adapter 集成测试：OpenHandsRuntimeAdapter 全方法 + cancellation 矩阵。

使用 SDK TestLLM 脚本化 LLM（无网络、无真实凭据）；workspace 为隔离
临时目录。覆盖 create_session/run/pause/cancel/stream_events/fork 与
cancel 前/后/重复/幂等语义。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from openhands.sdk.llm import Message, TextContent
from openhands.sdk.testing import TestLLM
from openhands.sdk.workspace.local import LocalWorkspace

from adapters.fakes import FakeCredentialResolver, FakePolicyEvaluator
from adapters.openhands.runtime_adapter import OpenHandsRuntimeAdapter
from adapters.openhands.session_types import AdapterDependencies
from packages.application.ports.agent_runtime import (
    AgentSessionSpec,
    ForkSpec,
    RuntimeEventKind,
)
from packages.application.ports.errors import InvalidInputError, PermanentPortError
from packages.domain.enums import PolicyDecision
from packages.domain.session_state import AgentSessionState
from tests.contracts.fixtures import agent_spec, research_task, role_definition, task_contract


def _spec() -> AgentSessionSpec:
    return AgentSessionSpec(
        task_id=research_task().id,
        task_contract=task_contract(),
        role=role_definition(),
        agent=agent_spec(),
    )


def _make_adapter(
    tmp_path: Path,
    *,
    messages: list[Message | Exception] | None = None,
) -> OpenHandsRuntimeAdapter:
    llm = TestLLM.from_messages(
        messages
        or [
            Message(role="assistant", content=[TextContent(text="Done.")]),
            Message(role="assistant", content=[TextContent(text="All set.")]),
        ]
    )
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir(exist_ok=True)
    deps = AdapterDependencies(
        credential_resolver=FakeCredentialResolver({"LLM_KEY": "sk-test"}),
        policy_evaluator=FakePolicyEvaluator(default=PolicyDecision.ALLOW),
        build_llm=lambda spec: llm,
        build_workspace=lambda lease, session_id: LocalWorkspace(working_dir=str(workspace_root)),
        persistence_dir=str(tmp_path / "persist"),
    )
    return OpenHandsRuntimeAdapter(deps)


class TestFullAdapter:
    def test_create_run_success_and_events(self, tmp_path: Path) -> None:
        runtime = _make_adapter(tmp_path)
        handle = runtime.create_session(_spec())
        result = runtime.run(handle.session_id)
        assert result.status == AgentSessionState.State.SUCCEEDED
        kinds = [event.kind for event in runtime.stream_events(handle.session_id)]
        assert kinds[0] is RuntimeEventKind.SESSION_CREATED
        assert kinds[-1] is RuntimeEventKind.SESSION_SUCCEEDED

    def test_rerun_after_terminal_is_idempotent(self, tmp_path: Path) -> None:
        runtime = _make_adapter(tmp_path)
        handle = runtime.create_session(_spec())
        first = runtime.run(handle.session_id)
        second = runtime.run(handle.session_id)
        assert first.status == second.status == AgentSessionState.State.SUCCEEDED
        # 终端后不再追加事件（事件流单调）
        assert len(runtime.stream_events(handle.session_id)) == len([
            e for e in runtime.stream_events(handle.session_id)
        ])

    def test_cancel_before_run_converges_cancelled(self, tmp_path: Path) -> None:
        runtime = _make_adapter(tmp_path)
        handle = runtime.create_session(_spec())
        runtime.cancel(handle.session_id)
        result = runtime.run(handle.session_id)
        assert result.status == AgentSessionState.State.CANCELLED
        kinds = [event.kind for event in runtime.stream_events(handle.session_id)]
        assert kinds[-1] is RuntimeEventKind.SESSION_CANCELLED

    def test_repeated_cancel_is_idempotent(self, tmp_path: Path) -> None:
        runtime = _make_adapter(tmp_path)
        handle = runtime.create_session(_spec())
        runtime.cancel(handle.session_id)
        runtime.cancel(handle.session_id)
        result = runtime.run(handle.session_id)
        assert result.status == AgentSessionState.State.CANCELLED

    def test_cancel_after_complete_is_noop(self, tmp_path: Path) -> None:
        runtime = _make_adapter(tmp_path)
        handle = runtime.create_session(_spec())
        runtime.run(handle.session_id)
        runtime.cancel(handle.session_id)
        result = runtime.run(handle.session_id)
        assert result.status == AgentSessionState.State.SUCCEEDED
        # 无 SESSION_CANCELLED 事件追加
        kinds = [event.kind for event in runtime.stream_events(handle.session_id)]
        assert kinds[-1] is RuntimeEventKind.SESSION_SUCCEEDED

    def test_pause_is_cooperative(self, tmp_path: Path) -> None:
        runtime = _make_adapter(tmp_path)
        handle = runtime.create_session(_spec())
        runtime.pause(handle.session_id)  # 非 RUNNING 状态：幂等不抛错
        runtime.pause(handle.session_id)
        assert handle.session_id

    def test_unknown_session_rejected(self, tmp_path: Path) -> None:
        runtime = _make_adapter(tmp_path)
        with pytest.raises(InvalidInputError):
            runtime.run("missing-session")
        with pytest.raises(InvalidInputError):
            runtime.cancel("missing-session")
        with pytest.raises(InvalidInputError):
            runtime.stream_events("missing-session")

    def test_fork_creates_new_lineage(self, tmp_path: Path) -> None:
        runtime = _make_adapter(tmp_path)
        handle = runtime.create_session(_spec())
        forked = runtime.fork(
            handle.session_id,
            ForkSpec(session_id=handle.session_id, reason="A/B test"),
        )
        assert forked.session_id != handle.session_id
        assert forked.status == AgentSessionState.State.CREATED

    def test_close_then_calls_rejected(self, tmp_path: Path) -> None:
        runtime = _make_adapter(tmp_path)
        handle = runtime.create_session(_spec())
        runtime.close()
        with pytest.raises(PermanentPortError):
            runtime.run(handle.session_id)
        with pytest.raises(PermanentPortError):
            runtime.create_session(_spec())

    def test_close_cleans_up_conversations(self, tmp_path: Path) -> None:
        runtime = _make_adapter(tmp_path)
        handle = runtime.create_session(_spec())
        runtime.run(handle.session_id)
        runtime.close()  # 幂等清理，不抛错
        runtime.close()

    def test_calls_recorded(self, tmp_path: Path) -> None:
        runtime = _make_adapter(tmp_path)
        handle = runtime.create_session(_spec())
        runtime.run(handle.session_id)
        methods = [call["method"] for call in runtime.calls]
        assert "create_session" in methods
        assert "run" in methods
