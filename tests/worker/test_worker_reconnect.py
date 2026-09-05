"""Worker process reconnect orchestration tests."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from services.worker.__main__ import _build_config
from services.worker.reconnect import run_with_reconnect

_ROOT = Path(__file__).resolve().parents[2]


def test_worker_process_retries_gateway_transport_outage() -> None:
    attempts = {"count": 0}
    sleeps: list[float] = []

    def run_once() -> int:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise httpx.ConnectError("gateway unavailable")
        return 4

    completed = run_with_reconnect(
        run_once,
        should_stop=lambda: False,
        sleep=sleeps.append,
        retry_seconds=2.0,
    )

    assert completed == 4
    assert attempts["count"] == 3
    assert sleeps == [2.0, 2.0]


def test_worker_process_does_not_retry_programming_error() -> None:
    def run_once() -> int:
        raise ValueError("bad worker configuration")

    with pytest.raises(ValueError, match="bad worker configuration"):
        run_with_reconnect(
            run_once,
            should_stop=lambda: False,
            sleep=lambda _seconds: None,
        )


def test_worker_runtime_version_defaults_to_project_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RESEARCHOS_WORKER_GATEWAY_URL", "http://127.0.0.1:8081")
    monkeypatch.setenv("RESEARCHOS_WORKER_ENROLLMENT_SECRET", "test-secret")
    monkeypatch.delenv("RESEARCHOS_WORKER_RUNTIME_VERSION", raising=False)

    config = _build_config("worker-version-test")

    expected = _ROOT.joinpath("VERSION").read_text(encoding="utf-8").strip()
    assert config.runtime_version == expected
