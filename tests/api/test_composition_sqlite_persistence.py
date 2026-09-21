"""SQLite 组成浮现测试（PLAN-040 WP-A）。

证明 dev 路径不再依赖进程内 Fake/503：
- assemble() 返回 SqliteArtifactStore/SqliteMemoryStore/SqliteExperimentStore/
  SqliteWorkerRegistry 类型（Port 不变，实现升级）；
- artifact 内容与 memory/实验记录跨"重启"（新 assemble 实例 + 同 db 文件与
  blob 目录）仍可读取——旧 FakeArtifactStore 在此必然失败；
- GET /health 暴露组成摘要（status/version/composition/pricing_degraded）。
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

from fastapi.testclient import TestClient

from adapters.sqlite.artifact_store import SqliteArtifactStore
from adapters.sqlite.experiment_store import SqliteExperimentStore
from adapters.sqlite.memory_store import SqliteMemoryStore
from adapters.sqlite.worker_registry import SqliteWorkerRegistry
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from packages.domain.enums import ArtifactState
from services.api.app import create_app
from services.api.composition import assemble
from services.api.settings import ApiSettings


def _settings(tmp_path: Path) -> ApiSettings:
    return ApiSettings(db_path=str(tmp_path.joinpath("control.db")))


def _artifact(content: bytes, artifact_id: str = "a-1") -> Artifact:
    return Artifact(
        id=artifact_id,
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type="text/plain",
        created_by="agent-1",
        source_refs=["task:a-1"],
        state=ArtifactState.STAGED,
    )


def test_assemble_sqlite_injects_durable_stores(tmp_path: Path) -> None:
    deps = assemble(_settings(tmp_path))
    try:
        assert isinstance(deps.artifacts, SqliteArtifactStore)
        assert isinstance(deps.memory, SqliteMemoryStore)
        assert isinstance(deps.experiment_store, SqliteExperimentStore)
        assert isinstance(deps.worker_registry, SqliteWorkerRegistry)
    finally:
        deps.close()


def test_artifact_survives_reassemble(tmp_path: Path) -> None:
    content = b"durable analysis report"
    deps = assemble(_settings(tmp_path))
    try:
        artifacts = cast(SqliteArtifactStore, deps.artifacts)
        artifacts.put(_artifact(content), content)
        artifacts.mark("a-1", ArtifactState.VERIFIED)
        artifacts.mark("a-1", ArtifactState.ACTIVE)
    finally:
        deps.close()

    restarted = assemble(_settings(tmp_path))
    try:
        artifacts = cast(SqliteArtifactStore, restarted.artifacts)
        assert artifacts.get("a-1") == content
        assert artifacts.verify("a-1") is True
        refs = {item.id for item in artifacts.list_refs()}
        # 装配同时种入协议**声明**的输入制品（GOAL-010 EC-02）——它们是组合根行为，
        # 所以这条精确集合断言把「a-1 幸存」与「声明输入在装配时被种入」一起钉住
        # （此前这里只断言 a-1，等于没有覆盖后者）。
        from services.api.demo import DECLARED_INPUTS

        assert refs == {"a-1", *DECLARED_INPUTS}
    finally:
        restarted.close()


def test_health_endpoint_reports_composition(tmp_path: Path) -> None:
    deps = assemble(_settings(tmp_path))
    try:
        app = create_app(deps)
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            payload = response.json()
            assert payload["status"] == "ok"
            assert payload["composition"] == "sqlite"
            assert isinstance(payload["pricing_degraded"], bool)
    finally:
        deps.close()
