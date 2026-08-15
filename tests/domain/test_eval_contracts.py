"""M11 EvalCase/EvalDataset/GateConfig 域契约测试：frozen 语义与 digest 防篡改。"""

from __future__ import annotations

from decimal import Decimal

import pytest

from packages.domain.core import Digest, Version
from packages.domain.eval_gate import GateConfig, ThresholdRule
from packages.domain.eval_result import (
    EvalFindingStatus,
    EvalResult,
    EvalScore,
    ScorerFinding,
)
from packages.domain.eval_spec import (
    EvalCase,
    EvalDataset,
    EvalDeterminism,
    EvalScope,
    RubricSpec,
    ScorerRef,
    case_digest,
)
from tests.domain.eval_contracts_support import make_case, make_dataset, make_report

# --- EvalCase / EvalDataset freeze semantics ---


def test_case_requires_executable_oracle() -> None:
    with pytest.raises(ValueError, match="expected or rubric"):
        EvalCase(
            id="case-x",
            version=Version("1.0.0"),
            scope=EvalScope.UNIT,
            input_ref="input://x",
            expected=None,
            description="text only",
        )


def test_case_rubric_counts_as_oracle() -> None:
    case = EvalCase(
        id="case-x",
        version=Version("1.0.0"),
        scope=EvalScope.UNIT,
        input_ref="input://x",
        expected=None,
        rubric=(RubricSpec("r1", "soundness", "is it sound"),),
    )
    assert case_digest(case).hex_value


def test_case_canary_requires_unit_or_integration() -> None:
    with pytest.raises(ValueError, match="canary"):
        EvalCase(
            id="case-w",
            version=Version("1.0.0"),
            scope=EvalScope.WORKFLOW,
            input_ref="input://w",
            expected={},
            tags=("canary",),
        )


def test_case_determinism_classification_changes_digest() -> None:
    case = EvalCase(
        id="case-nd",
        version=Version("1.0.0"),
        scope=EvalScope.UNIT,
        input_ref="input://nd",
        expected={"answer": 42},
        determinism=EvalDeterminism.NON_DETERMINISTIC,
    )
    assert case.determinism is EvalDeterminism.NON_DETERMINISTIC
    assert case_digest(case) != case_digest(make_case("case-nd"))


def test_case_digest_excludes_description() -> None:
    described = EvalCase(
        id="case-001",
        version=Version("1.0.0"),
        scope=EvalScope.UNIT,
        input_ref="input://case-001",
        expected={"answer": 42},
        scorer_refs=(ScorerRef("exact_match", Version("1.0.0")),),
        description="annotated",
    )
    assert case_digest(described) == case_digest(make_case("case-001"))


def test_case_digest_rejects_float_expected() -> None:
    case = EvalCase(
        id="case-f",
        version=Version("1.0.0"),
        scope=EvalScope.UNIT,
        input_ref="input://f",
        expected={"ratio": 0.5},
    )
    with pytest.raises(ValueError, match="float"):
        case_digest(case)


def test_dataset_rejects_duplicate_case_ids() -> None:
    with pytest.raises(ValueError, match="duplicate case id"):
        EvalDataset(
            id="ds",
            version=Version("1.0.0"),
            cases=(make_case("case-001"), make_case("case-001")),
        )


def test_dataset_rejects_empty() -> None:
    with pytest.raises(ValueError, match="at least one case"):
        EvalDataset(id="ds", version=Version("1.0.0"), cases=())


def test_dataset_digest_ignores_case_order() -> None:
    a = EvalDataset(
        id="ds",
        version=Version("1.0.0"),
        cases=(make_case("case-001"), make_case("case-002", expected={"answer": 7})),
    )
    b = EvalDataset(
        id="ds",
        version=Version("1.0.0"),
        cases=(make_case("case-002", expected={"answer": 7}), make_case("case-001")),
    )
    assert a.digest() == b.digest()


def test_dataset_digest_stable_across_instances() -> None:
    assert make_dataset().digest() == make_dataset().digest()


def test_dataset_digest_detects_case_mutation() -> None:
    mutated = EvalDataset(
        id="dataset-unit",
        version=Version("1.0.0"),
        cases=(
            make_case("case-001", expected={"answer": 43}),
            make_case("case-002", expected={"answer": 7}),
        ),
    )
    assert make_dataset().digest() != mutated.digest()


def test_dataset_digest_detects_case_removal() -> None:
    reduced = EvalDataset(
        id="dataset-unit",
        version=Version("1.0.0"),
        cases=(make_case("case-001"),),
    )
    assert make_dataset().digest() != reduced.digest()


def test_dataset_digest_detects_version_claim_change() -> None:
    renamed = EvalDataset(
        id="dataset-unit",
        version=Version("2.0.0"),
        cases=(make_case("case-001"), make_case("case-002", expected={"answer": 7})),
    )
    assert make_dataset().digest() != renamed.digest()


# --- EvalResult fail-closed 与 EvalScore ---


def test_eval_result_passed_fail_closed() -> None:
    report = make_report()
    assert report.results[0].passed is True
    empty = EvalResult(
        case_id="c",
        case_version=Version("1.0.0"),
        case_digest=Digest.of_bytes(b"x"),
        scope=EvalScope.UNIT,
        input_ref="input://c",
        scorer_findings=(),
    )
    assert empty.passed is False
    infra = EvalResult(
        case_id="c",
        case_version=Version("1.0.0"),
        case_digest=Digest.of_bytes(b"x"),
        scope=EvalScope.UNIT,
        input_ref="input://c",
        scorer_findings=(
            ScorerFinding(
                scorer_id="s",
                scorer_version=Version("1.0.0"),
                case_id="c",
                status=EvalFindingStatus.INFRA_ERROR,
                detail="backend down",
            ),
        ),
    )
    assert infra.passed is False


def test_eval_score_ratio() -> None:
    score = EvalScore(passed_cases=3, failed_cases=1, infra_error_cases=1, total_cases=5)
    assert score.pass_ratio == Decimal("0.6")
    empty = EvalScore(passed_cases=0, failed_cases=0, infra_error_cases=0, total_cases=0)
    assert empty.pass_ratio == Decimal("0")


# --- GateConfig versioning ---


def test_gate_config_digest_detects_threshold_change() -> None:
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


def test_gate_config_digest_detects_hard_invariant_change() -> None:
    soft = GateConfig(
        id="gate",
        version=Version("1.0.0"),
        rules=(ThresholdRule("digest_match"),),
    )
    hard = GateConfig(
        id="gate",
        version=Version("1.0.0"),
        rules=(ThresholdRule("digest_match", hard_invariant=True),),
    )
    assert soft.digest() != hard.digest()


def test_gate_config_validation() -> None:
    with pytest.raises(ValueError, match="hard invariant"):
        ThresholdRule("s", threshold=Decimal("0.9"), hard_invariant=True)
    with pytest.raises(ValueError, match="threshold out of range"):
        ThresholdRule("s", threshold=Decimal("1.5"))
    with pytest.raises(ValueError, match="min_pass_ratio"):
        GateConfig(id="g", version=Version("1.0.0"), min_pass_ratio=Decimal("1.2"))
    with pytest.raises(ValueError, match="duplicate rule"):
        GateConfig(
            id="g",
            version=Version("1.0.0"),
            rules=(ThresholdRule("s"), ThresholdRule("s")),
        )
