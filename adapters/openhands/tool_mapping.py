"""Tool 映射：frozen tool set → OpenHands 工具装配。

frozen_tool_set（AgentSessionSpec 冻结工具名元组）→ OpenHands Tool spec 列表；
custom tool 经 register_tool 注册（S3 模式）；MCP 配置仅做形状归一化
（live MCP 延后 M7，本模块只提供确定性纯函数映射）。
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from openhands.sdk.tool.registry import register_tool
from openhands.sdk.tool.spec import Tool
from openhands.sdk.tool.tool import ToolDefinition


def tools_for_frozen_set(frozen_tool_set: Sequence[str]) -> list[Tool]:
    """冻结工具名 → OpenHands Tool spec 列表（装配面）。

    每个名字映射为一个 Tool(name=...)；未注册的工具由 agent 侧
    resolver 在 init 时解析（未知名由 SDK 报错，属装配期失败）。
    """
    return [Tool(name=name) for name in frozen_tool_set]


def session_tool_ids(
    frozen_tool_set: Sequence[str],
    run_chain_tool_ids: Sequence[str] = (),
) -> tuple[str, ...]:
    """会话工具列表 = 冻结集 **减去**「由运行链执行」的那部分（GOAL-011 EC-01）。

    - 缺省（`run_chain_tool_ids` 空）⇒ 逐字返回冻结集：**既有语义不变**。
    - 排除项必须是冻结集的子集：越界即**装配期错误**（点名越界的名字），
      免得用一份不再描述本次冻结的名单去悄悄缩小工具面。
    - 排除是**声明化**的：只对协议里显式写了 `capability_execution: run_chain`
      的 phase 生效。缺席声明的名字**不会**被这里丢掉——它们照旧交给 SDK 解析，
      未注册时由 SDK 报错，并被
      `test_unmapped_tool_set_is_named_not_silently_dropped` 固定在「点名拒绝」。
    """
    frozen = set(frozen_tool_set)
    excluded = set(run_chain_tool_ids)
    outside = sorted(excluded - frozen)
    if outside:
        raise ValueError(f"run-chain tool ids not in the frozen tool set: {', '.join(outside)}")
    return tuple(name for name in frozen_tool_set if name not in excluded)


def register_custom_tools(
    definitions: Sequence[tuple[str, type[ToolDefinition[Any, Any]] | ToolDefinition[Any, Any]]],
) -> None:
    """注册自定义工具到进程级 registry（S3 模式，幂等）。"""
    for name, factory in definitions:
        register_tool(name, factory)


def normalize_mcp_config(mcp_config: dict[str, object]) -> dict[str, object]:
    """MCP 配置形状归一化（R-12；live MCP 延后 M7）。

    输入为 Research OS MCP registry 条目，输出为 OpenHands SDK MCP 配置
    可接受形状；未知字段不静默透传（extra 拒绝）。
    """
    allowed = {"command", "args", "env", "transport"}
    normalized: dict[str, object] = {}
    for key, value in mcp_config.items():
        if key not in allowed:
            raise ValueError(f"unsupported MCP config key: {key}")
        normalized[key] = value
    return normalized


__all__ = [
    "normalize_mcp_config",
    "register_custom_tools",
    "session_tool_ids",
    "tools_for_frozen_set",
]
