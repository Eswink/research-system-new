"""FakeResourceCatalog：preflight 只读目录（构造时注入快照）。"""

from __future__ import annotations

from adapters.fakes.base import FakeBase
from packages.application.ports.resource_catalog import CatalogSnapshot


class FakeResourceCatalog(FakeBase):
    """snapshot() 返回构造时注入的目录；可通过 set_snapshot 替换。"""

    def __init__(self, snapshot: CatalogSnapshot | None = None) -> None:
        super().__init__("resource_catalog")
        self._snapshot = snapshot or CatalogSnapshot()

    def set_snapshot(self, snapshot: CatalogSnapshot) -> None:
        self._snapshot = snapshot

    def snapshot(self) -> CatalogSnapshot:
        self._enter("snapshot", "")
        self._record("snapshot", "", result=str(len(self._snapshot.roles)))
        return self._snapshot
