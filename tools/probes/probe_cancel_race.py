"""Independent M14 audit probe: cancel vs completion vs expiry races (section 11).

- cancel then stale complete: CANCELLED must never be overwritten to COMPLETED.
- cancel vs complete concurrent (real subprocess): exactly one legal outcome.
- cancel then recover: recovered lease must not resurrect a cancelled task.

M14 audit probe (RECHECK-20260828-022, DoD row 11). Re-runnable.

WARNING: truncates tasks/leases/idempotency_records/outbox_events on the target
database. Point RESEARCHOS_POSTGRES_DSN at a disposable test instance.

Run: uv run --frozen --no-sync python -B tools/probes/probe_cancel_race.py
"""

from __future__ import annotations

import os
import subprocess
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
from tests.contracts.fixtures import research_task, task_contract  # noqa: E402

DSN = os.environ.get(
    "RESEARCHOS_POSTGRES_DSN",
    "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
)
_CHILD_BOOTSTRAP = f"import sys; sys.path.insert(0, r'{_REPO_ROOT}');"

results: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    results.append(f"{'PASS' if cond else 'FAIL'} {label}{' :: ' + detail if detail else ''}")


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
    return {
        "status": row["status"] if row else None,
        "cancelled": row["cancelled"] if row else None,
        "leases": n_leases,
        "completed": n_completed,
    }


def _clean() -> None:
    migrate(DSN)
    conn = psycopg.connect(DSN, autocommit=True)
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events CASCADE")
    conn.commit()
    conn.close()


def scenario_cancel_then_stale_complete() -> None:
    """CANCELLED must not be overwritten to COMPLETED by a stale worker."""
    _clean()
    task_id = str(uuid.uuid4())
    engine = PostgresWorkflowEngine(dsn=DSN)
    task = research_task(task_id=task_id)
    engine.submit(task, task_contract())
    lease = engine.acquire_lease(task.id.value)
    engine.cancel(task.id.value)
    try:
        engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
        stale = "accepted"
    except InvalidInputError:
        stale = "rejected"
    st = _state(task.id.value)
    check(
        "cancel-then-complete: stale complete rejected",
        stale == "rejected" and st["status"] == "CANCELLED" and st["cancelled"] is True,
        f"stale={stale} state={st}",
    )
    engine.close()


def scenario_cancel_then_recover() -> None:
    """Recovery must not resurrect a cancelled task."""
    _clean()
    task_id = str(uuid.uuid4())
    engine = PostgresWorkflowEngine(dsn=DSN, lease_ttl_seconds=2)
    task = research_task(task_id=task_id)
    engine.submit(task, task_contract())
    engine.acquire_lease(task.id.value)
    engine.cancel(task.id.value)
    engine.close()
    time.sleep(3)  # let the lease expire in real time
    engine2 = PostgresWorkflowEngine(dsn=DSN)
    n = engine2.recover_expired_leases()
    st = _state(task.id.value)
    check(
        "cancel-then-recover: no resurrection",
        st["status"] == "CANCELLED" and st["leases"] == 0,
        f"recovered={n} state={st}",
    )
    engine2.close()


def _completer_script(task_id: str) -> str:
    return (
        _CHILD_BOOTSTRAP + "from adapters.postgres.workflow_engine import PostgresWorkflowEngine;"
        "from tests.contracts.fixtures import task_contract;"
        "from packages.application.ports.workflow_engine import TaskCompletion;"
        "from packages.domain.tasks import ResearchTask;"
        "from packages.domain.core import ID;"
        "import uuid as _u;"
        f"e=PostgresWorkflowEngine(dsn=r'{DSN}');"
        f"t_id='{task_id}';"
        "t=ResearchTask(id=ID(t_id), run_id=ID(str(_u.uuid4())),"
        " phase_run_id=ID(str(_u.uuid4())), contract_id='research',"
        " assigned_agent_id='agent-1', status='CREATED', idempotency_key=f'idem-{t_id}');"
        "e.submit(t, task_contract());"
        "l=e.acquire_lease(t.id.value);"
        "e.complete(l, TaskCompletion(task_id=t.id.value, outcome='SUCCEEDED'));"
        "print('DONE', flush=True); e.close()"
    )


def _canceller_script(task_id: str) -> str:
    return (
        _CHILD_BOOTSTRAP + "from adapters.postgres.workflow_engine import PostgresWorkflowEngine;"
        "from tests.contracts.fixtures import task_contract;"
        "from packages.domain.tasks import ResearchTask;"
        "from packages.domain.core import ID;"
        "import uuid as _u;"
        f"e=PostgresWorkflowEngine(dsn=r'{DSN}');"
        f"t_id='{task_id}';"
        "t=ResearchTask(id=ID(t_id), run_id=ID(str(_u.uuid4())),"
        " phase_run_id=ID(str(_u.uuid4())), contract_id='research',"
        " assigned_agent_id='agent-2', status='CREATED', idempotency_key=f'idem-{t_id}');"
        "e.submit(t, task_contract());"
        f"e.cancel('{task_id}');"
        "print('CANCELLED', flush=True); e.close()"
    )


def scenario_concurrent_cancel_and_complete() -> None:
    """Two subprocesses race cancel vs complete; final state must be one legal
    outcome (CANCELLED or SUCCEEDED), never both, never a mix.

    Both children must exit cleanly. A crashing child would otherwise make the
    race trivially "legal" while never exercising the contended path at all.
    """
    for iteration in range(3):
        _clean()
        task_id = str(uuid.uuid4())
        env = os.environ.copy()
        env["PYTHONPATH"] = str(_REPO_ROOT)
        pa = subprocess.Popen(
            [sys.executable, "-B", "-c", _completer_script(task_id)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        pb = subprocess.Popen(
            [sys.executable, "-B", "-c", _canceller_script(task_id)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        out_a, err_a = pa.communicate(timeout=60)
        out_b, err_b = pb.communicate(timeout=60)
        # A contended race requires BOTH sides to have actually run. Either side
        # may legally lose on a domain error, but neither may crash on import or
        # a NameError-style defect.
        check(
            f"iter{iteration} completer child ran",
            pa.returncode == 0 or "InvalidInputError" in err_a,
            f"rc={pa.returncode} out={out_a.strip()} err={err_a.strip()[-300:]}",
        )
        check(
            f"iter{iteration} canceller child ran",
            pb.returncode == 0 or "InvalidInputError" in err_b,
            f"rc={pb.returncode} out={out_b.strip()} err={err_b.strip()[-300:]}",
        )

        st = _state(task_id)
        legal = st["status"] in ("SUCCEEDED", "CANCELLED")
        not_both = not (st["status"] == "SUCCEEDED" and st["cancelled"] is True)
        if st["status"] == "CANCELLED":
            ok = st["completed"] == 0
        else:
            ok = st["completed"] == 1 and st["leases"] == 0
        check(
            f"iter{iteration} cancel-vs-complete race: legal outcome",
            legal and not_both and ok,
            f"state={st}",
        )


def main() -> int:
    scenario_cancel_then_stale_complete()
    scenario_cancel_then_recover()
    scenario_concurrent_cancel_and_complete()
    print("\n".join(results))
    return 0 if all(r.startswith(("PASS", "INFO")) for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
