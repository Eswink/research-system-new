"""M11 Regression / Canary 测试（DoD 2：真实 before/after 被 gate 拦截）。"""

from __future__ import annotations

from packages.application.evaluation.canary import select_canary
from packages.application.evaluation.regression import compare_reports
from packages.application.evaluation.runner import (
    RunRequest,
    run_evaluation,
)
from packages.domain.core import Version
from packages.domain.enums import QualityGateVerdict
from packages.domain.eval_gate import GateConfig
from packages.domain.eval_spec import (
    EvalCase,
    EvalDataset,
    EvalScope,
    ScorerRef,
)

_GOOD_INPUTS: dict[str, object] = {
    "input://c1": {"answer": 42},
    "input://c2": {"answer": 7},
    "input://c3": {"answer": 1},
}


def _case(case_id: str, expected: object, tags: tuple[str, ...] = ()) -> EvalCase:
    return EvalCase(
        id=case_id,
        version=Version("1.0.0"),
        scope=EvalScope.UNIT,
        input_ref=f"input://{case_id}",
        expected=expected,
        scorer_refs=(ScorerRef("exact_match", Version("1.0.0")),),
        tags=tags,
    )


def _dataset() -> EvalDataset:
    return EvalDataset(
        id="regression-ds",
        version=Version("1.0.0"),
        cases=(
            _case("c1", {"answer": 42}, ("canary",)),
            _case("c2", {"answer": 7}),
            _case("c3", {"answer": 1}),
        ),
    )


def _request(
    inputs: dict[str, object],
    config: GateConfig | None = None,
) -> RunRequest:
    return RunRequest(
        dataset=_dataset(),
        config=config or GateConfig(id="gate", version=Version("1.0.0")),
        mode="OFFLINE_FAKE",
        system_version="0.4.0",
        inputs=inputs,
    )


def test_before_after_regression_blocked_by_gate() -> None:
    # DoD 2 核心场景：prompt/config 变更使 canary case c1 从 PASS 变 FAIL，
    # candidate 必须被 gate 拦截（BLOCK），即使聚合分数仍高
    baseline = run_evaluation(_request(_GOOD_INPUTS)).report
    assert baseline.gate_verdict is QualityGateVerdict.PASS
    changed = dict(_GOOD_INPUTS)
    changed["input://c1"] = {"answer": 43}  # 变更导致 canary 失败
    candidate = run_evaluation(_request(changed)).report
    comparison = compare_reports(baseline, candidate)
    assert comparison.comparable is True
    assert comparison.newly_regressed == ("c1",)
    assert comparison.verdict is QualityGateVerdict.BLOCK
    assert comparison.blocked is True
    # 聚合：c2/c3 仍 PASS，但 canary 回归不可被掩盖
    assert candidate.gate_verdict is QualityGateVerdict.BLOCK


def test_unchanged_baseline_is_pass() -> None:
    baseline = run_evaluation(_request(_GOOD_INPUTS)).report
    candidate = run_evaluation(_request(_GOOD_INPUTS)).report
    comparison = compare_reports(baseline, candidate)
    assert comparison.comparable is True
    assert comparison.newly_regressed == ()
    assert comparison.newly_fixed == ()
    assert comparison.verdict is QualityGateVerdict.PASS


def test_newly_fixed_is_reported() -> None:
    broken = dict(_GOOD_INPUTS)
    broken["input://c2"] = {"answer": 99}
    baseline = run_evaluation(_request(broken)).report
    candidate = run_evaluation(_request(_GOOD_INPUTS)).report
    comparison = compare_reports(baseline, candidate)
    assert comparison.newly_fixed == ("c2",)
    assert comparison.verdict is QualityGateVerdict.PASS


def test_frozen_conditions_mismatch_refuses_comparison() -> None:
    baseline = run_evaluation(_request(_GOOD_INPUTS)).report
    other_config = GateConfig(id="gate", version=Version("1.0.1"))
    candidate = run_evaluation(_request(_GOOD_INPUTS, config=other_config)).report
    comparison = compare_reports(baseline, candidate)
    assert comparison.comparable is False
    assert comparison.reason == "frozen conditions differ"
    assert comparison.verdict is QualityGateVerdict.BLOCK


def test_case_set_mismatch_refuses_comparison() -> None:
    baseline = run_evaluation(_request(_GOOD_INPUTS)).report
    reduced_dataset = EvalDataset(
        id="regression-ds",
        version=Version("1.0.0"),
        cases=(_case("c1", {"answer": 42}),),
    )
    candidate_request = RunRequest(
        dataset=reduced_dataset,
        config=GateConfig(id="gate", version=Version("1.0.0")),
        mode="OFFLINE_FAKE",
        system_version="0.4.0",
        inputs={"input://c1": {"answer": 42}},
    )
    candidate = run_evaluation(candidate_request).report
    comparison = compare_reports(baseline, candidate)
    assert comparison.comparable is False
    assert comparison.reason == "case sets differ"


def test_canary_selects_tagged_subset() -> None:
    selection = select_canary(_dataset())
    assert selection.dataset is not None
    assert [case.id for case in selection.dataset.cases] == ["c1"]
    assert selection.is_proper_subset is True
    assert selection.excluded_case_ids == ("c2", "c3")


def test_canary_empty_dataset_is_fail_closed() -> None:
    no_tags = EvalDataset(
        id="no-canary",
        version=Version("1.0.0"),
        cases=(_case("c1", {"answer": 42}),),
    )
    selection = select_canary(no_tags)
    assert selection.dataset is None


def test_canary_run_is_fast_path() -> None:
    selection = select_canary(_dataset())
    assert selection.dataset is not None
    canary_run = RunRequest(
        dataset=selection.dataset,
        config=GateConfig(id="gate", version=Version("1.0.0")),
        mode="OFFLINE_FAKE",
        system_version="0.4.0",
        inputs={"input://c1": {"answer": 42}},
    )
    report = run_evaluation(canary_run).report
    assert report.gate_verdict is QualityGateVerdict.PASS
    assert len(report.results) == 1  # 只跑 canary case
