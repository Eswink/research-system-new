"""Control Plane API 测试：Artifact 浏览/元数据/下载（PLAN-20260910-037 WP-C）。

诚实边界：store 缺失 503、未知 404、tombstone 410、超限 413；
ledger 是 run→artifact 的正式关联来源。
"""

from __future__ import annotations

import hashlib
from typing import Any, cast

from fastapi.testclient import TestClient

from adapters.fakes.artifact_store import FakeArtifactStore
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest
from packages.domain.enums import ArtifactState, TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.run import ResearchRun


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _seed_run(client: TestClient) -> str:
    """注册一个存在的 run（ID 为合法 UUID，与域不变量一致）。"""
    run_id = str(ID.generate().value)
    deps = _deps(client)
    deps.run_registry[run_id] = ResearchRun(id=ID(run_id), project_id="p", protocol_id="proto")
    return run_id


def _content() -> bytes:
    return b'{"result": "ok"}'


def _artifact(artifact_id: str, payload: bytes, size_bytes: int | None = None) -> Artifact:
    return Artifact(
        id=artifact_id,
        digest=Digest.of_bytes(payload),
        size_bytes=size_bytes if size_bytes is not None else len(payload),
        media_type="application/json",
        source_refs=["task:t-1"],
        classification="execution_result",
    )


def _seed_evidence(client: TestClient, run_id: str, artifact_id: str) -> None:
    deps = _deps(client)
    deps.ledger.register_source(
        SourceRecord(
            origin="paper://wp-c",
            content_digest="sha256:" + "a" * 64,
            trust_label=TrustLabel.VERIFIED_SOURCE,
        )
    )
    deps.ledger.register_evidence(
        Evidence(
            id="ev-wpc",
            source_ref="paper://wp-c",
            content_digest="sha256:" + "b" * 64,
            run_id=run_id,
            artifact_id=artifact_id,
        )
    )
    deps.ledger.register_claim(Claim(id="claim-wpc", statement="x", status=ClaimStatus.PROPOSED))
    deps.ledger.attach_relation(
        EvidenceRelation(
            claim_id="claim-wpc", evidence_id="ev-wpc", relation=EvidenceRelationType.SUPPORTS
        )
    )


def test_run_artifacts_store_missing_is_503(client: TestClient) -> None:
    run_id = _seed_run(client)
    assert _deps(client).artifacts is None
    response = client.get(f"/runs/{run_id}/artifacts")
    assert response.status_code == 503


def test_run_artifacts_unknown_run_is_404(client: TestClient) -> None:
    _deps(client).artifacts = FakeArtifactStore()
    response = client.get("/runs/run-does-not-exist/artifacts")
    assert response.status_code == 404


def test_list_metadata_and_content_flow(client: TestClient) -> None:
    payload = _content()
    _deps(client).artifacts = FakeArtifactStore()
    _deps(client).artifacts.put(_artifact("t-1:result.json", payload), payload)
    run_id = _seed_run(client)
    _seed_evidence(client, run_id, "t-1:result.json")
    listed = client.get(f"/runs/{run_id}/artifacts")
    assert listed.status_code == 200, listed.text
    rows = listed.json()
    assert [row["id"] for row in rows] == ["t-1:result.json"]
    assert rows[0]["verified"] is None  # 列表不做内容校验（不伪装已验证）
    meta = client.get("/artifacts/t-1:result.json")
    assert meta.status_code == 200
    assert meta.json()["verified"] is True
    content = client.get("/artifacts/t-1:result.json/content")
    assert content.status_code == 200
    assert content.content == payload
    assert content.headers["x-content-type-options"] == "nosniff"
    assert content.headers["content-disposition"].startswith("inline;")
    assert content.headers["etag"] == f'"sha256:{hashlib.sha256(payload).hexdigest()}"'


def test_unknown_artifact_is_404(client: TestClient) -> None:
    _deps(client).artifacts = FakeArtifactStore()
    assert client.get("/artifacts/nope").status_code == 404
    assert client.get("/artifacts/nope/content").status_code == 404


def test_tombstoned_artifact_content_is_410(client: TestClient) -> None:
    store = FakeArtifactStore()
    payload = _content()
    store.put(_artifact("t-2:gone", payload), payload)
    _deps(client).artifacts = store
    # 合法流转：STAGED→VERIFIED→ACTIVE→DELETED_TOMBSTONE（retention 路径同构）
    store.mark("t-2:gone", ArtifactState.VERIFIED)
    store.mark("t-2:gone", ArtifactState.ACTIVE)
    store.delete("t-2:gone")
    meta = client.get("/artifacts/t-2:gone")
    assert meta.json()["state"] == "DELETED_TOMBSTONE"
    content = client.get("/artifacts/t-2:gone/content")
    assert content.status_code == 410


def test_oversized_artifact_is_413(client: TestClient) -> None:
    store = FakeArtifactStore()
    payload = _content()
    oversized = _artifact("t-3:big", payload, size_bytes=10 * 1024 * 1024 + 1)
    store.put(oversized, payload)
    _deps(client).artifacts = store
    response = client.get("/artifacts/t-3:big/content")
    assert response.status_code == 413


def test_binary_media_downloads_not_inline(client: TestClient) -> None:
    store = FakeArtifactStore()
    payload = b"\x89PNG fake"
    artifact = Artifact(
        id="t-4:blob",
        digest=Digest.of_bytes(payload),
        size_bytes=len(payload),
        media_type="application/octet-stream",
    )
    store.put(artifact, payload)
    _deps(client).artifacts = store
    response = client.get("/artifacts/t-4:blob/content")
    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith("attachment;")
    assert response.headers["content-type"].startswith("application/octet-stream")


def _put_text(store: FakeArtifactStore, artifact_id: str, text: str) -> None:
    payload = text.encode("utf-8")
    store.put(_artifact(artifact_id, payload), payload)


def test_artifact_diff_reports_line_changes(client: TestClient) -> None:
    """两侧都是 persisted 制品：文本变更给出行级 diff（PLAN-047）。"""
    store = FakeArtifactStore()
    _put_text(store, "t-5:v1", '{"a": 1}\n')
    _put_text(store, "t-5:v2", '{"a": 2}\n{"b": 3}\n')
    _deps(client).artifacts = store
    response = client.get("/artifacts/t-5:v1/diff/t-5:v2")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["available"] is True
    assert body["identical"] is False
    assert body["comparison"] == "ARTIFACT_CONTENT"
    assert body["stats"]["added"] >= 1 and body["stats"]["removed"] >= 1
    assert any(line["kind"] == "ADDED" and '"b": 3' in line["text"] for line in body["lines"])


def test_artifact_diff_same_digest_is_identical(client: TestClient) -> None:
    store = FakeArtifactStore()
    _put_text(store, "t-6:v1", "same\n")
    _put_text(store, "t-6:v2", "same\n")
    _deps(client).artifacts = store
    body = client.get("/artifacts/t-6:v1/diff/t-6:v2").json()
    assert body["identical"] is True
    assert body["lines"] == []
    assert body["reason"] is None


def test_artifact_diff_binary_is_unavailable_with_reason(client: TestClient) -> None:
    """二进制不是错误：200 + available=false + reason（不伪造"看起来一样"）。"""
    store = FakeArtifactStore()
    payload = b"\x00\x01PNG\xff"
    store.put(_artifact("t-7:blob-a", payload), payload)
    store.put(_artifact("t-7:blob-b", payload + b"\x02"), payload + b"\x02")
    _deps(client).artifacts = store
    body = client.get("/artifacts/t-7:blob-a/diff/t-7:blob-b").json()
    assert body["available"] is False
    assert body["reason"] == "NOT_TEXT"
    assert body["lines"] == []


def test_artifact_diff_unknown_side_is_404_and_missing_store_503(client: TestClient) -> None:
    store = FakeArtifactStore()
    _put_text(store, "t-8:v1", "x\n")
    _deps(client).artifacts = store
    assert client.get("/artifacts/t-8:v1/diff/ghost").status_code == 404
    assert client.get("/artifacts/ghost/diff/t-8:v1").status_code == 404
    _deps(client).artifacts = None
    assert client.get("/artifacts/t-8:v1/diff/t-8:v1").status_code == 503
