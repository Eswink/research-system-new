"""SqliteIdempotencyStore：Idempotency-Key 响应的 SQLite 持久化（M13-R1 WP-M1）。

实现 services/api/idempotency.py 的 IdempotencyStore Protocol；替换内存
实现：API 重启后重复提交仍重放首次响应（幂等语义跨重启保持）。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, now_iso
from services.api.idempotency import StoredResponse

_SCHEMA = """
CREATE TABLE IF NOT EXISTS idempotency_responses (
    idem_key TEXT PRIMARY KEY,
    request_digest TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    body TEXT NOT NULL,
    etag TEXT,
    saved_at TEXT NOT NULL
);
"""


class SqliteIdempotencyStore(SqliteAdapterBase):
    """SQLite 持久化 IdempotencyStore；get/put + close 语义。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("idempotency_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def get(self, key: str) -> StoredResponse | None:
        self._ensure_open()
        row = self._conn.execute(
            "SELECT request_digest, status_code, body, etag FROM idempotency_responses"
            " WHERE idem_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            self._record("get", key, result="None")
            return None
        self._record("get", key, result=row["request_digest"][:12])
        return StoredResponse(
            request_digest=row["request_digest"],
            status_code=int(row["status_code"]),
            body=row["body"].encode("utf-8"),
            etag=row["etag"],
        )

    def put(self, key: str, value: StoredResponse) -> None:
        self._ensure_open()
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO idempotency_responses"
                " (idem_key, request_digest, status_code, body, etag, saved_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    key,
                    value.request_digest,
                    value.status_code,
                    value.body.decode("utf-8"),
                    value.etag,
                    now_iso(None),
                ),
            )
        self._record("put", key)
