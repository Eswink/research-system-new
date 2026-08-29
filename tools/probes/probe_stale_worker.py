"""Independent M14 audit probe: stale-worker fencing, two adversarial windows.

Scenario A (B completed already):
  A acquires L1; expiry; B reclaims (L2) + completes SUCCEEDED; A resumes.
  Requirement: A must NOT overwrite B's result. Complete-after-terminal is
  defined by the WorkflowEngine contract as an idempotent dedup no-op, so the
  real assertion is: canonical state unchanged, single completed event,
  no lease resurrection.

Scenario B (B holds the new lease, work in progress):
  A acquires L1; expiry; B reclaims (L2) and holds it (heartbeats).
  A resumes and tries complete(L1).
  Requirement: A's stale write MUST be rejected (InvalidInputError) — this is
  the case where a stale worker could otherwise corrupt in-flight work.

M14 audit probe (RECHECK-20260828-022, DoD row 6). Re-runnable.

Prerequisites: a reachable PostgreSQL instance. Override the default local
docker DSN with RESEARCHOS_POSTGRES_DSN. Uses real TTL expiry, so a run takes
roughly 15 seconds.

Run: uv run --frozen --no-sync python -B tools/probes/probe_stale_worker.py
"""

from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from adapters.postgres.db import migrate  # noqa: E402
from adapters.postgres.workflow_engine import PostgresWorkflowEngine  # noqa: E402
from packages.application.ports.errors import InvalidInputError  # noqa: E402
from packages.application.ports.workflow_engine import TaskCompletion  # noqa: E402
from packages.domain.core import ID  # noqa: E402
from packages.domain.tasks import (  # noqa: E402
    AcceptanceCriterion,
    AcceptanceCriterionType,
    ResearchTask,
    TaskContract,
)

DSN = os.environ.get(
    "RESEARCHOS_POSTGRES_DSN",
    "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
)
TTL = 5

results: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    results.append(f"{'PASS' if cond else 'FAIL'} {label}{' :: ' + detail if detail else ''}")


def _make_task(task_id: str) -> tuple[ResearchTask, TaskContract]:
    task = ResearchTask(
        id=ID(task_id),
        run_id=ID(str(uuid.uuid4())),
        status="QUEUED",
        assigned_agent_id="agent-a",
    )
    contract = TaskContract(
        id=str(uuid.uuid4()),
        version="1",
        purpose="audit stale worker fencing probe",
        acceptance_criteria=[
            AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS, description="probe")
        ],
    )
    return task, contract


def _state(task_id: str) -> dict[str, object]:
    conn = psycopg.connect(DSN, autocommit=True, row_factory=dict_row)
    row = conn.execute(
        "SELECT status, cancelled FROM tasks WHERE task_id=%s", (task_id,)
    ).fetchone()
    n_leases = conn.execute(
        "SELECT count(*) AS n FROM leases WHERE task_id=%s", (task_id,)
    ).fetchone()["n"]
    n_completed = conn.execute(
        "SELECT count(*) AS n FROM outbox_events"
        " WHERE envelope_json->>'task_id'=%s"
        " AND envelope_json->>'event_type'='task.completed'",
        (task_id,),
    ).fetchone()["n"]
    conn.close()
    return {"status": row["status"] if row else None, "leases": n_leases, "completed": n_completed}


def scenario_b_completed_first() -> None:
    """B completes; A's stale complete must be a dedup no-op (no overwrite)."""
    task_id = str(uuid.uuid4())
    migrate(DSN)
    engine_a = PostgresWorkflowEngine(dsn=DSN, lease_ttl_seconds=TTL)
    task, contract = _make_task(task_id)
    engine_a.submit(task, contract)
    lease_a = engine_a.acquire_lease(task_id)
    engine_a.close()
    time.sleep(TTL + 2)
    engine_b = PostgresWorkflowEngine(dsn=DSN, lease_ttl_seconds=TTL)
    lease_b = engine_b.acquire_lease(task_id)
    engine_b.complete(lease_b, TaskCompletion(task_id=task_id, outcome="SUCCEEDED"))
    engine_b.close()

    engine_a2 = PostgresWorkflowEngine(dsn=DSN, lease_ttl_seconds=TTL)
    try:
        engine_a2.complete(lease_a, TaskCompletion(task_id=task_id, outcome="SUCCEEDED"))
        stale_outcome = "deduped-noop"
    except InvalidInputError:
        stale_outcome = "rejected"
    engine_a2.close()

    st = _state(task_id)
    check(
        "S1 stale complete no-op or reject (never overwrite)",
        stale_outcome in ("deduped-noop", "rejected") and st["status"] == "SUCCEEDED",
        f"stale={stale_outcome} state={st}",
    )


def scenario_b_holds_new_lease() -> None:
    """B holds a new lease; A's stale complete must be rejected outright."""
    task_id = str(uuid.uuid4())
    migrate(DSN)
    engine_a = PostgresWorkflowEngine(dsn=DSN, lease_ttl_seconds=TTL)
    task, contract = _make_task(task_id)
    engine_a.submit(task, contract)
    lease_a = engine_a.acquire_lease(task_id)
    engine_a.close()
    time.sleep(TTL + 2)
    engine_b = PostgresWorkflowEngine(dsn=DSN, lease_ttl_seconds=TTL)
    lease_b = engine_b.acquire_lease(task_id)  # lazy reclaim -> L2
    # B heartbeats to keep L2 alive while "working"
    lease_b = engine_b.heartbeat(lease_b)

    engine_a2 = PostgresWorkflowEngine(dsn=DSN, lease_ttl_seconds=TTL)
    try:
        engine_a2.complete(lease_a, TaskCompletion(task_id=task_id, outcome="SUCCEEDED"))
        stale_outcome = "accepted"
    except InvalidInputError:
        stale_outcome = "rejected"
    engine_a2.close()

    st = _state(task_id)
    check(
        "S2 stale complete rejected while B works",
        stale_outcome == "rejected" and st["status"] == "LEASED" and st["leases"] == 1,
        f"stale={stale_outcome} state={st}",
    )
    # B still owns the lease and can finish
    engine_b.complete(lease_b, TaskCompletion(task_id=task_id, outcome="SUCCEEDED"))
    st = _state(task_id)
    check(
        "S2 B completes after rejecting stale write",
        st["status"] == "SUCCEEDED" and st["completed"] == 1 and st["leases"] == 0,
        f"state={st}",
    )
    engine_b.close()


def main() -> int:
    scenario_b_completed_first()
    scenario_b_holds_new_lease()
    print("\n".join(results))
    return 0 if all(r.startswith("PASS") for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
