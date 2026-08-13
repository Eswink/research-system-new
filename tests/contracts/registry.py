"""Port 实现注册表：contract suite 的单一事实源。

M6 起真实 adapter（OpenHandsRuntimeAdapter）与 Fake 共享同一套 contract
suite：Fake 保持无参工厂语义；真实 adapter 经模块级工厂注入确定性依赖
（TestLLM 脚本化 LLM + 隔离临时目录，无网络/无真实凭据）。
"""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from pathlib import Path

from openhands.sdk.llm import Message, TextContent
from openhands.sdk.testing import TestLLM
from openhands.sdk.workspace.local import LocalWorkspace

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
from adapters.openhands.runtime_adapter import OpenHandsRuntimeAdapter
from adapters.openhands.session_types import AdapterDependencies

Factory = Callable[[], object]

# 真实 adapter 的确定性装配（contract 级共享；测试进程退出自动清理）
_CONTRACT_WORKSPACE = Path(tempfile.mkdtemp(prefix="contract-openhands-ws-"))
_CONTRACT_PERSIST = tempfile.TemporaryDirectory(prefix="contract-openhands-persist-")


def _openhands_runtime_factory() -> OpenHandsRuntimeAdapter:
    """无参工厂：TestLLM 脚本化响应 + Fake 依赖 + 隔离 workspace。"""
    llm = TestLLM.from_messages([
        Message(role="assistant", content=[TextContent(text="Done.")]),
        Message(role="assistant", content=[TextContent(text="All set.")]),
    ])
    deps = AdapterDependencies(
        credential_resolver=FakeCredentialResolver({"LLM_KEY": "sk-contract"}),
        policy_evaluator=FakePolicyEvaluator(),
        build_llm=lambda spec: llm,
        build_workspace=lambda lease, session_id: LocalWorkspace(
            working_dir=str(_CONTRACT_WORKSPACE)
        ),
        persistence_dir=_CONTRACT_PERSIST.name,
    )
    return OpenHandsRuntimeAdapter(deps)


PORT_IMPLEMENTATIONS: dict[str, list[Factory]] = {
    "agent_runtime": [FakeAgentRuntime, _openhands_runtime_factory],
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
