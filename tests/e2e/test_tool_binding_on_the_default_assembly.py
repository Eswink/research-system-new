"""GOAL-028 EC-01 判据：**provider→SDK 工具映射**（默认装配路径，非 `map_tools=True`）。

**被测对象**：产品那条「声明 → 编译 → 会话解析 → adapter 装配」链，以及**生产组合根**
（`services/api/runtime_support.py::build_agent_runtime` 的真实缺省）在**没有**测试侧
惰性替身（`register_inert_tools`）的情况下能不能把会话建起来。

**五件事逐条取证**：

1. **三面一致**：协议文档（YAML 原文）/ 加载面（`load_protocol`）/ 编译面（`compile_protocol`）
   对绑定的读法逐字一致（不拿产品常量当预言机）；
2. **缺声明逐字不变**：未声明绑定的既有协议，会话工具面仍**逐字等于**（冻结集 − run-chain
   排除）——本 EC 没有偷偷改默认路径；
3. **默认装配实跑**：声明了绑定 + 装配方提供实现 ⇒ run 到 `SUCCEEDED`（**不**注入
   `register_inert_tools`）；
4. **反证一（删绑定）**：改跑**成对的**反证协议（只少一条声明，其余逐字相同）⇒ 缺席的那个
   provider id 直落 SDK ⇒ **点名** `ToolDefinition '<provider id>' is not registered`，
   且 **mock 端点零请求**（失败在任何 LLM 调用之前）；
5. **反证二（绑到没有实现的工具名）**：同协议、同装配，只把**实现表**换成缺那条 ⇒
   **点名那个工具名**（与 provider id 可区分），同样零请求。

**与既有判据的关系**：`tests/e2e/test_ec03_real_runtime_offline_chain.py` 把「未映射 ⇒
点名拒绝」固定在 **demo 协议**（不声明绑定）上；本文件把「声明了就起得来」固定在**新协议**上。
两条合起来才是「声明作用域」的完整句——**既有文件一字未改**。
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient

from adapters.contracts.protocol_loaders import load_protocol
from adapters.openhands.session_tools import build_session_tools
from packages.application.protocol_compile import compile_protocol
from packages.application.run_orchestration.session_resolution import (
    flatten_tool_providers,
    run_chain_tool_ids,
    session_tool_bindings,
    session_tool_face,
)
from packages.domain.protocols import SessionToolBinding
from services.api.app import create_app
from services.api.catalog import load_catalog_snapshot, load_project_settings
from services.api.runtime_support import build_agent_runtime, resolve_runtime_selection
from tests.e2e.live_run_support import openhands_deps, start_run

# 复用既有离线 e2e 的 mock 端点与读面（同一套装配，避免两处各写一份）。
from tests.e2e.test_ec03_real_runtime_offline_chain import (
    _MockRelayHandler,
    _read_chain,
    mock_relay,
)

#: 本判据自带的**成对**协议（落 `examples/protocols/`；不改任何既有协议）：
#: 完整版声明两条绑定，反证版只少一条 —— 差别只有那一行。
_PROTOCOL = "tool_binding_research_v1.yaml"
_PARTIAL_PROTOCOL = "tool_binding_partial_v1.yaml"
_PROTOCOL_ID = "tool_binding_research_v1_0_0"
#: 判据里写死（不 import 产品常量当预言机）：绑定把 provider 绑到**能力名**。
_BINDINGS = {
    "m12_artifact": "artifact.read",
    "openhands_workspace": "workspace.read",
}
#: 既有协议（**不**声明绑定）⇒ 会话工具面逐字等于（冻结集 − run-chain 排除）。
#: `multi_role_research_v1.yaml` 在 GOAL-028 **EC-03** 里按授权**新增**了绑定（它的
#: review phase 要真的在默认装配下开会话）⇒ 它已从本清单移出，改由
#: `tests/e2e/test_multi_role_on_the_default_assembly.py` 断言（那条判据钉的是
#: 「声明之后就起得来」，与本文件钉的「没声明就逐字不变」互补）。
_UNDECLARED = (
    "console_demo_research_v1.yaml",
    "sort_analysis_v1.yaml",
)

__all__ = ["mock_relay"]


@pytest.fixture
def relay_requests() -> list[dict[str, Any]]:
    """每个用例拿到干净的 mock 端点请求账（零请求反证要读它）。"""
    _MockRelayHandler.requests = []
    return _MockRelayHandler.requests


def _compiled(protocol_name: str) -> Any:
    protocol = load_protocol(f"examples/protocols/{protocol_name}")
    result = compile_protocol(protocol, load_catalog_snapshot(), load_project_settings())
    assert result.plan is not None, result.findings
    return result.plan


class TestTheDeclarationIsReadTheSameWayOnThreeFaces:
    """AC-1：文档面 / 加载面 / 编译面三面对绑定读法一致。"""

    def test_the_document_itself_declares_the_bindings(self) -> None:
        raw = yaml.safe_load(Path(f"examples/protocols/{_PROTOCOL}").read_text(encoding="utf-8"))
        for phase in raw["phases"]:
            declared = {
                item["provider_id"]: item["tool_name"]
                for item in phase.get("session_tool_bindings", [])
            }
            assert declared == _BINDINGS, (phase["id"], declared)

    def test_the_loader_reads_them_verbatim(self) -> None:
        protocol = load_protocol(f"examples/protocols/{_PROTOCOL}")
        for phase in protocol.phases:
            assert {
                item.provider_id: item.tool_name for item in phase.session_tool_bindings
            } == _BINDINGS, phase.id

    def test_the_compiler_carries_them_verbatim(self) -> None:
        plan = _compiled(_PROTOCOL)
        for phase in plan.phases:
            assert {
                item.provider_id: item.tool_name for item in phase.session_tool_bindings
            } == _BINDINGS, phase.id

    def test_the_refutation_protocol_differs_only_in_the_declaration(self) -> None:
        """反证协议与完整协议**只差一条声明**（失败因此可归因）。"""
        full = _compiled(_PROTOCOL)
        partial = _compiled(_PARTIAL_PROTOCOL)
        assert [phase.id for phase in partial.phases] == [phase.id for phase in full.phases]
        for whole, less in zip(full.phases, partial.phases, strict=True):
            assert set(item.provider_id for item in whole.session_tool_bindings) - set(
                item.provider_id for item in less.session_tool_bindings
            ) == {"openhands_workspace"}

    def test_an_undeclared_protocol_yields_no_bindings(self) -> None:
        """缺声明 ⇒ 空：既有协议逐字不受影响（本 EC 没有偷偷改默认路径）。"""
        for name in _UNDECLARED:
            for phase in _compiled(name).phases:
                assert not phase.session_tool_bindings, (name, phase.id)


class TestTheBindingTranslationIsDeclaredScopeOnly:
    """AC-2：绑定的效果**只**作用在声明它的 phase 上，其余逐字不变。"""

    def test_the_declaring_phase_translates_provider_ids_to_tool_names(self) -> None:
        plan = _compiled(_PROTOCOL)
        face = session_tool_face(plan, "analysis")
        assert face == ("m12_artifact", "openhands_workspace"), face
        assert dict(session_tool_bindings(plan, "analysis")) == _BINDINGS
        # 翻译出的名字 = 能力名（策略求值看到的正是这个名字）。
        assert set(_BINDINGS.values()) == {"artifact.read", "workspace.read"}

    def test_a_non_declaring_phase_keeps_the_frozen_face(self) -> None:
        """没声明绑定的 phase：会话工具面逐字等于（冻结集 − run-chain 排除）。"""
        plan = _compiled(_PROTOCOL)
        for phase in plan.phases:
            if phase.session_tool_bindings:
                continue
            expected = tuple(
                name
                for name in flatten_tool_providers(plan)
                if name not in set(run_chain_tool_ids(plan, phase.id))
            )
            assert session_tool_face(plan, phase.id) == expected, phase.id

    def test_a_undeclared_protocol_face_equals_frozen_minus_run_chain(self) -> None:
        """既有协议（未声明绑定）两面逐字对齐：本 EC 对默认路径**零影响**。"""
        for name in _UNDECLARED:
            plan = _compiled(name)
            for phase in plan.phases:
                expected = tuple(
                    item
                    for item in flatten_tool_providers(plan)
                    if item not in set(run_chain_tool_ids(plan, phase.id))
                )
                assert session_tool_face(plan, phase.id) == expected, (name, phase.id)
                assert not session_tool_bindings(plan, phase.id), (name, phase.id)

    def test_a_binding_outside_the_face_is_named(self) -> None:
        """绑定越界（provider 不在本 phase 会话工具面内）⇒ **点名**拒绝。"""
        plan = _compiled("console_demo_research_v1.yaml")
        phase = plan.phases[0]
        tampered = replace(
            phase,
            session_tool_bindings=(SessionToolBinding("not_a_provider", "some.tool"),),
        )
        broken = replace(plan, phases=[tampered, *plan.phases[1:]])
        with pytest.raises(ValueError, match="not_a_provider"):
            session_tool_bindings(broken, phase.id)

    def test_one_provider_bound_to_two_names_is_named(self) -> None:
        """同一 provider 绑两个工具名 ⇒ **点名**拒绝（一次会话一个身份）。"""
        plan = _compiled(_PROTOCOL)
        phase = plan.phases[0]
        tampered = replace(
            phase,
            session_tool_bindings=(
                SessionToolBinding("m12_artifact", "artifact.read"),
                SessionToolBinding("m12_artifact", "artifact.write"),
            ),
        )
        broken = replace(plan, phases=[tampered, *plan.phases[1:]])
        with pytest.raises(ValueError, match="two tool names"):
            session_tool_bindings(broken, phase.id)


class TestTheDefaultAssemblyActuallyRuns:
    """AC-3/AC-4/AC-5：默认装配实跑 + 两向反证（各自点名、零请求）。"""

    def test_the_run_reaches_success_on_the_production_assembly(
        self, mock_relay: str, relay_requests: list[dict[str, Any]]
    ) -> None:
        deps = _production_deps(mock_relay, impls=tuple(_BINDINGS.values()))
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)

        assert not any("is not registered" in message for message in reads.failures), reads.failures
        assert reads.run["protocol_id"] == _PROTOCOL_ID, reads.run
        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        assert relay_requests, "会话必须真的建起来并驱动 mock 端点"

    def test_dropping_one_binding_fails_by_name_before_any_llm_call(
        self, mock_relay: str, relay_requests: list[dict[str, Any]]
    ) -> None:
        """反证一：跑反证协议（只少一条声明）⇒ provider id 直落 SDK ⇒ 点名 + 零 LLM 请求。

        **为什么先摘掉 registry 里的名字**：SDK 的 registry 是**进程级、只增不减**的
        （`register_tool` 无撤销入口），而别的判据（`test_ec03_real_runtime_offline_chain.py`
        的 `map_tools=True` 路径）会把同样这几个 provider id 注册成惰性替身 ⇒ 全量跑时
        名字**已经**在表里，本反证会「通过」而其实没测到东西（**假绿**）。所以这里显式
        摘掉它，让「未注册」成为**本用例确定的事实**，而不是用例顺序的函数。
        （同族教训见 `MEM-20261001-180-sdk-tool-registry-is-process-global`；
        摘除是**瞬态**的：任何需要它的装配会在会话装配时重新注册。）
        """
        _unregister("openhands_workspace")
        deps = _production_deps(mock_relay, impls=tuple(_BINDINGS.values()))
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PARTIAL_PROTOCOL)
            reads = _read_chain(client, run)

        assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
        assert any(
            "ToolDefinition 'openhands_workspace' is not registered" in message
            for message in reads.failures
        ), reads.failures
        assert relay_requests == [], "失败必须发生在任何 LLM 调用之前"

    def test_binding_to_an_unimplemented_tool_name_fails_by_that_name(
        self, mock_relay: str, relay_requests: list[dict[str, Any]]
    ) -> None:
        """反证二：声明指向**装配方没有实现**的工具名 ⇒ 点名**工具名**（与 provider id 可区分）。

        用**专属协议** `tool_binding_unwired_v1.yaml`（目标名 `workspace.read.unwired`
        不与任何别的装配重合）而不是把实现表换掉：SDK 的 registry 是**进程级、只增不减**的
        （`register_tool` 无撤销入口）⇒ 同一进程里先跑的用例注册过的名字对后跑的**仍然可解析**，
        换表断言会**依赖用例顺序**。专属名字让失败是确定的。
        """
        deps = _production_deps(mock_relay, impls=tuple(_BINDINGS.values()))
        with TestClient(create_app(deps)) as client:
            run = start_run(client, "tool_binding_unwired_v1.yaml")
            reads = _read_chain(client, run)

        assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
        assert any(
            "ToolDefinition 'workspace.read.unwired' is not registered" in message
            for message in reads.failures
        ), reads.failures
        assert relay_requests == [], "失败必须发生在任何 LLM 调用之前"


def _unregister(tool_name: str) -> None:
    """把某个名字从 SDK 的**进程级** registry 里摘掉（只服务反证的确定性）。

    registry 是只增不减的（`register_tool` 无撤销入口）⇒ 「未注册」这条事实会被同进程里
    别的用例抹掉。摘除只影响**本进程后续**按名解析：真正的装配会在会话装配时按声明重新
    注册它需要的名字，所以这不是「改产品行为」，而是**让判据的事实成立**。
    """
    from openhands.sdk.tool import registry

    registry._REG.pop(tool_name, None)  # noqa: SLF001 - 判据侧清理，非产品路径
    registry._USABILITY_REG.pop(tool_name, None)  # noqa: SLF001


def _production_deps(mock_relay_url: str, *, impls: tuple[str, ...]) -> Any:
    """生产装配（`map_tools=False`）+ 本判据提供的实现表（**不**用惰性替身后门）。

    `impls` 是**装配方实现**了哪些工具名；只有声明与实现**都**在场的名字才解析得出来，
    否则 SDK 按名点名（这正是两条反证各自的失败形态）。
    """
    deps = openhands_deps(mock_relay_url, map_tools=False)
    _attach_register(deps, impls)
    return deps


def _attach_register(deps: Any, impls: tuple[str, ...]) -> None:
    """把注册面接到 `build_agent_runtime`（生产组合根的**真实缺省调用形态**）。"""
    from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.assembly import policy_bindings
    from services.api.settings import ApiSettings

    invokers = {
        tool_name: (lambda arguments, conversation=None, _n=tool_name: f"{_n} ok")
        for tool_name in impls
    }
    settings = ApiSettings(
        agent_runtime="openhands",
        allow_localhost_endpoints=True,
        workspace_allow_host_shell=True,
    )
    policy = EndpointUrlPolicy(allow_localhost=True)
    runtime = build_agent_runtime(
        settings,
        credentials=deps.credentials,
        policy_evaluator=policy_bindings().get("policy_evaluator"),
        budget_ledger=deps.budget,
        register_session_tools=build_session_tools(invokers),
    )
    deps.runs = RunOrchestrationService(replace(deps.runs._deps, runtime=runtime))
    deps.runtime_selection = resolve_runtime_selection(settings)
    deps.endpoint_url_policy = policy
