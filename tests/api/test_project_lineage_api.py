"""项目级来源血缘端点测试（G9 / GOAL-20260915-002 EC-01）。

`GET /projects/{id}/lineage`：项目内各 run 的血缘投影**合并**成一张图。
跨 run 关系由共享节点表达（同一来源/制品/模型被多个 run 引用 ⇒ `shared=true`），
不猜测连边；数据集/提示词只有未连边清单（引用关系无记录面 ⇒ `reference_recording`
如实返回 `NOT_RECORDED` + 原因）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.core import ID, Timestamp
from packages.domain.enums import TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.library import LibraryResource, ResourceKind, ResourceStatus
from packages.domain.run import ResearchRun
from services.api.dto.inspection import ProjectLineageDto
from services.api.run_access import save_run

PROJECT_ID = "example-project"

SHARED_SOURCE = "paper://shared-2024"


@dataclass(frozen=True)
class _EvidenceSeed:
    """一条 evidence + 其 claim 与 SUPPORTS 关系（run 归属由 run_id 给定）。"""

    run_id: str
    evidence_id: str
    claim_id: str
    source_ref: str
    artifact_id: str | None = None
    model_refs: tuple[str, ...] = ()


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _seed_run(client: TestClient, run_id: str) -> None:
    """按生产口径落 run：`save_run` 双写 runs store 与 registry（store 是读取真相）。"""
    deps = _deps(client)
    save_run(
        deps,
        ResearchRun(id=ID(run_id), project_id=PROJECT_ID, protocol_id="proto"),
    )


def _seed_evidence(client: TestClient, seed: _EvidenceSeed) -> None:
    deps = _deps(client)
    ledger = deps.ledger
    assert ledger is not None
    ledger.register_source(
        SourceRecord(
            origin=seed.source_ref,
            content_digest="sha256:" + "a" * 64,
            trust_label=TrustLabel.VERIFIED_SOURCE,
        )
    )
    ledger.register_evidence(
        Evidence(
            id=seed.evidence_id,
            source_ref=seed.source_ref,
            content_digest="sha256:" + "b" * 64,
            run_id=seed.run_id,
            artifact_id=seed.artifact_id,
            model_refs=seed.model_refs,
        )
    )
    ledger.register_claim(
        Claim(id=seed.claim_id, statement=f"claim of {seed.run_id}", status=ClaimStatus.PROPOSED)
    )
    ledger.attach_relation(
        EvidenceRelation(
            claim_id=seed.claim_id,
            evidence_id=seed.evidence_id,
            relation=EvidenceRelationType.SUPPORTS,
        )
    )


def _seed_library(client: TestClient, *, name: str, kind: ResourceKind) -> str:
    deps = _deps(client)
    store = deps.library_store
    assert store is not None
    now = Timestamp.now()
    resource = LibraryResource(
        id=str(ID.generate().value),
        project_id=PROJECT_ID,
        kind=kind,
        name=name,
        description="",
        content_ref=None,
        tags=(),
        status=ResourceStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    store.save_resource(resource)
    return resource.id


def _seeded(client: TestClient) -> tuple[str, str]:
    """两个 run 共用同一来源与模型，各自另有独立来源。"""
    run_a, run_b = str(ID.generate().value), str(ID.generate().value)
    _seed_run(client, run_a)
    _seed_run(client, run_b)
    _seed_evidence(
        client,
        _EvidenceSeed(
            run_id=run_a,
            evidence_id=f"ev-a-{run_a}",
            claim_id=f"claim-a-{run_a}",
            source_ref=SHARED_SOURCE,
            artifact_id=f"artifact-a-{run_a}",
            model_refs=("model-shared",),
        ),
    )
    _seed_evidence(
        client,
        _EvidenceSeed(
            run_id=run_a,
            evidence_id=f"ev-a2-{run_a}",
            claim_id=f"claim-a2-{run_a}",
            source_ref=f"paper://only-a-{run_a}",
        ),
    )
    _seed_evidence(
        client,
        _EvidenceSeed(
            run_id=run_b,
            evidence_id=f"ev-b-{run_b}",
            claim_id=f"claim-b-{run_b}",
            source_ref=SHARED_SOURCE,
            model_refs=("model-shared",),
        ),
    )
    return run_a, run_b


def test_project_lineage_merges_runs_and_marks_shared_nodes(run_ready_client: TestClient) -> None:
    run_a, run_b = _seeded(run_ready_client)

    response = run_ready_client.get(f"/projects/{PROJECT_ID}/lineage")

    assert response.status_code == 200
    view = ProjectLineageDto.model_validate(response.json())
    assert view.project_id == PROJECT_ID
    assert view.run_count >= 2
    assert view.degraded is False

    node_ids = {node.id for node in view.nodes}
    assert f"run:{run_a}" in node_ids and f"run:{run_b}" in node_ids
    # 共享来源/模型节点：由两个 run 共同贡献 ⇒ shared=true 且 run_ids 含两者
    shared_source = next(node for node in view.nodes if node.id == f"source:{SHARED_SOURCE}")
    assert shared_source.shared is True
    assert set(shared_source.run_ids) >= {run_a, run_b}
    shared_model = next(node for node in view.nodes if node.id == "model:model-shared")
    assert shared_model.shared is True
    # 只有一个 run 贡献的节点不得被标成共享
    only_a = next(node for node in view.nodes if node.id == f"source:paper://only-a-{run_a}")
    assert only_a.shared is False and only_a.run_ids == [run_a]
    # run 节点不共享（每个 run 只贡献自己）
    assert next(node for node in view.nodes if node.id == f"run:{run_a}").shared is False


def test_project_lineage_reports_library_resources_without_edges(
    run_ready_client: TestClient,
) -> None:
    _seeded(run_ready_client)
    dataset_id = _seed_library(run_ready_client, name="benchmark-v1", kind=ResourceKind.DATASET)
    prompt_id = _seed_library(run_ready_client, name="critic-v2", kind=ResourceKind.PROMPT)

    view = ProjectLineageDto.model_validate(
        run_ready_client.get(f"/projects/{PROJECT_ID}/lineage").json()
    )

    listed = {resource.id: resource for resource in view.library_resources}
    assert dataset_id in listed and prompt_id in listed
    assert listed[dataset_id].kind == "dataset"
    assert listed[prompt_id].kind == "prompt"
    assert listed[dataset_id].status == ResourceStatus.ACTIVE.value
    # 资源不得出现在任何边里（引用关系无记录面 ⇒ 不猜测连边）
    assert all("dataset:" not in edge.source for edge in view.edges)
    assert all("prompt:" not in edge.target for edge in view.edges)
    assert view.reference_recording == "NOT_RECORDED"
    assert view.reference_recording_reason is not None
    assert "无记录面" in view.reference_recording_reason


def test_project_lineage_edges_are_full_rule_set(run_ready_client: TestClient) -> None:
    _seeded(run_ready_client)

    view = ProjectLineageDto.model_validate(
        run_ready_client.get(f"/projects/{PROJECT_ID}/lineage").json()
    )

    kinds = {node.kind for node in view.nodes}
    assert {"run", "source", "evidence", "claim"} <= kinds
    assert "artifact" in kinds and "model" in kinds
    relations = {edge.relation for edge in view.edges}
    assert {"cited_by", "supports", "materialized_as", "produced_with"} <= relations


def test_project_lineage_is_deterministic(run_ready_client: TestClient) -> None:
    _seeded(run_ready_client)
    url = f"/projects/{PROJECT_ID}/lineage"
    assert run_ready_client.get(url).json() == run_ready_client.get(url).json()


def test_project_lineage_unknown_project_is_empty_not_404(run_ready_client: TestClient) -> None:
    """未知项目返回空图（与 /projects/{id}/runs、/projects/{id}/experiments 同口径）。"""
    response = run_ready_client.get("/projects/does-not-exist/lineage")

    assert response.status_code == 200
    view = ProjectLineageDto.model_validate(response.json())
    assert view.project_id == "does-not-exist"
    assert view.run_count == 0
    assert view.nodes == [] and view.edges == []


def test_run_lineage_still_scoped_to_its_own_run(run_ready_client: TestClient) -> None:
    """run 级血缘不得因为项目级投影的引入而跨 run 泄漏节点。"""
    run_a, run_b = _seeded(run_ready_client)

    view = run_ready_client.get(f"/runs/{run_a}/lineage").json()

    ids = {node["id"] for node in view["nodes"]}
    assert f"source:{SHARED_SOURCE}" in ids
    assert all(run_b not in node_id for node_id in ids)
    assert view["global_lineage_available"] is False
