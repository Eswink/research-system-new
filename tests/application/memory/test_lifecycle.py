"""Memory lifecycle 测试：deactivate（tombstone）/ delete / supersede + 审计事件。"""

from __future__ import annotations

import pytest

from adapters.fakes import FakeEventPublisher, FakeMemoryStore
from packages.application.memory.gate import MemoryGateDeps
from packages.application.memory.lifecycle import (
    MemoryLifecycleDeps,
    deactivate_memory,
    delete_memory,
    supersede_memory,
)
from packages.application.ports.errors import InvalidInputError
from packages.domain.events import EventType
from packages.domain.memory import MemoryWriteProposal
from tests.contracts.fixtures import memory_proposal


def _store() -> FakeMemoryStore:
    return FakeMemoryStore(allowed_sources=("source:article-1",))


class TestDeactivate:
    def test_deactivate_marks_tombstone_and_preserves_history(self) -> None:
        store = _store()
        store.commit(memory_proposal("mem-1"))
        tombstone = deactivate_memory(MemoryLifecycleDeps(store=store), "mem-1")
        assert tombstone.active is False
        preserved = store.get("mem-1")
        assert preserved.active is False
        assert preserved.content == memory_proposal("mem-1").content

    def test_deactivate_unknown_rejected(self) -> None:
        store = _store()
        with pytest.raises(InvalidInputError):
            deactivate_memory(MemoryLifecycleDeps(store=store), "missing")


class TestDelete:
    def test_delete_removes_canonical_and_publishes_event(self) -> None:
        store = _store()
        publisher = FakeEventPublisher()
        store.commit(memory_proposal("mem-1"))
        delete_memory(
            MemoryLifecycleDeps(store=store, publisher=publisher, actor="curator:a"),
            "mem-1",
        )
        with pytest.raises(InvalidInputError):
            store.get("mem-1")
        events = [
            envelope
            for envelope in publisher.published
            if envelope.event_type is EventType.MEMORY_DELETED
        ]
        assert len(events) == 1
        assert events[0].payload["memory_id"] == "mem-1"
        assert events[0].actor == "curator:a"
        assert events[0].scope == "memory:mem-1"

    def test_delete_unknown_rejected(self) -> None:
        store = _store()
        with pytest.raises(InvalidInputError):
            delete_memory(MemoryLifecycleDeps(store=store), "missing")


class TestSupersede:
    def test_supersede_records_supersedes_and_deactivates_old(self) -> None:
        store = _store()
        store.commit(memory_proposal("mem-1"))
        replacement = MemoryWriteProposal(
            id="mem-2",
            tier=memory_proposal("mem-1").tier,
            kind=memory_proposal("mem-1").kind,
            content="updated fact",
            provenance="source:article-1",
            confidence=0.95,
        )
        gate_deps = MemoryGateDeps(store=store, allowed_sources=frozenset({"source:article-1"}))
        record = supersede_memory(
            MemoryLifecycleDeps(store=store),
            "mem-1",
            replacement,
            gate_deps=gate_deps,
            curator_approved=True,
        )
        assert record.id == "mem-2"
        assert record.supersedes == ["mem-1"]
        assert store.get("mem-1").active is False
        assert store.get("mem-2").active is True

    def test_supersede_unknown_old_rejected(self) -> None:
        store = _store()
        gate_deps = MemoryGateDeps(store=store, allowed_sources=frozenset({"source:article-1"}))
        with pytest.raises(InvalidInputError):
            supersede_memory(
                MemoryLifecycleDeps(store=store),
                "missing",
                memory_proposal("mem-2"),
                gate_deps=gate_deps,
                curator_approved=True,
            )
