"""Conftest for M16 distributed-execution tests.

Skips when PostgreSQL is unreachable; fails closed when
`RESEARCHOS_REQUIRE_POSTGRES=1` (same posture as tests/postgres/conftest.py).
Every module here carries the `distributed` marker (subprocess workers +
loopback gateway + real PostgreSQL).
"""

from __future__ import annotations

import os

import psycopg
import pytest

from adapters.postgres.db import migrate as pg_migrate


def _postgres_dsn() -> str:
    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        os.environ.get(
            "DATABASE_URL",
            "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
        ),
    )


def _postgres_required() -> bool:
    return os.environ.get("RESEARCHOS_REQUIRE_POSTGRES") == "1"


def _postgres_available(dsn: str) -> bool:
    try:
        conn = psycopg.connect(dsn, autocommit=True, connect_timeout=2)
        conn.close()
        return True
    except Exception:
        return False


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: object, items: list[pytest.Item]) -> None:
    del config
    dsn = _postgres_dsn()
    if _postgres_available(dsn) or _postgres_required():
        return
    reason = (
        f"PostgreSQL not reachable at {dsn} — "
        "start with: docker compose -f docker-compose.m14.yml up -d"
    )
    skip = pytest.mark.skip(reason=reason)
    for item in items:
        if item.get_closest_marker("distributed") is not None:
            item.add_marker(skip)


@pytest.fixture(scope="session", autouse=True)
def _distributed_schema_ready() -> None:
    dsn = _postgres_dsn()
    if not _postgres_available(dsn):
        if _postgres_required():
            pytest.fail(f"PostgreSQL not reachable at {dsn}")
        return
    pg_migrate(dsn)


@pytest.fixture()
def pg_dsn() -> str:
    return _postgres_dsn()


@pytest.fixture()
def clean_worker_plane(pg_dsn: str) -> str:
    """Truncate the worker-plane tables for per-test isolation."""
    conn = psycopg.connect(pg_dsn, autocommit=True)
    conn.execute(
        "TRUNCATE tasks, leases, idempotency_records, outbox_events, workers,"
        " execution_jobs CASCADE"
    )
    conn.commit()
    conn.close()
    return pg_dsn
