"""通用 Port Contract suite：对注册表内每个实现强制共同语义。

覆盖：正常/invalid input/失败注入/close 语义/call recording/replay/serialization。
"""

from __future__ import annotations

import importlib
import pathlib
from collections.abc import Callable
from typing import Any

import pytest

from adapters.fakes import (
    FakeAgentRuntime,
    FakeArtifactStore,
    FakeBudgetLedger,
    FakeCredentialResolver,
    FakeEndpointStore,
    FakeEvalReportStore,
    FakeEventPublisher,
    FakeEvidenceLedger,
    FakeExecutionBackend,
    FakeMemoryStore,
    FakeModelGateway,
    FakePolicyEvaluator,
    FakeResourceCatalog,
    FakeRetrievalIndex,
    FakeToolPackStore,
    FakeToolProvider,
    FakeWorkerRegistry,
    FakeWorkflowEngine,
    FakeWorkspaceBackend,
)
from adapters.fakes.base import FakeBase
from packages.application.ports.agent_runtime import AgentSessionSpec
from packages.application.ports.credential_resolver import SecretValue
from packages.application.ports.errors import (
    InvalidInputError,
    PermanentPortError,
    PortError,
    PortTimeoutError,
    TransientPortError,
)
from packages.application.ports.policy_evaluator import PolicyRequest
from packages.domain.enums import FailureCategory
from packages.domain.serialization import canonical_json_bytes
from tests.contracts.fixtures import (
    agent_spec,
    budget_reservation,
    endpoint,
    event_envelope,
    execution_spec,
    research_task,
    role_definition,
    task_contract,
    tool_call_record,
    tool_provider_spec,
    usage_entry,
    workspace,
)
from tests.contracts.registry import PORT_IMPLEMENTATIONS

PORT_NAMES = tuple(PORT_IMPLEMENTATIONS)

_FAKE_FACTORIES: dict[str, Callable[[], FakeBase]] = {
    "agent_runtime": FakeAgentRuntime,
    "workflow_engine": FakeWorkflowEngine,
    "model_gateway": FakeModelGateway,
    "tool_provider": FakeToolProvider,
    "workspace_backend": FakeWorkspaceBackend,
    "execution_backend": FakeExecutionBackend,
    "artifact_store": FakeArtifactStore,
    "event_publisher": FakeEventPublisher,
    "eval_report_store": FakeEvalReportStore,
    "evidence_ledger": FakeEvidenceLedger,
    "retrieval_index": FakeRetrievalIndex,
    "policy_evaluator": FakePolicyEvaluator,
    "credential_resolver": FakeCredentialResolver,
    "memory_store": FakeMemoryStore,
    "budget_ledger": FakeBudgetLedger,
    "endpoint_store": FakeEndpointStore,
    "resource_catalog": FakeResourceCatalog,
    "tool_pack_store": FakeToolPackStore,
    "worker_registry": FakeWorkerRegistry,
}

_PORT_PROTOCOL_NAMES = {
    "agent_runtime": "AgentRuntime",
    "workflow_engine": "WorkflowEngine",
    "model_gateway": "ModelGateway",
    "tool_provider": "ToolProvider",
    "workspace_backend": "WorkspaceBackend",
    "execution_backend": "ExecutionBackend",
    "artifact_store": "ArtifactStore",
    "event_publisher": "EventPublisher",
    "eval_report_store": "EvalReportStore",
    "evidence_ledger": "EvidenceLedger",
    "retrieval_index": "RetrievalIndex",
    "policy_evaluator": "PolicyEvaluator",
    "credential_resolver": "CredentialResolver",
    "memory_store": "MemoryStore",
    "budget_ledger": "BudgetLedger",
    "endpoint_store": "EndpointStore",
    "resource_catalog": "ResourceCatalog",
    "tool_pack_store": "ToolPackStore",
    "telemetry_sink": "TelemetrySink",
    "worker_registry": "WorkerRegistry",
}

_PORT_PROBES: dict[str, Callable[[Any], object]] = {
    "agent_runtime": lambda fake: fake.stream_events("missing-session"),
    "workflow_engine": lambda fake: fake.acquire_lease("missing-task"),
    "model_gateway": lambda fake: fake.list_models(endpoint(), SecretValue("x")),
    "tool_provider": lambda fake: fake.execute(
        tool_provider_spec(), tool_call_record(operation_key="probe")
    ),
    "workspace_backend": lambda fake: fake.acquire_lease(workspace(), "session-probe"),
    "execution_backend": lambda fake: fake.execute(execution_spec()),
    "artifact_store": lambda fake: fake.get("missing-artifact"),
    "event_publisher": lambda fake: fake.publish(event_envelope(event_id="probe")),
    "eval_report_store": lambda fake: fake.get("missing-digest"),
    "evidence_ledger": lambda fake: fake.get_claim("missing-claim"),
    "retrieval_index": lambda fake: fake.search("probe"),
    "policy_evaluator": lambda fake: fake.evaluate(PolicyRequest(actor="probe", capability="x")),
    "credential_resolver": lambda fake: fake.resolve("missing-ref"),
    "memory_store": lambda fake: fake.get("missing-memory"),
    "budget_ledger": lambda fake: fake.snapshot(),
    "endpoint_store": lambda fake: fake.get_endpoint("missing-endpoint"),
    "resource_catalog": lambda fake: fake.snapshot(),
    "tool_pack_store": lambda fake: fake.get("missing-pack"),
    "worker_registry": lambda fake: fake.get("missing-worker"),
}

_PORT_PROBE_METHODS: dict[str, str] = {
    "agent_runtime": "stream_events",
    "workflow_engine": "acquire_lease",
    "model_gateway": "list_models",
    "tool_provider": "execute",
    "workspace_backend": "acquire_lease",
    "execution_backend": "execute",
    "artifact_store": "get",
    "event_publisher": "publish",
    "eval_report_store": "get",
    "evidence_ledger": "get_claim",
    "retrieval_index": "search",
    "policy_evaluator": "evaluate",
    "credential_resolver": "resolve",
    "memory_store": "get",
    "budget_ledger": "snapshot",
    "endpoint_store": "get_endpoint",
    "resource_catalog": "snapshot",
    "tool_pack_store": "get",
    "worker_registry": "get",
}


@pytest.mark.parametrize("port", PORT_NAMES)
def test_port_implementations_are_registered(port: str) -> None:
    factories = PORT_IMPLEMENTATIONS[port]
    assert factories, f"port {port} must register at least one implementation"
    for factory in factories:
        instance = factory()
        assert hasattr(instance, "calls"), "implementation must record calls"


@pytest.mark.parametrize("port", PORT_NAMES)
def test_interface_compatibility(port: str) -> None:
    """实现必须满足 Port Protocol（runtime_checkable）。"""
    factory = PORT_IMPLEMENTATIONS[port][0]
    instance = factory()
    ports_module = importlib.import_module("packages.application.ports")
    protocol = getattr(ports_module, _PORT_PROTOCOL_NAMES[port])
    assert isinstance(instance, protocol), f"{port} must satisfy {protocol!r}"


@pytest.mark.parametrize("port", PORT_NAMES)
def test_close_then_calls_are_rejected(port: str) -> None:
    """close 后调用必须抛 PermanentPortError(resource cleanup 语义)。"""
    if port not in _FAKE_FACTORIES:
        pytest.skip("dedicated fail-open contract suite")
    instance = _FAKE_FACTORIES[port]()
    instance.close()
    with pytest.raises(PermanentPortError):
        _PORT_PROBES[port](instance)


@pytest.mark.parametrize("port", PORT_NAMES)
def test_failure_injection_records_and_raises(port: str) -> None:
    """脚本注入的 PortError 必须被抛出并记录到 call log。"""
    if port not in _FAKE_FACTORIES:
        pytest.skip("dedicated fail-open contract suite")
    instance = _FAKE_FACTORIES[port]()
    probe = _PORT_PROBES[port]
    method = _PORT_PROBE_METHODS[port]
    injected = TransientPortError(
        "injected transient",
        failure_category=FailureCategory.EXECUTION_FAILURE,
    )
    instance.set_script(method, [injected])
    with pytest.raises(TransientPortError):
        probe(instance)
    assert instance.method_calls(method) == 1
    assert instance.calls[-1].error == "TransientPortError"


def test_errors_hierarchy_semantics() -> None:
    transient = TransientPortError("boom", failure_category=FailureCategory.EXECUTION_FAILURE)
    permanent = PermanentPortError("nope", failure_category=FailureCategory.CONFIGURATION)
    timeout = PortTimeoutError("late", failure_category=FailureCategory.MODEL_TIMEOUT)
    invalid = InvalidInputError("bad input")
    assert transient.retryable is True
    assert permanent.retryable is False
    assert timeout.retryable is True
    assert invalid.retryable is False
    assert all(isinstance(e, PortError) for e in (transient, permanent, timeout, invalid))


def test_error_messages_are_redacted() -> None:
    error = TransientPortError(
        "failed with Authorization: Bearer sk-secret-token-123456",
        failure_category=FailureCategory.MODEL_AUTH,
    )
    assert "sk-secret-token-123456" not in str(error)
    assert "***REDACTED***" in str(error)


def test_serialization_boundary_roundtrip() -> None:
    """Port 输入输出类型必须支持 canonical JSON（deterministic digest 前提）。

    注：MemoryWriteProposal.confidence 为 float，domain 既有约束拒绝 float
    进入 canonical digest（packages/domain/serialization.py），
    MemoryWriteProposal 不承诺 digest 语义，故不在本清单内。
    """
    for value in (
        research_task(),
        task_contract(),
        tool_call_record(),
        execution_spec(),
        budget_reservation(),
        usage_entry(),
        event_envelope(),
    ):
        encoded = canonical_json_bytes(value)
        assert isinstance(encoded, bytes) and len(encoded) > 0


def test_secret_never_appears_in_records() -> None:
    resolver = FakeCredentialResolver({"llm_main_key": "sk-super-secret-value-999"})
    value = resolver.resolve("llm_main_key")
    assert value.value == "sk-super-secret-value-999"
    assert "sk-super-secret-value-999" not in repr(value)
    joined = "\n".join(
        f"{call.args_summary}|{call.result_summary or ''}|{call.error or ''}"
        for call in resolver.calls
    )
    assert "sk-super-secret-value-999" not in joined


def test_provider_types_do_not_leak_from_ports() -> None:
    """ports 模块不得 import provider SDK 或 adapters 实现。"""
    root = pathlib.Path(__file__).resolve().parents[2]
    ports_dir = root / "packages" / "application" / "ports"
    forbidden = ("openhands", "litellm", "lite_llm", "temporal", "openai", "anthropic", "adapters.")
    for source in ports_dir.glob("*.py"):
        text = source.read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden), f"provider type leak in {source.name}"


def test_port_interface_compatibility_matrix() -> None:
    """注册表必须覆盖全部 20 个 Port 名称（M8/M10/M15/M16 增量）。"""
    expected = {
        "agent_runtime",
        "workflow_engine",
        "model_gateway",
        "tool_provider",
        "workspace_backend",
        "execution_backend",
        "artifact_store",
        "event_publisher",
        "evidence_ledger",
        "eval_report_store",
        "retrieval_index",
        "policy_evaluator",
        "credential_resolver",
        "memory_store",
        "budget_ledger",
        "endpoint_store",
        "resource_catalog",
        "tool_pack_store",
        "telemetry_sink",
        "worker_registry",
    }
    assert set(PORT_IMPLEMENTATIONS) == expected


def test_agent_runtime_session_spec_types() -> None:
    spec = AgentSessionSpec(
        task_id=research_task().id,
        task_contract=task_contract(),
        role=role_definition(),
        agent=agent_spec(),
    )
    assert str(spec.task_id.value) == "6f8f56a0-5c2a-4b3e-9f1d-2c7a4e8b6d90"
    assert spec.frozen_tool_set == ()
