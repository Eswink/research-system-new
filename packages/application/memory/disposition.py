"""记忆的**处置判定**（GOAL-20261009-042 / 050 / 051 / 052）。

**为什么在应用层**：这套判定被**两个读面**共用 —— 编排消费面（`adapters/canonical/memory_read.py`）
与 HTTP 读面（`services/api/routers/memory.py`）。HTTP 面**不得** import 具体适配器
（`.importlinter.api` 的契约：`services.api.routers is not allowed to import adapters`），
而它可以 import `packages.application.*` ⇒ 共用判定**必须**落在这一层。

**为什么是纯函数**：判定必须**可复现**（时点由调用方给，**不读挂钟**）；
且两个读面**不许各写一套**（两处各写一套 = 漂移无从发现）。

**五态互不混用**（`USE` / `ANNOTATE` / `SKIP` / `SUPERSEDED` / `CONFLICTED`），
优先级**固定**（从根本到表层）：已取代 > 已过期 > 有冲突 > 待复核 > 照用。
"""

from __future__ import annotations

from typing import Any

from packages.application.memory.validity import ValidityState

#: 处置：**五态 + 未声明** 各自的唯一取值（读面按这个字段分派，不靠措辞）。
DISPOSITION_USE = "USE"
DISPOSITION_ANNOTATE = "ANNOTATE"
DISPOSITION_SKIP = "SKIP"
#: GOAL-20261010-050 EC-03：**已取代**（`active=False` 且**被别的记录取代**）。
#: **与 `SKIP` 分开**：「已过期」是**时效**理由，「已取代」是**被新版本替代** ——
#: 两者处置都为「不适用」，但**理由与可复核依据不同**（判词必须点得出是哪一种）。
DISPOSITION_SUPERSEDED = "SUPERSEDED"
#: GOAL-20261011-051 EC-02：**带着未消解的冲突**。
#: **与 `ANNOTATE`（待复核）分开**：待复核是**时效**上的「该看了」，冲突是**内容**上的
#: 「这条与另一条说法不一致」—— 两者**处置同类**（执行但带标注）但**理由与可复核依据不同**
#: （判词必须点得出是哪一种，并**点名**冲突的 id）。
DISPOSITION_CONFLICTED = "CONFLICTED"

#: 时效状态 → 处置（**互不混用**：三态各归各的；`None` 见 `disposition_of`）。
_DISPOSITIONS: dict[ValidityState, str] = {
    ValidityState.EXPIRED: DISPOSITION_SKIP,
    ValidityState.REVIEW_DUE: DISPOSITION_ANNOTATE,
}


def disposition_of(
    state: ValidityState | None, *, superseded: bool = False, conflicted: bool = False
) -> str:
    """时效状态 → **处置**（纯函数；`None` = 未声明或未到 ⇒ 照用，**不猜**）。

    GOAL-20261010-050 EC-03：**已取代**是**第四个**不适用理由 —— 它**不看时效**（一条
    未声明时效的被取代记忆，此前会报 `USE` = 「照用」，那是把**已被替代**的知识当成现行知识）。

    GOAL-20261011-051 EC-02：**带着未消解的冲突**是**第五个** —— 同样**不看时效**
    （一条未声明时效的冲突记录，此前也会报 `USE`）。

    优先级**固定**（与判据同源，**四件事**从根本到表层）：

    1. `已取代` —— 「这条**已经不是当前版本**」最根本；
    2. `已过期` —— 时效上**已失效**（不再适用）；
    3. `有冲突` —— 内容上**有未消解的分歧**（可用，但要人看）；
    4. `待复核` —— 时效上**该看了**；
    5. 否则 `USE`。

    **顺序的实证**：`已取代` 与 `有冲突` **并存**时以**取代**为先 —— 一条已被替代的记录，
    「谁和它冲突」已无实际意义（它的去留已定）；而 `已过期` 与 `有冲突` 并存时以**过期**为先，
    因为「不参与后续行为」比「要人看」更彻底。**两个缺省参数都为 `False` ⇒ 与改动前逐字相同**。
    """
    if superseded:
        return DISPOSITION_SUPERSEDED
    if state is ValidityState.EXPIRED:
        return DISPOSITION_SKIP
    if conflicted:
        return DISPOSITION_CONFLICTED
    if state is None:
        return DISPOSITION_USE
    return _DISPOSITIONS[state]


def disposition_reason(
    state: ValidityState | None, record: Any, superseded_by: list[str] | None = None
) -> str:
    """处置理由（点名状态与**被引的声明值** —— 读面原文，不重算）+ 冲突补充点名。

    GOAL-20261010-050：**已取代**与**已过期**是**两种**不适用理由，判词必须点得出是哪一种
    （`已取代` 优先，且已过期时**两者都点名** —— 读者要能一次看全）。

    GOAL-20261011-051：**冲突**在它是**处置理由**时由本函数自己点名（不叠加，避免重复）；
    **其余分支**（已取代 / 待复核 / 照用）仍应让读者看见冲突 ⇒ 由 `_extra_conflict_note` 补上
    —— 「处置理由」与「读者可见信息」的**分离**：两者都不省，也都不重复。
    """
    note = _reason(state, record, superseded_by=superseded_by)
    return note + _extra_conflict_note(state, record)


def _reason(
    state: ValidityState | None, record: Any, superseded_by: list[str] | None = None
) -> str:
    superseded = list(superseded_by or ())
    conflicts = list(record.contradictions)
    if superseded:
        note = f"被 {','.join(superseded)} 取代 ⇒ 已不是当前版本（不照用）"
        if state is ValidityState.EXPIRED:
            return note + f"；**并且** expires_at={record.expires_at.value.isoformat()} 已过"
        if state is ValidityState.REVIEW_DUE:
            return note + f"；**并且** review_after={record.review_after.value.isoformat()} 已到"
        return note
    if state is ValidityState.EXPIRED:
        # 过期**先于**冲突（「不参与后续行为」比「要人看」更彻底）；仍点名冲突（读者要能看全）。
        note = f"expires_at={record.expires_at.value.isoformat()} 已过 ⇒ 跳过（不参与后续行为）"
        if conflicts:
            return note + f"；**并且** 声明与 {','.join(conflicts)} 冲突（未消解）"
        return note
    if conflicts:
        return f"声明与 {','.join(conflicts)} 冲突 ⇒ **有未消解的分歧**（照用但标注，未自动消解）"
    if state is ValidityState.REVIEW_DUE:
        return f"review_after={record.review_after.value.isoformat()} 已到 ⇒ 标注（仍需复核）"
    return "未声明时效或未到 ⇒ 照用（未声明不得被当成已到期）"


def superseded_by_index(records: tuple[Any, ...]) -> dict[str, list[str]]:
    """反向链接表（`被取代的 id → [取代它的 id, …]`）—— **只从同一批记录算**，不新增 Port 方法。

    「谁取代了我」在记录自身**读不到**（正向链接写在**新**记录上）⇒ 必须扫一遍同批记录。
    只报**直接**链接（**不**做传递闭包 —— 那是 `BB-1`，明确不做）。
    """
    reverse: dict[str, list[str]] = {}
    for record in records:
        for old_id in record.supersedes:
            reverse.setdefault(str(old_id), []).append(str(record.id))
    return reverse


def _extra_conflict_note(state: ValidityState | None, record: Any) -> str:
    """**仅在处置理由没有覆盖冲突时**追加点名（否则会重复同一句）。"""
    if not record.contradictions:
        return ""
    if state is ValidityState.EXPIRED:
        return ""  # 那一支已点名
    if disposition_of(state, conflicted=True) == DISPOSITION_CONFLICTED:
        return ""  # 冲突本身就是处置理由 ⇒ 已点名
    return _conflict_note(record)


def _conflict_note(record: Any) -> str:
    """冲突声明的**点名**句（空列表 ⇒ 不追加任何文字 —— **不**凭空说「有冲突」）。

    `[]` 与 `None` 的语义**互不混用**：`[]` = 已判定**无**冲突（本条不追加）；
    「未声明」在域上不存在第三种取值（缺省即 `[]`）⇒ 读面不给「未知」态，**不猜**。
    """
    conflicts = list(record.contradictions)
    if not conflicts:
        return ""
    return f"；**声明与 {','.join(conflicts)} 冲突**（点名，未自动消解）"


__all__ = [
    "DISPOSITION_ANNOTATE",
    "DISPOSITION_CONFLICTED",
    "DISPOSITION_SKIP",
    "DISPOSITION_SUPERSEDED",
    "DISPOSITION_USE",
    "disposition_of",
    "disposition_reason",
    "superseded_by_index",
]
