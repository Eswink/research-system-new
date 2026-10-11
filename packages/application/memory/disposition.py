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
    只报**直接**链接（**不**做传递闭包 —— 传递闭包见 `terminal_versions`：那条**另成事实**
    而不是把本函数的语义改掉，因为本函数的两个既有键语义必须**逐字保持**）。
    """
    reverse: dict[str, list[str]] = {}
    for record in records:
        for old_id in record.supersedes:
            reverse.setdefault(str(old_id), []).append(str(record.id))
    return reverse


#: 链终点的**四种形态**（互不混用；都**点名**，**不**静默）。
#: - `CURRENT`：本条**没有**后继 ⇒ 它**就是**当前版本；
#: - `SUCCEEDED`：本条有后继且链**有终点** ⇒ 终点是 `terminal` 点名的那些 id；
#: - `CYCLE`：链上有**环**（含自指）⇒ **点名**环上的 id，**不**无限追链、**不**静默截断；
#: - `OUT_OF_VIEW`：本条 `active=False`（**已不生效**）却在这批里**看不到**有任何后继
#:   ⇒ **看不见 ≠ 不存在**：它的后继可能在**本批查询范围之外**（比如按 `scope` 筛过，
#:   或已被删除）⇒ **点名**这件事，**不**报 `CURRENT` 假装它是当前版本
#:   （承 AGENTS.md 的「点名而非静默降级」；实测形态：跨 scope 时
#:   「全部」视角报 `SUCCEEDED`、按 scope 筛的视角**看不见**那条 ⇒ 旧口径会把它读成当前版本）。
TERMINAL_CURRENT = "CURRENT"
TERMINAL_SUCCEEDED = "SUCCEEDED"
TERMINAL_CYCLE = "CYCLE"
TERMINAL_OUT_OF_VIEW = "OUT_OF_VIEW"


def _successors(records: tuple[Any, ...]) -> dict[str, list[str]]:
    """直接后继表（**有序、去重**）—— 与 `superseded_by_index` **同一份事实**的另一种索引。

    两者都从 `record.supersedes` 读，**不**各自定义「谁取代了谁」；差别只在键的方向与
    是否展开到链终点。`superseded_by_index` 的返回值（既有键）**一字不改**。
    """
    successors: dict[str, list[str]] = {}
    for record in records:
        for old_id in record.supersedes:
            bucket = successors.setdefault(str(old_id), [])
            if str(record.id) not in bucket:
                bucket.append(str(record.id))
    return successors


def terminal_versions(records: tuple[Any, ...]) -> dict[str, dict[str, Any]]:
    """每条记录的**链终点**（`BB-1` / GOAL-20261011-053）：`id → 四态 + 终点 id 列表`。

    **为什么需要**：`superseded_by` 只报**直接**后继 ⇒ 在 A ⊂ B ⊂ C 链上，A 的链接指向的
    B **自己可能已经被取代**（`active=False`）⇒ 读者按链接找到的「替代品」**可能是死的**，
    而「**当前**版本是哪条」这件事在载荷里**没有字段**能回答（要自己追链）。

    **返回形态**（每条记录都有条目 —— **不**用「键缺失」表达「没有终点」）：

    - `{"state": CURRENT, "terminal": [自身 id]}`：**无后继** ⇒ 它就是当前版本；
    - `{"state": SUCCEEDED, "terminal": [...]}`：沿直接后继**走到没有后继**的那些记录；
    - `{"state": CYCLE, "terminal": [...]}`：追链时**回到已访问的 id**（含自指）⇒
      点名**环上的 id**（**不**返回一个假装是终点的值、**不**无限循环）；
    - `{"state": DANGLING, "terminal": [...]}`：后继 id **不在本批记录里** ⇒ 点名那些 id
      （**看不见 / 未判定，一律点名** —— 不静默当成「已到终点」）。

    **为什么不是「传递闭包」**：两者问的不是同一件事。闭包回答「**所有**（直接 + 间接）后继是谁」；
    本函数回答「**现在**的版本是哪条」—— 前者是集合，后者是**一条可判定的读数**（链的终点）。
    这也是本条与 `CC-*`（冲突消解）的边界：本函数**只读**声明，**不**判定谁对谁错。

    **纯函数**：只读入参那批记录，**不**查 store、**不**读挂钟（可复现）。
    """
    by_id = {str(record.id): record for record in records}
    successors = _successors(records)
    out: dict[str, dict[str, Any]] = {}
    for record in records:
        start = str(record.id)
        out[start] = _walk_to_terminal(start, successors, by_id)
    return out


def _walk_to_terminal(
    start: str, successors: dict[str, list[str]], by_id: dict[str, Any]
) -> dict[str, Any]:
    """从 `start` 沿直接后继走到**所有没有后继的记录**；环与「后继看不见」**点名**。

    **分支要全走**：「被两条取代」是可能的（A 同时被 B 与 C 取代）⇒ **不**取第一个就返回，
    而是把每条支路的终点都收进来（并存的多个当前版本要**逐个点名**）。

    **环与菱形必须分开**（实测踩到）：只有「回到**当前路径上**的 id」才是环；
    「汇合到**已走完**的 id」是菱形（A→B→D 与 A→C→D）⇒ 那**不是**环、不该报 `CYCLE`。
    所以用 DFS 三色（在路径上 / 已走完 / 未访问），**不**用「见过的集合」当环判据。
    """
    on_path: list[str] = []
    on_path_set: set[str] = set()
    settled: set[str] = set()
    terminals: list[str] = []
    stack: list[tuple[str, bool]] = [(start, False)]
    while stack:
        node, leaving = stack.pop()
        if leaving:
            on_path.pop()
            on_path_set.discard(node)
            settled.add(node)
            if node != start and not successors.get(node):
                terminals.append(node)  # 支路走到头 ⇒ 它是当前版本之一
            continue
        if node in settled:
            continue  # 菱形汇合：这条支路已经走过（**不是**环）
        if node in on_path_set:
            return {"state": TERMINAL_CYCLE, "terminal": on_path[on_path.index(node) :]}
        on_path.append(node)
        on_path_set.add(node)
        stack.append((node, True))
        for following in reversed(successors.get(node, [])):
            stack.append((following, False))
    if terminals:
        return {"state": TERMINAL_SUCCEEDED, "terminal": terminals}
    # 走到这里 = **本批里看不到任何后继**。此时分两种**互不混用**的情形：
    #   - 记录**仍生效**（`active=True`）⇒ 它**就是**当前版本（`CURRENT`）；
    #   - 记录**已不生效**（`active=False`）⇒ 它**曾经被取代过**，只是取代它的那条
    #     **不在本批**（跨 scope / 已删除）⇒ **点名**「后继看不见」，**不**假装它是当前版本。
    # 这一支是**实测**出来的（跨 scope：两条记录都在库、按 scope 筛后只看得到被取代的那条）。
    if not bool(by_id[start].active):
        return {"state": TERMINAL_OUT_OF_VIEW, "terminal": []}
    return {"state": TERMINAL_CURRENT, "terminal": [start]}


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
    "TERMINAL_CURRENT",
    "TERMINAL_CYCLE",
    "TERMINAL_OUT_OF_VIEW",
    "TERMINAL_SUCCEEDED",
    "disposition_of",
    "disposition_reason",
    "superseded_by_index",
    "terminal_versions",
]
