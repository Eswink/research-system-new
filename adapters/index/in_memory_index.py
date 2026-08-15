"""InMemoryRetrievalIndex：RetrievalIndex Port 的确定性内存实现。

派生条目存 (memory_id, content_hash)；search 用 token 重叠确定性评分
（非语义检索）；rebuild 全量替换；close 后不可用。无 embedding 依赖。
"""

from __future__ import annotations

from adapters.index.base import IndexAdapterBase
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.retrieval_index import (
    IndexEntry,
    IndexHit,
    content_hash_of,
)
from packages.domain.memory import MemoryRecord


def _tokens(text: str) -> set[str]:
    return {token for token in text.lower().split() if token}


def _score(content: str, query_tokens: set[str]) -> float:
    overlap = len(query_tokens & _tokens(content))
    return overlap / len(query_tokens) if query_tokens else 0.0


class InMemoryRetrievalIndex(IndexAdapterBase):
    """确定性内存索引；条目只读视图 entries() 供一致性检查。"""

    def __init__(self) -> None:
        super().__init__("retrieval_index")
        self._records: dict[str, MemoryRecord] = {}

    def rebuild(self, records: tuple[MemoryRecord, ...]) -> None:
        self._ensure_open()
        self._records = {record.id: record for record in records if record.active}
        self._record("rebuild", f"{len(records)} records", result=str(len(self._records)))

    def upsert(self, record: MemoryRecord) -> None:
        self._ensure_open()
        if record.active:
            self._records[record.id] = record
            self._record("upsert", record.id, result="indexed")
        else:
            self.remove(record.id)

    def remove(self, memory_id: str) -> None:
        self._ensure_open()
        if memory_id in self._records:
            del self._records[memory_id]
            self._record("remove", memory_id, result="removed")
        else:
            self._record("remove", memory_id, result="absent")

    def search(self, query: str, limit: int = 10) -> tuple[IndexHit, ...]:
        self._ensure_open()
        if limit < 0:
            self._record("search", query, error="InvalidInputError")
            raise InvalidInputError("limit must be non-negative")
        query_tokens = _tokens(query)
        hits = [
            IndexHit(memory_id=record.id, score=_score(record.content, query_tokens))
            for record in self._records.values()
        ]
        hits = sorted(hits, key=lambda hit: (-hit.score, hit.memory_id))
        result = tuple(hit for hit in hits[:limit] if hit.score > 0.0)
        self._record("search", query, result=str(len(result)))
        return result

    def entries(self) -> tuple[IndexEntry, ...]:
        self._ensure_open()
        result = tuple(
            IndexEntry(memory_id=record.id, content_hash=content_hash_of(record))
            for record in self._records.values()
        )
        self._record("entries", "*", result=str(len(result)))
        return result

    def clear(self) -> None:
        self._ensure_open()
        self._records = {}
        self._record("clear", "*", result="cleared")
