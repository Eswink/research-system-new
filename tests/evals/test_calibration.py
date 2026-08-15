"""M11 Calibration 测试与校准样本（obvious/ambiguous/adversarial 等）。"""

from __future__ import annotations

from packages.application.evaluation.calibration import (
    CalibrationSample,
    calibrate,
)
from packages.domain.eval_result import ReviewerVerdict


def test_calibration_agreement_and_disagreement() -> None:
    samples = (
        CalibrationSample("obvious-pass", ReviewerVerdict.PASS, ReviewerVerdict.PASS),
        CalibrationSample("obvious-fail", ReviewerVerdict.FAIL, ReviewerVerdict.FAIL),
        CalibrationSample("false-positive", ReviewerVerdict.FAIL, ReviewerVerdict.PASS),
        CalibrationSample("false-negative", ReviewerVerdict.PASS, ReviewerVerdict.FAIL),
    )
    report = calibrate(samples)
    assert report.total == 4
    assert report.agreements == 2
    assert report.disagreements == 2
    assert report.false_positives == ("false-positive",)
    assert report.false_negatives == ("false-negative",)
    assert report.ambiguous == ()


def test_calibration_ambiguous_is_excluded() -> None:
    samples = (
        CalibrationSample("ambiguous", ReviewerVerdict.AMBIGUOUS, ReviewerVerdict.PASS),
        CalibrationSample("machine-ambiguous", ReviewerVerdict.PASS, ReviewerVerdict.AMBIGUOUS),
    )
    report = calibrate(samples)
    assert report.ambiguous == ("ambiguous", "machine-ambiguous")
    assert report.agreements == 0
    assert report.disagreements == 0


def test_calibration_does_not_modify_samples() -> None:
    samples = (
        CalibrationSample(
            "polished-but-wrong",
            ReviewerVerdict.FAIL,
            ReviewerVerdict.PASS,
            "verbose confident wrong answer",
        ),
        CalibrationSample(
            "terse-but-correct", ReviewerVerdict.PASS, ReviewerVerdict.PASS, "short correct answer"
        ),
    )
    before = tuple(str(sample) for sample in samples)
    calibrate(samples)
    after = tuple(str(sample) for sample in samples)
    assert before == after


def test_calibration_adversarial_wording_not_rewarded() -> None:
    # polished-but-wrong：machine 给 PASS，human 判 FAIL → FP 必须被记录
    samples = (
        CalibrationSample(
            "adversarial-wording",
            ReviewerVerdict.FAIL,
            ReviewerVerdict.PASS,
            "eloquent but objectively incorrect",
        ),
    )
    report = calibrate(samples)
    assert report.false_positives == ("adversarial-wording",)


def test_calibration_empty_input() -> None:
    report = calibrate(())
    assert report.total == 0
    assert report.agreement_rate == "0"


def test_calibration_full_agreement_rate() -> None:
    samples = tuple(
        CalibrationSample(f"s{i}", ReviewerVerdict.PASS, ReviewerVerdict.PASS) for i in range(4)
    )
    report = calibrate(samples)
    assert report.agreement_rate == "1"
