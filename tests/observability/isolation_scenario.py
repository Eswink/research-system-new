"""确定性 canonical 场景与状态投影(failure-isolation 共用)。"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from adapters.sqlite.budget_ledger import SqliteBudgetLedger
from adapters.sqlite.evidence_ledger import SqliteEvidenceLedger
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.observability.signals import OperationBegin
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.application.ports.workflow_engine import TaskCompletion
from packages.domain.budget import (
    BudgetPolicy,
    BudgetReservation,
    LedgerCostStatus,
    ResourceType,
    UsageLedgerEntry,
)
from packages.domain.core import ID
from packages.domain.enums import TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.tasks import ResearchTask
from tests.contracts.fixtures import research_task, task_contract

__all__ = [
    "_begin_only",
    "_canonical_state",
    "_clock",
    "_evidence",
    "_engine",
    "_ledger",
    "_run_workflow",
    "_state_with",
    "_task",
]

_BASE = datetime(2026, 8, 29, 12, 0, 0, tzinfo=timezone.utc)
_TICK = iter(range(0, 1_000_000))


def _clock() -> datetime:
    return _BASE + timedelta(milliseconds=100 * next(_TICK))


def _engine(telemetry: TelemetrySink | None) -> SqliteWorkflowEngine:
    return SqliteWorkflowEngine(":memory:", now=_clock, telemetry=telemetry)


def _ledger() -> SqliteBudgetLedger:
    return SqliteBudgetLedger(":memory:")


def _evidence() -> SqliteEvidenceLedger:
    ledger = SqliteEvidenceLedger(":memory:")
    ledger.register_source(
        SourceRecord(
            origin="task:demo:artifact",
            content_digest="sha256:aa",
            trust_label=TrustLabel.GENERATED,
            access_time=None,
        )
    )
    ledger.register_evidence(
        Evidence(
            id="ev-1",
            source_ref="task:demo:artifact",
            content_digest="sha256:bb",
            artifact_id="artifact-1",
        )
    )
    ledger.register_claim(
        Claim(
            id="claim-1",
            statement="a measurable statement",
            status=ClaimStatus.PROPOSED,
            evidence_relations=[("ev-1", EvidenceRelationType.SUPPORTS)],
        )
    )
    return ledger


def _canonical_state(
    engine: SqliteWorkflowEngine,
    ledger: SqliteBudgetLedger,
    evidence: SqliteEvidenceLedger,
) -> dict[str, object]:
    """canonical 投影:确定性 id + 注入时钟 → 两次运行可逐项比较。"""
    run_id = str(research_task().run_id.value)
    return {
        "tasks": sorted((str(row.task.id), row.task.status) for row in engine.list_tasks(run_id)),
        "deliveries": sorted(engine.deliveries.items()),
        "completed": sorted((key, value.outcome) for key, value in engine.completed.items()),
        "usage": sorted(
            (entry.entry_id, entry.quantity, entry.cost_status.value)
            for entry in ledger.snapshot().entries
        ),
        "reservations": sorted(res.id for res in ledger.snapshot().reservations),
        "claims": sorted(claim.id for claim in evidence.claims()),
        "has_relation": bool(evidence.relations_for_claim("claim-1")),
    }


def _task(task_id: str, agent: str, idem: str) -> ResearchTask:
    base = research_task(task_id)
    return replace(base, id=ID(task_id), assigned_agent_id=agent, idempotency_key=idem)


def _run_workflow(
    engine: SqliteWorkflowEngine,
    ledger: SqliteBudgetLedger,
    evidence: SqliteEvidenceLedger,
) -> None:
    task_a = _task("6f8f56a0-5c2a-4b3e-9f1d-2c7a4e8b6d90", "agent-1", "idem-a")
    task_b = _task("6f8f56a0-5c2a-4b3e-9f1d-2c7a4e8b6d91", "agent-2", "idem-b")
    engine.submit(task_a, task_contract())
    engine.submit(task_b, task_contract())
    lease_a = engine.acquire_lease(task_a.id.value)
    lease_b = engine.acquire_lease(task_b.id.value)
    lease_a = engine.heartbeat(lease_a)  # heartbeat 续租返回新 lease_id
    engine.complete(lease_a, TaskCompletion(task_id=task_a.id.value, outcome="SUCCEEDED"))
    engine.complete(lease_b, TaskCompletion(task_id=task_b.id.value, outcome="FAILED"))
    _ = ledger.reserve(
        (
            BudgetReservation(
                id="res-1",
                scope="run-1",
                resource_type=ResourceType.MODEL_TOKENS,
                quantity=1000,
                unit="tokens",
            ),
        ),
        BudgetPolicy(id="policy-1"),
    )
    ledger.record_usage(
        UsageLedgerEntry(
            entry_id="entry-1",
            resource_type=ResourceType.MODEL_TOKENS,
            quantity=100,
            unit="tokens",
            cost_status=LedgerCostStatus.KNOWN,
            estimated_cost_minor=123,
            source="llm",
            occurred_at=_clock(),
        )
    )


def _state_with(telemetry: TelemetrySink | None) -> dict[str, object]:
    """跑一次 canonical 场景并返回投影(telemetry 可为 None / FailSafe)。"""
    engine = _engine(telemetry)
    ledger = _ledger()
    evidence = _evidence()
    _run_workflow(engine, ledger, evidence)
    return _canonical_state(engine, ledger, evidence)


def _begin_only(call_id: str) -> OperationBegin:
    from packages.application.observability.signals import (
        CorrelationRef,
        OperationScope,
        ParentSpanRef,
        SpanRef,
    )

    return OperationBegin(
        span_ref=SpanRef(value=f"{abs(hash(call_id)) % (10**32):032d}"),
        parent_span_ref=ParentSpanRef(value=None),
        scope=OperationScope.LLM_CALL,
        name="llm.call",
        correlation=CorrelationRef(tool_call_id=call_id),
        started_at=datetime.now(timezone.utc),
    )
