"""PricingSnapshotStore 的 PostgreSQL 实现(M15 WP3a,定价冻结 BLOCKER-6)。

表结构见 migrations/006_pricing_snapshot.sql;(version, digest) 主键,
ON CONFLICT DO NOTHING(append-only:同键必同内容,不同内容是新键)。
"""

from __future__ import annotations

import json
from typing import Any

from adapters.postgres.base import PostgresAdapterBase
from packages.application.cost.pricing import PricingTable, pricing_table_from_dict


class PostgresPricingSnapshotStore(PostgresAdapterBase):
    """PostgreSQL 定价快照存储;(version, digest) 可寻址。"""

    def __init__(
        self,
        *,
        dsn: str | None = None,
        connection: Any | None = None,
    ) -> None:
        from psycopg.rows import dict_row

        from adapters.postgres.db import connect as pg_connect
        from adapters.postgres.db import dsn_from_env

        super().__init__("pricing_snapshot_store")
        self._owns_connection = connection is None
        if connection is not None:
            self._conn: Any = connection
        else:
            resolved = dsn or dsn_from_env()
            if not resolved:
                raise ValueError("PostgresPricingSnapshotStore requires dsn or connection")
            self._conn = pg_connect(resolved)
        try:
            self._conn.row_factory = dict_row
        except Exception:
            pass

    def close(self) -> None:
        if getattr(self, "_owns_connection", False):
            try:
                self._conn.close()
            except Exception:
                pass
        super().close()

    def put(self, table: PricingTable) -> None:
        self._ensure_open()
        digest = table.pricing_digest()
        self._conn.execute(
            "INSERT INTO pricing_snapshots (version, digest, table_json)"
            " VALUES (%s, %s, %s)"
            " ON CONFLICT (version, digest) DO NOTHING",
            (table.version, digest, json.dumps(_encode(table), ensure_ascii=False)),
        )
        self._record("put", f"{table.version}@{digest[:12]}")

    def get(self, version: str, digest: str) -> PricingTable | None:
        self._ensure_open()
        row = self._conn.execute(
            "SELECT table_json FROM pricing_snapshots WHERE version = %s AND digest = %s",
            (version, digest),
        ).fetchone()
        self._record("get", f"{version}@{digest[:12]}", result="hit" if row else "miss")
        if row is None:
            return None
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
