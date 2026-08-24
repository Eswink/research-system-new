"""SqliteEvidenceLedger 行映射（与 evidence_ledger.py 拆分，保持模块规模阈值）。

SQLite row ↔ Domain 对象（SourceRecord / Evidence / Claim）的纯函数转换；
业务字段一致判定（观测元数据不参与冲突比较）。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from packages.domain.core import Timestamp
from packages.domain.enums import TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelationType,
    SourceRecord,
)

SOURCE_COLS = (
    "origin, content_digest, trust_label, access_time, license_terms, authors, parser_version"
)
EVIDENCE_COLS = (
    "id, source_ref, content_digest, extracted_by, captured_at, artifact_id, run_id, "
    "experiment_run_id, metric_refs, workspace_snapshot_before, workspace_snapshot_after, "
    "image_digest, environment_digest, tool_refs, skill_refs, model_refs, manifest_digest"
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS m12_sources (
    origin TEXT PRIMARY KEY,
    content_digest TEXT NOT NULL,
    trust_label TEXT NOT NULL,
    access_time TEXT,
    license_terms TEXT,
    authors TEXT NOT NULL,
    parser_version TEXT
);
CREATE TABLE IF NOT EXISTS m12_evidence (
    id TEXT PRIMARY KEY,
    source_ref TEXT NOT NULL,
    content_digest TEXT NOT NULL,
    extracted_by TEXT,
    captured_at TEXT,
    artifact_id TEXT,
    run_id TEXT,
    experiment_run_id TEXT,
    metric_refs TEXT NOT NULL,
    workspace_snapshot_before TEXT,
    workspace_snapshot_after TEXT,
    image_digest TEXT,
    environment_digest TEXT,
    tool_refs TEXT NOT NULL,
    skill_refs TEXT NOT NULL,
    model_refs TEXT NOT NULL,
    manifest_digest TEXT
);
CREATE TABLE IF NOT EXISTS m12_claims (
    id TEXT PRIMARY KEY,
    statement TEXT NOT NULL,
    status TEXT NOT NULL,
    author TEXT,
    evidence_relations TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS m12_relations (
    claim_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    strength REAL NOT NULL,
    PRIMARY KEY (claim_id, evidence_id, relation)
);
"""


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def source_from_row(row: sqlite3.Row) -> SourceRecord:
    return SourceRecord(
        origin=row["origin"],
        content_digest=row["content_digest"],
        trust_label=TrustLabel(row["trust_label"]),
        access_time=(
            Timestamp(datetime_from_iso(row["access_time"])) if row["access_time"] else None
        ),
        license_terms=row["license_terms"],
        authors=json.loads(row["authors"]),
        parser_version=row["parser_version"],
    )


def evidence_from_row(row: sqlite3.Row) -> Evidence:
    return Evidence(
        id=row["id"],
        source_ref=row["source_ref"],
        content_digest=row["content_digest"],
        extracted_by=row["extracted_by"],
        captured_at=(
            Timestamp(datetime_from_iso(row["captured_at"])) if row["captured_at"] else None
        ),
        artifact_id=row["artifact_id"],
        run_id=row["run_id"],
        experiment_run_id=row["experiment_run_id"],
        metric_refs=tuple(json.loads(row["metric_refs"])),
        workspace_snapshot_before=row["workspace_snapshot_before"],
        workspace_snapshot_after=row["workspace_snapshot_after"],
        image_digest=row["image_digest"],
        environment_digest=row["environment_digest"],
        tool_refs=tuple(json.loads(row["tool_refs"])),
        skill_refs=tuple(json.loads(row["skill_refs"])),
        model_refs=tuple(json.loads(row["model_refs"])),
        manifest_digest=row["manifest_digest"],
    )


def claim_values(claim: Claim) -> tuple[Any, ...]:
    relations = [
        (evidence_id, relation.value) for evidence_id, relation in claim.evidence_relations
    ]
    return (claim.id, claim.statement, claim.status.value, claim.author, to_json(relations))


def claim_from_row(row: sqlite3.Row) -> Claim:
    raw = json.loads(row["evidence_relations"])
    relations = [(evidence_id, EvidenceRelationType(relation)) for evidence_id, relation in raw]
    return Claim(
        id=row["id"],
        statement=row["statement"],
        status=ClaimStatus(row["status"]),
        author=row["author"],
        evidence_relations=relations,
    )


def same_source(row: sqlite3.Row, source: SourceRecord) -> bool:
    """业务字段一致判定；access_time 是观测元数据，不参与冲突比较。"""
    authors: list[str] = json.loads(row["authors"])
    return bool(
        row["content_digest"] == source.content_digest
        and row["trust_label"] == source.trust_label.value
        and row["license_terms"] == source.license_terms
        and authors == source.authors
        and row["parser_version"] == source.parser_version
    )


def same_evidence(row: sqlite3.Row, evidence: Evidence) -> bool:
    """业务字段一致判定；captured_at 是观测元数据，不参与冲突比较。"""
    metric_refs: list[str] = json.loads(row["metric_refs"])
    tool_refs: list[str] = json.loads(row["tool_refs"])
    skill_refs: list[str] = json.loads(row["skill_refs"])
    model_refs: list[str] = json.loads(row["model_refs"])
    return bool(
        row["source_ref"] == evidence.source_ref
        and row["content_digest"] == evidence.content_digest
        and row["extracted_by"] == evidence.extracted_by
        and row["artifact_id"] == evidence.artifact_id
        and row["run_id"] == evidence.run_id
        and row["experiment_run_id"] == evidence.experiment_run_id
        and metric_refs == list(evidence.metric_refs)
        and row["workspace_snapshot_before"] == evidence.workspace_snapshot_before
        and row["workspace_snapshot_after"] == evidence.workspace_snapshot_after
        and row["image_digest"] == evidence.image_digest
        and row["environment_digest"] == evidence.environment_digest
        and tool_refs == list(evidence.tool_refs)
        and skill_refs == list(evidence.skill_refs)
        and model_refs == list(evidence.model_refs)
        and row["manifest_digest"] == evidence.manifest_digest
    )


def datetime_from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


__all__ = [
    "EVIDENCE_COLS",
    "SCHEMA",
    "SOURCE_COLS",
    "claim_from_row",
    "claim_values",
    "evidence_from_row",
    "same_evidence",
    "same_source",
    "source_from_row",
    "to_json",
]
