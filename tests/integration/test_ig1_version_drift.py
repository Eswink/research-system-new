"""IG-1 version/digest drift detection through M11 scorer."""

from __future__ import annotations

from adapters.fakes import FakeArtifactStore
from packages.application.evaluation.scorer_types import ScorerContext, ScorerInput
from packages.application.evaluation.scorers_runtime import experiment_reproducibility_scorer
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest, Version
from packages.domain.enums import ArtifactState
from packages.domain.eval_result import EvalFindingStatus
from packages.domain.eval_spec import EvalCase, EvalScope
from packages.domain.experiment_state import ExperimentRunState
from packages.domain.experiments import (
    ExperimentRun,
    ExperimentRunResult,
    ExperimentRunSpec,
)
from packages.domain.serialization import digest_of

_RUN_ID = ID("11111111-2222-4333-8444-555555555555")


def _run(artifact_id: str) -> ExperimentRun:
    return ExperimentRun(
        id=_RUN_ID,
        plan_id=ID("22222222-2222-4333-8444-555555555555"),
        spec=ExperimentRunSpec(
            input_digest=digest_of({"x": 1}),
            command="python run.py",
            environment_digest=digest_of({}),
            seed=1,
        ),
        result=ExperimentRunResult(
            execution_run_id="exec-1",
            image_digest="sha256:" + "0" * 64,
            workspace_snapshot_before="snap-before",
            workspace_snapshot_after="snap-after",
            artifact_refs=(artifact_id,),
        ),
        state=ExperimentRunState.State.SUCCEEDED,
    )


def _case(experiment_run_id: str) -> EvalCase:
    return EvalCase(
        id="drift",
        version=Version("1.0.0"),
        scope=EvalScope.INTEGRATION,
        input_ref="input://drift",
        expected={"experiment_run_id": experiment_run_id},
        scorer_refs=(),
    )


def test_corrupted_artifact_digest_is_detected() -> None:
    store = FakeArtifactStore()
    artifact_id = f"{_RUN_ID.value}:result.json"
    content = b"original"
    store.put(
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            state=ArtifactState.STAGED,
        ),
        content,
    )
    store.mark(artifact_id, ArtifactState.VERIFIED)
    # Simulate artifact content drift after admission.
    store._content[artifact_id] = b"tampered"  # noqa: SLF001
    scorer = experiment_reproducibility_scorer(store)
    ctx = ScorerContext(
        case=_case(str(_RUN_ID.value)),
        input=ScorerInput(actual=_run(artifact_id)),
    )
    finding = scorer(ctx)
    assert finding.status is EvalFindingStatus.FAIL
    assert "integrity" in finding.detail or "artifact" in finding.detail
