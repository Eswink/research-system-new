"""Deterministic serialization for Postgres adapters.

Reuses `adapters/sqlite/serialization.py` canonical helpers so that
Postgres storage (JSONB / TIMESTAMPTZ) does not change `digest_of`
output. JSONB stores canonical text as JSONB value; on read we
decode via sqlite helpers to keep single truth.

Provides `decode_timestamp_pg` for TIMESTAMPTZ → domain Timestamp.
"""

from __future__ import annotations

from datetime import datetime, timezone

from adapters.sqlite.serialization import (
    TaskRow,
    decode_envelope,
    decode_task,
    decode_timestamp,
    encode_envelope,
    encode_task,
)
from packages.domain.core import Timestamp

__all__ = [
    "TaskRow",
    "decode_envelope",
    "decode_task",
    "decode_timestamp",
    "decode_timestamp_pg",
    "encode_envelope",
    "encode_task",
]


def decode_timestamp_pg(value: datetime | str) -> Timestamp:
    """TIMESTAMPTZ (datetime) or ISO text → domain Timestamp (UTC)."""
    if isinstance(value, str):
        return decode_timestamp(value)
    if value.tzinfo is None:
        # Treat naive as UTC (should not happen for TIMESTAMPTZ)
        value = value.replace(tzinfo=timezone.utc)
    return Timestamp(value.astimezone(timezone.utc))
