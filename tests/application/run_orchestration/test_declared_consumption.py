"""跨轮消费求值器（`CUSTOM_EVALUATOR`）的行为判据（GOAL-20261008-038 EC-02/EC-03）。

三条主轴（每条可被单变量按压）：

1. **声明与取值（EC-02）**：合约用**既有** `metric` 字段声明消费路径；解析器按点分路径
   取值；**fail-closed 三态**（未声明 / 路径缺失 / 值不可取）逐条点名。
2. **结构化比对（EC-03）**：取值与前序结论**逐字**比 —— 相等判过并留痕（含来源 run id
   与逐字值）；不等判负并**点名期望值与实际值**。
3. **接线（EC-03）**：求值结论经 `EvaluationInputs.consumption` 贴回**判据下标**；
   **未注入时域层的既有判词逐字保留**（两条路径互不覆盖）。

**如实边界**：本文件不判「因果」（「因为读了才这么写」）—— 那不可判；它判的是
「本轮产物**携带**了前序结论，且与来源**逐字一致**」。
"""

from __future__ import annotations

from typing import Any

from packages.application.run_orchestration.declared_consumption import (
    EVALUATOR_ID,
    declared_consumption_criteria,
    resolve_consumption,
    resolve_consumption_evaluations,
)
from packages.application.run_orchestration.evaluation_gate import (
    EvaluationInputs,
    evaluate_task_gate,
)
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, TaskContract

PRIOR_RUN = "11111111-1111-4111-8111-111111111111"
PRIOR_VERDICT = "PASS"
PATH = "meta_review.prior_verdict"


def _criterion(*, metric: str | None = PATH, evaluator: str = EVALUATOR_ID) -> AcceptanceCriterion:
    return AcceptanceCriterion(
        type=AcceptanceCriterionType.CUSTOM_EVALUATOR,
        evaluator=evaluator,
        metric=metric,
    )


def _task() -> ResearchTask:
    return ResearchTask(
        id=ID("22222222-2222-4222-8222-222222222222"),
        run_id=ID("33333333-3333-4333-8333-333333333333"),
        contract_id="cross_run_consumption_deliverable",
    )


def _contract(criteria: list[AcceptanceCriterion]) -> TaskContract:
    return TaskContract(
        id="cross_run_consumption_deliverable",
        version="1.0.0",
        purpose="p",
        output_schema="real_research_deliverable_v1",
        acceptance_criteria=criteria,
        required_capabilities=["artifact.write"],
    )


# --- EC-02：声明与取值（fail-closed 三态） --------------------------------------


def test_an_accepted_consumption_carries_the_source_and_the_verbatim_value() -> None:
    """主路：产物里的值与来源逐字一致 ⇒ 判过，判词含来源 run id 与逐字值。"""
    verdict = resolve_consumption(
        _criterion(),
        structured_output={"meta_review": {"prior_verdict": PRIOR_VERDICT}},
        prior_conclusion=PRIOR_VERDICT,
        prior_run_id=PRIOR_RUN,
    )
    assert verdict.passed is True
    assert PRIOR_VERDICT in verdict.reason
    assert PRIOR_RUN in verdict.reason, "判词必须点名来源 run id（可复核性）"
    assert verdict.observed == PRIOR_VERDICT


def test_a_mismatch_is_rejected_with_both_values_named() -> None:
    """反证：值与来源**不一致** ⇒ 判负且**期望值与实际值都点名**。"""
    verdict = resolve_consumption(
        _criterion(),
        structured_output={"meta_review": {"prior_verdict": "REJECT"}},
        prior_conclusion=PRIOR_VERDICT,
        prior_run_id=PRIOR_RUN,
    )
    assert verdict.passed is False
    assert "'REJECT'" in verdict.reason and "'PASS'" in verdict.reason, verdict.reason


def test_an_undeclared_path_is_named() -> None:
    """fail-closed①：没声明消费路径 ⇒ 点名（不回落默认值）。"""
    verdict = resolve_consumption(
        _criterion(metric=None),
        structured_output={"meta_review": {"prior_verdict": PRIOR_VERDICT}},
        prior_conclusion=PRIOR_VERDICT,
    )
    assert verdict.passed is False
    assert "未声明消费路径" in verdict.reason


def test_a_missing_declared_path_is_named() -> None:
    """fail-closed②：声明了但产物里没有那条路径 ⇒ 点名「声明路径缺失」。"""
    verdict = resolve_consumption(
        _criterion(),
        structured_output={"meta_review": {}},
        prior_conclusion=PRIOR_VERDICT,
    )
    assert verdict.passed is False
    assert "缺失" in verdict.reason and PATH in verdict.reason


def test_an_absent_prior_conclusion_is_never_a_pass() -> None:
    """fail-closed③：**没有前序结论** ⇒ 点名（不得当成「判过」）。"""
    verdict = resolve_consumption(
        _criterion(),
        structured_output={"meta_review": {"prior_verdict": PRIOR_VERDICT}},
        prior_conclusion=None,
    )
    assert verdict.passed is False
    assert "没有前序结论" in verdict.reason


def test_an_unknown_evaluator_id_is_named_not_ignored() -> None:
    """未认得的求值器 id ⇒ 点名（不静默当作「无此判据」）。"""
    resolved = resolve_consumption_evaluations(
        _contract([_criterion(evaluator="some_other_check")]),
        {"meta_review": {"prior_verdict": PRIOR_VERDICT}},
        PRIOR_VERDICT,
        PRIOR_RUN,
    )
    assert len(resolved) == 1
    assert list(resolved.values())[0].passed is False
    assert "不认识这个求值器" in list(resolved.values())[0].reason


def test_only_the_recognized_evaluator_is_selected() -> None:
    """声明面选择：只挑认得的那条（别的不动）。"""
    criteria = [_criterion(), _criterion(evaluator="other")]
    assert declared_consumption_criteria(_contract(criteria)) == (criteria[0],)


# --- EC-03：接线（贴回判据下标 + 未注入时既有判词保留） -------------------------


def test_the_gate_uses_the_orchestration_verdict_when_injected() -> None:
    """注入结论 ⇒ 判据判过，判词就是求值器的原文（逐字进既有读面）。"""
    contract = _contract([_criterion()])
    resolved = resolve_consumption_evaluations(
        contract, {"meta_review": {"prior_verdict": PRIOR_VERDICT}}, PRIOR_VERDICT, PRIOR_RUN
    )
    outcome = evaluate_task_gate(
        _task(),
        contract,
        EvaluationInputs(
            structured_output={"meta_review": {"prior_verdict": PRIOR_VERDICT}},
            consumption=resolved,
        ),
        reviewer="gate:test",
    )
    assert outcome.verdict == "PASS"
    assert any(PRIOR_RUN in reason for reason in outcome.review_finding.findings), (
        outcome.review_finding.findings
    )


def test_without_injection_the_domain_wording_is_preserved_verbatim() -> None:
    """未注入 ⇒ 域层既有判词**逐字保留**（两条路径互不覆盖）。"""
    outcome = evaluate_task_gate(
        _task(),
        _contract([_criterion()]),
        EvaluationInputs(structured_output={"meta_review": {"prior_verdict": PRIOR_VERDICT}}),
        reviewer="gate:test",
    )
    assert outcome.verdict == "REJECT"
    assert any(
        "must be executed by the orchestration layer" in reason
        for reason in outcome.review_finding.findings
    ), outcome.review_finding.findings


def test_a_rejected_consumption_makes_the_gate_reject() -> None:
    """反证在门面上的形态：消费不成立 ⇒ 门判 REJECT。"""
    contract = _contract([_criterion()])
    resolved = resolve_consumption_evaluations(
        contract, {"meta_review": {"prior_verdict": "REJECT"}}, PRIOR_VERDICT, PRIOR_RUN
    )
    outcome = evaluate_task_gate(
        _task(),
        contract,
        EvaluationInputs(
            structured_output={"meta_review": {"prior_verdict": "REJECT"}},
            consumption=resolved,
        ),
        reviewer="gate:test",
    )
    assert outcome.verdict == "REJECT"


def test_structured_values_are_compared_not_substrings() -> None:
    """结构化比对（不是子串巧合）：只是**包含**来源文本不算消费成立。"""
    verdict = resolve_consumption(
        _criterion(metric="meta_review.text"),
        structured_output={"meta_review": {"text": f"我参考了 {PRIOR_VERDICT} 的结论"}},
        prior_conclusion=PRIOR_VERDICT,
        prior_run_id=PRIOR_RUN,
    )
    assert verdict.passed is False, (
        "整段文本里含来源串**不**等于「携带了来源的结论」（那正是文本巧合）",
        verdict.reason,
    )


def test_a_non_string_value_is_compared_by_its_text_form() -> None:
    """非字符串值按文本形态比（判词里逐字给出实际值）。"""
    verdict: Any = resolve_consumption(
        _criterion(metric="meta_review.count"),
        structured_output={"meta_review": {"count": 3}},
        prior_conclusion="3",
    )
    assert verdict.passed is True
    assert verdict.observed == "3"
