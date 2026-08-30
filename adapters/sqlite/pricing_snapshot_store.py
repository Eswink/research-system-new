"""PricingSnapshotStore 的 SQLite 实现(M15 WP3a,定价冻结 BLOCKER-6)。

(version, digest) 主键;put 幂等(同键必同内容——digest 是内容摘要),
append-only(不同内容产生新 (version, digest) 对,历史快照保留)。
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, now_iso
from packages.application.cost.pricing import (
    PriceDimension,
    PriceEntry,
    PricingTable,
    pricing_table_from_dict,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS pricing_snapshots (
    version TEXT NOT NULL,
    digest TEXT NOT NULL,
    table_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (version, digest)
);
"""


class SqlitePricingSnapshotStore(SqliteAdapterBase):
    """SQLite 定价快照存储;(version, digest) 可寻址。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("pricing_snapshot_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def put(self, table: PricingTable) -> None:
        self._ensure_open()
        digest = table.pricing_digest()
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO pricing_snapshots (version, digest, table_json, created_at)"
                " VALUES (?, ?, ?, ?)",
                (
                    table.version,
                    digest,
                    json.dumps(_encode(table), ensure_ascii=False, sort_keys=True),
                    now_iso(None),
                ),
            )
        self._record("put", f"{table.version}@{digest[:12]}")

    def get(self, version: str, digest: str) -> PricingTable | None:
        self._ensure_open()
        row = self._conn.execute(
            "SELECT table_json FROM pricing_snapshots WHERE version = ? AND digest = ?",
            (version, digest),
        ).fetchone()
        if row is None:
            self._record("get", f"{version}@{digest[:12]}", error="KeyError")
            return None
        self._record("get", f"{version}@{digest[:12]}")
        return pricing_table_from_dict(json.loads(row["table_json"]))


def _encode(table: PricingTable) -> dict[str, Any]:
    return {
        "version": table.version,
        "currency": table.currency,
        "effective_from": table.effective_from,
        "calculation_method": table.calculation_method,
        "prices": [
            {
                "dimension": entry.dimension.value,
                "resource_key": entry.resource_key,
                "unit": entry.unit,
                "unit_price_minor": entry.unit_price_minor,
            }
            for entry in table.prices
        ],
    }


__all__ = ["SqlitePricingSnapshotStore", "PriceDimension", "PriceEntry"]
