"""工作区快照只读控制面测试（G8 / GOAL-20260915-002 EC-03 / PLAN-20260915-058）。

锁住诚实口径：未配置快照根 → 503（不是空树）；digest 非法或未保留 → 404；
run 侧只报"记录过哪些 digest + 是否保留"，不推断 run→工作区绑定；
文件级 diff 只比元数据（路径/大小/sha256），并把 truncation 如实透传。
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, cast

from fastapi.testclient import TestClient

from adapters.workspace.snapshot_reader import FileSnapshotReader
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
from services.api.run_access import save_run

DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
DIGEST_MISSING = "sha256:" + "c" * 64


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _seed_run(client: TestClient) -> str:
    run_id = str(ID.generate().value)
    run = ResearchRun(id=ID(run_id), project_id="example-project", protocol_id="p")
    save_run(_deps(client), run)
    return run_id


def _write(directory: Path, relative: str, payload: bytes) -> None:
    target = directory / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)


def _snapshot(root: Path, digest: str, files: dict[str, bytes]) -> None:
    directory = root / ".snapshots" / digest.split(":", 1)[1]
    for relative, payload in files.items():
        _write(directory, relative, payload)


def _configure(client: TestClient, root: Path) -> None:
    _deps(client).workspace_snapshots = FileSnapshotReader(root)


def _record_snapshots(client: TestClient, run_id: str, *, before: str, after: str) -> None:
    """按生产口径落 evidence + claim + SUPPORTS（run 归属由 evidence.run_id 给出）。"""
    deps = _deps(client)
    ledger = deps.ledger
    assert ledger is not None
    evidence_id = f"ev-{run_id}"
    ledger.register_source(
        SourceRecord(
            origin="workspace://run",
            content_digest="sha256:" + "a" * 64,
            trust_label=TrustLabel.VERIFIED_SOURCE,
        )
    )
    ledger.register_evidence(
        Evidence(
            id=evidence_id,
            source_ref="workspace://run",
            content_digest="sha256:" + "b" * 64,
            run_id=run_id,
            workspace_snapshot_before=before,
            workspace_snapshot_after=after,
        )
    )
    ledger.register_claim(
        Claim(
            id=f"claim-{run_id}",
            statement="run workspace snapshots",
            status=ClaimStatus.PROPOSED,
        )
    )
    ledger.attach_relation(
        EvidenceRelation(
            claim_id=f"claim-{run_id}",
            evidence_id=evidence_id,
            relation=EvidenceRelationType.SUPPORTS,
        )
    )


def test_capability_is_honest_when_root_not_configured(client: TestClient) -> None:
    response = client.get("/workspace-snapshots")

    assert response.status_code == 200
    body = response.json()
    assert body["configured"] is False
    assert body["retained_snapshots"] == 0
    assert "RESEARCHOS_WORKSPACE_SNAPSHOT_ROOT" in body["note"]


def test_capability_counts_retained_snapshots(client: TestClient, tmp_path: Path) -> None:
    _snapshot(tmp_path, DIGEST_A, {"a.txt": b"a"})
    _snapshot(tmp_path, DIGEST_B, {"b.txt": b"b"})
    _configure(client, tmp_path)

    body = client.get("/workspace-snapshots").json()

    assert body["configured"] is True
    assert body["retained_snapshots"] == 2
    assert body["max_files_per_snapshot"] > 0


def test_snapshot_files_without_configuration_is_503(client: TestClient, tmp_path: Path) -> None:
    _snapshot(tmp_path, DIGEST_A, {"a.txt": b"a"})

    response = client.get(f"/workspace-snapshots/{DIGEST_A}/files")

    assert response.status_code == 503
    assert "snapshot root" in response.json()["detail"].lower()


def test_snapshot_files_returns_tree_with_digests(client: TestClient, tmp_path: Path) -> None:
    _snapshot(tmp_path, DIGEST_A, {"b.txt": b"two", "nested/a.txt": b"one"})
    _configure(client, tmp_path)

    body = client.get(f"/workspace-snapshots/{DIGEST_A}/files").json()

    assert body["digest"] == DIGEST_A
    assert [item["path"] for item in body["files"]] == ["b.txt", "nested/a.txt"]
    assert body["file_count"] == 2
    assert body["total_bytes"] == 6
    assert body["truncated"] is False
    assert body["files"][1]["sha256"] == hashlib.sha256(b"one").hexdigest()


def test_snapshot_files_unknown_digest_is_404_not_empty_tree(
    client: TestClient, tmp_path: Path
) -> None:
    _snapshot(tmp_path, DIGEST_A, {"a.txt": b"a"})
    _configure(client, tmp_path)

    response = client.get(f"/workspace-snapshots/{DIGEST_MISSING}/files")

    assert response.status_code == 404
    assert "unknown snapshot digest" in response.json()["detail"]


def test_snapshot_files_malformed_digest_is_404(client: TestClient, tmp_path: Path) -> None:
    _configure(client, tmp_path)

    response = client.get("/workspace-snapshots/not-a-digest/files")

    assert response.status_code == 404


def test_snapshot_diff_reports_file_level_changes(client: TestClient, tmp_path: Path) -> None:
    _snapshot(tmp_path, DIGEST_A, {"keep.txt": b"same", "edit.txt": b"aaaa", "gone.txt": b"bye"})
    _snapshot(tmp_path, DIGEST_B, {"keep.txt": b"same", "edit.txt": b"bbbb", "new.txt": b"hi"})
    _configure(client, tmp_path)

    body = client.get(f"/workspace-snapshots/{DIGEST_A}/diff/{DIGEST_B}").json()

    assert body["comparison"] == "WORKSPACE_SNAPSHOT_METADATA"
    assert body["identical"] is False
    assert (body["added"], body["removed"], body["changed"], body["unchanged"]) == (1, 1, 1, 1)
    kinds = {item["path"]: item["kind"] for item in body["changes"]}
    assert kinds == {"new.txt": "ADDED", "gone.txt": "REMOVED", "edit.txt": "CHANGED"}
    assert "content line diff" in body["note"]


def test_snapshot_diff_of_same_digest_is_identical(client: TestClient, tmp_path: Path) -> None:
    _snapshot(tmp_path, DIGEST_A, {"a.txt": b"a"})
    _configure(client, tmp_path)

    body = client.get(f"/workspace-snapshots/{DIGEST_A}/diff/{DIGEST_A}").json()

    assert body["identical"] is True
    assert body["changes"] == []


def test_run_snapshots_reports_recorded_digests_and_retention(
    client: TestClient, tmp_path: Path
) -> None:
    run_id = _seed_run(client)
    _record_snapshots(client, run_id, before=DIGEST_A, after=DIGEST_B)
    _snapshot(tmp_path, DIGEST_A, {"a.txt": b"a"})
    _configure(client, tmp_path)

    body = client.get(f"/runs/{run_id}/workspace-snapshots").json()

    assert body["run_id"] == run_id
    rows = {item["digest"]: item for item in body["snapshots"]}
    assert set(rows) == {DIGEST_A, DIGEST_B}
    assert rows[DIGEST_A]["recorded_as"] == ["EVIDENCE_BEFORE"]
    assert rows[DIGEST_A]["retained"] is True
    assert rows[DIGEST_B]["recorded_as"] == ["EVIDENCE_AFTER"]
    assert rows[DIGEST_B]["retained"] is False
    assert "does not persist a run-to-workspace binding" in body["note"]


def test_run_snapshots_reports_same_digest_once_with_both_sources(client: TestClient) -> None:
    run_id = _seed_run(client)
    _record_snapshots(client, run_id, before=DIGEST_A, after=DIGEST_A)

    body = client.get(f"/runs/{run_id}/workspace-snapshots").json()

    assert len(body["snapshots"]) == 1
    assert body["snapshots"][0]["recorded_as"] == ["EVIDENCE_AFTER", "EVIDENCE_BEFORE"]


def test_run_snapshots_unknown_run_is_404(client: TestClient) -> None:
    response = client.get(f"/runs/{ID.generate().value}/workspace-snapshots")

    assert response.status_code == 404
