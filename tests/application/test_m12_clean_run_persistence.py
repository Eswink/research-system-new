"""Durable Reference Workflow persistence regression.

A personal-production run must leave one restorable PostgreSQL-shaped truth
closure rather than only returning identifiers from temporary state.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

from adapters.fakes.eval_report_store import FakeEvalReportStore
from packages.application.m12_reference.clean_run import run_clean_workflow
from packages.application.ports.eval_report_store import EvalReportQuery
from packages.domain.experiments import ExperimentPlan, ExperimentRun
from packages.domain.reproducibility import ReproducibilityAudit
from packages.domain.run import ResearchRun
from tests.application.m12_clean_run_fixtures import (
    COMMAND,
    IMAGE_DIGEST,
    PLAN_ID,
    RUN_ID,
    make_deps,
)


class _RunStore:
    def __init__(self) -> None:
        self.runs: dict[str, ResearchRun] = {}

    def list_runs(self, project_id: str | None = None) -> list[ResearchRun]:
        values = list(self.runs.values())
        if project_id is None:
            return values
        return [run for run in values if run.project_id == project_id]

    def get_run(self, run_id: str) -> ResearchRun:
        return self.runs[run_id]

    def save_run(self, run: ResearchRun) -> None:
        self.runs[run.id.value] = run


class _ExperimentStore:
    def __init__(self) -> None:
        self.plans: dict[str, ExperimentPlan] = {}
        self.runs: dict[str, ExperimentRun] = {}
        self.audits: dict[str, ReproducibilityAudit] = {}

    def save_plan(self, plan: ExperimentPlan) -> None:
        self.plans[plan.id.value] = plan

    def get_plan(self, plan_id: str) -> ExperimentPlan:
        return self.plans[plan_id]

    def save_run(self, run: ExperimentRun) -> None:
        self.runs[run.id.value] = run

    def get_run(self, run_id: str) -> ExperimentRun:
        return self.runs[run_id]

    def save_audit(self, audit: ReproducibilityAudit) -> None:
        self.audits[audit.experiment_run_id.value] = audit

    def get_audit(self, experiment_run_id: str) -> ReproducibilityAudit:
        return self.audits[experiment_run_id]

    def close(self) -> None:
        return None


@dataclass(frozen=True, slots=True)
class _Persistence:
    run_store: _RunStore
    experiment_store: _ExperimentStore
    eval_report_store: FakeEvalReportStore


def test_reference_run_persists_restorable_truth_closure(tmp_path: Path) -> None:
    base = make_deps(tmp_path)
    run_store = _RunStore()
    experiment_store = _ExperimentStore()
    eval_store = FakeEvalReportStore()
    deps = replace(
        base,
        expected_image_digest=IMAGE_DIGEST,
        persistence=_Persistence(
            run_store=run_store,
            experiment_store=experiment_store,
            eval_report_store=eval_store,
        ),
    )

    result = run_clean_workflow(
        deps,
        experiment_plan_id=PLAN_ID,
        experiment_command=COMMAND,
    )

    run = run_store.get_run(RUN_ID)
    assert run.state == "SUCCEEDED"
    manifest_id = f"{RUN_ID}:run_manifest.json"
    manifest_meta = deps.artifacts.meta(manifest_id)
    assert manifest_meta is not None
    assert str(manifest_meta.digest) == result.manifest_digest == str(run.manifest_digest)
    assert deps.artifacts.verify(manifest_id) is True

    assert experiment_store.plans
    assert result.experiment_run_id in experiment_store.runs
    assert result.experiment_run_id in experiment_store.audits

    reports = eval_store.query(EvalReportQuery(run_id=RUN_ID))
    assert len(reports) == 1
    assert reports[0].report_digest == result.eval_report_digest
    assert reports[0].verdict.value == "PASS"

    deliverable_id = f"{RUN_ID}:deliverable.json"
    deliverable_meta = deps.artifacts.meta(deliverable_id)
    assert deliverable_meta is not None
    assert str(deliverable_meta.digest) == result.deliverable_digest
    assert deps.artifacts.verify(deliverable_id) is True
    deliverable = json.loads(deps.artifacts.get(deliverable_id).decode("utf-8"))
    assert deliverable["run_id"] == RUN_ID
    assert deliverable["evaluation"]["verdict"] == "PASS"
    assert result.claim_id in deliverable_meta.source_refs
    assert result.eval_report_digest in deliverable_meta.source_refs
