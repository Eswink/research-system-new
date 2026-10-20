"""`EVIDENCE_COVERAGE` 的**工具维**（`minimum_tool_evidences`，GOAL-20261020-090）。

**它补哪一格**（GOAL-089 `W-6` 实测到的洞）：性质维数的是「来源里有多少条
`TrustLabel.RETRIEVED`」，而跨相输入的 `trust_label` 由**产出方**的声明推出
（`producer_trust_label`：声明 `run_chain` + 能力面落在带 `network_domains` 的 provider
⇒ `RETRIEVED`）—— 那个推导**不问产出方本次是否真的执行过任何调用**。

后果是一族**结构上咬不住的假绿**：一个 phase 为了把 provider 排除出**会话工具面**
（不排除的话 SDK 会点名 `ToolDefinition 'europe_pmc' is not registered`）而**必须**声明
`run_chain` + 声明 `literature.*`；于是它**模型写的字**被当成检索来源 ⇒ 下游检索格的
`minimum_retrieved_sources` 可被一条与被测能力无关的跨相边**单独满足**。

工具维只数**带 `tool_refs` 的证据**：工具证据登记时必然带 `(provider_id, tool_id)`，
跨相输入**不带**。它问的是**调用事实**，不是声明事实。

**本文件的判据**（每条都自带反证臂）：

1. 只有跨相证据（`tool_refs` 为空）⇒ 工具维**判负**并点名 —— 这正是 `W-6` 的形态；
2. 加上一条真工具证据 ⇒ **判过**（同一份来源集合，只多一条调用事实）；
3. 未声明 `minimum_tool_evidences` ⇒ **逐字不变**（既有两维的行为不动）；
4. 声明了但计数未知 ⇒ **fail-closed** 点名，不当作「没有要求」；
5. 合约层：出厂 `research_question_retrieval` 真的声明了这一维（否则本判据无执法对象）。
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from packages.domain.acceptance import CriterionInputs, evaluate_criterion
from packages.domain.enums import AcceptanceCriterionType
from packages.domain.evidence import Evidence
from packages.domain.tasks import AcceptanceCriterion

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "examples" / "contracts" / "task_contracts.yaml"


def _criterion(**overrides: object) -> AcceptanceCriterion:
    fields: dict[str, object] = {
        "type": AcceptanceCriterionType.EVIDENCE_COVERAGE,
        "minimum_sources": 1,
        "minimum_retrieved_sources": 1,
    }
    fields.update(overrides)
    return AcceptanceCriterion(**fields)  # type: ignore[arg-type]


def _verdict(criterion: AcceptanceCriterion, inputs: CriterionInputs) -> tuple[bool, str]:
    evaluation = evaluate_criterion(criterion, inputs)
    return evaluation.passed, evaluation.reason


def test_a_cross_phase_only_source_passes_the_first_two_dimensions() -> None:
    """**W-6 的形态**：那条跨相边确实能喂饱前两维 —— 这不是本判据要主张的反面。

    先把这个事实钉住，才能说明工具维补的是**真实存在的**缝，而不是想象出来的。
    """
    passed, reason = _verdict(
        _criterion(),
        CriterionInputs(evidence_source_count=1, retrieved_source_count=1),
    )
    assert passed is True, reason
    assert "1 >= 1 sources" in reason and "1 >= 1 retrieved" in reason, reason


def test_the_tool_dimension_rejects_a_cross_phase_only_source() -> None:
    """**核心反证**：同样的来源集合，加上工具维 ⇒ 判负且点名那条陈述。"""
    criterion = _criterion(minimum_tool_evidences=1)
    passed, reason = _verdict(
        criterion,
        CriterionInputs(evidence_source_count=1, retrieved_source_count=1, tool_evidence_count=0),
    )
    assert passed is False, reason
    assert "0 < 1 tool evidences" in reason, reason
    assert "cross-phase input is not a tool call" in reason, reason


def test_one_real_tool_call_satisfies_the_tool_dimension() -> None:
    """同一份来源集合 + 一条真工具证据 ⇒ 判过（只多了**调用事实**）。"""
    criterion = _criterion(minimum_tool_evidences=1)
    passed, reason = _verdict(
        criterion,
        CriterionInputs(evidence_source_count=1, retrieved_source_count=1, tool_evidence_count=1),
    )
    assert passed is True, reason
    assert "1 >= 1 tool evidences" in reason, reason


def test_without_the_declaration_the_behaviour_is_byte_identical() -> None:
    """**零回归**：未声明 ⇒ 判词**逐字**就是既有形态（不多一个分句）。"""
    passed, reason = _verdict(
        _criterion(),
        CriterionInputs(
            evidence_source_count=2,
            retrieved_source_count=1,
            # 即使这里给了 0，未声明就不该出现在判词里。
            tool_evidence_count=0,
        ),
    )
    assert passed is True, reason
    assert reason == "2 >= 1 sources; 1 >= 1 retrieved", reason


def test_an_unknown_tool_count_is_named_not_ignored() -> None:
    """**fail-closed**：声明了而计数未知 ⇒ 点名，不当作「没有要求」。"""
    criterion = _criterion(minimum_tool_evidences=1)
    passed, reason = _verdict(
        criterion,
        CriterionInputs(evidence_source_count=1, retrieved_source_count=1),
    )
    assert passed is False, reason
    assert reason == "tool evidence count unknown", reason


def test_a_negative_declaration_is_refused_at_construction() -> None:
    with pytest.raises(ValueError, match="minimum_tool_evidences must be >= 0"):
        _criterion(minimum_tool_evidences=-1)


def test_the_shipped_retrieval_contract_declares_the_dimension() -> None:
    """**受判对象必须存在**：出厂检索格真的声明了工具维（否则本判据空转）。

    空真（vacuously true）的绿不算收口 —— 承 `MEM-20260928-156`。这里读**产品数据文件**
    （不是夹具），所以「合约被改回两维」会立刻判红。
    """
    text = CONTRACTS.read_text(encoding="utf-8")
    marker = "  research_question_retrieval:"
    assert marker in text, "出厂合约 research_question_retrieval 不在任务契约文件里"
    section = text.split(marker, 1)[1].split("\n  research_", 1)[0]
    assert "minimum_tool_evidences: 1" in section, (
        "检索格没有声明工具维 ⇒ GOAL-089 的 W-6（跨相边喂饱性质维）在出厂的检索格上"
        f"仍然敞开。该合约现文：\n{section[:800]}"
    )
    assert "version: 1.1.0" in section, section[:200]


def test_tool_refs_is_the_discriminator_between_the_two_evidence_kinds() -> None:
    """**可判别性前提**：两类证据在 `tool_refs` 上确实可分（不是靠 id 猜）。

    这条钉住的是**判据赖以成立的那个结构事实**：工具证据带 `(provider, tool)`，
    跨相输入不带。若将来跨相输入开始带 `tool_refs`，工具维会被它一起满足 ⇒ 本判据判红，
    提醒改写判别依据 —— 而不是让工具维静默退化成「和性质维一样」。
    """
    tool_like = Evidence(
        id="evidence:run:task:tool",
        source_ref="tool:europe_pmc",
        content_digest="sha256:" + "0" * 64,
        extracted_by="system:run-chain",
        artifact_id="tool-result:x",
        run_id="run-1",
        tool_refs=("europe_pmc", "literature.search"),
    )
    cross_phase_like = Evidence(
        id="evidence:cross-phase:artifact:task",
        source_ref="cross-phase:task-a:research_question",
        content_digest="sha256:" + "1" * 64,
        extracted_by="system:cross-phase-input",
        artifact_id="task-a:research_question",
        run_id="run-1",
    )
    assert tool_like.tool_refs, "工具证据必须带 tool_refs"
    assert cross_phase_like.tool_refs == (), (
        "跨相输入的 tool_refs 必须为空 —— 它是工具维「不数跨相边」的唯一依据"
    )
    # 计数口径：只有前者被数进来。
    from packages.application.run_orchestration.result_handler import count_tool_evidences

    assert count_tool_evidences((tool_like, cross_phase_like)) == 1


def test_a_multiple_tool_threshold_counts_each_call() -> None:
    """阈值 >1 时按**条数**判（不是「有没有」的布尔折算）。"""
    criterion = _criterion(minimum_tool_evidences=2)
    passed_one, reason_one = _verdict(
        criterion,
        CriterionInputs(evidence_source_count=2, retrieved_source_count=2, tool_evidence_count=1),
    )
    assert passed_one is False, reason_one
    assert "1 < 2 tool evidences" in reason_one, reason_one
    passed_two, reason_two = _verdict(
        criterion,
        CriterionInputs(evidence_source_count=2, retrieved_source_count=2, tool_evidence_count=2),
    )
    assert passed_two is True, reason_two


def test_the_dimensions_are_independent_not_substitutes() -> None:
    """三维**互不顶替**：任缺一条即判负，判词点名缺的是哪一维。"""
    criterion = _criterion(minimum_tool_evidences=1)
    # 计数不够
    passed, reason = _verdict(
        criterion,
        CriterionInputs(evidence_source_count=0, retrieved_source_count=0, tool_evidence_count=5),
    )
    assert passed is False and "0 < 1 sources" in reason, reason
    # 性质不够（有工具也不够）
    passed, reason = _verdict(
        criterion,
        CriterionInputs(evidence_source_count=2, retrieved_source_count=0, tool_evidence_count=5),
    )
    assert passed is False and "0 < 1 retrieved" in reason, reason
    # 三维都够
    passed, reason = _verdict(
        criterion,
        CriterionInputs(
            evidence_source_count=2,
            retrieved_source_count=1,
            tool_evidence_count=1,
            metrics={"unrelated": Decimal("1")},
        ),
    )
    assert passed is True, reason
