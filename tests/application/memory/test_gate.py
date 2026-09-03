"""MemoryWriteProposal gate 全链路测试（M10 DoD 三类路径）。

覆盖：无 provenance 拒绝、policy deny、curator 通过、schema 校验、
supersedes 引用完整性、MEMORY_PROPOSED/MEMORY_COMMITTED 事件、
绕过 pipeline 的防御纵深。
"""

from __future__ import annotations

import pytest

from adapters.fakes import (
    FakeEventPublisher,
    FakeEvidenceLedger,
    FakeMemoryStore,
    FakePolicyEvaluator,
)
from packages.application.memory.gate import (
    GateResult,
    MemoryGateDeps,
    commit_memory,
    evaluate_memory_proposal,
)
from packages.application.ports.errors import InvalidInputError
from packages.domain.enums import MemoryTier, PolicyDecision, TrustLabel
from packages.domain.events import EventType
from packages.domain.evidence import SourceRecord
from packages.domain.memory import MemoryWriteProposal
from tests.contracts.fixtures import memory_proposal


def _store() -> FakeMemoryStore:
    return FakeMemoryStore(allowed_sources=("source:article-1",))


def _deps(
    store: FakeMemoryStore,
    *,
    policy: FakePolicyEvaluator | None = None,
    ledger: FakeEvidenceLedger | None = None,
    publisher: FakeEventPublisher | None = None,
) -> MemoryGateDeps:
    return MemoryGateDeps(
        store=store,
        policy=policy,
        ledger=ledger,
        publisher=publisher,
        allowed_sources=frozenset({"source:article-1"}),
    )


def _proposal(
    proposal_id: str = "mem-1",
    *,
    tier: MemoryTier = MemoryTier.RUN,
    provenance: str = "source:article-1",
) -> MemoryWriteProposal:
    proposal = memory_proposal(proposal_id)
    return MemoryWriteProposal(
        id=proposal.id,
        tier=tier,
        kind=proposal.kind,
        content=proposal.content,
        provenance=provenance,
        confidence=proposal.confidence,
    )


class TestProvenanceRejection:
    def test_unregistered_provenance_rejected_at_provenance_stage(self) -> None:
        store = _store()
        result = evaluate_memory_proposal(_proposal(provenance="source:untrusted"), _deps(store))
        assert result.accepted is False
        assert result.stage == "provenance"
        assert result.decision is PolicyDecision.DENY

    def test_unregistered_provenance_commit_rejected(self) -> None:
        store = _store()
        result = commit_memory(_proposal(provenance="source:untrusted"), _deps(store))
        assert result.accepted is False
        assert store.query() == ()

    def test_ledger_registered_provenance_accepted(self) -> None:
        store = FakeMemoryStore()
        ledger = FakeEvidenceLedger()
        ledger.register_source(
            SourceRecord(
                origin="source:article-2",
                content_digest="sha256:aa",
                trust_label=TrustLabel.VERIFIED_SOURCE,
            )
        )
        result = evaluate_memory_proposal(
            _proposal(provenance="source:article-2"),
            _deps(store, ledger=ledger),
        )
        assert result.accepted is True

    def test_ledger_verified_provenance_commits_without_store_whitelist(self) -> None:
        """PA-1 F1: gate 经 ledger 验证来源后，store 白名单自动打开；
        组合根无需预置 allowed_sources 也能提交受控内存。"""
        store = FakeMemoryStore()  # 空白名单 = deny-by-default
        ledger = FakeEvidenceLedger()
        ledger.register_source(
            SourceRecord(
                origin="source:article-2",
                content_digest="sha256:aa",
                trust_label=TrustLabel.VERIFIED_SOURCE,
            )
        )
        result = commit_memory(
            _proposal("mem-ledger", provenance="source:article-2"),
            _deps(store, ledger=ledger),
        )
        assert result.accepted is True
        assert result.record is not None
        assert store.get("mem-ledger").provenance == "source:article-2"


class TestSchemaRejection:
    def test_blank_content_rejected_at_schema_stage(self) -> None:
        store = _store()
        proposal = _proposal()
        blank = MemoryWriteProposal(
            id=proposal.id,
            tier=proposal.tier,
            kind=proposal.kind,
            content="   ",
            provenance=proposal.provenance,
            confidence=proposal.confidence,
        )
        result = evaluate_memory_proposal(blank, _deps(store))
        assert result.accepted is False
        assert result.stage == "schema"


class TestPolicyDeny:
    def test_policy_deny_rejected_at_policy_stage(self) -> None:
        store = _store()
        policy = FakePolicyEvaluator()
        policy.set_decision("memory.write", PolicyDecision.DENY)
        result = evaluate_memory_proposal(_proposal(), _deps(store, policy=policy))
        assert result.accepted is False
        assert result.stage == "policy"

    def test_policy_require_approval_without_curator_rejected(self) -> None:
        store = _store()
        policy = FakePolicyEvaluator()
        policy.set_decision("memory.write", PolicyDecision.REQUIRE_APPROVAL)
        result = evaluate_memory_proposal(_proposal(), _deps(store, policy=policy))
        assert result.accepted is False
        assert result.stage == "policy"

    def test_policy_require_approval_with_curator_accepted(self) -> None:
        store = _store()
        policy = FakePolicyEvaluator()
        policy.set_decision("memory.write", PolicyDecision.REQUIRE_APPROVAL)
        result = evaluate_memory_proposal(
            _proposal(), _deps(store, policy=policy), curator_approved=True
        )
        assert result.accepted is True


class TestCuratorGate:
    def test_project_tier_requires_curator_approval(self) -> None:
        store = _store()
        result = evaluate_memory_proposal(_proposal(tier=MemoryTier.PROJECT), _deps(store))
        assert result.accepted is False
        assert result.stage == "curator"

    def test_project_tier_with_curator_approval_accepted(self) -> None:
        store = _store()
        result = evaluate_memory_proposal(
            _proposal(tier=MemoryTier.PROJECT), _deps(store), curator_approved=True
        )
        assert result.accepted is True

    def test_session_and_run_tiers_automatic(self) -> None:
        store = _store()
        assert evaluate_memory_proposal(_proposal(tier=MemoryTier.SESSION), _deps(store)).accepted
        assert evaluate_memory_proposal(_proposal(tier=MemoryTier.RUN), _deps(store)).accepted


class TestCommitPath:
    def test_curator_approved_commit_publishes_events(self) -> None:
        store = _store()
        publisher = FakeEventPublisher()
        result = commit_memory(
            _proposal("mem-1", tier=MemoryTier.PROJECT),
            _deps(store, publisher=publisher),
            curator_approved=True,
        )
        assert result.accepted is True
        assert result.record is not None
        assert store.get("mem-1").content == "verified fact"
        events = {envelope.event_type for envelope in publisher.published}
        assert EventType.MEMORY_PROPOSED in events
        assert EventType.MEMORY_COMMITTED in events
        order = [envelope.event_type for envelope in publisher.published]
        assert order.index(EventType.MEMORY_PROPOSED) < order.index(EventType.MEMORY_COMMITTED)

    def test_rejected_proposal_publishes_no_memory_events(self) -> None:
        store = _store()
        publisher = FakeEventPublisher()
        result = commit_memory(
            _proposal(provenance="source:untrusted"),
            _deps(store, publisher=publisher),
        )
        assert result.accepted is False
        assert publisher.published == ()


class TestContradictionCheck:
    def test_supersedes_unknown_target_rejected(self) -> None:
        store = _store()
        proposal = _proposal("mem-2")
        missing = MemoryWriteProposal(
            id=proposal.id,
            tier=proposal.tier,
            kind=proposal.kind,
            content=proposal.content,
            provenance=proposal.provenance,
            confidence=proposal.confidence,
            supersedes=["mem-missing"],
        )
        result = evaluate_memory_proposal(missing, _deps(store))
        assert result.accepted is False
        assert result.stage == "contradiction"

    def test_supersedes_existing_target_accepted(self) -> None:
        store = _store()
        store.commit(_proposal("mem-1"))
        proposal = _proposal("mem-2")
        superseding = MemoryWriteProposal(
            id=proposal.id,
            tier=proposal.tier,
            kind=proposal.kind,
            content=proposal.content,
            provenance=proposal.provenance,
            confidence=proposal.confidence,
            supersedes=["mem-1"],
        )
        result = evaluate_memory_proposal(superseding, _deps(store))
        assert result.accepted is True


class TestBypassDefense:
    def test_direct_store_commit_without_pipeline_rejected(self) -> None:
        """绕过 pipeline 直调 MemoryStore：Fake 白名单是防御纵深。"""
        store = FakeMemoryStore(allowed_sources=("source:article-1",))
        with pytest.raises(InvalidInputError):
            store.commit(_proposal(provenance="source:untrusted"))

    def test_gate_result_is_classifiable(self) -> None:
        result = GateResult(accepted=False, stage="provenance", decision=PolicyDecision.DENY)
        assert result.stage == "provenance"
        assert result.decision is PolicyDecision.DENY
