"""GOAL-20261024-096 EC-03 的**读取面**判据：报告第 1 节来自本 run 自己的问题。

判什么（每条可证伪）：

1. **同源读出**：报告第 1 节**逐字节**包含本 run `research_question` 制品里的
   问题正文 —— 信封形态取模型声明的那块 JSON 原文切片，直形态取制品原文；
2. **反证（改制品 ⇒ 改报告）**：改问题制品的正文 ⇒ 第 1 节随之变（证明不是硬编码）；
3. **无制品 ⇒ 点名不编造**：证据里没有 `research_question` ⇒ `objective` 是 `None`，
   渲染出的第 1 节点名「本 run 没有 research_question 制品」；
4. **fail-closed**：制品在但解不出（缺键 / 多块歧义 / 多制品歧义）⇒ **点名抛错**，
   不静默当成「没有」。

与 `tests/e2e/test_direction_to_report_arc_offline.py` 分工：那里判**全链**
（真实编排跑出来的报告）；这里判**读取面本身**（两种形态、缺席、反证、fail-closed）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger
from packages.application.deliverable.research_report import (
    SECTION_HEADINGS,
    build_research_report,
)
from packages.application.run_orchestration.report_facts import report_inputs
from packages.application.run_orchestration.report_question import question_objective
from packages.domain.core import Digest, Timestamp
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
)

_RUN = "8d1c2e40-1111-4c33-9e55-0d2e6b8c4a17"
_TASK = "2c9fae7f-eaf6-43f3-b65f-6876f88211e9"
_ARTIFACT_ID = f"{_TASK}:research_question"
_QUESTION = "does retrieval augmentation improve planning?"
_QUERY = "retrieval augmented planning"
_ENVELOPE_CONTENT = (
    "The question this run pursues: does retrieval augmentation improve planning?\n\n"
    "```json\n"
    '{"research_question": {"query": "'
    + _QUERY
    + '", "rationale": "the direction implies this"}}\n'
    "```\n"
)
_ENVELOPE = {
    "declared_artifact": "research_question",
    "content": _ENVELOPE_CONTENT,
}
_DIRECT = {"query": _QUERY, "rationale": "the direction implies this"}


@dataclass(frozen=True)
class _Run:
    protocol_id: str
    state: str


def _store_with(payload: dict[str, Any] | str) -> FakeArtifactStore:
    store = FakeArtifactStore()
    content = payload.encode("utf-8") if isinstance(payload, str) else json.dumps(payload).encode()
    store.put(
        _artifact(content),
        content,
    )
    store.mark(_ARTIFACT_ID, _verified())
    return store


def _artifact(content: bytes) -> Any:
    from packages.domain.artifacts import Artifact

    return Artifact(
        id=_ARTIFACT_ID,
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type="application/json",
        created_by="agent:question",
        classification="execution_result",
    )


def _verified() -> Any:
    from packages.domain.enums import ArtifactState

    return ArtifactState.VERIFIED


def _ledger_with(store: FakeArtifactStore) -> FakeEvidenceLedger:
    """证据投影里挂上问题制品（claims → relations → evidence；读面唯一通道）。"""
    ledger = FakeEvidenceLedger()
    evidence = Evidence(
        id=f"evidence:{_ARTIFACT_ID}",
        source_ref=_ARTIFACT_ID,
        content_digest=str(Digest.of_bytes(store.get(_ARTIFACT_ID))),
        extracted_by="agent:question",
        captured_at=Timestamp.now(),
        artifact_id=_ARTIFACT_ID,
        run_id=_RUN,
    )
    claim = Claim(
        id=f"claim:{_TASK}:result",
        statement="the question phase produced research_question",
        status=ClaimStatus.PROPOSED,
        author="agent:question",
        evidence_relations=[(evidence.id, EvidenceRelationType.SUPPORTS)],
    )
    ledger.register_evidence(evidence)
    ledger.register_claim(claim)
    ledger.attach_relation(
        EvidenceRelation(
            claim_id=claim.id, evidence_id=evidence.id, relation=EvidenceRelationType.SUPPORTS
        )
    )
    return ledger


class _EmptyReviews:
    def for_run(self, run_id: str) -> tuple[Any, ...]:
        return ()


def _report_inputs(store: FakeArtifactStore, ledger: FakeEvidenceLedger) -> Any:
    return report_inputs(
        store,
        ledger,
        _EmptyReviews(),
        _Run(protocol_id="direction_to_report_v1_0_0", state="RUNNING"),
        _RUN,
    )


# ------------------------------------------------- (1) 两种形态、逐字节


def test_the_envelope_form_yields_the_declared_block_verbatim() -> None:
    """信封形态：第 1 节里逐字节出现模型声明的那块 JSON（含 query 与 rationale）。"""
    store = _store_with(_ENVELOPE)
    objective = question_objective(store, ledger_evidence(_ledger_with(store)))
    assert objective is not None
    assert objective in _ENVELOPE_CONTENT, (objective,)
    report = build_research_report(_report_inputs(store, _ledger_with(store)))
    section = report.split(SECTION_HEADINGS[1])[0]
    # 第 1 节以 blockquote 逐字节引用问题正文（不含围栏标记 —— 那是信封的包装，不是正文）。
    assert f"> {objective}" in section
    assert objective in section


def test_the_direct_form_yields_the_artifact_text_verbatim() -> None:
    """直形态（受控夹具）：正文 = 制品原文（落盘时已按规范 JSON 序列化）。"""
    store = _store_with(_DIRECT)
    objective = question_objective(store, ledger_evidence(_ledger_with(store)))
    assert objective == json.dumps(_DIRECT), objective


def test_changing_the_artifact_changes_the_report_section() -> None:
    """反证：改问题制品正文 ⇒ 第 1 节随之变（同源读出，不是硬编码）。"""
    first_store = _store_with(_ENVELOPE)
    first = build_research_report(_report_inputs(first_store, _ledger_with(first_store)))
    other = dict(_DIRECT, query="cross-phase planning evidence")
    second_store = _store_with(other)
    second = build_research_report(_report_inputs(second_store, _ledger_with(second_store)))
    assert first != second
    assert json.dumps(other) in second
    assert json.dumps(_DIRECT) not in second


# ------------------------------------------------- (3) 无制品 ⇒ 点名


def test_a_run_without_a_question_artifact_names_the_absence() -> None:
    """没有 `research_question` 证据 ⇒ `objective` 为 `None`，第 1 节点名缺席。"""
    store = _store_with(_DIRECT)
    empty_ledger = FakeEvidenceLedger()
    inputs = _report_inputs(store, empty_ledger)
    assert inputs.objective is None
    report = build_research_report(inputs)
    section = report.split(SECTION_HEADINGS[1])[0]
    assert "本 run 没有 research_question 制品" in section


# ------------------------------------------------- (4) fail-closed


def test_an_undecodable_artifact_is_named_not_silently_dropped() -> None:
    """信封里没有带键的 JSON 块 ⇒ 点名抛错（不静默当「没有」）。"""
    store = _store_with({"declared_artifact": "research_question", "content": "no block in here"})
    try:
        question_objective(store, ledger_evidence(_ledger_with(store)))
    except ValueError as error:
        assert "research_question" in str(error) and "no JSON object" in str(error)
    else:
        raise AssertionError("undecidable content must raise, not degrade")


def test_two_question_artifacts_are_named_not_picked() -> None:
    """两个 `research_question` 制品 ⇒ 点名歧义（不取第一个）。"""
    ledger = FakeEvidenceLedger()
    for task_id in (_TASK, "aaaaaaaa-bbbb-4ccc-8ddd-eeeeffff0000"):
        artifact_id = f"{task_id}:research_question"
        content = json.dumps(_DIRECT).encode()
        ledger.register_evidence(
            Evidence(
                id=f"evidence:{artifact_id}",
                source_ref=artifact_id,
                content_digest=str(Digest.of_bytes(content)),
                artifact_id=artifact_id,
                run_id=_RUN,
            )
        )
    claim = Claim(
        id="claim:shared",
        statement="two producers",
        status=ClaimStatus.PROPOSED,
        author="agent:question",
        evidence_relations=[],
    )
    ledger.register_claim(claim)
    for task_id in (_TASK, "aaaaaaaa-bbbb-4ccc-8ddd-eeeeffff0000"):
        ledger.attach_relation(
            EvidenceRelation(
                claim_id=claim.id,
                evidence_id=f"evidence:{task_id}:research_question",
                relation=EvidenceRelationType.SUPPORTS,
            )
        )
    try:
        question_objective(FakeArtifactStore(), ledger_evidence(ledger))
    except ValueError as error:
        assert "2 distinct" in str(error), error
    else:
        raise AssertionError("ambiguous artifacts must raise, not pick one")


def ledger_evidence(ledger: FakeEvidenceLedger) -> tuple[Any, ...]:
    """从假账本投影出证据元组（与 report_facts.evidence_of_run 同一步）。"""
    from packages.application.run_orchestration.report_facts import evidence_of_run

    return evidence_of_run(ledger, _RUN)
