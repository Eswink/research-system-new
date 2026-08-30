"""PG outbox relay (WP-E1).

Polls PostgresWorkflowEngine.pending_outbox(), delivers each event via an
EventPublisher implementation (in production PG assembly this is the same
publisher the scheduler uses), and marks events published. At-least-once:
if crash happens after publish but before mark, re-delivery occurs and
the consumer must deduplicate by event_id.

M15 观测:backlog 与 drained 计数经可选 telemetry 上报(OUTBOX_BACKLOG /
OUTBOX_DRAINED;闭集 metric,无业务 id label)。
"""

from __future__ import annotations

from typing import Any

from adapters.postgres.workflow_engine import PostgresWorkflowEngine
from packages.application.observability.attributes import MetricKind, MetricName, MetricSample
from packages.application.observability.scope import record_metric_safely
from packages.application.ports.telemetry_sink import TelemetrySink


class PgOutboxRelay:
    """One-shot relay pass (idempotent): drains PG outbox and marks published.

    The caller (scheduler or composition lifespan) calls ``run_once`` in a
    loop; each pass is atomic per-event (pending → publish → mark).
    """

    def __init__(
        self,
        engine: PostgresWorkflowEngine,
        sink: Any,
        *,
        telemetry: TelemetrySink | None = None,
    ) -> None:
        """``engine`` is the PG workflow engine (source of pending events);
        ``sink`` is any object with a ``publish(EventEnvelope)`` method
        (e.g. SqliteOutboxEventPublisher or a real EventPublisher adapter).
        """
        self._engine = engine
        self._sink = sink
        self._telemetry = telemetry

    def run_once(self) -> int:
        """Drain all currently pending PG outbox events via sink.

        Returns the number of events published in this pass (0 when none).
        Per-event marking keeps incomplete passes safe on crash (scenario C).

        Telemetry ordering matters: the backlog metric is recorded **after** the
        drain loop. Recording it first meant a raising sink skipped delivery for
        the whole pass — telemetry silently becoming an outbox availability
        dependency (M15 re-audit finding).
        """
        pending = self._engine.pending_outbox()
        count = 0
        for envelope in pending:
            # Sink must be idempotent on event_id (EventPublisher contract).
            self._sink.publish(envelope)
            self._engine.mark_outbox_published((envelope.event_id,))
            count += 1
        record_metric_safely(
            self._telemetry,
            lambda: MetricSample(
                name=MetricName.OUTBOX_BACKLOG,
                kind=MetricKind.HISTOGRAM,
                value=len(pending),
            ),
        )
        if count:
            record_metric_safely(
                self._telemetry,
                lambda: MetricSample(
                    name=MetricName.OUTBOX_DRAINED, kind=MetricKind.COUNTER, value=count
                ),
            )
        return count
