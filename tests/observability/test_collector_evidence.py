"""Pinned OTel Collector 证据套件(requires_collector)。

前置:`docker compose -f docker-compose.m15.yml up -d --build` 启动
`otel/opentelemetry-collector-contrib@sha256:faf125d...`(0.139.0)。
断言:Research OS sink 导出的 span 经真实 collector file exporter 落盘,
span 名可在导出文件中检索到。collector 不可达时整组跳过(离线 m0 不受影响)。
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path

import pytest

from adapters.otel.config import OtelConfig
from adapters.otel.provider import build_telemetry_sink
from packages.application.observability.scope import operation
from packages.application.observability.signals import CorrelationRef, OperationScope
from tests.observability.conftest import (
    collector_available,
    collector_endpoint,
    collector_required,
)

pytestmark = pytest.mark.requires_collector

_REPO_ROOT = Path(__file__).resolve().parents[2]
_COLLECTOR_FILE = _REPO_ROOT / "data" / "otel" / "research_os_signals.json"


@pytest.fixture(scope="module", autouse=True)
def _require_collector() -> None:
    if collector_available():
        return
    message = "OTel collector not reachable (docker compose -f docker-compose.m15.yml up)"
    if collector_required():
        pytest.fail(message)
    pytest.skip(message)


def test_collector_persists_research_os_spans() -> None:
    """唯一 marker span 导出后,轮询 file exporter 落盘内容(避免
    Windows bind mount 删除-重建竞态:不删文件,以 marker 增量断言)。"""
    marker = f"collector-evidence-{uuid.uuid4().hex}"
    before = ""
    if _COLLECTOR_FILE.exists():
        before = _COLLECTOR_FILE.read_text(encoding="utf-8", errors="ignore")
    config = OtelConfig(
        enabled=True,
        endpoint=collector_endpoint(),
        timeout_seconds=2.0,
        export_interval_millis=200,
        queue_size=64,
    )
    failsafe = build_telemetry_sink(config)
    with operation(
        failsafe,
        scope=OperationScope.RUN,
        name=marker,
        correlation=CorrelationRef(run_id="run-collector-evidence"),
    ):
        pass
    failsafe.flush(timeout_seconds=5.0)
    failsafe.shutdown()

    deadline = time.monotonic() + 45.0
    text = before
    while time.monotonic() < deadline:
        if _COLLECTOR_FILE.exists():
            text = _COLLECTOR_FILE.read_text(encoding="utf-8", errors="ignore")
            if marker in text and marker not in before:
                break
        time.sleep(1.0)
    assert marker in text and marker not in before, (
        "collector file exporter must persist the unique marker span"
    )
