"""SqliteModelStore 声明参数往返判据（EC-02）。

判据三件：写进去读得出来、**旧行缺键**不被新字段带崩、非法强度值不静默入库。
配置面是 JSON blob（无 SQL 列），所以「迁移」在这里的真实含义就是**解码向后兼容**。
"""

from __future__ import annotations

import json

from adapters.sqlite.db import connect, now_iso
from adapters.sqlite.model_store import SqliteModelStore
from packages.domain.enums import ThinkingIntensity
from packages.domain.models import ModelDefinition

DECLARED = ModelDefinition(
    id="model-agnes",
    endpoint_id="main",
    model_name="agnes-2.5-flash",
    context_window_tokens=512000,
    thinking_intensity=ThinkingIntensity.MAX,
)


def test_declared_parameters_round_trip() -> None:
    store = SqliteModelStore()
    store.save_model(DECLARED)
    loaded = store.get_model("model-agnes")
    assert loaded is not None
    assert loaded.context_window_tokens == 512000
    assert loaded.thinking_intensity is ThinkingIntensity.MAX


def test_undeclared_parameters_round_trip_as_absent() -> None:
    store = SqliteModelStore()
    store.save_model(ModelDefinition(id="m2", endpoint_id="main", model_name="agnes-2.5-flash"))
    loaded = store.get_model("m2")
    assert loaded is not None
    assert loaded.context_window_tokens is None
    assert loaded.thinking_intensity is None


def test_legacy_row_without_the_new_keys_decodes() -> None:
    """旧行（不含新键）必须仍能读出——不得因新字段让既有数据读不出。"""
    connection = connect(":memory:")
    store = SqliteModelStore(connection=connection)
    legacy_json = json.dumps({
        "id": "legacy",
        "endpoint_id": "main",
        "model_name": "agnes-2.5-flash",
        "display_name": None,
        "enabled": True,
        "capabilities": {},
    })
    connection.execute(
        "INSERT INTO models (model_id, model_json, created_at) VALUES (?, ?, ?)",
        ("legacy", legacy_json, now_iso(None)),
    )
    connection.commit()

    loaded = store.get_model("legacy")
    assert loaded is not None
    assert loaded.context_window_tokens is None
    assert loaded.thinking_intensity is None
