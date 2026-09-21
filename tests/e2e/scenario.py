"""M7 E2E 共享 wiring：StructuredOutputAgentRuntime + M7Harness。

CI 全程离线：SqliteWorkflowEngine(:memory:) + FakeAgentRuntime + FakeBudgetLedger；
不依赖真实 OpenHands/LLM/网络/凭据（AGENTS.md §11）。
"""

from __future__ import annotations

from pathlib import Path

from adapters.contracts.protocol_loaders import load_protocol
from adapters.fakes.agent_runtime import FakeAgentRuntime
from adapters.fakes.budget_ledger import FakeBudgetLedger
from adapters.fakes.evidence_ledger import FakeEvidenceLedger
from adapters.sqlite.artifact_store import SqliteArtifactStore
from adapters.sqlite.db import connect
from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.agent_runtime import (
    AgentSessionResult,
    RuntimeEvent,
    RuntimeEventKind,
)
from packages.application.run_orchestration import (
    OrchestrationDependencies,
    RunOrchestrationService,
)
from packages.domain.protocols import ProtocolDefinition
from packages.domain.session_state import AgentSessionState

PROTOCOL_PATH = "examples/protocols/sort_analysis_v1.yaml"


def m7_protocol() -> ProtocolDefinition:
    return load_protocol(PROTOCOL_PATH)


class StructuredOutputAgentRuntime(FakeAgentRuntime):
    """FakeAgentRuntime 的测试专用子类：run 产出结构化输出。

    不改动既有 Fake 契约（默认行为完全一致）。支持两种输出注入：
    - structured_output：全部会话共用；
    - outputs_by_contract：按 TaskContract.id 区分（多角色场景）。
    两者同时提供时 outputs_by_contract 优先。
    """

    def __init__(
        self,
        *,
        outcome: str = AgentSessionState.State.SUCCEEDED,
        structured_output: dict[str, object] | None = None,
        outputs_by_contract: dict[str, dict[str, object]] | None = None,
    ) -> None:
        super().__init__(outcome=outcome)
        self._structured_output = dict(structured_output or {})
        self._outputs_by_contract = outputs_by_contract

    def run(self, session_id: str) -> AgentSessionResult:
        self._enter("run", session_id)
        self._require_session("run", session_id)
        if self._states[session_id] in AgentSessionState.terminal():
            terminal = self._states[session_id]
            self._record("run", session_id, result=terminal)
            return AgentSessionResult(session_id=session_id, status=terminal)
        if session_id in self._cancel_requested:
            return self._finish(session_id, AgentSessionState.State.CANCELLED)
        if self._states[session_id] == AgentSessionState.State.CREATED:
            self._transition(session_id, AgentSessionState.Transition.INITIALIZE)
            self._transition(session_id, AgentSessionState.Transition.START)
            self._events[session_id].append(
                RuntimeEvent(session_id, RuntimeEventKind.SESSION_STARTED)
            )
        return self._finish_structured(session_id, self._outcome)

    def _output_for(self, session_id: str) -> dict[str, object]:
        spec = self._specs.get(session_id)
        if spec is not None and self._outputs_by_contract is not None:
            contract_id = spec.task_contract.id
            if contract_id in self._outputs_by_contract:
                return dict(self._outputs_by_contract[contract_id])
        return dict(self._structured_output or {})

    def _finish_structured(self, session_id: str, terminal: str) -> AgentSessionResult:
        kind = {
            AgentSessionState.State.SUCCEEDED: RuntimeEventKind.SESSION_SUCCEEDED,
            AgentSessionState.State.FAILED: RuntimeEventKind.SESSION_FAILED,
            AgentSessionState.State.CANCELLED: RuntimeEventKind.SESSION_CANCELLED,
        }[terminal]
        self._states[session_id] = terminal
        self._events[session_id].append(RuntimeEvent(session_id, kind))
        self._record("run", session_id, result=terminal)
        return AgentSessionResult(
            session_id=session_id,
            status=terminal,
            structured_output=self._output_for(session_id),
        )


class M7Harness:
    """一次 E2E 场景的完整 wiring（SQLite 共享连接保证事务语义）。"""

    def __init__(
        self,
        runtime: FakeAgentRuntime | None = None,
        ledger: FakeEvidenceLedger | None = None,
    ) -> None:
        self.connection = connect(":memory:")
        self.engine = SqliteWorkflowEngine(connection=self.connection, lease_ttl_seconds=60)
        self.artifacts = SqliteArtifactStore(connection=self.connection)
        # GOAL-010 EC-02：协议**声明**的输入制品必须真的在库里（生产组合根装配时
        # 做同一件事）；`EVIDENCE_COVERAGE` 收紧后只认非模型自述的来源。
        seed_run_inputs(self.artifacts)
        self.events = SqliteOutboxEventPublisher(connection=self.connection)
        self.budget = FakeBudgetLedger()
        self.ledger = ledger
        self.service = RunOrchestrationService(
            OrchestrationDependencies(
                runtime=runtime or StructuredOutputAgentRuntime(),
                workflow=self.engine,
                artifacts=self.artifacts,
                events=self.events,
                budget=self.budget,
                ledger=ledger,
            )
        )

    def close(self) -> None:
        self.engine.close()
        self.artifacts.close()
        self.events.close()


def blob_root() -> Path:
    return Path(".") / ".m7-blobs"


def seed_run_inputs(store: object) -> None:
    """测试侧种入协议**声明**的输入制品（等价于生产组合根装配时的动作）。

    GOAL-010 EC-02 之后，`EVIDENCE_COVERAGE` 只认非模型自述的来源；声明了输入却
    不在库里 ⇒ 任务点名失败（`declared input artifact ... is not in the artifact store`），
    **不**降级成「没有来源也算过」。自建 harness 的测试等于在仿组合根，故须同样种入。
    """
    from services.api.demo import seed_declared_inputs

    seed_declared_inputs(store)
