"""ToolPackStore 生命周期契约测试（install/update/revoke 状态语义）。"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from adapters.fakes import FakeToolPackStore
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.tool_pack_store import ToolPackRecord
from packages.domain.core import Digest, Timestamp, Version
from packages.domain.enums import ToolPackState
from packages.domain.tools import ToolPackManifest

NOW = datetime(2026, 8, 14, 12, 0, 0, tzinfo=timezone.utc)


def _record(pack_id: str = "lit-pack") -> ToolPackRecord:
    return ToolPackRecord(
        pack_id=pack_id,
        state=ToolPackState.INSTALLED,
        manifest=ToolPackManifest(
            id=pack_id,
            version=Version("1.0.0"),
            source="fixture://lit-pack",
            resolved_revision="abc123",
            digest=Digest.of_bytes(b"placeholder"),
            license="MIT",
        ),
        installed_at=Timestamp(NOW),
    )


class TestToolPackStoreContract:
    def test_install_then_get_roundtrip(self) -> None:
        store = FakeToolPackStore()
        record = _record()
        store.install(record)
        assert store.get("lit-pack") == record
        assert set(store.snapshot()) == {"lit-pack"}

    def test_duplicate_install_rejected(self) -> None:
        store = FakeToolPackStore()
        store.install(_record())
        with pytest.raises(InvalidInputError):
            store.install(_record())

    def test_replace_requires_installed(self) -> None:
        store = FakeToolPackStore()
        with pytest.raises(InvalidInputError):
            store.replace(_record())

    def test_revoke_marks_state_and_reason(self) -> None:
        store = FakeToolPackStore()
        store.install(_record())
        store.revoke("lit-pack", "supply chain alert")
        record = store.get("lit-pack")
        assert record is not None
        assert record.state is ToolPackState.REVOKED
        assert record.revoked_reason == "supply chain alert"

    def test_revoke_unknown_pack_rejected(self) -> None:
        store = FakeToolPackStore()
        with pytest.raises(InvalidInputError):
            store.revoke("missing-pack", "reason")

    def test_revoked_record_requires_reason(self) -> None:
        with pytest.raises(ValueError):
            replace(_record(), state=ToolPackState.REVOKED)

    def test_record_rejects_pack_id_mismatch(self) -> None:
        with pytest.raises(ValueError):
            replace(_record(), pack_id="other-id")
