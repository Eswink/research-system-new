"""Bounded worker-process reconnect loop for transient gateway outages."""

from __future__ import annotations

import time
from collections.abc import Callable

import httpx


def run_with_reconnect(
    run_once: Callable[[], int],
    *,
    should_stop: Callable[[], bool],
    sleep: Callable[[float], None] = time.sleep,
    retry_seconds: float = 2.0,
) -> int:
    """Restart a worker session after transport loss; propagate all other errors."""
    if retry_seconds <= 0:
        raise ValueError("retry_seconds must be > 0")
    while not should_stop():
        try:
            return run_once()
        except httpx.TransportError:
            print("worker: gateway unavailable; retrying", flush=True)  # noqa: T201
            if should_stop():
                return 0
            sleep(retry_seconds)
    return 0


__all__ = ["run_with_reconnect"]
