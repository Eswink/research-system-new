"""GOAL-20261024-096 EC-01 的**协议级**判据：六相链在协议文档里成立。

本文件与 `test_run_chain_reads_cross_phase_material.py` / `test_direction_to_question_protocol.py`
分工（互不替代）：

- 那两份判**机制**与**前两相的声明**；
- 本份判**出厂协议 `direction_to_report_v1.yaml` 真的把六相按声明的形态写出来**：
  相集、依赖链、跨相引用、C-1（experiment/report 两相**无**跨相 `inputs`）、
  review 相的四条绑定，且 role/agent/能力/合约全部编译解析。

**C-2**：两份既有协议一份都不改 —— 它们各自的判据
（`test_direction_to_question_protocol.py` 钉死两相、`test_research_report_arc_offline.py`
钉死四相）仍然全绿就是「未改」的机械证据。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

from adapters.contracts.protocol_loaders import load_protocol
from packages.application.protocol_compile import compile_protocol
from services.api.catalog import load_catalog_snapshot, load_project_settings

_ROOT = Path(__file__).resolve().parents[2]
_PROTOCOL = "direction_to_report_v1.yaml"
_PROTOCOL_ID = "direction_to_report_v1_0_0"
_PHASES = ("question", "retrieval", "plan", "experiment", "review", "report")
_REVIEW_BINDINGS = (
    {"provider_id": "m12_artifact", "tool_name": "artifact.read"},
    {"provider_id": "openhands_workspace", "tool_name": "workspace.read"},
    {"provider_id": "ncbi_eutils", "tool_name": "literature.search"},
    {"provider_id": "europe_pmc", "tool_name": "literature.read"},
)


def _raw() -> dict[str, Any]:
    path = _ROOT / "examples" / "protocols" / _PROTOCOL
    loaded: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], loaded)


def _phases() -> dict[str, dict[str, Any]]:
    return {phase["id"]: phase for phase in _raw()["phases"]}


def _compiled() -> Any:
    protocol = load_protocol(f"examples/protocols/{_PROTOCOL}")
    result = compile_protocol(protocol, load_catalog_snapshot(), load_project_settings())
    assert result.plan is not None, result.findings
    return result.plan


def test_the_document_declares_six_phases_in_the_required_shape() -> None:
    """**文档自己**写了六相与各自的声明形态（不靠产品代码转述）。"""
    phases = _phases()
    assert set(phases) == set(_PHASES), sorted(phases)

    assert phases["question"].get("outputs") == ["research_question"]
    assert phases["question"].get("capability_execution") == "run_chain"
    assert phases["question"].get("task_contract") == "research_question_proposal"
    assert not phases["question"].get("inputs"), phases["question"].get("inputs")

    assert phases["retrieval"].get("depends_on") == ["question"]
    assert phases["retrieval"].get("inputs") == ["question:research_question"]
    assert phases["retrieval"].get("task_contract") == "research_question_retrieval"

    # 立题格的输入是**上游检索产物**（不再吃手写简报）——这是与
    # `research_report_chain_v1` 的 plan 相唯一的声明差。
    assert phases["plan"].get("depends_on") == ["retrieval"]
    assert phases["plan"].get("inputs") == ["retrieval:retrieval_report"]
    assert phases["plan"].get("task_contract") == "research_report_plan"
    assert phases["plan"].get("capability_execution") == "run_chain"

    assert phases["experiment"].get("depends_on") == ["plan"]
    assert phases["experiment"].get("task_contract") == "experiment_execution"

    assert phases["review"].get("depends_on") == ["experiment"]
    assert phases["review"].get("inputs") == ["plan:research_plan"]
    assert phases["review"].get("task_contract") == "multi_role_review"
    assert phases["review"].get("session_tool_bindings") == list(_REVIEW_BINDINGS)

    assert set(phases["report"].get("depends_on") or []) == {"plan", "experiment", "review"}
    assert phases["report"].get("task_contract") == "research_report_deliverable"


def test_the_two_executors_that_cannot_declare_cross_phase_inputs_do_not() -> None:
    """**C-1**：`experiment` 与 `report` 两相**不声明**跨相 `inputs`。

    这两相的执行体（沙箱实验 / 报告汇编器）不消费声明输入
    （`protocol_compile/cross_phase_inputs._executor_consumes_declared_inputs`）：
    声明了会被编译期点名拒绝；实验设计只能经装配面 `design_source="plan"`、
    报告第 1 节只能经 `report_facts` 的读取面 —— 这两条边在协议里**写不出来**，
    本判据钉住「协议没有假装写得出来」。
    """
    phases = _phases()
    for phase_id in ("experiment", "report"):
        assert not phases[phase_id].get("inputs"), (phase_id, phases[phase_id].get("inputs"))


def test_the_protocol_compiles_with_the_whole_chain_resolved() -> None:
    """编译零 ERROR：六相、依赖链、role/agent/能力/合约、跨相引用全解析。"""
    plan = _compiled()
    compiled = {phase.id: phase for phase in plan.phases}
    assert set(compiled) == set(_PHASES), sorted(compiled)
    # 依赖链逐相成立（编译期已校验产出方是上游；这里按声明再对一遍）。
    assert compiled["retrieval"].depends_on == ("question",)
    assert compiled["plan"].depends_on == ("retrieval",)
    assert compiled["experiment"].depends_on == ("plan",)
    assert compiled["review"].depends_on == ("experiment",)
    assert set(compiled["report"].depends_on) == {"plan", "experiment", "review"}
    # 跨相边三处，性质各归各的产出方（声明事实；`plan` 的产物标签过宽这件事
    # 与 GOAL-089 `W-4` 同源，登记在 GOAL 残余节，不在这里改断言掩盖）。
    by_phase = {
        phase.id: [(item[0], item[1], item[2].name) for item in phase.cross_phase_inputs]
        for phase in plan.phases
    }
    assert by_phase["retrieval"] == [("question", "research_question", "RETRIEVED")]
    assert by_phase["plan"] == [("retrieval", "retrieval_report", "RETRIEVED")]
    assert by_phase["review"] == [("plan", "research_plan", "RETRIEVED")]
    assert by_phase["experiment"] == [] and by_phase["report"] == []


def test_the_run_chain_phases_have_an_empty_session_face() -> None:
    """三个 run_chain 相的会话工具面为**空**（没有名字需要不存在的实现）。"""
    from adapters.openhands.tool_mapping import session_tool_ids
    from packages.application.run_orchestration.session_resolution import (
        flatten_tool_providers,
        run_chain_tool_ids,
    )

    plan = _compiled()
    frozen = flatten_tool_providers(plan)
    assert set(frozen) == {
        "m12_artifact",
        "openhands_workspace",
        "ncbi_eutils",
        "europe_pmc",
    }, frozen
    for phase_id in ("question", "retrieval", "plan"):
        assert session_tool_ids(frozen, run_chain_tool_ids(plan, phase_id)) == (), phase_id


def test_the_sibling_protocols_are_untouched() -> None:
    """**C-2** 的正面取证：两份既有协议的相集逐字不变（改了会立刻在这里红）。"""
    assert set(_sibling_phases("direction_to_question_v1.yaml")) == {"question", "retrieval"}
    assert set(_sibling_phases("research_report_chain_v1.yaml")) == {
        "plan",
        "experiment",
        "review",
        "report",
    }


def _sibling_phases(name: str) -> list[str]:
    raw: Any = yaml.safe_load((_ROOT / "examples" / "protocols" / name).read_text(encoding="utf-8"))
    return [phase["id"] for phase in raw["phases"]]
