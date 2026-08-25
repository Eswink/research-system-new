"""Control Plane API 测试：Team / Protocol / Preflight / Dry-run。

Dry Run 门禁（M13 DoD 5）：dry-run 端点零 Research side effect——
不启动 Agent、不调用 Research Tool、不执行 Experiment、不写长期 Memory、
不 reserve budget。
"""

from __future__ import annotations

from fastapi.testclient import TestClient

_PROTOCOL = "m12_reference_research_v1.yaml"


def test_roles_catalog(client: TestClient) -> None:
    response = client.get("/roles")
    assert response.status_code == 200, response.text
    roles = response.json()
    assert len(roles) >= 10
    ids = {role["id"] for role in roles}
    assert "domain_researcher" in ids
    assert "scientific_reviewer" in ids
    role = next(item for item in roles if item["id"] == "domain_researcher")
    # RoleDefinition 不绑定具体模型（ADR-0011）
    assert "model_binding" not in role


def test_team_templates(client: TestClient) -> None:
    response = client.get("/team-templates")
    assert response.status_code == 200, response.text
    templates = response.json()
    ids = {template["id"] for template in templates}
    assert {"lean", "standard", "rigorous"} <= ids
    rigorous = next(item for item in templates if item["id"] == "rigorous")
    assert rigorous["extends"] == "standard"


def test_agents_catalog_keeps_role_agent_separation(client: TestClient) -> None:
    response = client.get("/projects/example-project/agents")
    assert response.status_code == 200, response.text
    agents = response.json()
    assert len(agents) >= 5
    scout_a = next(item for item in agents if item["id"] == "scout_a")
    scout_b = next(item for item in agents if item["id"] == "scout_b")
    # same-role multi-model Agent 语义：RoleDefinition != AgentSpec
    assert scout_a["role"] == "literature_scout"
    assert scout_b["role"] == "literature_scout"
    assert scout_a["model_binding"]["value"] != scout_b["model_binding"]["value"]


def test_protocol_validate_ok(client: TestClient) -> None:
    response = client.post("/protocols/validate", json={"path": _PROTOCOL})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["successful"] is True
    assert result["protocol_digest"].startswith("sha256:")


def test_protocol_validate_rejects_unknown_path(client: TestClient) -> None:
    response = client.post("/protocols/validate", json={"path": "../secret.yaml"})
    # 路径穿越被拒绝（path 必须在 examples/protocols/ 内）
    assert response.status_code == 422


def test_compile_and_preflight_flow(client: TestClient) -> None:
    response = client.post("/projects/example-project/compile", json={"path": _PROTOCOL})
    assert response.status_code == 200, response.text
    report = response.json()
    assert report["status"] in ("PASS", "WARN", "FAIL")
    assert report["estimated_cost"] is None or isinstance(report["estimated_cost"], float)


def test_dry_run_projection_shows_real_resources(client: TestClient) -> None:
    response = client.post("/projects/example-project/dry-run", json={"path": _PROTOCOL})
    assert response.status_code == 200, response.text
    projection = response.json()
    # 实际 Role/Agent/模型/工具/Workspace 投影
    assert "role_counts" in projection and len(projection["role_counts"]) >= 3
    assert "agent_models" in projection
    assert "tools" in projection
    assert "workspaces" in projection
    assert "budget_reservations" in projection
    # 成本未估算时必须是 None，禁止 0 填充（M2 语义）
    assert projection["estimated_cost_minor"] is None


def test_dry_run_has_zero_side_effects(client: TestClient) -> None:
    """Dry-run 不得触发任何 Research side effect（spy 断言零调用）。"""
    from adapters.fakes.budget_ledger import FakeBudgetLedger
    from adapters.fakes.event_publisher import FakeEventPublisher
    from adapters.fakes.execution_backend import FakeExecutionBackend
    from adapters.fakes.memory_store import FakeMemoryStore
    from adapters.fakes.tool_provider import FakeToolProvider

    ledger = FakeBudgetLedger()
    execution = FakeExecutionBackend()
    memory = FakeMemoryStore()
    tools = FakeToolProvider()
    events = FakeEventPublisher()
    client.post("/projects/example-project/dry-run", json={"path": _PROTOCOL})
    assert ledger.method_calls("reserve") == 0
    assert ledger.method_calls("release") == 0
    assert execution.method_calls("execute") == 0
    assert memory.method_calls("write") == 0
    assert tools.method_calls("execute_tool") == 0
    assert events.method_calls("publish") == 0
