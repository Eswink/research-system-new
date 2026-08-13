"""fork override 测试：ForkSpec.model_override / tool_set_override 必须生效。

M6 复审 F-4 回归：此前 fork() 忽略 ForkSpec 全部 override 字段（SDK fork
支持 agent= 重建）。model_override 需要 AdapterDependencies.build_llm_for_fork；
tool_set_override 重建工具集。
"""

from __future__ import annotations

from pathlib import Path

from openhands.sdk.llm import Message, TextContent
from openhands.sdk.testing import TestLLM
from openhands.sdk.workspace.local import LocalWorkspace

from adapters.fakes import FakeCredentialResolver, FakePolicyEvaluator
from adapters.openhands.runtime_adapter import OpenHandsRuntimeAdapter
from adapters.openhands.session_types import AdapterDependencies
from packages.application.ports.agent_runtime import AgentSessionSpec, ForkSpec
from packages.domain.enums import PolicyDecision
from packages.domain.session_state import AgentSessionState
from tests.contracts.fixtures import agent_spec, research_task, role_definition, task_contract


def _spec() -> AgentSessionSpec:
    return AgentSessionSpec(
        task_id=research_task().id,
        task_contract=task_contract(),
        role=role_definition(),
        agent=agent_spec(),
        frozen_tool_set=(),
    )


def _make_adapter(
    tmp_path: Path,
    *,
    fork_llm_calls: list[str | None],
) -> OpenHandsRuntimeAdapter:
    llm = TestLLM.from_messages([
        Message(role="assistant", content=[TextContent(text="Done.")]),
    ])
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir(exist_ok=True)

    def build_fork_llm(spec: AgentSessionSpec, model_override: str | None) -> TestLLM:
        fork_llm_calls.append(model_override)
        return TestLLM.from_messages([
            Message(role="assistant", content=[TextContent(text="Forked.")]),
        ])

    deps = AdapterDependencies(
        credential_resolver=FakeCredentialResolver({"LLM_KEY": "sk-test"}),
        policy_evaluator=FakePolicyEvaluator(default=PolicyDecision.ALLOW),
        build_llm=lambda spec: llm,
        build_workspace=lambda lease, session_id: LocalWorkspace(working_dir=str(workspace_root)),
        build_llm_for_fork=build_fork_llm,
        persistence_dir=str(tmp_path / "persist"),
    )
    return OpenHandsRuntimeAdapter(deps)


class TestForkOverrides:
    def test_fork_without_override_uses_sdk_deepcopy(self, tmp_path: Path) -> None:
        calls: list[str | None] = []
        runtime = _make_adapter(tmp_path, fork_llm_calls=calls)
        handle = runtime.create_session(_spec())
        forked = runtime.fork(
            handle.session_id, ForkSpec(session_id=handle.session_id, reason="copy")
        )
        assert forked.session_id != handle.session_id
        assert forked.status == AgentSessionState.State.CREATED
        assert calls == []  # 无 override 不重建 LLM
        runtime.close()

    def test_fork_model_override_rebuilds_llm(self, tmp_path: Path) -> None:
        calls: list[str | None] = []
        runtime = _make_adapter(tmp_path, fork_llm_calls=calls)
        handle = runtime.create_session(_spec())
        forked = runtime.fork(
            handle.session_id,
            ForkSpec(
                session_id=handle.session_id,
                reason="A/B model",
                model_override="openai/gpt-alt",
            ),
        )
        assert forked.session_id != handle.session_id
        assert calls == ["openai/gpt-alt"]  # 新 LLM 被构建
        runtime.close()

    def test_fork_without_build_llm_for_fork_rejected(self, tmp_path: Path) -> None:
        llm = TestLLM.from_messages([
            Message(role="assistant", content=[TextContent(text="Done.")]),
        ])
        workspace_root = tmp_path / "ws"
        workspace_root.mkdir(exist_ok=True)
        deps = AdapterDependencies(
            credential_resolver=FakeCredentialResolver({"LLM_KEY": "sk-test"}),
            policy_evaluator=FakePolicyEvaluator(default=PolicyDecision.ALLOW),
            build_llm=lambda spec: llm,
            build_workspace=lambda lease, session_id: LocalWorkspace(
                working_dir=str(workspace_root)
            ),
            persistence_dir=str(tmp_path / "persist"),
        )
        runtime = OpenHandsRuntimeAdapter(deps)
        handle = runtime.create_session(_spec())
        try:
            runtime.fork(
                handle.session_id,
                ForkSpec(
                    session_id=handle.session_id,
                    reason="A/B model",
                    model_override="openai/gpt-alt",
                ),
            )
        except Exception as exc:
            assert "build_llm_for_fork" in str(exc)
        else:  # pragma: no cover - 必须拒绝
            raise AssertionError("fork model_override must require build_llm_for_fork")
        runtime.close()
