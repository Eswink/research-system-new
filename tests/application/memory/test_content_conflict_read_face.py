"""GOAL-20261018-083 EC-03 判据：**冲突的来源分得开**（声明侧 vs 内容级）。

**改判的经过（如实记录）**：本条最初写成 e2e「读两种 422 判词」——**实测发现**
`MemoryProposalDto` **不接受** `contradictions` 字段（`extra="forbid"`），也就是说
**HTTP 写面根本不提供「声明冲突」这条路**（只有进程内用例能声明）。因此「两种来源在读面上
分得开」在今天的 HTTP 面上**无法成立**：读面只会有一种来源（内容级）。

⇒ 本判据判**门链层**的分开（那是两种来源**唯一共存**的层），并**如实登记**那条 API 缺口：

- 引用完整性：`contradiction target 'x' does not exist` / `is the proposal itself`；
- 内容级：`content contradicts memory 'id' (FORM): ...`；
- 两者**阶段相同**（`contradiction`）⇒ 只能靠**判词**分开，判据逐条断言这一点；
- **反证**：关掉内容级判定 ⇒ 内容相反那条通过、引用完整性那条**仍拒**。

**未覆盖（写进 GOAL 的残余）**：HTTP 写面缺「声明冲突」入口 —— 不在本 GOAL 射程
（那是读面/写面契约改动，需单独设计）。
"""

from __future__ import annotations

import pytest

from adapters.fakes import FakeMemoryStore
from packages.application.memory import gate as gate_module
from packages.application.memory.gate import MemoryGateDeps, evaluate_memory_proposal
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal

_PROVENANCE = "test:goal083-ec03"


def _deps(store: FakeMemoryStore) -> MemoryGateDeps:
    return MemoryGateDeps(store=store, allowed_sources=frozenset({_PROVENANCE}))


def _proposal(
    memory_id: str,
    content: str,
    *,
    contradictions: tuple[str, ...] = (),
    supersedes: tuple[str, ...] = (),
) -> MemoryWriteProposal:
    return MemoryWriteProposal(
        id=memory_id,
        tier=MemoryTier.RUN,
        kind=MemoryType.FACT,
        content=content,
        provenance=_PROVENANCE,
        confidence=0.9,
        scope="project",
        contradictions=list(contradictions),
        supersedes=list(supersedes),
    )


def _store_with(content: str = "X supports Y") -> FakeMemoryStore:
    store = FakeMemoryStore()
    store.allow_source(_PROVENANCE)
    store.commit(_proposal("mem-a", content))
    return store


def test_reference_integrity_and_content_conflict_use_distinguishable_wordings() -> None:
    """**两种来源的判词分得开**：一条点「不存在」，另一条点「内容相反 + 形态」。"""
    store = _store_with()

    reference = evaluate_memory_proposal(
        _proposal("mem-ref", "unrelated text", contradictions=("ghost",)), _deps(store)
    )
    content = evaluate_memory_proposal(
        _proposal("mem-content", "X does not support Y"), _deps(store)
    )

    assert reference.accepted is False and content.accepted is False
    reference_text = " ".join(reference.reasons)
    content_text = " ".join(content.reasons)

    assert "does not exist" in reference_text, reference_text
    assert "content contradicts" not in reference_text, reference_text

    assert "content contradicts" in content_text, content_text
    assert "mem-a" in content_text, content_text
    assert "NEGATION_POLARITY" in content_text, content_text
    assert "does not exist" not in content_text, content_text


def test_both_sources_land_on_the_same_stage() -> None:
    """**同一阶段**（`contradiction`）：不是新造第六段门链。"""
    store = _store_with()
    reference = evaluate_memory_proposal(
        _proposal("mem-ref", "unrelated", contradictions=("ghost",)), _deps(store)
    )
    content = evaluate_memory_proposal(_proposal("mem-c", "X does not support Y"), _deps(store))
    assert reference.stage == content.stage == "contradiction"


def test_declared_conflict_and_content_conflict_are_not_confused() -> None:
    """**声明侧与内容级不互相冒充**：声明了冲突的提案**通过**（声明优先），
    而同一份内容在没有声明时**被内容级拒**。"""
    store = _store_with()

    declared = evaluate_memory_proposal(
        _proposal("mem-d", "X does not support Y", contradictions=("mem-a",)), _deps(store)
    )
    undeclared = evaluate_memory_proposal(_proposal("mem-u", "X does not support Y"), _deps(store))

    assert declared.accepted is True, declared.reasons
    assert undeclared.accepted is False, undeclared.reasons


def test_the_http_proposal_dto_does_not_expose_declarations() -> None:
    """**如实登记的缺口**：HTTP 写面**不接受** `contradictions` ⇒ 读面上只有内容级一种来源。

    这条断言**钉住事实**（而不是钉住「应该如此」）：它是 EC-03 改判的依据。若将来给写面
    补上声明入口，**这条会红** —— 那时应当更新本判据与 GOAL 的残余登记，而不是让它默默变绿。
    """
    from services.api.dto.memory import MemoryProposalDto

    assert "contradictions" not in MemoryProposalDto.model_fields
    assert "supersedes" in MemoryProposalDto.model_fields, (
        "supersedes 是既有字段（替换），contradictions（冲突声明）不是 —— 两件事不同"
    )


def test_press_disabling_content_detection_leaves_reference_integrity_intact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """**反证**：关掉内容级判定 ⇒ 内容相反那条通过、引用完整性那条**仍拒**。"""
    store = _store_with()
    monkeypatch.setattr(gate_module, "_content_conflict_check", lambda proposal, deps: None)

    content = evaluate_memory_proposal(_proposal("mem-p", "X does not support Y"), _deps(store))
    reference = evaluate_memory_proposal(
        _proposal("mem-r", "unrelated", contradictions=("ghost",)), _deps(store)
    )

    assert content.accepted is True, ("关掉内容级后应通过", content.reasons)
    assert reference.accepted is False, ("引用完整性不受影响", reference.reasons)
