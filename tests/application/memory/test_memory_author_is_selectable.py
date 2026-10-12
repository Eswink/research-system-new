"""GOAL-20261013-066（序 34）：**记忆的作者可筛选** —— EC-02 / EC-03 的判据。

**为什么单列**：本轮的靶子是**作者维的「选得着」**（序 33 只做到「读得出」）；
与序 17（`scope` 第三维）**同一缺口形态、同一手法** —— 那一轮的判据在
`tests/adapters/canonical/test_memory_read_dispositions.py`，本组判**第三个维度**。

**判的是什么**：`MemoryStore.query` 的形参只有 `tier` / `scope` ⇒ 传 `proposed_by=`
直接 `TypeError`；**实跑**两条不同作者的记忆 ⇒ 读面**看得到作者**而**选不着**。
本轮让作者成为**可选维度**（三适配器同契约；缺省不筛；未知作者空集），
并让消费面**可传 + 点名**（缺省载荷逐字不变）。
"""

from __future__ import annotations

import inspect
from typing import cast

from adapters.canonical.memory_read import memory_read
from adapters.fakes import FakeMemoryStore
from adapters.sqlite.memory_store import SqliteMemoryStore
from packages.application.ports.memory_store import MemoryStore
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal

_NOW = "2026-05-01T12:00:00+00:00"


def _proposal(memory_id: str, author: str | None, *, scope: str = "project") -> MemoryWriteProposal:
    return MemoryWriteProposal(
        id=memory_id,
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content=f"内容 {memory_id}",
        provenance="source:a",
        confidence=0.9,
        scope=scope,
        proposed_by=author,
    )


def _store(*, second_scope: str = "project") -> FakeMemoryStore:
    """两条记忆（同一 tier，作者分别 `agent:x` / `agent:y`）—— 全走**产品路径**。"""
    store = FakeMemoryStore(allowed_sources=("source:a",))
    store.allow_source("source:a")
    store.commit(_proposal("m-x", "agent:x"))
    store.commit(_proposal("m-y", "agent:y", scope=second_scope))
    return store


def test_the_port_carries_the_third_dimension() -> None:
    """EC-02 ①：Port 的 `query` 有第三个维度（改动前直接 `TypeError`）。"""
    assert "proposed_by" in inspect.signature(MemoryStore.query).parameters


def test_the_author_selects_exactly_its_own_records() -> None:
    """EC-02 ②：**按作者选** ⇒ 只出那一位作者的记录（受判面 = 两条作者的**区分**）。"""
    store = _store()
    assert [r.id for r in store.query(proposed_by="agent:x")] == ["m-x"]
    assert [r.id for r in store.query(proposed_by="agent:y")] == ["m-y"]


def test_the_default_selection_is_verbatim() -> None:
    """EC-02 ③：**不传作者** ⇒ 全部（既有行为逐字不变 —— 与「筛出空集」是两件事）。"""
    store = _store()
    assert sorted(r.id for r in store.query()) == ["m-x", "m-y"]
    assert sorted(r.id for r in store.query(tier=MemoryTier.PROJECT)) == ["m-x", "m-y"]


def test_an_unknown_author_gives_an_empty_result_not_a_guess() -> None:
    """EC-02 ④：**未知作者 ⇒ 空结果**（**不猜**：不把未知当「全选」）。"""
    assert _store().query(proposed_by="agent:nowhere") == ()


def test_the_author_and_the_scope_coexist() -> None:
    """EC-02 ⑤：作者与 `scope` **可并存**（两维各自独立）。"""
    store = _store(second_scope="organization")
    assert [r.id for r in store.query(scope="project")] == ["m-x"]
    assert [r.id for r in store.query(scope="project", proposed_by="agent:x")] == ["m-x"]
    assert store.query(scope="project", proposed_by="agent:y") == ()
    assert [r.id for r in store.query(proposed_by="agent:y")] == ["m-y"]


def test_the_sqlite_adapter_shares_the_contract() -> None:
    """EC-02 ⑥：**SQLite 同契约**（按作者选 —— 真落库路径，不是内存字典）。"""
    store = SqliteMemoryStore(":memory:", allowed_sources=("source:a",))
    store.commit(_proposal("m-x", "agent:x"))
    store.commit(_proposal("m-y", "agent:y"))
    assert [r.id for r in store.query(proposed_by="agent:x")] == ["m-x"]
    assert sorted(r.id for r in store.query()) == ["m-x", "m-y"]


def test_the_consumption_face_can_pass_the_author() -> None:
    """EC-03 ①：消费面**可传**作者 ⇒ 只读那一位的（载荷点名）。"""
    payload = memory_read(_store(), {"now": _NOW, "proposed_by": "agent:x"})
    rows = cast("list[dict[str, object]]", payload["memories"])
    assert [r["memory_id"] for r in rows] == ["m-x"], rows
    assert payload["proposed_by"] == "agent:x", payload
    assert payload["filtered_out"] == 1, ("必须点名筛掉几条", payload)


def test_the_consumption_face_default_payload_is_verbatim() -> None:
    """EC-03 ②：**不传作者** ⇒ 载荷与改动前**逐字相同**（既有读者看到的键一个不多）。"""
    payload = memory_read(_store(), {"now": _NOW})
    for key in ("proposed_by", "filtered_out"):
        assert key not in payload, (key, sorted(payload))
    assert payload["memory_count"] == 2, payload


def test_the_scope_disclosure_is_untouched() -> None:
    """EC-03 ③（反证臂）：`scope` 那一支的披露**语义一字不动**（本轮只**加**第三个维度）。"""
    store = _store(second_scope="organization")
    payload = memory_read(store, {"now": _NOW, "scope": "project"})
    assert payload["scope"] == "project", payload
    assert payload["filtered_out"] == 1, ("序 17 立的语义逐字保持", payload)


def test_an_unknown_author_on_the_consumption_face_is_empty_not_refused() -> None:
    """EC-03 ④：消费面上的**未知作者** ⇒ 空载荷。

    **不猜**、**不**拒绝 —— 与 `scope` 的**已知集合**不同（作者是自由声明的标识）。
    """
    payload = memory_read(_store(), {"now": _NOW, "proposed_by": "agent:nowhere"})
    assert payload["memory_count"] == 0, payload
    assert payload["proposed_by"] == "agent:nowhere", payload
