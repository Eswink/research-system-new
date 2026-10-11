"""GOAL-20261012-058（`CC-1`）：**被消解的冲突读得出来** —— EC-03 的判据（两个读面）。

**判的是什么**：消解**逐对披露**（与编排面**同源同值**）；**未消解 ⇒ 逐字仍是
`CONFLICTED`**（既有行为逐字不变）；**声明一字不动**（`contradictions` 是历史事实）。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import cast

from adapters.canonical.memory_read import memory_read
from adapters.fakes import FakeMemoryStore
from packages.application.memory.lifecycle import MemoryLifecycleDeps, resolve_memory_conflict
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal

_NOW = Timestamp(datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc))
_AT = "2026-05-01T12:00:00+00:00"


def _store(*, resolved: bool) -> FakeMemoryStore:
    """主记录声明与 `m-peer` 冲突；（可选）把这一对消解掉 —— 全走**产品路径**。"""
    store = FakeMemoryStore(allowed_sources=("source:article-1",))
    store.allow_source("source:article-1")
    store.commit(
        MemoryWriteProposal(
            id="m-peer",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="内容 m-peer",
            provenance="source:article-1",
            confidence=0.9,
        )
    )
    store.commit(
        MemoryWriteProposal(
            id="m-main",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="内容 m-main",
            provenance="source:article-1",
            confidence=0.9,
            contradictions=["m-peer"],
        )
    )
    if resolved:
        resolve_memory_conflict(
            MemoryLifecycleDeps(store=store),
            "m-main",
            "m-peer",
            resolved_by="curator:a",
            resolved_at=_NOW,
        )
    return store


def _row(store: FakeMemoryStore, memory_id: str) -> dict[str, object]:
    payload = memory_read(store, {"now": _AT})
    rows = cast("list[dict[str, object]]", payload["memories"])
    return next(row for row in rows if str(row["memory_id"]) == memory_id)


def test_the_read_face_discloses_resolutions_and_keeps_the_declaration() -> None:
    """EC-03：消解**逐对披露**；**声明一字不动**（`contradictions` 是历史事实）。"""
    main_row = _row(_store(resolved=True), "m-main")
    assert main_row["conflict_resolutions"] == [
        {
            "other_id": "m-peer",
            "resolved_by": "curator:a",
            "resolved_at": _AT,
        }
    ], main_row["conflict_resolutions"]
    assert main_row["contradictions"] == ["m-peer"], ("声明不得被删", main_row["contradictions"])
    # 全部对已消解 ⇒ **不再是** `CONFLICTED`（这正是「消解决定了标注能否结束」）。
    assert main_row["disposition"] != "CONFLICTED", main_row["disposition"]
    # **未消解**的那条 ⇒ 仍是既有行为（无消解记载）。
    assert _row(_store(resolved=True), "m-peer")["conflict_resolutions"] == []


def test_an_unresolved_conflict_still_reads_conflicted_verbatim() -> None:
    """EC-03：**未消解** ⇒ 逐字仍是 `CONFLICTED`（既有行为逐字不变）。"""
    main_row = _row(_store(resolved=False), "m-main")
    assert main_row["disposition"] == "CONFLICTED", main_row
    assert main_row["conflict_resolutions"] == [], main_row


def test_the_nudge_signal_is_absent_when_every_pair_is_resolved() -> None:
    """EC-03 与序 25 的**衔接**：全部对已消解 ⇒ 超期信号**不再发**（没有要催的事了）。

    **受判面**：与「已消解披露」那条**同一份库**，但判的是**处置**而非载荷 ——
    处置从 `CONFLICTED` 回落到非冲突态 ⇒ 序 25 的超期分支**没有要催的事**。
    """
    main_row = _row(_store(resolved=True), "m-main")
    assert main_row["disposition"] != "CONFLICTED", main_row["disposition"]
