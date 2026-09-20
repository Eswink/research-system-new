"""PG 组合根下的模型声明参数读面（GOAL-20260920-008 EC-02 / AC-03 后半）。

GOAL 的判定细则要求判据证明「**PG 组合根下读到的模型仍带这两个值**」，而不是把
「SQLite 一侧往返 + 分派都是 Sqlite 存储」当成等价物。因此本用例：

1. 只构造**一个**配置面实例（`SqliteModelStore`），把它交给 `PgAssemblyConfig`；
2. 经 `build_postgres_assembly` → `build_postgres_apideps` 得到**PG 组合根**的 ApiDeps，
   **不做任何事后替换**（`tests/postgres/test_m13_pg_run_e2e.py` 用 `_to_apideps` 事后
   覆盖存储，那是为跑通 run 链路的取舍，不能拿来证明配置面来自装配）；
3. 通过真实 HTTP 面 POST / GET / PATCH 断言两值可判、未声明为 null、PATCH 后 ETag 变。

反证：让 `build_postgres_assembly` 丢掉 `model_store`（不回填 `assembly.model_store`）
⇒ `deps.model_store` 不是同一实例、POST 无法落库 ⇒ 本用例红。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.postgres


def _dsn() -> str:
    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
    )


def _pg_root_deps(tmp_path: Path) -> tuple[Any, Any]:
    """PG 组合根 ApiDeps + 那一个配置面实例（无事后替换）。"""
    from adapters.sqlite.db import connect as sqlite_connect
    from adapters.sqlite.endpoint_store import SqliteEndpointStore
    from adapters.sqlite.model_store import SqliteModelStore
    from services.api.pg_composition import (
        PgAssemblyConfig,
        build_postgres_apideps,
        build_postgres_assembly,
    )
    from services.api.settings import ApiSettings

    connection = sqlite_connect(str(tmp_path / "control.sqlite"))
    settings = ApiSettings(db_path=str(tmp_path / "control.sqlite"))
    model_store = SqliteModelStore(connection=connection)
    assembly = build_postgres_assembly(
        PgAssemblyConfig(
            effective=settings,
            connection=connection,
            endpoint_store=SqliteEndpointStore(connection=connection),
            model_store=model_store,
            pg_dsn=_dsn(),
            ensure_schema=True,
        )
    )
    return build_postgres_apideps(assembly), model_store


def test_pg_root_reads_back_the_declared_parameters(tmp_path: Path) -> None:
    from services.api.app import create_app

    deps, model_store = _pg_root_deps(tmp_path)
    assert deps.model_store is model_store, (
        "PG 组合根没有携带 config 里的那一个配置面实例（装配丢字段）"
    )
    client = TestClient(create_app(deps))

    endpoint = client.post(
        "/llm-endpoints",
        json={"name": "pg-root-relay", "base_url": "https://relay.example.com/api/v1"},
        headers={"Idempotency-Key": "pg-param-endpoint"},
    )
    assert endpoint.status_code == 201, endpoint.text
    endpoint_id = str(endpoint.json()["id"])

    created = client.post(
        "/models",
        json={
            "endpoint_id": endpoint_id,
            "model_name": "agnes-2.5-flash",
            "context_window_tokens": 512000,
            "thinking_intensity": "MAX",
        },
        headers={"Idempotency-Key": "pg-param-model"},
    )
    assert created.status_code == 201, created.text
    model = created.json()
    assert model["context_window_tokens"] == 512000
    assert model["thinking_intensity"] == "MAX"

    fetched = client.get(f"/models/{model['id']}")
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["context_window_tokens"] == 512000
    assert fetched.json()["thinking_intensity"] == "MAX"

    patched = client.patch(
        f"/models/{model['id']}",
        json={"context_window_tokens": 200000, "thinking_intensity": "LOW"},
        headers={"Idempotency-Key": "pg-param-patch", "If-Match": model["version"]},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["context_window_tokens"] == 200000
    assert patched.json()["thinking_intensity"] == "LOW"
    assert patched.json()["version"] != model["version"]


def test_pg_root_reads_undeclared_parameters_as_absent(tmp_path: Path) -> None:
    from services.api.app import create_app

    deps, _ = _pg_root_deps(tmp_path)
    client = TestClient(create_app(deps))
    endpoint = client.post(
        "/llm-endpoints",
        json={"name": "pg-root-relay-2", "base_url": "https://relay.example.com/api/v1"},
        headers={"Idempotency-Key": "pg-param-endpoint-2"},
    )
    assert endpoint.status_code == 201, endpoint.text
    created = client.post(
        "/models",
        json={"endpoint_id": endpoint.json()["id"], "model_name": "plain-model"},
        headers={"Idempotency-Key": "pg-param-model-2"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["context_window_tokens"] is None
    assert created.json()["thinking_intensity"] is None
