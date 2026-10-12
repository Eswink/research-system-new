"""`memory.read` 的**执行实现**（GOAL-20261009-042 EC-02；与 `read_provider.py` 分列）。

**为什么单列**：`read_provider.py` 已到 **433/450 行**（规模门），本轮再往上接一条读能力
就越界。拆分的切法与 `run_read.py` / `review_read.py` / `research_state_read.py` 同：
本模块只放 `memory.read` 这一条的实现，`read_provider.py` 只留一行委派。

**它读什么**：`MemoryStore.query()`（既有 Port）—— 与 HTTP 读面
`GET /projects/{id}/memory` **同一个**查询口径，**不新造第二套**。

**它比既有读面多什么（本 GOAL 的靶子）**：既有读面把 `validity` **印出来**就算完事；
本读面对每条记忆给出**处置**（`disposition`）—— 到期/待复核的记忆**被跳过或被标注**，
两者**互不混用**且都**点名理由**。这样研究循环有一条**可消费**的面，
到期/待复核才**真的**改变后续行为（而不是只做成一个没人读的字段）。

**三条硬约束（写进实现，不靠调用方自律）**：

1. **不读挂钟**：`now` 由**调用方**给（`args["now"]`），本模块**不**调 `Timestamp.now()`
   ⇒ 同一份记录 + 同一时点 ⇒ 判定必相同（可复现）。
2. **未声明不猜**：`expires_at` / `review_after` 都没声明 ⇒ 处置是「照用」
   （**不**当成已到期 —— AGENTS.md §8 的口径）。
3. **点名**：缺 `MemoryStore` / 缺 `now` / `now` 形态非法 ⇒ **点名拒绝**；
   **不**返回空列表冒充「没有记忆」。

**边界**（与既有读面同一条纪律）：

- **只读**：本模块不写任何 store；
- **不**自动删除 / 降权 / 重建索引（`Q-1` 的另两条子面，`GOAL-20261009-042` 的 `T-1`）；
- **不**跨项目（消费按项目内划界，`T-2`）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# GOAL-20261011-052 EC-03：**判定已搬去应用层**（两个读面共用；HTTP 面**不得** import
# 具体适配器 ⇒ 共用判定必须落在它能 import 的那一层）。本模块**原样再导出**这些名字
# （既有调用方与判据不受影响；**判定实现一字未动**）。
from packages.application.memory.disposition import (  # noqa: E402
    DISPOSITION_ANNOTATE,
    DISPOSITION_CONFLICTED,
    DISPOSITION_SKIP,
    DISPOSITION_SUPERSEDED,
    DISPOSITION_USE,
    TERMINAL_CURRENT,
    TERMINAL_CYCLE,
    TERMINAL_OUT_OF_VIEW,
    TERMINAL_SUCCEEDED,
    conflicted_by_index,
    disposition_of,
    disposition_reason,
    resolved_pair_index,
    superseded_by_index,
    terminal_versions,
)
from packages.application.memory.validity import conflict_timeliness_at, validity_at
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Timestamp


def _moment(args: dict[str, object]) -> Timestamp:
    """调用方给的时点（**必填**）：读面必须可复现 ⇒ 本模块不读挂钟。"""
    raw = args.get("now")
    if raw is None or str(raw).strip() == "":
        raise InvalidInputError(
            "memory_read requires an explicit 'now' (RFC3339) so the validity decision"
            " is reproducible; this read face never consults the wall clock"
        )
    text = str(raw).strip()
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise InvalidInputError(f"memory_read 'now' is not a valid timestamp: {text!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InvalidInputError(
            "memory_read 'now' must be timezone-aware (got "
            f"{text!r}); UTC is the only accepted zone"
        )
    try:
        return Timestamp(parsed)
    except ValueError as exc:
        raise InvalidInputError(str(exc)) from exc


def _identity_fields(record: Any, state: Any) -> dict[str, object]:
    """身份 / 内容 / 时效那几项（**逐条披露**；判定项由 `_memory_row` 补上）。

    GOAL-20261010-045 EC-03：**冲突声明**与**生效起点**逐条披露 —— 为什么在读面上
    （而不只塞进判词）：读面是消费者唯一能自己回答「这条记忆与谁冲突」的地方；
    判词只覆盖「本研究路径关心的那一条」，读面覆盖全部（两者**不互相顶替**）。
    """
    return {
        "memory_id": str(record.id),
        "tier": str(record.tier),
        "scope": str(record.scope),
        "content": str(record.content),
        "confidence": float(record.confidence),
        "active": bool(record.active),
        "contradictions": list(record.contradictions),
        "valid_from": (
            record.valid_from.value.isoformat() if record.valid_from is not None else None
        ),
        #: 时效状态（`None` = 未声明或未到 —— **不猜**，与「已到期」严格区分）。
        "validity": state.value if state is not None else None,
    }


def _conflict_timeliness_face(record: Any, moment: Timestamp) -> str | None:
    """**冲突声明**的时效（`STALE` / `REVIEW_DUE` / `None`）—— 与 `validity` **互不顶替**。

    为什么单列一个键而不是复用语义的 `validity`：两者说的是**两件事** ——
    `validity` 是**记录**的时效（这条记忆过期了吗），本键是**冲突声明**的时效
    （当年声明的那个分歧**还算不算数**）。记录的时效到了**不代表**冲突声明失效，
    反之亦然 ⇒ 两个键各自披露（读面**不合并**、**不推断**）。

    **`STALE` 不等于「没有冲突」**：声明仍在 `contradictions` 里、读面**照旧披露**；
    本键只回答「它还算不算数」。判定**在域层**（本面不重写第二套）。
    """
    state = conflict_timeliness_at(record, moment)
    return state.value if state is not None else None


def _terminal_face(record: Any, terminal: dict[str, object] | None) -> dict[str, object]:
    """GOAL-20261011-053 EC-02（`BB-1`）：**链的终点** —— 上面那两个键只给**直接**链接，
    在 A ⊂ B ⊂ C 时 A 的「替代品」B **自己可能已被取代** ⇒ 「**现在**的版本是哪条」
    在载荷里**答不出来**。本键让读者**不必自己追链**。

    四态互不混用（见 `terminal_versions`）：`CURRENT`（本条即当前版本）/
    `SUCCEEDED`（终点是点名的那些）/ `CYCLE`（有环，**点名**环上 id）/
    `OUT_OF_VIEW`（后继不在本批查询范围 ⇒ **点名**「看不见」，**不**假装它是当前版本）。
    """
    chain: dict[str, object] = dict(terminal or {})
    ids = chain.get("terminal")
    return {
        "state": str(chain.get("state", TERMINAL_CURRENT)),
        "ids": [str(item) for item in ids] if isinstance(ids, list) else [str(record.id)],
    }


def _resolution_face(record: Any) -> list[dict[str, str]]:
    """**逐对**消解记载的读面形态（GOAL-20261012-058 EC-03）。

    **声明一字不动**：`contradictions` 是历史事实，消解是**另一件事**；
    未消解 ⇒ 空列表 ⇒ 处置仍是 `CONFLICTED`（既有行为逐字不变）。
    """
    return [
        {
            "other_id": item.other_id,
            "resolved_by": item.resolved_by,
            "resolved_at": item.resolved_at.value.isoformat(),
        }
        for item in record.resolutions
    ]


def _project_records(records: Any, moment: Timestamp) -> list[dict[str, object]]:
    """把一批记录投影成读面行（三个索引**各算一次**，不逐条再查）。

    **为什么单列**：`memory_read` 有 50 行硬上限 —— 序 29/30 各加一个索引/键之后一度把它
    顶爆 ⇒ 逐段搬到这里（**语义一字未动**，只是换落点），并守住那道门。

    **三个索引都从同一批记录算**（不新增 Port 方法、不逐条再查 —— 那是 N+1 次查询，
    且会在两处看到不同的世界）：

    - `superseded_by_index`（序 18）：谁取代了它；
    - `terminal_versions`（序 21）：链的终点；
    - `conflicted_by_index`（序 30）：**谁声明了与它冲突**（与第一款**同一手法**）。
    """
    reverse = superseded_by_index(records)
    terminals = terminal_versions(records)
    conflicted_by = conflicted_by_index(records)
    # GOAL-20261012-063 EC-02：**已消解的那一对不再算作反向冲突**（先扣后判）——
    # 与 `conflicted_by_index` **同一手法**（同族的第三个实例）。
    resolved = resolved_pair_index(records)
    return [
        _memory_row(
            record,
            moment,
            _RowFacts(
                superseded_by=reverse.get(str(record.id), []),
                terminal=dict(terminals.get(str(record.id)) or {}),
                conflicted_by=_unresolved_declarers(
                    str(record.id), conflicted_by.get(str(record.id), []), resolved
                ),
                resolved_with=sorted(resolved.get(str(record.id), set())),
            ),
        )
        for record in records
    ]


def _unresolved_declarers(
    record_id: str, declarers: list[str], resolved: dict[str, set[str]]
) -> list[str]:
    """扣掉**已与它消解**的声明方（**逐对**；只消解一对 ⇒ 其余仍算数）。

    `declarers` = 声明了与**本记录**冲突的那些 id；`resolved[record_id]` = **已经与
    本记录消解**过的那些 id（反向表按**被消解方**索引、值是**记载方**）
    ⇒ 只留差集。**空 ⇒ 空**（缺省形态逐字不变）。

    **为什么逐对**：一条记录可以同时被多个人声明冲突 ⇒ 扣掉「声明方 A 与我消解的那一对」
    **不**等于「我这边的冲突都没了」（其余声明方仍在）。
    """
    if not declarers:
        return []
    settled = resolved.get(record_id, set())
    return [item for item in declarers if item not in settled]


@dataclass(frozen=True, slots=True)
class _RowFacts:
    """一条记录投影所需的**同批事实**（合成一个参数对象守 `max-args` 门）。

    四件都**不**来自记录自身（由调用方按同一批记录算出来）：反向取代 / 链终点 /
    反向冲突（已扣消解）/ 已消解的声明方。
    """

    superseded_by: list[str] = field(default_factory=list)
    terminal: dict[str, object] = field(default_factory=dict)
    conflicted_by: list[str] = field(default_factory=list)
    resolved_with: list[str] = field(default_factory=list)


def _memory_row(
    record: Any, moment: Timestamp, facts: _RowFacts | None = None
) -> dict[str, object]:
    """一条记忆的读面投影：**身份 + 内容 + 时效 + 取代关系 + 当前版本 + 处置 + 理由**。

    `facts.superseded_by` = **谁取代了它**（反向链接）；`facts.terminal` = **链的终点**（`BB-1`）。
    两者**都必须由调用方从同一批记录算出来** —— 那是「不新增 Port 方法」的代价，
    也是本条唯一的非局部输入（见 `superseded_by_index` / `terminal_versions`）。
    """
    state = validity_at(record, moment)
    # GOAL-20261011-051 EC-02：**未消解的冲突**是一维 —— `contradictions` 非空即「有」。
    # 这里**只读声明**（不推断谁和谁冲突 —— 那是序 13 的 `W-2`，明确不做）。
    # GOAL-20261012-058 EC-03：**逐对**判冲突 —— 已消解的那些**不再计入**。
    # 既有行为逐字不变：记录**没有**消解记载 ⇒ `unresolved` == `contradictions`
    # ⇒ `conflicted` 与改动前**同值**。
    conflicted = bool(record.unresolved_conflicts)
    row = _identity_fields(record, state)
    row["supersedes"] = list(record.supersedes)
    resolved = facts or _RowFacts()
    row["superseded_by"] = list(resolved.superseded_by)
    row["conflict_resolutions"] = _resolution_face(record)
    # GOAL-20261012-061 EC-03：**冲突声明的时效**逐条披露（按**调用方给的时点**判 ——
    # 本面**不读挂钟**，与 `validity_at` 同一纪律）。未声明 ⇒ `None`（**不猜**：
    # 未声明**不得**被当成「已失效」）。声明面（谁与谁冲突 / 谁消解了哪一对）**一字不动**。
    row["conflict_timeliness"] = _conflict_timeliness_face(record, moment)
    row["terminal"] = _terminal_face(record, resolved.terminal)
    # GOAL-20261012-062 EC-02：**被别人声明冲突**（本记录自己没声明）—— 由调用方按
    # **同一批记录**算出来（`conflicted_by_index`，与 `superseded_by` **同一手法**）。
    by_others = list(resolved.conflicted_by)
    row["conflicted_by"] = by_others
    # GOAL-20261012-063 EC-03：**已与本记录消解的那些声明方**（对端可见性）——
    # `conflicted_by` 里**扣掉**的那些在这一键里逐条点名（**不静默消失**：
    # 读者要能回答「那一对是被消解了，还是从来没声明过」）。
    row["resolved_with"] = list(resolved.resolved_with)
    row["disposition"] = disposition_of(
        state,
        superseded=bool(resolved.superseded_by),
        conflicted=conflicted,
        conflicted_by=bool(by_others),
    )
    #: 理由：处置是**可复核**的，不是不透明标签。
    # GOAL-20261011-051：**冲突的处置理由由 `_reason` 自己点名**（那一支已逐字给出 id）
    # ⇒ 不再叠加 `_conflict_note`（否则同一句出现两遍）。`_conflict_note` 保留给
    # **未被 `_reason` 覆盖**的场合（见下）—— 「不是当前处置理由、但读者仍该知道有冲突」。
    row["reason"] = disposition_reason(
        state, record, superseded_by=resolved.superseded_by, conflicted_by=by_others
    )
    return row


def _selection(memory_store: Any, args: dict[str, object]) -> tuple[str | None, str | None]:
    """解析两个**可选**筛选维度（`tier` / `scope`）：缺省或空白 ⇒ `None` = 不筛。

    **范围必须先确认为已知**（`_require_known_scope`）—— 未知范围**点名拒绝**，
    不静默当成「不筛」（那会让调用方以为自己筛过了）。
    """
    raw_tier = args.get("tier")
    tier = str(raw_tier).strip() if raw_tier is not None and str(raw_tier).strip() else None
    raw_scope = args.get("scope")
    scope = str(raw_scope).strip() if raw_scope is not None and str(raw_scope).strip() else None
    if scope is not None:
        _require_known_scope(memory_store, scope)
    return tier, scope


def memory_read(memory_store: Any | None, args: dict[str, object]) -> dict[str, object]:
    """读 governed memory 并按调用方给的时点给出**时效 + 处置**。

    载荷形状（读面契约）：

    - `now`：判定时点（**回显**调用方给的值 ⇒ 可复核）；
    - `tier`：读的 tier（缺省 `None` = 全部）；
    - `memory_count`：条数；
    - `memories`：逐条（`memory_id` / `tier` / `scope` / `content` / `confidence` /
      `active` / `validity` / `disposition` / `reason`）；
    - `dispositions`：**计数摘要**（`USE` / `ANNOTATE` / `SKIP` / `SUPERSEDED` / `CONFLICTED`
      各几条 —— 供消费者不解析数组就能看出「有没有被跳过 / 被取代 / 带着冲突」）。
    """
    if memory_store is None:
        raise InvalidInputError("memory_read requires a MemoryStore, which is not in this assembly")
    moment = _moment(args)
    tier, scope = _selection(memory_store, args)
    records = memory_store.query(_tier_of(tier), scope)
    rows = _project_records(records, moment)
    counts = {
        DISPOSITION_USE: 0,
        DISPOSITION_ANNOTATE: 0,
        DISPOSITION_SKIP: 0,
        DISPOSITION_SUPERSEDED: 0,
        DISPOSITION_CONFLICTED: 0,
    }
    for row in rows:
        counts[str(row["disposition"])] += 1
    payload: dict[str, object] = {
        "now": moment.value.isoformat(),
        "tier": tier,
        "memory_count": len(rows),
        "memories": rows,
        "dispositions": counts,
    }
    # GOAL-20261010-049 EC-03：**只有传了 `scope` 才加这两键** ⇒ 缺省路径的载荷与改动前
    # **逐字相同**（既有读者看到的键一个不少、一个不多）。
    if scope is not None:
        payload["scope"] = scope
        payload["filtered_out"] = _filtered_out(memory_store, tier, scope, len(rows))
    return payload


def _filtered_out(memory_store: Any, tier: str | None, scope: str, kept: int) -> int:
    """按范围**筛掉了多少条**（同一 tier 维下、不含该范围的条数）—— **不静默丢**。

    与 `dispositions` 同一种披露形态：调用方**不解析数组**就能看出「这次读有没有发生过滤」。
    它读的是**同一份 Port**（`query`），不另开统计面。
    """
    same_tier = memory_store.query(_tier_of(tier))
    return len(same_tier) - kept


def _require_known_scope(memory_store: Any, scope: str) -> None:
    """**未知范围 ⇒ 点名**（「你要的范围不存在」与「该范围当前没有记录」是两件事）。

    实测口径（GOAL-20261010-049 EC-02）：把「该范围无记录」当成「范围非法」会让调用方
    无法区分「拼错了」与「确实还没有这个范围的记忆」；本函数**只**在**全库任何 tier 下**
    都不存在该范围时点名拒绝。
    """
    if any(record.scope == scope for record in memory_store.query()):
        return
    known = sorted({str(record.scope) for record in memory_store.query()})
    raise InvalidInputError(f"memory_read scope {scope!r} is not a known scope (known: {known})")


def _tier_of(name: str | None) -> Any | None:
    """tier 名 → 域枚举（未知名 ⇒ **点名**，不静默读全部）。"""
    if name is None:
        return None
    from packages.domain.enums import MemoryTier

    try:
        return MemoryTier(name)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in MemoryTier)
        raise InvalidInputError(
            f"memory_read tier {name!r} is not a known tier (allowed: {allowed})"
        ) from exc


#: GOAL-20261011-052：**显式再导出**应用层的处置面（两处共用同一套判定）。
#: 严格 mypy 要求「再导出必须显式声明」——否则 `attr-defined` 判红（实测）。
__all__ = [
    "DISPOSITION_ANNOTATE",
    "DISPOSITION_CONFLICTED",
    "DISPOSITION_SKIP",
    "DISPOSITION_SUPERSEDED",
    "DISPOSITION_USE",
    "disposition_of",
    "disposition_reason",
    "memory_read",
    "TERMINAL_CURRENT",
    "TERMINAL_CYCLE",
    "TERMINAL_OUT_OF_VIEW",
    "TERMINAL_SUCCEEDED",
    "superseded_by_index",
    "terminal_versions",
]
