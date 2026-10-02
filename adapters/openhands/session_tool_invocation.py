"""会话工具调用桥：把工具名桥接到装配方给的 ToolProvider 实例（GOAL-028 EC-01）。

**它是什么**：`build_session_tools` 需要「工具名 → 调用桥」；本模块提供**真实**那种桥
（不是空壳）：按 `tool_name` 找到 provider id 与 tool id，构造 `ToolCallRecord`，
经 `execute_tool_call`（与运行链**同一个**策略+执行面）执行，并把结果从 ArtifactStore
读回来当作工具返回内容。

**为什么复用 `execute_tool_call` 而不是自己调 provider**：策略裁决与失败分类只应该有
**一个**判定点（AGENTS.md §5 的 Policy Wrapper 语义）。会话工具与运行链走同一扇门，
「会话里能不能调」与「运行链里能不能调」就不会分叉。

**参数传递同形**：参数经 `tool-args:{task_id}:{operation_key}` 制品传给 provider
（provider 按 `argument_digest` 重算校验，防篡改）——与运行链、REST 适配器、MCP 适配器
同一口径；调用方不能绕过 digest 直接塞参数。

**边界**：本模块只做「构造 + 调用 + 取回」；它不判定能力名是否被允许（那是 policy 的事），
也不编造结果（provider 没了就点名拒绝）。
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.policy_evaluator import PolicyEvaluator
from packages.application.ports.tool_provider import ToolProvider
from packages.application.tool_plane.execution import execute_tool_call
from packages.application.tool_plane.results import fetch_spilled_result
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import ToolCallStatus
from packages.domain.tools import ToolCallRecord, ToolProviderSpec

ARGS_ARTIFACT_PREFIX = "tool-args:"


@dataclass(frozen=True, slots=True)
class SessionToolSpec:
    """一个会话工具的三件事实：provider、provider 侧的工具 id、以及它承载的能力名。

    `capability` 是策略面看到的名字（`execute_tool_call` 用它求值）；它与
    **会话工具名**应当一致（`session_tool_bindings` 的 `tool_name`），否则策略放行的是
    一个名字、实际执行的是另一个——那正是本 GOAL 要修的旧症结的镜像。
    """

    provider_id: str
    tool_id: str
    capability: str


def make_tool_invoker(  # noqa: PLR0913 - 装配面：provider/tool/能力 + 四个依赖
    tool: SessionToolSpec,
    *,
    providers: Mapping[str, ToolProvider],
    provider_specs: Mapping[str, ToolProviderSpec],
    artifacts: ArtifactStore,
    policy: PolicyEvaluator,
    task_id: Callable[[], str],
    actor: str = "system:session-tool",
) -> Callable[[dict[str, object]], str]:
    """构造一个工具名的调用桥（每次调用只服务**一次**会话工具调用）。

    `task_id` 是**取当前 task id 的可调用对象**（会话工具不是在 task 构造时执行，
    所以 task id 必须在调用时刻取；提前绑死会让两次会话共用同一个参数制品）。
    """
    provider_id = tool.provider_id

    def _invoke(arguments: dict[str, object]) -> str:
        provider = providers.get(provider_id)
        provider_spec = provider_specs.get(provider_id)
        if provider is None or provider_spec is None:
            raise InvalidInputError(
                f"session tool provider {provider_id!r} has no registered instance in this assembly"
            )
        record = _tool_call(task_id(), tool, artifacts, arguments, actor)
        outcome = execute_tool_call(provider, provider_spec, record, policy, actor)
        result = outcome.result
        if result is None:
            raise InvalidInputError(f"session tool {tool.tool_id} returned no result record")
        raw = fetch_spilled_result(artifacts, result)
        if raw is None:
            raise InvalidInputError(
                f"session tool {tool.tool_id} produced no spilled output in this assembly"
            )
        payload: object = json.loads(raw.decode("utf-8"))
        return _as_text(payload)

    return _invoke


def _tool_call(
    task_id: str,
    tool: SessionToolSpec,
    artifacts: ArtifactStore,
    arguments: Mapping[str, object],
    actor: str,
) -> ToolCallRecord:
    """参数经 ArtifactStore 传递（provider 按 `argument_digest` 重算校验）。"""
    content = json.dumps(dict(arguments), ensure_ascii=False, sort_keys=True).encode("utf-8")
    operation_key = f"session:{tool.tool_id}"
    artifact_id = f"{ARGS_ARTIFACT_PREFIX}{task_id}:{operation_key}"
    if artifacts.meta(artifact_id) is None:
        artifacts.put(
            Artifact(
                id=artifact_id,
                digest=Digest.of_bytes(content),
                size_bytes=len(content),
                media_type="application/json",
                created_by=actor,
                source_refs=[f"task:{task_id}"],
                classification="tool-args",
            ),
            content,
        )
    return ToolCallRecord(
        task_id=task_id,
        attempt=1,
        operation_key=operation_key,
        tool_id=tool.tool_id,
        capability=tool.capability,
        argument_digest=Digest.of_bytes(content),
        status=ToolCallStatus.REQUESTED,
        recorded_at=Timestamp.now(),
    )


def _as_text(payload: object) -> str:
    if isinstance(payload, str):
        return payload
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


__all__ = ["ARGS_ARTIFACT_PREFIX", "make_tool_invoker"]
