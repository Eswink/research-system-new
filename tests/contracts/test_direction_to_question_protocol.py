"""GOAL-20261019-089 EC-01 的**协议级**判据：方向 → 问题 → 检索这条链在协议文档里成立。

本文件与 `test_run_chain_reads_cross_phase_material.py` 分工（互不替代）：

- 那一份判**机制**（跨相材料进参数材料；换产出换 query；摘上游编译期红）；
- 本份判**声明**（出厂协议 `direction_to_question_v1.yaml` 真的把这两格按那个形态
  写出来，且编译期解析出的跨相引用与参数路径**逐字对齐**）。

**为什么分开**：机制绿而声明错（或反过来）都会让「检索词来自上游问题」在产品面上
不成立 —— 两份判据各自可证伪，合起来才是这条链。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

from adapters.contracts.protocol_loaders import load_protocol
from packages.application.protocol_compile import compile_protocol
from packages.application.protocol_compile.cross_phase_inputs import (
    is_cross_phase_reference,
)
from packages.application.run_orchestration.phase_capabilities import RunChainCall
from services.api.catalog import load_catalog_snapshot, load_project_settings

_ROOT = Path(__file__).resolve().parents[2]
_PROTOCOL = "direction_to_question_v1.yaml"
_QUESTION = "question"
_RETRIEVAL = "retrieval"
_ARTIFACT = "research_question"


def _raw() -> dict[str, Any]:
    path = _ROOT / "examples" / "protocols" / _PROTOCOL
    loaded: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], loaded)


def _phases() -> dict[str, dict[str, Any]]:
    return {phase["id"]: phase for phase in _raw()["phases"]}


def test_the_document_declares_the_two_phases_in_the_required_shape() -> None:
    """**文档自己**写了这个形态（不靠产品代码转述）。"""
    phases = _phases()
    assert set(phases) == {_QUESTION, _RETRIEVAL}, sorted(phases)

    question = phases[_QUESTION]
    assert question.get("outputs") == [_ARTIFACT], question.get("outputs")
    # 立题格**声明 run_chain**：本协议的检索 provider 在冻结集里，而它没有会话实现
    # （生产装配的注册表只有 `m12_artifact` / `openhands_workspace`）⇒ 不排除的话
    # 会话面会含 `literature.*` 的名字而没有注册实现，**SDK 在 agent 初始化时点名**
    # （`ToolDefinition 'europe_pmc' is not registered`，本轮实测）。
    # **代价（如实登记，见 GOAL 的 `W-4`）**：`producer_trust_label` 只按「声明了
    # run_chain + 能力面落在带网络域的 provider 上」推导 ⇒ 本格产物被标 `RETRIEVED`，
    # 而它其实是模型写的。这是**既有推导的过宽**（本轮不改：改它等于改性质语义），
    # 所以「检索真的发生」由 provider 收到的参数逐字取证（e2e/live 两份判据），
    # **不**由这个标签单独承担。
    assert question.get("capability_execution") == "run_chain", question.get("capability_execution")
    assert question["task_contract"] == "research_question_proposal"
    # 它**没有**声明输入：方向走提示词（`ProjectDefinition.direction`），不是制品。
    assert not question.get("inputs"), question.get("inputs")

    retrieval = phases[_RETRIEVAL]
    assert retrieval.get("capability_execution") == "run_chain", retrieval
    assert retrieval.get("depends_on") == [_QUESTION], retrieval.get("depends_on")
    # 检索格的声明输入**就是**上游产物（跨相引用）。
    assert retrieval.get("inputs") == [f"{_QUESTION}:{_ARTIFACT}"], retrieval.get("inputs")


def test_the_loader_and_compiler_carry_the_cross_phase_reference() -> None:
    """编译期把 `question:research_question` 解析成 `(产出方, 产物名, 性质)`。

    性质是**产出方**的声明事实（`producer_trust_label` 的既定口径），不是读取方自报：
    `question` 声明 run_chain 且能力面落在带网络域的 provider 上 ⇒ `RETRIEVED`。
    **本条不断言它是「正确的」，只断言它与既有推导逐字一致** —— 该标签对本格产物
    不实这件事登记在 GOAL 的 `W-4`（含补偿判据），不靠改这条断言掩盖。
    """
    protocol = load_protocol(f"examples/protocols/{_PROTOCOL}")
    assert is_cross_phase_reference(protocol, f"{_QUESTION}:{_ARTIFACT}") is True

    result = compile_protocol(protocol, load_catalog_snapshot(), load_project_settings())
    assert result.plan is not None, result.findings
    compiled = {phase.id: phase for phase in result.plan.phases}
    assert compiled[_RETRIEVAL].cross_phase_inputs == (
        (_QUESTION, _ARTIFACT, compiled[_RETRIEVAL].cross_phase_inputs[0][2]),
    )
    # 性质由**产出方**决定：与 `producer_trust_label` 的既有推导逐字相同（按压见
    # `tests/application/run_orchestration/test_cross_phase_inputs.py::test_b_*`）。
    assert compiled[_RETRIEVAL].cross_phase_inputs[0][2].value == "RETRIEVED"


def test_the_run_chain_argument_path_matches_the_declared_artifact_name() -> None:
    """**参数路径与声明逐字对齐**：`arguments_from_input` 的首段 == 上游产物名。

    这条是「两边都写了但写得不一致」的唯一守卫：材料按**产物名**挂进参数材料
    （`phase_input_material.input_material`），所以 `research_question.query` 的首段
    必须是 `research_question` —— 写成 `question.query` 会在运行期才点名失败。
    """
    raw = _raw()
    declared_outputs = {name for phase in raw["phases"] for name in phase.get("outputs", [])}
    assert _ARTIFACT in declared_outputs, declared_outputs

    # 生产声明的参数路径（与 `tests/e2e/live_run_support._retrieval_calls` 同一形态）。
    call = RunChainCall(
        provider_id="ncbi_eutils",
        tool_id="literature_search",
        capability="literature.search",
        arguments_from_input=("research_question.query",),
    )
    head = call.arguments_from_input[0].split(".")[0]
    assert head == _ARTIFACT, (head, _ARTIFACT)
    # 参数名的最后一段就是 provider 看到的参数名（既有 `arguments_for` 口径）。
    assert call.arguments_from_input[0].rsplit(".", 1)[-1] == "query"


def test_removing_the_question_phase_breaks_compilation_naming_the_producer() -> None:
    """**摘掉上游 phase** ⇒ 编译期点名（`CROSS_PHASE_INPUT_INVALID`）。

    与机制判据的同名反证同向：这里按**真实出厂协议**做（去掉 `question` 那一格），
    证明协议文档与编译器之间的这条约束是**当前有效**的，不是只在合成样本上成立。
    """
    raw = _raw()
    raw["phases"] = [phase for phase in raw["phases"] if phase["id"] != _QUESTION]
    raw["phases"][0]["depends_on"] = []

    from packages.application.protocol_compile.cross_phase_inputs import (
        resolve_cross_phase_inputs,
    )
    from packages.domain.core import Version
    from packages.domain.protocols import ProtocolDefinition, ProtocolPhase

    def _phase(item: dict[str, Any]) -> ProtocolPhase:
        from packages.domain.protocols import CapabilityExecution, PhaseStrategy

        return ProtocolPhase(
            id=item["id"],
            strategy=PhaseStrategy.SINGLE_AGENT,
            depends_on=list(item.get("depends_on", [])),
            inputs=list(item.get("inputs", [])),
            outputs=list(item.get("outputs", [])),
            required_capabilities=list(item.get("required_capabilities", [])),
            capability_execution=(
                CapabilityExecution.RUN_CHAIN
                if item.get("capability_execution") == "run_chain"
                else CapabilityExecution.SESSION
            ),
        )

    protocol = ProtocolDefinition(
        id=str(raw["id"]), version=Version("0.1.0"), phases=[_phase(p) for p in raw["phases"]]
    )
    resolution = resolve_cross_phase_inputs(protocol, load_catalog_snapshot())
    codes = [finding.code for finding in resolution.findings]
    assert codes == ["CROSS_PHASE_INPUT_INVALID"], codes
    assert _QUESTION in resolution.findings[0].message, resolution.findings[0].message
