"""GOAL-20261114-113 EC-04 判据：**合约声明式记忆导出**（四条判据含两条反证）。

- ① 正例：合约带 `memory_export` ⇒ 晋升发生（真实运行链版本由
  `tests/integration/test_ig1_phase_runner.py` 钉住；这里钉声明 → 逐字段的映射）；
- ② 反证（零回归）：合约不带 ⇒ 不晋升 ——「没声明就没这条通道」，不是拒绝；
- ③ 反证（curator 门仍咬）：同一提案形态、`curator_approved=False` ⇒ 不写入，
  且点名 curator 阶段 —— 证明「声明即绕过门」不成立；
- ④ 读得到：提交后，**下一轮**的 `prior_knowledge` 视图非空，且渲染行逐字匹配
  `- {memory_id}{marks}: {shown} (source: {provenance})`。

**授权来源点名**：①④ 的判词点名「本 run 的 curator 授权来自合约 `memory_export`」
—— 门的 `_CURATOR_TIERS` 与 curator 判定逐字未动（`gate.py` 一行不改）。
"""

from __future__ import annotations

from datetime import datetime, timezone

from adapters.fakes import FakeEvidenceLedger, FakeMemoryStore, FakePolicyEvaluator
from packages.application.memory.gate import MemoryGateDeps, evaluate_memory_proposal
from packages.application.run_orchestration.memory_promotion import (
    MemoryPromotionContext,
    promote_memory,
    promote_memory_from_registration,
)
from packages.application.run_orchestration.prior_knowledge import build_prior_knowledge
from packages.application.run_orchestration.result_handler import ResultRegistration
from packages.application.run_orchestration.retrieval_prompt import render_prior_knowledge_prompt
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType, TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.memory import MemoryWriteProposal
from packages.domain.tasks import MemoryExportSpec

_SOURCE = "artifact:1"
_NOW = Timestamp(datetime(2026, 11, 15, tzinfo=timezone.utc))


def _ledger_and_registration() -> tuple[FakeEvidenceLedger, ResultRegistration]:
    ledger = FakeEvidenceLedger()
    evidence = Evidence(
        id="evidence:1",
        source_ref=_SOURCE,
        content_digest="sha256:" + "0" * 64,
        artifact_id=_SOURCE,
    )
    claim = Claim(
        id="claim:1",
        statement="verified claim",
        status=ClaimStatus.PROPOSED,
        evidence_relations=[("evidence:1", EvidenceRelationType.SUPPORTS)],
    )
    ledger.register_source(
        SourceRecord(
            origin=_SOURCE,
            content_digest="sha256:" + "0" * 64,
            trust_label=TrustLabel.GENERATED,
            access_time=Timestamp.now(),
        )
    )
    ledger.register_evidence(evidence)
    ledger.register_claim(claim)
    ledger.attach_relation(EvidenceRelation("claim:1", "evidence:1", EvidenceRelationType.SUPPORTS))
    ledger.update_claim(
        Claim(
            id=claim.id,
            statement=claim.statement,
            status=ClaimStatus.VERIFIED,
            author=claim.author,
            evidence_relations=claim.evidence_relations,
        )
    )
    return ledger, ResultRegistration(artifacts=(), evidence=(evidence,), claims=(claim,))


def _gate(store: FakeMemoryStore, ledger: FakeEvidenceLedger) -> MemoryGateDeps:
    return MemoryGateDeps(
        store=store,
        policy=FakePolicyEvaluator(),
        ledger=ledger,
        actor="system:ig1",
    )


class _Deps:
    """`promote_memory` 的最小装配面（只读 `memory_gate` 一个字段）。"""

    def __init__(self, gate: MemoryGateDeps | None) -> None:
        self.memory_gate = gate


def test_a_declared_contract_promotes_into_project_memory() -> None:
    """① 正例：声明在场 ⇒ PROJECT 档提交，授权来自合约 `memory_export`（判词点名）。"""
    ledger, registration = _ledger_and_registration()
    store = FakeMemoryStore()
    promote_memory(
        _Deps(_gate(store, ledger)),
        registration,
        memory_export=MemoryExportSpec(tier=MemoryTier.PROJECT),
    )
    records = store.query()
    assert records, (
        "合约声明了 memory_export ⇒ 必须晋升；本 run 的 curator 授权来自合约 memory_export"
    )
    record = records[0]
    assert record.tier is MemoryTier.PROJECT, record
    assert record.scope == "project", record
    assert record.provenance == _SOURCE, ("provenance 指向本 run 的 evidence", record)
    assert record.kind is MemoryType.FACT, record


def test_without_the_declaration_nothing_is_promoted() -> None:
    """② 反证（零回归）：合约不带 `memory_export` ⇒ 不晋升（不是拒绝，是无通道）。"""
    ledger, registration = _ledger_and_registration()
    store = FakeMemoryStore()
    promote_memory(_Deps(_gate(store, ledger)), registration, memory_export=None)
    assert store.query() == (), "缺省 None ⇒ 不晋升；既有 34 份合约行为逐字不变"


def test_no_gate_wired_means_no_promotion() -> None:
    """② 反证（装配侧）：gate 没接 ⇒ 不晋升（既有语义逐字不变）。"""
    ledger, registration = _ledger_and_registration()
    store = FakeMemoryStore()
    promote_memory(_Deps(None), registration, memory_export=MemoryExportSpec())
    assert store.query() == (), "memory_gate=None ⇒ 不晋升（装配缺省逐字不变）"


def test_the_curator_gate_still_bites_with_the_declaration_present() -> None:
    """③ 反证：同一提案、`curator_approved=False` ⇒ 不写入且点名 curator 阶段。

    证明「声明即绕过门」不成立：晋升路径写入与否的差别**只在** curator 标志 ——
    门链（`gate.py` 的 `_CURATOR_TIERS`）承担判定，声明只是授权来源。
    """
    ledger, registration = _ledger_and_registration()
    store = FakeMemoryStore()
    ctx = MemoryPromotionContext(
        memory_gate=_gate(store, ledger),
        tier=MemoryTier.PROJECT,
        curator_approved=False,
    )
    records = promote_memory_from_registration(ctx, registration)
    assert records == (), "curator 门必须咬住 PROJECT 档（无授权不写入）"
    assert store.query() == (), store.query()
    # 提案本体未入库 ⇒ 门的拒绝发生在 curator 阶段（用门自身逐字判词钉住）。
    gate = _gate(store, ledger)
    proposal = MemoryWriteProposal(
        id="memory:claim:1",
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content="Claim claim:1: verified claim",
        provenance=_SOURCE,
        confidence=0.8,
        scope="project",
        proposed_by="system:ig1",
    )
    denied = evaluate_memory_proposal(proposal, gate, curator_approved=False)
    assert denied.accepted is False, denied
    assert denied.stage == "curator", ("点名 curator 阶段", denied)
    assert "PROJECT" in " ".join(denied.reasons), denied.reasons


def test_the_next_run_reads_the_committed_record_in_its_prior_knowledge() -> None:
    """④ 读得到：提交后下一轮 `prior_knowledge` 非空，渲染行逐字匹配。"""
    ledger, registration = _ledger_and_registration()
    store = FakeMemoryStore()
    promote_memory(
        _Deps(_gate(store, ledger)),
        registration,
        memory_export=MemoryExportSpec(tier=MemoryTier.PROJECT),
    )
    view = build_prior_knowledge(store, now=_NOW, run_id="next-run")
    assert view.entries, ("同一项目的下一轮必须读得到", view.reason)
    rendered = render_prior_knowledge_prompt(view)
    record = store.query()[0]
    expected = f"- {record.id}: {record.content} (source: {record.provenance})"
    assert expected in rendered, ("渲染行逐字匹配（无标记时 marks 为空）", rendered)
