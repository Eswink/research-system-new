"""M15 EvalReportStore port: canonical report bytes plus derived index.

The report body is canonical truth.  Every index value is a derived projection,
not an alternative verdict source.  A report is immutable after its first
successful write: duplicate ``report_digest`` writes are idempotent no-ops so
``recorded_at`` cannot be used to rewrite trend direction.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable

from packages.domain.enums import QualityGateVerdict
from packages.domain.eval_report_codec import report_from_dict


@dataclass(frozen=True, slots=True)
class EvalReportIndexEntry:
    """Body-derived report index with immutable ingestion ordering metadata."""

    report_digest: str
    comparison_digest: str
    dataset_id: str
    dataset_version: str
    dataset_digest: str
    gate_config_id: str
    gate_config_version: str
    gate_config_digest: str
    scorer_versions: tuple[tuple[str, str], ...]
    system_version: str
    verdict: QualityGateVerdict
    recorded_at: datetime
    rubric_digest: str | None = None
    case_ids: tuple[str, ...] = field(default_factory=tuple)
    evaluator_identities: tuple[str, ...] = field(default_factory=tuple)
    pass_count: int = 0
    fail_count: int = 0
    infra_error_count: int = 0
    reviewer_failure_count: int = 0
    usage_ref: str | None = None
    cost_ref: str | None = None
    run_id: str | None = None

    def __post_init__(self) -> None:
        if not self.report_digest:
            raise ValueError("eval report index requires report_digest")
        if not isinstance(self.verdict, QualityGateVerdict):
            raise ValueError("eval report index verdict must be a QualityGateVerdict")
        if self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None:
            raise ValueError("eval report index recorded_at must be timezone-aware")
        counts = (
            self.pass_count,
            self.fail_count,
            self.infra_error_count,
            self.reviewer_failure_count,
        )
        if any(value < 0 for value in counts):
            raise ValueError("eval report index counts must not be negative")


@dataclass(frozen=True, slots=True)
class StoredEvalReport:
    """Verbatim report body and its derived projection.

    Construction validates the canonical body before any adapter persists it.
    This stops an arbitrary index digest or verdict from being used to publish
    a result different from the report that was actually evaluated.
    """

    index: EvalReportIndexEntry
    body: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.body, bytes) or not self.body:
            raise ValueError("stored eval report body must be non-empty bytes")
        try:
            decoded = json.loads(self.body.decode("utf-8"))
            if not isinstance(decoded, dict):
                raise ValueError("report body must be a JSON object")
            report = report_from_dict(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as error:
            raise ValueError("stored eval report body is not a valid EvalReport") from error
        if str(report.digest()) != self.index.report_digest:
            raise ValueError("stored eval report digest does not match its body")
        if report.gate_verdict is not self.index.verdict:
            raise ValueError("stored eval report verdict does not match its body")


@dataclass(frozen=True, slots=True)
class EvalReportQuery:
    """Derived-index query.  Results are newest-first and bounded by ``limit``."""

    comparison_digest: str | None = None
    dataset_id: str | None = None
    run_id: str | None = None
    limit: int = 50

    def __post_init__(self) -> None:
        if self.limit < 1:
            raise ValueError("query limit must be >= 1")


@dataclass(frozen=True, slots=True)
class EvalReportQueryPage:
    """Bounded report query plus an explicit indication that rows were omitted."""

    entries: tuple[EvalReportIndexEntry, ...]
    truncated: bool = False


@runtime_checkable
class EvalReportStore(Protocol):
    """Immutable report store with deterministic newest-first queries."""

    def put(self, report: StoredEvalReport) -> None: ...

    def get(self, report_digest: str) -> StoredEvalReport | None: ...

    def query(self, query: EvalReportQuery) -> tuple[EvalReportIndexEntry, ...]: ...

    def query_page(self, query: EvalReportQuery) -> EvalReportQueryPage: ...
