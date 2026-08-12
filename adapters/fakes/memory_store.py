"""FakeMemoryStore：Memory 写入门禁 + 持久化（CONTEXT_ENGINE.md §6）。"""

from __future__ import annotations

from adapters.fakes.base import FakeBase
from packages.application.ports.errors import InvalidInputError
from packages.domain.enums import MemoryTier
from packages.domain.memory import MemoryRecord, MemoryWriteProposal


class FakeMemoryStore(FakeBase):
    """commit 执行 provenance gate；未授权来源的写入被拒绝。"""

    def __init__(self, allowed_sources: tuple[str, ...] = ()) -> None:
        super().__init__("memory_store")
        self._allowed_sources = set(allowed_sources)
        self._records: dict[str, MemoryRecord] = {}

    def allow_source(self, source: str) -> None:
        self._allowed_sources.add(source)

    def commit(self, proposal: MemoryWriteProposal) -> MemoryRecord:
        self._enter("commit", proposal.id)
        if self._allowed_sources and proposal.provenance not in self._allowed_sources:
            self._record("commit", proposal.id, error="InvalidInputError")
            raise InvalidInputError(
                f"memory provenance gate rejected source {proposal.provenance!r}",
            )
        record = MemoryRecord(
            id=proposal.id,
            tier=proposal.tier,
            kind=proposal.kind,
            content=proposal.content,
            provenance=proposal.provenance,
            confidence=proposal.confidence,
        )
        self._records[record.id] = record
        self._record("commit", proposal.id, result="committed")
        return record

    def get(self, memory_id: str) -> MemoryRecord:
        self._enter("get", memory_id)
        if memory_id not in self._records:
            self._record("get", memory_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown memory id: {memory_id}")
        self._record("get", memory_id)
        return self._records[memory_id]

    def query(self, tier: MemoryTier | None = None) -> tuple[MemoryRecord, ...]:
        self._enter("query", tier.value if tier else "*")
        records = tuple(
            record for record in self._records.values() if tier is None or record.tier is tier
        )
        self._record("query", tier.value if tier else "*", result=str(len(records)))
        return records

    def delete(self, memory_id: str) -> None:
        self._enter("delete", memory_id)
        if memory_id not in self._records:
            self._record("delete", memory_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown memory id: {memory_id}")
        del self._records[memory_id]
        self._record("delete", memory_id)
