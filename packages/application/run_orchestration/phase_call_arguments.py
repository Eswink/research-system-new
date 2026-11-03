"""运行链调用的**参数装配**（从 `phase_capabilities.py` 拆出：规模门）。

拆法与全仓一致（「声明面 vs 执行面」）：本模块只做「声明字段 → provider 参数」的翻译，
执行循环与证据登记留在 `phase_capabilities.py`。**行为逐字不变**（纯搬迁）。
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import TYPE_CHECKING, Any

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


def apply_retmax(
    declared: tuple["RunChainCall", ...], retmax: int | None
) -> "tuple[RunChainCall, ...]":
    """把**项目级** `retmax` 声明施加到检索类调用上（GOAL-20261101-103 EC-05）。

    为什么是本模块：`retmax` 是检索调用的一个**参数**（`fixed_arguments["retmax"]`），
    而本模块的职责正是「声明字段 → provider 参数」的翻译。

    **两条逐字边界**（判据钉住）：

    - `retmax is None` ⇒ 返回**入参本身**（``is`` 相同）⇒ 不声明项目的装配方行为逐字节不变；
    - 只改**带 `retmax` 键**的调用：读取步（`literature.read`）与任何别的能力**不被碰**
      —— 给一个不认识该参数的调用塞参数就是伪造调用。
    """
    if retmax is None:
        return declared
    applied: list["RunChainCall"] = []
    for call in declared:
        fixed = getattr(call, "fixed_arguments", None)
        if not isinstance(fixed, Mapping) or "retmax" not in fixed:
            applied.append(call)
            continue
        applied.append(replace(call, fixed_arguments={**fixed, "retmax": retmax}))
    return tuple(applied)


def declared_retmax(run_chain_arguments: object, *, where: str = "protocol phase") -> int | None:
    """从**协议相级**的 `run_chain_arguments` 取 `retmax`（未声明 ⇒ `None`）。

    **这是这一级的唯一取值点**：它只认 `{"retmax": <int>}` 这一种形态。

    三种拒绝（各自点名，判词都**指出来源是协议相级**）：
    - 映射本身不是映射 ⇒ 「`run_chain_arguments` 必须是映射」；
    - `retmax` 不是整数（含 `True` / `"three"`）⇒ 点名「协议相级必须是整数」；
    - 越界（`0` / `-1` / `101`）⇒ 点名「协议相级必须在 1…`MAX_RETMAX`」。

    **范围常数与 env / 项目面共用 `MAX_RETMAX`**（从 `retrieval_wiring` 取）—— 一个规则、
    一处上界。不在这里 import 顶层是为了不给 `run_orchestration` 包引入对 `services` 的
    模块级依赖（分层方向：`services` 依赖 `packages`，不能反过来）。
    """
    if run_chain_arguments is None:
        return None
    if not isinstance(run_chain_arguments, Mapping):
        raise InvalidInputError(
            f"{where} run_chain_arguments must be a mapping, got "
            f"{type(run_chain_arguments).__name__}"
        )
    if "retmax" not in run_chain_arguments:
        return None
    raw = run_chain_arguments["retmax"]
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise InvalidInputError(f"{where} retmax must be an integer, got {raw!r}")
    from services.api.retrieval_wiring import MAX_RETMAX

    if not 1 <= raw <= MAX_RETMAX:
        raise InvalidInputError(f"{where} retmax must be between 1 and {MAX_RETMAX}, got {raw}")
    return raw


def retmax_for_phase(spec: Any, deps: Any) -> int | None:
    """本相该用哪个 `retmax`（协议相级 > 项目声明；都未声明 ⇒ `None` = **不施加**）。

    `None` 一路传下去是「未声明」的完整表达：`apply_retmax(calls, None)` 原样返回，
    env / 显式参数各自的臂因此在下游生效（GOAL-20261103-105 EC-03 的缺陷修复即此）。
    `deps.retmax` 只承载**项目声明那一级**；协议那一级由 `declared_retmax` 判定并校验。
    """
    from_phase = declared_retmax(getattr(spec, "run_chain_arguments", None))
    return from_phase if from_phase is not None else getattr(deps, "retmax", None)


__all__ = ["apply_retmax", "arguments_for", "declared_retmax", "lookup_path", "retmax_for_phase"]
