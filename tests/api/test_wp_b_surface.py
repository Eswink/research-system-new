"""WP-B API 面补齐测试（PLAN-20260912-040）。

覆盖：run 审批历史、custom role/team-template 创建（schema/冲突/缺 store 503）、
agent clone、G10 删除语义（endpoint/model/draft/agent + 引用完整性 409）、
compatibility 硬能力投影。
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.application.ports.approval_store import ApprovalSpec
from packages.domain.core import ID
from packages.domain.run import ResearchRun
from services.api.approvals import ApprovalRegistry
from services.api.composition import ApiDeps
from tests.api.conftest import create_endpoint

_DRAFT_YAML = Path("examples/protocols/sort_analysis_v1.yaml").read_text(encoding="utf-8")


def _idem() -> dict[str, str]:
    return {"Idempotency-Key": f"k-{uuid.uuid4().hex}"}


def _role_payload(role_id: str, **overrides: Any) -> dict[str, Any]:
    document: dict[str, Any] = {
        "id": role_id,
        "role_type": "analysis",
        "category": "evaluation",
        "default_model_profile": "research_strong",
        "activation_default": "ON_DEMAND",
        "requested_capabilities": ["analysis.read"],
        "hard_model_capabilities": {"all_of": ["function_calling"], "any_of": []},
        "workspace_policy": "read_only",
    }
    document.update(overrides)
    return document


# --- run 审批历史 ---


def test_run_approvals_history_and_404(client: TestClient) -> None:
    deps = cast(Any, client.app).state.deps
    deps.approvals = ApprovalRegistry()
    run_id = ID.generate().value
    deps.run_registry[run_id] = ResearchRun(
        id=ID(run_id), project_id="example-project", protocol_id="proto"
    )
    approval = deps.approvals.register(
        ApprovalSpec(
            run_id=run_id,
            action="workspace.delete",
            risk="HIGH",
            context="destructive workspace action",
            policy_source="native-policy",
            requested_event_id=f"evt-{run_id}",
        )
    )
    listed = client.get(f"/runs/{run_id}/approvals")
    assert listed.status_code == 200
    payload = listed.json()
    assert [item["id"] for item in payload] == [approval.id]
    assert payload[0]["status"] == "PENDING"

    assert client.get("/runs/no-such-run/approvals").status_code == 404


# --- custom role / team template ---


def test_custom_role_created_visible_and_conflicts(client: TestClient) -> None:
    role_id = f"custom_role_{uuid.uuid4().hex[:8]}"
    created = client.post("/roles/custom", json=_role_payload(role_id), headers=_idem())
    assert created.status_code == 201, created.text
    assert created.json()["id"] == role_id

    ids = {item["id"] for item in client.get("/roles").json()}
    assert role_id in ids

    duplicate = client.post("/roles/custom", json=_role_payload(role_id), headers=_idem())
    assert duplicate.status_code == 409

    baseline = client.post(
        "/roles/custom", json=_role_payload("research_director"), headers=_idem()
    )
    assert baseline.status_code == 409

    invalid = client.post(
        "/roles/custom",
        json=_role_payload(f"bad_{uuid.uuid4().hex[:8]}", category="not-a-category"),
        headers=_idem(),
    )
    assert invalid.status_code == 422


def test_custom_team_template_created_and_visible(client: TestClient) -> None:
    template_id = f"custom_tpl_{uuid.uuid4().hex[:8]}"
    payload = {
        "id": template_id,
        "display_name": "Custom Solo",
        "roles": {"research_director": {"min_instances": 1, "max_instances": 1}},
    }
    created = client.post("/team-templates/custom", json=payload, headers=_idem())
    assert created.status_code == 201, created.text
    ids = {item["id"] for item in client.get("/team-templates").json()}
    assert template_id in ids


def test_custom_contract_without_store_is_503(client: TestClient) -> None:
    deps: ApiDeps = cast(Any, client.app).state.deps
    deps.catalog_overrides = None
    response = client.post("/roles/custom", json=_role_payload("orphan"), headers=_idem())
    assert response.status_code == 503


# --- agent clone + delete ---


def test_agent_clone_and_delete_roundtrip(client: TestClient) -> None:
    new_id = f"cloned_{uuid.uuid4().hex[:8]}"
    cloned = client.post("/agents/director/clone", json={"new_id": new_id}, headers=_idem())
    assert cloned.status_code == 201, cloned.text
    assert cloned.json()["id"] == new_id
    assert cloned.json()["role"] == "research_director"

    ids = {item["id"] for item in client.get("/projects/example-project/agents").json()}
    assert new_id in ids

    conflict = client.post("/agents/director/clone", json={"new_id": new_id}, headers=_idem())
    assert conflict.status_code == 409

    unknown = client.post("/agents/no_such_agent/clone", json={}, headers=_idem())
    assert unknown.status_code == 404

    assert client.delete(f"/agents/{new_id}", headers=_idem()).status_code == 204
    ids_after = {item["id"] for item in client.get("/projects/example-project/agents").json()}
    assert new_id not in ids_after

    assert client.delete(f"/agents/{new_id}", headers=_idem()).status_code == 404
    assert client.delete("/agents/director", headers=_idem()).status_code == 404


# --- endpoint/model 引用完整性 + compatibility 投影 ---


def test_delete_reference_integrity_and_compatibility(client: TestClient) -> None:
    endpoint = create_endpoint(client, name=f"relay-{uuid.uuid4().hex[:6]}")
    endpoint_id = endpoint["id"]
    model = client.post(
        "/models",
        json={"endpoint_id": endpoint_id, "model_name": "probe-target"},
        headers=_idem(),
    )
    assert model.status_code == 201, model.text
    model_id = model.json()["id"]

    role_id = f"probe_role_{uuid.uuid4().hex[:8]}"
    assert (
        client.post("/roles/custom", json=_role_payload(role_id), headers=_idem()).status_code
        == 201
    )
    agent = client.post(
        "/projects/example-project/agents",
        json={"role": role_id, "model_binding": {"mode": "EXPLICIT_MODEL", "value": model_id}},
        headers=_idem(),
    )
    assert agent.status_code == 201, agent.text
    agent_id = agent.json()["id"]

    compat = client.get(f"/models/{model_id}/compatibility").json()
    assert compat["hard_capability_requirements"] == ["function_calling"]

    assert client.delete(f"/models/{model_id}", headers=_idem()).status_code == 409
    assert client.delete(f"/llm-endpoints/{endpoint_id}", headers=_idem()).status_code == 409

    assert client.delete(f"/agents/{agent_id}", headers=_idem()).status_code == 204
    assert client.delete(f"/models/{model_id}", headers=_idem()).status_code == 204
    assert client.delete(f"/llm-endpoints/{endpoint_id}", headers=_idem()).status_code == 204
    assert client.delete(f"/llm-endpoints/{endpoint_id}", headers=_idem()).status_code == 404
    assert client.delete("/models/no-such-model", headers=_idem()).status_code == 404


def test_compatibility_empty_when_nothing_declares(client: TestClient) -> None:
    endpoint = create_endpoint(client, name=f"relay-{uuid.uuid4().hex[:6]}")
    model = client.post(
        "/models",
        json={"endpoint_id": endpoint["id"], "model_name": "lonely-model"},
        headers=_idem(),
    )
    compat = client.get(f"/models/{model.json()['id']}/compatibility").json()
    assert compat["hard_capability_requirements"] == []


# --- draft delete ---


def test_draft_delete_roundtrip(client: TestClient) -> None:
    created = client.post(
        "/projects/example-project/protocol-drafts",
        json={"name": "to delete", "yaml_text": _DRAFT_YAML},
        headers=_idem(),
    )
    assert created.status_code == 201, created.text
    draft_id = created.json()["draft_id"]

    assert client.delete(f"/protocol-drafts/{draft_id}", headers=_idem()).status_code == 204
    assert client.get(f"/protocol-drafts/{draft_id}").status_code == 404
    assert client.delete(f"/protocol-drafts/{draft_id}", headers=_idem()).status_code == 404
