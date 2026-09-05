"""Independent read-only checks against canonical SQL and restored blob bytes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import psycopg


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def check_run(conn: psycopg.Connection[Any], root: Path, run_id: str) -> dict[str, Any]:
    artifacts = dict(conn.execute("SELECT artifact_id, digest FROM artifacts").fetchall())
    verified: dict[str, bytes] = {}
    for key, expected in artifacts.items():
        hex_digest = expected.removeprefix("sha256:")
        content = (root / hex_digest[:2] / hex_digest).read_bytes()
        assert digest(content) == expected, f"artifact digest mismatch: {key}"
        verified[key] = content
    row = conn.execute("SELECT run_json FROM runs WHERE run_id=%s", (run_id,)).fetchone()
    assert row is not None and row[0]["state"] == "SUCCEEDED"
    manifest_id = f"{run_id}:run_manifest.json"
    assert artifacts[manifest_id] == row[0]["manifest_digest"]
    manifest = json.loads(verified[manifest_id])
    delivery_id = f"{run_id}:deliverable.json"
    delivery = json.loads(verified[delivery_id])
    assert delivery["run_id"] == run_id
    assert delivery["protocol"]["manifest_digest"] == artifacts[manifest_id]
    evidence = check_evidence(conn, artifacts, run_id, delivery)
    budget = check_budget(conn, run_id, delivery)
    tasks = conn.execute(
        "SELECT task_id, status, fence_seq FROM tasks WHERE run_id=%s", (run_id,)
    ).fetchall()
    assert len(tasks) == 1 and tasks[0][1] == "SUCCEEDED", "missing owning execution task"
    observed_duration = conn.execute(
        "SELECT execution_elapsed_seconds FROM execution_jobs WHERE task_id=%s", (tasks[0][0],)
    ).fetchone()[0]
    assert observed_duration is not None, "new workers must persist original execution duration"
    assert delivery["budget"]["experiment_seconds"] == int(observed_duration)
    reports = conn.execute(
        "SELECT report_digest, verdict, pass_count, fail_count FROM eval_reports WHERE run_id=%s",
        (run_id,),
    ).fetchall()
    assert len(reports) == 1 and reports[0][1:] == ("PASS", 7, 0)
    refs = conn.execute(
        "SELECT source_refs_json FROM artifacts WHERE artifact_id=%s", (delivery_id,)
    ).fetchone()[0]
    if isinstance(refs, str):
        refs = json.loads(refs)
    assert reports[0][0] in refs
    assert delivery["memory"]["kind"] == "FACT"
    assert "FP32" in delivery["objective"] and "TF-IDF" not in delivery["objective"]
    return {"run_id": run_id, "state": row[0]["state"], "artifacts_checked": len(verified),
            "manifest_digest": artifacts[manifest_id], "deliverable_digest": artifacts[delivery_id],
            "image_digest": manifest["image_digest"], "evidence_count": len(evidence),
            "claim": delivery["evidence_chain"]["claim_id"], "tasks": tasks,
            "evaluation": reports, "budget": budget, "memory_kind": delivery["memory"]["kind"]}


def check_evidence(
    conn: psycopg.Connection[Any], artifacts: dict[str, str], run_id: str, delivery: dict[str, Any]
) -> list[tuple[Any, ...]]:
    rows = conn.execute(
        "SELECT e.id,e.artifact_id,e.content_digest,e.manifest_digest,s.content_digest "
        "FROM m12_evidence e JOIN m12_sources s ON s.origin=e.source_ref WHERE e.run_id=%s",
        (run_id,),
    ).fetchall()
    assert len(rows) == 3
    for _, artifact_id, content, manifest, source in rows:
        assert artifacts[artifact_id] == content == source
        assert manifest == artifacts[f"{run_id}:run_manifest.json"]
    claim_id = delivery["evidence_chain"]["claim_id"]
    claim = conn.execute("SELECT status FROM m12_claims WHERE id=%s", (claim_id,)).fetchone()
    assert claim is not None and claim[0] == "VERIFIED"
    relations = conn.execute(
        "SELECT e.id,e.run_id FROM m12_relations r JOIN m12_evidence e ON e.id=r.evidence_id "
        "WHERE r.claim_id=%s", (claim_id,),
    ).fetchall()
    assert len(relations) == 3 and all(item[1] == run_id for item in relations)
    assert {item[0] for item in relations} == set(delivery["evidence_chain"]["evidence_ids"])
    return rows


def check_budget(
    conn: psycopg.Connection[Any], run_id: str, delivery: dict[str, Any]
) -> dict[str, Any]:
    entries = [r[0] for r in conn.execute(
        "SELECT entry_json FROM budget_usage_entries WHERE entry_json->>'run_id'=%s", (run_id,)
    ).fetchall()]
    budget = delivery["budget"]
    assert len(entries) == budget["entries"] == 3
    assert budget["experiment_runs"] == 1 and budget["experiment_duration_known"] is True
    assert {r["entry_id"] for r in entries} == {r["entry_id"] for r in budget["ledger_entries"]}
    return {"entries": len(entries), "types": sorted(r["resource_type"] for r in entries),
            "duration_known": budget["experiment_duration_known"]}


def table_counts(conn: psycopg.Connection[Any]) -> dict[str, int]:
    names = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY 1"
    ).fetchall()
    return {name: conn.execute(psycopg.sql.SQL("SELECT count(*) FROM {}").format(
        psycopg.sql.Identifier(name))).fetchone()[0] for (name,) in names}
