"""Worker helper: run one PG engine action in a subprocess (true cross-process).

Usage: python -B worker_cross_process.py <action> [task_id] [lease_ttl]
Actions:
  seed            migrate + submit a fresh task, print its id
  acquire         acquire_lease(task_id), print lease_id
  renew           heartbeat(existing lease printed on stdout) — not used
  recover         recover_expired_leases(), print count
  claim-complete  acquire + complete SUCCEEDED, print result
  restore-status  print task status from canonical table

Every worker opens its own psycopg connection (independent process/DSN).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, r"d:\research-system")

from adapters.postgres.db import migrate  # noqa: E402
from adapters.postgres.workflow_engine import PostgresWorkflowEngine  # noqa: E402
from packages.application.ports.workflow_engine import TaskCompletion  # noqa: E402
from tests.contracts.fixtures import research_task, task_contract  # noqa: E402


def dsn() -> str:
    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
    )


def main() -> None:
    action = sys.argv[1]
    ttl = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    engine = PostgresWorkflowEngine(dsn=dsn(), lease_ttl_seconds=ttl)
    pid = os.getpid()
    try:
        if action == "seed":
            migrate(dsn())
            task = research_task()
            engine.submit(task, task_contract())
            print(f"SEED pid={pid} task={task.id.value}", flush=True)
        elif action == "acquire":
            task_id = sys.argv[2]
            lease = engine.acquire_lease(task_id)
            print(f"ACQUIRE pid={pid} lease={lease.lease_id}", flush=True)
        elif action == "recover":
            n = engine.recover_expired_leases()
            print(f"RECOVER pid={pid} n={n}", flush=True)
        elif action == "claim-complete":
            task_id = sys.argv[2]
            lease = engine.acquire_lease(task_id)
            engine.complete(lease, TaskCompletion(task_id=task_id, outcome="SUCCEEDED"))
            print(f"COMPLETE pid={pid} lease={lease.lease_id}", flush=True)
        elif action == "status":
            task_id = sys.argv[2]
            import psycopg
            from psycopg.rows import dict_row

            conn = psycopg.connect(dsn(), autocommit=True, row_factory=dict_row)
            row = conn.execute("SELECT status FROM tasks WHERE task_id=%s", (task_id,)).fetchone()
            conn.close()
            print(f"STATUS pid={pid} status={row['status'] if row else 'MISSING'}", flush=True)
    finally:
        engine.close()


if __name__ == "__main__":
    main()
