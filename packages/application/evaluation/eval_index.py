"""EvalReport body encoding and derived-index validation for M15 operations."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from packages.application.ports.eval_report_store import EvalReportIndexEntry, StoredEvalReport
from packages.domain.eval_report_codec import report_from_dict, report_to_dict
from packages.domain.eval_result import EvalFindingStatus, EvalReport


def encode_report_body(report: EvalReport) -> bytes:
    """Encode a report once in its deterministic, verbatim storage form."""
    return json.dumps(
        report_to_dict(report),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def decode_report_body(body: bytes) -> EvalReport:
    """Decode stored bytes fail-closed through the Domain report codec."""
    decoded = json.loads(body.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("stored eval report body must be a JSON object")
    return report_from_dict(decoded)


def build_index_entry(
    report: EvalReport,
    *,
    run_id: str | None = None,
    usage_ref: str | None = None,
    cost_ref: str | None = None,
    recorded_at: datetime | None = None,
) -> EvalReportIndexEntry:
    """Project every report-owned index value directly from its canonical body."""
    frozen = report.frozen_conditions
    recorded = recorded_at or datetime.now(timezone.utc)
    pass_count, fail_count, infra_error_count = _finding_counts(report)
    return EvalReportIndexEntry(
        report_digest=str(report.digest()),
        comparison_digest=str(frozen.comparison_digest()),
        dataset_id=frozen.dataset_id,
        dataset_version=frozen.dataset_version.text,
        dataset_digest=str(frozen.dataset_digest),
        gate_config_id=frozen.gate_config_id,
        gate_config_version=frozen.gate_config_version.text,
        gate_config_digest=str(frozen.gate_config_digest),
        scorer_versions=tuple(sorted(frozen.scorer_versions.items())),
        system_version=frozen.system_version,
        verdict=report.gate_verdict,
        recorded_at=recorded,
        rubric_digest=str(frozen.rubric_digest) if frozen.rubric_digest else None,
        case_ids=tuple(result.case_id for result in report.results),
        evaluator_identities=_evaluator_identities(report),
        pass_count=pass_count,
        fail_count=fail_count,
        infra_error_count=infra_error_count,
        reviewer_failure_count=_reviewer_failure_count(report),
        usage_ref=usage_ref,
        cost_ref=cost_ref,
        run_id=run_id,
    )


def index_matches_body(index: EvalReportIndexEntry, report: EvalReport) -> bool:
    """Verify an index by rebuilding it from its report body and stored metadata."""
    expected = build_index_entry(
        report,
        run_id=index.run_id,
        usage_ref=index.usage_ref,
        cost_ref=index.cost_ref,
        recorded_at=index.recorded_at,
    )
    return index == expected


def stored_from_report(
    report: EvalReport,
    *,
    run_id: str | None = None,
    usage_ref: str | None = None,
    cost_ref: str | None = None,
    recorded_at: datetime | None = None,
) -> StoredEvalReport:
    """Create a validated report storage record from Domain truth."""
    return StoredEvalReport(
        index=build_index_entry(
            report,
            run_id=run_id,
            usage_ref=usage_ref,
            cost_ref=cost_ref,
            recorded_at=recorded_at,
        ),
        body=encode_report_body(report),
    )


def _finding_counts(report: EvalReport) -> tuple[int, int, int]:
    passed = 0
    failed = 0
    infra = 0
    for result in report.results:
        for finding in result.scorer_findings:
            if finding.status is EvalFindingStatus.PASS:
                passed += 1
            elif finding.status is EvalFindingStatus.FAIL:
                failed += 1
            else:
                infra += 1
    return passed, failed, infra


def _evaluator_identities(report: EvalReport) -> tuple[str, ...]:
    identities = {
        finding.model_identity
        for result in report.results
        for finding in result.reviewer_findings
        if finding.model_identity
    }
    return tuple(sorted(identities))


def _reviewer_failure_count(report: EvalReport) -> int:
    return sum(
        1
        for result in report.results
        for finding in result.reviewer_findings
        if finding.failure is not None
    )
