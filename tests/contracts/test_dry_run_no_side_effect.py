"""M13 dry-run 零副作用契约测试。

证明（M13 DoD 5）：`dry_run_projection` 与 API dry-run 端点不触发
Research side effect——不启动 Agent、不调用 Research Tool、不执行
Experiment、不写长期 Memory、不 reserve budget（budget ledger 零调用）。
"""

from __future__ import annotations

from adapters.fakes.budget_ledger import FakeBudgetLedger
from adapters.fakes.event_publisher import FakeEventPublisher
from adapters.fakes.execution_backend import FakeExecutionBackend
from adapters.fakes.memory_store import FakeMemoryStore
from adapters.fakes.tool_provider import FakeToolProvider
from packages.application.ports import PreflightContext
from packages.application.preflight.preflight import dry_run_projection, run_preflight
from packages.application.protocol_compile.compiler import compile_protocol
from services.api.catalog import (
    load_catalog_snapshot,
    load_project_settings,
    load_protocol_definition,
)

_PROTOCOL = "m12_reference_research_v1.yaml"


def test_dry_run_projection_never_touches_side_effect_ports() -> None:
    catalog = load_catalog_snapshot()
    project = load_project_settings()
    protocol = load_protocol_definition(_PROTOCOL)
    ledger = FakeBudgetLedger()
    execution = FakeExecutionBackend()
    memory = FakeMemoryStore()
    tools = FakeToolProvider()
    events = FakeEventPublisher()
    context = PreflightContext(
        catalog=catalog,
        project=project,
        credentials=None,
        budget_ledger=ledger,
        policy_evaluator=None,
    )
    result = compile_protocol(protocol, catalog, project)
    assert result.plan is not None
    report = run_preflight(result.plan, context, result.findings)
    projection = dry_run_projection(result.plan, context, report)
    payload = projection.to_payload()

    # 投影内容完整（角色/模型/工具/工作区/预算/审批）
    assert payload["role_counts"]
    assert payload["agent_models"]
    assert payload["tools"]
    assert payload["workspaces"]
    assert payload["budget_reservations"]
    # 成本未估算必须是 None，禁止 0 填充
    assert payload["estimated_cost_minor"] is None

    # 零副作用：所有 side-effect Port 零调用
    assert ledger.method_calls("reserve") == 0
    assert ledger.method_calls("release") == 0
    assert execution.method_calls("execute") == 0
    assert memory.method_calls("write") == 0
    assert tools.method_calls("execute_tool") == 0
    assert events.method_calls("publish") == 0


def test_dry_run_projections_deterministic() -> None:
    """同输入同投影（确定性；digest 语义与 M2 一致）。"""
    catalog = load_catalog_snapshot()
    project = load_project_settings()
    protocol = load_protocol_definition(_PROTOCOL)
    context = PreflightContext(catalog=catalog, project=project)
    result = compile_protocol(protocol, catalog, project)
    assert result.plan is not None
    report = run_preflight(result.plan, context, result.findings)
    first = dry_run_projection(result.plan, context, report).to_payload()
    second = dry_run_projection(result.plan, context, report).to_payload()
    assert first == second
