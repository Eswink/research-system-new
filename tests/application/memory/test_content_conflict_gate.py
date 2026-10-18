"""GOAL-20261018-083 EC-02 判据：内容级判定**接进既有门链**，且不放宽既有语义。

三条硬要求（逐条一组用例）：

1. **未声明但相反 ⇒ 提案被拒**，且判词**点名**那一条 id 与判词形态；
2. **既有语义逐字不变**：引用完整性（被引 id 存在 + 不得自指）照旧；「声明了冲突就落
   `CONFLICTED`」的行为也照旧（声明优先，不被内容判定改写）；
3. **三条边界**：只扫同 `scope`；已声明的对象不重复判；`active=False` 的记录不参与。

**按压**（`test_press_disabling_the_content_check_lets_it_through`）：把内容级判定关掉
（monkeypatch 成恒 `None`）⇒ 「未声明但相反」那条**又变回通过** —— 证明它真的在起作用，
而不是判据在别处顺手拒绝了。
"""

from __future__ import annotations

import pytest

from adapters.fakes import FakeMemoryStore
from packages.application.memory import gate as gate_module
from packages.application.memory.gate import GateResult, MemoryGateDeps, evaluate_memory_proposal
from packages.domain.enums import MemoryTier, MemoryType, PolicyDecision
from packages.domain.memory import MemoryWriteProposal

_PROVENANCE = "test:goal083"


def _store() -> FakeMemoryStore:
    store = FakeMemoryStore()
    store.allow_source(_PROVENANCE)
    return store


def _proposal(
    memory_id: str,
    content: str,
    *,
    scope: str = "project",
    contradictions: tuple[str, ...] = (),
) -> MemoryWriteProposal:
    return MemoryWriteProposal(
        id=memory_id,
        tier=MemoryTier.RUN,
        kind=MemoryType.FACT,
        content=content,
        provenance=_PROVENANCE,
        confidence=0.9,
        scope=scope,
        contradictions=list(contradictions),
    )


def _commit(store: FakeMemoryStore, proposal: MemoryWriteProposal) -> None:
    """直接落一条（用 gate 自己，确保走的是**同一条**写入链）。"""
    result = _evaluate(store, proposal)
    assert result.accepted, result.reasons
    store.commit(proposal)


def _evaluate(store: FakeMemoryStore, proposal: MemoryWriteProposal) -> GateResult:
    """走**同一条**门链（provenance 面显式放行本判据用的那个来源）。"""
    return evaluate_memory_proposal(
        proposal,
        MemoryGateDeps(store=store, allowed_sources=frozenset({_PROVENANCE})),
    )


# --------------------------------------------------- 1) 未声明但相反 ⇒ 判拒并点名


def test_undeclared_opposite_content_is_rejected_with_the_id_and_form() -> None:
    """**核心读数**：库里有一条 `X supports Y`，再提交 `X does not support Y` ⇒ **判拒**。"""
    store = _store()
    _commit(store, _proposal("mem-a", "X supports Y"))

    result = _evaluate(store, _proposal("mem-b", "X does not support Y"))

    assert result.accepted is False, result.reasons
    assert result.stage == "contradiction", result.stage
    joined = " ".join(result.reasons)
    assert "mem-a" in joined, ("判词必须点名**哪一条**记录", joined)
    assert "NEGATION_POLARITY" in joined, ("判词必须点名**判词形态**", joined)


def test_numeric_direction_is_rejected() -> None:
    store = _store()
    _commit(store, _proposal("mem-n1", "the metric is 2.0 ms"))

    result = _evaluate(store, _proposal("mem-n2", "the metric is 0.5 ms"))

    assert result.accepted is False, result.reasons
    assert "NUMERIC_DIRECTION" in " ".join(result.reasons)


def test_antonym_is_rejected() -> None:
    store = _store()
    _commit(store, _proposal("mem-p1", "该药有效"))

    result = _evaluate(store, _proposal("mem-p2", "该药无效"))

    assert result.accepted is False, result.reasons
    assert "ANTONYM_PREDICATE" in " ".join(result.reasons)


# ------------------------------------------- 2) 既有语义逐字不变（两条子要求）


def test_reference_integrity_is_unchanged() -> None:
    """`supersedes` / `contradictions` 引未知 id ⇒ 仍**点名拒绝**（既有判词逐字）。"""
    store = _store()
    missing_supersedes = _evaluate(
        store,
        MemoryWriteProposal(
            id="mem-s1",
            tier=MemoryTier.RUN,
            kind=MemoryType.FACT,
            content="anything",
            provenance=_PROVENANCE,
            confidence=0.9,
            scope="project",
            supersedes=["nope"],
        ),
    )
    assert missing_supersedes.accepted is False
    assert "supersedes target 'nope' does not exist" in " ".join(missing_supersedes.reasons)

    missing_contradiction = _evaluate(
        store, _proposal("mem-c1", "anything", contradictions=("ghost",))
    )
    assert missing_contradiction.accepted is False
    assert "contradiction target 'ghost' does not exist" in " ".join(missing_contradiction.reasons)


def test_self_contradiction_is_still_rejected() -> None:
    """自指冲突仍点名拒绝（既有判词逐字）。"""
    store = _store()
    result = _evaluate(store, _proposal("mem-self", "anything", contradictions=("mem-self",)))
    assert result.accepted is False
    assert "is the proposal itself" in " ".join(result.reasons)


def test_a_declared_conflict_still_wins_over_content() -> None:
    """**声明优先**：提案方已点名的对象，内容判定**不再**改变结论（既有语义不变）。"""
    store = _store()
    _commit(store, _proposal("mem-d1", "X supports Y"))

    result = _evaluate(
        store,
        _proposal("mem-d2", "X does not support Y", contradictions=("mem-d1",)),
    )

    assert result.accepted is True, result.reasons
    assert result.stage == "evaluated"


# ------------------------------------------------------- 3) 三条边界（逐条）


def test_only_the_same_scope_is_scanned() -> None:
    """**只扫同 scope**：另一 scope 里相反的说法**不**让本 scope 的提案被拒。"""
    store = _store()
    _commit(store, _proposal("mem-other", "X supports Y", scope="run"))

    result = _evaluate(store, _proposal("mem-project", "X does not support Y", scope="project"))

    assert result.accepted is True, result.reasons


def test_inactive_records_do_not_participate() -> None:
    """**`active=False` 不参与**：一条已停用的相反记录不构成现行分歧。"""
    store = _store()
    _commit(store, _proposal("mem-off", "X supports Y"))
    store.deactivate("mem-off")

    result = _evaluate(store, _proposal("mem-on", "X does not support Y"))

    assert result.accepted is True, result.reasons


def test_consistent_content_is_accepted() -> None:
    """**不相反 ⇒ 照常通过**（误报会把记忆写入掐死）。"""
    store = _store()
    _commit(store, _proposal("mem-x", "the ratio increases with n"))

    result = _evaluate(store, _proposal("mem-y", "the metric is 2.0 ms"))

    assert result.accepted is True, result.reasons


# ------------------------------------------------------------------- 按压


def test_press_disabling_the_content_check_lets_it_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """**按压**：把内容级判定关掉（恒 `None`）⇒ 同一条提案**又变回通过**。

    与第一条用例成对：同一份输入、只改「判定在不在」⇒ 读数必须相反。这证明拒绝是
    **内容级判定**给的，不是别处顺手拒的。
    """
    store = _store()
    _commit(store, _proposal("mem-a", "X supports Y"))

    monkeypatch.setattr(gate_module, "_content_conflict_check", lambda proposal, deps: None)
    result = _evaluate(store, _proposal("mem-b2", "X does not support Y"))

    assert result.accepted is True, ("关掉判定后应通过（否则判据考的不是它）", result.reasons)
    assert result.decision is PolicyDecision.ALLOW
