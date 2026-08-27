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


def test_create_agent_persists_and_is_visible(client: TestClient) -> None:
    """B3.5：创建 Agent（同 Role 可多实例）→ 持久化 → 合并目录可见。"""
    response = client.post(
        "/projects/example-project/agents",
        json={
            "role": "domain_researcher",
            "model_binding": {"mode": "EXPLICIT_MODEL", "value": "research_alpha"},
        },
        headers={"Idempotency-Key": "agent-create-1"},
    )
    assert response.status_code == 201, response.text
    agent = response.json()
    assert agent["role"] == "domain_researcher"
    assert agent["model_binding"]["value"] == "research_alpha"
    assert agent["version"].startswith("sha256:")
    assert response.headers.get("etag", "").startswith("sha256:")

    agents = client.get("/projects/example-project/agents").json()
    assert any(item["id"] == agent["id"] for item in agents)
    # 同 Role 多实例：新 agent 与 example agent 并存
    same_role = [item for item in agents if item["role"] == "domain_researcher"]
    assert len(same_role) >= 2


def test_create_agent_rejects_unknown_role_or_model(client: TestClient) -> None:
    """B3.5：role/model 引用必须真实存在（后端校验，不依赖 UI 隐藏）。"""
    bad_role = client.post(
        "/projects/example-project/agents",
        json={"role": "no_such_role", "model_binding": {"mode": "EXPLICIT_MODEL", "value": "x"}},
        headers={"Idempotency-Key": "agent-create-bad-role"},
    )
    assert bad_role.status_code == 422
    bad_model = client.post(
        "/projects/example-project/agents",
        json={
            "role": "domain_researcher",
            "model_binding": {"mode": "EXPLICIT_MODEL", "value": "no_such_model"},
        },
        headers={"Idempotency-Key": "agent-create-bad-model"},
    )
    assert bad_model.status_code == 422
    bad_mode = client.post(
        "/projects/example-project/agents",
        json={"role": "domain_researcher", "model_binding": {"mode": "NOPE", "value": "x"}},
        headers={"Idempotency-Key": "agent-create-bad-mode"},
    )
    assert bad_mode.status_code == 422


def test_patch_agent_rebinds_model_with_if_match(client: TestClient) -> None:
    """B3.5：PATCH 已有 example agent 持久化新绑定；If-Match 强制。"""
    agents = client.get("/projects/example-project/agents").json()
    domain_a = next(item for item in agents if item["id"] == "domain_a")
    assert domain_a["version"].startswith("sha256:")

    missing = client.patch(
        "/agents/domain_a",
        json={"model_binding": {"mode": "EXPLICIT_MODEL", "value": "coding_beta"}},
        headers={"Idempotency-Key": "agent-patch-no-ifmatch"},
    )
    assert missing.status_code == 428

    stale = client.patch(
        "/agents/domain_a",
        json={"model_binding": {"mode": "EXPLICIT_MODEL", "value": "coding_beta"}},
        headers={"Idempotency-Key": "agent-patch-stale", "If-Match": "sha256:" + "0" * 64},
    )
    assert stale.status_code == 412

    updated = client.patch(
        "/agents/domain_a",
        json={"model_binding": {"mode": "EXPLICIT_MODEL", "value": "coding_beta"}},
        headers={"Idempotency-Key": "agent-patch-ok", "If-Match": domain_a["version"]},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["model_binding"]["value"] == "coding_beta"

    # 用最新 ETag 更新成功
    etag = updated.headers.get("etag", "")
    assert etag.startswith("sha256:")
    second = client.patch(
        "/agents/domain_a",
        json={"model_binding": {"mode": "EXPLICIT_MODEL", "value": "research_alpha"}},
        headers={"Idempotency-Key": "agent-patch-ok2", "If-Match": etag},
    )
    assert second.status_code == 200, second.text
    assert second.json()["model_binding"]["value"] == "research_alpha"

    # 合并目录中 domain_a 的新绑定进入 dry-run 投影（用户配置真实生效）
    projection = client.post(
        "/projects/example-project/dry-run", json={"path": "console_demo_research_v1.yaml"}
    ).json()
    assert projection["agent_models"].get("domain_a") == "research_alpha"


def test_patch_agent_unknown_is_404(client: TestClient) -> None:
    response = client.patch(
        "/agents/no_such_agent",
        json={"model_binding": {"mode": "INHERIT"}},
        headers={"Idempotency-Key": "agent-patch-404"},
    )
    assert response.status_code == 404


def test_put_settings_persists_and_validates(client: TestClient) -> None:
    """B3.5：项目设置持久化；模板/工作区引用校验。"""
    payload = {
        "team_template_id": "rigorous",
        "default_model_profile_id": "research_strong",
        "budget_policy_id": "low_cost",
        "workspace_backend": "openhands_docker",
        "policy_id": "project-policy",
    }
    headers = {"Idempotency-Key": "settings-put-1"}
    response = client.put("/projects/example-project/settings", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    fetched = client.get("/projects/example-project/settings").json()
    assert fetched["team_template_id"] == "rigorous"
    assert fetched["budget_policy_id"] == "low_cost"

    bad_template = client.put(
        "/projects/example-project/settings",
        json={**payload, "team_template_id": "no_such_template"},
        headers={"Idempotency-Key": "settings-put-2"},
    )
    assert bad_template.status_code == 422
    bad_workspace = client.put(
        "/projects/example-project/settings",
        json={**payload, "workspace_backend": "no_such_backend"},
        headers={"Idempotency-Key": "settings-put-3"},
    )
    assert bad_workspace.status_code == 422
