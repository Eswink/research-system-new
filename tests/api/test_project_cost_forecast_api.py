"""/projects/{id}/cost-forecast 控制面测试（G12 / GOAL-20260915-002 EC-02）。

锁住"跨 run 时序投影"的诚实口径：只对已计价的天外推、其余逐日给出排除原因；
归属限定在项目 runs（其它项目的已知 run 明确排除、归属不明的条目计数）；
未知项目返回空序列 + NO_VALUED_DAYS；horizon 越界 422；无 ledger 503。
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.budget import (
    LedgerCostStatus,
    LedgerQuantityStatus,
    ResourceType,
    UsageLedgerEntry,
)
from packages.domain.core import ID
from packages.domain.run import ResearchRun
from services.api.dto.operations import ProjectCostForecastDto
from services.api.run_access import save_run

PROJECT_ID = "example-project"
OTHER_PROJECT_ID = "other-project"


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _seed_run(client: TestClient, project_id: str = PROJECT_ID) -> str:
    """按生产口径落 run（`save_run` 双写）并返回 run id（Domain 要求 UUID）。"""
    run_id = str(ID.generate().value)
    save_run(
        _deps(client),
        ResearchRun(id=ID(run_id), project_id=project_id, protocol_id="proto"),
    )
    return run_id


def _entry(day_offset: int, **overrides: object) -> UsageLedgerEntry:
    base: dict[str, object] = {
        "entry_id": f"u-{uuid.uuid4().hex}",
        "resource_type": ResourceType.MODEL_TOKENS,
        "quantity": 1000,
        "unit": "tokens",
        # 中转站未上报金额的默认态：UNKNOWN + 原因（Domain 要求）；金额由用例显式给。
        "cost_status": LedgerCostStatus.UNKNOWN,
        "unavailable_reason": "cost not reported by the relay",
        "source": "model_gateway",
        "occurred_at": datetime.now(timezone.utc) + timedelta(days=day_offset),
        "model_id": "model-alpha",
    }
    base.update(overrides)
    return UsageLedgerEntry(**base)  # type: ignore[arg-type]


def _record(client: TestClient, *entries: UsageLedgerEntry) -> None:
    deps = _deps(client)
    assert deps.budget is not None
    deps.budget.record_usage_batch(entries)


def _valued(client: TestClient, run_id: str, *, day: int, minor: int) -> None:
    """一天一笔已计价（ACTUAL）用量：actual_cost_minor 直接就位，无需价表。"""
    _record(
        client,
        _entry(
            day,
            run_id=run_id,
            actual_cost_minor=minor,
            quantity=1000,
        ),
    )


def test_project_cost_forecast_requires_ledger(client: TestClient) -> None:
    deps = _deps(client)
    deps.budget = None
    assert client.get(f"/projects/{PROJECT_ID}/cost-forecast").status_code == 503


def test_project_cost_forecast_projects_from_valued_days(run_ready_client: TestClient) -> None:
    run_id = _seed_run(run_ready_client)
    _valued(run_ready_client, run_id, day=-2, minor=1000)
    _valued(run_ready_client, run_id, day=-1, minor=3000)

    response = run_ready_client.get(f"/projects/{PROJECT_ID}/cost-forecast?horizon_days=7")

    assert response.status_code == 200, response.text
    view = ProjectCostForecastDto.model_validate(response.json())
    assert view.project_id == PROJECT_ID
    projection = view.projection
    assert projection.method == "MEAN_OF_VALUED_DAYS"
    assert projection.horizon_days == 7
    assert projection.valued_days == 2
    assert projection.excluded_days == 0
    assert projection.observed_minor == 4000
    assert projection.observed_status == "ACTUAL"
    assert projection.currency == "USD"
    assert projection.daily_mean_minor == 2000
    # 已计价日均 2000 × 7 天
    assert projection.projected_minor == 14000
    assert projection.unavailable_reason is None
    assert all(day.included_in_projection for day in view.days)
    assert "not a commitment" in projection.note


def test_project_cost_forecast_excludes_unpriced_and_unknown_days(
    run_ready_client: TestClient,
) -> None:
    run_id = _seed_run(run_ready_client)
    _valued(run_ready_client, run_id, day=-3, minor=1000)
    # 同日两笔不同定价来源（一笔有实际金额、一笔 quantity 未知）→ 不猜、不补零
    _record(
        run_ready_client,
        _entry(-1, run_id=run_id, quantity_status=LedgerQuantityStatus.UNKNOWN),
    )

    view = ProjectCostForecastDto.model_validate(
        run_ready_client.get(f"/projects/{PROJECT_ID}/cost-forecast").json()
    )

    reasons = {day.exclusion_reason for day in view.days if not day.included_in_projection}
    assert "USAGE_UNKNOWN" in reasons
    assert view.projection.valued_days == 1
    assert view.projection.excluded_days == 1
    assert view.projection.projected_minor == 1000 * 7


def test_project_cost_forecast_is_scoped_to_project_runs(run_ready_client: TestClient) -> None:
    mine = _seed_run(run_ready_client)
    theirs = _seed_run(run_ready_client, OTHER_PROJECT_ID)
    _valued(run_ready_client, mine, day=-1, minor=500)
    _valued(run_ready_client, theirs, day=-1, minor=999_999)
    # 归属不明的条目（run 不在任何项目）计入 unattributed，不混进项目序列
    _record(run_ready_client, _entry(-1, run_id="ghost-run", actual_cost_minor=777_000))

    view = ProjectCostForecastDto.model_validate(
        run_ready_client.get(f"/projects/{PROJECT_ID}/cost-forecast").json()
    )

    assert view.projection.observed_minor == 500
    assert view.unattributed_entries == 1
    assert view.attribution_note is not None and "could not be attributed" in view.attribution_note
    # 其它项目的条目既不进序列也不计为"归属不明"
    other = ProjectCostForecastDto.model_validate(
        run_ready_client.get(f"/projects/{OTHER_PROJECT_ID}/cost-forecast").json()
    )
    assert other.projection.observed_minor == 999_999


def test_project_cost_forecast_unknown_project_is_empty_not_404(
    run_ready_client: TestClient,
) -> None:
    response = run_ready_client.get("/projects/does-not-exist/cost-forecast")

    assert response.status_code == 200
    view = ProjectCostForecastDto.model_validate(response.json())
    assert view.days == []
    assert view.projection.valued_days == 0
    assert view.projection.projected_minor is None
    assert view.projection.unavailable_reason is not None
    assert view.projection.unavailable_reason.startswith("NO_VALUED_DAYS")


def test_project_cost_forecast_window_and_horizon_edges(run_ready_client: TestClient) -> None:
    run_id = _seed_run(run_ready_client)
    _valued(run_ready_client, run_id, day=-1, minor=1000)

    out_of_range = run_ready_client.get(
        f"/projects/{PROJECT_ID}/cost-forecast", params={"horizon_days": 0}
    )
    assert out_of_range.status_code == 422
    too_big = run_ready_client.get(
        f"/projects/{PROJECT_ID}/cost-forecast", params={"horizon_days": 91}
    )
    assert too_big.status_code == 422
    bad_date = run_ready_client.get(
        f"/projects/{PROJECT_ID}/cost-forecast", params={"date_from": "2026/09/01"}
    )
    assert bad_date.status_code == 422

    today = datetime.now(timezone.utc).date()
    windowed = ProjectCostForecastDto.model_validate(
        run_ready_client.get(
            f"/projects/{PROJECT_ID}/cost-forecast",
            params={"date_from": today.isoformat(), "date_to": today.isoformat()},
        ).json()
    )
    assert windowed.from_date == today.isoformat()
    assert all(day.date == today.isoformat() for day in windowed.days)

    # 未来窗口：没有数据的日期不填充（NO_DATA 不是插值）
    future_from = (today + timedelta(days=30)).isoformat()
    empty_window = ProjectCostForecastDto.model_validate(
        run_ready_client.get(
            f"/projects/{PROJECT_ID}/cost-forecast", params={"date_from": future_from}
        ).json()
    )
    assert empty_window.days == []
    assert empty_window.projection.projected_minor is None


def test_project_cost_forecast_truncation_flag_is_present(run_ready_client: TestClient) -> None:
    """日序列截断阈值（400 天）由 daily_series 决定，本端点如实透传该标志。"""
    run_id = _seed_run(run_ready_client)
    _valued(run_ready_client, run_id, day=-1, minor=1000)

    view = ProjectCostForecastDto.model_validate(
        run_ready_client.get(f"/projects/{PROJECT_ID}/cost-forecast").json()
    )

    assert view.truncated is False
    assert date.fromisoformat(view.days[-1].date) <= datetime.now(timezone.utc).date()
    assert "reserved-vs-consumed" in view.scope_note
