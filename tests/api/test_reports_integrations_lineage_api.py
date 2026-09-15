"""reports / integrations / lineage 只读控制面端点测试（PLAN-043 WP-A，EC-02）。

- `GET /runs/{id}/deliverable`：persisted `deliverable.json` 产物；未知 run 404；
  无产物 available=false（不伪装空报告）。
- `GET /tool-providers`：catalog tool_providers 只读投影 + 三态健康；NATIVE=HEALTHY，
  外部未注册=UNKNOWN；无管理动作（供应链治理面）。
- `GET /runs/{id}/lineage`：evidence/claim 投影 typed 节点/边（确定性）；未知 run 404；
  全局血缘恒不可用（G9）。
"""

from __future__ import annotations

import json
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.core import ID
from packages.domain.enums import TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.run import ResearchRun


def _seed_run(client: TestClient) -> str:
    deps = cast(Any, client.app).state.deps
    run_id = str(ID.generate().value)
    deps.run_registry[run_id] = ResearchRun(id=ID(run_id), project_id="p", protocol_id="proto")
    return run_id


def _seed_lineage_truth(client: TestClient, run_id: str) -> None:
    deps = cast(Any, client.app).state.deps
    assert deps.ledger is not None
    ledger = deps.ledger
    ledger.register_source(
        SourceRecord(
            origin="paper://lineage-2024",
            content_digest="sha256:" + "a" * 64,
            trust_label=TrustLabel.VERIFIED_SOURCE,
        )
    )
    ledger.register_evidence(
        Evidence(
            id="ev-lineage",
            source_ref="paper://lineage-2024",
            content_digest="sha256:" + "b" * 64,
            run_id=run_id,
            artifact_id="artifact-lineage",
            model_refs=("model-alpha",),
        )
    )
    ledger.register_claim(
        Claim(
            id="claim-lineage", statement="Method X improves accuracy", status=ClaimStatus.PROPOSED
        )
    )
    ledger.attach_relation(
        EvidenceRelation(
            claim_id="claim-lineage",
            evidence_id="ev-lineage",
            relation=EvidenceRelationType.SUPPORTS,
        )
    )


# ---------------------------------------------------------------- deliverable


def test_deliverable_store_missing_is_503(client: TestClient) -> None:
    """artifact store 未配置时 503（与 /artifacts 诚实边界一致，不伪装空态）。"""
    run_id = _seed_run(client)
    response = client.get(f"/runs/{run_id}/deliverable")
    assert response.status_code == 503


def test_deliverable_absent_is_honest_empty(run_ready_client: TestClient) -> None:
    """store 存在但 run 无 deliverable 产物 → available=false + reason。"""
    run_id = _seed_run(run_ready_client)
    response = run_ready_client.get(f"/runs/{run_id}/deliverable")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["available"] is False
    assert payload["deliverable"] == {}
    assert payload["reason"]


def test_deliverable_unknown_run_is_404(client: TestClient) -> None:
    response = client.get("/runs/does-not-exist/deliverable")
    assert response.status_code == 404


def test_deliverable_reads_persisted_artifact(run_ready_client: TestClient) -> None:
    """完成 M12 参考链的 run 产出 deliverable.json；端点读回 persisted 产物。"""
    start = run_ready_client.post(
        "/projects/example-project/runs",
        json={"protocol_path": "sort_analysis_v1.yaml"},
        headers={"Idempotency-Key": "deliverable-1"},
    )
    assert start.status_code == 200, start.text
    run_id = start.json()["id"]
    deps = cast(Any, run_ready_client.app).state.deps
    assert deps.artifacts is not None
    artifact_id = f"{run_id}:deliverable.json"
    if deps.artifacts.meta(artifact_id) is None:
        # 部分装配不落产物：注入受控 deliverable 以验证读回路径。
        from packages.domain.artifacts import Artifact
        from packages.domain.core import Digest

        content = json.dumps({"run_id": run_id, "objective": "study"}).encode("utf-8")
        deps.artifacts.put(
            Artifact(
                id=artifact_id,
                digest=Digest.of_bytes(content),
                size_bytes=len(content),
                media_type="application/json",
                source_refs=[],
                classification="research_deliverable",
            ),
            content,
        )
    response = run_ready_client.get(f"/runs/{run_id}/deliverable")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["available"] is True
    assert payload["run_id"] == run_id
    assert payload["artifact_id"] == artifact_id
    assert payload["deliverable"]["run_id"] == run_id


# -------------------------------------------------------------- tool providers


def test_tool_providers_lists_catalog_with_health(client: TestClient) -> None:
    response = client.get("/tool-providers")
    assert response.status_code == 200, response.text
    payload = response.json()
    providers = {item["id"]: item for item in payload["providers"]}
    assert "openhands_workspace" in providers
    native = providers["openhands_workspace"]
    assert native["kind"] == "NATIVE"
    assert native["health"] == "HEALTHY"
    # 外部 provider（REST）未注册实例时诚实收敛为 UNKNOWN，不伪装健康。
    external = next(
        (item for item in payload["providers"] if item["kind"] != "NATIVE"),
        None,
    )
    assert external is not None
    assert external["health"] == "UNKNOWN"
    # PLAN-060 起治理写面在 /tool-provider-registrations，本端点随之标记可管理
    # （目录本身仍是只读：只反映 examples 契约与已批准注册）。
    assert payload["management_available"] is True
    assert payload["management_reason"] is None


def test_tool_providers_is_deterministically_sorted(client: TestClient) -> None:
    ids = [item["id"] for item in client.get("/tool-providers").json()["providers"]]
    assert ids == sorted(ids)


# -------------------------------------------------------------------- lineage


def test_lineage_projects_run_evidence_and_claims(client: TestClient) -> None:
    run_id = _seed_run(client)
    _seed_lineage_truth(client, run_id)
    response = client.get(f"/runs/{run_id}/lineage")
    assert response.status_code == 200, response.text
    payload = response.json()
    kinds = {node["kind"] for node in payload["nodes"]}
    assert {"source", "evidence", "artifact", "model", "claim"} <= kinds
    relations = {edge["relation"] for edge in payload["edges"]}
    assert {"cited_by", "materialized_as", "produced_with", "supports"} <= relations
    # 全局血缘诚实锁定。
    assert payload["global_lineage_available"] is False
    assert payload["degraded"] is False


def test_lineage_is_deterministic(client: TestClient) -> None:
    run_id = _seed_run(client)
    _seed_lineage_truth(client, run_id)
    first = client.get(f"/runs/{run_id}/lineage").json()
    second = client.get(f"/runs/{run_id}/lineage").json()
    assert first == second


def test_lineage_unknown_run_is_404(client: TestClient) -> None:
    response = client.get("/runs/does-not-exist/lineage")
    assert response.status_code == 404


def test_lineage_empty_for_run_without_refs(client: TestClient) -> None:
    run_id = _seed_run(client)
    payload = client.get(f"/runs/{run_id}/lineage").json()
    assert payload["nodes"] == []
    assert payload["edges"] == []
