"""M15 observability tests 共享 fixture:OTLP receiver 生命周期。"""

from __future__ import annotations

import os
import socket
from collections.abc import Iterator
from urllib.parse import urlsplit

import pytest

from tests.observability.fault_collector import FaultyCollector
from tests.observability.otlp_receiver import OtlpHttpReceiver

_DEFAULT_COLLECTOR = "http://localhost:4318"


@pytest.fixture()
def collector() -> Iterator[FaultyCollector]:
    fc = FaultyCollector()
    fc.start()
    try:
        yield fc
    finally:
        fc.stop()


@pytest.fixture()
def receiver() -> Iterator[OtlpHttpReceiver]:
    r = OtlpHttpReceiver()
    r.start()
    try:
        yield r
    finally:
        r.stop()


def collector_endpoint() -> str:
    return os.environ.get("RESEARCHOS_OTEL_COLLECTOR_ENDPOINT", _DEFAULT_COLLECTOR)


def collector_required() -> bool:
    """Whether a selected live-evidence job must fail rather than skip."""
    return os.environ.get("RESEARCHOS_REQUIRE_COLLECTOR") == "1"


def collector_available() -> bool:
    """pinned collector 证据套件的可达性探测(仅 loopback/本机端口)。"""
    parsed = urlsplit(collector_endpoint())
    host = parsed.hostname or "localhost"
    port = parsed.port or 4318
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False
