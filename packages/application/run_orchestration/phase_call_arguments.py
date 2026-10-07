"""运行链调用的**参数装配**（从 `phase_capabilities.py` 拆出：规模门）。

拆法与全仓一致（「声明面 vs 执行面」）：本模块只做「声明字段 → provider 参数」的翻译，
执行循环与证据登记留在 `phase_capabilities.py`。**行为逐字不变**（纯搬迁）。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from packages.application.ports.errors import InvalidInputError
from packages.application.run_orchestration.phase_capability_triggers import (
    select_artifact_id,
    select_artifact_id_for_prefixes,
)

if TYPE_CHECKING:  # 只为类型：避免导入环
    from packages.application.run_orchestration.phase_capabilities import RunChainCall, _StepInputs


def lookup_path(material: Mapping[str, object], path: str) -> object:
    """点分路径取值（如 `retrieval.query`）；任一层缺失 ⇒ 抛错（fail closed，不猜）。"""
    current: object = material
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise InvalidInputError(f"declared input carries no {path!r}")
        current = current[part]
    return current


def arguments_for(
    call: RunChainCall,
    inputs: _StepInputs,
) -> dict[str, object]:
    args: dict[str, object] = dict(call.fixed_arguments)
    for path in call.arguments_from_input:
        # 点分路径的最后一段就是 provider 看到的参数名（`retrieval.query` → `query`）。
        args[path.rsplit(".", 1)[-1]] = lookup_path(inputs.material, path)
    if call.ids_from_previous is not None:
        if "." in call.ids_from_previous:
            # 点分路径：与 `arguments_from_input` 同一取法（`_lookup`），用于信封形
            # 结果（如 MCP 的 `structured.ids`）。非点分名字走**原样**分支，既有行为
            # 逐字节不变（`test_run_chain_capabilities` 未改一行）。
            ids = lookup_path(inputs.previous or {}, call.ids_from_previous)
        else:
            ids = (inputs.previous or {}).get(call.ids_from_previous)

        if not isinstance(ids, list) or not ids:
            raise InvalidInputError(
                f"previous step carries no {call.ids_from_previous!r} ids "
                f"for run-chain tool {call.tool_id}"
            )
        args["ids"] = [str(item) for item in ids]
    if call.artifact_from_previous is not None:
        # 派生面：本步读哪个制品由**上一步的读面结果**决定（见 `artifact_from_previous`）。
        # 声明了 `artifact_from_previous_round`（多轮循环）⇒ 收窄到**上一轮**那一份；
        # 未声明 ⇒ 走既有后缀判据（单轮 / 两轮语义**逐字节不变**）。
        if call.artifact_from_previous_round:
            args["artifact_id"] = select_artifact_id_for_prefixes(
                inputs.previous,
                call.artifact_from_previous,
                call.tool_id,
                task_prefixes=inputs.previous_round_task_prefixes,
            )
        else:
            args["artifact_id"] = select_artifact_id(
                inputs.previous, call.artifact_from_previous, call.tool_id
            )
    if call.run_id_argument:
        # 本次 run 的标识（**执行期才存在**）：缺它 ⇒ 点名拒绝，不猜一个。
        if not inputs.run_id:
            raise InvalidInputError(
                f"run-chain tool {call.tool_id} declares run_id_argument but no run id "
                "is available in this step context"
            )
        args["run_id"] = inputs.run_id
    return args


__all__ = ["arguments_for", "lookup_path"]
