"""ToolProvider Port：执行工具调用（docs/architecture/TOOL_RUNTIME.md）。

职责：按 ToolProviderSpec 执行 ToolCallRecord 对应的工具，返回归一化
ToolResultRecord（输出只保存 digest，内容经 ArtifactStore 持久化）；
枚举 provider 可用的 ToolSpec schema（list_tools）；健康探测
（check_health，schema digest 供漂移检测）。
非职责：Skill/Capability 装配（ToolResolver）；frozen tool set 约束由
调用方（AgentSessionSpec.frozen_tool_set）执行；Tool credential 属于独立
信任域（ADR-0012、DoD：tool credential 与 LLM credential 隔离），本 Port
不解析凭据。

错误消息必须 redaction；高风险工具（EffectClass）由 PolicyEvaluator 在
调用前裁决，本 Port 不承担策略判断。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.tools import (
    ToolCallRecord,
    ToolHealthReport,
    ToolProviderSpec,
    ToolResultRecord,
    ToolSpec,
)


@runtime_checkable
class ToolProvider(Protocol):
    """工具执行契约；operation_key 幂等由调用方保证。"""

    def execute(self, provider: ToolProviderSpec, call: ToolCallRecord) -> ToolResultRecord: ...

    def list_tools(self, provider: ToolProviderSpec) -> tuple[ToolSpec, ...]: ...

    def check_health(self, provider: ToolProviderSpec) -> ToolHealthReport: ...

    def close(self) -> None: ...
