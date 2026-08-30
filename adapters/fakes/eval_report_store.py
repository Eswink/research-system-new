"""In-memory EvalReportStore adapter with immutable first-write semantics."""

from __future__ import annotations

from datetime import datetime, timezone

from adapters.fakes.base import FakeBase
from packages.application.ports.eval_report_store import (
    EvalReportIndexEntry,
    EvalReportQuery,
    EvalReportQueryPage,
    StoredEvalReport,
)

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class FakeEvalReportStore(FakeBase):
    """Deterministic test adapter matching the production store contract."""

    def __init__(self) -> None:
        super().__init__("eval_report_store")
        self._reports: dict[str, StoredEvalReport] = {}

    def put(self, report: StoredEvalReport) -> None:
        self._enter("put", report.index.report_digest)
        self._reports.setdefault(report.index.report_digest, report)
        self._record("put", report.index.report_digest)

    def get(self, report_digest: str) -> StoredEvalReport | None:
        self._enter("get", report_digest)
        found = self._reports.get(report_digest)
        self._record("get", report_digest, result="hit" if found else "miss")
        return found

    def query(self, query: EvalReportQuery) -> tuple[EvalReportIndexEntry, ...]:
        return self.query_page(query).entries

    def query_page(self, query: EvalReportQuery) -> EvalReportQueryPage:
        self._enter("query", query.dataset_id or "")
        selected = [
            report.index for report in self._reports.values() if _matches(report.index, query)
        ]
        selected.sort(
            key=lambda entry: (entry.recorded_at or _EPOCH, entry.report_digest),
            reverse=True,
        )
        truncated = len(selected) > query.limit
        entries = tuple(selected[: query.limit])
        self._record("query", query.dataset_id or "", result=f"{len(entries)} hits")
        return EvalReportQueryPage(entries=entries, truncated=truncated)


def _matches(entry: EvalReportIndexEntry, query: EvalReportQuery) -> bool:
    if query.comparison_digest is not None and entry.comparison_digest != query.comparison_digest:
        return False
    if query.dataset_id is not None and entry.dataset_id != query.dataset_id:
        return False
    if query.run_id is not None and entry.run_id != query.run_id:
        return False
    return True
