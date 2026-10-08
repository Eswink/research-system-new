"""Canonical 读面的**工具面描述子**（GOAL-029；与 `read_provider.py` 拆分）。

**为什么单列**：`read_provider.py` 有 **450 行硬上限**（规模门），而本 GOAL 逐轮往它上面
接新的读能力实现 ⇒ 越界。拆分的切法是「**声明面的描述子** vs **执行面的实现**」：
本模块放「有哪些工具、各自承载哪个能力、它们的 `ToolSpec` 长什么样」；
`read_provider.py` 放 `CanonicalReadProvider` 的执行实现。

**工具名的命名空间是能力名**（与 `policy.yaml` 同源）—— 两者必须一致，否则
「放行的是一个名字、执行的是另一个」。本模块是那个对应关系的**唯一**声明点。
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from packages.application.ports.errors import InvalidInputError
from packages.application.tool_plane.results import spill_large_result
from packages.domain.core import Digest
from packages.domain.enums import ProviderType
from packages.domain.tools import ToolProviderSpec, ToolResultRecord, ToolSpec

#: 参数制品的 id 前缀（与 `ncbi` / `europe_pmc` / MCP 同一口径）。
ARGS_ARTIFACT_PREFIX = "tool-args:"

#: provider 侧 tool id → 说明。**能力的名字空间是能力名**（与 `policy.yaml` 同源）。
_TOOL_DESCRIPTIONS: dict[str, str] = {
    "artifact_read": "Read an artifact (metadata + content) from the canonical artifact store.",
    "evidence_read": "Read claims / evidence / relations for a run from the canonical ledger.",
    "claim_read": "Read claims (with their evidence relations) from the canonical ledger.",
    "workspace_read": "Read the canonical workspace/run view exposed to the session.",
    "budget_read": "Read the canonical budget ledger snapshot (reservations + usage entries).",
    "experiment_read": "Read runs of a plan recorded in the canonical experiment store.",
    "experiment_plan_read": "Read canonical experiment plans (preregistered; filterable by state).",
    "deliverable_read": "Read the persisted research deliverable for a run (deliverable.json).",
    "run_read": "Read a canonical research run (state / protocol / manifest digests).",
    # GOAL-20261008-036 EC-02：`review.read` 的描述子（实现在 `review_read.py`）。
    "review_read": "Read recorded acceptance review findings (per-criterion verdicts) for a run.",
    # GOAL-20261008-037 EC-03：`research_state.read` 的描述子（实现在
    # `research_state_read.py`）——读**程序内前序 run** 的落库结论（入口是程序归属）。
    "research_state_read": (
        "Read the recorded state of a research program's prior runs (their terminal state"
        " and verbatim review verdicts); the entry is the program, not this run."
    ),
}

#: tool id → 它承载的能力名。**承接 = 声明 + 实现**：两者必须同时在，工具名与策略面同源。
_TOOL_CAPABILITIES: dict[str, str] = {
    "artifact_read": "artifact.read",
    "evidence_read": "evidence.read",
    "claim_read": "claim.read",
    "workspace_read": "workspace.read",
    "budget_read": "budget.read",
    "experiment_read": "experiment.read",
    "experiment_plan_read": "experiment_plan.read",
    "deliverable_read": "deliverable.read",
    "run_read": "run.read",
    # GOAL-20261008-036 EC-02：`review.read` 的承载（工具名与策略面同源）。
    "review_read": "review.read",
    # GOAL-20261008-037 EC-03：`research_state.read` 的承载 —— 读**程序内前序 run**
    # 的落库结论（入口是程序归属，不是本 run 的标识）。
    "research_state_read": "research_state.read",
}

#: deliverable 的 canonical 落点（与 `services/api/routers/deliverable.py` 同一约定：
#: `persist_completion` 写的 `f"{run_id}:deliverable.json"`）。读面不新造第二个名字。
_DELIVERABLE_ARTIFACT = "deliverable.json"


def tool_ids() -> list[str]:
    """声明的工具 id（排序后，供 schema digest 稳定复用）。"""
    return sorted(_TOOL_DESCRIPTIONS)


def describe_tools(
    provider: ToolProviderSpec, *, capabilities: Mapping[str, str]
) -> tuple[ToolSpec, ...]:
    """把声明的工具面映射成 `ToolSpec` 元组（与 `ncbi.py::list_tools` 同形）。

    `capabilities` 给每个 tool id 对应的**能力名**（本 provider 的若干工具可能承载不同能力，
    如 `artifact_read` → `artifact.read`、`evidence_read` → `evidence.read`）。
    """
    return tuple(
        ToolSpec(
            id=tool_id,
            name=tool_id,
            effect_class=provider.effect_class,
            provider_kind=ProviderType.NATIVE,
            capabilities=[capabilities[tool_id]] if tool_id in capabilities else [],
            description=description,
        )
        for tool_id, description in _TOOL_DESCRIPTIONS.items()
    )


def read_tool_args(artifacts: Any, call: Any) -> dict[str, object]:
    """参数制品的读取口径（**唯一一处**）：内容寻址 + `argument_digest` 重算校验。

    与 `ncbi` / `europe_pmc` / MCP 同一口径 —— 调用方不能绕过 digest 直接塞参数。
    """
    artifact_id = f"{ARGS_ARTIFACT_PREFIX}{call.task_id}:{call.operation_key}"
    try:
        content = artifacts.get(artifact_id)
    except Exception as exc:  # noqa: BLE001 - 未知制品按 args 缺失收敛
        raise InvalidInputError(f"tool args missing for {call.operation_key}") from exc
    if Digest.of_bytes(content) != call.argument_digest:
        raise InvalidInputError("tool args digest mismatch")
    parsed = json.loads(content.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise InvalidInputError("tool args must be a JSON object")
    return parsed


def spill_tool_result(
    artifacts: Any, call: Any, payload: dict[str, object], *, threshold_bytes: int
) -> ToolResultRecord:
    """结果落盘口径（TOOL_RUNTIME §7 的阈值分流）；返回 `ToolResultRecord`。"""
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    record: ToolResultRecord = spill_large_result(
        artifacts, call, raw, threshold_bytes=threshold_bytes
    ).record
    return record


__all__ = [
    "ARGS_ARTIFACT_PREFIX",
    "describe_tools",
    "read_tool_args",
    "spill_tool_result",
    "tool_ids",
]
