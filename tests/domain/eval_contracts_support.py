"""M11 eval 契约测试共享 helpers（非测试模块，pytest 不收集）。"""

from __future__ import annotations

from packages.domain.core import Digest, Version
from packages.domain.enums import QualityGateVerdict
from packages.domain.eval_result import (
    EvalFindingStatus,
    EvalReport,
    EvalResult,
    FrozenConditions,
    ScorerFinding,
)
from packages.domain.eval_spec import (
    EvalCase,
    EvalDataset,
    EvalScope,
    ScorerRef,
    case_digest,
)

_DEFAULT_EXPECTED = {"answer": 42}


def make_case(case_id: str = "case-001", expected: object = _DEFAULT_EXPECTED) -> EvalCase:
    return EvalCase(
        id=case_id,
        version=Version("1.0.0"),
        scope=EvalScope.UNIT,
        input_ref=f"input://{case_id}",
        expected=expected,
        scorer_refs=(ScorerRef("exact_match", Version("1.0.0")),),
    )


def make_dataset() -> EvalDataset:
    return EvalDataset(
        id="dataset-unit",
        version=Version("1.0.0"),
        cases=(
            make_case("case-001"),
            make_case("case-002", expected={"answer": 7}),
        ),
    )


def make_report(
    *,
    verdict: QualityGateVerdict = QualityGateVerdict.PASS,
    status: EvalFindingStatus = EvalFindingStatus.PASS,
    report_id: str = "report-1",
    generated_at: str = "2026-08-15T00:00:00Z",
) -> EvalReport:
    dataset = make_dataset()
    case = dataset.cases[0]
    frozen = FrozenConditions(
        dataset_id=dataset.id,
        dataset_version=dataset.version,
        dataset_digest=dataset.digest(),
        gate_config_id="gate-ci-v1",
        gate_config_version=Version("1.0.0"),
        gate_config_digest=Digest.of_bytes(b"gate-config"),
        system_version="0.4.0",
        scorer_versions={"exact_match": "1.0.0"},
        input_digests={case.input_ref: "sha256:" + "a" * 64},
    )
    result = EvalResult(
        case_id=case.id,
        case_version=case.version,
        case_digest=case_digest(case),
        scope=case.scope,
        input_ref=case.input_ref,
        scorer_findings=(
            ScorerFinding(
                scorer_id="exact_match",
                scorer_version=Version("1.0.0"),
                case_id=case.id,
                status=status,
                detail="detail",
            ),
        ),
    )
    return EvalReport(
        report_id=report_id,
        generated_at=generated_at,
        mode="OFFLINE_FAKE",
        scope=EvalScope.UNIT,
        gate_verdict=verdict,
        frozen_conditions=frozen,
        results=(result,),
    )
