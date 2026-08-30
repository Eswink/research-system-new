"""FakePricingSnapshotStore：内存定价快照 Port 实现(M15 WP3a)。"""

from __future__ import annotations

from adapters.fakes.base import FakeBase
from packages.application.cost.pricing import PricingTable


class FakePricingSnapshotStore(FakeBase):
    """按 (version, digest) 保存不可变 PricingTable，put/get 幂等。"""

    def __init__(self) -> None:
        super().__init__("pricing_snapshot_store")
        self._tables: dict[tuple[str, str], PricingTable] = {}

    def put(self, table: PricingTable) -> None:
        self._enter("put", table.version)
        digest = table.pricing_digest()
        self._tables.setdefault((table.version, digest), table)
        self._record("put", f"{table.version}@{digest[:12]}", result="stored")

    def get(self, version: str, digest: str) -> PricingTable | None:
        self._enter("get", f"{version}@{digest[:12]}")
        table = self._tables.get((version, digest))
        self._record("get", f"{version}@{digest[:12]}", result="hit" if table else "miss")
        return table


__all__ = ["FakePricingSnapshotStore"]
