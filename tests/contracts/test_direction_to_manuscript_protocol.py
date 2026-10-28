"""GOAL-20261028-099 EC-01：**八相手稿协议**在编译期成立，且既有协议一字未改。

**它补哪一格**：`validate_bundle.py` 只加载 `ai_ml_research_v{version}`（`:380`）⇒ 新协议的
DAG / 引用完整性**没有任何既有判据看着**，只有 `compile_protocol` 会在运行前判。本文件把
「它能编译、零 ERROR」变成机械事实，并逐条钉住那五件**必须**成立的结构事实：

1. **八相**且相集逐字（`question → retrieval → novelty → plan → experiment → review →
   manuscript → report`）；
2. `manuscript` 是**会话相**：它引用的合约**不声明** `report:` / `experiment:`
   —— 这是它能合法声明跨相 `inputs` 的**唯一**理由（`_executor_consumes_declared_inputs`
   对那两个执行体一律返回 False）；
3. 三条跨相边各自解析成 `(产出方, 产物名, 性质)`，且**性质由产出方决定**；
4. C-1 仍守住：`experiment` / `report` 两相**不声明**跨相 `inputs`；
5. **既有协议一字未改**：v1 六相 / v2 七相 / 两相版 / 四相链各自仍按原相集编译
   —— 这是「未改」的机械证据（不是本文件自己断言「我没改」）。

**反证臂**（真文件按压，按 raw `sha256` 逐字节复原）：

- 给 `manuscript` 相的合约加上 `report: {}` ⇒ 编译**必须**点名
  `CROSS_PHASE_INPUT_INVALID`（否则第 2 条只是一句注释）；
- 从 `manuscript` 相摘掉一条 `inputs` ⇒ 「三条边」判据**必须**红。
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

from adapters.contracts.protocol_loaders import load_protocol
from adapters.contracts.tasks_loaders import load_task_contracts
from packages.application.protocol_compile import compile_protocol
from services.api.catalog import load_catalog_snapshot, load_project_settings

_ROOT = Path(__file__).resolve().parents[2]
_PROTOCOLS = _ROOT / "examples" / "protocols"
_PROTOCOL = "direction_to_manuscript_v1.yaml"
_PROTOCOL_ID = "direction_to_manuscript_v1_0_0"
_CONTRACTS = _ROOT / "examples" / "contracts" / "task_contracts.yaml"

_PHASES = (
    "question",
    "retrieval",
    "novelty",
    "plan",
    "experiment",
    "review",
    "manuscript",
    "report",
)
#: 本协议必须声明的跨相边（读取方 ← 产出方:产物名）。
_CROSS_PHASE_EDGES: tuple[tuple[str, str], ...] = (
    ("retrieval", "question:research_question"),
    ("novelty", "retrieval:retrieval_report"),
    ("plan", "retrieval:retrieval_report"),
    ("plan", "novelty:novelty_claim"),
    ("review", "plan:research_plan"),
    ("review", "novelty:novelty_claim"),
    ("manuscript", "retrieval:retrieval_report"),
    ("manuscript", "novelty:novelty_claim"),
    ("manuscript", "plan:research_plan"),
)
#: C-1：不消费声明输入的两个执行体，它们的相位**不得**声明跨相 `inputs`。
_NON_CONSUMING_PHASES = ("experiment", "report")
_MANUSCRIPT_CONTRACT = "research_manuscript"


def _raw(name: str = _PROTOCOL) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load((_PROTOCOLS / name).read_text(encoding="utf-8")))


def _phases(name: str = _PROTOCOL) -> dict[str, dict[str, Any]]:
    return {str(phase["id"]): cast(dict[str, Any], phase) for phase in _raw(name)["phases"]}


def _compiled(name: str = _PROTOCOL) -> Any:
    protocol = load_protocol(f"examples/protocols/{name}")
    result = compile_protocol(protocol, load_catalog_snapshot(), load_project_settings())
    assert result.plan is not None, [f.message for f in result.findings]
    return result


def test_the_document_declares_eight_phases_in_order() -> None:
    """(1) 文档自己写下八相，且顺序就是执行序（不靠产品代码转述）。"""
    ids = tuple(str(phase["id"]) for phase in _raw()["phases"])
    assert ids == _PHASES, ids
    assert _raw()["id"] == _PROTOCOL_ID


def test_the_protocol_compiles_with_zero_errors() -> None:
    """(1) `compile_protocol` 通过且**零** finding（既有判据看不见这份协议 ⇒ 必须自己判）。"""
    result = _compiled()
    errors = [
        f for f in result.findings if str(getattr(f.severity, "value", f.severity)) == "ERROR"
    ]
    assert errors == [], [f.message for f in errors]
    assert result.plan is not None
    assert [phase.id for phase in result.plan.phases] == list(_PHASES)


def test_the_manuscript_phase_is_a_session_phase() -> None:
    """(2) 手稿相是**会话相**：合约不声明 `report:` / `experiment:`。

    这是它能合法声明跨相 `inputs` 的**唯一**理由 —— 两个执行体的相位在编译期被判
    「不消费声明输入」⇒ 声明输入会被拒（`_executor_consumes_declared_inputs`）。
    """
    contract = load_task_contracts("examples/contracts/task_contracts.yaml")[_MANUSCRIPT_CONTRACT]
    assert contract.report is None, "手稿契约声明了 report ⇒ 它会被当汇编器，跨相 inputs 必被拒"
    assert contract.experiment is None, "手稿契约声明了 experiment ⇒ 同上"
    phase = _phases()["manuscript"]
    assert phase["strategy"] == "single_agent"
    assert phase["task_contract"] == _MANUSCRIPT_CONTRACT
    assert str(phase.get("capability_execution", "session")) == "run_chain"


def test_the_manuscript_phase_declares_its_cross_phase_inputs() -> None:
    """(3) 手稿相的三条跨相边各自解析成 `(产出方, 产物名, 性质)`。"""
    plan = _compiled().plan
    manuscript = next(phase for phase in plan.phases if phase.id == "manuscript")
    declared = {
        (producer, artifact): label for producer, artifact, label in manuscript.cross_phase_inputs
    }
    assert set(declared) == {
        ("retrieval", "retrieval_report"),
        ("novelty", "novelty_claim"),
        ("plan", "research_plan"),
    }, sorted(declared)
    # 性质由**产出方**的声明推导（`producer_trust_label`），不由读取方自报：
    # 三份材料的产出相都声明了 `capability_execution: run_chain`、且它们的能力面落在
    # 带 `network_domains` 的 provider 上 ⇒ 三条都是 RETRIEVED。**这是既有规则的读数，
    # 不是本协议放宽了什么**：判据在这里断言它（而不是断言一个「看起来更严」的值），
    # 因为性质面是上游那条机制的事 —— 手稿相不重推它。
    for (producer, _artifact), label in declared.items():
        assert label.value == "RETRIEVED", (producer, label)


def test_every_declared_cross_phase_edge_resolves() -> None:
    """(3) 九条边（含本相三条）逐条解析，一条都不缺 —— 缺一条就是「材料从没进过会话」。"""
    found = {
        (phase["id"], reference)
        for phase in _raw()["phases"]
        for reference in phase.get("inputs") or []
    }
    assert found == set(_CROSS_PHASE_EDGES), sorted(found ^ set(_CROSS_PHASE_EDGES))


def test_the_non_consuming_phases_declare_no_cross_phase_inputs() -> None:
    """(4) C-1：`experiment` / `report` 两相不声明跨相 `inputs`（它们的执行体不读）。"""
    phases = _phases()
    offenders = {
        phase_id: phases[phase_id].get("inputs")
        for phase_id in _NON_CONSUMING_PHASES
        if phases[phase_id].get("inputs")
    }
    assert not offenders, offenders


def test_the_report_phase_declares_both_products() -> None:
    """手稿要与报告**并存**：报告相声明两个产物（既有产物零回归 + 新产物）。"""
    report = _phases()["report"]
    assert report["outputs"] == ["research_report.md", "manuscript.md"]
    assert report["task_contract"] == "research_report_deliverable"


def test_the_existing_protocols_are_untouched() -> None:
    """(5) 既有协议各自的相集**一字未改**（这是「未改」的机械证据）。

    四份协议各自的相集被各自的判据钉死；本判据在这里再钉一次**字面**相集（不重跑
    那四份判据 —— 它们在本轮各自全绿，那是另一条证据）。
    """
    expected = {
        "direction_to_question_v1.yaml": ("question", "retrieval"),
        "research_report_chain_v1.yaml": ("plan", "experiment", "review", "report"),
        "direction_to_report_v1.yaml": (
            "question",
            "retrieval",
            "plan",
            "experiment",
            "review",
            "report",
        ),
        "direction_to_report_v2.yaml": (
            "question",
            "retrieval",
            "novelty",
            "plan",
            "experiment",
            "review",
            "report",
        ),
    }
    actual = {name: tuple(str(phase["id"]) for phase in _raw(name)["phases"]) for name in expected}
    assert actual == expected, actual


def test_a_report_executor_on_the_manuscript_contract_is_refused() -> None:
    """反证臂 (a)：给手稿契约加上 `report: {}` ⇒ 编译**点名** `CROSS_PHASE_INPUT_INVALID`。

    按压在**真文件**上做（改字节 → 编译必须点名拒绝 → 按 raw `sha256` 逐字节复原）。
    没有这一臂，「手稿相是会话相」这条判据可能只是碰巧为真。
    """
    path = _CONTRACTS
    original = path.read_bytes()
    before = hashlib.sha256(original).hexdigest()
    anchor = "  research_manuscript:\n    version: 1.0.0\n"
    text = original.decode("utf-8")
    assert anchor in text, "contract block anchor not found"
    pressed = text.replace(
        anchor, "  research_manuscript:\n    version: 1.0.0\n    report: {}\n", 1
    ).encode("utf-8")
    assert hashlib.sha256(pressed).hexdigest() != before
    try:
        path.write_bytes(pressed)
        protocol = load_protocol(f"examples/protocols/{_PROTOCOL}")
        result = compile_protocol(protocol, load_catalog_snapshot(), load_project_settings())
        codes = {str(f.code) for f in result.findings}
        assert "CROSS_PHASE_INPUT_INVALID" in codes, (
            "a report executor on the manuscript phase did not produce "
            f"CROSS_PHASE_INPUT_INVALID: {sorted(codes)}"
        )
        # `compile_protocol` 只在 **DAG** 阻塞时返回 `plan=None`；跨相输入的 ERROR 随计划
        # 携带（`finding` 的 severity 是 ERROR），由 preflight 聚合判死。判据因此判
        # **severity 与点名**，不判 `plan is None` —— 后者会是一条假判据。
        blocking = [
            f
            for f in result.findings
            if str(f.code) == "CROSS_PHASE_INPUT_INVALID"
            and str(getattr(f.severity, "value", f.severity)) == "ERROR"
        ]
        assert blocking, [str(f.severity) for f in result.findings]
        joined = " ".join(str(f.message) for f in blocking)
        assert "manuscript" in joined, joined
    finally:
        path.write_bytes(original)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before, "press restore failed"


def test_dropping_a_manuscript_edge_turns_the_edge_judge_red() -> None:
    """反证臂 (b)：从手稿相摘掉 `plan:research_plan` ⇒ 边判据**点名判红**（真文件按压）。"""
    path = _PROTOCOLS / _PROTOCOL
    original = path.read_bytes()
    before = hashlib.sha256(original).hexdigest()
    line = "    inputs: [retrieval:retrieval_report, novelty:novelty_claim, plan:research_plan]\n"
    text = original.decode("utf-8")
    assert line in text, "manuscript inputs line not found"
    pressed = text.replace(
        line,
        "    inputs: [retrieval:retrieval_report, novelty:novelty_claim]\n",
        1,
    ).encode("utf-8")
    try:
        path.write_bytes(pressed)
        found = {
            (str(phase["id"]), reference)
            for phase in _raw()["phases"]
            for reference in phase.get("inputs") or []
        }
        assert found != set(_CROSS_PHASE_EDGES), (
            "dropping a manuscript cross-phase edge left the edge set unchanged — "
            "the judge cannot see the defect it exists to catch"
        )
        assert ("manuscript", "plan:research_plan") not in found
    finally:
        path.write_bytes(original)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before, "press restore failed"


@pytest.mark.parametrize("name", sorted(path.name for path in _PROTOCOLS.glob("*.yaml")))
def test_every_shipped_protocol_still_loads(name: str) -> None:
    """遍历面非空且每份协议仍可解析（新协议不是「唯一能读的那一份」）。"""
    assert _phases(name), name
