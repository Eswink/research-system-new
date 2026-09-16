"""Deterministic serialization for Postgres adapters.

Reuses `adapters/sqlite/serialization.py` canonical helpers so that
Postgres storage (JSONB / TIMESTAMPTZ) does not change `digest_of`
output. JSONB stores canonical text as JSONB value; on read we
decode via sqlite helpers to keep single truth.

Provides `decode_timestamp_pg` for TIMESTAMPTZ → domain Timestamp.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone

from adapters.sqlite.serialization import (
    TaskRow,
    decode_contract,
    decode_envelope,
    decode_task,
    decode_timestamp,
    encode_envelope,
    encode_task,
)
from packages.domain.core import Timestamp
from packages.domain.tasks import TaskContract

__all__ = [
    "TaskRow",
    "decode_contract",
    "decode_contract_json",
    "decode_envelope",
    "decode_task",
    "decode_timestamp",
    "decode_timestamp_pg",
    "encode_envelope",
    "encode_task",
    "reencode_task_json",
    "task_json_text",
]


def decode_contract_json(value: object) -> TaskContract:
    """contract_json（JSONB → Python 对象，或 TEXT → str）→ TaskContract。

    完成路径要读 `retry_policy`（PLAN-20260915-078）；两种列类型都收。
    """
    text = value if isinstance(value, str) else json.dumps(value)
    return decode_contract(text)


def task_json_text(value: object) -> str:
    """task_json 列（JSONB → Python 对象，或 TEXT → str）→ canonical JSON 文本。"""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def reencode_task_json(
    task_value: object, contract_value: object, *, attempt: int, lease_id: str
) -> str:
    """这次交付写回 canonical task JSON：`attempt` 与 `lease_id` 一起推进。

    交付一次 lease = 开始一次尝试，所以交付路径（claim / acquire）必须把这一段同步进
    canonical state（PLAN-20260915-078）。投影 `list_tasks` 读的就是 task_json：它一旦
    落后于交付代次，重试产生的用量会一直落在上一次尝试的 entry id 上（`_attempt_scope`
    的 attempt 后缀永不出现），重试预算看到的序号也会与实际交付次数不符。
    """
    entry = decode_task(task_json_text(task_value), task_json_text(contract_value))
    task = replace(entry.task, attempt=attempt, lease_id=lease_id)
    return encode_task(task, entry.contract)[0]


def decode_timestamp_pg(value: datetime | str) -> Timestamp:
    """TIMESTAMPTZ (datetime) or ISO text → domain Timestamp (UTC)."""
    if isinstance(value, str):
        return decode_timestamp(value)
    if value.tzinfo is None:
        # Treat naive as UTC (should not happen for TIMESTAMPTZ)
        value = value.replace(tzinfo=timezone.utc)
    return Timestamp(value.astimezone(timezone.utc))
