"""PostgresExperimentStore roundtrip tests (M14 DS-1).

Plan/Run state-machine transitions survive a PG roundtrip; ReproducibilityAudit
re-reads with audit_digest intact and re-verifies; unknown ids raise
InvalidInputError (EvidenceLedger Port convention, M5 decision D2).
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Generator
from decimal import Decimal

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.experiment_store import PostgresExperimentStore
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

pytestmark = pytest.mark.postgres

PLAN_ID = ID(str(uuid.uuid4()))
RUN_ID = ID(str(uuid.uuid4()))
RUN2_ID = ID(str(uuid.uuid4()))
RUN9_ID = ID(str(uuid.uuid4()))
AUDIT_ID = ID(str(uuid.uuid4()))


def _dsn() -> str:
    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
    )


@pytest.fixture
def store() -> Generator[PostgresExperimentStore, None, None]:
    migrate(_dsn())
    import psycopg

    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("TRUNCATE experiment_plans, experiment_runs, reproducibility_audits")
    conn.commit()
    conn.close()
    s = PostgresExperimentStore(dsn=_dsn())
    yield s
    s.close()


def _digest(tag: str) -> Digest:
    return Digest.parse(f"sha256:{tag * 64}")


def _plan() -> ExperimentPlan:
    return ExperimentPlan(
        id=PLAN_ID,
        name="sort-benchmark",
        hypothesis="policy A lowers p50 latency",
        task_contract_ref="sort_analysis_contract",
        input_spec_digest=_digest("a"),
    )


def _audit(run_id: ID) -> ReproducibilityAudit:
    return ReproducibilityAudit(
        audit_id=AUDIT_ID,
        experiment_run_id=run_id,
        input_digest=_digest("b"),
        command="python sort_bench.py --seed 42",
        environment_digest=_digest("c"),
        seed=42,
        image_digest="sha256:" + "d" * 64,
        workspace_snapshot_before="snap-" + "e" * 32,
        workspace_snapshot_after="snap-" + "f" * 32,
        output_artifact_digests=("sha256:" + "1" * 64,),
        metrics_digest=_digest("2"),
        semantic_metrics_digest=_digest("3"),
    )


def test_plan_roundtrip_with_state_transition(store: PostgresExperimentStore) -> None:
    plan = _plan().transition(ExperimentPlanState.Transition.PREREGISTER)
    store.save_plan(plan)
    loaded = store.get_plan(PLAN_ID.value)
    assert loaded == plan
    assert loaded.state == ExperimentPlanState.State.PREREGISTERED
    assert loaded.input_spec_digest == _digest("a")

    archived = loaded.transition(ExperimentPlanState.Transition.ARCHIVE)
    store.save_plan(archived)
    assert store.get_plan(PLAN_ID.value) == archived
    assert store.get_plan(PLAN_ID.value).is_terminal


def test_run_roundtrip_with_spec_result_and_metrics(store: PostgresExperimentStore) -> None:
    run = ExperimentRun(
        id=RUN_ID,
        plan_id=PLAN_ID,
        spec=ExperimentRunSpec(
            input_digest=_digest("b"),
            command="python sort_bench.py --seed 42",
            code_digest=_digest("c"),
            environment_digest=_digest("d"),
            seed=42,
            resource_profile="cpu-small",
        ),
    ).transition(ExperimentRunState.Transition.START)
    store.save_run(run)
    assert store.get_run(RUN_ID.value) == run
    assert store.get_run(RUN_ID.value).state == ExperimentRunState.State.RUNNING

    result = ExperimentRunResult(
        execution_run_id="run-abc",
        image_digest="sha256:" + "d" * 64,
        workspace_snapshot_before="snap-before",
        workspace_snapshot_after="snap-after",
        elapsed_seconds=17,
        stdout_digest=_digest("1"),
        stderr_digest=_digest("2"),
        metrics=metric_values_from_mapping({
            "p50_ms": Decimal("12.5"),
            "name": "quicksort",
            "ok": True,
            "n": 1000,
        }),
        metrics_digest=_digest("3"),
        semantic_metrics_digest=_digest("4"),
        artifact_refs=("sha256:" + "5" * 64,),
    )
    finished = run.with_result(result).transition(ExperimentRunState.Transition.COMPLETE_SUCCESS)
    store.save_run(finished)

    loaded = store.get_run(RUN_ID.value)
    assert loaded == finished
    assert loaded.completed_at is not None
    assert loaded.result is not None
    metrics = {mv.metric.name: mv for mv in loaded.result.metrics}
    assert metrics["p50_ms"].value == Decimal("12.5")
    assert metrics["p50_ms"].metric.kind.value == "NUMBER"
    assert metrics["name"].value == "quicksort"
    assert metrics["ok"].value is True
    assert metrics["n"].value == Decimal("1000")
    assert loaded.is_terminal


def test_audit_roundtrip_and_digest_reverify(store: PostgresExperimentStore) -> None:
    run_id = RUN9_ID
    audit = _audit(run_id).with_audit_digest()
    store.save_audit(audit)

    loaded = store.get_audit(RUN9_ID.value)
    assert loaded == audit
    assert loaded.audit_digest == audit.compute_audit_digest()
    assert loaded.verify()
    assert loaded.status == "PASS"

    # re-save overwrites (one audit per experiment run, upsert semantics)
    drift = ReproducibilityAudit(
        audit_id=audit.audit_id,
        experiment_run_id=run_id,
        input_digest=_digest("b"),
        seed=43,
    ).with_audit_digest()
    store.save_audit(drift)
    assert store.get_audit(RUN9_ID.value).seed == 43
    # digest resealed over the new payload → self-consistent again
    assert store.get_audit(RUN9_ID.value).verify()


def test_unknown_ids_raise_invalid_input(store: PostgresExperimentStore) -> None:
    with pytest.raises(InvalidInputError):
        store.get_plan("no-such-plan")
    with pytest.raises(InvalidInputError):
        store.get_run("no-such-run")
    with pytest.raises(InvalidInputError):
        store.get_audit("no-such-run")


def test_metric_value_decimal_roundtrip_exact(store: PostgresExperimentStore) -> None:
    """NUMBER MetricValue survives as exact Decimal (no float drift)."""
    run = ExperimentRun(
        id=RUN2_ID,
        plan_id=PLAN_ID,
        spec=ExperimentRunSpec(input_digest=_digest("b")),
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
