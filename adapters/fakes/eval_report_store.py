"""EvalReportStore 的 Fake 实现(adapters/fakes)。

与真实 adapter 遵守相同 Port Contract:put 幂等(同 report_digest 覆盖同
内容)、get 精确反查、query 确定性排序;close 后抛 PermanentPortError
(通用 contract suite 语义;本 Port 非 fail-open)。
"""

from __future__ import annotations

from datetime import datetime, timezone

from adapters.fakes.base import FakeBase
from packages.application.ports.eval_report_store import (
    EvalReportIndexEntry,
    EvalReportQuery,
    StoredEvalReport,
)

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class FakeEvalReportStore(FakeBase):
    """内存存储;query 条件过滤 + (comparison_digest, recorded_at) 排序。"""

    def __init__(self) -> None:
        super().__init__("eval_report_store")
        self._reports: dict[str, StoredEvalReport] = {}

    def put(self, report: StoredEvalReport) -> None:
        self._enter("put", report.index.report_digest)
        self._reports[report.index.report_digest] = report
        self._record("put", report.index.report_digest)

    def get(self, report_digest: str) -> StoredEvalReport | None:
        self._enter("get", report_digest)
        found = self._reports.get(report_digest)
        self._record("get", report_digest, result="hit" if found else "miss")
        return found

    def query(self, query: EvalReportQuery) -> tuple[EvalReportIndexEntry, ...]:
        self._enter("query", query.dataset_id or "")
        selected = [
            report.index for report in self._reports.values() if _matches(report.index, query)
        ]
        selected.sort(key=lambda entry: (entry.comparison_digest, entry.recorded_at or _EPOCH))
        self._record("query", query.dataset_id or "", result=f"{len(selected)} hits")
        return tuple(selected[: query.limit])


def _matches(entry: EvalReportIndexEntry, query: EvalReportQuery) -> bool:
    if query.comparison_digest is not None and entry.comparison_digest != query.comparison_digest:
        return False
    if query.dataset_id is not None and entry.dataset_id != query.dataset_id:
        return False
    if query.run_id is not None and entry.run_id != query.run_id:
        return False
    return True
