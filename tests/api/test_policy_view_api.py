"""策略面可见性 API 测试（PLAN-20260914-049 WP-C/WP-D）。

`GET /policy/capabilities` 只读快照 + 门链能力逐 scope 有效判决；以及可控收紧
（deny）后 memory 提案在 API 层被 422/policy 阶段拒绝（reason 可读）。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

from fastapi.testclient import TestClient

from adapters.contracts import load_policy
from adapters.fakes.memory_store import FakeMemoryStore
from packages.application.policy.native import NativePolicyEvaluator
from packages.domain.enums import TrustLabel
from packages.domain.evidence import SourceRecord
from packages.domain.policy import PolicyDefinition, PolicyRule

SOURCE = "paper://policy-wiring"


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _tighten(policy: PolicyDefinition, *, deny_scope: str) -> PolicyDefinition:
    return replace(
        policy,
        deny=policy.deny + (PolicyRule(capability="memory.write", scope=deny_scope),),
    )


def _wire_policy(client: TestClient, policy: PolicyDefinition) -> None:
    deps = _deps(client)
    deps.policy = policy
    deps.policy_evaluator = NativePolicyEvaluator(policy)


def _wire_memory(client: TestClient) -> None:
    deps = _deps(client)
    deps.memory = FakeMemoryStore()
    deps.ledger.register_source(
        SourceRecord(
            origin=SOURCE,
            content_digest="sha256:" + "b" * 64,
            trust_label=TrustLabel.VERIFIED_SOURCE,
        )
    )


def _proposal() -> dict[str, object]:
    return {
        "tier": "SESSION",
        "kind": "FACT",
        "content": "policy wiring probe",
        "provenance": SOURCE,
        "confidence": 0.8,
    }


def test_snapshot_is_503_when_policy_is_not_loaded(client: TestClient) -> None:
    """策略面不可用时不伪造快照（诚实 503）。"""
    assert _deps(client).policy is None
    assert client.get("/policy/capabilities").status_code == 503


def test_snapshot_lists_declared_rules_and_memory_tiers(client: TestClient) -> None:
    _wire_policy(client, load_policy("examples/config/policy.yaml"))
    response = client.get("/policy/capabilities")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["policy_id"] == "project-policy"
    assert body["version"] == "0.4.0"
    assert body["default_effect"] == "DENY"
    assert body["source"] == "examples/config/policy.yaml"
    declared = [
        rule
        for rule in body["rules"]
        if rule["capability"] == "memory.write" and rule["effect"] == "ALLOW"
    ]
    assert {rule["scope"] for rule in declared} == {"SESSION", "RUN", "PROJECT", "ORGANIZATION"}
    (gate,) = body["gate_capabilities"]
    assert gate["capability"] == "memory.write"
    assert gate["scopes"] == ["ORGANIZATION", "PROJECT", "RUN", "SESSION"]
    assert set(gate["effects"].values()) == {"ALLOW"}
    assert "actor" in body["note"]


def test_tightened_policy_is_visible_and_blocks_proposal(client: TestClient) -> None:
    """收紧为 deny 后：快照如实呈现 DENY，且提案在 policy 阶段被 422 拒绝。"""
    _wire_policy(client, _tighten(load_policy("examples/config/policy.yaml"), deny_scope="SESSION"))
    _wire_memory(client)
    snapshot = client.get("/policy/capabilities").json()
    (gate,) = snapshot["gate_capabilities"]
    assert gate["effects"]["SESSION"] == "DENY"
    assert gate["effects"]["RUN"] == "ALLOW"
    rejected = client.post(
        "/memory/proposals",
        json=_proposal(),
        headers={"Idempotency-Key": "policy-deny-1"},
    )
    assert rejected.status_code == 422, rejected.text
    problem = rejected.json()
    assert problem["title"] == "Memory Proposal policy"
    assert problem["detail"] == "policy deny: matched deny rule"


def test_default_policy_keeps_session_writes_working(client: TestClient) -> None:
    """默认策略下 SESSION 提案仍提交成功（接线不改变既有行为）。"""
    _wire_policy(client, load_policy("examples/config/policy.yaml"))
    _wire_memory(client)
    created = client.post(
        "/memory/proposals",
        json=_proposal(),
        headers={"Idempotency-Key": "policy-allow-1"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["decision"] == "ALLOW"
