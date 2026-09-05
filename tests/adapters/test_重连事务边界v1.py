"""A dead transaction must not replay its last statement on a new connection."""

from __future__ import annotations

from typing import Any

import psycopg
import pytest

from adapters.postgres.db import ReconnectableConnection, dsn_from_env
from tests.postgres.test_reconnect import _wrapper_with_fakes


def test_closed_connection_inside_explicit_transaction_is_not_replayed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wrapper, created = _wrapper_with_fakes(
        monkeypatch, fail_first=False, status=psycopg.pq.TransactionStatus.IDLE
    )

    def disconnected(*_: Any, **__: Any) -> Any:
        created[0].closed = True
        raise psycopg.OperationalError("the connection is closed")

    monkeypatch.setattr(wrapper._inner, "execute", disconnected)
    with pytest.raises(psycopg.OperationalError):
        with wrapper.transaction():
            wrapper.execute("SELECT 1")
    assert len(created) == 1


def test_wrapper_tracks_nested_transaction_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    wrapper, _ = _wrapper_with_fakes(
        monkeypatch, fail_first=False, status=psycopg.pq.TransactionStatus.IDLE
    )
    assert isinstance(wrapper, ReconnectableConnection)
    with wrapper.transaction():
        with wrapper.transaction():
            assert wrapper._idle() is False
        assert wrapper._idle() is False
    assert wrapper._idle() is True


def test_explicit_gateway_dsn_wins_over_ambient_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://ambient/unrelated")
    monkeypatch.setenv("RESEARCHOS_DATABASE_URL", "postgresql://configured/api")
    monkeypatch.setenv("RESEARCHOS_POSTGRES_DSN", "postgresql://configured/gateway")
    assert dsn_from_env() == "postgresql://configured/gateway"
