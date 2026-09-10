"""/cost/daily 控制面测试（PLAN-20260910-037 WP-D）。

503（无 ledger）、跨日投影、unattributed 诚实注记、日期参数校验。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.budget import LedgerCostStatus, ResourceType, UsageLedgerEntry


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _entry(day_offset: int, **overrides: object) -> UsageLedgerEntry:
    base: dict[str, object] = {
        "entry_id": f"u-{uuid.uuid4().hex}",
        "resource_type": ResourceType.MODEL_TOKENS,
        "quantity": 1000,
        "unit": "tokens",
        "cost_status": LedgerCostStatus.UNKNOWN,
        "source": "model_gateway",
        "occurred_at": datetime.now(timezone.utc) + timedelta(days=day_offset),
        "model_id": "model-alpha",
        "run_id": f"ghost-run-{day_offset}",
    }
    base.update(overrides)
    return UsageLedgerEntry(**base)  # type: ignore[arg-type]


def _record(client: TestClient, *entries: UsageLedgerEntry) -> None:
    deps = _deps(client)
    assert deps.budget is not None
    deps.budget.record_usage_batch(entries)


def test_cost_daily_store_missing_is_503(client: TestClient) -> None:
    deps = _deps(client)
    deps.budget = None
    response = client.get("/cost/daily")
    assert response.status_code == 503


def test_cost_daily_buckets_days_and_notes_unattributed(client: TestClient) -> None:
    _record(client, _entry(0), _entry(1))
    response = client.get("/cost/daily")
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["days"]) >= 2
    day = body["days"][0]
    assert day["mixed_pricing"] is False
    # run 不存在 → unfrozen 定价组（绝不回落当期价表）
    assert day["groups"][0]["pricing_version"] == "unfrozen"
    assert day["groups"][0]["pricing_frozen"] is False
    assert "could not be attributed" in (body["attribution_note"] or "")


def test_cost_daily_window_filter_is_422_on_bad_date(client: TestClient) -> None:
    _record(client, _entry(0))
    bad = client.get("/cost/daily", params={"date_from": "2026/09/01"})
    assert bad.status_code == 422
    today = datetime.now(timezone.utc).date().isoformat()
    ok = client.get("/cost/daily", params={"date_from": today, "date_to": today})
    assert ok.status_code == 200
