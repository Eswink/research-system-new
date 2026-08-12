"""Contract suite 共享 fixtures：领域对象构造器（跨 Port 测试复用）。"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from packages.domain.budget import (
    BudgetPolicy,
    BudgetReservation,
    LedgerCostStatus,
    ResourceType,
    UsageLedgerEntry,
)
from packages.domain.core import ID, Digest, Timestamp
from packages.domain.enums import (
    AcceptanceCriterionType,
    ActivationPolicy,
    BackendKind,
    EffectClass,
    MemoryTier,
    MemoryType,
    ModelBindingMode,
    ProviderType,
    RoleCategory,
    TrustLevel,
    TrustProfile,
    WorkspacePolicy,
)
from packages.domain.events import EventEnvelope, EventType, digest_of_payload
from packages.domain.memory import MemoryWriteProposal
from packages.domain.models import LLMEndpoint
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from packages.domain.tasks import (
    AcceptanceCriterion,
    ResearchTask,
    TaskContract,
)
from packages.domain.tools import ToolCallRecord, ToolProviderSpec
from packages.domain.workspace import ExecutionSpec, Workspace

NOW = datetime(2026, 8, 12, 9, 0, 0, tzinfo=timezone.utc)


def endpoint() -> LLMEndpoint:
    return LLMEndpoint(
        id="main",
        name="Main Relay",
        protocol="OPENAI_COMPATIBLE",
        base_url="https://relay.example.com/api/v1",
        credential_ref="llm_main_key",
    )


def task_contract(contract_id: str = "research") -> TaskContract:
    return TaskContract(
        id=contract_id,
        version="1.0",
        purpose="collect evidence",
        required_capabilities=["workspace.read"],
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        timeout_seconds=60,
        retry_policy=None,
    )


def research_task(task_id: str = "task-1") -> ResearchTask:
    return ResearchTask(
        id=ID("6f8f56a0-5c2a-4b3e-9f1d-2c7a4e8b6d90"),
        run_id=ID("a1b2c3d4-0000-4000-8000-000000000001"),
        phase_run_id=ID("a1b2c3d4-0000-4000-8000-000000000002"),
        contract_id="research",
        assigned_agent_id="agent-1",
        status="CREATED",
        idempotency_key="idem-1",
    )


def role_definition() -> RoleDefinition:
    return RoleDefinition(
        id="researcher",
        role_type="researcher",
        category=RoleCategory.DISCOVERY,
        activation_default=ActivationPolicy.ALWAYS,
        requested_capabilities=["workspace.read"],
        workspace_policy=WorkspacePolicy.READ_ONLY,
    )


def agent_spec() -> AgentSpec:
    return AgentSpec(
        id="agent-1",
        role="researcher",
        model_binding=AgentBinding(ModelBindingMode.EXPLICIT_MODEL, "model-1"),
        workspace_policy=WorkspacePolicy.READ_ONLY,
        runtime_kind=BackendKind.OPENHANDS_NATIVE,
    )


def tool_provider_spec(provider_id: str = "research_mcp") -> ToolProviderSpec:
    return ToolProviderSpec(
        id=provider_id,
        kind=ProviderType.NATIVE,
        trust_level=TrustLevel.VERIFIED,
        capabilities=["workspace.read"],
        effect_class=EffectClass.READ_ONLY,
    )


def tool_call_record(
    operation_key: str = "op-1",
    tool_id: str = "tool-a",
    task_id: str = "task-1",
) -> ToolCallRecord:
    return ToolCallRecord(
        task_id=task_id,
        attempt=1,
        operation_key=operation_key,
        tool_id=tool_id,
        capability="workspace.read",
        argument_digest=Digest.of_bytes(b"{}"),
        status="REQUESTED",
    )


def workspace(workspace_id: str = "workspace") -> Workspace:
    return Workspace(
        id=workspace_id,
        name="Fixture Workspace",
        trust_profile=TrustProfile.SANDBOXED_STANDARD,
    )


def execution_spec() -> ExecutionSpec:
    return ExecutionSpec(backend_kind="sandbox", command="pytest")


def budget_policy() -> BudgetPolicy:
    return BudgetPolicy(
        id="budget",
        hard_limits={"tool_requests": 10, "wall_clock_seconds": 3600},
    )


def budget_reservation(reservation_id: str = "res-1") -> BudgetReservation:
    return BudgetReservation(
        id=reservation_id,
        scope="run:r1",
        resource_type=ResourceType.TOOL_REQUESTS,
        quantity=1,
        unit="requests",
        reserved_at=Timestamp(NOW),
    )


def usage_entry(entry_id: str = "entry-1") -> UsageLedgerEntry:
    return UsageLedgerEntry(
        entry_id=entry_id,
        resource_type=ResourceType.TOOL_REQUESTS,
        quantity=1,
        unit="requests",
        cost_status=LedgerCostStatus.KNOWN,
        estimated_cost_minor=1,
        source="contract-test",
        occurred_at=NOW,
    )


def memory_proposal(proposal_id: str = "mem-1") -> MemoryWriteProposal:
    return MemoryWriteProposal(
        id=proposal_id,
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content="verified fact",
        provenance="source:article-1",
        confidence=0.9,
    )


def event_envelope(event_id: str = "evt-1") -> EventEnvelope:
    payload: dict[str, object] = {"phase": "collect"}
    return EventEnvelope(
        event_id=event_id,
        event_type=EventType.TASK_CREATED,
        schema_version="1",
        occurred_at=Timestamp(NOW),
        actor="project:demo",
        scope="run:r1",
        payload=payload,
        payload_digest=digest_of_payload(payload),
    )


@pytest.fixture
def port_factory_scope() -> str:
    """registry 参数化标记（供测试 id 可读性）。"""
    return "fakes"
