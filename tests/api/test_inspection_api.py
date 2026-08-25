"""Control Plane API 测试：Evidence / Claim Map / Budget / Audit Export。

证明（M13 DoD 9/10/11）：
- Workspace/Experiment/Evidence/Claim inspection 来自 persisted truth；
- Budget/Usage 来自正式 UsageLedger（UNKNOWN ≠ 0）；
- Audit/Export 来自 persisted state（不导出 UI 内存）；
- 页面只 render persisted truth（无 UI click → VERIFIED；Claim 状态改变
  必须经过正式 use case/gate——本层只读）。
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.budget import LedgerCostStatus, ResourceType, UsageLedgerEntry
from packages.domain.core import Timestamp
from packages.domain.enums import TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)


def _seed_evidence_truth(client: TestClient, run_id: str) -> None:
    """受控注入 persisted evidence/claim（正式 ledger 登记面，M10 语义）。"""
    deps = cast(Any, client.app).state.deps
    assert deps.ledger is not None
    ledger = deps.ledger
    ledger.register_source(
        SourceRecord(
            origin="paper://example-2024",
            content_digest="sha256:" + "a" * 64,
            trust_label=TrustLabel.VERIFIED_SOURCE,
        )
    )
    evidence = Evidence(
        id="ev-1",
        source_ref="paper://example-2024",
        content_digest="sha256:" + "b" * 64,
        run_id=run_id,
        experiment_run_id="exp-1",
        artifact_id="artifact-1",
    )
    ledger.register_evidence(evidence)
    ledger.register_claim(
        Claim(id="claim-1", statement="Method X improves accuracy", status=ClaimStatus.PROPOSED)
    )
    ledger.attach_relation(
        EvidenceRelation(
            claim_id="claim-1", evidence_id="ev-1", relation=EvidenceRelationType.SUPPORTS
        )
    )
    ledger.register_claim(
        Claim(id="claim-2", statement="Unsupported statement", status=ClaimStatus.DRAFT)
    )


def _seed_usage_truth(client: TestClient, run_id: str) -> None:
    """受控注入正式 UsageLedger 条目（KNOWN 与 UNKNOWN 并存）。"""
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
        )
    )


def test_evidence_from_persisted_truth(client: TestClient) -> None:
    """evidence inspection 来自 persisted ledger（页面只 render）。"""
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun

    deps = cast(Any, client.app).state.deps
    run_id = str(ID.generate().value)
    deps.run_registry[run_id] = ResearchRun(id=ID(run_id), project_id="p", protocol_id="proto")
    _seed_evidence_truth(client, run_id)
    response = client.get(f"/runs/{run_id}/evidence")
    assert response.status_code == 200, response.text
    items = response.json()
    assert len(items) == 1
    assert items[0]["id"] == "ev-1"
    assert items[0]["source_ref"] == "paper://example-2024"


def test_claim_map_marks_unsupported(client: TestClient) -> None:
    """unsupported claim（无 relation）显式标记（视觉语义）。"""
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun

    deps = cast(Any, client.app).state.deps
    run_id = str(ID.generate().value)
    deps.run_registry[run_id] = ResearchRun(id=ID(run_id), project_id="p", protocol_id="proto")
    _seed_evidence_truth(client, run_id)
    response = client.get(f"/runs/{run_id}/claims")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload["claims"]) == 2
    assert "claim-2" in payload["unsupported_claims"]
    claim_1 = next(item for item in payload["claims"] if item["id"] == "claim-1")
    assert claim_1["relations"][0]["relation"] == "SUPPORTS"


def test_claim_map_detects_contradiction(client: TestClient) -> None:
    """contradiction（SUPPORTS + REFUTES 并存）显式标记。"""
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun

    deps = cast(Any, client.app).state.deps
    run_id = str(ID.generate().value)
    deps.run_registry[run_id] = ResearchRun(id=ID(run_id), project_id="p", protocol_id="proto")
    _seed_evidence_truth(client, run_id)
    ledger = deps.ledger
    ledger.register_evidence(
        Evidence(
            id="ev-2",
            source_ref="paper://example-2024",
            content_digest="sha256:" + "c" * 64,
            run_id=run_id,
        )
    )
    ledger.attach_relation(
        EvidenceRelation(
            claim_id="claim-1", evidence_id="ev-2", relation=EvidenceRelationType.REFUTES
        )
    )
    response = client.get(f"/runs/{run_id}/claims")
    assert "claim-1" in response.json()["contradictory_claims"]


def test_budget_usage_unknown_not_zero(client: TestClient) -> None:
    """Budget/Usage：UNKNOWN 成本显式计数，禁止显示 0。"""
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun

    deps = cast(Any, client.app).state.deps
    run_id = str(ID.generate().value)
    deps.run_registry[run_id] = ResearchRun(id=ID(run_id), project_id="p", protocol_id="proto")
    _seed_usage_truth(client, run_id)
    response = client.get(f"/runs/{run_id}/usage")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["unknown_cost_entries"] == 1
    assert payload["total_estimated_cost_minor"] == 10
    unknown = next(item for item in payload["entries"] if item["cost_status"] == "UNKNOWN")
    assert unknown["estimated_cost_minor"] is None


def test_export_from_persisted_state(client: TestClient) -> None:
    """Audit/Export：来自 persisted state，不导出 UI 内存。"""
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun

    deps = cast(Any, client.app).state.deps
    run_id = str(ID.generate().value)
    deps.run_registry[run_id] = ResearchRun(
        id=ID(run_id), project_id="p", protocol_id="proto", state="SUCCEEDED"
    )
    _seed_evidence_truth(client, run_id)
    _seed_usage_truth(client, run_id)
    response = client.get(f"/runs/{run_id}/export")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["run_id"] == run_id
    assert payload["exported_from"] == "persisted-state"
    assert len(payload["evidence"]) == 1
    assert len(payload["claims"]) == 2
    assert payload["usage"]["unknown_cost_entries"] == 1


def test_claim_status_not_mutable_via_api(client: TestClient) -> None:
    """页面只 render persisted truth：无 API 端点可把 Claim 置为 VERIFIED
    （Claim 状态改变必须经过正式 use case/gate）。"""
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun

    deps = cast(Any, client.app).state.deps
    run_id = str(ID.generate().value)
    deps.run_registry[run_id] = ResearchRun(id=ID(run_id), project_id="p", protocol_id="proto")
    _seed_evidence_truth(client, run_id)
    # 不存在任何 mutating claim 端点
    response = client.post("/runs/x/claims/claim-1/verify", headers={"Idempotency-Key": "verify"})
    assert response.status_code == 404
