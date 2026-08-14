"""FakeToolPackStore：ToolPack 注册状态内存实现（错误注入 + 调用记录）。"""

from __future__ import annotations

from dataclasses import replace

from adapters.fakes.base import FakeBase
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.tool_pack_store import ToolPackRecord
from packages.domain.enums import ToolPackState


class FakeToolPackStore(FakeBase):
    """install 重复抛 InvalidInputError；revoke 幂等拒绝；snapshot 确定性。"""

    def __init__(self) -> None:
        super().__init__("tool_pack_store")
        self._records: dict[str, ToolPackRecord] = {}

    def install(self, record: ToolPackRecord) -> None:
        self._enter("install", record.pack_id)
        if record.pack_id in self._records:
            self._record("install", record.pack_id, error="InvalidInputError")
            raise InvalidInputError(f"tool pack already installed: {record.pack_id}")
        self._records[record.pack_id] = record
        self._record("install", record.pack_id, result="stored")

    def replace(self, record: ToolPackRecord) -> None:
        self._enter("replace", record.pack_id)
        if record.pack_id not in self._records:
            self._record("replace", record.pack_id, error="InvalidInputError")
            raise InvalidInputError(f"tool pack not installed: {record.pack_id}")
        self._records[record.pack_id] = record
        self._record("replace", record.pack_id, result="stored")

    def revoke(self, pack_id: str, reason: str) -> None:
        self._enter("revoke", pack_id)
        record = self._records.get(pack_id)
        if record is None:
            self._record("revoke", pack_id, error="InvalidInputError")
            raise InvalidInputError(f"tool pack not installed: {pack_id}")
        revoked = replace(record, state=ToolPackState.REVOKED, revoked_reason=reason)
        self._records[pack_id] = revoked
        self._record("revoke", pack_id, result="revoked")

    def get(self, pack_id: str) -> ToolPackRecord | None:
        self._enter("get", pack_id)
        record = self._records.get(pack_id)
        self._record("get", pack_id, result="hit" if record else "miss")
        return record

    def snapshot(self) -> dict[str, ToolPackRecord]:
        self._enter("snapshot", "*")
        result = dict(sorted(self._records.items()))
        self._record("snapshot", "*", result=f"{len(result)} records")
        return result

    def close(self) -> None:
        super().close()
        self._records.clear()
        self._record("close", "*", result="closed")
