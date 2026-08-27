"""PostgresWorkflowEngine — submit path."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adapters.postgres.db import now_iso
from adapters.postgres.leases import request_digest
from packages.domain.tasks import ResearchTask, TaskContract


@dataclass(frozen=True, slots=True)
class SubmitPayload:
    task: ResearchTask
    contract: TaskContract
    task_json: str
    contract_json: str


def _is_duplicate(conn: Any, task: ResearchTask) -> bool:
    existing: Any = conn.execute(
        "SELECT 1 FROM tasks WHERE task_id = %s", (task.id.value,)
    ).fetchone()
    if existing is not None:
        return True
    if task.idempotency_key is not None:
        dup: Any = conn.execute(
            "SELECT 1 FROM tasks WHERE idempotency_key = %s", (task.idempotency_key,)
        ).fetchone()
        if dup is not None:
            return True
        dup2: Any = conn.execute(
            "SELECT 1 FROM idempotency_records WHERE operation_key = %s",
            (task.idempotency_key,),
        ).fetchone()
        if dup2 is not None:
            return True
    return False


def submit_task(conn: Any, record: Any, payload: SubmitPayload, now: Any) -> str:
    task = payload.task
    contract = payload.contract
    with conn.transaction():
        if _is_duplicate(conn, task):
            record("submit", task.id.value, result="deduped")
            return "deduped"
        conn.execute(
            "INSERT INTO tasks (task_id, run_id, idempotency_key, attempt, status, "
            "assigned_agent_id, task_json, contract_json, cancelled, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, FALSE, %s)",
            (
                task.id.value,
                task.run_id.value,
                task.idempotency_key,
                task.attempt,
                task.status,
                task.assigned_agent_id,
                payload.task_json,
                payload.contract_json,
                now_iso(now),
            ),
        )
        if task.idempotency_key is not None:
            conn.execute(
                "INSERT INTO idempotency_records (operation_key, task_id, "
                "request_digest, created_at) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (operation_key) DO NOTHING",
                (
                    task.idempotency_key,
                    task.id.value,
                    request_digest(task, contract),
                    now_iso(now),
                ),
            )
    record("submit", task.id.value)
    return "ok"
