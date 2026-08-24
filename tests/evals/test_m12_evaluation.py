"""M12 Independent Evaluation E2E：M11 harness 独立评测 M12 workflow 产物。

用真实 M12 实验/证据链产物作为冻结输入，跑 `m12_research_v1` 评测集
（deterministic scorer + independent ground truth scorer），验证：
- 冻结数据集 digest 校验（篡改拒绝）；
- 全部 case PASS → gate verdict PASS（metric 与 ArtifactStore 独立重算一致）；
- 输入缺失 → INFRA_ERROR（不判被评对象失败）；
- 报告 digest 可复现（同输入同 digest）；
- baseline vs candidate 方向与 Claim 语义一致（M12-R1 WP5：无 0.745 自证常量）。

fixtures/标识与生产链一致（tests/evals/m12_eval_fixtures.py）。
"""

from __future__ import annotations

import pytest

from packages.application.evaluation.registry import dataset_from_dict
from packages.application.evaluation.runner import RunRequest, run_evaluation
from packages.domain.enums import QualityGateVerdict
from packages.domain.eval_result import EvalFindingStatus
from tests.evals.m12_eval_fixtures import (
    DATASET_PATH,
    base_inputs,
    dataset,
    evidence_map,
    gate,
    make_artifacts,
    make_ledger,
    run,
    runtime_scorers,
)


class TestM12IndependentEvaluation:
    def test_all_cases_pass_with_real_artifacts(self) -> None:
        report = run(base_inputs())
        assert report.gate_verdict is QualityGateVerdict.PASS
        assert len(report.results) == 12
        for result in report.results:
            assert result.passed, f"case {result.case_id} failed: {result.scorer_findings}"

    def test_missing_input_is_infra_error_not_fail(self) -> None:
        inputs = base_inputs()
        inputs.pop("input://m12/result_correctness")
        outcome = run_evaluation(
            RunRequest(
                dataset=dataset(),
                config=gate(),
                mode="OFFLINE_FAKE",
                system_version="0.4.0",
                inputs=inputs,
                evidence=evidence_map(),
                runtime_scorers=runtime_scorers(make_artifacts(), make_ledger()),
            )
        )
        assert outcome.missing_inputs == ("input://m12/result_correctness",)
        missing = [
            result
            for result in outcome.report.results
            if result.case_id == "result_correctness_001"
        ][0]
        assert missing.scorer_findings[0].status is EvalFindingStatus.INFRA_ERROR
        assert outcome.report.gate_verdict is QualityGateVerdict.REVISE

    def test_report_digest_reproducible(self) -> None:
        first = run(base_inputs())
        second = run(base_inputs())
        assert first.digest() == second.digest()

    def test_dataset_tampering_rejected(self) -> None:
        raw = _dataset_text().replace("result_correctness_001", "result_correctness_002")
        with pytest.raises(Exception):
            dataset_from_dict(_parse(raw), declared_digest="sha256:" + "0" * 64)

    def test_metric_ground_truth_from_artifact_not_expected_constant(self) -> None:
        """0.745 不再以 expected 常量形式存在于 dataset（自证循环消除）。"""
        raw = _dataset_text()
        assert "'0.745'" not in raw
        assert "metric: metrics.baseline_accuracy" in raw
        assert "artifact_id:" in raw

    def test_reported_metric_must_match_artifact(self) -> None:
        """伪造报告值（0.999）→ metric_correctness FAIL。"""
        report = run({**base_inputs(), "input://m12/result_correctness": "0.999"})
        result = next(item for item in report.results if item.case_id == "result_correctness_001")
        assert not result.passed
        assert result.scorer_findings[0].status is EvalFindingStatus.FAIL

    def test_reversed_direction_fails(self) -> None:
        """方向反转（candidate 0.75 > baseline 0.20）→ direction_improvement FAIL。"""
        reversed_experiment = {
            "status": "SUCCEEDED",
            "metrics": {
                "baseline_accuracy": "0.20",
                "candidate_accuracy": "0.75",
                "n_train": 500,
                "n_test": 200,
            },
            "seed": 7,
        }
        report = run({
            **base_inputs(),
            "input://m12/experimental_validity": reversed_experiment,
        })
        result = next(
            item for item in report.results if item.case_id == "direction_improvement_001"
        )
        assert not result.passed
        assert result.scorer_findings[0].status is EvalFindingStatus.FAIL


def _dataset_text() -> str:
    from pathlib import Path

    return Path(DATASET_PATH).read_text(encoding="utf-8")


def _parse(text: str) -> dict[str, object]:
    import yaml

    parsed = yaml.safe_load(text)
    if not isinstance(parsed, dict):
        raise ValueError("dataset must be a mapping")
    return parsed
