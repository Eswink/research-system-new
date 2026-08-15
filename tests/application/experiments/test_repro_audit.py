"""ReproducibilityAudit use case 测试（M9）。"""

from __future__ import annotations

from decimal import Decimal

import pytest

from adapters.fakes import FakeArtifactStore
from packages.application.experiments.repro_audit import (
    build_reproducibility_audit,
    is_auditable_state,
    verify_reproducibility_audit,
)
from packages.application.ports.errors import InvalidInputError
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest
from packages.domain.experiment_state import ExperimentRunState
from packages.domain.experiments import (
    ExperimentRun,
    ExperimentRunResult,
    ExperimentRunSpec,
    metric_value_from_raw,
)
from packages.domain.reproducibility import ReproducibilityAudit

_PLAN_ID = ID("3f1c6a8e-9b2d-4f3a-8c5e-1a2b3c4d5e6f")
_RUN_ID = ID("7a2b3c4d-5e6f-4a5b-9c0d-1e2f3a4b5c6d")
_AUDIT_ID = ID("8b3c4d5e-6f7a-4b5c-9d0e-1f2a3b4c5d6e")


def _terminal_run() -> ExperimentRun:
    spec = ExperimentRunSpec(
        input_digest=Digest.of_bytes(b"input"),
        code_digest=Digest.of_bytes(b"code"),
        environment_digest=Digest.of_bytes(b"env"),
        seed=42,
        resource_profile="small",
    )
    result = ExperimentRunResult(
        execution_run_id="exec-1",
        image_digest="sha256:" + "ab" * 32,
        workspace_snapshot_before="sha256:" + "cd" * 32,
        workspace_snapshot_after="sha256:" + "ef" * 32,
        stdout_digest=Digest.of_bytes(b"stdout"),
        stderr_digest=Digest.of_bytes(b"stderr"),
        metrics=(metric_value_from_raw("accuracy", Decimal("0.5")),),
        artifact_refs=("a-1", "a-2"),
    )
    run = ExperimentRun(id=_RUN_ID, plan_id=_PLAN_ID, spec=spec)
    run = run.transition(ExperimentRunState.Transition.START)
    run = run.with_result(result)
    return run.transition(ExperimentRunState.Transition.COMPLETE_SUCCESS)


def _store_with_outputs() -> FakeArtifactStore:
    store = FakeArtifactStore()
    for artifact_id, content in (
        ("a-1", b"content-1"),
        ("a-2", b"content-2"),
    ):
        store.put(
            Artifact(
                id=artifact_id,
                digest=Digest.of_bytes(content),
                size_bytes=len(content),
                media_type="application/octet-stream",
            ),
            content,
        )
    return store


class TestBuildAudit:
    def test_terminal_run_produces_sealed_audit(self) -> None:
        audit = build_reproducibility_audit(
            _terminal_run(), audit_id=_AUDIT_ID, artifacts=_store_with_outputs()
        )
        assert audit.status == "PASS"
        assert verify_reproducibility_audit(audit)

    def test_audit_binds_all_anchors(self) -> None:
        audit = build_reproducibility_audit(
            _terminal_run(), audit_id=_AUDIT_ID, artifacts=_store_with_outputs()
        )
        assert audit.seed == 42
        assert audit.resource_profile == "small"
        assert audit.image_digest == "sha256:" + "ab" * 32
        assert audit.output_artifact_digests == tuple(
            str(Digest.of_bytes(content)) for content in (b"content-1", b"content-2")
        )
        assert audit.metrics_digest is not None

    def test_missing_artifact_ref_rejected(self) -> None:
        store = FakeArtifactStore()
        with pytest.raises(InvalidInputError):
            build_reproducibility_audit(_terminal_run(), audit_id=_AUDIT_ID, artifacts=store)

    def test_non_terminal_run_rejected(self) -> None:
        pending = ExperimentRun(id=_RUN_ID, plan_id=_PLAN_ID)
        with pytest.raises(InvalidInputError):
            build_reproducibility_audit(
                pending, audit_id=_AUDIT_ID, artifacts=_store_with_outputs()
            )

    def test_auditable_state_guard(self) -> None:
        assert is_auditable_state(ExperimentRunState.State.SUCCEEDED)
        assert is_auditable_state(ExperimentRunState.State.NEGATIVE_RESULT)
        assert not is_auditable_state(ExperimentRunState.State.FAILED)
        assert not is_auditable_state(ExperimentRunState.State.TIMED_OUT)


class TestAuditTampering:
    def test_digest_change_breaks_verify(self) -> None:
        audit = build_reproducibility_audit(
            _terminal_run(), audit_id=_AUDIT_ID, artifacts=_store_with_outputs()
        )
        tampered = ReproducibilityAudit(
            audit_id=audit.audit_id,
            experiment_run_id=audit.experiment_run_id,
            input_digest=audit.input_digest,
            code_digest=audit.code_digest,
            environment_digest=audit.environment_digest,
            seed=audit.seed,
            resource_profile=audit.resource_profile,
            image_digest=audit.image_digest,
            workspace_snapshot_before=audit.workspace_snapshot_before,
            workspace_snapshot_after=audit.workspace_snapshot_after,
            output_artifact_digests=audit.output_artifact_digests,
            metrics_digest=audit.metrics_digest,
            audit_digest=audit.audit_digest,
        )
        tampered = ReproducibilityAudit(
            audit_id=tampered.audit_id,
            experiment_run_id=tampered.experiment_run_id,
            input_digest=tampered.input_digest,
            seed=43,
            audit_digest=tampered.audit_digest,
        )
        assert not verify_reproducibility_audit(tampered)
