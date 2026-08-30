"""Conftest for postgres integration tests: skip `postgres`-marked tests if DB unreachable."""

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


@pytest.fixture(scope="session", autouse=True)
def _pg_schema_ready() -> None:
    """Ensure PG schema exists before postgres-marked tests run (idempotent migrate)."""
    dsn = _postgres_dsn()
    if not _postgres_available(dsn):
        if _postgres_required():
            pytest.fail(f"PostgreSQL not reachable at {dsn}")
        return
    pg_migrate(dsn)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: object, items: list[pytest.Item]) -> None:
    del config
    dsn = _postgres_dsn()
    if _postgres_available(dsn) or _postgres_required():
        return
    reason = (
        f"PostgreSQL not reachable at {_postgres_dsn()} — "
        "start with: docker compose -f docker-compose.m14.yml up -d"
    )
    skip = pytest.mark.skip(reason=reason)
    for item in items:
        if item.get_closest_marker("postgres") is not None:
            item.add_marker(skip)
