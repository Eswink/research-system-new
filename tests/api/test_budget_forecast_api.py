"""Control Plane API 测试：budget_adjust 干预 + 成本预测投影（PLAN-046）。

证明（PLAN-20260914-046 AC-01/AC-02）：
- budget_adjust 走 BudgetLedger 正式面（release 既有预留 + reserve 新额度，
  append-only 账本无原地改数）；预算面缺失 503、无调整行 422；
- 运行中语义变更（replace_agent）保持诚实 501，不被预算分支吞掉；
- cost-forecast 只覆盖已预留部分：UNKNOWN 不解释为 0、跨币种不求和、
  未知 run 404、账本缺失 503。
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.budget import (
    BudgetPolicy,
    BudgetReservation,
    LedgerCostStatus,
    LedgerQuantityStatus,
    ResourceType,
    UsageLedgerEntry,
)
from packages.domain.core import ID
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState

_AT = datetime(2026, 9, 14, tzinfo=UTC)


def _inject_run(client: TestClient) -> tuple[Any, str]:
    """受控注入一个 RUNNING run（免 preflight；预算面测试不依赖冻结链路）。

    返回 (ApiDeps, run_id)；deps 用 Any 暴露给测试改写（如 budget=None）。
    """
    deps = cast(Any, client.app).state.deps
    run_id = str(ID.generate().value)
    deps.run_registry[run_id] = ResearchRun(
        id=ID(run_id),
        project_id="example-project",
        protocol_id="test_protocol",
        state=ResearchRunState.State.RUNNING,
    )
    return deps, run_id


def _intervene(client: TestClient, run_id: str, payload: dict[str, Any]) -> Any:
    return client.post(
        f"/runs/{run_id}/interventions",
        json=payload,
        headers={"Idempotency-Key": f"k-{uuid.uuid4()}"},
    )


def _policy() -> BudgetPolicy:
    return BudgetPolicy(id="default")


def _reserve(client: TestClient, deps: Any, run_id: str, quantity: int) -> str:
    ref: str = deps.budget.reserve(
        (
            BudgetReservation(
                id=f"budget:{run_id}:MODEL_TOKENS:initial",
                scope=f"run:{run_id}",
                resource_type=ResourceType.MODEL_TOKENS,
                quantity=quantity,
                unit="tokens",
            ),
        ),
        _policy(),
    )
    deps.runs.register_reservation_ref(run_id, ref)
    return ref


def _entry(  # noqa: PLR0913 - 账本条目构造器，参数即字段
    run_id: str,
    *,
    entry_id: str,
    quantity: int,
    cost_status: LedgerCostStatus = LedgerCostStatus.KNOWN,
    estimated: int | None = 120,
    currency: str = "USD",
    quantity_status: LedgerQuantityStatus = LedgerQuantityStatus.KNOWN,
    resource_type: ResourceType = ResourceType.MODEL_TOKENS,
    unit: str = "tokens",
) -> UsageLedgerEntry:
    unmetered = quantity_status is LedgerQuantityStatus.UNKNOWN
    return UsageLedgerEntry(
        entry_id=entry_id,
        resource_type=resource_type,
        quantity=quantity,
        unit=unit,
        cost_status=cost_status,
        source="test",
        occurred_at=_AT,
        estimated_cost_minor=estimated,
        currency=currency,
        run_id=run_id,
        quantity_status=quantity_status,
        unavailable_reason="metering unavailable" if unmetered else None,
    )


def test_budget_adjust_releases_previous_and_reserves_new(client: TestClient) -> None:
    deps, run_id = _inject_run(client)
    previous_ref = _reserve(client, deps, run_id, quantity=1000)
    response = _intervene(
        client,
        run_id,
        {
            "kind": "budget_adjust",
            "adjustments": [{"resource_type": "MODEL_TOKENS", "quantity": 4000, "unit": "tokens"}],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["released_ref"] == previous_ref
    assert body["reservation_ref"] != previous_ref
    assert [item["quantity"] for item in body["reservations"]] == [4000]
    assert all(item["scope"] == f"run:{run_id}" for item in body["reservations"])
    # append-only：旧预留已释放、新预留生效；后续收敛释放指向新额度。
    reservations = deps.budget.snapshot().reservations
    assert [(item.resource_type.value, item.quantity) for item in reservations] == [
        ("MODEL_TOKENS", 4000)
    ]
    assert deps.runs.reservation_ref(run_id) == body["reservation_ref"]


def test_budget_adjust_without_existing_reservation_is_allowed(client: TestClient) -> None:
    deps, run_id = _inject_run(client)
    response = _intervene(
        client,
        run_id,
        {
            "kind": "budget_adjust",
            "adjustments": [{"resource_type": "MODEL_COST", "quantity": 500, "unit": "minor"}],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["released_ref"] is None


def test_budget_adjust_empty_adjustments_is_422(client: TestClient) -> None:
    deps, run_id = _inject_run(client)
    response = _intervene(client, run_id, {"kind": "budget_adjust", "adjustments": []})
    assert response.status_code == 422, response.text


def test_budget_adjust_without_ledger_is_503(client: TestClient) -> None:
    deps, run_id = _inject_run(client)
    deps.budget = None
    response = _intervene(
        client,
        run_id,
        {
            "kind": "budget_adjust",
            "adjustments": [{"resource_type": "MODEL_TOKENS", "quantity": 10, "unit": "tokens"}],
        },
    )
    assert response.status_code == 503, response.text


def test_budget_adjust_unknown_run_is_404(client: TestClient) -> None:
    response = _intervene(
        client,
        "run-missing",
        {
            "kind": "budget_adjust",
            "adjustments": [{"resource_type": "MODEL_TOKENS", "quantity": 10, "unit": "tokens"}],
        },
    )
    assert response.status_code == 404, response.text


def test_replace_agent_still_501(client: TestClient) -> None:
    _deps, run_id = _inject_run(client)
    response = _intervene(client, run_id, {"kind": "replace_agent", "detail": "swap role"})
    assert response.status_code == 501, response.text


def test_cost_forecast_reserved_minus_consumed(client: TestClient) -> None:
    deps, run_id = _inject_run(client)
    _reserve(client, deps, run_id, quantity=1000)
    deps.budget.record_usage(_entry(run_id, entry_id="e-1", quantity=250))
    deps.budget.record_usage(_entry(run_id, entry_id="e-2", quantity=150))
    response = client.get(f"/runs/{run_id}/cost-forecast")
    assert response.status_code == 200, response.text
    body = response.json()
    line = body["lines"][0]
    assert line["resource_type"] == "MODEL_TOKENS"
    assert (line["reserved"], line["consumed"], line["remaining"]) == (1000, 400, 600)
    assert line["data_status"] == "KNOWN"
    assert body["consumed_cost_minor"] == 240
    assert body["currency"] == "USD"
    assert body["cost_status"] == "ESTIMATED"
    assert body["forecast_scope"] == "RESERVED_ONLY"


def test_cost_forecast_adjust_is_visible(client: TestClient) -> None:
    deps, run_id = _inject_run(client)
    _reserve(client, deps, run_id, quantity=1000)
    _intervene(
        client,
        run_id,
        {
            "kind": "budget_adjust",
            "adjustments": [{"resource_type": "MODEL_TOKENS", "quantity": 3000, "unit": "tokens"}],
        },
    )
    body = client.get(f"/runs/{run_id}/cost-forecast").json()
    assert body["lines"][0]["reserved"] == 3000


def test_cost_forecast_unknown_quantity_is_not_zero(client: TestClient) -> None:
    deps, run_id = _inject_run(client)
    _reserve(client, deps, run_id, quantity=1000)
    deps.budget.record_usage(
        _entry(
            run_id,
            entry_id="e-unknown",
            quantity=0,
            quantity_status=LedgerQuantityStatus.UNKNOWN,
            cost_status=LedgerCostStatus.UNKNOWN,
            estimated=None,
        )
    )
    body = client.get(f"/runs/{run_id}/cost-forecast").json()
    line = body["lines"][0]
    assert line["data_status"] == "UNKNOWN"
    assert line["consumed"] is None and line["remaining"] is None
    assert line["reserved"] == 1000
    assert body["consumed_cost_minor"] is None
    assert body["cost_status"] == "MONETARY_UNAVAILABLE"
    assert body["unknown_cost_entries"] == 1


def test_cost_forecast_mixed_currency_is_conflict(client: TestClient) -> None:
    deps, run_id = _inject_run(client)
    deps.budget.record_usage(_entry(run_id, entry_id="e-usd", quantity=10, currency="USD"))
    deps.budget.record_usage(_entry(run_id, entry_id="e-eur", quantity=10, currency="EUR"))
    body = client.get(f"/runs/{run_id}/cost-forecast").json()
    assert body["cost_status"] == "CURRENCY_CONFLICT"
    assert body["consumed_cost_minor"] is None
    assert body["lines"][0]["consumed"] == 20


def test_cost_forecast_no_entries_is_no_data(client: TestClient) -> None:
    _deps, run_id = _inject_run(client)
    body = client.get(f"/runs/{run_id}/cost-forecast").json()
    assert body["lines"] == []
    assert body["cost_status"] == "NO_DATA"
    assert body["consumed_cost_minor"] is None


def test_cost_forecast_unknown_run_404(client: TestClient) -> None:
    response = client.get("/runs/run-missing/cost-forecast")
    assert response.status_code == 404, response.text


def test_cost_forecast_without_ledger_503(client: TestClient) -> None:
    deps, run_id = _inject_run(client)
    deps.budget = None
    response = client.get(f"/runs/{run_id}/cost-forecast")
    assert response.status_code == 503, response.text


def test_real_run_reservation_visible_then_adjust_takes_effect(
    run_ready_client: TestClient,
) -> None:
    """冻结链路的真实 run：preflight 预留 → 预测可见 → 调整后预测跟随。"""
    started = run_ready_client.post(
        "/projects/example-project/runs",
        json={"protocol_path": "m12_reference_research_v1.yaml"},
        headers={"Idempotency-Key": f"run-{uuid.uuid4()}"},
    )
    assert started.status_code == 200, started.text
    run_id = cast(dict[str, Any], started.json())["id"]
    before = run_ready_client.get(f"/runs/{run_id}/cost-forecast")
    assert before.status_code == 200, before.text
    assert any(line["reserved"] > 0 for line in before.json()["lines"])
    adjusted = _intervene(
        run_ready_client,
        run_id,
        {
            "kind": "budget_adjust",
            "adjustments": [{"resource_type": "MODEL_TOKENS", "quantity": 5000, "unit": "tokens"}],
        },
    )
    assert adjusted.status_code == 200, adjusted.text
    after = run_ready_client.get(f"/runs/{run_id}/cost-forecast").json()
    tokens = [line for line in after["lines"] if line["resource_type"] == "MODEL_TOKENS"]
    assert tokens[0]["reserved"] == 5000
