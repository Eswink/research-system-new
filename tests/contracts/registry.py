"""Port 实现注册表：contract suite 的单一事实源。

M6/M7 真实 adapter 落地后在此注册工厂，同一套 contract suite 自动复用
（无需修改 suite 文件）。当前注册全部 Fake 实现。
"""

from __future__ import annotations

from collections.abc import Callable

from adapters.fakes import (
    FakeAgentRuntime,
    FakeArtifactStore,
    FakeBudgetLedger,
    FakeCredentialResolver,
    FakeEndpointStore,
    FakeEventPublisher,
    FakeExecutionBackend,
    FakeMemoryStore,
    FakeModelGateway,
    FakePolicyEvaluator,
    FakeResourceCatalog,
    FakeToolProvider,
    FakeWorkflowEngine,
    FakeWorkspaceBackend,
)

Factory = Callable[[], object]

PORT_IMPLEMENTATIONS: dict[str, list[Factory]] = {
    "agent_runtime": [FakeAgentRuntime],
    "workflow_engine": [FakeWorkflowEngine],
    "model_gateway": [FakeModelGateway],
    "tool_provider": [FakeToolProvider],
    "workspace_backend": [FakeWorkspaceBackend],
    "execution_backend": [FakeExecutionBackend],
    "artifact_store": [FakeArtifactStore],
    "event_publisher": [FakeEventPublisher],
    "policy_evaluator": [FakePolicyEvaluator],
    "credential_resolver": [FakeCredentialResolver],
    "memory_store": [FakeMemoryStore],
    "budget_ledger": [FakeBudgetLedger],
    "endpoint_store": [FakeEndpointStore],
    "resource_catalog": [FakeResourceCatalog],
}
