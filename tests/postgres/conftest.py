"""Conftest for postgres integration tests: schema readiness fixture only.

跳过逻辑（`postgres` 标记 + 可达性 + `RESEARCHOS_REQUIRE_POSTGRES` 的 fail-closed）已**集中**
到 `tests/postgres_guard.py`，并由**根 conftest** 安装——它只有在 pytest 收集到本目录时才加载，
定向跑（例如只跑 `tests/api`）过去因此既**不跳过**也**不快失败**（实测挂死）。本文件只保留
「schema 先就位」这个只对本目录有意义的 session 夹具。
"""

from __future__ import annotations

import pytest

from adapters.postgres.db import migrate as pg_migrate
from tests.postgres_guard import postgres_available, postgres_dsn, postgres_required


@pytest.fixture(scope="session", autouse=True)
def _pg_schema_ready() -> None:
    """Ensure PG schema exists before postgres-marked tests run (idempotent migrate)."""
    dsn = postgres_dsn()
    if not postgres_available(dsn):
        if postgres_required():
            pytest.fail(f"PostgreSQL not reachable at {dsn}")
        return
    pg_migrate(dsn)
