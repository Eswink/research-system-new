"""M11 Quality Gate 与 anti-gaming 测试：阈值篡改、自证绕过、失败样本删除。"""

from __future__ import annotations

from decimal import Decimal

from packages.application.evaluation.runner import (
    RunRequest,
    run_evaluation,
)
from packages.domain.core import Version
from packages.domain.enums import QualityGateVerdict
from packages.domain.eval_gate import GateConfig, ThresholdRule
from packages.domain.eval_result import EvalFindingStatus
from packages.domain.eval_spec import (
    EvalCase,
    EvalDataset,
    EvalScope,
    ScorerRef,
)


def _case(case_id: str, expected: object) -> EvalCase:
    return EvalCase(
        id=case_id,
        version=Version("1.0.0"),
        scope=EvalScope.UNIT,
        input_ref=f"input://{case_id}",
        expected=expected,
        scorer_refs=(ScorerRef("exact_match", Version("1.0.0")),),
    )


def _dataset() -> EvalDataset:
    return EvalDataset(
        id="gate-ds",
        version=Version("1.0.0"),
        cases=(_case("c1", {"answer": 42}), _case("c2", {"answer": 7})),
    )


def _request(
    config: GateConfig | None = None,
    *,
    dataset: EvalDataset | None = None,
    inputs: dict[str, object] | None = None,
) -> RunRequest:
    return RunRequest(
        dataset=dataset or _dataset(),
        config=config or GateConfig(id="gate", version=Version("1.0.0")),
        mode="OFFLINE_FAKE",
        system_version="0.4.0",
        inputs=inputs
        if inputs is not None
        else {
            "input://c1": {"answer": 42},
            "input://c2": {"answer": 7},
        },
    )


def test_threshold_lowering_changes_config_digest() -> None:
    strict = GateConfig(
        id="gate",
        version=Version("1.0.0"),
        rules=(ThresholdRule("review_score", threshold=Decimal("0.9")),),
    )
    loosened = GateConfig(
        id="gate",
        version=Version("1.0.0"),
        rules=(ThresholdRule("review_score", threshold=Decimal("0.5")),),
    )
    assert strict.digest() != loosened.digest()


def test_threshold_change_fails_frozen_conditions_comparison() -> None:
    # 同一 dataset 不同 gate config：frozen_conditions 不同 → 不能声称同一基线
    strict = run_evaluation(
        _request(
            config=GateConfig(
                id="gate",
                version=Version("1.0.0"),
                rules=(ThresholdRule("exact_match", hard_invariant=True),),
            )
        )
    )
    loose = run_evaluation(
        _request(
            config=GateConfig(
                id="gate",
                version=Version("1.0.1"),
                rules=(ThresholdRule("exact_match", threshold=Decimal("0.1")),),
            )
        )
    )
    assert (
        strict.report.frozen_conditions.gate_config_digest
        != loose.report.frozen_conditions.gate_config_digest
    )


def test_self_reported_score_cannot_become_eval_result() -> None:
    # 被评对象输出里塞 score=PASS；exact_match 全量比较 → 注入字段导致
    # FAIL → BLOCK（自报分数不能变成 PASS，fail-closed 防自证）
    report = run_evaluation(
        _request(
            inputs={
                "input://c1": {"answer": 42, "score": "PASS", "verdict": "0.99"},
                "input://c2": {"answer": 7, "score": "PASS"},
            }
        )
    ).report
    assert report.gate_verdict is QualityGateVerdict.BLOCK
    # 干净输入（无自报字段）才 PASS：自报字段不参与也不提升评分
    clean = run_evaluation(_request()).report
    assert clean.gate_verdict is QualityGateVerdict.PASS
    for result in clean.results:
        for finding in result.scorer_findings:
            assert finding.status is EvalFindingStatus.PASS


def test_any_deterministic_fail_blocks_even_with_high_aggregate() -> None:
    # 90% case 通过但 1 个确定性 FAIL → BLOCK（聚合不能掩盖关键失败）
    dataset = EvalDataset(
        id="gate-ds",
        version=Version("1.0.0"),
        cases=tuple(_case(f"c{i}", {"answer": i}) for i in range(10)),
    )
    inputs: dict[str, object] = {f"input://c{i}": {"answer": i} for i in range(10)}
    inputs["input://c9"] = {"answer": 999}
    report = run_evaluation(_request(dataset=dataset, inputs=inputs)).report
    assert report.gate_verdict is QualityGateVerdict.BLOCK


def test_failed_sample_deletion_breaks_dataset_identity() -> None:
    # 删除失败 case 后重跑 → dataset digest 改变 → 不能再声称同一数据集通过
    full = _dataset()
    reduced = EvalDataset(
        id="gate-ds",
        version=Version("1.0.0"),
        cases=(_case("c1", {"answer": 42}),),
    )
    assert full.digest() != reduced.digest()


def test_verdict_rule_reference_mismatch_is_revise() -> None:
    # config 声明了 scorer 但 dataset 不产生该 scorer → REVISE（fail-closed）
    config = GateConfig(
        id="gate",
        version=Version("1.0.0"),
        rules=(ThresholdRule("schema_validity", hard_invariant=True),),
    )
    outcome = run_evaluation(_request(config=config))
    assert outcome.report.gate_verdict is QualityGateVerdict.REVISE
