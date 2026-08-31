"""Research OS Fake test-double 实现（adapters/fakes）。

Fake 是 test-double adapter：与真实 adapter 遵守相同 Port Contract
（tests/contracts 强制）；deterministic、可错误注入、可记录调用、
支持 close 语义；不依赖网络/API Key/Docker/OpenHands/外部服务。
"""

from __future__ import annotations

from adapters.fakes.agent_runtime import FakeAgentRuntime
from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.base import CallRecord, FakeBase
from adapters.fakes.budget_ledger import FakeBudgetLedger
from adapters.fakes.credential_resolver import FakeCredentialResolver
from adapters.fakes.endpoint_store import FakeEndpointStore
from adapters.fakes.eval_report_store import FakeEvalReportStore
from adapters.fakes.event_publisher import FakeEventPublisher
from adapters.fakes.evidence_ledger import FakeEvidenceLedger
from adapters.fakes.execution_backend import FakeExecutionBackend
from adapters.fakes.execution_job_queue import FakeExecutionJobQueue
from adapters.fakes.memory_store import FakeMemoryStore
from adapters.fakes.model_gateway import FakeModelGateway, FakeModelGatewayOptions
from adapters.fakes.policy_evaluator import FakePolicyEvaluator
from adapters.fakes.resource_catalog import FakeResourceCatalog
from adapters.fakes.retrieval_index import FakeRetrievalIndex
from adapters.fakes.telemetry_sink import FakeTelemetrySink, NullTelemetrySink
from adapters.fakes.tool_pack_store import FakeToolPackStore
from adapters.fakes.tool_provider import FakeToolProvider
from adapters.fakes.worker_registry import FakeWorkerRegistry
from adapters.fakes.workflow_engine import FakeWorkflowEngine
from adapters.fakes.workspace_backend import FakeWorkspaceBackend

__all__ = [
    "CallRecord",
    "FakeAgentRuntime",
    "FakeArtifactStore",
    "FakeBase",
    "FakeBudgetLedger",
    "FakeCredentialResolver",
    "FakeEndpointStore",
    "FakeEventPublisher",
    "FakeEvalReportStore",
    "FakeEvidenceLedger",
    "FakeExecutionBackend",
    "FakeExecutionJobQueue",
    "FakeMemoryStore",
    "FakeModelGateway",
    "FakeModelGatewayOptions",
    "FakePolicyEvaluator",
    "FakeResourceCatalog",
    "FakeRetrievalIndex",
    "FakeTelemetrySink",
    "FakeToolPackStore",
    "FakeToolProvider",
    "FakeWorkflowEngine",
    "FakeWorkerRegistry",
    "FakeWorkspaceBackend",
    "NullTelemetrySink",
]
