"""PG EvidenceLedger row mapping (mirrors sqlite/evidence_rows.py).

SQLite row is sqlite3.Row (string JSON); PG row is dict_row (JSONB → Python object,
TIMESTAMPTZ → datetime). Helpers handle both.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, cast

from packages.domain.core import Timestamp
from packages.domain.enums import TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelationType,
    SourceRecord,
)


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        return cast(list[Any], json.loads(value))
    if isinstance(value, list):
        return value
    return list(value)


def _as_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return None


def source_from_row(row: Any) -> SourceRecord:
    at = _as_datetime(row["access_time"])
    authors = _as_list(row["authors"])
    return SourceRecord(
        origin=row["origin"],
        content_digest=row["content_digest"],
        trust_label=TrustLabel(row["trust_label"]),
        access_time=Timestamp(at) if at is not None else None,
        license_terms=row["license_terms"],
        authors=authors,
        parser_version=row["parser_version"],
    )


def evidence_from_row(row: Any) -> Evidence:
    cap = _as_datetime(row["captured_at"])
    return Evidence(
        id=row["id"],
        source_ref=row["source_ref"],
        content_digest=row["content_digest"],
        extracted_by=row["extracted_by"],
        captured_at=Timestamp(cap) if cap is not None else None,
        artifact_id=row["artifact_id"],
        run_id=row["run_id"],
        experiment_run_id=row["experiment_run_id"],
        metric_refs=tuple(_as_list(row["metric_refs"])),
        workspace_snapshot_before=row["workspace_snapshot_before"],
        workspace_snapshot_after=row["workspace_snapshot_after"],
        image_digest=row["image_digest"],
        environment_digest=row["environment_digest"],
        tool_refs=tuple(_as_list(row["tool_refs"])),
        skill_refs=tuple(_as_list(row["skill_refs"])),
        model_refs=tuple(_as_list(row["model_refs"])),
        manifest_digest=row["manifest_digest"],
    )


def claim_values(claim: Claim) -> tuple[Any, ...]:
    relations = [
        (evidence_id, relation.value) for evidence_id, relation in claim.evidence_relations
    ]
    return (claim.id, claim.statement, claim.status.value, claim.author, to_json(relations))


def claim_from_row(row: Any) -> Claim:
    raw = row["evidence_relations"]
    if isinstance(raw, str):
        raw_list = json.loads(raw)
    else:
        raw_list = raw
    relations = [
        (evidence_id, EvidenceRelationType(relation)) for evidence_id, relation in raw_list
    ]
    return Claim(
        id=row["id"],
        statement=row["statement"],
        status=ClaimStatus(row["status"]),
        author=row["author"],
        evidence_relations=relations,
    )


def same_source(row: Any, source: SourceRecord) -> bool:
    authors = _as_list(row["authors"])
    return bool(
        row["content_digest"] == source.content_digest
        and row["trust_label"] == source.trust_label.value
        and row["license_terms"] == source.license_terms
        and authors == source.authors
        and row["parser_version"] == source.parser_version
    )


def same_evidence(row: Any, evidence: Evidence) -> bool:
    return bool(
        row["source_ref"] == evidence.source_ref
        and row["content_digest"] == evidence.content_digest
        and row["extracted_by"] == evidence.extracted_by
        and row["artifact_id"] == evidence.artifact_id
        and row["run_id"] == evidence.run_id
        and row["experiment_run_id"] == evidence.experiment_run_id
        and _as_list(row["metric_refs"]) == list(evidence.metric_refs)
        and row["workspace_snapshot_before"] == evidence.workspace_snapshot_before
        and row["workspace_snapshot_after"] == evidence.workspace_snapshot_after
        and row["image_digest"] == evidence.image_digest
        and row["environment_digest"] == evidence.environment_digest
        and _as_list(row["tool_refs"]) == list(evidence.tool_refs)
        and _as_list(row["skill_refs"]) == list(evidence.skill_refs)
        and _as_list(row["model_refs"]) == list(evidence.model_refs)
        and row["manifest_digest"] == evidence.manifest_digest
    )
