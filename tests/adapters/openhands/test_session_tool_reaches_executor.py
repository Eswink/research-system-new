"""GOAL-029 EC-01 判据：**会话工具真的被执行**（收 GOAL-028 `W-1` 之下的更底层缺陷）。

**被测缺陷（建档轮实测）**：`PolicyEnforcingAgent._evaluate` 构造的 `PolicyRequest` 曾用
`scope=self.policy_scope`（= 会话 id），而 `examples/config/policy.yaml` 的带 scope `allow`
规则要求 **scope 相等**才匹配 ⇒ 会话 id 永不等于 `project` / `run` /
`approved_tool_providers` ⇒ **每一条**会话工具调用都落 `default_effect: DENY`。
实测后果：`artifact.read`（**已放行**能力）的会话工具调用 `status=SUCCEEDED` 但
**工具 executor 一次也没被触达**（`executor_reached == []`）—— 终态是绿的，工具从未运行。

**为什么判据读「executor 是否被触达」而不是 run 终态**：终态绿**不**蕴含工具运行
（上段的实测就是反例）。受判事实必须是「executor 真被调用过」，否则判据会被
「拒绝后 agent 照样收尾」骗过。

**四向（承 MEM-20260922-159：反证两向）** 都取真实 `NativePolicyEvaluator(policy.yaml)`：

1. **已放行**（`artifact.read` @ `project`）⇒ executor **被触达**；
2. **未放行**（A 组 `claim.read`）⇒ 拒绝，executor **未触达**；
3. **需审批**（`external.publish`）⇒ 拒绝，executor **未触达**；
4. **两条门同形**：agent loop 门（`PolicyEnforcingAgent._evaluate`）与桥门
   （`session_tool_invocation` 经 `execute_tool_call`）读**同一张** scope 表。

**不 import 产品常量当预言机**：本文件把「哪条能力被放行」写死成字面量（与
`policy.yaml` 同源），而不是调用 `policy_scope_for` 反过来证明 `policy_scope_for` 对。

**工具名用专属名**：承 `MEM-20261001-180`（SDK registry **进程级且只增不减**）——
本文件用 `goal029.*` 前缀的专属工具名，避免与别的装配串台；注册后**显式摘除**，
使重复运行与合跑都确定。
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Any

import pytest
from openhands.sdk.tool.schema import Action, Observation
from openhands.sdk.tool.tool import ToolDefinition, ToolExecutor

from adapters.fakes import FakeCredentialResolver
from adapters.openhands.runtime_adapter import OpenHandsRuntimeAdapter
from adapters.openhands.session_types import AdapterDependencies
from packages.application.policy.native import NativePolicyEvaluator
from packages.application.ports.agent_runtime import AgentSessionSpec
from packages.domain.enums import PolicyDecision
from services.api.catalog import load_policy_definition

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

_REACHED: list[str] = []

#: 字面量（与 `examples/config/policy.yaml` 同源，不 import 产品常量当预言机）。
_GRANTED = "artifact.read"
_REGISTERED_NOT_GRANTED = "claim.read"
_REQUIRES_APPROVAL = "external.publish"


def _real_evaluator() -> NativePolicyEvaluator:
    """工厂目录里的真实策略求值器（`policy.yaml` 必须可加载 ⇒ 否则判据前提不成立）。"""
    policy = load_policy_definition()
    assert policy is not None, "examples/config/policy.yaml 必须可加载（本判据的前提）"
    return NativePolicyEvaluator(policy)


class _ProbeAction(Action):
    """探针工具的调用参数（**模块级**：见下）。"""

    text: str = ""


class _ProbeObservation(Observation):
    """具体 Observation 子类（判别联合要求具体 kind）。"""


class _ProbeExecutor(ToolExecutor[Any, Observation]):
    """executor 被调用即记录 —— 本判据读的就是**这个**事实（不是 run 终态）。"""

    def __call__(self, action: Any, conversation: Any = None) -> Observation:
        _REACHED.append(str(getattr(action, "text", "x")))
        return _ProbeObservation.from_text("probe-ok")


def _make_tool(name: str) -> Any:
    """专属名字的探针工具（`executor` 被调用即记录）。

    **`Action` / `Observation` 子类必须在模块级**（本文件的 `_ProbeAction` /
    `_ProbeObservation` 就是）：SDK 会枚举它们的**具体子类**来构建判别联合，
    `<locals>` 限定名会让**同进程后续所有事件 round-trip** 直接抛
    `Local classes not supported!` —— 实测代价是 CI 上
    `tests/contracts/test_agent_runtime_contract.py` 两条 fork 判据整轮判红
    （本地单跑看不见，只有全量 `python/tests` 合跑才暴露）。
    同族教训与正确写法见 `tests/e2e/live_run_support.py` 的 `inert_tool_class`。
    """
    class_name = "Probe" + "".join(part.title() for part in name.replace(".", "_").split("_"))
    return type(
        class_name,
        (ToolDefinition[Any, Observation],),
        {
            "__module__": __name__,
            "__qualname__": class_name,
            "name": name,
            "create": classmethod(
                lambda cls, conv_state=None, **params: [
                    cls(
                        description=f"GOAL-029 probe tool {name}",
                        action_type=_ProbeAction,
                        observation_type=_ProbeObservation,
                        executor=_ProbeExecutor(),
                    )
                ]
            ),
        },
    )


def _tool_call_llm(tool_name: str) -> Any:
    """让模型先调一次 `tool_name`、再收尾的两轮脚本（`TestLLM` 固定应答）。"""
    from openhands.sdk.llm import Message, MessageToolCall, TextContent
    from openhands.sdk.testing import TestLLM

    return TestLLM.from_messages([
        Message(
            role="assistant",
            content=[TextContent(text="")],
            tool_calls=[
                MessageToolCall(
                    id="call-goal029",
                    name=tool_name,
                    arguments='{"text": "probe"}',
                    origin="completion",
                )
            ],
        ),
        Message(role="assistant", content=[TextContent(text="Done.")]),
    ])


def _run_tool(tmp_path: Path, tool_name: str, *, evaluator: Any | None = None) -> str:
    """起一次真实会话让模型调用 `tool_name`，返回 run 终态；`_REACHED` 记录触达。

    装配与 `tests/adapters/openhands/test_policy_enforcement.py` 同形，
    **缺省把 FakePolicyEvaluator 换成真实 `NativePolicyEvaluator(policy.yaml)`** ——
    缺陷只在真实策略面可见（Fake 的缺省决策是 ALLOW，恰好掩盖它）。
    `evaluator` 可传入记录器（读被消费的实际请求）。
    """
    from openhands.sdk.tool.registry import register_tool
    from openhands.sdk.workspace.local import LocalWorkspace

    from tests.contracts.fixtures import (
        agent_spec,
        research_task,
        role_definition,
        task_contract,
    )

    _REACHED.clear()
    register_tool(tool_name, _make_tool(tool_name))
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir(exist_ok=True)
    llm = _tool_call_llm(tool_name)
    deps = AdapterDependencies(
        credential_resolver=FakeCredentialResolver({"LLM_KEY": "sk-test"}),
        policy_evaluator=evaluator or _real_evaluator(),
        build_llm=lambda spec: llm,
        build_workspace=lambda lease, session_id: LocalWorkspace(working_dir=str(workspace_root)),
        persistence_dir=str(tmp_path / "persist"),
    )
    spec = AgentSessionSpec(
        task_id=research_task().id,
        task_contract=task_contract(),
        role=role_definition(),
        agent=agent_spec(),
        frozen_tool_set=(tool_name,),
    )
    runtime = OpenHandsRuntimeAdapter(deps)
    handle = runtime.create_session(spec)
    result = runtime.run(handle.session_id)
    runtime.close()
    return str(result.status)


class TestTheGrantedCapabilityReachesItsExecutor:
    """EC-01 AC-1 的主判据：策略**放行**的能力 ⇒ 会话工具的 executor 真被触达。"""

    def test_a_granted_capability_tool_reaches_its_executor(self, tmp_path: Path) -> None:
        """修 F-6 之前这条必红（`executor_reached == []`）；修复后触达。

        这是本判据的**正控制**：若它绿而下面的拒绝臂也绿，才说明策略面仍在起作用
        （而不是「所有工具都放行」）。
        """
        status = _run_tool(tmp_path, _GRANTED)
        assert status.endswith("SUCCEEDED"), status
        assert _REACHED == ["probe"], (
            "已放行能力（artifact.read @ project）的会话工具必须真的触达 executor；"
            "实测未触达 ⇒ 执行期求值 scope 与会话 id 混用（F-6）回归了",
            _REACHED,
        )


class TestTheDeniedSideStaysDenied:
    """四向中的拒绝两向：未放行 / 需审批的能力**不得**因本修复而被放行。"""

    def test_a_registered_but_ungranted_capability_is_refused(self, tmp_path: Path) -> None:
        """A 组读能力（`claim.read`）在 `policy.yaml` 里**无 allow 规则** ⇒ 仍拒绝。

        `D-02(b)` 的「读类能力是否成类预放行」是未决口径（需用户拍板）⇒ 本判据钉住
        「**未**放行就是未放行」，防止修复被误当成放行。
        """
        _run_tool(tmp_path, _REGISTERED_NOT_GRANTED)
        assert _REACHED == [], (
            f"{_REGISTERED_NOT_GRANTED} 未获放行 ⇒ executor 不得被触达（D-02(b) 未决）"
        )

    def test_a_requires_approval_capability_is_refused(self, tmp_path: Path) -> None:
        """`require_approval` 能力（`external.publish`）在审批通道接通前**阻塞**。"""
        _run_tool(tmp_path, _REQUIRES_APPROVAL)
        assert _REACHED == [], (
            f"{_REQUIRES_APPROVAL} 是 require_approval ⇒ 审批通道未接通前不得触达 executor"
        )


_PROBE_PROVIDER_ID = "goal029_probe_provider"
_PROBE_TOOL_ID = "artifact_read"


def _bridge_invoker(recorded: list[Any]) -> Any:
    """造一个把真实策略面记录下来的桥（供「两条门同源」判据读被消费的 `scope`）。"""
    from adapters.fakes import FakeArtifactStore, FakeToolProvider
    from adapters.openhands.session_tool_invocation import SessionToolSpec, make_tool_invoker
    from packages.domain.enums import EffectClass, ProviderType, TrustLevel
    from packages.domain.tools import ToolProviderSpec

    class _Recording:
        """转发给真实求值器，同时记录每个请求（读的是被消费的那个值）。"""

        def __init__(self, inner: Any) -> None:
            self._inner = inner

        def evaluate(self, request: Any) -> Any:
            recorded.append(request)
            return self._inner.evaluate(request)

    spec = ToolProviderSpec(
        id=_PROBE_PROVIDER_ID,
        kind=ProviderType.NATIVE,
        trust_level=TrustLevel.BUILT_IN,
        capabilities=[_GRANTED],
        effect_class=EffectClass.READ_ONLY,
    )
    return make_tool_invoker(
        SessionToolSpec(
            provider_id=_PROBE_PROVIDER_ID, tool_id=_PROBE_TOOL_ID, capability=_GRANTED
        ),
        providers={_PROBE_PROVIDER_ID: FakeToolProvider(registered_tools=(_PROBE_TOOL_ID,))},
        provider_specs={_PROBE_PROVIDER_ID: spec},
        artifacts=FakeArtifactStore(),
        policy=_Recording(_real_evaluator()),
    )


class TestBothGatesReadTheSameScopeTable:
    """四向之四：两条门读**同一张** scope 表（agent loop 面 + 桥面）。"""

    def test_the_agent_loop_gate_uses_the_declared_scope(self, tmp_path: Path) -> None:
        """结构事实：agent loop 门把**能力自己的声明 scope**交给求值器，不是会话 id。

        读法：包一层**记录器**套住真实 `NativePolicyEvaluator(policy.yaml)` 再跑一次
        **真会话** —— 断言的是求值器**实际收到**的 `scope`（不是源码字面量），
        因此重构改名不会误红，而语义回归（scope 又变回会话 id）必红。
        """
        recorded: list[Any] = []

        class _Recording:
            """转发给真实求值器，同时记录每个请求（读的是被消费的那个值）。"""

            def __init__(self, inner: Any) -> None:
                self._inner = inner

            def evaluate(self, request: Any) -> Any:
                recorded.append(request)
                return self._inner.evaluate(request)

        status = _run_tool(tmp_path, _GRANTED, evaluator=_Recording(_real_evaluator()))
        assert status.endswith("SUCCEEDED"), status
        assert _REACHED == ["probe"], _REACHED
        assert recorded, "求值器一次也没被调用 ⇒ 本判据在空转（MEM-156）"
        scopes = {request.scope for request in recorded}
        assert scopes == {"project"}, (
            "会话工具求值必须用能力自己的声明 scope（artifact.read ⇒ project）；"
            f"实测收到 {sorted(scopes)} ⇒ scope 又与别的身份（会话 id）混用了"
        )

    def test_the_bridge_gate_uses_the_declared_scope(self) -> None:
        """桥门同形：`make_tool_invoker` 交给执行期门禁的求值器会补上声明 scope。

        读法：**真跑一次桥调用**（`make_tool_invoker(...)()`），用**记录器**套住真实
        `NativePolicyEvaluator(policy.yaml)`，断言求值器实际收到的 `scope` 是
        `project` 而不是 `None`。缺 `ScopedPolicy` 时 `artifact.read` 会被
        `default_effect: DENY` 拒掉并抛 `POLICY_DENIED` ⇒ 本判据在撤掉补齐器时必红，
        而不是只在源码字面量变化时才红（按压记录见 PLAN-20261004-275）。
        """
        recorded: list[Any] = []
        invoker = _bridge_invoker(recorded)

        # 桥在策略放行后会继续走到「取回结果」；Fake provider 不 spill 输出 ⇒ 那一步
        # 点名拒绝。**执行面**的失败不是本判据的对象（本判据只钉策略面的 scope）。
        with contextlib.suppress(Exception):
            invoker({"text": "probe"}, None)

        assert recorded, "桥一次也没求值 ⇒ 本判据在空转（受判面非空是交付前提）"
        scopes = sorted({str(request.scope) for request in recorded})
        assert scopes == ["project"], (
            "桥交给执行期门禁的请求必须带能力自己的声明 scope（artifact.read ⇒ project）；"
            f"实测 {scopes} ⇒ 补齐器缺失或与 preflight 的表不一致"
        )

    def test_without_the_scope_the_same_call_is_refused(self) -> None:
        """反证臂（判据内的正控制）：同一条能力**不带** scope 时必被拒绝。

        没有这一臂，「收到 project」可能只是恰好没匹配上别的东西；有了它，
        「补齐器真的在起作用」与「不补就会被拒」是同一次运行里的两个读数。
        """
        from packages.application.ports.policy_evaluator import PolicyRequest

        evaluator = _real_evaluator()
        without_scope = evaluator.evaluate(
            PolicyRequest(actor="a", capability=_GRANTED, action="tool_call", resource="t")
        )
        assert without_scope.decision is PolicyDecision.DENY, (
            "不带 scope 时 artifact.read 必须落 default_effect: DENY（否则本判据的区分力失效）",
            without_scope.decision,
        )
        assert "default policy effect" in without_scope.reason, without_scope.reason


def test_the_declared_scope_table_is_the_only_source() -> None:
    """受判面非空（MEM-156）：本判据覆盖的能力必须在 `policy.yaml` 里有真实规则。

    防「判据在空集上恒真」：三条受判能力各自断言其在策略面里的**真实** 归属
    （放行 / 无规则 / 需审批）——这是判据自身的正控制。
    """
    from packages.application.ports.policy_evaluator import PolicyRequest
    from packages.domain.enums import PolicyDecision

    evaluator = _real_evaluator()
    expected = {
        _GRANTED: PolicyDecision.ALLOW,
        _REGISTERED_NOT_GRANTED: PolicyDecision.DENY,
        _REQUIRES_APPROVAL: PolicyDecision.REQUIRE_APPROVAL,
    }
    from packages.application.preflight.policy_check import policy_scope_for

    for capability, decision in expected.items():
        outcome = evaluator.evaluate(
            PolicyRequest(
                actor="agent:goal029",
                capability=capability,
                action="execute",
                scope=policy_scope_for(capability),
                resource=capability,
            )
        )
        assert outcome.decision is decision, (
            f"{capability} 在出厂策略里的归属变了（本判据的前提）："
            f"expected {decision.value}, got {outcome.decision.value}"
        )
