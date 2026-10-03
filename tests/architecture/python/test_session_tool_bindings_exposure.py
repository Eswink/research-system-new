"""GOAL-028 EC-01 同源判据：**会话工具绑定**在每个面一致，且不是静默丢弃。

链条（任何一环单独改、另几环不变，就是漂移）：

1. **协议声明**：`examples/protocols/*.yaml` 的 `session_tool_bindings`——产品面的声明；
2. **加载面**：`load_protocol` 把它读成 `ProtocolPhase.session_tool_bindings`（缺省空）；
3. **编译面**：`CompiledPhase.session_tool_bindings` 原样透传；
4. **冻结面**：`flatten_tool_providers(plan)`（= `frozen_tool_set`）**不因绑定而变**——
   这是「声明化翻译」与「偷偷换工具面」的分界线：provider 仍被冻结、仍会被
   `require_frozen_tool_set` 拦住越权执行；
5. **会话面**：`session_tool_face` 与 adapter 的 `session_tool_ids` 是**同一次减法**的两处
   实现（application 不能 import adapter，所以只能各写一份）⇒ 本判据逐字对齐两者，
   任何一边改了语义都会在这里红。

判据**不**复用被测辅助函数当预言机：协议面直接读 YAML 原文，加载 / 编译 / 派生走产品路径；
adapter 侧另行调用（它是被对齐的另一面，不是预言机）。

成对反证（记录在本 PLAN 的按压条目里）：把 `bind_session_tools` 的翻译架空 ⇒
`test_tool_binding_on_the_default_assembly.py` 的三条主判据即红（实测 `session_builder`
恢复后 `sha256` 逐字节一致）；删掉绑定声明行 ⇒ 第 2/3 面即红。
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
import yaml

from adapters.contracts.protocol_loaders import load_protocol
from adapters.openhands.tool_mapping import bind_session_tools, session_tool_ids
from packages.application.protocol_compile import compile_protocol
from packages.application.run_orchestration.session_resolution import (
    flatten_tool_providers,
    run_chain_tool_ids,
    session_tool_bindings,
    session_tool_face,
)
from packages.domain.protocols import SessionToolBinding
from services.api.catalog import load_catalog_snapshot, load_project_settings

_ROOT = Path(__file__).resolve().parents[3]
_PROTOCOLS = _ROOT / "examples" / "protocols"

#: 声明了绑定的协议 → 它的哪个 phase 声明了绑定（**字面量**写在判据里，不 import
#: 产品常量当预言机）。`multi_role_research_v1.yaml` 在 GOAL-028 **EC-03** 里按授权新增了
#: 绑定（review phase 四条）⇒ 它从本文件的「未声明」清单移到这里，期望值见
#: `_EXPECTED_DECLARED`。
_BOUND = {
    "tool_binding_research_v1.yaml": "analysis",
    "multi_role_research_v1.yaml": "review",
}
#: 未声明该字段的协议 ⇒ 绑定为空、会话工具面逐字等于（冻结集 − run-chain 排除）。
_UNDECLARED = (
    "real_research_task_v1.yaml",
    "console_demo_research_v1.yaml",
    "sort_analysis_v1.yaml",
)


def _raw_phases(name: str) -> dict[str, dict[str, Any]]:
    raw = yaml.safe_load((_PROTOCOLS / name).read_text(encoding="utf-8"))
    return {phase["id"]: phase for phase in raw["phases"]}


def _compiled(name: str) -> Any:
    protocol = load_protocol(f"examples/protocols/{name}")
    result = compile_protocol(protocol, load_catalog_snapshot(), load_project_settings())
    assert result.plan is not None, result.findings
    return result.plan


#: 每个「声明了绑定的」协议的**期望声明**（逐字写死在判据里 ⇒ 文档改一个字这里就红）。
_EXPECTED_DECLARED: dict[str, list[dict[str, str]]] = {
    # EC-01 的判据自带协议：两件 NATIVE provider。
    "tool_binding_research_v1.yaml": [
        {"provider_id": "m12_artifact", "tool_name": "artifact.read"},
        {"provider_id": "openhands_workspace", "tool_name": "workspace.read"},
    ],
    # EC-03 的真实协议：review phase 四条（run-chain 排除是 per-phase 的 ⇒
    # europe_pmc 在这一相位仍在会话工具面内，必须绑）。
    "multi_role_research_v1.yaml": [
        {"provider_id": "m12_artifact", "tool_name": "artifact.read"},
        {"provider_id": "openhands_workspace", "tool_name": "workspace.read"},
        {"provider_id": "ncbi_eutils", "tool_name": "literature.search"},
        {"provider_id": "europe_pmc", "tool_name": "literature.read"},
    ],
}


def test_the_document_itself_declares_the_bindings() -> None:
    """第 1 面：**文档自己**写了绑定（不靠产品代码转述）。"""
    for name, phase_id in _BOUND.items():
        declared = _raw_phases(name)[phase_id]["session_tool_bindings"]
        assert declared == _EXPECTED_DECLARED[name], (name, declared)


def test_the_loader_and_the_compiler_agree_with_the_document() -> None:
    """第 2/3 面：加载与编译都原样读到声明。"""
    for name, phase_id in _BOUND.items():
        protocol = load_protocol(f"examples/protocols/{name}")
        loaded = {
            item.provider_id: item.tool_name
            for item in next(p for p in protocol.phases if p.id == phase_id).session_tool_bindings
        }
        compiled = {
            item.provider_id: item.tool_name
            for item in next(
                p for p in _compiled(name).phases if p.id == phase_id
            ).session_tool_bindings
        }
        declared = {
            item["provider_id"]: item["tool_name"]
            for item in _raw_phases(name)[phase_id]["session_tool_bindings"]
        }
        assert loaded == declared, name
        assert compiled == declared, name


def test_the_frozen_set_does_not_shrink_because_of_bindings() -> None:
    """第 4 面：绑定**不**改冻结集（它只翻译会话工具名）。"""
    for name in (*_BOUND, *_UNDECLARED):
        plan = _compiled(name)
        frozen = flatten_tool_providers(plan)
        for phase in plan.phases:
            assert set(session_tool_face(plan, phase.id)) <= set(frozen), (name, phase.id)


def test_the_session_face_matches_the_adapter_subtraction_exactly() -> None:
    """第 5 面：application 的会话工具面 == adapter 的 `session_tool_ids`（逐字）。"""
    for name in (*_BOUND, *_UNDECLARED):
        plan = _compiled(name)
        frozen = flatten_tool_providers(plan)
        for phase in plan.phases:
            adapter_face = session_tool_ids(frozen, run_chain_tool_ids(plan, phase.id))
            assert session_tool_face(plan, phase.id) == adapter_face, (name, phase.id)


def test_undeclared_protocols_have_no_bindings_and_an_untouched_face() -> None:
    """未声明 ⇒ 绑定为空、会话面逐字等于（冻结集 − run-chain 排除）：既有语义不变。"""
    for name in _UNDECLARED:
        plan = _compiled(name)
        for phase in plan.phases:
            assert not phase.session_tool_bindings, (name, phase.id)
            assert session_tool_bindings(plan, phase.id) == (), (name, phase.id)
            expected = session_tool_ids(
                flatten_tool_providers(plan), run_chain_tool_ids(plan, phase.id)
            )
            assert session_tool_face(plan, phase.id) == expected, (name, phase.id)


class TestTheBindingTranslationKeepsPositionAndScope:
    """`bind_session_tools` 的三条语义（缺声明不变 / 位置保持 / 越界点名）。"""

    def test_no_bindings_returns_the_input_verbatim(self) -> None:
        face = ("openhands_workspace", "m12_artifact", "ncbi_eutils")
        assert bind_session_tools(face, ()) == face

    def test_a_declared_name_is_replaced_in_place(self) -> None:
        face = ("openhands_workspace", "m12_artifact")
        bound = bind_session_tools(face, (("m12_artifact", "artifact.read"),))
        assert bound == ("openhands_workspace", "artifact.read")
        assert len(bound) == len(face), "绑定不增减会话工具数"
        assert bound[0] == face[0], "未绑定的名字逐字保留"

    def test_a_binding_outside_the_face_is_named(self) -> None:
        with pytest.raises(ValueError, match="not_a_provider"):
            bind_session_tools(("m12_artifact",), (("not_a_provider", "some.tool"),))

    def test_the_application_point_rejects_a_binding_outside_the_face(self) -> None:
        plan = _compiled("tool_binding_research_v1.yaml")
        phase = plan.phases[0]
        tampered = replace(
            phase, session_tool_bindings=(SessionToolBinding("not_a_provider", "x"),)
        )
        with pytest.raises(ValueError, match="not_a_provider"):
            session_tool_bindings(replace(plan, phases=[tampered, *plan.phases[1:]]), phase.id)
