"""Experiment 域实体与状态机测试（M9）。"""

from __future__ import annotations

from decimal import Decimal

import pytest

from packages.domain.core import ID, Digest
from packages.domain.experiment_state import ExperimentPlanState, ExperimentRunState
from packages.domain.experiments import (
    ExperimentPlan,
    ExperimentRun,
    ExperimentRunResult,
    ExperimentRunSpec,
    Metric,
    MetricKind,
    MetricValue,
    metric_value_from_raw,
    metric_values_from_mapping,
)
from packages.domain.reproducibility import ReproducibilityAudit
from packages.domain.serialization import digest_of
from packages.domain.state_base import InvalidTransitionError

_PLAN_ID = ID("3f1c6a8e-9b2d-4f3a-8c5e-1a2b3c4d5e6f")
_RUN_ID = ID("7a2b3c4d-5e6f-4a5b-9c0d-1e2f3a4b5c6d")


def _plan() -> ExperimentPlan:
    return ExperimentPlan(id=_PLAN_ID, name="sort-benchmark")


def _spec() -> ExperimentRunSpec:
    return ExperimentRunSpec(
        input_digest=Digest.of_bytes(b"input"),
        code_digest=Digest.of_bytes(b"code"),
        environment_digest=Digest.of_bytes(b"env"),
        seed=42,
        resource_profile="small",
    )


class TestExperimentPlanStateMachine:
    def test_draft_to_preregistered_to_archived(self) -> None:
        plan = _plan()
        assert plan.state == ExperimentPlanState.State.DRAFT
        plan = plan.transition(ExperimentPlanState.Transition.PREREGISTER)
        assert plan.state == ExperimentPlanState.State.PREREGISTERED
        plan = plan.transition(ExperimentPlanState.Transition.ARCHIVE)
        assert plan.state == ExperimentPlanState.State.ARCHIVED
        assert plan.is_terminal

    def test_draft_can_archive_directly(self) -> None:
        plan = _plan().transition(ExperimentPlanState.Transition.ARCHIVE)
        assert plan.state == ExperimentPlanState.State.ARCHIVED

    def test_preregistered_cannot_unregister(self) -> None:
        plan = _plan().transition(ExperimentPlanState.Transition.PREREGISTER)
        with pytest.raises(InvalidTransitionError):
            plan.transition(ExperimentPlanState.Transition.PREREGISTER)

    def test_terminal_has_no_outgoing(self) -> None:
        plan = _plan().transition(ExperimentPlanState.Transition.ARCHIVE)
        with pytest.raises(InvalidTransitionError):
            plan.transition(ExperimentPlanState.Transition.ARCHIVE)


class TestExperimentRunStateMachine:
    def test_happy_path_to_succeeded(self) -> None:
        run = ExperimentRun(id=_RUN_ID, plan_id=_PLAN_ID)
        run = run.transition(ExperimentRunState.Transition.START)
        assert run.started_at is not None
        run = run.transition(ExperimentRunState.Transition.COMPLETE_SUCCESS)
        assert run.state == ExperimentRunState.State.SUCCEEDED
        assert run.completed_at is not None
        assert run.is_terminal

    def test_negative_result_is_terminal_and_distinct(self) -> None:
        run = ExperimentRun(id=_RUN_ID, plan_id=_PLAN_ID)
        run = run.transition(ExperimentRunState.Transition.START)
        run = run.transition(ExperimentRunState.Transition.COMPLETE_NEGATIVE)
        assert run.state == ExperimentRunState.State.NEGATIVE_RESULT
        assert run.is_terminal

    def test_failed_and_timed_out_are_terminal(self) -> None:
        for event in (
            ExperimentRunState.Transition.COMPLETE_FAILED,
            ExperimentRunState.Transition.COMPLETE_TIMED_OUT,
        ):
            run = ExperimentRun(id=_RUN_ID, plan_id=_PLAN_ID)
            run = run.transition(ExperimentRunState.Transition.START)
            run = run.transition(event)
            assert run.is_terminal

    def test_cancel_from_pending_and_running(self) -> None:
        pending = ExperimentRun(id=_RUN_ID, plan_id=_PLAN_ID)
        assert (
            pending.transition(ExperimentRunState.Transition.CANCEL).state
            == ExperimentRunState.State.CANCELLED
        )
        running = pending.transition(ExperimentRunState.Transition.START)
        assert (
            running.transition(ExperimentRunState.Transition.CANCEL).state
            == ExperimentRunState.State.CANCELLED
        )

    def test_terminal_cannot_transition(self) -> None:
        run = ExperimentRun(id=_RUN_ID, plan_id=_PLAN_ID)
        run = run.transition(ExperimentRunState.Transition.START)
        run = run.transition(ExperimentRunState.Transition.COMPLETE_SUCCESS)
        with pytest.raises(InvalidTransitionError):
            run.transition(ExperimentRunState.Transition.CANCEL)

    def test_with_result_preserves_state(self) -> None:
        run = ExperimentRun(id=_RUN_ID, plan_id=_PLAN_ID, spec=_spec())
        result = ExperimentRunResult(execution_run_id="exec-1")
        with_result = run.with_result(result)
        assert with_result.state == ExperimentRunState.State.PENDING
        assert with_result.result is result
        assert with_result.spec is run.spec


class TestExperimentRunSpecInvariants:
    def test_negative_seed_rejected(self) -> None:
        with pytest.raises(ValueError):
            ExperimentRunSpec(input_digest=Digest.of_bytes(b"x"), seed=-1)

    def test_spec_digest_deterministic(self) -> None:
        first = _spec()
        second = ExperimentRunSpec(
            input_digest=Digest.of_bytes(b"input"),
            code_digest=Digest.of_bytes(b"code"),
            environment_digest=Digest.of_bytes(b"env"),
            seed=42,
            resource_profile="small",
        )
        assert digest_of(first) == digest_of(second)


class TestMetricValue:
    def test_number_metric_normalizes_to_decimal(self) -> None:
        value = metric_value_from_raw("accuracy", Decimal("0.91"))
        assert value.metric.kind is MetricKind.NUMBER
        assert isinstance(value.value, Decimal)
        assert str(value.value) == "0.91"

    def test_float_rejected_by_domain_policy(self) -> None:
        """float 拒绝进入 Domain（canonical digest 禁止 float；解析层已转 Decimal）。"""
        with pytest.raises(ValueError):
            metric_value_from_raw("accuracy", 0.91)

    def test_string_bool_null_metrics(self) -> None:
        assert metric_value_from_raw("name", "alpha").metric.kind is MetricKind.STRING
        assert metric_value_from_raw("flag", True).metric.kind is MetricKind.BOOLEAN
        assert metric_value_from_raw("missing", None).metric.kind is MetricKind.NULL

    def test_unsupported_type_rejected(self) -> None:
        with pytest.raises(ValueError):
            metric_value_from_raw("x", object())

    def test_kind_value_mismatch_rejected(self) -> None:
        metric = Metric(name="m", kind=MetricKind.NUMBER)
        with pytest.raises(ValueError):
            MetricValue(metric=metric, value="not-a-number")

    def test_mapping_to_values_is_deterministic_order(self) -> None:
        values = metric_values_from_mapping({"b": 2, "a": 1})
        assert [value.metric.name for value in values] == ["a", "b"]

    def test_metric_values_participate_in_digest(self) -> None:
        first = metric_values_from_mapping({"a": 1, "b": 2})
        second = metric_values_from_mapping({"a": 1, "b": 2})
        assert digest_of(first) == digest_of(second)


class TestReproducibilityAudit:
    def _audit(self, **overrides: object) -> ReproducibilityAudit:
        fields: dict[str, object] = {
            "audit_id": ID("8b3c4d5e-6f7a-4b5c-9d0e-1f2a3b4c5d6e"),
            "experiment_run_id": _RUN_ID,
            "input_digest": Digest.of_bytes(b"input"),
            "code_digest": Digest.of_bytes(b"code"),
            "environment_digest": Digest.of_bytes(b"env"),
            "seed": 42,
            "resource_profile": "small",
            "image_digest": "sha256:" + "ab" * 32,
            "workspace_snapshot_before": "sha256:" + "cd" * 32,
            "workspace_snapshot_after": "sha256:" + "ef" * 32,
            "output_artifact_digests": ("sha256:" + "12" * 32,),
            "metrics_digest": Digest.of_bytes(b"metrics"),
            **overrides,
        }
        return ReproducibilityAudit(**fields)  # type: ignore[arg-type]

    def test_full_binding_passes(self) -> None:
        audit = self._audit().with_audit_digest()
        assert audit.status == "PASS"
        assert audit.verify()

    def test_missing_image_digest_fails(self) -> None:
        audit = self._audit(image_digest=None).with_audit_digest()
        assert audit.status == "FAIL"

    def test_missing_snapshot_fails(self) -> None:
        audit = self._audit(workspace_snapshot_before=None).with_audit_digest()
        assert audit.status == "FAIL"

    def test_empty_output_artifacts_fails(self) -> None:
        audit = self._audit(output_artifact_digests=()).with_audit_digest()
        assert audit.status == "FAIL"

    def test_missing_metrics_fails(self) -> None:
        audit = self._audit(metrics_digest=None).with_audit_digest()
        assert audit.status == "FAIL"

    def test_tampered_binding_fails_verify(self) -> None:
        audit = self._audit().with_audit_digest()
        tampered = self._audit(seed=43, audit_digest=audit.audit_digest)
        assert not tampered.verify()

    def test_unsealed_audit_fails_verify(self) -> None:
        assert not self._audit().verify()

    def test_audit_digest_deterministic_across_instances(self) -> None:
        first = self._audit().with_audit_digest()
        second = self._audit().with_audit_digest()
        assert first.audit_digest == second.audit_digest
