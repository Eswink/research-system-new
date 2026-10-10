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

from datetime import datetime
from typing import Any

from packages.application.memory.validity import ValidityState, validity_at
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Timestamp

#: 处置：**四态 + 未声明** 各自的唯一取值（读面按这个字段分派，不靠措辞）。
DISPOSITION_USE = "USE"
DISPOSITION_ANNOTATE = "ANNOTATE"
DISPOSITION_SKIP = "SKIP"
#: GOAL-20261010-050 EC-03：**已取代**（`active=False` 且**被别的记录取代**）。
#: **与 `SKIP` 分开**：「已过期」是**时效**理由，「已取代」是**被新版本替代** ——
#: 两者处置都为「不适用」，但**理由与可复核依据不同**（判词必须点得出是哪一种）。
DISPOSITION_SUPERSEDED = "SUPERSEDED"

#: 时效状态 → 处置（**互不混用**：三态各归各的；`None` 见 `disposition_of`）。
_DISPOSITIONS: dict[ValidityState, str] = {
    ValidityState.EXPIRED: DISPOSITION_SKIP,
    ValidityState.REVIEW_DUE: DISPOSITION_ANNOTATE,
}


def disposition_of(state: ValidityState | None, *, superseded: bool = False) -> str:
    """时效状态 → **处置**（纯函数；`None` = 未声明或未到 ⇒ 照用，**不猜**）。

    GOAL-20261010-050 EC-03：**已取代**是**第四个**不适用理由 —— 它**不看时效**（一条
    未声明时效的被取代记忆，此前会报 `USE` = 「照用」，那是把**已被替代**的知识当成现行知识）。

    优先级**固定**（与判据同源）：`已取代` **先于** 时效 —— 因为「这条已经不是当前版本」
    比「这条过期没有」更根本；**已过期且已取代** ⇒ 报 `SUPERSEDED` 且理由**同时点名两者**
    （见 `_reason`）。**`superseded=False`（缺省）⇒ 与改动前逐字相同**。
    """
    if superseded:
        return DISPOSITION_SUPERSEDED
    if state is None:
        return DISPOSITION_USE
    return _DISPOSITIONS[state]


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


def _memory_row(
    record: Any, moment: Timestamp, superseded_by: list[str] | None = None
) -> dict[str, object]:
    """一条记忆的读面投影：**身份 + 内容 + 时效 + 取代关系 + 处置 + 理由**（逐条点名）。

    `superseded_by` = **谁取代了它**（反向链接）。它**必须由调用方从同一批记录算出来**
    —— 那是「不新增 Port 方法」的代价，也是本条唯一的非局部输入（见 `_reverse_links`）。
    """
    state = validity_at(record, moment)
    superseded = bool(superseded_by)
    disposition = disposition_of(state, superseded=superseded)
    content = str(record.content)
    return {
        "memory_id": str(record.id),
        "tier": str(record.tier),
        "scope": str(record.scope),
        "content": content,
        "confidence": float(record.confidence),
        "active": bool(record.active),
        # GOAL-20261010-045 EC-03：**冲突声明**与**生效起点**逐条披露。
        # 为什么在读面上（而不只塞进判词）：读面是消费者唯一能自己回答「这条记忆与谁冲突」的地方；
        # 判词只覆盖「本研究路径关心的那一条」，读面覆盖全部（两者**不互相顶替**）。
        "contradictions": list(record.contradictions),
        "valid_from": (
            record.valid_from.value.isoformat() if record.valid_from is not None else None
        ),
        #: 时效状态（`None` = 未声明或未到 —— **不猜**，与「已到期」严格区分）。
        "validity": state.value if state is not None else None,
        # GOAL-20261010-050 EC-02：**取代关系两个方向都披露**（`[]` = 无关系 —— 是**声明性**的
        # 值而不是缺字段；与「缺字段点名」的既有纪律一致）。读者据此能回答
        # 「这条被谁取代 / 它取代了谁」，而不必自己去比对 id 列表。
        "supersedes": list(record.supersedes),
        "superseded_by": list(superseded_by or ()),
        #: 处置（供研究循环**按它分派**：`SKIP` / `ANNOTATE` / `USE` / `SUPERSEDED`）。
        "disposition": disposition,
        #: 理由：处置是**可复核**的，不是不透明标签。
        "reason": _reason(state, record, superseded_by=superseded_by) + _conflict_note(record),
    }


def _reason(
    state: ValidityState | None, record: Any, superseded_by: list[str] | None = None
) -> str:
    """处置理由（点名状态与**被引的声明值** —— 读面原文，不重算）。

    GOAL-20261010-050：**已取代**与**已过期**是**两种**不适用理由，判词必须点得出是哪一种
    （`已取代` 优先，且已过期时**两者都点名** —— 读者要能一次看全）。
    """
    superseded = list(superseded_by or ())
    if superseded:
        note = f"被 {','.join(superseded)} 取代 ⇒ 已不是当前版本（不照用）"
        if state is ValidityState.EXPIRED:
            return note + f"；**并且** expires_at={record.expires_at.value.isoformat()} 已过"
        if state is ValidityState.REVIEW_DUE:
            return note + f"；**并且** review_after={record.review_after.value.isoformat()} 已到"
        return note
    if state is ValidityState.EXPIRED:
        return f"expires_at={record.expires_at.value.isoformat()} 已过 ⇒ 跳过（不参与后续行为）"
    if state is ValidityState.REVIEW_DUE:
        return f"review_after={record.review_after.value.isoformat()} 已到 ⇒ 标注（仍需复核）"
    return "未声明时效或未到 ⇒ 照用（未声明不得被当成已到期）"


def _reverse_links(records: tuple[Any, ...]) -> dict[str, list[str]]:
    """反向链接表（`被取代的 id → [取代它的 id, …]`）—— **只从同一批记录算**，不新增 Port 方法。

    「谁取代了我」在记录自身**读不到**（正向链接写在**新**记录上）⇒ 必须扫一遍同批记录。
    只报**直接**链接（**不**做传递闭包 —— 那是本 GOAL 明确不做的 `BB-1`）。
    """
    reverse: dict[str, list[str]] = {}
    for record in records:
        for old_id in record.supersedes:
            reverse.setdefault(str(old_id), []).append(str(record.id))
    return reverse


def _conflict_note(record: Any) -> str:
    """冲突声明的**点名**句（空列表 ⇒ 不追加任何文字 —— **不**凭空说「有冲突」）。

    `[]` 与 `None` 的语义**互不混用**：`[]` = 已判定**无**冲突（本条不追加）；
    「未声明」在域上不存在第三种取值（缺省即 `[]`）⇒ 读面不给「未知」态，**不猜**。
    """
    conflicts = list(record.contradictions)
    if not conflicts:
        return ""
    return f"；**声明与 {','.join(conflicts)} 冲突**（点名，未自动消解）"


def memory_read(memory_store: Any | None, args: dict[str, object]) -> dict[str, object]:
    """读 governed memory 并按调用方给的时点给出**时效 + 处置**。

    载荷形状（读面契约）：

    - `now`：判定时点（**回显**调用方给的值 ⇒ 可复核）；
    - `tier`：读的 tier（缺省 `None` = 全部）；
    - `memory_count`：条数；
    - `memories`：逐条（`memory_id` / `tier` / `scope` / `content` / `confidence` /
      `active` / `validity` / `disposition` / `reason`）；
    - `dispositions`：**计数摘要**（`USE` / `ANNOTATE` / `SKIP` / `SUPERSEDED` 各几条 ——
      供消费者不解析数组就能看出「有没有被跳过 / 有没有被取代」）。
    """
    if memory_store is None:
        raise InvalidInputError("memory_read requires a MemoryStore, which is not in this assembly")
    moment = _moment(args)
    raw_tier = args.get("tier")
    tier = str(raw_tier).strip() if raw_tier is not None and str(raw_tier).strip() else None
    raw_scope = args.get("scope")
    scope = str(raw_scope).strip() if raw_scope is not None and str(raw_scope).strip() else None
    if scope is not None:
        _require_known_scope(memory_store, scope)
    records = memory_store.query(_tier_of(tier), scope)
    # GOAL-20261010-050 EC-02：反向链接从**同一批记录**算一次（不新增 Port 方法、
    # 不逐条再查 —— 那是 N+1 次查询，且会在两处看到不同的世界）。
    reverse = _reverse_links(records)
    rows = [_memory_row(record, moment, reverse.get(str(record.id), [])) for record in records]
    counts = {
        DISPOSITION_USE: 0,
        DISPOSITION_ANNOTATE: 0,
        DISPOSITION_SKIP: 0,
        DISPOSITION_SUPERSEDED: 0,
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
