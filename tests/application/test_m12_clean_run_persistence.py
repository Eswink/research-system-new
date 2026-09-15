"""Durable Reference Workflow persistence regression.

A personal-production run must leave one restorable PostgreSQL-shaped truth
closure rather than only returning identifiers from temporary state.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

from adapters.fakes.eval_report_store import FakeEvalReportStore
from adapters.fakes.experiment_store import FakeExperimentStore
from packages.application.m12_reference.clean_run import run_clean_workflow
from packages.application.ports.eval_report_store import EvalReportQuery
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


@dataclass(frozen=True, slots=True)
class _Persistence:
    run_store: _RunStore
    experiment_store: FakeExperimentStore
    eval_report_store: FakeEvalReportStore


def _assert_persisted_closure(store: FakeExperimentStore, experiment_run_id: str) -> None:
    """经 Port 回读整条闭包（未知 id 会抛 InvalidInputError，而非静默空值）。"""
    assert store.get_plan(PLAN_ID.value).id.value == PLAN_ID.value
    assert store.get_run(experiment_run_id).id.value == experiment_run_id
    assert store.get_audit(experiment_run_id).experiment_run_id.value == experiment_run_id


def test_reference_run_persists_restorable_truth_closure(tmp_path: Path) -> None:
    base = make_deps(tmp_path)
    run_store = _RunStore()
    experiment_store = FakeExperimentStore()
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

    experiment_run_id = result.experiment_run_id
    assert experiment_run_id is not None
    _assert_persisted_closure(experiment_store, experiment_run_id)

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
