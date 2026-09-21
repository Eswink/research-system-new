"""真实交付物契约的同源判据（GOAL-010 EC-01 / PLAN-20260921-127 WP3）。

**判据判同源，不判文笔。** 「交付物的键名由**合约声明**决定」这条规则同时活在四处：
合约文件（声明本身）、adapter（读声明）、离线链用例（端到端行为）、以及文档（给人读的
口径）。任何一处单独改掉，读者就会读到与代码不符的事实。本判据把四处**互相钉住**。

它钉住三件容易被悄悄改掉的事：

1. **声明只有一个**：`console_demo_deliverable` 声明**恰一个** artifact 名
   `analysis_report`——这是「谁声明名字」的**事实来源**，不是 adapter 的注释。
2. **不猜的边界**：声明**零个**或**多个互不相同**的名字时，adapter 必须回落事实名
   `session_message`——不允许挑一个去凑验收门（那等于 adapter 自己变成了声明方）。
   **同名在两处重复声明不算「多个」**（`required_artifacts` 与 `ARTIFACT_EXISTS` 去重）。
3. **文档与代码同口径**：交付物载荷的三个来源字段与「宣告权归合约」这句写在 adapter 的
   读面文档里，且链级**两个分支**的函数名都写在架构文档里——改行为必须同改文档。

**本判据不发起任何真实调用**，也不 import adapter 的私有构造；它判的是**规则本身**。
端到端行为由 `tests/e2e/test_ec03_real_runtime_offline_chain.py` 的两个分支用例承担。
"""

from __future__ import annotations

from pathlib import Path

from adapters.contracts import load_task_contracts
from adapters.openhands.runtime_adapter import _declared_deliverable_name
from packages.domain.enums import AcceptanceCriterionType
from packages.domain.tasks import AcceptanceCriterion, TaskContract

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = REPO_ROOT / "examples/contracts/task_contracts.yaml"
ADAPTER = REPO_ROOT / "adapters/openhands/runtime_adapter.py"
ADAPTER_DOC = REPO_ROOT / "docs/integration/OPENHANDS_ADAPTER.md"
RUNTIME_DOC = REPO_ROOT / "docs/architecture/AGENT_RUNTIME.md"
ADR = REPO_ROOT / "docs/adr/ADR-0031-toolpack-capability-policy.md"
CHAIN_TEST = REPO_ROOT / "tests/e2e/test_ec03_real_runtime_offline_chain.py"

CONTRACT_KEY = "console_demo_deliverable"
DECLARED_NAME = "analysis_report"
FACT_NAME = "session_message"


def _contract(
    *, criteria: list[AcceptanceCriterion], required: list[str] | None = None
) -> TaskContract:
    """一个最小合约：只有本判据关心的两处声明（其余字段取缺省）。

    域模型要求**至少一条**验收标准，因此调用方给的 `criteria` 为空时补一条
    `EVIDENCE_COVERAGE`——它不声明 artifact 名，正好让「名字只写在
    `required_artifacts` 里」这一格可测。
    """
    return TaskContract(
        id=CONTRACT_KEY,
        version="1.0.0",
        purpose="judged by the same-source gate",
        required_artifacts=list(required or []),
        acceptance_criteria=list(criteria) or [_coverage()],
    )


def _artifact(name: str) -> AcceptanceCriterion:
    return AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS, artifact=name)


def _coverage() -> AcceptanceCriterion:
    return AcceptanceCriterion(type=AcceptanceCriterionType.EVIDENCE_COVERAGE, minimum_sources=1)


def test_the_example_contract_declares_exactly_one_artifact_name() -> None:
    """事实来源：示例合约声明**恰一个** artifact 名，且就是 `analysis_report`。"""
    contract = load_task_contracts(str(CONTRACTS))[CONTRACT_KEY]
    names = {
        item.artifact
        for item in contract.acceptance_criteria
        if item.type is AcceptanceCriterionType.ARTIFACT_EXISTS
    }
    assert names == {DECLARED_NAME}, (names, contract.acceptance_criteria)
    assert contract.required_artifacts == [], contract.required_artifacts
    assert _declared_deliverable_name(contract) == DECLARED_NAME


def test_a_single_declaration_names_the_deliverable() -> None:
    """恰一个声明 ⇒ 用该名（无论它写在哪一处声明面）。"""
    assert _declared_deliverable_name(_contract(criteria=[_artifact(DECLARED_NAME)])) == (
        DECLARED_NAME
    )
    assert (
        _declared_deliverable_name(_contract(criteria=[], required=[DECLARED_NAME]))
        == DECLARED_NAME
    )


def test_the_same_name_in_both_surfaces_is_still_a_single_declaration() -> None:
    """同一名字在两处声明**不算多个**：合并去重后仍是唯一，仍用该名。"""
    both = _contract(criteria=[_artifact(DECLARED_NAME)], required=[DECLARED_NAME])
    assert _declared_deliverable_name(both) == DECLARED_NAME


def test_a_non_unique_declaration_is_not_guessed() -> None:
    """**不猜的边界**：零个或两个互不相同的名字 ⇒ `None`（adapter 回落事实名）。

    这一格是本契约最要紧的诚实点：没有它，只要合约多声明一个 artifact，
    adapter 就会挑一个名字去凑验收门——等于 adapter 自己变成了声明方。
    """
    assert _declared_deliverable_name(_contract(criteria=[_coverage()])) is None
    two = _contract(criteria=[_artifact(DECLARED_NAME), _artifact("review_verdict")])
    assert _declared_deliverable_name(two) is None


def test_the_deliverable_actually_uses_the_declared_name() -> None:
    """adapter 的交付物**真的读**这条规则——不是只有 helper 存在。"""
    source = ADAPTER.read_text(encoding="utf-8")
    assert "_declared_deliverable_name(" in source, "交付物必须调用声明解析"
    assert "_FACT_NAME" in source, "事实名必须仍是回落值（也是 ADR-0031 判据的断言）"
    assert FACT_NAME in source, "事实名的字面值必须留在 adapter 里"


def test_the_read_face_documents_the_provenance_fields() -> None:
    """读面文档与载荷同口径：三个来源字段都写在文档里。"""
    text = ADAPTER_DOC.read_text(encoding="utf-8")
    for field in ("fact_name", "declared_artifact", "contract_id"):
        assert field in text, f"交付物载荷字段 {field} 必须写进 adapter 文档"
    assert "恰一个" in text, "「声明恰一个才用该名」这条规则必须在文档里"
    assert "不猜" in text or "回落" in text, "回落事实名的边界必须在文档里"


def test_the_two_branches_are_documented_by_name() -> None:
    """架构文档写的是**真的在跑的**两个分支：用例名必须能在用例文件里找到。"""
    chain = CHAIN_TEST.read_text(encoding="utf-8")
    doc = RUNTIME_DOC.read_text(encoding="utf-8")
    for case in (
        "test_real_runtime_offline_chain_segments",
        "test_real_runtime_offline_chain_rejects_a_non_unique_declaration",
    ):
        assert case in chain, f"{case} 必须仍在链用例里"
        assert case in doc, f"架构文档必须按名指向 {case}"
    assert "字面" in doc, "「门仍按字面名匹配」必须在文档里（否则读者会以为判据放宽了）"


def test_the_adr_records_the_direction_without_claiming_acceptance() -> None:
    """ADR-0031：D2 的定向被记录，而**整体仍是草案**（D1 未决）。"""
    text = ADR.read_text(encoding="utf-8")
    assert "Status: Proposed" in text, "D1 未决 ⇒ 该 ADR 整体必须仍是 Proposed"
    assert "Status: Accepted" not in text, "未拍板不得冒充 Accepted"
    assert "已定向" in text, "D2 的定向必须写进该 ADR 的 D2 节"
    assert "可分别决定" in text, "「两个决定可分别决定」是保持 Proposed 的依据"
