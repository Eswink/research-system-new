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
from packages.application.ports.agent_store import AgentStore
from packages.application.ports.approval_store import ApprovalRecord, ApprovalStore
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.budget_ledger import BudgetLedger, LedgerSnapshot
from packages.application.ports.catalog_override_store import CatalogOverrideStore
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
from packages.application.ports.eval_report_store import (
    EvalReportIndexEntry,
    EvalReportQuery,
    EvalReportQueryPage,
    EvalReportStore,
    StoredEvalReport,
)
from packages.application.ports.event_publisher import EventPublisher
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.ports.execution_backend import ExecutionBackend
from packages.application.ports.execution_job_queue import (
    ExecutionJobOutcome,
    ExecutionJobQueue,
)
from packages.application.ports.library_store import LibraryStore
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
from packages.application.ports.model_store import ModelStore
from packages.application.ports.policy_evaluator import (
    PolicyEvaluation,
    PolicyEvaluator,
    PolicyRequest,
)
from packages.application.ports.pricing_snapshot_store import PricingSnapshotStore
from packages.application.ports.project_settings_store import ProjectSettingsStore
from packages.application.ports.project_store import ProjectStore
from packages.application.ports.protocol_draft_store import (
    DraftQuery,
    DraftRevisionRef,
    DraftSaveInput,
    DraftSaveResult,
    DraftStoreConflictError,
    DraftStoreNotFoundError,
    DraftTemplate,
    DraftValidationIssue,
    DraftValidationResult,
    ProtocolDraftRecord,
    ProtocolDraftRevision,
    ProtocolDraftStore,
)
from packages.application.ports.resource_catalog import (
    CatalogSnapshot,
    PreflightContext,
    ProjectSettings,
    ResourceCatalog,
)
from packages.application.ports.retrieval_index import IndexEntry, IndexHit, RetrievalIndex
from packages.application.ports.run_projection import RunProjection
from packages.application.ports.run_store import RunStore
from packages.application.ports.telemetry_sink import NullTelemetrySink, TelemetrySink
from packages.application.ports.tool_pack_store import ToolPackRecord, ToolPackStore
from packages.application.ports.tool_provider import ToolProvider
from packages.application.ports.worker_registry import WorkerRegistry
from packages.application.ports.workflow_engine import TaskCompletion, TaskLease, WorkflowEngine
from packages.application.ports.workspace_backend import WorkspaceBackend

__all__ = [
    "AgentRuntime",
    "AgentSessionHandle",
    "AgentSessionResult",
    "AgentSessionSpec",
    "AgentStore",
    "ApprovalRecord",
    "ApprovalStore",
    "ArtifactStore",
    "BudgetLedger",
    "CatalogOverrideStore",
    "CatalogSnapshot",
    "CompletionRequest",
    "CompletionResult",
    "CredentialResolver",
    "EndpointStore",
    "EvalReportIndexEntry",
    "EvalReportQuery",
    "EvalReportQueryPage",
    "EvalReportStore",
    "EventPublisher",
    "StoredEvalReport",
    "EvidenceLedger",
    "ExecutionBackend",
    "ExecutionJobOutcome",
    "ExecutionJobQueue",
    "ForkSpec",
    "InvalidInputError",
    "IndexEntry",
    "IndexHit",
    "LedgerSnapshot",
    "MemoryStore",
    "ModelGateway",
    "ModelsListResult",
    "ModelStore",
    "PermanentPortError",
    "PolicyEvaluation",
    "PolicyEvaluator",
    "PolicyRequest",
    "ProjectSettingsStore",
    "LibraryStore",
    "ProjectStore",
    "ProtocolDraftStore",
    "ProtocolDraftRecord",
    "ProtocolDraftRevision",
    "DraftQuery",
    "DraftSaveInput",
    "DraftSaveResult",
    "DraftRevisionRef",
    "DraftTemplate",
    "DraftValidationIssue",
    "DraftValidationResult",
    "DraftStoreConflictError",
    "DraftStoreNotFoundError",
    "PricingSnapshotStore",
    "PortCancelledError",
    "PortError",
    "PortTimeoutError",
    "PreflightContext",
    "ProjectSettings",
    "ResourceCatalog",
    "RetrievalIndex",
    "RunProjection",
    "RunStore",
    "RuntimeEvent",
    "RuntimeEventKind",
    "SecretValue",
    "TaskCompletion",
    "TaskLease",
    "TelemetrySink",
    "NullTelemetrySink",
    "ToolCallDraft",
    "ToolPackRecord",
    "ToolPackStore",
    "ToolProvider",
    "TransientPortError",
    "WorkflowEngine",
    "WorkerRegistry",
    "WorkspaceBackend",
    "capability_assertion_probed",
    "failure_category_of_http_status",
]
