"""Research OS application-owned Ports。

所有 Port 由 Research OS 拥有（inward-owned）；adapter 实现这些接口，
不反向控制 Domain。Port 输入输出只使用 packages.domain 类型与
本包内 DTO，禁止 provider-specific 类型泄漏。
"""

from __future__ import annotations

from packages.application.ports.agent_runtime import (
    AgentRuntime,
    AgentSessionHandle,
    AgentSessionResult,
    AgentSessionSpec,
    ForkSpec,
    RuntimeEvent,
    RuntimeEventKind,
)
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.budget_ledger import BudgetLedger, LedgerSnapshot
from packages.application.ports.credential_resolver import CredentialResolver, SecretValue
from packages.application.ports.endpoint_store import EndpointStore
from packages.application.ports.errors import (
    InvalidInputError,
    PermanentPortError,
    PortCancelledError,
    PortError,
    PortTimeoutError,
    TransientPortError,
)
from packages.application.ports.event_publisher import EventPublisher
from packages.application.ports.execution_backend import ExecutionBackend
from packages.application.ports.memory_store import MemoryStore
from packages.application.ports.model_gateway import (
    CompletionRequest,
    CompletionResult,
    ModelGateway,
    ModelsListResult,
    ToolCallDraft,
    capability_assertion_probed,
    failure_category_of_http_status,
)
from packages.application.ports.policy_evaluator import (
    PolicyEvaluation,
    PolicyEvaluator,
    PolicyRequest,
)
from packages.application.ports.resource_catalog import (
    CatalogSnapshot,
    PreflightContext,
    ProjectSettings,
    ResourceCatalog,
)
from packages.application.ports.tool_provider import ToolProvider
from packages.application.ports.workflow_engine import TaskCompletion, TaskLease, WorkflowEngine
from packages.application.ports.workspace_backend import WorkspaceBackend

__all__ = [
    "AgentRuntime",
    "AgentSessionHandle",
    "AgentSessionResult",
    "AgentSessionSpec",
    "ArtifactStore",
    "BudgetLedger",
    "CatalogSnapshot",
    "CompletionRequest",
    "CompletionResult",
    "CredentialResolver",
    "EndpointStore",
    "EventPublisher",
    "ExecutionBackend",
    "ForkSpec",
    "InvalidInputError",
    "LedgerSnapshot",
    "MemoryStore",
    "ModelGateway",
    "ModelsListResult",
    "PermanentPortError",
    "PolicyEvaluation",
    "PolicyEvaluator",
    "PolicyRequest",
    "PortCancelledError",
    "PortError",
    "PortTimeoutError",
    "PreflightContext",
    "ProjectSettings",
    "ResourceCatalog",
    "RuntimeEvent",
    "RuntimeEventKind",
    "SecretValue",
    "TaskCompletion",
    "TaskLease",
    "ToolCallDraft",
    "ToolProvider",
    "TransientPortError",
    "WorkflowEngine",
    "WorkspaceBackend",
    "capability_assertion_probed",
    "failure_category_of_http_status",
]
