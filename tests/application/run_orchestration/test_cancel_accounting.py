"""M15 cancellation accounting production wiring regression."""

from __future__ import annotations

from dataclasses import replace

from adapters.fakes.agent_runtime import FakeAgentRuntime
from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.budget_ledger import FakeBudgetLedger
from adapters.fakes.event_publisher import FakeEventPublisher
from adapters.fakes.workflow_engine import FakeWorkflowEngine
from packages.application.run_orchestration.commands import CancelRunCommand
from packages.application.run_orchestration.service import (
    OrchestrationDependencies,
    RunOrchestrationService,
)
from packages.domain.core import ID
from tests.contracts.fixtures import research_task, task_contract


def test_cancel_run_records_task_scoped_unknown_usage_and_replays_noop() -> None:
    run_id = ID.generate()
    workflow = FakeWorkflowEngine()
    budget = FakeBudgetLedger()
    for suffix in ("a", "b"):
        task = replace(
            research_task(),
            id=ID.generate(),
            run_id=run_id,
            idempotency_key=f"cancel-{suffix}",
        )
        workflow.submit(task, task_contract())
    service = RunOrchestrationService(
        OrchestrationDependencies(
            runtime=FakeAgentRuntime(),
            workflow=workflow,
            artifacts=FakeArtifactStore(),
            events=FakeEventPublisher(),
            budget=budget,
        )
    )

    service.cancel_run(CancelRunCommand(run_id=run_id))
    service.cancel_run(CancelRunCommand(run_id=run_id))

    entries = budget.snapshot().entries
    assert len(entries) == 2
    assert {entry.task_id for entry in entries} == set(workflow.cancelled_task_ids(run_id.value))
    assert all(entry.quantity_status.value == "UNKNOWN" for entry in entries)
    assert all(entry.quantity == 0 for entry in entries)
