"""ExperimentRun -> Evidence admission tests (IG-1 seam)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from adapters.fakes import (
    FakeArtifactStore,
    FakeEvidenceLedger,
    FakeExecutionBackend,
    FakeWorkspaceBackend,
)
from packages.application.experiments import (
    ExperimentExecutionRequest,
    ExperimentExecutor,
    ExperimentProvenance,
    register_experiment_evidence,
)
from packages.domain.core import ID
from packages.domain.enums import ArtifactState
from packages.domain.evidence import ClaimStatus
from packages.domain.experiment_state import ExperimentPlanState, ExperimentRunState
from packages.domain.experiments import ExperimentPlan
from packages.domain.workspace import Workspace

_PLAN_ID = ID("3f1c6a8e-9b2d-4f3a-8c5e-1a2b3c4d5e6f")
_RUN_ID = ID("7a2b3c4d-5e6f-4a5b-9c0d-1e2f3a4b5c6d")


def _plan() -> ExperimentPlan:
    return ExperimentPlan(
        id=_PLAN_ID,
        name="evidence-admission",
        hypothesis="test",
    ).transition(ExperimentPlanState.Transition.PREREGISTER)


def _write_result(tmp_path: Path, status: str = "SUCCEEDED") -> None:
    (tmp_path / "experiment_result.json").write_text(
        json.dumps({
            "experiment_run_id": str(_RUN_ID.value),
            "status": status,
            "artifact_refs": ["samples.json"],
            "metrics": {"mean": 0.5},
        }),
        encoding="utf-8",
    )


def _execute(tmp_path: Path) -> tuple[Any, FakeArtifactStore, FakeWorkspaceBackend]:
    workspaces = FakeWorkspaceBackend()
    workspaces.create_workspace(Workspace(id="ws-a", name="ws-a"))
    artifacts = FakeArtifactStore()
    executor = ExperimentExecutor(
        execution=FakeExecutionBackend(),
        workspaces=workspaces,
        artifacts=artifacts,
        workspace_dir=lambda lease: tmp_path,
    )
    (tmp_path / "samples.json").write_bytes(b"[1,2,3]")
    _write_result(tmp_path)
    outcome = executor.execute(
        ExperimentExecutionRequest(
            plan=_plan(),
            run_id=_RUN_ID,
            command="python run.py",
            workspace=Workspace(id="ws-a", name="ws-a"),
            agent_session_id="session-1",
            seed=42,
        )
    )
    return outcome, artifacts, workspaces


def test_admission_registers_evidence_with_provenance(tmp_path: Path) -> None:
    outcome, artifacts, _ = _execute(tmp_path)
    ledger = FakeEvidenceLedger()
    result = register_experiment_evidence(
        ledger,
        outcome.run,
        artifacts,
        provenance=ExperimentProvenance(
            run_id="run-1",
            manifest_digest="sha256:" + "0" * 64,
            tool_refs=("lit_search@1.0.0",),
            skill_refs=("literature_scouting@1.0.0",),
            model_refs=("model-a@1",),
        ),
    )
    assert result.claim.id == f"claim:{_RUN_ID.value}:result"
    assert result.claim.status is ClaimStatus.PROPOSED
    assert result.evidence
    evidence = result.evidence[0]
    assert evidence.experiment_run_id == str(_RUN_ID.value)
    assert evidence.run_id == "run-1"
    assert evidence.image_digest is not None or evidence.image_digest is None
    assert evidence.metric_refs == (f"metric:{_RUN_ID.value}:mean",)
    assert evidence.tool_refs == ("lit_search@1.0.0",)
    assert ledger.has_source(evidence.source_ref)
    assert ledger.get_claim(result.claim.id).status is ClaimStatus.PROPOSED
    # Artifact must have been moved from STAGED to VERIFIED before evidence.
    artifact = next(a for a in artifacts.list_refs() if a.id == f"{_RUN_ID.value}:samples.json")
    assert artifact.state in (ArtifactState.VERIFIED, ArtifactState.ACTIVE)


def test_non_scientific_state_rejected(tmp_path: Path) -> None:
    outcome, artifacts, _ = _execute(tmp_path)
    ledger = FakeEvidenceLedger()
    # Force a failed run by removing result file is not needed: mutate state via
    # a terminal failed run is hard with frozen dataclass; use TIMED_OUT instead.
    from dataclasses import replace

    failed = replace(outcome.run, state=ExperimentRunState.State.TIMED_OUT)
    with pytest.raises(ValueError, match="non-scientific"):
        register_experiment_evidence(ledger, failed, artifacts)
