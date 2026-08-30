"""PostgresWorkflowEngine telemetry note helpers(M15,拆分自 workflow_engine)。

best-effort、只读:telemetry off 时零开销;任何查询/解析失败静默返回,
绝不阻断业务路径(ADR-0026)。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from packages.application.observability.attributes import MetricKind, MetricName, MetricSample
from packages.application.observability.scope import record_metric_safely
from packages.application.ports.telemetry_sink import TelemetrySink


def seconds_since(created_at: object) -> float | None:
    """created_at → 现在的秒数;非 datetime 返回 None(telemetry 不阻断)。

    始终用挂钟,不读注入的业务时钟:观测旁观业务时间,不参与推进它。
    """
    if not isinstance(created_at, datetime):
        return None
    delta = datetime.now(timezone.utc) - created_at
    return max(0.0, delta.total_seconds())


def note_queue_lag(
    telemetry: TelemetrySink | None,
    conn: Any,
    task_id: str,
) -> None:
    """claim 时的排队时延(created_at → 挂钟);telemetry off 时零开销。"""
    if telemetry is None:
        return
    created_at = _created_at_of(conn, task_id)
    if created_at is None:
        return
    seconds = seconds_since(created_at)
    if seconds is None:
        return
    record_metric_safely(
        telemetry,
        lambda: MetricSample(
            name=MetricName.WORKFLOW_QUEUE_LAG_MS,
            kind=MetricKind.HISTOGRAM,
            value=seconds * 1000.0,
        ),
    )


def note_task_duration(
    telemetry: TelemetrySink | None,
    conn: Any,
    task_id: str,
) -> None:
    """任务总时长(created_at → complete);telemetry off 时零开销。"""
    if telemetry is None:
        return
    created_at = _created_at_of(conn, task_id)
    if created_at is None:
        return
    seconds = seconds_since(created_at)
    if seconds is None:
        return
    record_metric_safely(
        telemetry,
        lambda: MetricSample(
            name=MetricName.WORKFLOW_TASK_DURATION_MS,
            kind=MetricKind.HISTOGRAM,
            value=seconds * 1000.0,
        ),
    )


def _created_at_of(conn: Any, task_id: str) -> object | None:
    """best-effort 读取 created_at(telemetry 专用,不阻断业务)。"""
    try:
        row = conn.execute("SELECT created_at FROM tasks WHERE task_id = %s", (task_id,)).fetchone()
    except Exception:
        return None
    if row is None:
        return None
    if isinstance(row, dict):
        return row.get("created_at")
    return row[0] if isinstance(row, (tuple, list)) else None
