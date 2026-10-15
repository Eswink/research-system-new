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


def _make_adapter_with_think_call(tmp_path: Path, *, decision: PolicyDecision) -> Any:
    """一个**会在 loop 里调 `think`** 的真实 adapter（本组判据的公共夹具）。

    `think` 的调用经 `TestLLM` 注入 ⇒ 走真实 agent loop（`PolicyEnforcingAgent`
    的执行点），而不是直达通道 —— 后者由另一条判据钉住（豁免不扩散）。
    """
    from openhands.sdk.llm import Message, MessageToolCall, TextContent
    from openhands.sdk.workspace.local import LocalWorkspace

    from adapters.openhands.session_types import AdapterDependencies

    llm = TestLLM.from_messages([
        Message(
            role="assistant",
            content=[TextContent(text="")],
            tool_calls=[
                MessageToolCall(
                    id="call-think-1",
                    name="think",
                    arguments='{"thought": "let me consider the plan"}',
                    origin="completion",
                )
            ],
        ),
        Message(role="assistant", content=[TextContent(text="Done.")]),
    ])
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir(exist_ok=True)
    deps = AdapterDependencies(
        credential_resolver=FakeCredentialResolver({"LLM_KEY": "sk-test"}),
        policy_evaluator=FakePolicyEvaluator(default=decision),
        build_llm=lambda spec: llm,
        build_workspace=lambda lease, session_id: LocalWorkspace(working_dir=str(workspace_root)),
        persistence_dir=str(tmp_path / "persist"),
    )
    return OpenHandsRuntimeAdapter(deps)


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


class TestLoopControlVerbsAreNotCapabilities:
    """GOAL-20261015-080 EC-04：SDK 的**循环控制**动词不走能力策略（实测缺陷的反证）。

    **实测缺陷**：真实 run 里 `think` 与 `finish` 双双落 `default_effect: DENY` ⇒
    模型无法思考、无法收尾（自陈「even `think` is being denied」）⇒ 会话永远产不出答复。
    它们**不是能力**（SDK 逐字：these are *required* for the agent to work；且
    `readOnlyHint=True` / `destructiveHint=False` / `openWorldHint=False`）。

    **射程**：本组只判「这两个名字被豁免」**与**「豁免面恰是这两个」——
    其余动词仍走能力策略（由 `TestAgentLoopPolicyGate` 的三条 + 本组第 3 条共同钉住）。
    """

    def test_the_exempt_set_is_exactly_the_loop_control_verbs(self) -> None:
        """**逐字**钉住豁免面（写成两个名字的字面量，不 import 产品常量当预言机）。"""
        from adapters.openhands.policy_enforcing_agent import LOOP_CONTROL_VERBS

        assert set(LOOP_CONTROL_VERBS) == {"think", "finish"}, sorted(LOOP_CONTROL_VERBS)

    def test_a_think_call_in_the_agent_loop_is_not_denied(self, tmp_path: Path) -> None:
        """**行为读数**（判据本源）：模型在 loop 里调 `think` ⇒ **不被拒**。

        **实测缺陷**：真实 run 里模型的 `think` 与 `finish` 双双被拒（自陈
        「even `think` is being denied」）⇒ 模型**无法思考、无法收尾**。
        本判据用真实的 agent loop（`TestLLM` 发出 think 工具调用）复现同一路径 ——
        读的是「有没有 `policy denied` 的 AgentErrorEvent」，不是源码文本。
        """
        runtime = _make_adapter_with_think_call(tmp_path, decision=PolicyDecision.DENY)
        handle = runtime.create_session(_spec())
        result = runtime.run(handle.session_id)
        events = runtime.stream_events(handle.session_id)
        denied = [
            item.message
            for item in events
            if item.payload.get("error") and "policy denied" in (item.message or "")
        ]
        assert result.status == AgentSessionState.State.SUCCEEDED
        assert denied == [], f"think 在 agent loop 里被拒了：{denied}"
        runtime.close()

    def test_a_loop_control_verb_is_exempt_only_on_the_agent_loop_path(
        self, tmp_path: Path
    ) -> None:
        """反证：豁免**不扩散到 R-03 直达通道**（`execute_tool_gated` 照旧全门禁）。

        理由：直达通道的调用方是**产品代码**，不是模型的循环控制 ⇒ 给它开口子等于
        在既有的「先裁决后执行」门上挖一个洞。
        """
        from openhands.sdk.tool.builtins.finish import FinishAction

        runtime = _make_adapter(tmp_path, default_decision=PolicyDecision.DENY)
        handle = runtime.create_session(_spec())
        result = runtime.run(handle.session_id)
        assert result.status == AgentSessionState.State.SUCCEEDED
        with pytest.raises(Exception) as excinfo:
            runtime.execute_tool_gated(handle.session_id, "finish", FinishAction(message="done"))
        assert "policy denied" in str(excinfo.value).lower()
        runtime.close()

    def test_an_ordinary_unlisted_tool_is_still_denied(self, tmp_path: Path) -> None:
        """反证：豁免**不扩散** —— 普通工具在 DENY 装配下照旧被拒、executor 未触达。"""
        runtime = _make_adapter(tmp_path, default_decision=PolicyDecision.DENY)
        handle = runtime.create_session(_spec())
        with pytest.raises(Exception) as excinfo:
            runtime.execute_tool_gated(
                handle.session_id, "policy_echo", _PolicyEchoAction(text="x")
            )
        assert "policy denied" in str(excinfo.value).lower()
        assert _EXECUTIONS == []
        runtime.close()


class TestDirectExecutionGate:
    def test_the_adapter_exposes_exactly_one_tool_execution_entry(self) -> None:
        """EC-05：adapter 的公开面里执行入口只有门控那一个（结构事实的运行时读数）。"""
        public = {
            name
            for name in dir(OpenHandsRuntimeAdapter)
            if not name.startswith("_") and "execute" in name
        }
        assert public == {"execute_tool_gated"}, public

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
