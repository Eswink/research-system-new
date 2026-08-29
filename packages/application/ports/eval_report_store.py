"""EvalReportStore Port:verbatim report bytes + derived index(M15 WP3)。

Canonical truth 是报告原文字节(`report_digest` 可校验);index 列是可重建的
derived projection(有 rebuild-from-bodies 测试保证)。评测 verdict 的唯一
权威仍是 M11 `compute_verdict` / `compare_reports`——本 store 不产生判断。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class EvalReportIndexEntry:
    """从报告正文派生的索引(不含正文);body 可由 report_digest 反查。"""

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
    case_ids: tuple[str, ...] = field(default_factory=tuple)
    evaluator_identities: tuple[str, ...] = field(default_factory=tuple)
    verdict: str = ""
    pass_count: int = 0
    fail_count: int = 0
    infra_error_count: int = 0
    usage_ref: str | None = None
    cost_ref: str | None = None
    run_id: str | None = None
    recorded_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class StoredEvalReport:
    """存储记录:verbatim 正文 + 派生索引。"""

    index: EvalReportIndexEntry
    body: bytes

    def __post_init__(self) -> None:
        if not self.body:
            raise ValueError("stored eval report body must not be empty")
        if not self.index.report_digest:
            raise ValueError("stored eval report must carry report_digest")


@dataclass(frozen=True, slots=True)
class EvalReportQuery:
    """索引查询;全部条件可选,确定性排序。"""

    comparison_digest: str | None = None
    dataset_id: str | None = None
    run_id: str | None = None
    limit: int = 50

    def __post_init__(self) -> None:
        if self.limit < 1:
            raise ValueError("query limit must be >= 1")


@runtime_checkable
class EvalReportStore(Protocol):
    """报告存储;put 幂等(同 report_digest 覆盖同内容),查询确定性排序。"""

    def put(self, report: StoredEvalReport) -> None: ...

    def get(self, report_digest: str) -> StoredEvalReport | None: ...

    def query(self, query: EvalReportQuery) -> tuple[EvalReportIndexEntry, ...]: ...
