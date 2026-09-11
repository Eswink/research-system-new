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
