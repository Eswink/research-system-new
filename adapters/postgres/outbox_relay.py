"""PG outbox relay (WP-E1).

Polls PostgresWorkflowEngine.pending_outbox(), delivers each event via an
EventPublisher implementation (in production PG assembly this is the same
publisher the scheduler uses), and marks events published. At-least-once:
if crash happens after publish but before mark, re-delivery occurs and
the consumer must deduplicate by event_id.
"""

from __future__ import annotations

from typing import Any

from adapters.postgres.workflow_engine import PostgresWorkflowEngine


class PgOutboxRelay:
    """One-shot relay pass (idempotent): drains PG outbox and marks published.

    The caller (scheduler or composition lifespan) calls ``run_once`` in a
    loop; each pass is atomic per-event (pending → publish → mark).
    """

    def __init__(self, engine: PostgresWorkflowEngine, sink: Any) -> None:
        """``engine`` is the PG workflow engine (source of pending events);
        ``sink`` is any object with a ``publish(EventEnvelope)`` method
        (e.g. SqliteOutboxEventPublisher or a real EventPublisher adapter).
        """
        self._engine = engine
        self._sink = sink

    def run_once(self) -> int:
        """Drain all currently pending PG outbox events via sink.

        Returns the number of events published in this pass (0 when none).
        Per-event marking keeps incomplete passes safe on crash (scenario C).
        """
        pending = self._engine.pending_outbox()
        count = 0
        for envelope in pending:
            # Sink must be idempotent on event_id (EventPublisher contract).
            self._sink.publish(envelope)
            self._engine.mark_outbox_published((envelope.event_id,))
            count += 1
        return count
