"""FakeRetrievalIndex：RetrievalIndex Port 的 test-double（deterministic + 注入）。

委托 InMemoryRetrievalIndex 实现检索逻辑；本类提供 FakeBase 语义
（call recording / set_script 错误注入 / close），供 common contract
suite 与其他 Fake 同构复用。
"""

from __future__ import annotations

from adapters.fakes.base import FakeBase
from adapters.index.in_memory_index import InMemoryRetrievalIndex
from packages.application.ports.retrieval_index import IndexEntry, IndexHit
from packages.domain.memory import MemoryRecord


class FakeRetrievalIndex(FakeBase):
    """deterministic test-double；逻辑委托 InMemoryRetrievalIndex。"""

    def __init__(self) -> None:
        super().__init__("retrieval_index")
        self._inner = InMemoryRetrievalIndex()

    def rebuild(self, records: tuple[MemoryRecord, ...]) -> None:
        self._enter("rebuild", str(len(records)))
        self._inner.rebuild(records)
        self._record("rebuild", str(len(records)), result="rebuilt")

    def upsert(self, record: MemoryRecord) -> None:
        self._enter("upsert", record.id)
        self._inner.upsert(record)
        self._record("upsert", record.id, result="indexed")

    def remove(self, memory_id: str) -> None:
        self._enter("remove", memory_id)
        self._inner.remove(memory_id)
        self._record("remove", memory_id, result="removed")

    def search(self, query: str, limit: int = 10) -> tuple[IndexHit, ...]:
        self._enter("search", query)
        hits = self._inner.search(query, limit)
        self._record("search", query, result=str(len(hits)))
        return hits

    def entries(self) -> tuple[IndexEntry, ...]:
        self._enter("entries", "*")
        result = self._inner.entries()
        self._record("entries", "*", result=str(len(result)))
        return result

    def clear(self) -> None:
        self._enter("clear", "*")
        self._inner.clear()
        self._record("clear", "*", result="cleared")
