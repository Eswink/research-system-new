"""Durable persistence for the Reference Research Workflow.

The workflow can still run with ephemeral test adapters. When a
``CleanRunPersistence`` bundle is supplied, this module materializes the
restorable personal-production truth closure through inward-owned ports.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from packages.application.evaluation.eval_index import stored_from_report
from packages.application.m12_reference.deps import CleanRunDeps
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from packages.domain.enums import ArtifactState
from packages.domain.eval_result import EvalReport
from packages.domain.experiments import ExperimentPlan, ExperimentRun
from packages.domain.manifest import RunManifest
from packages.domain.reproducibility import ReproducibilityAudit
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from packages.domain.serialization import canonical_json_bytes

_MANIFEST_NAME = "run_manifest.json"
_DELIVERABLE_NAME = "deliverable.json"


@dataclass(frozen=True, slots=True)
class CompletionTruth:
    """Objects that become authoritative only after the full gate passes."""

    run_id: str
    manifest: RunManifest
    audit: ReproducibilityAudit
    eval_report: EvalReport
    deliverable: dict[str, object]
    claim_id: str


def persist_experiment_plan(deps: CleanRunDeps, plan: ExperimentPlan) -> None:
    persistence = deps.persistence
    if persistence is not None:
        persistence.experiment_store.save_plan(plan)


def persist_experiment_run(deps: CleanRunDeps, run: ExperimentRun) -> None:
    persistence = deps.persistence
    if persistence is not None:
        persistence.experiment_store.save_run(run)


def persist_completion(deps: CleanRunDeps, truth: CompletionTruth) -> None:
    """Persist the closed run, manifest, audit, evaluation, and deliverable."""
    persistence = deps.persistence
    if persistence is None:
        return
    succeeded = _succeeded_run(deps, truth)
    persistence.experiment_store.save_audit(truth.audit)
    persistence.eval_report_store.put(stored_from_report(truth.eval_report, run_id=truth.run_id))
    _put_manifest(deps, truth.run_id, truth.manifest)
    _put_deliverable(deps, truth)
    persistence.run_store.save_run(succeeded)


def _put_manifest(deps: CleanRunDeps, run_id: str, manifest: RunManifest) -> None:
    content = canonical_json_bytes(manifest)
    existing = deps.artifacts.meta(f"{run_id}:{_MANIFEST_NAME}")
    if existing is not None:
        if existing.digest != Digest.of_bytes(content) or not deps.artifacts.verify(existing.id):
            raise RuntimeError("frozen manifest cannot be overwritten")
        return
    _put_json_artifact(
        deps,
        artifact_id=f"{run_id}:{_MANIFEST_NAME}",
        content=content,
        classification="run_manifest",
        source_refs=_manifest_source_refs(manifest),
    )


def _manifest_source_refs(manifest: RunManifest) -> list[str]:
    refs = [str(manifest.digest()), str(manifest.semantic_digest())]
    if manifest.protocol_digest is not None:
        refs.append(str(manifest.protocol_digest))
    if manifest.compiled_plan_digest is not None:
        refs.append(str(manifest.compiled_plan_digest))
    return refs


def _put_deliverable(deps: CleanRunDeps, truth: CompletionTruth) -> None:
    content = json.dumps(
        truth.deliverable,
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    refs = [
        str(truth.manifest.digest()),
        truth.claim_id,
        str(truth.eval_report.digest()),
    ]
    if truth.audit.audit_digest is not None:
        refs.append(str(truth.audit.audit_digest))
    _put_json_artifact(
        deps,
        artifact_id=f"{truth.run_id}:{_DELIVERABLE_NAME}",
        content=content,
        classification="research_deliverable",
        source_refs=refs,
    )


def _put_json_artifact(
    deps: CleanRunDeps,
    *,
    artifact_id: str,
    content: bytes,
    classification: str,
    source_refs: list[str],
) -> None:
    deps.artifacts.put(
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            created_by="reference_workflow",
            source_refs=source_refs,
            classification=classification,
            state=ArtifactState.ACTIVE,
        ),
        content,
    )


def _succeeded_run(deps: CleanRunDeps, truth: CompletionTruth) -> ResearchRun:
    if deps.persistence is None:
        raise RuntimeError("canonical completion requires persistence")
    run = deps.persistence.run_store.get_run(truth.run_id)
    if run.manifest_digest != truth.manifest.digest():
        raise RuntimeError("completion disagrees with the admitted frozen manifest")
    return run.transition(ResearchRunState.Transition.SUCCEED)


__all__ = [
    "CompletionTruth",
    "persist_completion",
    "persist_experiment_plan",
    "persist_experiment_run",
]
