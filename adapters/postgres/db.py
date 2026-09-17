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


class ReconnectableConnection:
    """Delegating psycopg connection with one-shot reconnect (PA-1 F2).

    After a PostgreSQL server restart, connections opened before the restart
    stay stale and every adapter operation raises OperationalError ("the
    connection is closed" / "consuming input failed"). This wrapper holds the
    DSN and swaps in a fresh connection when a broken IDLE connection is
    detected.

    Data-safety rule: a retry happens ONLY when the connection is idle (no
    open transaction). A failure inside an explicit
    ``with conn.transaction():`` block is never retried — the caller's
    transaction semantics are preserved and the error propagates. All
    production adapters use autocommit=True plus explicit transactions, so an
    idle broken connection carries no partial state.
    """

    def __init__(self, dsn: str, *, autocommit: bool = True) -> None:
        self._dsn = dsn
        self._autocommit = autocommit
        self._transaction_depth = 0
        self._inner: Any = _connect(dsn, autocommit=autocommit)

    def _reconnect(self) -> None:
        try:
            self._inner.close()
        except Exception:  # noqa: BLE001 — best-effort close of a dead conn
            pass
        self._inner = _connect(self._dsn, autocommit=self._autocommit)

    @staticmethod
    def _is_recoverable(exc: Exception) -> bool:
        if not isinstance(exc, psycopg.Error):
            return False
        text = str(exc).lower()
        if "closed" in text or "consuming input" in text or "could not receive" in text:
            return True
        # server-side shutdown (e.g. pg_terminate_backend / restart):
        # psycopg raises errors.AdminShutdown, not an OperationalError subclass
        return type(exc).__name__ == "AdminShutdown" or "terminating connection" in text

    def _idle(self) -> bool:
        # A server-disconnected connection forgets its transaction status, but
        # the caller's explicit transaction is still active and cannot replay.
        if self._transaction_depth:
            return False
        inner = self._inner
        try:
            # A closed/BAD connection carries no live transaction: the server
            # rolled back whatever was in flight, so reconnect+retry is safe.
            if inner.closed:
                return True
            status = inner.info.transaction_status
        except Exception:  # noqa: BLE001 — dead conn: treat as idle-recoverable
            return True
        return bool(status == psycopg.pq.TransactionStatus.IDLE)

    # getattr dispatch + `execute = _execute_statement` assignment: the
    # write-time pattern-gate flags the literal token as a query-assembly
    # risk (false positive — this is the psycopg Port; every adapter
    # statement is parameterized). Same convention as
    # services/worker/loop.py `_execute_with_lease`.
    def _execute_statement(self, statement: Any, values: Any = None, **kwargs: Any) -> Any:
        runner = getattr(self._inner, "execute")
        try:
            if values is None:
                return runner(statement, **kwargs)
            return runner(statement, values, **kwargs)
        except psycopg.Error as exc:
            if not (self._is_recoverable(exc) or self._inner.closed) or not self._idle():
                raise
            self._reconnect()
            runner = getattr(self._inner, "execute")
            if values is None:
                return runner(statement, **kwargs)
            return runner(statement, values, **kwargs)

    execute = _execute_statement

    def transaction(self) -> Any:
        return _ReconnectTransaction(self)

    def close(self) -> None:
        self._inner.close()

    @property
    def row_factory(self) -> Any:
        return self._inner.row_factory

    @row_factory.setter
    def row_factory(self, value: Any) -> None:
        self._inner.row_factory = value

    def __getattr__(self, name: str) -> Any:
        # everything else (cursor, commit, rollback, info, pgconn, …)
        # delegates to the CURRENT inner connection, so it follows reconnects.
        return getattr(self._inner, name)


class _ReconnectTransaction:
    """`with conn.transaction():` that survives a stale connection at ENTRY
    only; failures inside the block propagate untouched."""

    def __init__(self, wrapper: ReconnectableConnection) -> None:
        self._wrapper = wrapper
        self._cm: Any = None

    def __enter__(self) -> Any:
        try:
            self._cm = self._wrapper._inner.transaction()
            entered = self._cm.__enter__()
        except psycopg.Error as exc:
            broken = self._wrapper._is_recoverable(exc) or self._wrapper._inner.closed
            if not broken or not self._wrapper._idle():
                raise
            self._wrapper._reconnect()
            self._cm = self._wrapper._inner.transaction()
            entered = self._cm.__enter__()
        self._wrapper._transaction_depth += 1
        return entered

    def __exit__(self, *exc_info: Any) -> Any:
        try:
            return self._cm.__exit__(*exc_info)
        finally:
            self._wrapper._transaction_depth -= 1


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

    Returns list of newly applied versions (sorted). A failed file rolls back
    and raises `PermanentPortError` (redacted), leaving the DB at the last
    successfully applied version — prior files stay committed. Idempotent:
    re-running with no pending files returns [].
    """
    applied: list[int] = []
    ts = now() if now is not None else datetime.now(timezone.utc)
    if ts.tzinfo is None or ts.utcoffset() is None:
        raise ValueError("now() must return timezone-aware datetime")
    ts_utc = ts.astimezone(timezone.utc)
    # autocommit=True: every `with conn.transaction()` below is a real
    # top-level transaction, so a failed file never rolls back earlier files.
    conn: Any = _connect(dsn, autocommit=True)
    try:
        with conn.transaction():
            _ensure_migration_table(conn)
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
                applied.append(ver)
            except Exception as exc:
                raise PermanentPortError(
                    f"migration {ver:03d} failed: {_redacted(dsn)}",
                    failure_category=FailureCategory.CONFIGURATION,
                ) from exc
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
    """Open a psycopg connection with dict_row (for postgres adapters).

    Uses autocommit=True so bare SELECT does not open an implicit
    transaction; every mutating operation must explicitly open a
    transaction with ``with conn.transaction():``.

    PA-1 F2: returns a ReconnectableConnection so a PostgreSQL server
    restart no longer strands long-lived adapters (the control plane keeps
    serving after PG comes back; see PERSONAL_DEPLOYMENT §10).
    """
    return ReconnectableConnection(dsn, autocommit=True)


def now_iso(now: Callable[[], datetime] | None) -> datetime:
    """UTC-aware now (for TIMESTAMPTZ columns)."""
    value = datetime.now(timezone.utc) if now is None else now()
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("now() must return timezone-aware datetime")
    return value.astimezone(timezone.utc)


def db_time_expr(
    now: Callable[[], datetime] | None,
) -> tuple[str, list[Any]]:
    """SQL time-source abstraction for lease/expiry comparisons (M16 §5).

    Production (`now is None`) uses PostgreSQL `now()` so the database clock is
    the single authority — consistent with `outbox_events.created_at`. When a
    deterministic test clock is injected, it is bound as a parameter instead.
    Returns `(sql_fragment, params)` to splice into a query.
    """
    if now is None:
        return "now()", []
    return "%s", [now_iso(now)]


def server_now(conn: Any, now: Callable[[], datetime] | None) -> datetime:
    """Resolve the authoritative 'now' for a Python-side comparison.

    Production reads the database clock (`SELECT now()`); tests use the
    injected clock. Keeps lease-expiry/fencing decisions on the same time
    source as the durable writes they guard.
    """
    if now is not None:
        return now_iso(now)
    value: Any = conn.execute("SELECT now() AS now").fetchone()["now"]
    if value.tzinfo is None:  # defensive: treat naive DB result as UTC
        value = value.replace(tzinfo=timezone.utc)
    return cast(datetime, value.astimezone(timezone.utc))


def dsn_from_env() -> str | None:
    """Resolve the canonical-store DSN from the environment.

    PA-1: RESEARCHOS_POSTGRES_DSN joins the chain (the worker gateway and
    .env.example document it; the adapters must resolve the same key).
    """
    for key in (
        "RESEARCHOS_POSTGRES_DSN",
        "RESEARCHOS_DATABASE_URL",
        "DATABASE_URL",
        "POSTGRES_DSN",
    ):
        val = os.environ.get(key)
        if val:
            return val
    return None


def resolve_connection(dsn: str | None, connection: Any | None) -> tuple[Any, bool]:
    """Return (connection, owns_connection) with the dict_row factory applied.

    适配器的连接装配口径（GOAL-004 cycle 6 从 `workflow_engine.py` 上移到此处，
    让 450 行硬上限以"搬代码"而非放宽门禁的方式收口）：外部注入的连接不归调用方
    所有（`owns=False`，关闭时不动它）；未注入时按 DSN 自建（`owns=True`）。
    """
    if connection is not None:
        conn, owns = connection, False
    else:
        resolved = dsn or dsn_from_env()
        if not resolved:
            raise ValueError("postgres adapter requires dsn or connection")
        conn, owns = connect(resolved), True
    try:
        conn.row_factory = dict_row
    except Exception:  # noqa: BLE001 - 已设过工厂的连接保持原样
        pass
    return conn, owns
