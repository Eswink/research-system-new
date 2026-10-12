"""Memory 控制面 DTO（PLAN-20260910-037 WP-F）。

诚实语义：提案经完整 §8 门链后直接提交（accepted）或以 stage+reasons
分类拒绝（422）；域内没有持久化 pending 状态，因此不提供两阶段 decide。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MemoryRecordDto(BaseModel):
    id: str
    tier: str
    kind: str
    content: str
    provenance: str
    confidence: float
    # GOAL-20261008-039 EC-02：适用范围（AGENTS.md §8「有适用范围」的可判定形态）。
    scope: str = "project"
    valid_from: str | None = None
    review_after: str | None = None
    expires_at: str | None = None
    supersedes: list[str] = Field(default_factory=list)
    active: bool
    # GOAL-20261008-039 EC-04：**给定时点上的时效判定**（`EXPIRED` / `REVIEW_DUE` / None）。
    # 只有显式给 `at` 的路由才填它 —— 不给时点的读面**不猜**（`None` = 未判定）。
    validity: str | None = None
    # GOAL-20261011-052 EC-02：**与编排消费面（`memory.read`）对齐的四样** ——
    # 此前只有编排面能判定这些事实（冲突 / 反向取代 / 处置 / 理由），HTTP 面**完全看不见**
    # ⇒ 同一份 canonical 事实在两条读路径上**可判定性不同**。
    # **都是附加**：既有 13 字段一个不改名、不改语义；四处取值**复用**编排面的同一批纯函数
    # （`disposition_of` / `_reason` / `_reverse_links`）⇒ 两处**同源同值**。
    contradictions: list[str] = Field(default_factory=list)
    superseded_by: list[str] = Field(default_factory=list)
    #: 处置（五态之一：`USE` / `ANNOTATE` / `SKIP` / `SUPERSEDED` / `CONFLICTED`）。
    disposition: str = ""
    #: 处置理由（**逐字**与编排面同源；可复核，不是不透明标签）。
    reason: str = ""
    # GOAL-20261011-053 EC-02（`BB-1`）：**链的终点**（与编排面**同源同值**）。
    # 光有 `superseded_by`（**直接**链接）答不出「**现在**的版本是哪条」：在 A ⊂ B ⊂ C 上，
    # A 的链接指向的 B **自己可能已被取代** ⇒ 读者要么自己追链、要么被误导。
    # `terminal_state` 四态互不混用（`CURRENT` / `SUCCEEDED` / `CYCLE` / `DANGLING`）；
    # `terminal_ids` **点名**终点 —— 环与悬空后继都点名，**不**静默（承本 GOAL 的禁令）。
    terminal_state: str = ""
    terminal_ids: list[str] = Field(default_factory=list)
    # GOAL-20261012-058 EC-03：**冲突消解**逐对披露（与编排面**同源同值**）。
    # 未消解 ⇒ 空列表 ⇒ 处置仍是 `CONFLICTED`（既有行为逐字不变）。
    conflict_resolutions: list[MemoryConflictResolutionDto] = Field(default_factory=list)
    #: GOAL-20261012-062 EC-03：**被别人声明冲突**的 id 列表（本记录自己**没有**声明、
    #: 但别的记录声明了与它冲突）。与 `contradictions`（**正向**）**互不顶替** ——
    #: 两者都要读得出（缺省 `[]` ⇒ 没有任何反向声明 ⇒ 与改动前逐字相同）。
    conflicted_by: list[str] = Field(default_factory=list)
    #: GOAL-20261012-065 EC-03：**提议者**（谁把这条知识记下来）—— 与 `provenance`
    #: （**来源**）**互不顶替**。缺省 `None` ⇒ 未声明（既有记录读出同一语义）。
    proposed_by: str | None = None
    #: GOAL-20261012-064 EC-03：**悬空引用**（本批里找不到的被引 id）—— 两个方向**各自点名**：
    #: 一条记录的「来源可查」在**删除之后**不该静默失效（写面对未知 id 是拒提交的）。
    #: 缺省 `[]` ⇒ 没有悬空引用 ⇒ 与改动前逐字相同。
    dangling_supersedes: list[str] = Field(default_factory=list)
    dangling_contradictions: list[str] = Field(default_factory=list)
    #: GOAL-20261012-063 EC-03：**已与本记录消解的那些声明方** —— 对端可见性；
    #: `conflicted_by` 里**扣掉**的那些在这里逐条点名（**不静默消失**）。
    #: 缺省 `[]` ⇒ 没有任何消解记载 ⇒ 与改动前逐字相同。
    resolved_with: list[str] = Field(default_factory=list)
    #: GOAL-20261012-061 EC-03：**冲突声明的时效**（`STALE` / `REVIEW_DUE` / `None`）——
    #: 与 `validity`（**记录**的时效）**互不顶替**（两件事：这条记忆过期了吗 / 当年声明的
    #: 那个分歧还算不算数）。**只在给了时点时**判（不给 ⇒ `None` = 未判定，**不猜**）。
    conflict_timeliness: str | None = None


class MemoryConflictResolutionDto(BaseModel):
    """一条**冲突消解**的记载（GOAL-20261012-058 EC-03；**与编排面同源同值**）。"""

    other_id: str
    resolved_by: str
    resolved_at: str


class MemoryListViewDto(BaseModel):
    """项目内记忆清单（**缺省形态**：逐条记录 + 诚实边界说明）。

    GOAL-20261010-049：**按范围筛**是**另一个**形态 —— 见 `MemoryFilteredListViewDto`。
    分成两个 DTO 而不是给本模型加两个可空字段，是因为 pydantic 的响应模型会**把 `None`
    序列化成 `null`**、键仍在 ⇒ 既有读者会凭空多看到两个键（实测过）。两个形态各自
    **显式**声明自己的键，schema 与载荷一致。
    """

    records: list[MemoryRecordDto] = Field(default_factory=list)
    scope_note: str


class MemoryFilteredListViewDto(MemoryListViewDto):
    """按某个维度筛过的清单（在缺省形态上**追加**键：筛了什么与**筛掉了多少条**）。

    `filtered_out` 与 `dispositions` 同一披露形态：调用方**不解析数组**就知道这次读
    有没有发生过滤。**不静默丢**：筛掉的条数是必报项。

    GOAL-20261013-067 EC-03：本形态**扩到两个维度**（`scope` / `proposed_by`）——
    `scope` 仍必报（序 17 的既有语义**逐字保持**），`proposed_by` **只在这一维被筛时**出现
    （作者维的**专用形态**见 `MemoryAuthoredListViewDto`，两者**互斥**：一次只筛一维）。
    """

    scope: str | None = None
    filtered_out: int


class MemoryAuthoredListViewDto(MemoryListViewDto):
    """按**作者**筛过的清单（GOAL-20261013-067 EC-03）—— 与本轮之前的 `scope` 形态
    **同一手法**（缺省形态 + 追加键），**不**给路由开 `response_model_exclude_none`
    （那会连嵌套模型一起递归抹掉别的读面上有意义的 `null` —— 序 17 实测过）。
    """

    proposed_by: str
    filtered_out: int


class MemoryProposalDto(BaseModel):
    tier: str = Field(min_length=1, max_length=40)
    kind: str = Field(min_length=1, max_length=40)
    content: str = Field(min_length=1, max_length=8000)
    provenance: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0.0, le=1.0)
    supersedes: list[str] = Field(default_factory=list)
    proposed_by: str | None = Field(default=None, max_length=200)
    curator_approved: bool = False


class MemoryCommittedDto(BaseModel):
    record: MemoryRecordDto
    decision: str


class MemoryValidityDto(BaseModel):
    """一条记忆在**给定时点**上的时效（GOAL-20261008-039 EC-04）。

    时点由调用方给（`at`）⇒ 同一份数据同一时点判定必相同（可复现；**不读挂钟**）。
    """

    id: str
    scope: str
    review_after: str | None = None
    expires_at: str | None = None
    validity: str | None = None


class MemoryValidityViewDto(BaseModel):
    """按显式时点的时效读面（逐条给判定 + 原始两时点）。"""

    at: str
    records: list[MemoryValidityDto] = Field(default_factory=list)
    scope_note: str
