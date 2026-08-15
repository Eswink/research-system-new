"""M10 独立复审对抗性回归：gate bypass / 幂等 / adapter 缺陷检测。

这些测试锁定独立复审发现并修复的缺陷：
- supersede_memory 未走 gate 可绕过 provenance/policy（BLOCKER，已修复）；
- FakeMemoryStore 空白名单放行任意 provenance（BLOCKER，已修复）；
- 同 id 重复 commit 静默覆盖 + 事件风暴（MAJOR，已修复）；
- contradiction check 的宽异常把 store 故障误判为拒绝（MAJOR，已修复）；
- commit_memory 对 adapter 返回记录无一致性校验（MAJOR，已修复）。
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from adapters.fakes import (
    FakeEventPublisher,
    FakeMemoryStore,
    FakePolicyEvaluator,
)
from packages.application.memory.gate import (
    MemoryGateDeps,
    commit_memory,
    evaluate_memory_proposal,
)
from packages.application.memory.lifecycle import (
    MemoryLifecycleDeps,
    supersede_memory,
)
from packages.application.ports.errors import InvalidInputError, PortError
from packages.domain.enums import MemoryTier, PolicyDecision
from packages.domain.events import EventType
from packages.domain.memory import MemoryRecord, MemoryWriteProposal
from tests.contracts.fixtures import memory_proposal


def _proposal(
    proposal_id: str,
    *,
    tier: MemoryTier = MemoryTier.RUN,
    provenance: str = "source:article-1",
    content: str = "verified fact",
) -> MemoryWriteProposal:
    base = memory_proposal(proposal_id)
    return MemoryWriteProposal(
        id=base.id,
        tier=tier,
        kind=base.kind,
        content=content,
        provenance=provenance,
        confidence=base.confidence,
    )


def _gate_deps(
    store: FakeMemoryStore,
    *,
    policy: FakePolicyEvaluator | None = None,
    publisher: FakeEventPublisher | None = None,
    allowed: frozenset[str] = frozenset({"source:article-1"}),
) -> MemoryGateDeps:
    return MemoryGateDeps(
        store=store,
        policy=policy,
        publisher=publisher,
        allowed_sources=allowed,
    )


class TestSupersedeGateBypass:
    """supersede_memory 必须走正式 gate；未授权 provenance / policy deny 拒绝。"""

    def test_supersede_with_unregistered_provenance_rejected(self) -> None:
        store = FakeMemoryStore(allowed_sources=("source:article-1",))
        store.commit(_proposal("mem-old"))
        gate_deps = _gate_deps(store, allowed=frozenset({"source:article-1"}))
        with pytest.raises(InvalidInputError, match="supersede proposal rejected"):
            supersede_memory(
                MemoryLifecycleDeps(store=store),
                "mem-old",
                _proposal("mem-new", provenance="source:untrusted"),
                gate_deps=gate_deps,
            )
        # 旧记录未受影响，新记录未入账
        assert store.get("mem-old").active is True
        with pytest.raises(InvalidInputError):
            store.get("mem-new")

    def test_supersede_with_policy_deny_rejected(self) -> None:
        store = FakeMemoryStore(allowed_sources=("source:article-1",))
        store.commit(_proposal("mem-old"))
        policy = FakePolicyEvaluator()
        policy.set_decision("memory.write", PolicyDecision.DENY)
        gate_deps = _gate_deps(store, policy=policy)
        with pytest.raises(InvalidInputError, match="supersede proposal rejected"):
            supersede_memory(
                MemoryLifecycleDeps(store=store),
                "mem-old",
                _proposal("mem-new"),
                gate_deps=gate_deps,
            )
        assert store.get("mem-old").active is True

    def test_supersede_project_tier_with_curator_approval_accepted(self) -> None:
        store = FakeMemoryStore(allowed_sources=("source:article-1",))
        store.commit(_proposal("mem-old", tier=MemoryTier.PROJECT))
        gate_deps = _gate_deps(store)
        record = supersede_memory(
            MemoryLifecycleDeps(store=store),
            "mem-old",
            _proposal("mem-new", tier=MemoryTier.PROJECT),
            gate_deps=gate_deps,
            curator_approved=True,
        )
        assert record.id == "mem-new"
        assert store.get("mem-old").active is False
        assert store.get("mem-new").active is True

    def test_supersede_inactive_target_rejected(self) -> None:
        store = FakeMemoryStore(allowed_sources=("source:article-1",))
        store.commit(_proposal("mem-old"))
        store.deactivate("mem-old")
        gate_deps = _gate_deps(store)
        with pytest.raises(InvalidInputError, match="inactive"):
            supersede_memory(
                MemoryLifecycleDeps(store=store),
                "mem-old",
                _proposal("mem-new"),
                gate_deps=gate_deps,
            )


class TestStoreDenyByDefault:
    """FakeMemoryStore 空白名单 = deny-by-default，不是放行。"""

    def test_empty_allowlist_rejects_direct_commit(self) -> None:
        store = FakeMemoryStore()
        with pytest.raises(InvalidInputError, match="deny by default"):
            store.commit(_proposal("mem-x", provenance="source:totally-unknown"))

    def test_duplicate_commit_rejected_no_silent_overwrite(self) -> None:
        store = FakeMemoryStore(allowed_sources=("source:article-1",))
        store.commit(_proposal("mem-1", content="content-A"))
        with pytest.raises(InvalidInputError, match="already committed"):
            store.commit(_proposal("mem-1", content="content-B"))
        assert store.get("mem-1").content == "content-A"

    def test_repeated_commit_memory_publishes_no_event_storm(self) -> None:
        store = FakeMemoryStore(allowed_sources=("source:article-1",))
        publisher = FakeEventPublisher()
        deps = _gate_deps(store, publisher=publisher)
        first = commit_memory(_proposal("mem-1"), deps)
        assert first.accepted is True
        with pytest.raises(InvalidInputError, match="already committed"):
            commit_memory(_proposal("mem-1"), deps)
        events = [envelope.event_type for envelope in publisher.published]
        # 重复提案不产生第二次 COMMITTED，也不产生第二条 canonical 记录
        assert events.count(EventType.MEMORY_COMMITTED) == 1
        assert len(store.query()) == 1
        assert store.get("mem-1").content == "verified fact"


class TestStoreFailurePropagation:
    """contradiction check 不得把 store 故障误分类为"引用不存在"。"""

    def test_store_failure_propagates_not_misclassified(self) -> None:
        class BrokenStore:
            def get(self, memory_id: str) -> object:
                raise PortError(
                    "store backend unavailable",
                    failure_category=None,
                    retryable=False,
                )

        deps = MemoryGateDeps(
            store=BrokenStore(),  # type: ignore[arg-type]
            allowed_sources=frozenset({"source:article-1"}),
        )

        proposal = _proposal("mem-1")
        with_supersedes = MemoryWriteProposal(
            id=proposal.id,
            tier=proposal.tier,
            kind=proposal.kind,
            content=proposal.content,
            provenance=proposal.provenance,
            confidence=proposal.confidence,
            supersedes=["mem-old"],
        )
        with pytest.raises(PortError, match="backend unavailable"):
            evaluate_memory_proposal(with_supersedes, deps)


class TestCommittedRecordVerification:
    """commit 后 adapter 返回记录与提案不一致必须失败，不得静默入账。"""

    def test_inconsistent_record_rejected_and_no_committed_event(self) -> None:
        class SwappingStore(FakeMemoryStore):
            def commit(self, proposal: MemoryWriteProposal) -> MemoryRecord:
                record = super().commit(proposal)
                return replace(record, content="swapped content")

        store = SwappingStore(allowed_sources=("source:article-1",))
        publisher = FakeEventPublisher()
        deps = _gate_deps(store, publisher=publisher)
        with pytest.raises(InvalidInputError, match="inconsistent with proposal"):
            commit_memory(_proposal("mem-1"), deps)
        events = [envelope.event_type for envelope in publisher.published]
        assert EventType.MEMORY_COMMITTED not in events


class TestSecretSanitization:
    """secret 样式内容在 commit 前脱敏；不得先入账后清理。"""

    def test_bearer_token_redacted_before_commit(self) -> None:
        store = FakeMemoryStore(allowed_sources=("source:article-1",))
        deps = _gate_deps(store)
        result = commit_memory(
            _proposal(
                "mem-secret",
                content="observed Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload",
            ),
            deps,
        )
        assert result.accepted is True
        committed = store.get("mem-secret").content
        assert "eyJhbGciOiJIUzI1NiJ9.payload" not in committed
        assert "***REDACTED***" in committed

    def test_api_key_pattern_redacted_before_commit(self) -> None:
        store = FakeMemoryStore(allowed_sources=("source:article-1",))
        deps = _gate_deps(store)
        result = commit_memory(
            _proposal("mem-key", content="used key sk-1234567890abcdef"),
            deps,
        )
        assert result.accepted is True
        committed = store.get("mem-key").content
        assert "sk-1234567890abcdef" not in committed
        assert "***REDACTED***" in committed

    def test_clean_content_committed_unchanged(self) -> None:
        store = FakeMemoryStore(allowed_sources=("source:article-1",))
        deps = _gate_deps(store)
        result = commit_memory(
            _proposal("mem-clean", content="treatment shows no significant effect"),
            deps,
        )
        assert result.accepted is True
        assert store.get("mem-clean").content == "treatment shows no significant effect"
