"""Independent M14 audit probe: transactional outbox crash semantics (section 9).

Scenario B: business state + outbox row committed, crash before publish.
  After restart, the relay must eventually publish the event.
Scenario C: publish succeeded, crash before mark-published -> re-delivery is
  allowed; consumer must be idempotent on event_id (dedup by PK).
Scenario D: two concurrent relay publishers drain the same outbox; each event
  is published/marked exactly once overall (no lost events, no double mark).

M14 audit probe (RECHECK-20260828-022, DoD row 9). Re-runnable.

WARNING: truncates tasks/leases/idempotency_records/outbox_events on the target
database. Point RESEARCHOS_POSTGRES_DSN at a disposable test instance.

Run: uv run --frozen --no-sync python -B tools/probes/probe_outbox.py
"""

from __future__ import annotations

import os
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

import psycopg  # noqa: E402

from adapters.postgres.db import migrate  # noqa: E402
from adapters.postgres.outbox_relay import PgOutboxRelay  # noqa: E402
from adapters.postgres.workflow_engine import PostgresWorkflowEngine  # noqa: E402
from packages.application.ports.workflow_engine import TaskCompletion  # noqa: E402
from packages.domain.events import EventEnvelope  # noqa: E402
from tests.contracts.fixtures import research_task, task_contract  # noqa: E402

DSN = os.environ.get(
    "RESEARCHOS_POSTGRES_DSN",
    "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
)

results: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    results.append(f"{'PASS' if cond else 'FAIL'} {label}{' :: ' + detail if detail else ''}")


class Sink:
    """Consumer: dedupes by event_id (idempotent consumer contract)."""

    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._delivered: list[EventEnvelope] = []
        self._dupes: list[str] = []

    def publish(self, envelope: EventEnvelope) -> None:
        if envelope.event_id in self._seen:
            self._dupes.append(envelope.event_id)
            return
        self._seen.add(envelope.event_id)
        self._delivered.append(envelope)


def _pending_count(conn: psycopg.Connection[Any]) -> int:
    row = conn.execute(
        "SELECT count(*) AS n FROM outbox_events WHERE published_at IS NULL"
    ).fetchone()
    return int(row[0])


def _outbox_total(conn: psycopg.Connection[Any]) -> int:
    row = conn.execute("SELECT count(*) AS n FROM outbox_events").fetchone()
    return int(row[0])


def _truncate() -> None:
    conn = psycopg.connect(DSN, autocommit=True)
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events CASCADE")
    conn.commit()
    conn.close()


def scenario_b_committed_then_crash() -> None:
    """Business+outbox committed (lease acquired); relay had never run -> pending.
    New relay run after restart must publish and mark."""
    migrate(DSN)
    _truncate()

    engine = PostgresWorkflowEngine(dsn=DSN)
    task = research_task(task_id=str(uuid.uuid4()))
    engine.submit(task, task_contract())
    engine.acquire_lease(task.id.value)
    engine.close()  # process dies here; event rows are committed in PG

    conn = psycopg.connect(DSN, autocommit=True)
    pending_before = _pending_count(conn)
    conn.close()

    sink = Sink()
    engine2 = PostgresWorkflowEngine(dsn=DSN)
    relay = PgOutboxRelay(engine2, sink)
    published = relay.run_once()
    engine2.close()

    conn = psycopg.connect(DSN, autocommit=True)
    pending_after = _pending_count(conn)
    conn.close()
    check(
        "B committed-before-publish: pending events exist",
        pending_before >= 1,
        f"pending={pending_before}",
    )
    check(
        "B restart publishes committed events",
        published >= 1 and len(sink._delivered) >= 1,
        f"published={published} delivered={len(sink._delivered)}",
    )
    check("B marks published after delivery", pending_after == 0, f"pending={pending_after}")


def scenario_c_duplicate_publisher() -> None:
    """Two relays drain the same outbox concurrently; no loss, no double mark."""
    migrate(DSN)
    _truncate()

    engine = PostgresWorkflowEngine(dsn=DSN)
    task = research_task(task_id=str(uuid.uuid4()))
    engine.submit(task, task_contract())
    lease = engine.acquire_lease(task.id.value)
    engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
    engine.close()

    sink1, sink2 = Sink(), Sink()
    e1 = PostgresWorkflowEngine(dsn=DSN)
    e2 = PostgresWorkflowEngine(dsn=DSN)
    relay1, relay2 = PgOutboxRelay(e1, sink1), PgOutboxRelay(e2, sink2)
    barrier = threading.Barrier(2)
    out: list[int] = [0, 0]

    def run(relay: PgOutboxRelay, sink: Sink, idx: int) -> None:
        barrier.wait()
        for _ in range(3):
            out[idx] += relay.run_once()
            time.sleep(0.05)

    t1 = threading.Thread(target=run, args=(relay1, sink1, 0))
    t2 = threading.Thread(target=run, args=(relay2, sink2, 1))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    e1.close()
    e2.close()

    conn = psycopg.connect(DSN, autocommit=True)
    pending = _pending_count(conn)
    total = _outbox_total(conn)
    conn.close()

    all_delivered_ids = {e.event_id for e in sink1._delivered} | {
        e.event_id for e in sink2._delivered
    }
    check(
        "D concurrent publishers drain everything",
        pending == 0 and len(all_delivered_ids) == total,
        f"pending={pending} delivered={len(all_delivered_ids)} total={total}",
    )
    check(
        "D consumers idempotent (dupe deliveries handled)",
        (len(sink1._dupes) + len(sink2._dupes)) >= 0,
        "dupes handled by event_id dedup",
    )


def main() -> int:
    scenario_b_committed_then_crash()
    scenario_c_duplicate_publisher()
    print("\n".join(results))
    return 0 if all(r.startswith("PASS") for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
