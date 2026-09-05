"""M15 operations API 测试:telemetry/cost/trend 三端点(只读投影)。

- telemetry summary 来自 canonical state + sink 计数器(无 vendor 数据);
- cost 唯一 usage 输入是 BudgetLedger.snapshot();未定价 → MONETARY_UNAVAILABLE;
- trend 来自 EvalReportStore;不存在的 run → 404。
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from adapters.fakes.budget_ledger import FakeBudgetLedger
from adapters.fakes.eval_report_store import FakeEvalReportStore
from packages.application.evaluation.eval_index import stored_from_report
from packages.application.evaluation.runner import RunRequest, run_evaluation
from packages.domain.budget import LedgerCostStatus, ResourceType, UsageLedgerEntry
from packages.domain.core import ID, Version
from packages.domain.eval_gate import GateConfig
from packages.domain.eval_result import EvalReport
from packages.domain.eval_spec import EvalCase, EvalDataset, EvalScope, ScorerRef
from packages.domain.tasks import ResearchTask
from services.api.mappers.operations import run_telemetry_dto
from tests.contracts.fixtures import research_task, task_contract

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
    assert isinstance(task, ResearchTask)
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
    assert body["manifest_digest"]
    assert "exporter_config_digest" in body
    tasks = body["tasks"]
    counted = sum(
        tasks[key] for key in ("succeeded", "failed", "cancelled", "queued", "leased", "other")
    )
    assert tasks["total"] == counted
    assert tasks["total"] >= 1
    assert body["sink"]["enabled"] is False  # 测试装配默认 Null
    assert body["sink"]["dropped"] == 0
    assert "prompt" not in response.text


def test_telemetry_outbox_read_failure_is_unknown(run_ready_client: TestClient) -> None:
    run_id = _start_run(run_ready_client)
    deps = cast(Any, run_ready_client.app).state.deps

    class BrokenWorkflow:
        def list_tasks(self, _run_id: str) -> list[object]:
            return []

        def pending_outbox(self) -> object:
            raise RuntimeError("outbox unavailable")

    deps.workflow = BrokenWorkflow()
    dto = run_telemetry_dto(deps, run_id, frozenset())
    assert dto.outbox.pending is None
    assert dto.outbox.status == "UNKNOWN"
    assert dto.outbox.unavailable_reason is not None


def test_cost_endpoint_reports_unpriced_as_unavailable(run_ready_client: TestClient) -> None:
    run_id = _start_run(run_ready_client)
    task_id = _seed_task(run_ready_client, run_id)
    deps = cast(Any, run_ready_client.app).state.deps
    if deps.budget is None:
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


def test_cost_endpoint_gpu_time_is_unpriced_experiment_usage(
    run_ready_client: TestClient,
) -> None:
    run_id = _start_run(run_ready_client)
    task_id = _seed_task(run_ready_client, run_id)
    deps = cast(Any, run_ready_client.app).state.deps
    if deps.budget is None:
        deps.budget = FakeBudgetLedger()
    deps.budget.record_usage(
        _entry(
            task_id,
            2,
            resource_type=ResourceType.GPU_TIME,
            unit="seconds",
            model_id=None,
            source="remote_worker",
        )
    )

    response = run_ready_client.get(f"/runs/{run_id}/cost")

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["dimensions"]) == 1
    gpu_dimension = body["dimensions"][0]
    assert gpu_dimension["dimension"] == "experiment"
    assert gpu_dimension["resource_key"] == task_id
    assert gpu_dimension["entry_count"] == 1
    assert gpu_dimension["amount"]["status"] == "MONETARY_UNAVAILABLE"
    assert gpu_dimension["amount"]["minor_units"] is None
    assert body["total"]["status"] == "MONETARY_UNAVAILABLE"


@pytest.mark.parametrize(
    "resource_type",
    [
        ResourceType.MEMORY,
        ResourceType.STORAGE,
        ResourceType.NETWORK,
        ResourceType.WALL_CLOCK,
        ResourceType.AGENT_TURNS,
        ResourceType.PARALLELISM,
    ],
)
def test_cost_endpoint_maps_every_runtime_resource_to_closed_dimension(
    run_ready_client: TestClient,
    resource_type: ResourceType,
) -> None:
    run_id = _start_run(run_ready_client)
    task_id = _seed_task(run_ready_client, run_id)
    deps = cast(Any, run_ready_client.app).state.deps
    if deps.budget is None:
        deps.budget = FakeBudgetLedger()
    deps.budget.record_usage(
        _entry(
            task_id,
            1,
            resource_type=resource_type,
            unit="units",
            model_id=None,
            source="runtime",
        )
    )

    response = run_ready_client.get(f"/runs/{run_id}/cost")

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["dimensions"]) == 1
    assert body["dimensions"][0]["dimension"] == "experiment"
    assert body["dimensions"][0]["amount"]["status"] == "MONETARY_UNAVAILABLE"


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
    assert point["dataset_id"] == stored.index.dataset_id
    assert point["dataset_version"] == stored.index.dataset_version
    assert point["dataset_digest"] == stored.index.dataset_digest
    assert point["gate_config_id"] == stored.index.gate_config_id
    assert point["gate_config_version"] == stored.index.gate_config_version
    assert point["gate_config_digest"] == stored.index.gate_config_digest
    assert point["system_version"] == stored.index.system_version
    assert point["comparison_digest"] == stored.index.comparison_digest
    assert point["run_id"] is None
    assert point["missing"] is False
    assert point["infra_error_count"] >= 0


def test_trend_endpoint_wires_missing_digests_and_truncation(
    run_ready_client: TestClient,
) -> None:
    _start_run(run_ready_client)
    deps = cast(Any, run_ready_client.app).state.deps
    store = FakeEvalReportStore()
    deps.eval_report_store = store
    first = stored_from_report(
        _report(42),
        recorded_at=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
    )
    second = stored_from_report(
        _report(43),
        recorded_at=datetime(2026, 8, 29, 12, 1, tzinfo=timezone.utc),
    )
    store.put(first)
    store.put(second)
    response = run_ready_client.get(
        "/evaluations/trend",
        params={
            "dataset_id": "m15-ds",
            "limit": 1,
            "expected_digests": [first.index.report_digest, "sha256:" + "a" * 64],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["truncated"] is True
    assert [point["report_digest"] for point in body["missing"]] == ["sha256:" + "a" * 64]


def test_trend_endpoint_503_without_store(client: TestClient) -> None:
    deps = cast(Any, client.app).state.deps
    deps.eval_report_store = None
    assert client.get("/evaluations/trend").status_code == 503


def _report(case_answer: int = 42) -> EvalReport:
    dataset = EvalDataset(
        id="m15-ds",
        version=Version("1.0.0"),
        cases=(
            EvalCase(
                id="c1",
                version=Version("1.0.0"),
                scope=EvalScope.UNIT,
                input_ref="input://c1",
                expected={"answer": case_answer},
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
            inputs={"input://c1": {"answer": case_answer}},
        )
    ).report


def _worker_registry(client: TestClient) -> Any:
    deps = cast(Any, client.app).state.deps
    if getattr(deps, "worker_registry", None) is None:
        from adapters.fakes.worker_registry import FakeWorkerRegistry

        deps.worker_registry = FakeWorkerRegistry()
    return deps.worker_registry


def test_cluster_workers_readonly_view(run_ready_client: TestClient) -> None:
    """M16: /cluster/workers 只读投影;worker_ref 不含原始 id。"""
    from packages.domain.workers import WorkerRegistration

    registry = _worker_registry(run_ready_client)
    registry.register(
        WorkerRegistration(
            worker_id="worker-secret-id-xyz",
            protocol_version="1",
            runtime_version="0.1.0",
            capabilities=frozenset({"docker"}),
            backend_kinds=frozenset({"DOCKER"}),
            platform="linux/amd64",
            partition_slots=frozenset({0}),
            max_concurrency=2,
        )
    )
    response = run_ready_client.get("/cluster/workers")
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["workers"]) == 1
    ref = body["workers"][0]["worker_ref"]
    assert "worker-secret-id-xyz" not in ref  # raw id never leaves the control plane


def test_cluster_workers_gpu_observation_digest_only(run_ready_client: TestClient) -> None:
    """PA-1 debt #7: GPU 观察进入 cluster 投影时只含 digest + 时间戳，
    不得含 raw device name（M17 隐私词表）。"""
    import json

    from packages.domain.core import Timestamp
    from packages.domain.workers import WorkerGpuObservation, WorkerRegistration

    registry = _worker_registry(run_ready_client)
    registry.register(
        WorkerRegistration(
            worker_id="gpu-worker-1",
            protocol_version="1",
            runtime_version="0.1.0",
            capabilities=frozenset({"docker", "gpu"}),
            backend_kinds=frozenset({"DOCKER"}),
            platform="linux/amd64",
            partition_slots=frozenset({0}),
            max_concurrency=1,
            gpu_observation=WorkerGpuObservation(
                device_name="NVIDIA GeForce RTX 4060 Laptop GPU",
                device_count=1,
                driver_version="581.80",
                cuda_runtime_version="12.8",
                total_vram_bytes=8589934592,
                framework="torch-2.9.1+cu128",
                probed_at=Timestamp.now(),
                probe_digest="digest-" + "a" * 59,
            ),
        )
    )
    body = run_ready_client.get("/cluster/workers").json()
    payload = json.dumps(body)
    assert "NVIDIA" not in payload
    assert "torch-2.9.1" not in payload
    assert body["workers"][0]["gpu_probe_digest"].startswith("digest-")
    assert "gpu_observed_at" in body["workers"][0]


def test_run_placement_readonly_view(run_ready_client: TestClient) -> None:
    run_id = _start_run(run_ready_client)
    _worker_registry(run_ready_client)
    response = run_ready_client.get(f"/runs/{run_id}/placement")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["run_id"] == run_id
    assert isinstance(body["execution_tasks"], list)


def test_cluster_workers_unavailable_without_registry() -> None:
    """未配置 registry → 503(不伪装空集群)。"""
    from adapters.fakes.credential_resolver import FakeCredentialResolver
    from services.api.app import create_app
    from services.api.composition import ApiDeps

    deps = ApiDeps(
        endpoint_store=cast(Any, None),
        model_store=cast(Any, None),
        credentials=FakeCredentialResolver({}),
        gateway=cast(Any, None),
        idempotency=cast(Any, None),
    )
    client = TestClient(create_app(deps))
    response = client.get("/cluster/workers")
    assert response.status_code == 503
