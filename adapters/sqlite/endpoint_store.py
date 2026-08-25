"""SqliteEndpointStore：LLMEndpoint 配置的 SQLite 持久化（M13 控制面）。

M13 声明：本实现是控制面配置持久化（wizard 保存的 endpoint 配置），
不是 M14 PostgreSQL canonical state 承诺；PostgreSQL 迁移走同一
EndpointStore Port（M14 阶段实现，接口不变）。

序列化使用 domain canonical JSON（DETERMINISTIC_SERIALIZATION.md），
与 YamlEndpointStore 的 payload 结构一致；api_style 一并持久化
（M12 遗留：Memory/Yaml store 未保存 api_style 的缺口在此补齐）。
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, now_iso
from packages.domain.circuit_breaker import CircuitBreakerConfig
from packages.domain.models import EndpointDiscoveryConfig, LLMEndpoint

_SCHEMA = """
CREATE TABLE IF NOT EXISTS llm_endpoints (
    endpoint_id TEXT PRIMARY KEY,
    endpoint_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class SqliteEndpointStore(SqliteAdapterBase):
    """SQLite 持久化 EndpointStore；list/get/save/delete + close 语义。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("endpoint_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def list_endpoints(self) -> list[LLMEndpoint]:
        self._ensure_open()
        rows = self._conn.execute(
            "SELECT endpoint_json FROM llm_endpoints ORDER BY created_at, endpoint_id"
        ).fetchall()
        endpoints = [_decode(json.loads(row["endpoint_json"])) for row in rows]
        self._record("list_endpoints", "", result=str(len(endpoints)))
        return endpoints

    def get_endpoint(self, endpoint_id: str) -> LLMEndpoint:
        self._ensure_open()
        row = self._conn.execute(
            "SELECT endpoint_json FROM llm_endpoints WHERE endpoint_id = ?", (endpoint_id,)
        ).fetchone()
        if row is None:
            self._record("get_endpoint", endpoint_id, error="KeyError")
            raise KeyError(f"endpoint not found: {endpoint_id!r}")
        self._record("get_endpoint", endpoint_id, result=endpoint_id)
        return _decode(json.loads(row["endpoint_json"]))

    def save_endpoint(self, endpoint: LLMEndpoint) -> None:
        self._ensure_open()
        payload = _encode(endpoint)
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO llm_endpoints (endpoint_id, endpoint_json, created_at)"
                " VALUES (?, ?, ?)",
                (
                    endpoint.id,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    now_iso(None),
                ),
            )
        self._record("save_endpoint", endpoint.id)

    def delete_endpoint(self, endpoint_id: str) -> None:
        self._ensure_open()
        with self._conn:
            cursor = self._conn.execute(
                "DELETE FROM llm_endpoints WHERE endpoint_id = ?", (endpoint_id,)
            )
        if cursor.rowcount == 0:
            self._record("delete_endpoint", endpoint_id, error="KeyError")
            raise KeyError(f"endpoint not found: {endpoint_id!r}")
        self._record("delete_endpoint", endpoint_id)


def _encode(endpoint: LLMEndpoint) -> dict[str, Any]:
    record: dict[str, Any] = {
        "id": endpoint.id,
        "name": endpoint.name,
        "protocol": endpoint.protocol,
        "base_url": endpoint.base_url,
        "credential_ref": endpoint.credential_ref,
        "enabled": endpoint.enabled,
        "request_timeout_seconds": endpoint.request_timeout_seconds,
        "max_retries": endpoint.max_retries,
        "concurrency_limit": endpoint.concurrency_limit,
        "api_style": endpoint.api_style,
    }
    if endpoint.discovery is not None:
        record["discovery"] = {
            "enabled": endpoint.discovery.enabled,
            "allow_models": list(endpoint.discovery.allow_models),
        }
    if endpoint.circuit_breaker is not None:
        record["circuit_breaker"] = {
            "failure_threshold": endpoint.circuit_breaker.failure_threshold,
            "open_timeout_seconds": endpoint.circuit_breaker.open_timeout_seconds,
            "half_open_max_probes": endpoint.circuit_breaker.half_open_max_probes,
        }
    return record


def _decode(record: dict[str, Any]) -> LLMEndpoint:
    discovery = record.get("discovery")
    circuit = record.get("circuit_breaker")
    return LLMEndpoint(
        id=record["id"],
        name=record["name"],
        protocol=record["protocol"],
        base_url=record["base_url"],
        credential_ref=record["credential_ref"],
        enabled=record.get("enabled", True),
        request_timeout_seconds=record.get("request_timeout_seconds", 60),
        max_retries=record.get("max_retries", 3),
        concurrency_limit=record.get("concurrency_limit", 4),
        api_style=record.get("api_style", "chat_completions"),
        discovery=_decode_discovery(discovery) if discovery else None,
        circuit_breaker=_decode_circuit(circuit) if circuit else None,
    )


def _decode_discovery(raw: dict[str, Any]) -> EndpointDiscoveryConfig:
    return EndpointDiscoveryConfig(
        enabled=bool(raw.get("enabled", False)),
        allow_models=tuple(str(item) for item in (raw.get("allow_models") or [])),
    )


def _decode_circuit(raw: dict[str, Any]) -> CircuitBreakerConfig:
    return CircuitBreakerConfig(
        failure_threshold=int(raw.get("failure_threshold", 5)),
        open_timeout_seconds=int(raw.get("open_timeout_seconds", 60)),
        half_open_max_probes=int(raw.get("half_open_max_probes", 1)),
    )