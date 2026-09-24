"""Real PostgreSQL type-width regression for single-card device observations."""

from __future__ import annotations

import psycopg
import pytest

from tests.postgres_guard import postgres_dsn

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("peak_bytes", [2**31, 8 * 1024**3])
def test_canonical_peak_gpu_memory_column_can_represent_single_card_vram(peak_bytes: int) -> None:
    with psycopg.connect(postgres_dsn()) as conn:
        row = conn.execute(
            "SELECT data_type FROM information_schema.columns WHERE table_schema='public' "
            "AND table_name='execution_jobs' AND column_name='peak_gpu_memory_bytes'"
        ).fetchone()
        assert row is not None and row[0] == "bigint"
        # Copy the actual canonical column type into an isolated transaction-local
        # probe. No task/lease/domain rows are edited to repair a failed worker.
        conn.execute(
            "CREATE TEMP TABLE gpu_width_probe ON COMMIT DROP AS "
            "SELECT peak_gpu_memory_bytes FROM execution_jobs WITH NO DATA"
        )
        conn.execute("INSERT INTO gpu_width_probe VALUES (%s)", (peak_bytes,))
        observed = conn.execute("SELECT peak_gpu_memory_bytes FROM gpu_width_probe").fetchone()
        assert observed is not None and observed[0] == peak_bytes
