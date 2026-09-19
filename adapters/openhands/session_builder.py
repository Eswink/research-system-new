"""会话装配：Agent/Conversation 构建、fork override、usage 记录。

职责：把 AgentSessionSpec 装配为 OpenHands Conversation 会话（含策略门禁
Agent）；ForkSpec override 重建 LLM/工具集；run() 终态后 usage 归一化写
BudgetLedger。所有 SDK 类型只存在于本包。
"""

from __future__ import annotations

from typing import Any

from openhands.sdk.agent.agent import Agent as OpenHandsAgent
from openhands.sdk.conversation.conversation import Conversation
from openhands.sdk.event.conversation_error import ConversationErrorEvent
from openhands.sdk.tool.spec import Tool

from adapters.openhands.policy_enforcing_agent import (
    PolicyEnforcingAgent,
    register_policy_context,
)
from adapters.openhands.session_types import _SessionEntry
from adapters.openhands.usage_mapping import UsageContext, publish_usage
from packages.application.ports.agent_runtime import (
    AgentSessionSpec,
    ForkSpec,
    RuntimeEvent,
    RuntimeEventKind,
)
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.policy_evaluator import PolicyEvaluator


class SessionBuilder:
    """adapter 的会话装配面（依赖经构造注入，避免 adapter 参数爆炸）。"""

    def __init__(self, deps: Any) -> None:
        self._policy_evaluator: PolicyEvaluator = deps.policy_evaluator
        self._build_llm = deps.build_llm
        self._build_llm_for_fork = deps.build_llm_for_fork
        self._build_workspace = deps.build_workspace
        self._register_tools = deps.register_tools or (lambda spec: None)
        self._use_default_agent = deps.build_agent is None
        self._build_agent = deps.build_agent
        self._budget_ledger = deps.budget_ledger
        self._usage_reporter = deps.usage_reporter
        self._persistence_dir = deps.persistence_dir
        self._callbacks = deps.callbacks
        self._policy_context_ids: set[str] = set()

    def release_policy_contexts(self) -> None:
        from adapters.openhands.policy_enforcing_agent import unregister_policy_context

        for context_id in self._policy_context_ids:
            unregister_policy_context(context_id)
        self._policy_context_ids.clear()

    def build_session(self, session_id: str, spec: AgentSessionSpec) -> _SessionEntry:
        workspace = self._build_workspace(spec.workspace_lease, session_id)
        self._register_tools(spec.frozen_tool_set)
        llm = self._build_llm(spec)
        agent = self.assemble_agent(llm, spec, session_id)
        # SDK v1.42.0 Conversation.__new__ 工厂返回 LocalConversation，但 mypy
        # 无法解析其实例方法签名（上游类型标注缺陷）；此处用 Any 承载 SDK 对象。
        conversation: Any = Conversation(
            agent=agent,
            workspace=workspace,
            persistence_dir=self._persistence_dir,
            callbacks=self._callbacks,
        )
        conversation.send_message(spec.task_contract.purpose)
        return _SessionEntry(
            session_id=session_id,
            spec=spec,
            conversation=conversation,
            conversation_id=str(conversation.id),
            events=[RuntimeEvent(session_id, RuntimeEventKind.SESSION_CREATED)],
        )

    def assemble_agent(self, llm: Any, spec: AgentSessionSpec, session_id: str) -> Any:
        """装配带策略门禁的 Agent（evaluator 经注册表随序列化传递）。"""
        context_id = register_policy_context(self._policy_evaluator)
        self._policy_context_ids.add(context_id)
        if self._use_default_agent:
            return PolicyEnforcingAgent(
                llm=llm,
                tools=[Tool(name=name) for name in spec.frozen_tool_set],
                policy_context_id=context_id,
                policy_actor=spec.agent.id,
                policy_scope=session_id,
            )
        agent = self._build_agent(llm, list(spec.frozen_tool_set))
        if isinstance(agent, OpenHandsAgent) and not isinstance(agent, PolicyEnforcingAgent):
            tools = list(getattr(agent, "tools", None) or spec.frozen_tool_set)
            return PolicyEnforcingAgent(
                llm=llm,
                tools=tools,
                policy_context_id=context_id,
                policy_actor=spec.agent.id,
                policy_scope=session_id,
            )
        return agent

    def fork_conversation(self, entry: _SessionEntry, spec: ForkSpec, new_id: str) -> Any:
        """fork：按 override 重建 LLM/Agent（无 override 时 SDK 默认深拷贝）。"""
        if spec.model_override is None and spec.tool_set_override is None:
            return entry.conversation.fork()
        if spec.model_override is not None:
            if self._build_llm_for_fork is None:
                raise InvalidInputError(
                    "fork model_override requires AdapterDependencies.build_llm_for_fork"
                )
            llm = self._build_llm_for_fork(entry.spec, spec.model_override)
        else:
            llm = getattr(entry.conversation.agent, "llm", None)
        tool_set = (
            tuple(spec.tool_set_override)
            if spec.tool_set_override is not None
            else entry.spec.frozen_tool_set
        )
        self._register_tools(tool_set)
        agent = self.assemble_agent(llm, entry.spec, new_id)
        return entry.conversation.fork(agent=agent)

    @staticmethod
    def spec_with_overrides(spec: AgentSessionSpec, fork: ForkSpec) -> AgentSessionSpec:
        if fork.tool_set_override is None and fork.manifest_revision_ref is None:
            return spec
        return AgentSessionSpec(
            task_id=spec.task_id,
            task_contract=spec.task_contract,
            role=spec.role,
            agent=spec.agent,
            frozen_tool_set=(
                tuple(fork.tool_set_override)
                if fork.tool_set_override is not None
                else spec.frozen_tool_set
            ),
            workspace_lease=spec.workspace_lease,
            context_snapshot=spec.context_snapshot,
            budget_reservation=spec.budget_reservation,
            manifest_ref=fork.manifest_revision_ref or spec.manifest_ref,
        )

    def record_usage(self, entry: _SessionEntry, on_failure: Any) -> None:
        """run() 终态后把 SDK usage 归一化写入 BudgetLedger（signal 语义）。"""
        if self._budget_ledger is None and self._usage_reporter is None:
            return
        try:
            stats = entry.conversation.state.stats
            context = UsageContext(
                source="openhands",
                task_id=entry.spec.task_id.value,
                agent_id=entry.spec.agent.id,
                # EC-03：用量要能归因到**实际跑的那个 model**（AGENTS.md §4 同名漂移
                # 必须可见）。spec 现在携带执行目标，这个事实在 adapter 侧可见；缺目标
                # 时保持 None——不猜、不回填别的 model。
                model_id=entry.spec.model.id if entry.spec.model is not None else None,
            )
            entries = publish_usage(stats, self._budget_ledger, context)
            if self._usage_reporter is not None:
                self._usage_reporter(entries)
        except Exception:  # noqa: BLE001  记账失败不阻断 run 结果
            on_failure(entry.session_id)

    @staticmethod
    def find_error_event(entry: _SessionEntry) -> Any:
        """从 SDK 事件树取最后一个 ConversationErrorEvent（双通道映射用）。"""
        last_error: Any = None
        for event in entry.conversation.state.events:
            if isinstance(event, ConversationErrorEvent):
                last_error = event
        return last_error


__all__ = ["SessionBuilder"]
