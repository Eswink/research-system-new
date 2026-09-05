"""Revalidate already-admitted evidence on replay without downgrading truth."""

from __future__ import annotations

from packages.application.evidence.m12_chain import verify_claim
from packages.application.m12_reference.deps import CleanRunDeps
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Digest
from packages.domain.evidence import ClaimStatus, EvidenceRelation, EvidenceRelationType
from packages.domain.experiments import ExperimentRun
from packages.domain.manifest import RunManifest
from packages.domain.redaction import redact_text


def replay_claim(
    deps: CleanRunDeps, run_id: str, manifest: RunManifest, run: ExperimentRun
) -> tuple[str, tuple[str, ...], str] | None:
    if deps.persistence is None:
        return None
    claim_id = f"claim:{run.id.value}:result"
    try:
        claim = deps.ledger.get_claim(claim_id)
    except (InvalidInputError, KeyError):
        return None
    if claim.statement != deps.claim_statement or claim.status not in (
        ClaimStatus.PROPOSED,
        ClaimStatus.VERIFIED,
    ):
        raise RuntimeError("stored Claim conflicts with the frozen reference request")
    assert run.result is not None
    evidence_ids = tuple(f"evidence:{artifact}" for artifact in run.result.artifact_refs)
    expected = {(key, EvidenceRelationType.SUPPORTS) for key in evidence_ids}
    if set(claim.evidence_relations) != expected:
        raise RuntimeError("stored Claim evidence references disagree with ExperimentRun")
    _verify_evidence(deps, run_id, manifest, evidence_ids)
    present = {(r.evidence_id, r.relation) for r in deps.ledger.relations_for_claim(claim_id)}
    if not present <= expected:
        raise RuntimeError("stored Claim contains unexpected evidence relations")
    for key, relation in expected - present:
        deps.ledger.attach_relation(EvidenceRelation(claim_id, key, relation))
    if claim.status is ClaimStatus.PROPOSED:
        claim = verify_claim(
            deps.ledger, claim, reviewer="gate:independent-acceptance", verdict="PASS"
        )
    return claim.id, evidence_ids, claim.status.value


def _verify_evidence(
    deps: CleanRunDeps, run_id: str, manifest: RunManifest, evidence_ids: tuple[str, ...]
) -> None:
    for key in evidence_ids:
        evidence = deps.ledger.get_evidence(key)
        if evidence.run_id != run_id or evidence.manifest_digest != str(manifest.digest()):
            raise RuntimeError("restored Evidence provenance mismatch")
        if not evidence.artifact_id or not deps.ledger.has_source(evidence.source_ref):
            raise RuntimeError("restored Evidence is missing Artifact/Source provenance")
        meta = deps.artifacts.meta(evidence.artifact_id)
        content = deps.artifacts.get(evidence.artifact_id)
        if (
            meta is None
            or str(meta.digest) != evidence.content_digest
            or Digest.of_bytes(content) != meta.digest
        ):
            raise RuntimeError("restored Evidence content digest mismatch")


def replay_memory(deps: CleanRunDeps, memory_id: str, provenance: str) -> bool:
    if deps.persistence is None:
        return False
    try:
        record = deps.memory.get(memory_id)
    except (InvalidInputError, KeyError):
        return False
    if (
        record.kind != deps.memory_kind
        or record.content != redact_text(deps.memory_content)
        or record.provenance != provenance
        or not record.active
    ):
        raise RuntimeError("stored Memory conflicts with the frozen reference request")
    return True
