"""Console 集成测试专用 FastAPI 装配（PLAN-20260908-034 T30）。

复用 tests/api/run_fixtures 的 Fake Port 装配（run_fixtures.make_run_ready_deps），
通过真实 uvicorn HTTP 服务驱动浏览器 e2e：API 层真实，外部模型/工具为确定性替身。
不依赖真实凭据或付费 LLM。

运行：uv run --frozen --no-sync python -m uvicorn tests.api.console_api_app:app \
      --host 127.0.0.1 --port 8011

受控 fixture（只服务 live e2e，不进入任何生产路径）：
- 制品内容 diff 的两份 JSON（PLAN-047）；
- 工作区快照：临时快照根 + 两个内容寻址快照 + 一个记录了两侧 digest 的 run
  （PLAN-20260915-058；控制面不持久化 run→工作区绑定，这里显式落 evidence 记录）。
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from adapters.workspace.bundle import tree_digest
from adapters.workspace.snapshot_reader import FileSnapshotReader
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest, Timestamp
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
from services.api.app import create_app
from services.api.composition import ApiDeps
from services.api.run_access import save_run
from tests.api.run_fixtures import make_run_ready_deps

# live 制品 diff 正向链需要 store 里有真实内容：两份受控 JSON（执行前/后）。
LIVE_DIFF_ARTIFACTS: tuple[tuple[str, bytes], ...] = (
    ("live-fixture:before.json", b'{\n  "status": "running",\n  "attempts": 1\n}\n'),
    ("live-fixture:after.json", b'{\n  "status": "succeeded",\n  "attempts": 1\n}\n'),
)

# live 快照链的受控 run（UUID 形式；evidence 记录快照 digest，端点据此回答）。
LIVE_SNAPSHOT_RUN_ID = "11111111-1111-4111-8111-111111111111"
LIVE_SNAPSHOT_FILES: tuple[tuple[str, bytes], ...] = (
    ("notes.md", b"# live snapshot fixture\n"),
    ("src/main.py", b"print('before')\n"),
)
LIVE_SNAPSHOT_FILES_AFTER: tuple[tuple[str, bytes], ...] = (
    ("notes.md", b"# live snapshot fixture\n"),
    ("src/main.py", b"print('after')\n"),
    ("src/util.py", b"def helper():\n    return 1\n"),
)


def _seed_artifact(artifact_id: str, payload: bytes) -> Artifact:
    return Artifact(
        id=artifact_id,
        digest=Digest.of_bytes(payload),
        size_bytes=len(payload),
        media_type="application/json",
        source_refs=["task:live-fixture"],
        classification="execution_result",
    )


def _with_artifacts(deps: ApiDeps) -> ApiDeps:
    """控制面只读链与 Fake store 共享实例：放入 live diff 的两份受控内容。"""
    store = deps.artifacts
    if store is None:
        return deps
    for artifact_id, payload in LIVE_DIFF_ARTIFACTS:
        store.put(_seed_artifact(artifact_id, payload), payload)
    return deps


def _write_snapshot(root: Path, files: tuple[tuple[str, bytes], ...]) -> str:
    """把一份受控内容写成内容寻址快照，返回其 tree digest。"""
    staged = root / ".staging"
    for relative, payload in files:
        target = staged / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    digest = tree_digest(staged)
    staged.replace(root / ".snapshots" / digest.split(":", 1)[1])
    return digest


def _seed_snapshot_evidence(deps: ApiDeps, run_id: str, *, before: str, after: str) -> None:
    ledger = deps.ledger
    if ledger is None:
        return
    ledger.register_source(
        SourceRecord(
            origin="workspace://live-snapshot-fixture",
            content_digest="sha256:" + "a" * 64,
            trust_label=TrustLabel.VERIFIED_SOURCE,
        )
    )
    ledger.register_evidence(
        Evidence(
            id="ev-live-snapshot",
            source_ref="workspace://live-snapshot-fixture",
            content_digest="sha256:" + "b" * 64,
            run_id=run_id,
            captured_at=Timestamp.now(),
            workspace_snapshot_before=before,
            workspace_snapshot_after=after,
        )
    )
    ledger.register_claim(
        Claim(id="claim-live-snapshot", statement="live snapshot", status=ClaimStatus.PROPOSED)
    )
    ledger.attach_relation(
        EvidenceRelation(
            claim_id="claim-live-snapshot",
            evidence_id="ev-live-snapshot",
            relation=EvidenceRelationType.SUPPORTS,
        )
    )


def _with_snapshots(deps: ApiDeps) -> ApiDeps:
    """临时快照根 + 两个受控快照 + 记录两侧 digest 的 run（live e2e 专用）。"""
    root = Path(tempfile.mkdtemp(prefix="research-os-live-snapshots-"))
    (root / ".snapshots").mkdir(parents=True, exist_ok=True)
    before = _write_snapshot(root, LIVE_SNAPSHOT_FILES)
    after = _write_snapshot(root, LIVE_SNAPSHOT_FILES_AFTER)
    deps.workspace_snapshots = FileSnapshotReader(root)
    save_run(
        deps,
        ResearchRun(id=ID(LIVE_SNAPSHOT_RUN_ID), project_id="example-project", protocol_id="proto"),
    )
    _seed_snapshot_evidence(deps, LIVE_SNAPSHOT_RUN_ID, before=before, after=after)
    return deps


# 单一进程内装配：SQLite in-memory + Fake runtime/gateway/ledger。
app = create_app(_with_snapshots(_with_artifacts(make_run_ready_deps())))
