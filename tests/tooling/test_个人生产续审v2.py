"""Independent PA-1R counterexamples for deployment and research truth."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import create_autospec

import pytest

import tools.personal_reference_workflow as production
from adapters.execution.remote_backend import RemoteExecutionBackend
from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.eval_report_store import FakeEvalReportStore
from adapters.fakes.execution_job_queue import FakeExecutionJobQueue
from adapters.fakes.experiment_store import FakeExperimentStore
from adapters.relay.registry_credential_resolver import RegistryCredentialResolver
from packages.application.deliverable.builder import (
    DeliverableBuildError,
    _get_artifact_content,
)
from packages.application.m12_reference.clean_run import run_clean_workflow
from packages.domain.artifacts import Artifact
from packages.domain.budget import LedgerCostStatus, ResourceType, UsageLedgerEntry
from packages.domain.core import Digest
from packages.domain.enums import MemoryType
from packages.domain.workspace import ExecutionSpec
from services.api.worker_gateway.composition import build_worker_gateway_deps
from tests.application.m12_clean_run_fixtures import (
    COMMAND,
    IMAGE_DIGEST,
    PLAN_ID,
    RUN_ID,
    make_deps,
)
from tests.application.test_m12_clean_run_persistence import (
    _Persistence,
    _RunStore,
)

OTHER_RUN = "33333333-4444-4555-8666-777777777777"


def _durable_deps(tmp_path: Path) -> Any:
    return replace(
        make_deps(tmp_path),
        expected_image_digest=IMAGE_DIGEST,
        persistence=_Persistence(_RunStore(), FakeExperimentStore(), FakeEvalReportStore()),
    )


def _foreign_usage() -> UsageLedgerEntry:
    return UsageLedgerEntry(
        entry_id="usage:foreign-run:cpu",
        resource_type=ResourceType.CPU_TIME,
        quantity=999,
        unit="seconds",
        cost_status=LedgerCostStatus.UNKNOWN,
        source="regression",
        occurred_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
        run_id=OTHER_RUN,
    )


def test_deliverable_and_summary_exclude_other_runs(tmp_path: Path) -> None:
    deps = _durable_deps(tmp_path)
    deps.budget.record_usage(_foreign_usage())

    result = run_clean_workflow(deps, experiment_plan_id=PLAN_ID, experiment_command=COMMAND)

    own = [entry for entry in deps.budget.snapshot().entries if entry.run_id == RUN_ID]
    report = json.loads(deps.artifacts.get(f"{RUN_ID}:deliverable.json"))
    assert result.budget_entries == len(own)
    assert report["budget"]["entries"] == len(own)
    assert report["budget"]["experiment_runs"] == 1
    assert report["budget"]["experiment_seconds"] == 12
    assert all(
        item["entry_id"] != "usage:foreign-run:cpu" for item in report["budget"]["ledger_entries"]
    )


def test_duration_known_does_not_depend_on_price_availability(tmp_path: Path) -> None:
    deps = _durable_deps(tmp_path)
    run_clean_workflow(deps, experiment_plan_id=PLAN_ID, experiment_command=COMMAND)
    report = json.loads(deps.artifacts.get(f"{RUN_ID}:deliverable.json"))
    assert report["budget"]["experiment_duration_known"] is True
    assert any(item["cost_status"] == "UNKNOWN" for item in report["budget"]["ledger_entries"])


def test_memory_kind_and_id_come_from_reference_configuration(tmp_path: Path) -> None:
    deps = replace(_durable_deps(tmp_path), memory_kind=MemoryType.FACT)
    run_clean_workflow(deps, experiment_plan_id=PLAN_ID, experiment_command=COMMAND)
    report = json.loads(deps.artifacts.get(f"{RUN_ID}:deliverable.json"))
    assert report["memory"]["kind"] == "FACT"
    assert report["memory"]["memory_id"] == f"mem:{RUN_ID}:fact"


def test_production_composition_wires_memory_kind_to_workflow(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("RESEARCHOS_POSTGRES_DSN", "unused")
    monkeypatch.chdir(tmp_path)
    for name in (
        "migrate",
        "PostgresArtifactStore",
        "PostgresEvidenceLedger",
        "PostgresBudgetLedger",
        "PostgresMemoryStore",
        "PostgresExecutionJobQueue",
        "PostgresRunStore",
        "PostgresExperimentStore",
        "PostgresEvalReportStore",
        "_catalog",
        "_project",
        "_context",
        "load_protocol",
    ):
        original = getattr(production, name)
        mock = create_autospec(original)
        if isinstance(original, type):
            # Constructors retain real signatures; no DB connection is opened.
            mock.return_value = SimpleNamespace(close=lambda: None)
        monkeypatch.setattr(production, name, mock)
    resources = production._build_resources(RUN_ID, False)
    assert resources.deps.memory_kind is MemoryType.FACT
    assert resources.deps.execution._run_id == RUN_ID  # type: ignore[attr-defined]
    assert "FP32" in resources.deps.objective
    resources.close()


def _bound_backend(run_id: str, queue: FakeExecutionJobQueue, artifacts: FakeArtifactStore) -> Any:
    factory = getattr(RemoteExecutionBackend, "for_run", None)
    if factory is not None:
        return factory(run_id, job_queue=queue, artifacts=artifacts)
    # The pre-fix production assembly has no run binding; exercise it unchanged.
    return RemoteExecutionBackend(job_queue=queue, artifacts=artifacts)


def test_remote_jobs_keep_parent_run_and_separate_idempotency(tmp_path: Path) -> None:
    queue = FakeExecutionJobQueue()
    artifacts = FakeArtifactStore()
    spec = ExecutionSpec(backend_kind="DOCKER", command="echo ok", workspace_path=str(tmp_path))
    first = _bound_backend(RUN_ID, queue, artifacts)
    second = _bound_backend(OTHER_RUN, queue, artifacts)

    task = first._submit(spec, tmp_path)
    repeat = first._submit(spec, tmp_path)
    foreign = second._submit(spec, tmp_path)

    assert queue.state.jobs[task].run_id == RUN_ID
    assert repeat == task
    assert foreign != task
    assert queue.state.jobs[foreign].run_id == OTHER_RUN


def test_remote_deduplication_covers_execution_configuration(tmp_path: Path) -> None:
    queue = FakeExecutionJobQueue()
    artifacts = FakeArtifactStore()
    backend = _bound_backend(RUN_ID, queue, artifacts)
    base = ExecutionSpec(backend_kind="DOCKER", command="echo ok", resource_profile="small")
    tasks = {
        backend._submit(spec, tmp_path)
        for spec in (
            base,
            replace(base, resource_profile="gpu-small"),
            replace(base, environment={"SEED": "8"}),
        )
    }
    assert len(tasks) == 3


def test_gateway_uses_documented_canonical_blob_root(monkeypatch: pytest.MonkeyPatch) -> None:
    root = "data/independent-canonical-blobs"
    monkeypatch.setenv("RESEARCHOS_ARTIFACT_BLOB_DIR", root)
    monkeypatch.delenv("RESEARCHOS_WORKER_ARTIFACT_BLOB_DIR", raising=False)
    for module, name in (
        ("artifact_store", "PostgresArtifactStore"),
        ("execution_job_queue", "PostgresExecutionJobQueue"),
        ("worker_registry", "PostgresWorkerRegistry"),
        ("workflow_engine", "PostgresWorkflowEngine"),
    ):
        monkeypatch.setattr(f"adapters.postgres.{module}.{name}", lambda **kw: kw)
        monkeypatch.setattr(f"services.api.worker_gateway.composition.{name}", lambda **kw: kw)
    deps = build_worker_gateway_deps(dsn="unused", credentials=RegistryCredentialResolver())
    assert deps.artifacts is not None
    assert deps.artifacts["blob_dir"] == root


def test_deployment_restore_query_matches_canonical_schema() -> None:
    doc = Path("docs/operations/PERSONAL_DEPLOYMENT.md").read_text(encoding="utf-8")
    assert "SELECT id, state, manifest_digest FROM runs" not in doc
    assert "run_json->>'state'" in doc


def test_deliverable_rejects_content_that_disagrees_with_metadata() -> None:
    class CorruptRead(FakeArtifactStore):
        def get(self, artifact_id: str) -> bytes:
            return b"modified after admission"

    artifacts = CorruptRead()
    content = b"original experiment result"
    artifacts.put(
        Artifact(
            id="result",
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="text/plain",
        ),
        content,
    )
    with pytest.raises(DeliverableBuildError, match="digest"):
        _get_artifact_content(artifacts, "result")
