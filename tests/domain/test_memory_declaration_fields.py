"""GOAL-20261010-045 EC-02/EC-04(d) 判据：**声明式冲突与生效起点**（域面的可声明性）。

**为什么单列**：`tests/adapters/sqlite/test_memory_scope_and_validity.py`（11 例）判的是
**适配器面**（落库与往返）；本文件判**域面**（提案可否声明、缺省语义、非法项点名）——
两者的对象不同，**不互相顶替**（承既有纪律：声明面 vs 实现面分列）。

**靶子**：`MemoryWriteProposal` 此前**没有** `contradictions` / `valid_from` 字段
⇒ 提案**无从声明**（实测：构造即 `TypeError: unexpected keyword argument`），
而 `MemoryRecord` 上**有**这两个字段 ⇒ **有类型、零写者**。

**两向反证**：① 可声明（本轮新增）；② 不声明 ⇒ `[]` / `None`（**既有语义逐字不变**）；
③ `[]`（已判定无冲突）与 `None`（不适用/未声明）**互不混用**；④ 非法项（空串）⇒ **点名**。
"""

from __future__ import annotations

# --- GOAL-20261010-045：冲突声明与生效起点（可选字段，缺省逐字不变） ------------------


def test_a_proposal_can_declare_conflicts_and_a_valid_from() -> None:
    """**本轮的靶子**：提案此前**无从声明**这两个（构造即 `TypeError`）⇒ 现在可声明。"""
    from datetime import datetime, timezone

    from packages.domain.core import Timestamp
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryWriteProposal

    proposal = MemoryWriteProposal(
        id="m-declares",
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content="与既有结论冲突的断言",
        provenance="test:goal045",
        confidence=0.9,
        contradictions=["memory:earlier-claim"],
        valid_from=Timestamp(datetime(2026, 10, 1, tzinfo=timezone.utc)),
    )
    assert proposal.contradictions == ["memory:earlier-claim"], proposal
    assert proposal.valid_from is not None


def test_the_declaration_defaults_keep_the_old_behaviour() -> None:
    """**反证（不该红时不红）**：不声明 ⇒ `[]` / `None`（既有语义逐字不变）。"""
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryWriteProposal

    proposal = MemoryWriteProposal(
        id="m-default",
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content="既有形态",
        provenance="test:goal045",
        confidence=0.9,
    )
    assert proposal.contradictions == [], proposal
    assert proposal.valid_from is None, proposal


def test_the_two_defaults_are_not_interchangeable() -> None:
    """`[]`（**已判定无冲突**）与 `None`（**不适用/未声明**）语义**互不混用**。"""
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryRecord

    record = MemoryRecord(
        id="m-shape",
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content="c",
        provenance="test:goal045",
        confidence=0.9,
    )
    assert record.contradictions == [] and record.contradictions is not None
    assert record.valid_from is None


def test_a_non_string_conflict_is_named() -> None:
    """**点名而非静默**：冲突必须是**非空字符串**列表 ⇒ 非法项点名。"""
    import pytest

    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryWriteProposal

    with pytest.raises(ValueError, match="non-empty strings"):
        MemoryWriteProposal(
            id="m-bad",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="c",
            provenance="test:goal045",
            confidence=0.9,
            contradictions=[""],
        )
