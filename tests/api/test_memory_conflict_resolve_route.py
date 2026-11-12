"""GOAL-20261111-110 EC-02/EC-03（路由层）：**消解路由的幂等 / 缺省 / 落账**。

**判什么**（每条独立取证）：

1. **幂等键**：mutating POST 必带 `Idempotency-Key`（中间件 422 点名）；同 key + 同载荷
   ⇒ **同响应重放**；同 key + 不同载荷 ⇒ 422 点名复用；
2. **缺省 = `REQUIRE_HUMAN`**：空体 ⇒ 200 判词 + **不落账**（`resolution_recorded=False`）；
3. **正例**：声明 `NEWER_WINS`（带阈值）⇒ 落账，`resolved_by="arbitration:NEWER_WINS"`
   逐字入账，胜者与域层判词一致；
4. **反证（EC-03）**：同一对**重复消解** ⇒ 422 点名（域层的门经路由仍然咬得住）；
   未知 id ⇒ 404 点名；声明自动策略而不给阈值 ⇒ 422 点名；双方都没声明冲突 ⇒ 422 点名；
5. **人来裁决**：`strategy="REQUIRE_HUMAN"` + `resolved_by` ⇒ 落账且 `resolved_by`
   逐字入账（闭环的最后一米：仲裁说「要人来」，人来了有路可走）。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, cast

from fastapi.testclient import TestClient

from tests.api.test_memory_api import _deps, _wire


def _conflict_pair(client: TestClient) -> tuple[str, str]:
    """经门链提交两条互相指认的记忆（PROVENANCE 已由 `_wire` 注册）。"""
    deps = _deps(client)
    store = deps.memory
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryRecord

    store._records["mem-a"] = MemoryRecord(  # noqa: SLF001 - 判据摆件
        id="mem-a",
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content="baseline is O(n log n)",
        provenance="paper://memory-wpf",
        confidence=0.9,
        valid_from=_stamp(1),
        contradictions=["mem-b"],
    )
    store._records["mem-b"] = MemoryRecord(  # noqa: SLF001
        id="mem-b",
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content="baseline is O(n squared)",
        provenance="paper://memory-wpf",
        confidence=0.9,
        valid_from=_stamp(10),
    )
    return "mem-a", "mem-b"


def _stamp(day: int) -> Any:
    from packages.domain.core import Timestamp

    return Timestamp(value=datetime(2026, 11, day, tzinfo=timezone.utc))


def _resolve(
    client: TestClient,
    memory_id: str,
    other_id: str,
    body: dict[str, object] | None = None,
    *,
    key: str = "resolve-1",
) -> Any:
    return client.post(
        f"/memory/{memory_id}/conflicts/{other_id}/resolve",
        json=body,
        headers={"Idempotency-Key": f"goal110-{key}"},
    )


def test_resolve_requires_an_idempotency_key(client: TestClient) -> None:
    """mutating POST 无幂等键 ⇒ 422 点名（控制面既有姿态，路由不另开口子）。"""
    _wire(client)
    _conflict_pair(client)
    response = client.post("/memory/mem-a/conflicts/mem-b/resolve", json={})
    assert response.status_code == 422, response.text
    assert "Idempotency-Key" in response.text


def test_same_key_same_payload_replays_the_same_response(client: TestClient) -> None:
    """幂等正例：同 key + 同载荷 ⇒ 同一响应（middleware replay）。"""
    _wire(client)
    _conflict_pair(client)
    body: dict[str, object] = {"strategy": "NEWER_WINS", "min_confidence": 0.6}
    first = _resolve(client, "mem-a", "mem-b", body, key="replay")
    assert first.status_code == 200, first.text
    second = _resolve(client, "mem-a", "mem-b", body, key="replay")
    assert second.status_code == first.status_code
    assert second.json() == first.json()


def test_same_key_different_payload_is_refused(client: TestClient) -> None:
    _wire(client)
    _conflict_pair(client)
    first = _resolve(
        client, "mem-a", "mem-b", {"strategy": "NEWER_WINS", "min_confidence": 0.6}, key="reuse"
    )
    second = _resolve(
        client, "mem-a", "mem-b", {"strategy": "NEWER_WINS", "min_confidence": 0.7}, key="reuse"
    )
    assert first.status_code in {200, 422}
    assert second.status_code == 422, second.text
    assert "Reused" in second.json()["title"]


def test_the_default_verdict_is_require_human_and_records_nothing(client: TestClient) -> None:
    """**缺省**：空体 ⇒ 200 判词 `REQUIRE_HUMAN` + **不落账**（自动化必须显式声明）。"""
    _wire(client)
    memory_id, other_id = _conflict_pair(client)
    response = _resolve(client, memory_id, other_id, {}, key="default")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["verdict"]["outcome"] == "REQUIRE_HUMAN"
    assert payload["verdict"]["winner_id"] is None
    assert payload["resolution_recorded"] is False
    assert payload["record"] is None
    # 落账面确实没动：记录的 resolutions 仍为空。
    store = _deps(client).memory
    assert store._records[memory_id].resolutions == []  # noqa: SLF001


def test_declared_newer_wins_records_the_arbitration_attribution(client: TestClient) -> None:
    """正例：声明 `NEWER_WINS`（带阈值）⇒ 落账且 `resolved_by` 逐字可读。"""
    _wire(client)
    memory_id, other_id = _conflict_pair(client)
    response = _resolve(
        client, memory_id, other_id, {"strategy": "NEWER_WINS", "min_confidence": 0.6}, key="newer"
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["resolution_recorded"] is True
    assert payload["verdict"]["outcome"] == "NEWER_WINS"
    assert payload["verdict"]["winner_id"] == other_id
    assert payload["record"] is not None
    resolutions = payload["record"]["conflict_resolutions"]
    assert [row["resolved_by"] for row in resolutions] == ["arbitration:NEWER_WINS"]
    assert [row["other_id"] for row in resolutions] == [other_id]


def test_an_auto_strategy_without_a_threshold_is_refused(client: TestClient) -> None:
    """**反证**：声明自动策略而不给阈值 ⇒ 422 点名（无凭据的口子开不出来）。"""
    _wire(client)
    memory_id, other_id = _conflict_pair(client)
    response = _resolve(client, memory_id, other_id, {"strategy": "NEWER_WINS"}, key="no-thresh")
    assert response.status_code == 422, response.text
    assert "min_confidence" in response.text


def test_unknown_ids_are_404_by_name(client: TestClient) -> None:
    _wire(client)
    _conflict_pair(client)
    missing = _resolve(client, "mem-nope", "mem-b", {}, key="404a")
    assert missing.status_code == 404
    assert "mem-nope" in missing.text


def test_a_second_resolution_is_refused_by_name(client: TestClient) -> None:
    """**反证（EC-03）**：同一对重复消解 ⇒ 422 点名（域层的门经路由仍然咬得住）。"""
    _wire(client)
    memory_id, other_id = _conflict_pair(client)
    body: dict[str, object] = {"strategy": "NEWER_WINS", "min_confidence": 0.6}
    first = _resolve(client, memory_id, other_id, body, key="first")
    assert first.status_code == 200 and first.json()["resolution_recorded"] is True
    second = _resolve(client, memory_id, other_id, body, key="second")
    assert second.status_code == 422, second.text
    assert "already resolved" in second.text


def test_a_human_resolution_is_recorded_verbatim(client: TestClient) -> None:
    """**人来裁决**：`REQUIRE_HUMAN` + `resolved_by` ⇒ 落账且 `resolved_by` 逐字入账。"""
    _wire(client)
    memory_id, other_id = _conflict_pair(client)
    response = _resolve(
        client,
        memory_id,
        other_id,
        {"strategy": "REQUIRE_HUMAN", "resolved_by": "human:alice"},
        key="human",
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["resolution_recorded"] is True
    assert [row["resolved_by"] for row in payload["record"]["conflict_resolutions"]] == [
        "human:alice"
    ]


def test_a_pair_nobody_declared_is_refused(client: TestClient) -> None:
    """**反证**：两条记录互不指认 ⇒ 422 点名（不是声明的冲突对就没有消解可落）。"""
    _wire(client)
    _conflict_pair(client)
    body: dict[str, object] = {"strategy": "NEWER_WINS", "min_confidence": 0.6}
    # mem-b↔mem-a 是**声明的对**（方向判定走 mem-a）；真正「双方都没声明」的
    # 形状要另摆两条干净记录。
    store = cast(Any, _deps(client).memory)
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryRecord

    store._records["mem-c"] = MemoryRecord(  # noqa: SLF001
        id="mem-c",
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content="c",
        provenance="paper://memory-wpf",
        confidence=0.9,
    )
    store._records["mem-d"] = MemoryRecord(  # noqa: SLF001
        id="mem-d",
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content="d",
        provenance="paper://memory-wpf",
        confidence=0.9,
    )
    refused = _resolve(client, "mem-c", "mem-d", body, key="undeclared-2")
    assert refused.status_code == 422, refused.text
    assert "declares the other" in refused.text or "Not A Declared Conflict" in refused.text
