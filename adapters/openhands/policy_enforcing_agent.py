"""PolicyEnforcingAgent：SDK agent loop 工具执行点的 Research OS 策略门禁。

背景（R-03 / M6 DoD AC-04）：SDK v1.42.0 无进程内 public 工具级策略注入面
（hook 仅 command/agent 类型，confirmation policy 只支持整体挂起且
Conversation.execute_tool 后门可绕过，官方文档明确警告）。唯一能同时覆盖
agent loop 与 direct execution 的执行点是 Agent._execute_action_event（单
下划线方法）。本模块是该 internal symbol 的必要使用边界：SDK 周更可能调整
内部签名，Upgrade Gate 必须重跑 contract suite 与本模块测试。

- DENY：返回 AgentErrorEvent 拒绝反馈（agent loop 可转向），不抛 SDK 异常；
- REQUIRE_APPROVAL：队列 APPROVAL_REQUESTED RuntimeEvent（M6 无审批通道，
  由 adapter 冲刷到会话事件流）并返回拒绝反馈；
- ALLOW / ALLOW_WITH_CONSTRAINTS：委托 SDK 原执行路径。

策略上下文序列化：SDK fork() 通过 model_validate 重建 agent（fork 源码），
非 pydantic 字段的依赖会丢失。因此 evaluator 经模块级注册表按 context_id
查找（简单字符串字段随序列化保留）；actor/scope 为普通字符串字段。
注册表缺失时默认 DENY（安全侧默认拒绝）。
"""

from __future__ import annotations

import os
import uuid
from threading import Lock
from typing import Any

import openhands.sdk.agent.base as _sdk_agent_base
from openhands.sdk.agent.agent import Agent as OpenHandsAgent
from openhands.sdk.event.error_classification import AGENT_OUTCOME
from openhands.sdk.event.llm_convertible import ActionEvent
from openhands.sdk.event.llm_convertible.observation import AgentErrorEvent
from pydantic import Field, PrivateAttr

from packages.application.ports.agent_runtime import RuntimeEvent, RuntimeEventKind
from packages.application.ports.policy_evaluator import PolicyEvaluator, PolicyRequest
from packages.domain.enums import PolicyDecision

_POLICY_REGISTRY: dict[str, PolicyEvaluator] = {}


def register_policy_context(evaluator: PolicyEvaluator) -> str:
    """注册 evaluator，返回 context_id（adapter 创建 agent 时调用）。"""
    context_id = str(uuid.uuid4())
    _POLICY_REGISTRY[context_id] = evaluator
    return context_id


def unregister_policy_context(context_id: str) -> None:
    """注销 evaluator（adapter close 时调用）。"""
    _POLICY_REGISTRY.pop(context_id, None)


class PolicyEnforcingAgent(OpenHandsAgent):
    """在工具执行点强制 PolicyEvaluator 裁决的 SDK Agent 子类。"""

    policy_context_id: str = Field(default="")
    policy_actor: str = Field(default="")
    policy_scope: str = Field(default="")

    _ros_policy_lock: Lock = PrivateAttr(default_factory=Lock)
    _ros_pending_events: list[RuntimeEvent] = PrivateAttr(default_factory=list)

    @property
    def prompt_dir(self) -> str:
        # SDK 默认按类模块定位 prompts/；子类位于 adapter 包，这里显式指回
        # SDK 内置 prompts 目录，避免复制模板造成升级漂移。
        return os.path.join(os.path.dirname(_sdk_agent_base.__file__), "prompts")

    def drain_policy_events(self) -> tuple[RuntimeEvent, ...]:
        """取走待投影的策略事件（adapter 在事件同步时冲刷）。"""
        with self._ros_policy_lock:
            events, self._ros_pending_events = self._ros_pending_events, []
        return tuple(events)

    def _queue_approval(self, tool_name: str) -> None:
        with self._ros_policy_lock:
            self._ros_pending_events.append(
                RuntimeEvent(
                    session_id=self.policy_scope,
                    kind=RuntimeEventKind.APPROVAL_REQUESTED,
                    message=tool_name,
                    payload={"tool_name": tool_name},
                )
            )

    def _denied_event(self, action_event: ActionEvent, reason: str) -> AgentErrorEvent:
        return AgentErrorEvent(
            tool_name=action_event.tool_name,
            tool_call_id=action_event.tool_call_id,
            error=f"policy denied tool execution: {reason}",
            classification=AGENT_OUTCOME,
        )

    def _evaluate(self, tool_name: str) -> PolicyDecision:
        evaluator = _POLICY_REGISTRY.get(self.policy_context_id)
        if evaluator is None:
            # 注册表缺失（极端状态）→ 安全侧默认拒绝
            return PolicyDecision.DENY
        request = PolicyRequest(
            actor=self.policy_actor,
            capability=tool_name,
            action="execute",
            scope=self.policy_scope,
            resource=tool_name,
        )
        with self._ros_policy_lock:
            evaluation = evaluator.evaluate(request)
        return evaluation.decision

    def _execute_action_event(self, conversation: Any, action_event: ActionEvent) -> list[Any]:
        """策略裁决后委托 SDK 执行；拒绝不触达工具 executor。"""
        decision = self._evaluate(action_event.tool_name)
        if decision is PolicyDecision.DENY:
            return [self._denied_event(action_event, "denied by Research OS policy")]
        if decision is PolicyDecision.REQUIRE_APPROVAL:
            self._queue_approval(action_event.tool_name)
            return [
                self._denied_event(action_event, f"approval required ({action_event.tool_name})")
            ]
        return super()._execute_action_event(conversation, action_event)


__all__ = [
    "PolicyEnforcingAgent",
    "register_policy_context",
    "unregister_policy_context",
]
