"""GOAL-20261011-054（`W-2` 声明面完整性）：`contradictions` 的被引 id 与
`supersedes` **同一条纪律**。

**为什么单列**：`tests/application/memory/test_gate_adversarial.py` 已 251 行；
本轮的靶子（引用完整性两侧对齐）自成一组，单列更清楚。

**判的是什么**：门链的 `contradiction` 阶段此前**只**校验 `supersedes` 的被引 id
（引未知 id ⇒ 拒绝），`contradictions` **一字未查** ⇒ 一条**指向空气**的「冲突」与一条
**真实分歧**在读面**同处置**（都 `CONFLICTED`）⇒ 序 19 的第五态会被**悬空声明**污染。
本轮让两侧**同一条纪律**：存在性 + **不得自指**，且 `supersedes` 那一侧**逐字未动**。
"""

from __future__ import annotations

from adapters.fakes import FakeMemoryStore
from packages.application.memory.gate import MemoryGateDeps, commit_memory
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal


def _proposal(
    memory_id: str,
    *,
    supersedes: list[str] | None = None,
    contradicts: list[str] | None = None,
) -> MemoryWriteProposal:
    return MemoryWriteProposal(
        id=memory_id,
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content=f"内容 {memory_id}",
        provenance="source:article-1",
        confidence=0.9,
        supersedes=list(supersedes or ()),
        contradictions=list(contradicts or ()),
    )


def _deps(store: FakeMemoryStore) -> MemoryGateDeps:
    return MemoryGateDeps(store=store, allowed_sources=frozenset({"source:article-1"}))


def _store() -> FakeMemoryStore:
    store = FakeMemoryStore(allowed_sources=("source:article-1",))
    store.allow_source("source:article-1")
    return store


def test_a_dangling_conflict_target_is_rejected_by_name() -> None:
    """EC-02：被引 id **查不到** ⇒ 拒绝，且判词**点名**那个 id（不静默接受）。"""
    store = _store()
    result = commit_memory(
        _proposal("m-ghost", contradicts=["m-nowhere"]), _deps(store), curator_approved=True
    )
    assert result.accepted is False, result
    assert result.stage == "contradiction", result
    assert "m-nowhere" in result.reasons[0] and "does not exist" in result.reasons[0], (
        result.reasons
    )


def test_a_self_referential_conflict_target_is_rejected_by_name() -> None:
    """EC-02：被引 id == **提案自身** ⇒ 拒绝，且判词**点名**「就是它自己」。

    「与自己冲突」不是分歧 —— 但它此前会被当成真的分歧（读面 `CONFLICTED` 并点名自己）。
    """
    store = _store()
    result = commit_memory(
        _proposal("m-self", contradicts=["m-self"]), _deps(store), curator_approved=True
    )
    assert result.accepted is False, result
    assert result.stage == "contradiction", result
    assert "m-self" in result.reasons[0] and "itself" in result.reasons[0], result.reasons


def test_a_real_conflict_target_is_accepted() -> None:
    """EC-02：指向**真实存在**的记录 ⇒ **照常通过**（校验**不误伤**正常声明）。

    受判面**必须可区分**：本条与上面两条的唯一差别是「被引 id 在不在库里」
    ⇒ 三条放在一起才证明校验判的是**存在性**而不是「有没有 `contradictions`」。
    """
    store = _store()
    deps = _deps(store)
    first = commit_memory(_proposal("m-real"), deps, curator_approved=True)
    assert first.accepted is True, first
    result = commit_memory(_proposal("m-ok", contradicts=["m-real"]), deps, curator_approved=True)
    assert result.accepted is True, result
    assert result.stage == "committed", result
    assert store.get("m-ok").contradictions == ["m-real"]


def test_the_supersedes_side_is_unchanged_verbatim() -> None:
    """EC-02：`supersedes` 的既有校验**逐字未动**（那一侧是**基准**）。

    两侧现在是**同一条纪律**，但本轮的改动**只加**在 `contradictions` 那一侧 ——
    `supersedes` 的判词形态与阶段都与改动前**逐字相同**（这条用例是它的**回归锚**）。
    """
    store = _store()
    result = commit_memory(
        _proposal("m-sup", supersedes=["m-nowhere"]), _deps(store), curator_approved=True
    )
    assert result.accepted is False, result
    assert result.stage == "contradiction", result
    assert result.reasons == ("supersedes target 'm-nowhere' does not exist",), result.reasons
