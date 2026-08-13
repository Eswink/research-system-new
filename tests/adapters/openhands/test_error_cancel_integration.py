"""错误路径与取消的 adapter 级集成测试（Fault Injection 落地）。

M6 复审 F-5/F-9 回归：
- 错误 run（LLM 异常）→ FAILED 终态，SESSION_FAILED 事件不重复，SDK
  异常类型不越过边界；
- secret 不进入事件/错误/结果；
- run 进行中 cancel（真实并发，非 mock）→ CANCELLED。
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

import pytest
from openhands.sdk.llm import Message, MessageToolCall, TextContent
from openhands.sdk.llm.exceptions import LLMContextWindowExceedError
from openhands.sdk.testing import TestLLM
from openhands.sdk.tool.registry import register_tool
from openhands.sdk.tool.schema import Action, Observation
from openhands.sdk.tool.tool import ToolDefinition, ToolExecutor
from openhands.sdk.workspace.local import LocalWorkspace

from adapters.fakes import FakeCredentialResolver, FakePolicyEvaluator
from adapters.openhands.runtime_adapter import OpenHandsRuntimeAdapter
from adapters.openhands.session_types import AdapterDependencies
from packages.application.ports.agent_runtime import AgentSessionSpec, RuntimeEventKind
from packages.application.ports.errors import PortError, TransientPortError
from packages.domain.enums import FailureCategory, PolicyDecision
from packages.domain.session_state import AgentSessionState
from tests.contracts.fixtures import agent_spec, research_task, role_definition, task_contract


class _SlowAction(Action):
    text: str = ""


class _SlowObservation(Observation):
    """具体 Observation 子类（判别联合要求具体 kind）。"""


class _SlowExecutor(ToolExecutor[Any, Observation]):
    def __call__(self, action: Any, conversation: Any = None) -> Observation:
        time.sleep(2.0)  # 让 run 保持运行以便并发 cancel
        return _SlowObservation.from_text("slow-ok")


class SlowPolicyEchoTool(ToolDefinition[Any, Observation]):
    @classmethod
    def create(cls, conv_state: Any = None, **params: Any) -> list["SlowPolicyEchoTool"]:
        tool = cls(
            description="Slow echo tool for cancellation tests",
            action_type=_SlowAction,
            observation_type=None,
            executor=_SlowExecutor(),
        )
        object.__setattr__(tool, "name", "slow_policy_echo")
        return [tool]


register_tool(SlowPolicyEchoTool.name, SlowPolicyEchoTool)


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
    llm: TestLLM,
) -> OpenHandsRuntimeAdapter:
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir(exist_ok=True)
    deps = AdapterDependencies(
        credential_resolver=FakeCredentialResolver({"LLM_KEY": "sk-test"}),
        policy_evaluator=FakePolicyEvaluator(default=PolicyDecision.ALLOW),
        build_llm=lambda spec: llm,
        build_workspace=lambda lease, session_id: LocalWorkspace(working_dir=str(workspace_root)),
        persistence_dir=str(tmp_path / "persist"),
    )
    return OpenHandsRuntimeAdapter(deps)


class TestErrorIntegration:
    def test_llm_error_run_fails_with_single_failed_event(self, tmp_path: Path) -> None:
        llm = TestLLM.from_messages([
            LLMContextWindowExceedError("context window exceeded"),
        ])
        runtime = _make_adapter(tmp_path, llm=llm)
        handle = runtime.create_session(_spec())
        with pytest.raises(PortError):
            runtime.run(handle.session_id)
        kinds = [event.kind for event in runtime.stream_events(handle.session_id)]
        # SESSION_FAILED 至多一次（事件映射与 _finish 不重复追加）
        assert kinds.count(RuntimeEventKind.SESSION_FAILED) == 1
        assert kinds[0] is RuntimeEventKind.SESSION_CREATED
        runtime.close()

    def test_sdk_exception_never_crosses_boundary(self, tmp_path: Path) -> None:
        llm = TestLLM.from_messages([
            LLMContextWindowExceedError("context window exceeded"),
        ])
        runtime = _make_adapter(tmp_path, llm=llm)
        handle = runtime.create_session(_spec())
        with pytest.raises(PortError) as excinfo:
            runtime.run(handle.session_id)
        # 边界检查：Public 层只见 Research OS normalized PortError
        assert isinstance(excinfo.value, PortError)
        assert not isinstance(excinfo.value, LLMContextWindowExceedError)
        assert not isinstance(excinfo.value, RuntimeError)
        runtime.close()

    def test_timeout_error_maps_transient_relay(self, tmp_path: Path) -> None:
        from openhands.sdk.llm.exceptions import LLMTimeoutError

        llm = TestLLM.from_messages([LLMTimeoutError("timed out")])
        runtime = _make_adapter(tmp_path, llm=llm)
        handle = runtime.create_session(_spec())
        with pytest.raises(TransientPortError) as excinfo:
            runtime.run(handle.session_id)
        assert excinfo.value.failure_category is FailureCategory.MODEL_RELAY_UNAVAILABLE
        runtime.close()

    def test_secret_not_in_events_or_error(self, tmp_path: Path) -> None:
        llm = TestLLM.from_messages([
            LLMContextWindowExceedError("boom sk-super-secret-777"),
        ])
        runtime = _make_adapter(tmp_path, llm=llm)
        handle = runtime.create_session(_spec())
        with pytest.raises(PortError) as excinfo:
            runtime.run(handle.session_id)
        for event in runtime.stream_events(handle.session_id):
            assert "sk-super-secret-777" not in str(event)
            assert "sk-super-secret-777" not in event.message
        assert "sk-super-secret-777" not in str(excinfo.value)
        runtime.close()


class TestCancelRunning:
    def test_cancel_during_run_converges_cancelled(self, tmp_path: Path) -> None:
        """run 进行中 cancel：真实并发路径（SDK interrupt fallback pause）。"""
        llm = TestLLM.from_messages([
            Message(
                role="assistant",
                content=[TextContent(text="")],
                tool_calls=[
                    MessageToolCall(
                        id="call-slow-1",
                        name="slow_policy_echo",
                        arguments='{"text": "sleep"}',
                        origin="completion",
                    )
                ],
            ),
            Message(role="assistant", content=[TextContent(text="Done.")]),
        ])
        runtime = _make_adapter(tmp_path, llm=llm)
        spec = AgentSessionSpec(
            task_id=research_task().id,
            task_contract=task_contract(),
            role=role_definition(),
            agent=agent_spec(),
            frozen_tool_set=("slow_policy_echo",),
        )
        handle = runtime.create_session(spec)
        outcomes: list[str] = []

        def _run_in_thread() -> None:
            result = runtime.run(handle.session_id)
            outcomes.append(result.status)

        thread = threading.Thread(target=_run_in_thread, daemon=True)
        thread.start()
        time.sleep(1.2)  # 让 run 进入工具执行（slow_policy_echo sleep 2s）
        runtime.cancel(handle.session_id)
        thread.join(timeout=20)
        assert outcomes == [AgentSessionState.State.CANCELLED]
        kinds = [event.kind for event in runtime.stream_events(handle.session_id)]
        assert RuntimeEventKind.SESSION_SUCCEEDED not in kinds
        assert kinds[-1] is RuntimeEventKind.SESSION_CANCELLED
        runtime.close()

    def test_cancel_running_then_cleanup(self, tmp_path: Path) -> None:
        """cancel 后 close 清理不抛错（资源释放路径）。"""
        llm = TestLLM.from_messages([
            Message(
                role="assistant",
                content=[TextContent(text="")],
                tool_calls=[
                    MessageToolCall(
                        id="call-slow-2",
                        name="slow_policy_echo",
                        arguments='{"text": "sleep"}',
                        origin="completion",
                    )
                ],
            ),
            Message(role="assistant", content=[TextContent(text="Done.")]),
        ])
        runtime = _make_adapter(tmp_path, llm=llm)
        spec = AgentSessionSpec(
            task_id=research_task().id,
            task_contract=task_contract(),
            role=role_definition(),
            agent=agent_spec(),
            frozen_tool_set=("slow_policy_echo",),
        )
        handle = runtime.create_session(spec)
        outcomes: list[str] = []

        def _run_in_thread() -> None:
            outcomes.append(runtime.run(handle.session_id).status)

        thread = threading.Thread(target=_run_in_thread, daemon=True)
        thread.start()
        time.sleep(1.2)
        runtime.cancel(handle.session_id)
        thread.join(timeout=20)
        runtime.close()  # cancel 后 close 幂等清理
        runtime.close()
        assert outcomes == [AgentSessionState.State.CANCELLED]
