"""FakeAgentRuntime：会话生命周期（domain 状态机驱动，协作式取消）。"""

from __future__ import annotations

from uuid import uuid4

from adapters.fakes.base import FakeBase
from packages.application.ports.agent_runtime import (
    AgentSessionHandle,
    AgentSessionResult,
    AgentSessionSpec,
    ForkSpec,
    RuntimeEvent,
    RuntimeEventKind,
)
from packages.application.ports.errors import InvalidInputError
from packages.domain.session_state import AgentSessionState


class FakeAgentRuntime(FakeBase):
    """create/run/pause/cancel/stream_events/fork；run 结局可配置。

    advance() 为 test-only 中间态驱动器（非 AgentRuntime Protocol 方法）：
    显式沿 domain 状态机推进 INITIALIZING/WAITING_FOR_APPROVAL/PAUSED/STUCK
    等中间态，供 M6 adapter 中间态映射测试对照。
    """

    # 迁移 → runtime event 映射；无对应 kind 的迁移（INITIALIZE/APPROVAL_GRANTED/
    # APPROVAL_REJECTED/RESUME/UNSTUCK）不追加事件。
    _EVENT_ON_TRANSITION: dict[str, RuntimeEventKind] = {
        AgentSessionState.Transition.START: RuntimeEventKind.SESSION_STARTED,
        AgentSessionState.Transition.REQUEST_APPROVAL: RuntimeEventKind.APPROVAL_REQUESTED,
        AgentSessionState.Transition.PAUSE: RuntimeEventKind.SESSION_PAUSED,
        AgentSessionState.Transition.STUCK: RuntimeEventKind.SESSION_STUCK,
    }

    def __init__(
        self,
        *,
        outcome: str = AgentSessionState.State.SUCCEEDED,
        structured_output: dict[str, object] | None = None,
        observed_model_identifiers: tuple[str, ...] = (),
    ) -> None:
        """受控 Fake 会话结局；structured_output 注入会话结果（M13-R1 demo）。

        默认 None → 会话结果无结构化输出（register 门禁如实拒绝，
        与既有语义一致）；控制面 demo 装配显式注入可满足验收标准的输出，
        并在 UI 披露"受控 Fake Runtime"。

        `observed_model_identifiers`（GOAL-010 EC-04）：受控执行体**不发起模型调用**，
        所以默认**空** = 没有观测（读面如实点名缺项）。显式传入只用于驱动「有观测」
        这条链路的判据——它描述的是 provider 侧报告过的 model 名，不是请求里那个 id。
        """
        super().__init__("agent_runtime")
        self._specs: dict[str, AgentSessionSpec] = {}
        self._states: dict[str, str] = {}
        self._events: dict[str, list[RuntimeEvent]] = {}
        self._cancel_requested: set[str] = set()
        self._outcome = outcome
        self._structured_output = dict(structured_output or {})
        self._observed_model_identifiers = tuple(observed_model_identifiers)

    def create_session(self, spec: AgentSessionSpec) -> AgentSessionHandle:
        self._enter("create_session", spec.task_id.value)
        session_id = str(uuid4())
        self._specs[session_id] = spec
        self._states[session_id] = AgentSessionState.State.CREATED
        self._events[session_id] = [RuntimeEvent(session_id, RuntimeEventKind.SESSION_CREATED)]
        self._record("create_session", spec.task_id.value, result=session_id)
        return AgentSessionHandle(session_id)

    def _require_session(self, method: str, session_id: str) -> None:
        if session_id not in self._states:
            self._record(method, session_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown session: {session_id}")

    def _transition(self, session_id: str, event: str) -> None:
        current = self._states[session_id]
        self._states[session_id] = AgentSessionState.transition(current, event)

    def advance(self, session_id: str, transition: str) -> str:
        """沿 domain 状态机推进一个迁移，返回新状态；非法迁移抛领域错误。

        仅用于测试驱动中间态；不改变 Port 契约签名。
        """
        self._require_session("advance", session_id)
        current = self._states[session_id]
        next_state = AgentSessionState.transition(current, transition)
        self._states[session_id] = next_state
        kind = self._EVENT_ON_TRANSITION.get(transition)
        if kind is not None:
            self._events[session_id].append(RuntimeEvent(session_id, kind))
        self._record("advance", f"{session_id}/{transition}", result=next_state)
        return next_state

    def run(self, session_id: str) -> AgentSessionResult:
        self._enter("run", session_id)
        self._require_session("run", session_id)
        if self._states[session_id] in AgentSessionState.terminal():
            # 终端状态为最终：重复 run 返回同一结果，不追加事件（事件流单调）。
            terminal = self._states[session_id]
            self._record("run", session_id, result=terminal)
            return AgentSessionResult(
                session_id=session_id,
                status=terminal,
                structured_output=dict(self._structured_output) if terminal == "SUCCEEDED" else {},
                observed_model_identifiers=self._observed_model_identifiers,
            )
        if session_id in self._cancel_requested:
            return self._finish(session_id, AgentSessionState.State.CANCELLED)
        if self._states[session_id] == AgentSessionState.State.CREATED:
            self._transition(session_id, AgentSessionState.Transition.INITIALIZE)
            self._transition(session_id, AgentSessionState.Transition.START)
            self._events[session_id].append(
                RuntimeEvent(session_id, RuntimeEventKind.SESSION_STARTED)
            )
        return self._finish(session_id, self._outcome)

    def _finish(self, session_id: str, terminal: str) -> AgentSessionResult:
        if self._states[session_id] != terminal:
            self._states[session_id] = terminal
        kind = {
            AgentSessionState.State.SUCCEEDED: RuntimeEventKind.SESSION_SUCCEEDED,
            AgentSessionState.State.FAILED: RuntimeEventKind.SESSION_FAILED,
            AgentSessionState.State.CANCELLED: RuntimeEventKind.SESSION_CANCELLED,
        }[terminal]
        self._events[session_id].append(RuntimeEvent(session_id, kind))
        self._record("run", session_id, result=terminal)
        return AgentSessionResult(
            session_id=session_id,
            status=terminal,
            structured_output=dict(self._structured_output) if terminal == "SUCCEEDED" else {},
            observed_model_identifiers=self._observed_model_identifiers,
        )

    def pause(self, session_id: str) -> None:
        self._enter("pause", session_id)
        self._require_session("pause", session_id)
        if self._states[session_id] == AgentSessionState.State.RUNNING:
            self._transition(session_id, AgentSessionState.Transition.PAUSE)
            self._events[session_id].append(
                RuntimeEvent(session_id, RuntimeEventKind.SESSION_PAUSED)
            )
        self._record("pause", session_id)

    def cancel(self, session_id: str) -> None:
        self._enter("cancel", session_id)
        self._require_session("cancel", session_id)
        self._cancel_requested.add(session_id)
        self._record("cancel", session_id)

    def stream_events(self, session_id: str) -> tuple[RuntimeEvent, ...]:
        self._enter("stream_events", session_id)
        self._require_session("stream_events", session_id)
        self._record("stream_events", session_id)
        return tuple(self._events[session_id])

    def fork(self, session_id: str, spec: ForkSpec) -> AgentSessionHandle:
        self._enter("fork", session_id)
        self._require_session("fork", session_id)
        forked = AgentSessionHandle(str(uuid4()), AgentSessionState.State.CREATED)
        self._states[forked.session_id] = AgentSessionState.State.CREATED
        self._events[forked.session_id] = [
            RuntimeEvent(forked.session_id, RuntimeEventKind.SESSION_CREATED)
        ]
        # ForkSpec override 投影到新会话 spec（与真实 adapter 对齐，M6 复审 F-4）
        source = self._specs[session_id]
        if spec.tool_set_override is not None and spec.manifest_revision_ref is None:
            # EC-05：有效 Tool Set 冻结——改写必须显式声明 Manifest Revision（与真实
            # adapter 的 `spec_with_overrides` 同一条契约，两个实现一起被判）。
            raise InvalidInputError(
                "fork tool_set_override requires ForkSpec.manifest_revision_ref:"
                " the effective tool set is frozen and may only change under an"
                " explicit manifest revision"
            )
        if spec.tool_set_override is not None or spec.manifest_revision_ref is not None:
            self._specs[forked.session_id] = AgentSessionSpec(
                task_id=source.task_id,
                task_contract=source.task_contract,
                role=source.role,
                agent=source.agent,
                frozen_tool_set=(
                    tuple(spec.tool_set_override)
                    if spec.tool_set_override is not None
                    else source.frozen_tool_set
                ),
                workspace_lease=source.workspace_lease,
                context_snapshot=source.context_snapshot,
                budget_reservation=source.budget_reservation,
                manifest_ref=spec.manifest_revision_ref or source.manifest_ref,
            )
        else:
            self._specs[forked.session_id] = source
        self._record("fork", session_id, result=forked.session_id)
        return forked
