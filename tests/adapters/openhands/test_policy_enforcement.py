"""Policy 门禁全链路测试：真实 adapter 的工具执行必须经过 Research OS Policy。

M6 复审 F-1 回归：SDK agent loop 内工具执行（PolicyEnforcingAgent 执行点）
与 execute_tool 直通面（PolicyWrappedToolExecutor 门禁）都必须被
PolicyEvaluator 裁决；DENY/REQUIRE_APPROVAL 不触达工具 executor。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from openhands.sdk.llm import Message, MessageToolCall, TextContent
from openhands.sdk.testing import TestLLM
from openhands.sdk.tool.registry import register_tool
from openhands.sdk.tool.schema import Action, Observation
from openhands.sdk.tool.tool import ToolDefinition, ToolExecutor
from openhands.sdk.workspace.local import LocalWorkspace

from adapters.fakes import FakeCredentialResolver, FakePolicyEvaluator
from adapters.openhands.runtime_adapter import OpenHandsRuntimeAdapter
from adapters.openhands.session_types import AdapterDependencies
from packages.application.ports.agent_runtime import (
    AgentSessionSpec,
    RuntimeEventKind,
)
from packages.domain.enums import PolicyDecision
from packages.domain.session_state import AgentSessionState
from tests.contracts.fixtures import agent_spec, research_task, role_definition, task_contract

_EXECUTIONS: list[str] = []


class _PolicyEchoAction(Action):
    text: str = ""


class _PolicyEchoObservation(Observation):
    """具体 Observation 子类（判别联合要求具体 kind）。"""


class _PolicyEchoExecutor(ToolExecutor[Any, Observation]):
    def __call__(self, action: Any, conversation: Any = None) -> Observation:
        _EXECUTIONS.append(str(getattr(action, "text", "echo")))
        return _PolicyEchoObservation.from_text("echo-ok")


class PolicyEchoTool(ToolDefinition[Any, Observation]):
    @classmethod
    def create(cls, conv_state: Any = None, **params: Any) -> list["PolicyEchoTool"]:
        tool = cls(
            description="Echo input back",
            action_type=_PolicyEchoAction,
            observation_type=None,
            executor=_PolicyEchoExecutor(),
        )
        object.__setattr__(tool, "name", "policy_echo")
        return [tool]


def _tool_call_message() -> Message:
    return Message(
        role="assistant",
        content=[TextContent(text="")],
        tool_calls=[
            MessageToolCall(
                id="call-policy-1",
                name="policy_echo",
                arguments='{"text": "hi"}',
                origin="completion",
            )
        ],
    )


def _make_adapter(
    tmp_path: Path,
    *,
    default_decision: PolicyDecision,
) -> OpenHandsRuntimeAdapter:
    llm = TestLLM.from_messages([
        _tool_call_message(),
        Message(role="assistant", content=[TextContent(text="Done.")]),
    ])
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir(exist_ok=True)
    deps = AdapterDependencies(
        credential_resolver=FakeCredentialResolver({"LLM_KEY": "sk-test"}),
        policy_evaluator=FakePolicyEvaluator(default=default_decision),
        build_llm=lambda spec: llm,
        build_workspace=lambda lease, session_id: LocalWorkspace(working_dir=str(workspace_root)),
        persistence_dir=str(tmp_path / "persist"),
    )
    return OpenHandsRuntimeAdapter(deps)


def _spec() -> AgentSessionSpec:
    return AgentSessionSpec(
        task_id=research_task().id,
        task_contract=task_contract(),
        role=role_definition(),
        agent=agent_spec(),
        frozen_tool_set=("policy_echo",),
    )


@pytest.fixture(autouse=True)
def _register_policy_echo() -> None:
    register_tool(PolicyEchoTool.name, PolicyEchoTool)
    _EXECUTIONS.clear()


class TestAgentLoopPolicyGate:
    def test_deny_blocks_tool_execution_in_agent_loop(self, tmp_path: Path) -> None:
        runtime = _make_adapter(tmp_path, default_decision=PolicyDecision.DENY)
        handle = runtime.create_session(_spec())
        result = runtime.run(handle.session_id)
        assert result.status == AgentSessionState.State.SUCCEEDED
        assert _EXECUTIONS == []  # 工具 executor 未触达
        kinds = [event.kind for event in runtime.stream_events(handle.session_id)]
        assert kinds[-1] is RuntimeEventKind.SESSION_SUCCEEDED
        runtime.close()

    def test_require_approval_emits_event_and_blocks(self, tmp_path: Path) -> None:
        runtime = _make_adapter(tmp_path, default_decision=PolicyDecision.REQUIRE_APPROVAL)
        handle = runtime.create_session(_spec())
        result = runtime.run(handle.session_id)
        assert result.status == AgentSessionState.State.SUCCEEDED
        assert _EXECUTIONS == []
        kinds = [event.kind for event in runtime.stream_events(handle.session_id)]
        assert RuntimeEventKind.APPROVAL_REQUESTED in kinds
        runtime.close()

    def test_allow_executes_tool(self, tmp_path: Path) -> None:
        runtime = _make_adapter(tmp_path, default_decision=PolicyDecision.ALLOW)
        handle = runtime.create_session(_spec())
        result = runtime.run(handle.session_id)
        assert result.status == AgentSessionState.State.SUCCEEDED
        assert _EXECUTIONS == ["hi"]
        runtime.close()


class TestDirectExecutionGate:
    def test_gated_direct_execution_denied_before_sdk(self, tmp_path: Path) -> None:
        runtime = _make_adapter(tmp_path, default_decision=PolicyDecision.DENY)
        handle = runtime.create_session(_spec())
        with pytest.raises(Exception) as excinfo:
            runtime.execute_tool_gated(
                handle.session_id, "policy_echo", _PolicyEchoAction(text="x")
            )
        assert "policy denied" in str(excinfo.value).lower()
        assert _EXECUTIONS == []  # SDK execute_tool 未触达
        runtime.close()

    def test_gated_direct_execution_allowed(self, tmp_path: Path) -> None:
        runtime = _make_adapter(tmp_path, default_decision=PolicyDecision.ALLOW)
        handle = runtime.create_session(_spec())
        observation = runtime.execute_tool_gated(
            handle.session_id, "policy_echo", _PolicyEchoAction(text="direct")
        )
        assert observation is not None
        assert _EXECUTIONS == ["direct"]
        runtime.close()
