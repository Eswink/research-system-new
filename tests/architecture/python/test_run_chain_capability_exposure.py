"""GOAL-011 EC-01 同源判据：**谁执行能力**的声明在每个面一致，且不是静默丢弃。

链条（任何一环单独改、另几环不变，就是漂移）：

1. **协议声明**：`examples/protocols/*.yaml` 的 `capability_execution`——产品面的声明；
2. **加载面**：`load_protocol` 把声明读成 `ProtocolPhase.capability_execution`（缺省 session）；
3. **编译面**：`CompiledPhase.capability_execution` 原样透传；
4. **冻结面**：`flatten_tool_providers(plan)`（= `frozen_tool_set`）**不因声明而缩小**——
   这是「声明化排除」与「静默丢弃」的分界线：provider 仍被冻结、仍会被
   `require_frozen_tool_set` 拦住越权执行；
5. **会话面**：`session_tool_ids(frozen, run_chain)` 才是被拿掉的那一份。

判据**不**复用被测辅助函数当预言机：协议面直接读 YAML 原文，加载/编译/派生三面走
产品路径，两条相互独立（YAML 与产品路径）必须逐字对上。

成对反证（R-5，记录在 RECHECK）：把 `real_research_task_v1.yaml` 里的
`capability_execution` 行删掉 ⇒ 第 2/3/5 条即红（会话工具列表重新等于冻结集）；
把 `session_tool_ids` 的越界分支改成静默过滤 ⇒ 最后一条即红。
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
import yaml

from adapters.contracts.protocol_loaders import load_protocol
from adapters.openhands.tool_mapping import session_tool_ids
from packages.application.protocol_compile import compile_protocol
from packages.application.run_orchestration.session_resolution import (
    flatten_tool_providers,
    run_chain_tool_ids,
)
from packages.domain.protocols import (
    CapabilityExecution,
    CompiledRunPlan,
    ToolRequirement,
)
from services.api.catalog import load_catalog_snapshot, load_project_settings

_ROOT = Path(__file__).resolve().parents[3]
_PROTOCOLS = _ROOT / "examples" / "protocols"

#: 声明「由运行链执行」的协议 → 它的哪个 phase 声明了、以及该 phase 的能力。
#: 字面量写在判据里（不 import 产品常量当预言机）。
_RUN_CHAIN = {
    "real_retrieval_research_v1.yaml": (
        "analysis",
        {"artifact.read", "literature.search", "literature.read"},
    ),
}
#: 未声明该字段的协议 ⇒ 会话工具列表必须**逐字等于**冻结集（既有语义）。
#: `real_research_task_v1` 在这里还有第二重身份：它是**默认装配下真的会跑**的那条真实
#: 协议，本判据因此同时钉住「改动没有波及既有的那条」。
_UNDECLARED = (
    "real_research_task_v1.yaml",
    "console_demo_research_v1.yaml",
    "m12_reference_research_v1.yaml",
)


def _raw_phases(name: str) -> dict[str, dict[str, Any]]:
    raw = yaml.safe_load((_PROTOCOLS / name).read_text(encoding="utf-8"))
    return {phase["id"]: phase for phase in raw["phases"]}


def _compiled(name: str) -> CompiledRunPlan:
    protocol = load_protocol(f"examples/protocols/{name}")
    result = compile_protocol(protocol, load_catalog_snapshot(), load_project_settings())
    assert result.plan is not None, result.findings
    return result.plan


def test_declared_protocol_says_run_chain_in_the_document_itself() -> None:
    """第 1 面：**文档自己**写了 `capability_execution: run_chain`（不靠产品代码转述）。"""
    for name, (phase_id, capabilities) in _RUN_CHAIN.items():
        phase = _raw_phases(name)[phase_id]
        assert phase.get("capability_execution") == "run_chain", (name, phase_id, phase)
        assert set(phase.get("required_capabilities", [])) == capabilities, (name, phase_id)


def test_loader_and_compiler_carry_the_declaration() -> None:
    """第 2/3 面：加载器读成域枚举、编译器原样透传（缺省仍是 session）。"""
    for name, (phase_id, _) in _RUN_CHAIN.items():
        protocol = load_protocol(f"examples/protocols/{name}")
        loaded = {phase.id: phase for phase in protocol.phases}
        assert loaded[phase_id].capability_execution is CapabilityExecution.RUN_CHAIN
        plan = _compiled(name)
        compiled = {phase.id: phase for phase in plan.phases}
        assert compiled[phase_id].capability_execution is CapabilityExecution.RUN_CHAIN

    for name in _UNDECLARED:
        protocol = load_protocol(f"examples/protocols/{name}")
        assert all(
            phase.capability_execution is CapabilityExecution.SESSION for phase in protocol.phases
        ), name


def test_declaration_does_not_shrink_the_frozen_tool_set() -> None:
    """第 4 面：冻结集**不**因声明而缩小——这是「声明化排除 ⇔ 静默丢弃」的分界。"""
    for name, (phase_id, _) in _RUN_CHAIN.items():
        plan = _compiled(name)
        frozen = flatten_tool_providers(plan)
        assert frozen, f"{name} 的冻结集为空 ⇒ 本判据空转"
        run_chain = run_chain_tool_ids(plan, phase_id)
        assert run_chain, f"{name} 的 {phase_id} 没有解析出 run-chain provider"
        assert set(run_chain) <= set(frozen), (frozen, run_chain)
        # 该 phase 的能力仍逐条落在 tool_requirements 里（preflight/策略面一字不减）
        declared = {
            (item.phase_id, item.capability)
            for item in plan.tool_requirements
            if item.phase_id == phase_id
        }
        assert declared, f"{name} 的 {phase_id} 在 tool_requirements 里没有任何能力"


def test_session_tools_exclude_exactly_the_run_chain_providers() -> None:
    """第 5 面：被拿掉的只有会话工具列表，且**只**拿掉声明过的那部分。"""
    for name, (phase_id, _) in _RUN_CHAIN.items():
        plan = _compiled(name)
        frozen = flatten_tool_providers(plan)
        session = session_tool_ids(frozen, run_chain_tool_ids(plan, phase_id))
        assert session == (), (name, frozen, session)

    for name in _UNDECLARED:
        plan = _compiled(name)
        frozen = flatten_tool_providers(plan)
        for phase in plan.phases:
            assert run_chain_tool_ids(plan, phase.id) == (), (name, phase.id)
            assert session_tool_ids(frozen, run_chain_tool_ids(plan, phase.id)) == frozen, (
                name,
                phase.id,
                frozen,
            )


def test_run_chain_tool_ids_are_scoped_to_their_phase() -> None:
    """声明是 **phase 级**的：别的 phase 不受影响（判据不许被一个全局开关骗过）。"""
    from tests.application import protocol_fixtures as fixtures

    plan, _ = fixtures.compiled()
    phase = plan.phases[0]
    requirement = ToolRequirement(
        phase_id=phase.id, capability="fixture-capability", provider_ids=("fixture-tools",)
    )
    run_chain_plan = replace(
        plan,
        phases=[replace(phase, capability_execution=CapabilityExecution.RUN_CHAIN)],
        tool_requirements=[requirement],
    )
    assert run_chain_tool_ids(run_chain_plan, phase.id) == ("fixture-tools",)
    assert run_chain_tool_ids(run_chain_plan, "no-such-phase") == ()
    assert session_tool_ids(("fixture-tools",), ("fixture-tools",)) == ()
    assert session_tool_ids(("fixture-tools",)) == ("fixture-tools",)
    assert session_tool_ids(("a", "b"), ("b",)) == ("a",)


def test_excluding_a_provider_outside_the_frozen_set_is_named() -> None:
    """越界的排除名单必须**点名拒绝**，不得静默过滤（fail-closed）。"""
    with pytest.raises(ValueError, match="intruder-provider"):
        session_tool_ids(("fixture-tools",), ("intruder-provider",))
