"""SqliteModelStore：ModelDefinition 配置的 SQLite 持久化（M13 控制面）。

M13 声明：配置面持久化（wizard add/discover 与 probe 后保存的能力声明），
不是 M14 PostgreSQL canonical state 承诺；PostgreSQL 走同一 ModelStore Port。

capabilities 以稳定枚举字符串持久化（ModelCapability/CapabilityStatus/
CapabilitySource），读写显式映射，不依赖 dataclass 自动序列化。
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, now_iso
from packages.domain.enums import (
    CapabilitySource,
    CapabilityStatus,
    ModelCapability,
    ThinkingIntensity,
)
from packages.domain.models import CapabilityAssertion, ModelDefinition

_SCHEMA = """
CREATE TABLE IF NOT EXISTS models (
    model_id TEXT PRIMARY KEY,
    model_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class SqliteModelStore(SqliteAdapterBase):
    """SQLite 持久化 ModelStore；list/get/save/delete + close 语义。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("model_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def list_models(self) -> list[ModelDefinition]:
        self._ensure_open()
        rows = self._conn.execute(
            "SELECT model_json FROM models ORDER BY created_at, model_id"
        ).fetchall()
        models = [_decode(json.loads(row["model_json"])) for row in rows]
        self._record("list_models", "", result=str(len(models)))
        return models

    def get_model(self, model_id: str) -> ModelDefinition:
        self._ensure_open()
        row = self._conn.execute(
            "SELECT model_json FROM models WHERE model_id = ?", (model_id,)
        ).fetchone()
        if row is None:
            self._record("get_model", model_id, error="KeyError")
            raise KeyError(f"model not found: {model_id!r}")
        self._record("get_model", model_id, result=model_id)
        return _decode(json.loads(row["model_json"]))

    def save_model(self, model: ModelDefinition) -> None:
        self._ensure_open()
        payload = _encode(model)
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO models (model_id, model_json, created_at) VALUES (?, ?, ?)",
                (model.id, json.dumps(payload, ensure_ascii=False, sort_keys=True), now_iso(None)),
            )
        self._record("save_model", model.id)

    def delete_model(self, model_id: str) -> None:
        self._ensure_open()
        with self._conn:
            cursor = self._conn.execute("DELETE FROM models WHERE model_id = ?", (model_id,))
        if cursor.rowcount == 0:
            self._record("delete_model", model_id, error="KeyError")
            raise KeyError(f"model not found: {model_id!r}")
        self._record("delete_model", model_id)


def _encode(model: ModelDefinition) -> dict[str, Any]:
    capabilities: dict[str, dict[str, Any]] = {}
    for capability, assertion in model.capabilities.items():
        capabilities[capability.value] = {
            "status": assertion.status.value,
            "confidence": assertion.confidence,
            "source": assertion.source.value,
            "probe_version": assertion.probe_version,
        }
    return {
        "id": model.id,
        "endpoint_id": model.endpoint_id,
        "model_name": model.model_name,
        "display_name": model.display_name,
        "enabled": model.enabled,
        "capabilities": capabilities,
        # 声明参数（EC-02）：显式编码，不依赖 dataclass 自动序列化
        "context_window_tokens": model.context_window_tokens,
        "thinking_intensity": (
            model.thinking_intensity.value if model.thinking_intensity is not None else None
        ),
    }


def _decode(record: dict[str, Any]) -> ModelDefinition:
    capabilities: dict[ModelCapability, CapabilityAssertion] = {}
    for capability_name, assertion in record.get("capabilities", {}).items():
        capabilities[ModelCapability(capability_name)] = CapabilityAssertion(
            status=CapabilityStatus(assertion["status"]),
            confidence=assertion["confidence"],
            source=CapabilitySource(assertion["source"]),
            last_verified_at=None,
            probe_version=assertion.get("probe_version"),
        )
    intensity = record.get("thinking_intensity")
    return ModelDefinition(
        id=record["id"],
        endpoint_id=record["endpoint_id"],
        model_name=record["model_name"],
        display_name=record.get("display_name"),
        enabled=record.get("enabled", True),
        capabilities=capabilities,
        # 旧行不含这两个键 ⇒ 读出 None（向后兼容，不因新字段读不出既有数据）
        context_window_tokens=record.get("context_window_tokens"),
        thinking_intensity=ThinkingIntensity(intensity) if intensity is not None else None,
    )
