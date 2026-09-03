"""PA-1 F2: ReconnectableConnection — stale connections after a PG restart
must self-heal for idle operations, and must NEVER retry inside an open
transaction (data safety).

Unit tests use a scripted fake inner connection; the integration test kills
the wrapper's own backend via pg_terminate_backend (the same server-side
breakage a restart produces) and asserts the SAME wrapper instance recovers.
"""

from __future__ import annotations

import os
from typing import Any

import psycopg
import pytest

from adapters.postgres.db import ReconnectableConnection, connect, dsn_from_env

pytestmark = pytest.mark.postgres


def _dsn() -> str:
    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        os.environ.get(
            "DATABASE_URL",
            "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
        ),
    )


class _FakeInfo:
    def __init__(self, status: Any) -> None:
        self.transaction_status = status


class _FakeInner:
    """Scripted psycopg-connection stand-in.

    `fail_first` makes the FIRST execute OR the FIRST transaction() call
    raise OperationalError once (then the instance behaves normally).
    """

    def __init__(self, *, fail_first: bool, status: Any) -> None:
        self.info = _FakeInfo(status)
        self.closed = False
        self.row_factory: Any = None
        self._fail_first = fail_first
        self._armed = fail_first
        self.calls = 0

    def _disarm(self) -> bool:
        was_armed = self._armed
        self._armed = False
        return was_armed

    def _run(self, statement: Any, values: Any = None, **kwargs: Any) -> Any:
        self.calls += 1
        if self._disarm():
            raise psycopg.OperationalError("the connection is closed")
        return [("ok",)]

    execute = _run

    def transaction(self) -> Any:
        if self._disarm():
            raise psycopg.OperationalError("the connection is closed")

        class _T:
            def __enter__(_self) -> Any:  # noqa: N805
                return None

            def __exit__(_self, *exc: Any) -> Any:  # noqa: N805
                return False

        return _T()

    def close(self) -> None:
        self.closed = True


def _wrapper_with_fakes(
    monkeypatch: Any, *, fail_first: bool, status: Any
) -> tuple[ReconnectableConnection, list[_FakeInner]]:
    created: list[_FakeInner] = []

    def fake_connect(dsn: str, *, autocommit: bool = False) -> _FakeInner:
        inner = _FakeInner(fail_first=fail_first if not created else False, status=status)
        created.append(inner)
        return inner

    monkeypatch.setattr("adapters.postgres.db._connect", fake_connect)
    return ReconnectableConnection("postgresql://fake/db"), created


def test_idle_broken_connection_reconnects_and_retries(monkeypatch: Any) -> None:
    wrapper, created = _wrapper_with_fakes(
        monkeypatch, fail_first=True, status=psycopg.pq.TransactionStatus.IDLE
    )
    result = wrapper.execute("SELECT 1")
    assert result == [("ok",)]
    assert len(created) == 2  # original + one reconnect
    assert created[0].closed is True


def test_admin_shutdown_recovers(monkeypatch: Any) -> None:
    """pg_terminate_backend / server restart raise errors.AdminShutdown —
    NOT an OperationalError subclass — and must still self-heal."""
    wrapper, created = _wrapper_with_fakes(
        monkeypatch, fail_first=False, status=psycopg.pq.TransactionStatus.IDLE
    )

    def shutdown(*args: Any, **kwargs: Any) -> Any:
        raise psycopg.errors.AdminShutdown("terminating connection due to administrator command")

    monkeypatch.setattr(wrapper._inner, "execute", shutdown)
    # first call raises AdminShutdown on the ORIGINAL inner; after reconnect
    # the fresh fake behaves normally
    result = wrapper.execute("SELECT 1")
    assert result == [("ok",)]
    assert len(created) == 2


def test_in_transaction_failure_is_never_retried(monkeypatch: Any) -> None:
    wrapper, created = _wrapper_with_fakes(
        monkeypatch, fail_first=True, status=psycopg.pq.TransactionStatus.INTRANS
    )
    with pytest.raises(psycopg.OperationalError):
        wrapper.execute("SELECT 1")
    assert len(created) == 1  # no reconnect attempted


def test_non_operational_error_propagates(monkeypatch: Any) -> None:
    wrapper, _created = _wrapper_with_fakes(
        monkeypatch, fail_first=False, status=psycopg.pq.TransactionStatus.IDLE
    )

    def boom(*args: Any, **kwargs: Any) -> Any:
        raise psycopg.ProgrammingError("bad syntax")

    monkeypatch.setattr(wrapper._inner, "execute", boom)
    with pytest.raises(psycopg.ProgrammingError):
        wrapper.execute("SELECT 1")


def test_transaction_entry_survives_stale_connection(monkeypatch: Any) -> None:
    wrapper, created = _wrapper_with_fakes(
        monkeypatch, fail_first=True, status=psycopg.pq.TransactionStatus.IDLE
    )
    # first inner.execute raises once; transaction() entry must reconnect too
    with wrapper.transaction() as tx:
        assert tx is None
    assert len(created) == 2


def test_row_factory_setter_applies_to_inner(monkeypatch: Any) -> None:
    wrapper, created = _wrapper_with_fakes(
        monkeypatch, fail_first=False, status=psycopg.pq.TransactionStatus.IDLE
    )
    wrapper.row_factory = "sentinel"
    assert created[0].row_factory == "sentinel"


def test_real_stale_backend_recovers() -> None:
    """Integration: kill the wrapper's own server backend (the exact stale
    state a PG restart leaves behind) and assert the SAME instance recovers."""
    dsn = _dsn()
    conn = connect(dsn)
    try:
        pid = conn.execute("SELECT pg_backend_pid() AS pid").fetchone()["pid"]
        admin = psycopg.connect(dsn, autocommit=True)
        try:
            admin.execute("SELECT pg_terminate_backend(%s)", (pid,))
        finally:
            admin.close()
        row = conn.execute("SELECT 1 AS one").fetchone()
        assert int(row["one"]) == 1
        conn.execute("SELECT 1 AS one").fetchone()
    finally:
        conn.close()


def test_dsn_from_env_reads_gateway_key(monkeypatch: Any) -> None:
    for key in ("DATABASE_URL", "RESEARCHOS_DATABASE_URL", "POSTGRES_DSN"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("RESEARCHOS_POSTGRES_DSN", "postgresql://x/y")
    assert dsn_from_env() == "postgresql://x/y"
