"""Postgres unit tests: type-parity and behavior helpers (offline, no live DB)."""

from __future__ import annotations

from adapters.postgres.serialization import decode_timestamp_pg
from adapters.sqlite.serialization import decode_timestamp


class TestTimestampParity:
    def test_pg_timestamp_handles_both_serializations(self) -> None:
        text_z = "2026-08-13T09:00:00Z"
        text_offset = "2026-08-13T09:00:00+00:00"
        assert decode_timestamp(text_z).value == decode_timestamp_pg(text_z).value
        assert decode_timestamp_pg(text_offset).value.isoformat().endswith("+00:00")
