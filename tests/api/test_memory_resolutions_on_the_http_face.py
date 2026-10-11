"""GOAL-20261012-058 EC-03：**消解事实两处同值** —— HTTP 面与编排面（同源 ⇒ 同值）。"""

from datetime import datetime, timezone
from typing import cast

from fastapi.testclient import TestClient

from packages.application.memory.lifecycle import (
    MemoryLifecycleDeps,
    resolve_memory_conflict,
)
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal
from tests.api.test_memory_api import _deps, _wire

_NOW = Timestamp(datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc))


def test_the_resolution_facts_agree_between_the_two_faces(client: TestClient) -> None:
    """GOAL-20261012-058 EC-03：**消解事实两处同值**（同源 ⇒ 同值）。"""
    from adapters.canonical.memory_read import memory_read

    store = _wire(client)

    live = _deps(client).memory
    live.allow_source("source:article-1")
    live.commit(
        MemoryWriteProposal(
            id="m-peer",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="内容 m-peer",
            provenance="source:article-1",
            confidence=0.9,
        )
    )
    live.commit(
        MemoryWriteProposal(
            id="m-res",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="内容 m-res",
            provenance="source:article-1",
            confidence=0.9,
            contradictions=["m-peer"],
        )
    )
    resolve_memory_conflict(
        MemoryLifecycleDeps(store=live),
        "m-res",
        "m-peer",
        resolved_by="curator:a",
        resolved_at=Timestamp(datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)),
    )
    http_rows = cast(
        "list[dict[str, object]]",
        client.get("/projects/example-project/memory").json()["records"],
    )
    http = {str(row["id"]): row for row in http_rows}
    orch_rows = cast("list[dict[str, object]]", memory_read(store, {"now": "2026-05-01T12:00:00+00:00"})["memories"])
    orch = {str(row["memory_id"]): row for row in orch_rows}
    assert http["m-res"]["conflict_resolutions"] == orch["m-res"]["conflict_resolutions"], (
        http["m-res"]["conflict_resolutions"],
        orch["m-res"]["conflict_resolutions"],
    )
    resolutions = cast("list[dict[str, object]]", http["m-res"]["conflict_resolutions"])
    assert resolutions[0]["resolved_by"] == "curator:a"
