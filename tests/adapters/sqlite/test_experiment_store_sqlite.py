"""SqliteExperimentStore roundtrip tests（PLAN-040 WP-A）。

与 `tests/postgres/test_experiment_store_pg.py` 同一语义矩阵（Port 契约共享）：
plan/run 状态迁移与 spec/result 完整往返、audit 重算自洽、未知 id
InvalidInputError、Decimal 精确无浮点漂移。SQLite 开发路径与 PG canonical
state 双实现必须给出一致结果。
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from decimal import Decimal

import pytest

from adapters.sqlite.experiment_store import SqliteExperimentStore
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import ID, Digest
from packages.domain.experiment_state import ExperimentPlanState, ExperimentRunState
from packages.domain.experiments import (
    ExperimentPlan,
    ExperimentRun,
    ExperimentRunResult,
    ExperimentRunSpec,
    metric_value_from_raw,
    metric_values_from_mapping,
)
from packages.domain.reproducibility import ReproducibilityAudit

PLAN_ID = ID(str(uuid.uuid4()))
RUN_ID = ID(str(uuid.uuid4()))
RUN2_ID = ID(str(uuid.uuid4()))
AUDIT_ID = ID(str(uuid.uuid4()))


def _digest(tag: bytes) -> Digest:
    return Digest.of_bytes(tag)


@pytest.fixture
def store() -> Iterator[SqliteExperimentStore]:
    s = SqliteExperimentStore(":memory:")
    yield s
    s.close()


def _plan() -> ExperimentPlan:
    return ExperimentPlan(
        id=PLAN_ID,
        name="sort-benchmark",
        hypothesis="policy A lowers p50 latency",
        task_contract_ref="sort_analysis_contract",
        input_spec_digest=_digest(b"plan-input"),
    )


def test_plan_roundtrip_with_state_transition(store: SqliteExperimentStore) -> None:
    plan = _plan().transition(ExperimentPlanState.Transition.PREREGISTER)
    store.save_plan(plan)
    loaded = store.get_plan(PLAN_ID.value)
    assert loaded == plan
    assert loaded.state == ExperimentPlanState.State.PREREGISTERED
    assert loaded.input_spec_digest == _digest(b"plan-input")

    archived = loaded.transition(ExperimentPlanState.Transition.ARCHIVE)
    store.save_plan(archived)
    assert store.get_plan(PLAN_ID.value) == archived
    assert store.get_plan(PLAN_ID.value).is_terminal


def test_run_roundtrip_with_spec_result_and_metrics(store: SqliteExperimentStore) -> None:
    run = ExperimentRun(
        id=RUN_ID,
        plan_id=PLAN_ID,
        spec=ExperimentRunSpec(
            input_digest=_digest(b"run-input"),
            command="python sort_bench.py --seed 42",
            code_digest=_digest(b"run-code"),
            environment_digest=_digest(b"run-env"),
            seed=42,
            resource_profile="cpu-small",
        ),
    ).transition(ExperimentRunState.Transition.START)
    store.save_run(run)
    assert store.get_run(RUN_ID.value) == run
    assert store.get_run(RUN_ID.value).state == ExperimentRunState.State.RUNNING

    result = ExperimentRunResult(
        execution_run_id="run-abc",
        image_digest=str(_digest(b"run-image")),
        workspace_snapshot_before="snap-before",
        workspace_snapshot_after="snap-after",
        elapsed_seconds=17,
        stdout_digest=_digest(b"stdout"),
        stderr_digest=_digest(b"stderr"),
        metrics=metric_values_from_mapping({
            "p50_ms": Decimal("12.5"),
            "name": "quicksort",
            "ok": True,
        }),
        metrics_digest=_digest(b"metrics"),
        semantic_metrics_digest=_digest(b"semantic"),
        artifact_refs=(str(_digest(b"artifact-ref")),),
    )
    finished = run.with_result(result).transition(ExperimentRunState.Transition.COMPLETE_SUCCESS)
    store.save_run(finished)

    loaded = store.get_run(RUN_ID.value)
    assert loaded == finished
    assert loaded.completed_at is not None
    assert loaded.result is not None
    metrics = {mv.metric.name: mv for mv in loaded.result.metrics}
    assert metrics["p50_ms"].value == Decimal("12.5")
    assert metrics["name"].value == "quicksort"
    assert metrics["ok"].value is True
    assert loaded.is_terminal


def test_audit_roundtrip_and_digest_reverify(store: SqliteExperimentStore) -> None:
    audit = ReproducibilityAudit(
        audit_id=AUDIT_ID,
        experiment_run_id=RUN_ID,
        input_digest=_digest(b"audit-input"),
        command="python sort_bench.py --seed 42",
        seed=42,
        image_digest=str(_digest(b"audit-image")),
    ).with_audit_digest()
    store.save_audit(audit)

    loaded = store.get_audit(RUN_ID.value)
    assert loaded == audit
    assert loaded.audit_digest == audit.compute_audit_digest()
    assert loaded.verify()

    drift = ReproducibilityAudit(
        audit_id=audit.audit_id,
        experiment_run_id=RUN_ID,
        input_digest=_digest(b"audit-input"),
        seed=43,
    ).with_audit_digest()
    store.save_audit(drift)
    # re-save overwrites (one audit per experiment run, upsert semantics)
    assert store.get_audit(RUN_ID.value).seed == 43
    assert store.get_audit(RUN_ID.value).verify()


def test_unknown_ids_raise_invalid_input(store: SqliteExperimentStore) -> None:
    with pytest.raises(InvalidInputError):
        store.get_plan("no-such-plan")
    with pytest.raises(InvalidInputError):
        store.get_run("no-such-run")
    with pytest.raises(InvalidInputError):
        store.get_audit("no-such-run")


def test_metric_value_decimal_roundtrip_exact(store: SqliteExperimentStore) -> None:
    """NUMBER MetricValue survives as exact Decimal (no float drift)."""
    run = ExperimentRun(
        id=RUN2_ID,
        plan_id=PLAN_ID,
        spec=ExperimentRunSpec(input_digest=_digest(b"run2-input")),
    )
    result = ExperimentRunResult(
        execution_run_id="run-xyz",
        metrics=(
            metric_value_from_raw("ratio", Decimal("0.1"), source_ref="stdout"),
            metric_value_from_raw("exact", "text"),
        ),
    )
    run = run.with_result(result).transition(ExperimentRunState.Transition.START)
    store.save_run(run)
    loaded = store.get_run(RUN2_ID.value)
    assert loaded.result is not None
    metrics = {mv.metric.name: mv for mv in loaded.result.metrics}
    assert metrics["ratio"].value == Decimal("0.1")
    assert metrics["exact"].value == "text"
