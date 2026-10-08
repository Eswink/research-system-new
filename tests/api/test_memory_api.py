"""Memory 控制面测试（PLAN-20260910-037 WP-F）。

503（SQLite 无 store）、§8 门链全阶段可分类 422、PG canonical 语义经
FakeMemoryStore 注入验证、DELETE lifecycle + 幂等键要求。
"""

from __future__ import annotations

from typing import Any, cast

from fastapi.testclient import TestClient

from adapters.fakes.memory_store import FakeMemoryStore
from packages.application.ports.errors import InvalidInputError
from packages.domain.enums import TrustLabel
from packages.domain.evidence import SourceRecord


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _wire(client: TestClient) -> FakeMemoryStore:
    store = FakeMemoryStore()
    deps = _deps(client)
    deps.memory = store
    deps.ledger.register_source(
        SourceRecord(
            origin="paper://memory-wpf",
            content_digest="sha256:" + "a" * 64,
            trust_label=TrustLabel.VERIFIED_SOURCE,
        )
    )
    return store


def _proposal(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "tier": "SESSION",
        "kind": "FACT",
        "content": "observed sorting baseline is O(n log n)",
        "provenance": "paper://memory-wpf",
        "confidence": 0.8,
    }
    base.update(overrides)
    return base


def _post(client: TestClient, key: str, body: dict[str, object]) -> Any:
    return client.post("/memory/proposals", json=body, headers={"Idempotency-Key": f"mem-{key}"})


def test_sqlite_dev_path_memory_store_missing_is_503(client: TestClient) -> None:
    assert _deps(client).memory is None
    assert client.get("/projects/example-project/memory").status_code == 503
    assert _post(client, "no-store", _proposal()).status_code == 503


def test_proposal_commits_through_full_gate(client: TestClient) -> None:
    _wire(client)
    created = _post(client, "ok", _proposal())
    assert created.status_code == 201, created.text
    record = created.json()["record"]
    assert record["tier"] == "SESSION"
    assert record["active"] is True
    listed = client.get("/projects/example-project/memory")
    assert listed.status_code == 200
    assert [row["id"] for row in listed.json()["records"]] == [record["id"]]


def test_unregistered_provenance_rejected_422(client: TestClient) -> None:
    _wire(client)
    rejected = _post(client, "badprov", _proposal(provenance="paper://not-registered"))
    assert rejected.status_code == 422
    assert "provenance" in rejected.text


def test_blank_content_rejected_by_schema_stage(client: TestClient) -> None:
    _wire(client)
    rejected = _post(client, "blank", _proposal(content="   "))
    assert rejected.status_code == 422
    assert "schema" in rejected.json()["title"] or "blank" in rejected.text


def test_project_tier_requires_curator(client: TestClient) -> None:
    _wire(client)
    denied = _post(client, "curator-0", _proposal(tier="PROJECT", content="team decision"))
    assert denied.status_code == 422
    granted = _post(
        client,
        "curator-1",
        _proposal(tier="PROJECT", content="team decision", curator_approved=True),
    )
    assert granted.status_code == 201, granted.text


def test_delete_lifecycle_and_idempotency_key(client: TestClient) -> None:
    store = _wire(client)
    record_id = _post(client, "del", _proposal()).json()["record"]["id"]
    no_key = client.delete(f"/memory/{record_id}")
    assert no_key.status_code == 422  # Idempotency-Key required
    missing = client.delete("/memory/ghost", headers={"Idempotency-Key": "k-ghost"})
    assert missing.status_code == 404
    removed = client.delete(f"/memory/{record_id}", headers={"Idempotency-Key": "k-1"})
    assert removed.status_code == 204
    try:
        store.get(record_id)
    except InvalidInputError:
        pass
    else:
        raise AssertionError("deleted memory id must be unknown to the store")
    listed = client.get("/projects/example-project/memory")
    assert listed.json()["records"] == []


# --- GOAL-20261008-039 EC-02 / EC-04：读面披露 + 按时点判定 -------------------------


def test_the_list_face_discloses_the_scope(client: TestClient) -> None:
    """EC-02：列表读面逐条披露 `scope`（此前该字段根本不落库）。"""
    _wire(client)
    created = client.post(
        "/memory/proposals",
        json=_proposal(provenance="paper://memory-wpf"),
        headers={"Idempotency-Key": "mem-scope-1"},
    )
    assert created.status_code == 201, created.text
    rows = client.get("/projects/example-project/memory").json()["records"]
    assert rows and rows[0]["scope"] == "project", rows


def _commit_expiring(store: Any, memory_id: str) -> None:
    """直写一条带明确到期时刻的记录（钉的是**判定面**本身，不经提案面）。"""
    from datetime import datetime, timezone

    from packages.domain.core import Timestamp
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryWriteProposal

    store.allow_source("paper://memory-wpf")
    store.commit(
        MemoryWriteProposal(
            id=memory_id,
            tier=MemoryTier.SESSION,
            kind=MemoryType.FACT,
            content="c",
            provenance="paper://memory-wpf",
            confidence=0.5,
            expires_at=Timestamp(datetime(2027, 1, 1, tzinfo=timezone.utc)),
        )
    )


def test_the_validity_face_judges_at_the_time_the_caller_gives(client: TestClient) -> None:
    """EC-04：`?at=` 显式时点 ⇒ 逐条三态判定；**不给时点的列表读面不猜**（`validity` 为 None）。"""
    store = _wire(client)
    with_expiry = _proposal(provenance="paper://memory-wpf")
    created = client.post(
        "/memory/proposals",
        json=with_expiry,
        headers={"Idempotency-Key": "mem-validity-1"},
    )
    assert created.status_code == 201, created.text
    memory_id = str(created.json()["record"]["id"])
    _commit_expiring(store, "memory-validity-explicit")
    before = client.get(
        "/projects/example-project/memory/validity", params={"at": "2026-06-01T00:00:00+00:00"}
    )
    assert before.status_code == 200, before.text
    payload = before.json()
    assert payload["at"].startswith("2026-06-01")
    assert {row["id"] for row in payload["records"]} >= {memory_id, "memory-validity-explicit"}
    by_id = {row["id"]: row for row in payload["records"]}
    assert by_id["memory-validity-explicit"]["validity"] is None, "未到期 ⇒ 不报"
    after = client.get(
        "/projects/example-project/memory/validity", params={"at": "2028-01-01T00:00:00+00:00"}
    ).json()
    by_id_after = {row["id"]: row for row in after["records"]}
    assert by_id_after["memory-validity-explicit"]["validity"] == "EXPIRED", "到期 ⇒ 必报"
    # **未声明时效的记录不被误报**（缺席不猜）。
    assert by_id_after[memory_id]["validity"] is None, (
        "未声明时效不得被误报（反证③）",
        by_id_after[memory_id],
    )
    # 不给时点的**列表**读面：`validity` 不填（未判定，不猜）。
    listed = client.get("/projects/example-project/memory").json()["records"]
    assert all(row["validity"] is None for row in listed)


def test_the_validity_face_refuses_a_bad_timestamp(client: TestClient) -> None:
    """边界：非法时点 ⇒ 422（点名，不静默按当前时间兜底）。"""
    _wire(client)
    bad = client.get("/projects/example-project/memory/validity", params={"at": "not-a-time"})
    assert bad.status_code == 422, bad.text
