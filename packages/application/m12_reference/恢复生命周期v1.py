"""Canonical admission and replay for the durable Reference Research Run."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any

from packages.application.m12_reference.deps import CleanRunDeps
from packages.application.m12_reference.persistence import _put_json_artifact, _put_manifest
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import ID, Digest, Timestamp, Version
from packages.domain.experiment_state import ExperimentRunState
from packages.domain.experiments import ExperimentRun
from packages.domain.manifest import RunManifest
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from packages.domain.serialization import canonical_json_bytes


def _inputs(deps: CleanRunDeps, plan_id: ID, command: str) -> bytes:
    script = Path(deps.experiment_script) if deps.experiment_script else None
    return canonical_json_bytes({
        "plan_id": plan_id.value,
        "command": command,
        "resource_profile": deps.resource_profile,
        "script_digest": str(Digest.of_bytes(script.read_bytes())) if script else None,
        "objective": deps.objective,
        "hypothesis": deps.hypothesis,
        "plan_name": deps.plan_name,
        "claim_statement": deps.claim_statement,
        "memory_kind": deps.memory_kind.value,
        "memory_content": deps.memory_content,
    })


def _existing_run(deps: CleanRunDeps, run_id: str) -> ResearchRun | None:
    assert deps.persistence is not None
    try:
        return deps.persistence.run_store.get_run(run_id)
    except KeyError:
        return None


def _restore_manifest(deps: CleanRunDeps, candidate: RunManifest) -> RunManifest:
    artifact_id = f"{candidate.run_id}:run_manifest.json"
    meta = deps.artifacts.meta(artifact_id)
    if meta is None:
        return candidate
    content = deps.artifacts.get(artifact_id)
    if meta.digest != Digest.of_bytes(content):
        raise RuntimeError("frozen manifest content digest mismatch")
    payload: dict[str, Any] = json.loads(content)
    payload["protocol_version"] = Version(**payload["protocol_version"])
    for key in ("protocol_digest", "compiled_plan_digest"):
        payload[key] = Digest(**payload[key]) if payload.get(key) else None
    if payload.get("frozen_at"):
        payload["frozen_at"] = Timestamp(datetime.fromisoformat(payload["frozen_at"]["value"]))
    restored = RunManifest(**payload)
    if (
        restored.digest() != meta.digest
        or restored.semantic_digest() != candidate.semantic_digest()
    ):
        raise RuntimeError("resume manifest/configuration drift; fork a new Run")
    return restored


def admit_or_resume(
    deps: CleanRunDeps, manifest: RunManifest, plan_id: ID, command: str
) -> RunManifest:
    if deps.persistence is None:
        return manifest
    if not manifest.image_digest:
        raise RuntimeError("durable Reference Run requires a frozen expected image digest")
    existing = _existing_run(deps, manifest.run_id)
    if existing is not None and existing.state != ResearchRunState.State.RUNNING:
        raise RuntimeError(f"Run is not resumable: {existing.state}; inspect its stored artifacts")
    content = _inputs(deps, plan_id, command)
    inputs_digest = Digest.of_bytes(content)
    candidate = replace(manifest, input_artifact_digests=[str(inputs_digest)])
    frozen = _restore_manifest(deps, candidate)
    if existing is not None and existing.manifest_digest != frozen.digest():
        raise RuntimeError("canonical Run and frozen manifest disagree")
    artifact_id = f"{manifest.run_id}:reference_inputs.json"
    meta = deps.artifacts.meta(artifact_id)
    if meta is not None:
        if meta.digest != inputs_digest or not deps.artifacts.verify(artifact_id):
            raise RuntimeError("reference input artifact drift")
    else:
        _put_json_artifact(
            deps,
            artifact_id=artifact_id,
            content=content,
            classification="reference_inputs",
            source_refs=[],
        )
    _put_manifest(deps, manifest.run_id, frozen)
    if existing is None:
        deps.persistence.run_store.save_run(_started_run(deps, frozen))
    return frozen


def _started_run(deps: CleanRunDeps, manifest: RunManifest) -> ResearchRun:
    run = ResearchRun(
        id=ID(manifest.run_id), project_id=deps.project.project_id, protocol_id=deps.protocol.id
    )
    for event in (
        ResearchRunState.Transition.START_COMPILE,
        ResearchRunState.Transition.COMPILE_OK,
        ResearchRunState.Transition.PREFLIGHT_OK,
    ):
        run = run.transition(event)
    run = run.with_manifest(
        manifest.digest(),
        manifest.semantic_digest(),
        pricing_version=manifest.pricing_version,
        pricing_digest=manifest.pricing_digest,
    )
    return run.transition(ResearchRunState.Transition.START)


def fail_admitted_run(deps: CleanRunDeps, run_id: str) -> None:
    if deps.persistence is None:
        return
    run = deps.persistence.run_store.get_run(run_id)
    if not run.is_terminal:
        deps.persistence.run_store.save_run(run.transition(ResearchRunState.Transition.FAIL))


def restored_experiment(deps: CleanRunDeps, experiment_id: str) -> ExperimentRun | None:
    if deps.persistence is None:
        return None
    try:
        run = deps.persistence.experiment_store.get_run(experiment_id)
    except (InvalidInputError, KeyError):
        return None
    if run.state not in (
        ExperimentRunState.State.SUCCEEDED,
        ExperimentRunState.State.NEGATIVE_RESULT,
    ):
        raise RuntimeError(f"stored experiment is not successfully completed: {run.state}")
    artifacts = [a for a in deps.artifacts.list_refs() if a.id.startswith(experiment_id + ":")]
    if not artifacts or not all(deps.artifacts.verify(a.id) for a in artifacts):
        raise RuntimeError("stored experiment artifact integrity failure")
    return run
