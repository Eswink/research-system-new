"""OpenHandsRuntimeAdapter：AgentRuntime Port 的 OpenHands SDK 实现。

依赖方向：adapter → SDK；OpenHands 类型只存在于本包。Session 生命周期
create/run/pause/cancel/stream_events/fork 全同步语义（M5 D2）。

关键映射（M5_PORT_COMPATIBILITY_MATRIX §1）：
- cancel：SDK interrupt() 后为 PAUSED（可恢复）→ 本 adapter 显式收敛为
  domain CANCELLED（R-01；不做静默映射）。
- 状态：ConversationExecutionStatus → AgentSessionState 显式映射
  （session_types.map_status_to_domain）；SDK STUCK 收敛 FAILED。
- 事件：SDK 事件树 → RuntimeEvent（event_mapping 纯函数）；按 event id
  去重，事件缓冲单调追加；已投影终端 kind 不再重复追加（复审 F-5）。
- run() 契约：AgentSessionResult.status 必须为 domain 终态（Port 强制），
  因此 run() 驱动 SDK 直至终态或取消信号。
- 策略：PolicyEnforcingAgent 在工具执行点强制 PolicyEvaluator（复审 F-1）；
  execute_tool 直通面经 PolicyWrappedToolExecutor 门禁。
- usage：run() 终态后归一化 ConversationStats 写入 BudgetLedger（signal
  语义，记账失败不阻断结果；复审 F-2）。
- fork：ForkSpec.model_override / tool_set_override 经注入的
  build_llm_for_fork 重建 Agent 后 fork（复审 F-4）。
- 会话装配与 usage 记录委托 session_builder.SessionBuilder（行数约束）。
"""

from __future__ import annotations

import threading
from typing import Any
from uuid import uuid4

from openhands.sdk.conversation.state import ConversationExecutionStatus

from adapters.openhands.error_mapping import (
    map_conversation_run_error,
    map_unexpected_exception,
)
from adapters.openhands.event_mapping import map_event
from adapters.openhands.policy_enforcing_agent import PolicyEnforcingAgent
from adapters.openhands.policy_wrapper import PolicyWrappedToolExecutor
from adapters.openhands.session_builder import SessionBuilder
from adapters.openhands.session_types import (
    _SDK_TERMINAL_TO_DOMAIN,
    _TERMINAL_EVENT_KIND,
    AdapterDependencies,
    _SessionEntry,
)
from packages.application.ports.agent_runtime import (
    AgentSessionHandle,
    AgentSessionResult,
    AgentSessionSpec,
    ForkSpec,
    RuntimeEvent,
    RuntimeEventKind,
)
from packages.application.ports.errors import (
    InvalidInputError,
    PermanentPortError,
    PortCancelledError,
    PortError,
)
from packages.domain.enums import FailureCategory
from packages.domain.session_state import AgentSessionState


class OpenHandsRuntimeAdapter:
    """AgentRuntime Port 实现（OpenHands Software Agent SDK）。"""

    def __init__(self, deps: AdapterDependencies) -> None:
        self._builder = SessionBuilder(deps)
        self._lock = threading.Lock()
        self._sessions: dict[str, _SessionEntry] = {}
        self._closed = False
        self.calls: list[dict[str, object]] = []

    # ------------------------------------------------------------------ #
    # AgentRuntime Protocol
    # ------------------------------------------------------------------ #

    def create_session(self, spec: AgentSessionSpec) -> AgentSessionHandle:
        self._check_open("create_session")
        self._record("create_session", spec.task_id.value)
        session_id = str(uuid4())
        try:
            entry = self._builder.build_session(session_id, spec)
        except PortError:
            raise
        except Exception as exc:  # noqa: BLE001  SDK 装配失败 → 收敛 PortError
            raise map_unexpected_exception(exc) from exc
        with self._lock:
            self._sessions[session_id] = entry
        return AgentSessionHandle(session_id)

    def run(self, session_id: str) -> AgentSessionResult:
        self._check_open("run")
        self._record("run", session_id)
        entry = self._require_session("run", session_id)
        if entry.terminal_result is not None:
            return entry.terminal_result
        try:
            terminal = self._drive_until_terminal(entry)
        except PortCancelledError:
            terminal = AgentSessionState.State.CANCELLED
        except PortError:
            raise
        except Exception as exc:  # noqa: BLE001
            # SDK 双通道失败：先投影 ConversationErrorEvent → SESSION_FAILED，
            # 再按事件分类/原始异常类型归一化为 PortError（复审 F-9）
            self._sync_events(entry)
            raise map_conversation_run_error(exc, self._builder.find_error_event(entry)) from exc
        if entry.cancel_requested:
            terminal = AgentSessionState.State.CANCELLED
        self._sync_events(entry)
        result = self._finish(entry, terminal)
        self._builder.record_usage(
            entry, lambda sid: self._record("usage", sid, error="usage_report_failed")
        )
        return result

    def pause(self, session_id: str) -> None:
        self._check_open("pause")
        entry = self._require_session("pause", session_id)
        if entry.status == AgentSessionState.State.RUNNING:
            entry.conversation.pause()
            self._sync_events(entry)

    def cancel(self, session_id: str) -> None:
        self._check_open("cancel")
        entry = self._require_session("cancel", session_id)
        if entry.terminal_result is not None:
            return  # 终端后 cancel 幂等 no-op
        entry.cancel_requested = True
        try:
            entry.conversation.interrupt()
        except PortError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise map_unexpected_exception(exc) from exc
        self._sync_events(entry)

    def stream_events(self, session_id: str) -> tuple[RuntimeEvent, ...]:
        self._check_open("stream_events")
        entry = self._require_session("stream_events", session_id)
        self._sync_events(entry)
        with self._lock:
            return tuple(entry.events)

    def fork(self, session_id: str, spec: ForkSpec) -> AgentSessionHandle:
        self._check_open("fork")
        entry = self._require_session("fork", session_id)
        new_id = str(uuid4())
        try:
            forked = self._builder.fork_conversation(entry, spec, new_id)
        except PortError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise map_unexpected_exception(exc) from exc
        fork_entry = _SessionEntry(
            session_id=new_id,
            spec=self._builder.spec_with_overrides(entry.spec, spec),
            conversation=forked,
            conversation_id=str(forked.id),
            events=[RuntimeEvent(new_id, RuntimeEventKind.SESSION_CREATED)],
        )
        with self._lock:
            self._sessions[new_id] = fork_entry
        self._record("fork", session_id, new_id)
        return AgentSessionHandle(new_id)

    def close(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for entry in sessions:
            try:
                entry.conversation.close()
            except Exception:  # noqa: BLE001  cleanup 尽力而为
                pass
        self._builder.release_policy_contexts()
        self._closed = True

    # ------------------------------------------------------------------ #
    # 内部实现
    # ------------------------------------------------------------------ #

    def _drive_until_terminal(self, entry: _SessionEntry) -> str:
        """驱动 SDK run() 直至 SDK 终态、取消信号或确认等待。"""
        started = False
        while True:
            if entry.cancel_requested:
                return AgentSessionState.State.CANCELLED
            if not started and entry.status == AgentSessionState.State.CREATED:
                entry.events.append(
                    RuntimeEvent(entry.session_id, RuntimeEventKind.SESSION_STARTED)
                )
                started = True
            entry.conversation.run()
            status = entry.conversation.state.execution_status
            if status.value in _SDK_TERMINAL_TO_DOMAIN:
                return _SDK_TERMINAL_TO_DOMAIN[status.value]
            if status is ConversationExecutionStatus.WAITING_FOR_CONFIRMATION:
                return AgentSessionState.State.FAILED
            if status is ConversationExecutionStatus.PAUSED and not entry.cancel_requested:
                # 协作式 pause：pause() 已显式调用；run() 再次驱动 = resume。
                continue

    def _sync_events(self, entry: _SessionEntry) -> None:
        """把 SDK 事件树投影追加到会话事件缓冲（按 event id 去重）。"""
        with self._lock:
            for event in entry.conversation.state.events:
                event_id = str(getattr(event, "id", ""))
                if event_id and event_id in entry.seen_event_ids:
                    continue
                projected = map_event(event, entry.session_id)
                for projected_event in projected:
                    if projected_event.kind in _TERMINAL_EVENT_KIND.values():
                        entry.terminal_kinds_seen.add(projected_event.kind)
                entry.events.extend(projected)
                if event_id:
                    entry.seen_event_ids.add(event_id)
            agent = getattr(entry.conversation, "agent", None)
            if isinstance(agent, PolicyEnforcingAgent):
                entry.events.extend(agent.drain_policy_events())

    def _finish(self, entry: _SessionEntry, terminal: str) -> AgentSessionResult:
        entry.status = terminal
        kind = _TERMINAL_EVENT_KIND[terminal]
        if kind not in entry.terminal_kinds_seen:
            entry.events.append(RuntimeEvent(entry.session_id, kind))
        result = AgentSessionResult(session_id=entry.session_id, status=terminal)
        entry.terminal_result = result
        return result

    def execute_tool_gated(self, session_id: str, tool_name: str, action: Any) -> Any:
        """经 Policy Wrapper 的 direct tool execution 面（R-03 独占通道）。"""
        self._check_open("execute_tool_gated")
        entry = self._require_session("execute_tool_gated", session_id)
        wrapper = PolicyWrappedToolExecutor(
            self._builder._policy_evaluator,
            actor=entry.spec.agent.id,
            scope=session_id,
            emit=lambda event: entry.events.append(event),
        )
        observation = wrapper.execute(entry.conversation.execute_tool, tool_name, action)
        self._sync_events(entry)
        return observation

    def _require_session(self, method: str, session_id: str) -> _SessionEntry:
        with self._lock:
            entry = self._sessions.get(session_id)
        if entry is None:
            self._record(method, session_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown session: {session_id}")
        return entry

    def _check_open(self, method: str) -> None:
        if self._closed:
            self._record(method, error="PermanentPortError")
            raise PermanentPortError(
                "adapter is closed",
                failure_category=FailureCategory.CONFIGURATION,
            )

    def _record(
        self,
        method: str,
        session_id: str = "",
        result: object = None,
        error: str = "",
    ) -> None:
        self.calls.append({
            "method": method,
            "session_id": session_id,
            "result": result,
            "error": error,
        })


__all__ = ["OpenHandsRuntimeAdapter"]
