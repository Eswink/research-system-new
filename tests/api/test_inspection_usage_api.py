"""Control Plane API 测试：Budget/Usage run 级隔离（M13 复审补充）。

证明（M13 DoD 11 + 复审 FINDING-M13-6）：
- Budget/Usage 来自正式 UsageLedger（UNKNOWN ≠ 0）；
- usage 视图按 run 隔离：仅返回归属本 run task 的 entry；
- 无 task 归属的 entry 不得泄漏到任何 run；
- 不存在的 run → 404（与 experiments 一致）。
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.budget import LedgerCostStatus, ResourceType, UsageLedgerEntry
from packages.domain.core import Timestamp


def _seed_usage_truth(client: TestClient, run_id: str, task_id: str | None = None) -> None:
    """受控注入正式 UsageLedger 条目（KNOWN 与 UNKNOWN 并存）。

    task_id 非 None 时 entry 归属该 task（run 级隔离判定依据）；
    task_id 为 None 时 entry 无归属（不得出现在任何 run 的 usage 视图）。
    """
    deps = cast(Any, client.app).state.deps
    assert deps.budget is not None
    now = Timestamp.now()
    deps.budget.record_usage(
        UsageLedgerEntry(
            entry_id=f"u-{uuid.uuid4().hex}",
            resource_type=ResourceType.MODEL_TOKENS,
            quantity=1000,
            unit="tokens",
            cost_status=LedgerCostStatus.KNOWN,
            source="model_gateway",
            occurred_at=now.value,
            estimated_cost_minor=10,
            model_id="model-alpha",
            task_id=task_id,
        )
    )
    deps.budget.record_usage(
        UsageLedgerEntry(
            entry_id=f"u-{uuid.uuid4().hex}",
            resource_type=ResourceType.TOOL_REQUESTS,
            quantity=2,
            unit="requests",
            cost_status=LedgerCostStatus.UNKNOWN,
            source="tool_provider",
            occurred_at=now.value,
            task_id=task_id,
        )
    )


def _seed_task_for_run(client: TestClient, run_id: str) -> str:
    """为 run 创建一条真实 task 投影（workflow.submit），返回 task_id。"""
    from packages.domain.core import ID
    from packages.domain.enums import AcceptanceCriterionType
    from packages.domain.tasks import AcceptanceCriterion, ResearchTask, TaskContract

    deps = cast(Any, client.app).state.deps
    connection = cast(Any, deps)._connection
    assert connection is not None
    from adapters.sqlite.workflow_engine import SqliteWorkflowEngine

    workflow = SqliteWorkflowEngine(connection=connection)
    task = ResearchTask(
        id=ID.generate(),
        run_id=ID(run_id),
        contract_id="usage-seed-contract",
        assigned_agent_id="agent-x",
    )
    contract = TaskContract(
        id="usage-seed-contract",
        version="1.0.0",
        purpose="usage isolation seed",
        required_capabilities=[],
        acceptance_criteria=[
            AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS, artifact="x")
        ],
        timeout_seconds=60,
    )
    workflow.submit(task, contract)
    return task.id.value


def test_budget_usage_unknown_not_zero(client: TestClient) -> None:
    """Budget/Usage：UNKNOWN 成本显式计数，禁止显示 0。"""
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun

    deps = cast(Any, client.app).state.deps
    run_id = str(ID.generate().value)
    deps.run_registry[run_id] = ResearchRun(id=ID(run_id), project_id="p", protocol_id="proto")
    task_id = _seed_task_for_run(client, run_id)
    _seed_usage_truth(client, run_id, task_id=task_id)
    response = client.get(f"/runs/{run_id}/usage")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["unknown_cost_entries"] == 1
    assert payload["total_estimated_cost_minor"] is None
    assert payload["known_cost_subtotal_minor"] == 10
    unknown = next(item for item in payload["entries"] if item["cost_status"] == "UNKNOWN")
    assert unknown["estimated_cost_minor"] is None
    assert unknown["quantity_status"] == "KNOWN"
    assert unknown["currency"] == "USD"


def test_usage_isolated_per_run(client: TestClient) -> None:
    """Budget/Usage run 级隔离：其他 run 的 entry 不可见（M13 复审修复）。"""
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun

    deps = cast(Any, client.app).state.deps
    run_a = str(ID.generate().value)
    run_b = str(ID.generate().value)
    for run_id in (run_a, run_b):
        deps.run_registry[run_id] = ResearchRun(id=ID(run_id), project_id="p", protocol_id="proto")
    task_a = _seed_task_for_run(client, run_a)
    task_b = _seed_task_for_run(client, run_b)
    _seed_usage_truth(client, run_a, task_id=task_a)
    _seed_usage_truth(client, run_b, task_id=task_b)

    payload_a = client.get(f"/runs/{run_a}/usage").json()
    assert payload_a["entries"], "run_a must have its own entries"
    assert all(entry["task_id"] == task_a for entry in payload_a["entries"])
    assert all(entry["task_id"] != task_b for entry in payload_a["entries"])

    payload_b = client.get(f"/runs/{run_b}/usage").json()
    assert payload_b["entries"], "run_b must have its own entries"
    assert all(entry["task_id"] == task_b for entry in payload_b["entries"])
    assert all(entry["task_id"] != task_a for entry in payload_b["entries"])


def test_direct_run_usage_is_visible_only_to_its_run(client: TestClient) -> None:
    """无 task 的独立评测/实验 usage 用直接 run_id 归属，仍严格隔离。"""
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun

    deps = cast(Any, client.app).state.deps
    run_a = str(ID.generate().value)
    run_b = str(ID.generate().value)
    deps.run_registry[run_a] = ResearchRun(id=ID(run_a), project_id="p", protocol_id="proto")
    deps.run_registry[run_b] = ResearchRun(id=ID(run_b), project_id="p", protocol_id="proto")
    assert deps.budget is not None
    deps.budget.record_usage(
        UsageLedgerEntry(
            entry_id=f"u-eval-{uuid.uuid4().hex}",
            resource_type=ResourceType.EVALUATION_SCORER,
            quantity=3,
            unit="scorer_calls",
            cost_status=LedgerCostStatus.UNKNOWN,
            source="evaluation",
            occurred_at=Timestamp.now().value,
            run_id=run_a,
        )
    )

    entries_a = client.get(f"/runs/{run_a}/usage").json()["entries"]
    entries_b = client.get(f"/runs/{run_b}/usage").json()["entries"]
    assert len(entries_a) == 1
    assert entries_a[0]["run_id"] == run_a
    assert entries_b == []

    """Budget/Usage：不存在的 run → 404（与 experiments 一致，M13 复审修复）。"""
    response = client.get("/runs/does-not-exist/usage")
    assert response.status_code == 404, response.text


def test_usage_does_not_sum_mixed_currencies(client: TestClient) -> None:
    """不同币种的最小货币单位不得被无条件相加。"""
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun

    deps = cast(Any, client.app).state.deps
    run_id = str(ID.generate().value)
    deps.run_registry[run_id] = ResearchRun(id=ID(run_id), project_id="p", protocol_id="proto")
    assert deps.budget is not None
    for entry_id, currency, amount in (
        ("u-usd", "USD", 300),
        ("u-jpy", "JPY", 3000),
    ):
        deps.budget.record_usage(
            UsageLedgerEntry(
                entry_id=entry_id,
                resource_type=ResourceType.MODEL_COST,
                quantity=1,
                unit="requests",
                cost_status=LedgerCostStatus.KNOWN,
                source="model_gateway",
                occurred_at=Timestamp.now().value,
                estimated_cost_minor=amount,
                currency=currency,
                run_id=run_id,
                model_id="model-alpha",
            )
        )
    payload = client.get(f"/runs/{run_id}/usage").json()
    assert payload["total_estimated_cost_minor"] is None
    assert payload["total_currency"] is None
    assert payload["known_cost_subtotal_minor"] is None


def test_usage_untracked_entry_not_leaked(client: TestClient) -> None:
    """无 task 归属的 usage entry 不得出现在任何 run 的 usage 视图。"""
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun

    deps = cast(Any, client.app).state.deps
    run_id = str(ID.generate().value)
    deps.run_registry[run_id] = ResearchRun(id=ID(run_id), project_id="p", protocol_id="proto")
    task_id = _seed_task_for_run(client, run_id)
    _seed_usage_truth(client, run_id, task_id=task_id)
    # 注入一条无 task_id 的全局条目（模拟无法归属的记账）
    deps = cast(Any, client.app).state.deps
    assert deps.budget is not None
    deps.budget.record_usage(
        UsageLedgerEntry(
            entry_id=f"u-global-{uuid.uuid4().hex}",
            resource_type=ResourceType.MODEL_COST,
            quantity=1,
            unit="requests",
            cost_status=LedgerCostStatus.KNOWN,
            source="unknown-source",
            occurred_at=Timestamp.now().value,
            estimated_cost_minor=9999,
        )
    )
    payload = client.get(f"/runs/{run_id}/usage").json()
    assert all(entry["task_id"] == task_id for entry in payload["entries"])
    assert payload["total_estimated_cost_minor"] is None
    assert payload["known_cost_subtotal_minor"] == 10, "global entry must not leak"
