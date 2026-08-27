"""M13-R1 WP-S4：Experiment 只读视图来自 persisted truth。"""

from __future__ import annotations

from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.enums import TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)


def _seed_experiment_truth(client: TestClient, run_id: str) -> None:
    deps = cast(Any, client.app).state.deps
    ledger = deps.ledger
    ledger.register_source(
        SourceRecord(
            origin=f"paper://experiment-{run_id}",
            content_digest="sha256:" + "a" * 64,
            trust_label=TrustLabel.GENERATED,
        )
    )
    ledger.register_evidence(
        Evidence(
            id="ev-exp-1",
            source_ref=f"paper://experiment-{run_id}",
            content_digest="sha256:" + "b" * 64,
            run_id=run_id,
            experiment_run_id="exp-run-1",
            artifact_id=f"{run_id}:experiment_result.json",
            image_digest="sha256:" + "c" * 64,
            environment_digest="sha256:" + "d" * 64,
        )
    )
    ledger.register_claim(
        Claim(id="claim-exp-1", statement="experiment result", status=ClaimStatus.PROPOSED)
    )
    ledger.attach_relation(
        EvidenceRelation(
            claim_id="claim-exp-1",
            evidence_id="ev-exp-1",
            relation=EvidenceRelationType.SUPPORTS,
        )
    )


def test_experiment_view_from_persisted_truth(client: TestClient) -> None:
    """experiments 端点聚合 evidence 关联的 experiment run；页面只读。"""
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun

    deps = cast(Any, client.app).state.deps
    run_id = str(ID.generate().value)
    deps.run_registry[run_id] = ResearchRun(id=ID(run_id), project_id="p", protocol_id="proto")
    _seed_experiment_truth(client, run_id)

    response = client.get(f"/runs/{run_id}/experiments")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload["experiments"]) == 1
    experiment = payload["experiments"][0]
    assert experiment["experiment_run_id"] == "exp-run-1"
    assert f"{run_id}:experiment_result.json" in experiment["artifact_ids"]
    assert experiment["image_digest"].startswith("sha256:")
    assert experiment["reproduction_available"] is False
    assert "unavailable" in payload["reproduction_note"]


def test_experiment_view_isolated_per_run(client: TestClient) -> None:
    """experiment 视图按 run 隔离（他 run evidence 不泄漏）。"""
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun

    deps = cast(Any, client.app).state.deps
    run_a = str(ID.generate().value)
    run_b = str(ID.generate().value)
    for run_id in (run_a, run_b):
        deps.run_registry[run_id] = ResearchRun(id=ID(run_id), project_id="p", protocol_id="proto")
    _seed_experiment_truth(client, run_b)
    payload_a = client.get(f"/runs/{run_a}/experiments").json()
    assert payload_a["experiments"] == []
    payload_b = client.get(f"/runs/{run_b}/experiments").json()
    assert len(payload_b["experiments"]) == 1
