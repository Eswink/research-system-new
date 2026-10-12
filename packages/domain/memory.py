"""Memory / Context 域实体定义。

来源：docs/architecture/CONTEXT_ENGINE.md。
Memory 写入必须经过 MemoryWriteProposal → schema → provenance → policy → gate
（AGENTS.md §8）。向量索引是 derived，不是 canonical。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType


@dataclass(frozen=True, slots=True)
class ConflictResolution:
    """**一条冲突消解的记载**（GOAL-20261012-058 EC-02）。

    **为什么是独立记载而不是改声明**：`contradictions` 是**历史事实**（那条记录曾经声明过
    与谁冲突 —— 序 22 让这件事可查）；「这个分歧被谁在何时消解了」是**另一件事**。
    把两者混成一件事会让「曾经有过这个分歧」消失 ⇒ **声明一字不动**，消解另记。

    **为什么记「哪一对」**：一条记录可以声明**多个**冲突（`contradictions` 是列表）⇒
    只能**逐对**消解。「消解了 A↔B 这一对」比「这条无冲突了」精确 —— 后者会把其余
    未消解的对一起抹掉。
    """

    other_id: str
    resolved_by: str
    resolved_at: Timestamp


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    id: str
    tier: MemoryTier
    kind: MemoryType
    content: str
    provenance: str
    confidence: float
    # GOAL-20261008-039 EC-02：**适用范围**（AGENTS.md §8 要求「有适用范围」）。
    # 缺省 `"project"` ⇒ 既有记录读出同一语义（迁移只加列 + 缺省回填，不改既有行语义）。
    scope: str = "project"
    valid_from: Timestamp | None = None
    review_after: Timestamp | None = None
    expires_at: Timestamp | None = None
    supersedes: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    # GOAL-20261012-058 EC-02：**逐对的消解记载**（缺省空列表 = **一对都没消解**
    # ⇒ 既有行为**逐字不变**：未消解 ⇒ 读面仍报 `CONFLICTED`）。
    resolutions: list[ConflictResolution] = field(default_factory=list)
    # GOAL-20261012-065 EC-02：**提议者**（可选；缺省 `None` = **未声明**
    # ⇒ 既有记录读出**同值**）。由**提案面既有的** `proposed_by` 原样带进 canonical
    # （**不**新造第二个作者字段：同一个概念只应有一个声明点）。
    # **与 `provenance` 是两件事**：`provenance` 是**来源**（这条知识从哪来），
    # `proposed_by` 是**谁提议**把它记下来 —— 两者各自独立、互不顶替。
    # **不是 ACL**（与 `scope` 的边界同形）：它只回答「是谁」，不授权任何访问。
    proposed_by: str | None = None
    # GOAL-20261012-061 EC-02：**冲突声明的时效**（可选；缺省 `None` = **未声明**
    # ⇒ 既有行为**逐字不变**：冲突照旧永久算数）。
    # 语义与记忆自身的时效**同一纪律**（`review_after` 到点 ⇒ 该复核；`expires_at` 到点
    # ⇒ 过期）—— 但它说的是**冲突声明本身**还算不算数：一条三年前记录的冲突声明，
    # 与今天声明的**同处置**（都 `CONFLICTED`）是不对称的。
    # **不**自动消解 / **不**自动失效：到点**只点名**（决定权仍在**人**）。
    conflict_review_after: Timestamp | None = None
    conflict_expires_at: Timestamp | None = None
    active: bool = True

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("memory id must not be empty")
        if not self.content:
            raise ValueError("memory content must not be empty")
        if not self.provenance:
            raise ValueError("memory provenance must not be empty")
        if not self.scope:
            raise ValueError("memory scope must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        _validate_resolutions(self)
        _validate_conflict_timeliness(self)

    @property
    def unresolved_conflicts(self) -> list[str]:
        """**尚未消解**的冲突 id（**逐对**判 —— 已消解的那些不再计入）。

        **为什么逐对判**：一条记录可以声明**多个**冲突，只消解其中一个**不等于**「无冲突」。
        读面与处置面都按这里返回的集合分派 ⇒ 两处**同源**。
        """
        settled = {item.other_id for item in self.resolutions}
        return [item for item in self.contradictions if item not in settled]


def _validate_conflict_timeliness(record: MemoryRecord) -> None:
    """**冲突时效**的校验（GOAL-20261012-061 EC-02）—— 坏形态**点名拒绝**。

    两件（与记忆自身的时效**同一纪律**，见 `validity.py` 的 `expires_at` 优先）：

    - **时效不许空转**：声明了时效**却没有任何冲突** ⇒ 点名拒绝 —— 否则
      「我声明了冲突时效但永远不生效」（`contradictions` 是空的）会变成看不见的故障；
    - **互斥的先后**：`conflict_expires_at` **早于** `conflict_review_after` ⇒ 点名拒绝
      （那样「该复核」永远不会到来 —— 过期已把它们都盖住了；与 `validity_at` 里
      「过期是更强的状态」同一口径，但**声明期**就该拒绝这种不可能的组合）。
    """
    review_after = record.conflict_review_after
    expires_at = record.conflict_expires_at
    if (review_after is not None or expires_at is not None) and not record.contradictions:
        raise ValueError(
            "conflict timeliness declared but the record declares no contradictions"
            " (nothing would ever become due)"
        )
    if (
        review_after is not None
        and expires_at is not None
        and expires_at.value < review_after.value
    ):
        raise ValueError(
            "conflict_expires_at must not precede conflict_review_after"
            f" (got expires_at={expires_at.value.isoformat()},"
            f" review_after={review_after.value.isoformat()})"
        )


def _validate_resolutions(record: MemoryRecord) -> None:
    """**消解记载**的校验（GOAL-20261012-058 EC-02）—— 四种坏形态**逐条点名**。

    - **未知冲突对**（`other_id` **不在** `contradictions` 里）：消解记载与声明**脱钩**
      ⇒ 点名拒绝（静默接受会让「消解了一条不存在的分歧」看起来像成功）；
    - **自己与自己**：语义上无意义（序 22 已对**声明**拒过这一形态 ⇒ 此处对**消解**同样拒）；
    - **空 id**（`other_id` / `resolved_by` 为空串）：无可复核的主体。

    **`resolved_at` 不在这里校验**：它的类型是 `Timestamp` ⇒ 非法值在**构造期**就被拒
    （比运行期判更早、更近因）。
    """
    for item in record.resolutions:
        if not item.other_id:
            raise ValueError("resolution other_id must not be empty")
        if item.other_id == record.id:
            raise ValueError(f"a record cannot resolve a conflict with itself: {record.id!r}")
        if item.other_id not in record.contradictions:
            raise ValueError(
                f"resolution target {item.other_id!r} is not declared in contradictions"
            )
        if not item.resolved_by:
            raise ValueError("resolution resolved_by must not be empty")


@dataclass(frozen=True, slots=True)
class MemoryWriteProposal:
    id: str
    tier: MemoryTier
    kind: MemoryType
    content: str
    provenance: str
    confidence: float
    scope: str = "project"
    proposed_by: str | None = None
    supersedes: list[str] = field(default_factory=list)
    # GOAL-20261008-039 EC-03：**声明式时效**（可选；缺省 `None` ⇒ 既有行为逐字不变）。
    # 由提案方声明，门链原样带进 canonical —— 不新造门链（仍是既有 §8 五段）。
    review_after: Timestamp | None = None
    expires_at: Timestamp | None = None
    # GOAL-20261010-045 EC-02：**冲突声明**与**生效起点**（可选；缺省 `[]` / `None`
    # ⇒ 既有行为逐字不变）。此前 `MemoryRecord` 上有这两个字段而**提案无法声明**
    # （`commit` 也丢）⇒ 「有冲突」既写不进也读不出。
    #: 声明与既有结论/记忆**冲突**的标识（`[]` = **已判定无冲突**；非空 = 点名冲突对象）。
    contradictions: list[str] = field(default_factory=list)
    #: 生效起点（`None` = **不适用/未声明**，**不猜** —— 与 `[]` 的语义各归各的）。
    valid_from: Timestamp | None = None
    # GOAL-20261012-061 EC-02：**冲突声明的时效**（可选；缺省 `None` = 未声明
    # ⇒ 既有行为逐字不变）。由提案方声明、门链原样带进 canonical ——
    # 与 `review_after` / `expires_at`（序 7 起）**同一形态**，
    # 说的是**冲突声明本身**还算不算数（见 `MemoryRecord` 上同名两字段的说明）。
    conflict_review_after: Timestamp | None = None
    conflict_expires_at: Timestamp | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("proposal id must not be empty")
        if not self.content:
            raise ValueError("proposal content must not be empty")
        if not self.provenance:
            raise ValueError("proposal provenance must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        # GOAL-20261010-045 EC-04(d)：冲突是**标识列表** ⇒ **逐个点名**非法项
        # （既有的 `supersedes` 无此校验；本条只**新增**校验，不动既有字段的语义）。
        for item in self.contradictions:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"proposal contradictions must be non-empty strings: {item!r}")


@dataclass(frozen=True, slots=True)
class ContextSnapshot:
    selected_refs: list[str] = field(default_factory=list)
    template_hash: str | None = None
    retrieval_digest: str | None = None
    token_allocation: int = 0
    trust_labels: list[str] = field(default_factory=list)
    created_at: Timestamp | None = None

    def __post_init__(self) -> None:
        if self.token_allocation < 0:
            raise ValueError("token_allocation must be non-negative")
