"""Postgres unit tests: type-parity and behavior helpers (offline, no live DB)."""

from __future__ import annotations

import pytest

from adapters.postgres.serialization import decode_timestamp_pg
from adapters.sqlite.serialization import decode_timestamp

_PARITY_CASES = [
    ("2026-08-13T09:00:00Z", "2026-08-13T09:00:00Z"),
    ("2026-08-13T09:00:00+00:00", "2026-08-13T09:00:00Z"),
]


@pytest.mark.parametrize(("text", "expected_z"), _PARITY_CASES)
def test_pg_timestamp_parity(text: str, expected_z: str) -> None:
    ts_sqlite = decode_timestamp(text)
    ts_pg = decode_timestamp_pg(text)
    assert ts_pg.value.isoformat().replace("+00:00", "Z") == expected_z
    assert ts_pg.value == ts_sqlite.value


def test_pg_timestamp_datetime_roundtrip() -> None:
    from datetime import datetime, timezone

    dt = datetime(2026, 8, 13, 9, 0, 0, tzinfo=timezone.utc)
    assert decode_timestamp_pg(dt).value == dt


def test_pg_timestamp_handles_naive_as_utc() -> None:
    from datetime import datetime, timezone

    naive = datetime(2026, 8, 13, 9, 0, 0)
    ts = decode_timestamp_pg(naive)
    assert ts.value.tzinfo is not None
    assert ts.value == datetime(2026, 8, 13, 9, 0, 0, tzinfo=timezone.utc)
