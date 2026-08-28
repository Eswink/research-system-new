"""Independent M14 audit probe: scheduled lease recovery (section 7).

Runs the REAL LeaseRecoveryScheduler (services/api/scheduler.py) — the same
code wired in services/api/app.py lifespan — with a short interval, against a
task whose lease has expired. Verifies the periodic mechanism (not a manual
recover_expired_leases() call) recovers the task, emits TASK_RETRY_SCHEDULED,
and does not double-recover on repeated scheduler passes. Also runs TWO
concurrent scheduler instances to verify no double-recovery / no conflict.

M14 audit probe (RECHECK-20260828-022, DoD row 7). Re-runnable.

Prerequisites: a reachable PostgreSQL instance. Override the default local
docker DSN with RESEARCHOS_POSTGRES_DSN. Uses real TTL expiry plus scheduler
passes, so a run takes roughly 30 seconds.

Run: uv run --frozen --no-sync python -B tools/probes/probe_scheduled_recovery.py
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
from packages.application.ports.workflow_engine import TaskCompletion  # noqa: E402
from packages.domain.core import ID  # noqa: E402
from packages.domain.tasks import (  # noqa: E402
    AcceptanceCriterion,
    AcceptanceCriterionType,
    ResearchTask,
    TaskContract,
)
from services.api.scheduler import LeaseRecoveryScheduler  # noqa: E402

DSN = os.environ.get(
    "RESEARCHOS_POSTGRES_DSN",
    "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
)
TTL = 3

results: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    results.append(f"{'PASS' if cond else 'FAIL'} {label}{' :: ' + detail if detail else ''}")


def _make_task(task_id: str) -> tuple[ResearchTask, TaskContract]:
    task = ResearchTask(
        id=ID(task_id),
        run_id=ID(str(uuid.uuid4())),
        phase_run_id=ID(str(uuid.uuid4())),
        contract_id="probe-contract",
        assigned_agent_id="agent-a",
        status="CREATED",
        idempotency_key=f"idem-{task_id}",
    )
    contract = TaskContract(
        id="probe-contract",
        version="1.0",
        purpose="audit scheduled recovery probe",
        required_capabilities=["workspace.read"],
        acceptance_criteria=[
            AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)
        ],
    )
    return task, contract


def _state(task_id: str) -> dict[str, object]:
    conn = psycopg.connect(DSN, autocommit=True, row_factory=dict_row)
    row = conn.execute(
        "SELECT status FROM tasks WHERE task_id=%s", (task_id,)
    ).fetchone()
    n_leases = conn.execute(
        "SELECT count(*) AS n FROM leases WHERE task_id=%s", (task_id,)
    ).fetchone()["n"]
    n_retry = conn.execute(
        "SELECT count(*) AS n FROM outbox_events"
        " WHERE envelope_json->>'task_id'=%s"
        " AND envelope_json->>'event_type'='task.retry_scheduled'",
        (task_id,),
    ).fetchone()["n"]
    conn.close()
    return {
        "status": row["status"] if row else None,
        "leases": n_leases,
        "retry_events": n_retry,
    }


def scenario_single_scheduler() -> None:
    task_id = str(uuid.uuid4())
    migrate(DSN)
    engine = PostgresWorkflowEngine(dsn=DSN, lease_ttl_seconds=TTL)
    task, contract = _make_task(task_id)
    engine.submit(task, contract)
    engine.acquire_lease(task_id)
    engine.close()

    # Wait for real expiry, then let the periodic scheduler do its job.
    time.sleep(TTL + 2)
    sched_engine = PostgresWorkflowEngine(dsn=DSN, lease_ttl_seconds=TTL)
    sched = LeaseRecoveryScheduler(sched_engine, interval_seconds=1.0)
    sched.start()
    deadline = time.time() + 10
    st: dict[str, object] = {}
    while time.time() < deadline:
        st = _state(task_id)
        if st["status"] == "QUEUED" and st["leases"] == 0 and st["retry_events"] >= 1:
            break
        time.sleep(0.5)
    sched.stop()
    sched_engine.close()

    check("scheduler auto-recovers expired lease",
          st.get("status") == "QUEUED" and st.get("leases") == 0,
          f"state={st}")
    check("recovery emits retry_scheduled event", st.get("retry_events", 0) >= 1,
          f"retry_events={st.get('retry_events')}")
    # Task is now claimable by a worker again
    w = PostgresWorkflowEngine(dsn=DSN, lease_ttl_seconds=TTL)
    lease = w.acquire_lease(task_id)
    check("task claimable after scheduled recovery", lease is not None, f"lease={lease.lease_id}")
    w.complete(lease, TaskCompletion(task_id=task_id, outcome="SUCCEEDED"))
    w.close()


def scenario_two_schedulers_no_double_recover() -> None:
    task_id = str(uuid.uuid4())
    migrate(DSN)
    engine = PostgresWorkflowEngine(dsn=DSN, lease_ttl_seconds=TTL)
    task, contract = _make_task(task_id)
    engine.submit(task, contract)
    engine.acquire_lease(task_id)
    engine.close()

    time.sleep(TTL + 2)
    e1 = PostgresWorkflowEngine(dsn=DSN, lease_ttl_seconds=TTL)
    e2 = PostgresWorkflowEngine(dsn=DSN, lease_ttl_seconds=TTL)
    s1 = LeaseRecoveryScheduler(e1, interval_seconds=1.0)
    s2 = LeaseRecoveryScheduler(e2, interval_seconds=1.0)
    s1.start()
    s2.start()
    deadline = time.time() + 12
    st: dict[str, object] = {}
    while time.time() < deadline:
        st = _state(task_id)
        if st["status"] == "QUEUED" and st["leases"] == 0:
            break
        time.sleep(0.5)
    time.sleep(3)  # let both schedulers run several more passes
    st = _state(task_id)
    s1.stop()
    s2.stop()
    e1.close()
    e2.close()

    check("two concurrent schedulers recover exactly once",
          st["status"] == "QUEUED" and st["leases"] == 0 and st["retry_events"] == 1,
          f"state={st}")


def main() -> int:
    scenario_single_scheduler()
    scenario_two_schedulers_no_double_recover()
    print("\n".join(results))
    return 0 if all(r.startswith("PASS") for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
