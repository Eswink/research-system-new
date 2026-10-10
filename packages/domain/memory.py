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
