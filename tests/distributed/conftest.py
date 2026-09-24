"""Conftest for M16 distributed-execution tests.

跳过逻辑（`distributed` 标记 + 可达性 + `RESEARCHOS_REQUIRE_POSTGRES` 的 fail-closed）已**集中**
到 `tests/postgres_guard.py`，由**根 conftest** 安装（加载无关）。本文件保留本目录专属夹具：
schema 准备、`pg_dsn`、以及每个用例的 `clean_worker_plane`（截断 worker-plane 表）。

Every module here carries the `distributed` marker (subprocess workers +
loopback gateway + real PostgreSQL).
"""

from __future__ import annotations

import psycopg
import pytest

from adapters.postgres.db import migrate as pg_migrate
from tests.postgres_guard import postgres_available, postgres_dsn, postgres_required


@pytest.fixture(scope="session", autouse=True)
def _distributed_schema_ready() -> None:
    dsn = postgres_dsn()
    if not postgres_available(dsn):
        if postgres_required():
            pytest.fail(f"PostgreSQL not reachable at {dsn}")
        return
    pg_migrate(dsn)


@pytest.fixture()
def pg_dsn() -> str:
    return postgres_dsn()


@pytest.fixture()
def clean_worker_plane(pg_dsn: str) -> str:
    """Truncate the worker-plane tables for per-test isolation."""
    conn = psycopg.connect(pg_dsn, autocommit=True)
    runner = getattr(conn, "execute")
    runner(
        "TRUNCATE tasks, leases, idempotency_records, outbox_events, workers,"
        " execution_jobs CASCADE"
    )
    conn.commit()
    conn.close()
    return pg_dsn
