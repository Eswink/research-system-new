"""M15 operations API 测试:telemetry/cost/trend 三端点(只读投影)。

- telemetry summary 来自 canonical state + sink 计数器(无 vendor 数据);
- cost 唯一 usage 输入是 BudgetLedger.snapshot();未定价 → MONETARY_UNAVAILABLE;
- trend 来自 EvalReportStore;不存在的 run → 404。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, cast

from fastapi.testclient import TestClient

from adapters.fakes.eval_report_store import FakeEvalReportStore
from packages.application.evaluation.eval_index import stored_from_report
from packages.application.evaluation.runner import RunRequest, run_evaluation
from packages.domain.budget import LedgerCostStatus, ResourceType, UsageLedgerEntry
from packages.domain.core import Version
from packages.domain.eval_gate import GateConfig
from packages.domain.eval_result import EvalReport
from packages.domain.eval_spec import EvalCase, EvalDataset, EvalScope, ScorerRef

_PROTOCOL = "m12_reference_research_v1.yaml"


def _start_run(run_ready_client: TestClient) -> str:
    response = run_ready_client.post(
        "/projects/example-project/runs",
        json={"protocol_path": _PROTOCOL},
        headers={"Idempotency-Key": f"run-{uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    return str(response.json()["id"])


def _seed_task(run_ready_client: TestClient, run_id: str) -> str:
    """向 workflow 提交确定性任务并返回 task_id(projection 可读)。"""
    from dataclasses import replace

    from packages.domain.core import ID
    from packages.domain.tasks import ResearchTask
    from tests.contracts.fixtures import research_task, task_contract

    deps = cast(Any, run_ready_client.app).state.deps
    base = research_task()
    task_id = f"6f8f56a0-5c2a-4b3e-9f1d-{uuid.uuid4().hex[:12]}"
    task = replace(
        base,
        id=ID(task_id),
        run_id=ID(run_id),
        assigned_agent_id="agent-1",
        idempotency_key=f"ops-{task_id}",
    )
    _ = ResearchTask
    deps.runs._deps.workflow.submit(task, task_contract())
    return task_id


def _entry(task_id: str | None, quantity: int, **overrides: object) -> UsageLedgerEntry:
    base: dict[str, object] = {
        "entry_id": f"u-{uuid.uuid4().hex}",
        "resource_type": ResourceType.MODEL_TOKENS,
        "quantity": quantity,
        "unit": "tokens",
        "cost_status": LedgerCostStatus.UNKNOWN,
        "source": "model_gateway",
        "occurred_at": datetime.now(timezone.utc),
        "model_id": "model-alpha",
        "task_id": task_id,
    }
    base.update(overrides)
    return UsageLedgerEntry(**base)  # type: ignore[arg-type]


def test_telemetry_endpoint_returns_canonical_projection(run_ready_client: TestClient) -> None:
    run_id = _start_run(run_ready_client)
    _seed_task(run_ready_client, run_id)
    response = run_ready_client.get(f"/runs/{run_id}/telemetry")
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == run_id
    tasks = body["tasks"]
    counted = sum(
        tasks[key] for key in ("succeeded", "failed", "cancelled", "queued", "leased", "other")
    )
    assert tasks["total"] == counted
    assert tasks["total"] >= 1
    assert body["sink"]["enabled"] is False  # 测试装配默认 Null
    assert body["sink"]["dropped"] == 0
    assert "prompt" not in response.text


def test_telemetry_endpoint_unknown_run_404(client: TestClient) -> None:
    assert client.get("/runs/nope/telemetry").status_code == 404


def test_cost_endpoint_reports_unpriced_as_unavailable(run_ready_client: TestClient) -> None:
    run_id = _start_run(run_ready_client)
    task_id = _seed_task(run_ready_client, run_id)
    deps = cast(Any, run_ready_client.app).state.deps
    if deps.budget is None:
        from adapters.fakes.budget_ledger import FakeBudgetLedger

        deps.budget = FakeBudgetLedger()
    deps.budget.record_usage(_entry(task_id, 500, estimated_cost_minor=12))
    response = run_ready_client.get(f"/runs/{run_id}/cost")
    assert response.status_code == 200
    body = response.json()
    assert body["pricing_version"] == "unpriced_v1"
    assert body["pricing_digest"]
    model_dimensions = [d for d in body["dimensions"] if d["dimension"] == "model"]
    assert model_dimensions, "model usage must appear as a dimension"
    assert model_dimensions[0]["amount"]["status"] == "MONETARY_UNAVAILABLE"
    assert model_dimensions[0]["amount"]["minor_units"] is None


def test_cost_endpoint_unknown_run_404(client: TestClient) -> None:
    assert client.get("/runs/nope/cost").status_code == 404


def test_trend_endpoint_reports_segments(run_ready_client: TestClient) -> None:
    _start_run(run_ready_client)
    deps = cast(Any, run_ready_client.app).state.deps
    store = FakeEvalReportStore()
    deps.eval_report_store = store
    stored = stored_from_report(_report(), recorded_at=None)
    store.put(stored)
    response = run_ready_client.get("/evaluations/trend", params={"dataset_id": "m15-ds"})
    assert response.status_code == 200
    body = response.json()
    assert body["segments"], "comparable series must produce a segment"
    point = body["segments"][0]["points"][0]
    assert point["report_digest"] == stored.index.report_digest
    assert point["missing"] is False
    assert point["infra_error_count"] >= 0


def test_trend_endpoint_503_without_store(client: TestClient) -> None:
    deps = cast(Any, client.app).state.deps
    deps.eval_report_store = None
    assert client.get("/evaluations/trend").status_code == 503


def _report() -> EvalReport:
    dataset = EvalDataset(
        id="m15-ds",
        version=Version("1.0.0"),
        cases=(
            EvalCase(
                id="c1",
                version=Version("1.0.0"),
                scope=EvalScope.UNIT,
                input_ref="input://c1",
                expected={"answer": 42},
                scorer_refs=(ScorerRef("exact_match", Version("1.0.0")),),
            ),
        ),
    )
    return run_evaluation(
        RunRequest(
            dataset=dataset,
            config=GateConfig(id="gate", version=Version("1.0.0")),
            mode="OFFLINE_FAKE",
            system_version="0.4.0",
            inputs={"input://c1": {"answer": 42}},
        )
    ).report
