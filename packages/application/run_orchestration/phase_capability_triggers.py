"""运行链的**声明式触发**与 **phase 级过滤**（GOAL-20261006-031 EC-03）。

**为什么单列**：`phase_capabilities.py` 有 450 行硬上限（规模门），EC-03 在 `RunChainCall`
上加的两个声明字段（`requires_previous_ids` / `phase_id`）带来的判定逻辑放在这里；
`phase_capabilities.py` 保留执行循环与取参，只从这里取判定 —— 与全仓既有的
「声明面 vs 执行面分列」同一手法（`read_surface.py` vs `read_provider.py`）。

**射程**：四个纯判定（过滤 / 取 id 字段 / 跳过判定 / 跳过判词）。全部**只看声明的
字段**（在场性 / 相等），不看内容、不做业务判断 —— 「如果就」由协议/装配方**声明**，
不写在代码里。`lookup` 由调用方注入（点分路径**唯一取法**在 `phase_capabilities._lookup`，
本模块不复制一份）。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from packages.application.ports.errors import InvalidInputError

if TYPE_CHECKING:  # 只为类型：避免与 phase_capabilities / task_executor 形成导入环
    from packages.application.run_orchestration.phase_capabilities import RunChainCall
    from packages.application.run_orchestration.task_executor import SessionSpecContext

#: 点分路径取值函数（`phase_capabilities._lookup` 的签名；用于 `ids_from_previous`）。
Lookup = Callable[[Mapping[str, object], str], object]


def planned_in_this_phase(call: RunChainCall, spec: SessionSpecContext) -> bool:
    """本 phase 是否该执行这条调用（**phase 级过滤**）。

    两重判定，缺一不可：

    1. **provider 在声明面**（既有语义，逐字节不变）：`call.provider_id` 必须在
       本 phase 的 `run_chain_tool_ids` 里 —— 声明的排除面仍然有效；
    2. **phase 归属**（EC-03 新增）：`call.phase_id` 非空时**必须等于**本 phase 的
       `phase_id`；缺省 `None` ⇒ 该条件不参与判定（既有行为逐字节不变）。

    为什么需要第 2 重：过滤若只按 provider，一次 run 里两个 phase 声明的
    **同一 provider 的不同调用**会在**两个 phase 都执行**——第二轮调用因此会被第一轮
    phase 抢先跑掉（跳过臂的判词落在错误的任务上，「第二轮没跑」从任务归属上不可判）。
    """
    if call.provider_id not in spec.run_chain_tool_ids:
        return False
    if call.phase_id is None:
        return True
    return call.phase_id == spec.phase_id


def previous_ids(
    call: RunChainCall,
    previous: Mapping[str, object] | None,
    *,
    lookup: Lookup,
) -> object:
    """上一步结果里该步声明的 id 列表字段（点分路径走注入的 `lookup`，与取值同源）。

    **路径缺失**（点分路径取不到）⇒ **点名失败**、**不吞**：那是**声明坏掉**
    （写错路径 / 第二轮输入与第一轮结果脱钩）⇒ 必须判红，不得被读成「不触发」。
    「不触发」的合法形态是**路径在场但值为空列表**。非点分名字取不到 ⇒ `None`
    （既有 `.get` 形态；`requires_previous_ids=False` 时它落进「不触发」）。
    """
    if call.ids_from_previous is None:
        return None
    if "." in call.ids_from_previous:
        try:
            return lookup(previous or {}, call.ids_from_previous)
        except InvalidInputError as error:
            raise InvalidInputError(
                f"run-chain tool {call.tool_id}: previous step's result carries no "
                f"{call.ids_from_previous!r} ({error})"
            ) from error
    return (previous or {}).get(call.ids_from_previous)


def should_skip(
    call: RunChainCall,
    previous: Mapping[str, object] | None,
    *,
    lookup: Lookup,
) -> bool:
    """**声明式触发**：`requires_previous_ids=False` 且上一步**没给出** id 列表 ⇒ 跳过本步。

    判定只看**声明的字段**在场性（值是不是**非空列表**）——不看内容、不做业务判断。
    「不触发」的形态是**路径在场但值为空列表**（或非点分名字取不到）：声明路径本身
    写错 ⇒ `previous_ids` 抛错、本函数**不**吞（fail closed，点名的是路径）。
    """
    if call.requires_previous_ids or call.ids_from_previous is None:
        return False
    value = previous_ids(call, previous, lookup=lookup)
    return not (isinstance(value, list) and value)


def select_artifact_id(
    previous: Mapping[str, object] | None,
    suffix: str,
    tool_id: str,
) -> str:
    """从**上一步读面结果**的证据列表里选出一个**制品 id**（GOAL-20261006-031 EC-03）。

    `evidence_read` 的返回内容里，每条证据都带 `artifact_id`（读面投影的既有域字段，
    `Evidence.artifact_id`）——本函数按**声明的后缀**选出那一条，把它的 `artifact_id`
    直接作为下一步的 `artifact_id` 参数。这是「第二轮读**第一轮的产出**」里
    「哪一份产出」的**声明式**决定点。

    **为什么是后缀匹配而不是拼 id**：制品 id 里含**执行期才生成**的 task id，装配方
    无从写死；而「产出名 / 工具名」（如合约声明的 `discovery_report`、工具
    `literature_search` 的结果制品 `tool-result:{task}:{op}:literature_search`）是
    **声明事实**——按它选是承接声明，不是猜字符串。合成 id 的字符串运算不该出现在
    应用层。

    fail closed（两种情况都**点名**，不静默取一条）：
    - 上一步结果里没有 `evidence` 列表 ⇒ 点名（声明与该步的输出形态不符）；
    - 匹配数 ≠ 1（零条 / 多条）⇒ 点名并**列出全部候选 `artifact_id`**（可诊断）。
    """
    entries = (previous or {}).get("evidence")
    if not isinstance(entries, list):
        raise InvalidInputError(
            f"run-chain tool {tool_id} declares an evidence source_ref suffix but the "
            "previous step carries no 'evidence' list to select from"
        )
    ids = [
        str(item.get("artifact_id"))
        for item in entries
        if isinstance(item, Mapping) and item.get("artifact_id")
    ]
    matched = [item for item in ids if item.endswith(suffix)]
    if len(matched) != 1:
        raise InvalidInputError(
            f"run-chain tool {tool_id}: expected exactly one evidence artifact_id ending "
            f"with {suffix!r}, found {sorted(matched)} (candidates: {sorted(ids)})"
        )
    return matched[0]


def select_artifact_id_for_prefixes(
    previous: Mapping[str, object] | None,
    suffix: str,
    tool_id: str,
    *,
    task_prefixes: tuple[str, ...],
) -> str:
    """按后缀选中**恰好一条**制品，并限定它属于给定的**任务前缀**之一（多轮循环用）。

    为什么多轮需要它（实测的机制缺口）：`select_artifact_id` 要求后缀匹配**恰好一条** ——
    两轮时成立；**三轮起**同一后缀会匹配到**多份**（前几轮的产出都还在证据投影里）
    ⇒ 既有函数 fail closed 点名「found 多份」。那不是判据缺陷，而是**两轮语义不适用于三轮**。

    `task_prefixes` 是**上一轮**的制品标识前缀（由调用方按该轮的任务 id 声明/推导）：
    候选先按它收窄，再要求恰好一条 ⇒ 第 N 轮稳定选中**第 N-1 轮**那一份。

    fail closed 形态**不放宽**：收窄后零条 / 仍多条 ⇒ 点名，并把候选与收窄条件一并列出
    （可诊断）。

    与 `select_artifact_id` 的关系：两者同源（同样的 `evidence` 列表、同样的后缀判据、
    同样的 fail-closed 形态），差别只有「是否按任务前缀收窄」——既有函数逐字未动，
    单轮/两轮调用方**逐字节不变**。
    """
    entries = (previous or {}).get("evidence")
    if not isinstance(entries, list):
        raise InvalidInputError(
            f"run-chain tool {tool_id} declares an evidence source_ref suffix but the "
            "previous step carries no 'evidence' list to select from"
        )
    ids = [
        str(item.get("artifact_id"))
        for item in entries
        if isinstance(item, Mapping) and item.get("artifact_id")
    ]
    narrowed = [item for item in ids if any(prefix in item for prefix in task_prefixes)]
    matched = [item for item in narrowed if item.endswith(suffix)]
    if len(matched) != 1:
        raise InvalidInputError(
            f"run-chain tool {tool_id}: expected exactly one evidence artifact_id ending with "
            f"{suffix!r} in the previous round, found {sorted(matched)} "
            f"(candidates: {sorted(ids)}; narrowed by: {sorted(task_prefixes)})"
        )
    return matched[0]


def skip_reason(call: RunChainCall) -> str:
    """跳过理由（**逐字点名**工具与字段 —— 跳过不是静默）。"""
    return (
        f"run-chain tool {call.tool_id} skipped: previous step carried no "
        f"{call.ids_from_previous!r} ids and this call declares requires_previous_ids=False"
    )


#: 记忆时效门的三条**处置**（与 `adapters.canonical.memory_read` 同源：读面给处置，
#: 这里按处置分派）。**互不混用**：三态各归各的处置，读面按值分派、不靠措辞。
MEMORY_USE = "USE"
MEMORY_ANNOTATE = "ANNOTATE"
MEMORY_SKIP = "SKIP"


def _memory_entries(payload: Mapping[str, object], tool_id: str) -> list[Mapping[str, object]]:
    """读面上一步的 `memories` 列表（缺字段 / 形态不符 ⇒ **点名**，fail closed）。"""
    raw = payload.get("memories")
    if not isinstance(raw, list):
        raise InvalidInputError(
            f"run-chain tool {tool_id} declares a memory gate but the previous step's "
            "result carries no 'memories' list to judge"
        )
    entries: list[Mapping[str, object]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            raise InvalidInputError(
                f"run-chain tool {tool_id}: memory entry is not an object ({item!r})"
            )
        entries.append(item)
    return entries


def _split_by_disposition(
    entries: list[Mapping[str, object]], tool_id: str
) -> tuple[list[str], list[str]]:
    """按 `disposition` 分成 `(已过期, 待复核)` 两组，**逐条点名**；未知取值 ⇒ 点名。"""
    expired: list[str] = []
    due: list[str] = []
    for item in entries:
        disposition = item.get("disposition")
        memory_id = str(item.get("memory_id") or "")
        note = f"{memory_id}（{item.get('validity')}；{item.get('reason')}）"
        if disposition == MEMORY_SKIP:
            expired.append(note)
        elif disposition == MEMORY_ANNOTATE:
            due.append(note)
        elif disposition != MEMORY_USE:
            raise InvalidInputError(
                f"run-chain tool {tool_id}: memory {memory_id!r} carries an unknown "
                f"disposition {disposition!r} (expected USE / ANNOTATE / SKIP)"
            )
    return expired, due


@dataclass(frozen=True, slots=True)
class MemoryGateDecision:
    """记忆时效门的判定结果（`skip=True` ⇒ 本步不执行；否则**执行**并带 `notes` 标注）。"""

    skip: bool
    notes: tuple[str, ...] = ()


def memory_step_gate(
    call: RunChainCall, previous: Mapping[str, object] | None
) -> MemoryGateDecision:
    """本步的记忆时效门判定（**未声明门 ⇒ 不跳过、不带标注** ⇒ 既有行为逐字节不变）。"""
    if not call.memory_validity_gate:
        return MemoryGateDecision(skip=False)
    verdict, notes = memory_gate_verdict(previous or {}, call.tool_id)
    return MemoryGateDecision(skip=verdict == MEMORY_SKIP, notes=notes)


def memory_gate_verdict(
    payload: Mapping[str, object],
    tool_id: str,
) -> tuple[str, tuple[str, ...]]:
    """**记忆时效门**（GOAL-20261009-042 EC-03）：按读面的 `disposition` 决定本步做什么。

    **为什么这是声明式而不是业务判断**：判定输入是**上一步读面的结果**（执行期才知道），
    而「到期怎么办」由**装配方**在协议里声明 —— 本函数只按读面给的 `disposition`
    三态分派（与 `should_skip` 同一形态：判断依据是**声明字段的取值**，不是应用层硬编码）。

    三态与处置**互不混用**（逐条）：

    - 任一记忆 `disposition == SKIP`（已过期）⇒ 整步**跳过**（不执行工具），
      理由**逐条点名**该记忆 id 与状态；
    - 否则若有 `disposition == ANNOTATE`（待复核）⇒ **照常执行**，但把**标注**带回
      （哪些记忆待复核、各自的 `review_after`）—— 「待复核」不是「过期」，
      不跳过、也不静默；
    - 否则（全部 `USE` / 无可判定的记忆）⇒ **照用**，标注为空（**不得**凭空加标记）。

    **缺字段点名**（fail closed，与全模块同一纪律）：`memories` 不在 / 不是列表 ⇒ 点名
    （那是**声明与该步输出形态不符**，不是「没有记忆」）；单条记忆缺 `disposition` ⇒ 点名。
    返回 `(verdict, notes)`；`verdict` ∈ `{USE, ANNOTATE, SKIP}`，`notes` 逐条点名。
    """
    raw = _memory_entries(payload, tool_id)
    expired, due = _split_by_disposition(raw, tool_id)
    if expired:
        return MEMORY_SKIP, (
            f"run-chain tool {tool_id} skipped: {len(expired)} expired memory record(s) "
            "in the read result: " + "; ".join(expired),
        )
    if due:
        return MEMORY_ANNOTATE, (
            f"run-chain tool {tool_id} annotated: {len(due)} memory record(s) due for "
            "review (not expired, still used): " + "; ".join(due),
        )
    return MEMORY_USE, ()


__all__ = [
    "Lookup",
    "MEMORY_ANNOTATE",
    "MEMORY_SKIP",
    "MEMORY_USE",
    "MemoryGateDecision",
    "memory_gate_verdict",
    "memory_step_gate",
    "planned_in_this_phase",
    "previous_ids",
    "select_artifact_id",
    "select_artifact_id_for_prefixes",
    "should_skip",
    "skip_reason",
]
