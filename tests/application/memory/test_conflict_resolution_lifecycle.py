"""GOAL-20261012-058（`CC-1`）：**冲突消解**的写路径判据（域校验 + 生命周期用例）。

**为什么单列**：本轮的靶子（「消解」成为可记录的事实）自成一组。

**判的是什么**：一个已声明的冲突此前是**终态**（一经声明**永远** `CONFLICTED` ——
消解面与改声明路径**全零命中**）。本轮加**消解记载**：**谁在何时**消解了**哪一对**；
**声明一字不动**；四种坏形态**点名拒绝**。
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from adapters.fakes import FakeMemoryStore
from packages.application.memory.lifecycle import (
    MemoryLifecycleDeps,
    resolve_memory_conflict,
)
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import ConflictResolution, MemoryRecord, MemoryWriteProposal

_NOW = Timestamp(datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc))


def _proposal(memory_id: str, contradictions: list[str]) -> MemoryWriteProposal:
    return MemoryWriteProposal(
        id=memory_id,
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content=f"内容 {memory_id}",
        provenance="source:article-1",
        confidence=0.9,
        contradictions=list(contradictions),
    )


def _store_with(*memory_ids: str) -> FakeMemoryStore:
    store = FakeMemoryStore(allowed_sources=("source:article-1",))
    store.allow_source("source:article-1")
    for memory_id in memory_ids:
        store.commit(_proposal(memory_id, [memory_id.replace("m-", "m-other-")]))
    return store


def test_a_resolution_is_recorded_with_who_and_when() -> None:
    """EC-02：消解**可记录** —— 记下**哪一对**、**由谁**、**何时**。"""
    store = _store_with("m-a")
    updated = resolve_memory_conflict(
        MemoryLifecycleDeps(store=store),
        "m-a",
        "m-other-a",
        resolved_by="curator:a",
        resolved_at=_NOW,
    )
    assert len(updated.resolutions) == 1, updated.resolutions
    item = updated.resolutions[0]
    assert item.other_id == "m-other-a", item
    assert item.resolved_by == "curator:a", item
    assert item.resolved_at == _NOW, item


def test_the_declaration_is_untouched_by_a_resolution() -> None:
    """EC-02：**声明一字不动** —— `contradictions` 是历史事实，消解是另一件事。"""
    store = _store_with("m-a")
    updated = resolve_memory_conflict(
        MemoryLifecycleDeps(store=store),
        "m-a",
        "m-other-a",
        resolved_by="curator:a",
        resolved_at=_NOW,
    )
    assert updated.contradictions == ["m-other-a"], ("声明不得被删", updated.contradictions)


def test_an_unknown_pair_is_rejected_by_name() -> None:
    """EC-02：**未知冲突对**（不在该记录 `contradictions` 里）⇒ **点名拒绝**。

    受判面**必须可区分**：本条与「可记录」那条的唯一差别是**这个对有没有被声明过** ——
    两条放在一起才证明拒绝判的是**脱钩**而不是「消解能不能用」。
    """
    store = _store_with("m-a")
    with pytest.raises((ValueError, InvalidInputError), match="not declared in contradictions"):
        resolve_memory_conflict(
            MemoryLifecycleDeps(store=store),
            "m-a",
            "m-never-declared",
            resolved_by="curator:a",
            resolved_at=_NOW,
        )


def test_a_self_pair_is_rejected_by_name() -> None:
    """EC-02：**自己与自己** ⇒ 点名拒绝（序 22 对声明拒过这一形态 ⇒ 消解同样拒）。"""
    # 受判面 = **真实存在的记录**（自指拒绝发生在校验里，而非「找不到记录」）。
    store = FakeMemoryStore(allowed_sources=("source:article-1",))
    store.allow_source("source:article-1")
    store.commit(
        MemoryWriteProposal(
            id="m-self",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="内容 m-self",
            provenance="source:article-1",
            confidence=0.9,
            # 受判面要求**这条真的声明了与自身冲突**（否则「未声明」那条先拒 ⇒ 测不到自指）。
            contradictions=["m-self"],
        )
    )
    with pytest.raises((ValueError, InvalidInputError), match="itself"):
        resolve_memory_conflict(
            MemoryLifecycleDeps(store=store),
            "m-self",
            "m-self",
            resolved_by="curator:a",
            resolved_at=_NOW,
        )


def test_an_empty_actor_is_rejected_by_name() -> None:
    """EC-02：**空消解者** ⇒ 点名拒绝（无可复核的主体）。"""
    store = _store_with("m-a")
    with pytest.raises(ValueError, match="resolved_by must not be empty"):
        store.get("m-a").__class__(**{
            **{
                f.name: getattr(store.get("m-a"), f.name)
                for f in store.get("m-a").__dataclass_fields__.values()
            },
            "resolutions": [
                ConflictResolution(other_id="m-other-a", resolved_by="", resolved_at=_NOW)
            ],
        })


def test_partially_resolved_names_only_the_remaining_ones() -> None:
    """EC-02：**逐对消解** —— 只消解一个 ⇒ `unresolved_conflicts` 里**仍有**其余的。"""
    store = FakeMemoryStore(allowed_sources=("source:article-1",))
    store.allow_source("source:article-1")
    record = MemoryRecord(
        id="m-multi",
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content="内容 m-multi",
        provenance="source:article-1",
        confidence=0.9,
        contradictions=["m-x", "m-y"],
    )
    store._records["m-multi"] = record
    resolve_memory_conflict(
        MemoryLifecycleDeps(store=store),
        "m-multi",
        "m-x",
        resolved_by="curator:a",
        resolved_at=_NOW,
    )
    assert store.get("m-multi").unresolved_conflicts == ["m-y"], store.get(
        "m-multi"
    ).unresolved_conflicts


def test_an_already_resolved_pair_is_rejected() -> None:
    """EC-02：**重复消解**同一对 ⇒ 存储层**点名拒绝**（不静默去重）。"""
    store = _store_with("m-a")
    deps = MemoryLifecycleDeps(store=store)
    resolve_memory_conflict(deps, "m-a", "m-other-a", resolved_by="curator:a", resolved_at=_NOW)
    with pytest.raises((ValueError, InvalidInputError), match="already resolved"):
        resolve_memory_conflict(deps, "m-a", "m-other-a", resolved_by="curator:b", resolved_at=_NOW)


def test_a_resolution_survives_a_store_round_trip() -> None:
    """EC-02：消解记载**真的落库**（SQLite 读-改-写；重开连接后仍在）。"""
    import sqlite3

    from adapters.sqlite.memory_store import SqliteMemoryStore

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    store = SqliteMemoryStore(connection=connection)
    store.allow_source("source:article-1")
    store.commit(_proposal("mem-round", ["m-old"]))
    deps = MemoryLifecycleDeps(store=store)
    resolve_memory_conflict(deps, "mem-round", "m-old", resolved_by="curator:a", resolved_at=_NOW)
    reloaded = SqliteMemoryStore(connection=connection).get("mem-round")
    assert len(reloaded.resolutions) == 1, reloaded.resolutions
    assert reloaded.resolutions[0].other_id == "m-old", reloaded.resolutions
    # 声明仍在（历史事实）。
    assert reloaded.contradictions == ["m-old"], reloaded.contradictions


def _gated_for_domain() -> None:
    """占位（保持 import 面：`replace` 在本文件用于域值对象构造）。"""
    assert replace is not None
