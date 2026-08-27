"""PostgreSQL shared infrastructure: DSN helpers + hand-rolled migration runner.

WP1: psycopg[binary] sync, deterministic ordering, transactional per-file,
failed migration rolls back, `bootstrap()` for clean DB.

No Alembic — migration_version table + versioned SQL files only.
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import psycopg
from psycopg.rows import dict_row

from packages.application.ports.errors import PermanentPortError
from packages.domain.enums import FailureCategory

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def _redacted(dsn: str) -> str:
    """Redact password from DSN for logs/errors (never log cleartext)."""
    text = re.sub(r"(password\s*=\s*)\S+", r"\1***REDACTED***", dsn, flags=re.IGNORECASE)
    text = re.sub(r"://[^@]*@", "://***REDACTED***@", text)
    return text


def _connect(dsn: str, *, autocommit: bool = False) -> Any:
    try:
        conn = psycopg.connect(dsn, row_factory=dict_row, autocommit=autocommit)
    except Exception as exc:  # pragma: no cover — connection failure path
        raise PermanentPortError(
            f"postgres connection failed: {_redacted(dsn)}",
            failure_category=FailureCategory.CONFIGURATION,
        ) from exc
    return conn


def _ensure_migration_table(conn: Any) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS migration_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL
        )
        """
    )


def _applied_versions(conn: Any) -> set[int]:
    rows: Any = conn.execute("SELECT version FROM migration_version").fetchall()
    return {int(cast(int, r["version"])) for r in rows}


def _discover_migrations() -> list[tuple[int, Path]]:
    files: list[tuple[int, Path]] = []
    for path in sorted(_MIGRATIONS_DIR.glob("*.sql")):
        stem = path.stem  # e.g. 001_initial
        try:
            ver = int(stem.split("_", 1)[0])
        except (ValueError, IndexError):
            continue
        files.append((ver, path))
    files.sort(key=lambda item: item[0])
    return files


def migrate(
    dsn: str,
    *,
    now: Callable[[], datetime] | None = None,
) -> list[int]:
    """Apply pending migrations in order; each file is one transaction.

    Returns list of newly applied versions (sorted). Failed file rolls back
    and raises `PermanentPortError` (redacted), leaving DB at prior version.
    Idempotent: re-running with no pending files returns [].
    """
    applied: list[int] = []
    ts = now() if now is not None else datetime.now(timezone.utc)
    if ts.tzinfo is None or ts.utcoffset() is None:
        raise ValueError("now() must return timezone-aware datetime")
    ts_utc = ts.astimezone(timezone.utc)
    conn: Any = _connect(dsn, autocommit=False)
    try:
        _ensure_migration_table(conn)
        conn.commit()
        existing = _applied_versions(conn)
        for ver, path in _discover_migrations():
            if ver in existing:
                continue
            sql = path.read_text(encoding="utf-8")
            try:
                with conn.transaction():
                    conn.execute(sql)
                    conn.execute(
                        "INSERT INTO migration_version (version, applied_at) VALUES (%s, %s)",
                        (ver, ts_utc),
                    )
            except Exception as exc:
                raise PermanentPortError(
                    f"migration {ver:03d} failed: {_redacted(dsn)}",
                    failure_category=FailureCategory.CONFIGURATION,
                ) from exc
            applied.append(ver)
        conn.commit()
    finally:
        conn.close()
    return applied


def bootstrap(
    dsn: str,
    *,
    now: Callable[[], datetime] | None = None,
) -> list[int]:
    """Clean bootstrap: ensure DB reachable then migrate. Returns applied versions."""
    return migrate(dsn, now=now)


def connect(dsn: str) -> Any:
    """Open a psycopg connection with dict_row (for postgres adapters)."""
    return _connect(dsn, autocommit=False)


def now_iso(now: Callable[[], datetime] | None) -> datetime:
    """UTC-aware now (for TIMESTAMPTZ columns)."""
    value = datetime.now(timezone.utc) if now is None else now()
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("now() must return timezone-aware datetime")
    return value.astimezone(timezone.utc)


def dsn_from_env() -> str | None:
    for key in ("DATABASE_URL", "RESEARCHOS_DATABASE_URL", "POSTGRES_DSN"):
        val = os.environ.get(key)
        if val:
            return val
    return None
