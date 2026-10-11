"""GOAL-20261011-053（`BB-1`）：**链式取代的「当前版本」可判定** —— 两个读面的判据。

**为什么单列**：`tests/api/test_memory_api.py` 已到 401 行（规模门软阈值 300 / 硬上限 450）；
本轮的靶子（链的终点四态）自成一组，单列更清楚，也不挤那个文件。

**判的是什么**：`superseded_by` / `supersedes` 只给**直接**链接 ⇒ 在 A ⊂ B ⊂ C 上，
A 的「替代品」B **自己可能已被取代** ⇒ 「**现在**的版本是哪条」答不出来。
本轮补 `terminal`（读面）/ `terminal_state` + `terminal_ids`（HTTP 面），四态互不混用。
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from adapters.fakes import FakeMemoryStore

_NOW = "2026-05-01T00:00:00+00:00"


def _commit_chain(store: FakeMemoryStore, ids: list[str]) -> None:
    """直写一条**取代链**：`ids[i+1]` 取代 `ids[i]`（钉的是**读面**，不经提案面）。

    与 `test_memory_api.py::_commit_superseding` 同一形态 —— 两处都只写**声明**，
    读面的判定完全由被测代码给出。
    """
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryWriteProposal

    store.allow_source("test:goal053")
    for index, memory_id in enumerate(ids):
        store.commit(
            MemoryWriteProposal(
                id=memory_id,
                tier=MemoryTier.PROJECT,
                kind=MemoryType.FACT,
                content=f"内容 {memory_id}",
                provenance="test:goal053",
                confidence=0.9,
                scope="project",
                supersedes=[ids[index - 1]] if index else [],
            )
        )


def _wire(client: TestClient) -> FakeMemoryStore:
    """把该客户端的记忆存储换成新的 Fake（与 `test_memory_api.py::_wire` **同一取法**）。

    **不**新造装配方式：HTTP 面的读面判据必须打在**同一个请求装配**上，
    否则「HTTP 面看得见什么」这件事测的就不是产品路径。
    """
    from tests.api.test_memory_api import _wire as wire_memory_store

    return wire_memory_store(client)


def test_the_chain_end_is_decidable_on_the_orchestration_face() -> None:
    """EC-02（编排面）：A ⊂ B ⊂ C ⇒ A 与 B 的 `terminal` **都**是 C（**当前版本**）。

    **反证**：旧口径下 A 的 `superseded_by` 指向 B，而 B 自己是死的 ⇒ 读者被误导。
    """
    from adapters.canonical.memory_read import memory_read

    store = FakeMemoryStore(allowed_sources=("test:goal053",))
    _commit_chain(store, ["mem-a", "mem-b", "mem-c"])
    rows = memory_read(store, {"now": _NOW})["memories"]
    assert isinstance(rows, list)
    by_id = {str(row["memory_id"]): row for row in rows}
    assert by_id["mem-a"]["terminal"] == {"state": "SUCCEEDED", "ids": ["mem-c"]}, by_id["mem-a"]
    assert by_id["mem-b"]["terminal"] == {"state": "SUCCEEDED", "ids": ["mem-c"]}, by_id["mem-b"]
    assert by_id["mem-c"]["terminal"] == {"state": "CURRENT", "ids": ["mem-c"]}, by_id["mem-c"]
    # **既有键逐字不变**：直接链接仍然只报直接后继（没有被「升级」成终点）。
    assert by_id["mem-a"]["superseded_by"] == ["mem-b"], by_id["mem-a"]
    assert by_id["mem-c"]["supersedes"] == ["mem-b"], by_id["mem-c"]


def test_the_chain_a_record_that_has_no_successor_is_its_own_current_version() -> None:
    """EC-02：**无后继** ⇒ `CURRENT` 且点名**自身**（不是空、不是缺字段）。"""
    from adapters.canonical.memory_read import memory_read

    store = FakeMemoryStore(allowed_sources=("test:goal053",))
    _commit_chain(store, ["mem-solo"])
    rows = memory_read(store, {"now": _NOW})["memories"]
    assert isinstance(rows, list)
    assert rows[0]["terminal"] == {"state": "CURRENT", "ids": ["mem-solo"]}, rows[0]


def test_a_cycle_is_named_not_silently_truncated() -> None:
    """EC-02 / `P-4` 的受判面：链上**有环** ⇒ `CYCLE` 且**点名**环上的 id。

    **不**静默截断（不返回一个假装是终点的值）、**不**无限循环。
    """
    from packages.application.memory.disposition import terminal_versions
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryWriteProposal

    store = FakeMemoryStore(allowed_sources=("test:goal053",))
    store.allow_source("test:goal053")
    for memory_id, replaces in (("ring-a", "ring-c"), ("ring-b", "ring-a"), ("ring-c", "ring-b")):
        store.commit(
            MemoryWriteProposal(
                id=memory_id,
                tier=MemoryTier.PROJECT,
                kind=MemoryType.FACT,
                content=f"内容 {memory_id}",
                provenance="test:goal053",
                confidence=0.9,
                scope="project",
                supersedes=[replaces],
            )
        )
    got = terminal_versions(tuple(store.query()))
    assert got["ring-a"]["state"] == "CYCLE", got["ring-a"]
    assert sorted(got["ring-a"]["terminal"]) == ["ring-a", "ring-b", "ring-c"], got["ring-a"]


def _cross_scope_store() -> FakeMemoryStore:
    """两条记录：`m-proj`（project）被 `m-team`（team）取代 —— **走真实取代路径**。

    为什么必须走 `supersede_memory`（而不是直写 `supersedes`）：直写**不会**把旧记录
    `deactivate` ⇒ 造出的受判面里旧记录**仍生效**，与「被取代」的真实形态不符
    （本用例初版正是这样写的，实测发现 `active` 还是 `True` ⇒ `OUT_OF_VIEW` 支不触发）。
    """
    from packages.application.memory.gate import MemoryGateDeps
    from packages.application.memory.lifecycle import MemoryLifecycleDeps, supersede_memory
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryWriteProposal

    store = FakeMemoryStore(allowed_sources=("test:goal053",))
    store.allow_source("test:goal053")
    _commit_at_scope(store, memory_id="m-proj", scope="project")
    supersede_memory(
        MemoryLifecycleDeps(store=store),
        "m-proj",
        MemoryWriteProposal(
            id="m-team",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="内容 m-team",
            provenance="test:goal053",
            confidence=0.9,
            scope="team",
        ),
        gate_deps=MemoryGateDeps(store=store, allowed_sources=frozenset({"test:goal053"})),
        curator_approved=True,
    )
    return store


def test_an_invisible_successor_is_named_not_read_as_the_current_version() -> None:
    """EC-02：后继**在本批查询范围之外**（跨 `scope`）⇒ `OUT_OF_VIEW`，**不**报 `CURRENT`。

    **为什么这条是实测出来的**（不是设计出来的）：初版设计了 `DANGLING`（后继 id 不在批内）——
    实测证明**那条分支不可达**：`successors` 的值全部来自批内记录的 `record.id`
    （见 `_successors`）⇒ 后继**必然**在 `by_id` 里。真正的「后继看不见」是**跨范围**：
    取代它的记录在另一个 `scope` ⇒ 按 `scope` 筛之后，被取代的那条**孤立可见**。
    **旧口径会把它读成当前版本**（`terminal=CURRENT`、`ids=[自己]`），而它 `active=False`。
    """
    from adapters.canonical.memory_read import memory_read

    store = _cross_scope_store()
    all_rows = memory_read(store, {"now": _NOW})["memories"]
    assert isinstance(all_rows, list)
    everything = {str(row["memory_id"]): row for row in all_rows}
    assert everything["m-proj"]["terminal"] == {"state": "SUCCEEDED", "ids": ["m-team"]}, (
        everything["m-proj"]
    )
    filtered = memory_read(store, {"now": _NOW, "scope": "project"})["memories"]
    assert isinstance(filtered, list)
    only = {str(row["memory_id"]): row for row in filtered}
    # 受判面**可区分**：同一份库、两种查询范围给出**不同**的读数（不筛 ⇒ SUCCEEDED）。
    assert only["m-proj"]["active"] is False, only["m-proj"]
    assert only["m-proj"]["terminal"] == {"state": "OUT_OF_VIEW", "ids": []}, only["m-proj"]
    # **不**假装「它就是当前版本」—— 那是旧口径（`CURRENT` + 指自己）会犯的错。
    assert only["m-proj"]["terminal"]["state"] != "CURRENT", only["m-proj"]


def _commit_at_scope(
    store: FakeMemoryStore, *, memory_id: str, scope: str, supersedes: list[str] | None = None
) -> None:
    """直写一条指定 `scope` 的记录（跨范围用例的构造面）。"""
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryWriteProposal

    store.commit(
        MemoryWriteProposal(
            id=memory_id,
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content=f"内容 {memory_id}",
            provenance="test:goal053",
            confidence=0.9,
            scope=scope,
            supersedes=list(supersedes or ()),
        )
    )


def test_the_http_face_carries_the_chain_end_too(client: TestClient) -> None:
    """EC-03：**链的终点在 HTTP 面也看得见**（与编排面**同源同值**）。"""
    from adapters.canonical.memory_read import memory_read

    store = _wire(client)
    _commit_chain(store, ["m-a", "m-b", "m-c"])
    rows = client.get("/projects/example-project/memory").json()["records"]
    http = {str(row["id"]): row for row in rows}
    raw = memory_read(store, {"now": _NOW})["memories"]
    assert isinstance(raw, list)
    orch = {str(row["memory_id"]): row for row in raw}
    for rid in ("m-a", "m-b", "m-c"):
        assert http[rid]["terminal_state"] == orch[rid]["terminal"]["state"], rid
        assert list(http[rid]["terminal_ids"]) == list(orch[rid]["terminal"]["ids"]), rid
    assert http["m-a"]["terminal_state"] == "SUCCEEDED", http["m-a"]
    assert list(http["m-a"]["terminal_ids"]) == ["m-c"], http["m-a"]
    # **既有键逐字不变**：HTTP 面的直接链接仍是直接后继。
    assert list(http["m-a"]["superseded_by"]) == ["m-b"], http["m-a"]
