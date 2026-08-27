"""M13-R1 WP-M1：SQLite 存储契约（run/approval/idempotency/budget）。

证明：四个新存储实现满足对应 Port 语义（含跨 reopen 持久化），
API 重启恢复依赖这些契约。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from adapters.sqlite.approval_store import SqliteApprovalStore
from adapters.sqlite.budget_ledger import SqliteBudgetLedger
from adapters.sqlite.idempotency_store import SqliteIdempotencyStore
from adapters.sqlite.run_store import SqliteRunStore
from packages.application.ports.approval_store import ApprovalSpec
from packages.application.ports.budget_ledger import LedgerSnapshot
from packages.application.ports.errors import InvalidInputError
from packages.domain.budget import (
    BudgetPolicy,
    BudgetReservation,
    LedgerCostStatus,
    ResourceType,
    UsageLedgerEntry,
)
from packages.domain.core import ID, Digest
from packages.domain.run import ResearchRun
from services.api.idempotency import StoredResponse


def _run(state: str = "RUNNING", with_manifest: bool = False) -> ResearchRun:
    return ResearchRun(
        id=ID.generate(),
        project_id="project-1",
        protocol_id="console_demo_research_v1_0_1",
        state=state,
        manifest_digest=Digest.parse("sha256:" + "a" * 64) if with_manifest else None,
        manifest_semantic_digest=Digest.parse("sha256:" + "b" * 64) if with_manifest else None,
    )


def test_run_store_roundtrip_and_reopen(tmp_path: Path) -> None:
    db_path = tmp_path / "runs.db"
    run = _run(state="SUCCEEDED", with_manifest=True)
    store = SqliteRunStore(db_path)
    store.save_run(run)
    assert store.get_run(run.id.value).state == "SUCCEEDED"
    assert store.get_run(run.id.value).manifest_digest == run.manifest_digest
    assert store.list_runs("project-1")[0].id == run.id
    store.close()

    reopened = SqliteRunStore(db_path)
    restored = reopened.get_run(run.id.value)
    assert restored.state == "SUCCEEDED"
    assert restored.manifest_semantic_digest == run.manifest_semantic_digest
    assert restored.created_at == run.created_at
    assert [item.id.value for item in reopened.list_runs()] == [run.id.value]
    try:
        reopened.get_run("missing")
    except KeyError:
        pass
    else:
        reopened.close()
        raise AssertionError("missing run must raise KeyError")
    reopened.close()


def test_approval_store_roundtrip_and_reopen(tmp_path: Path) -> None:
    db_path = tmp_path / "approvals.db"
    store = SqliteApprovalStore(db_path)
    approval = store.register(
        ApprovalSpec(
            run_id="run-1",
            action="high-risk-tool",
            risk="HIGH",
            context="tool requires human approval",
            policy_source="project-policy:require_approval",
            requested_event_id="evt-1",
        )
    )
    assert approval.status == "PENDING"
    assert approval.id in {item.id for item in store.list_pending()}
    decided = approval.with_decision("approve")
    assert decided.status == "APPROVED"
    assert decided.version != approval.version
    store.replace(decided)
    assert store.list_pending() == ()
    restored = store.get(approval.id)
    assert restored is not None
    assert restored.status == "APPROVED"
    store.close()

    reopened = SqliteApprovalStore(db_path)
    restored_reopened = reopened.get(approval.id)
    assert restored_reopened is not None
    assert restored_reopened.status == "APPROVED"
    assert reopened.get("missing") is None
    reopened.close()


def test_idempotency_store_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "idem.db"
    store = SqliteIdempotencyStore(db_path)
    value = StoredResponse(
        request_digest="digest-1", status_code=201, body=b'{"id":"x"}', etag="etag-1"
    )
    store.put("key-1", value)
    restored = store.get("key-1")
    assert restored is not None
    assert restored.request_digest == "digest-1"
    assert restored.body == b'{"id":"x"}'
    assert restored.etag == "etag-1"
    assert store.get("missing") is None
    store.close()

    reopened = SqliteIdempotencyStore(db_path)
    restored_after = reopened.get("key-1")
    assert restored_after is not None
    assert restored_after.etag == "etag-1"
    reopened.close()


def test_budget_ledger_roundtrip_and_reopen(tmp_path: Path) -> None:
    db_path = tmp_path / "budget.db"
    ledger = SqliteBudgetLedger(db_path)
    policy = BudgetPolicy(id="low_cost", hard_limits={"tool_requests": 100})
    reservations = (
        BudgetReservation(
            id="res-1",
            scope="run-1",
            resource_type=ResourceType.TOOL_REQUESTS,
            quantity=3,
            unit="requests",
        ),
    )
    ref = ledger.reserve(reservations, policy)
    assert ledger.snapshot().reservations == reservations
    ledger.release(ref)
    ledger.release(ref)  # 幂等 no-op
    assert ledger.snapshot().reservations == ()
    entry = UsageLedgerEntry(
        entry_id=f"u-{uuid.uuid4().hex}",
        resource_type=ResourceType.MODEL_TOKENS,
        quantity=10,
        unit="tokens",
        cost_status=LedgerCostStatus.UNKNOWN,
        source="model_gateway",
        occurred_at=datetime.now(timezone.utc),
    )
    ledger.record_usage(entry)
    try:
        ledger.record_usage(entry)
    except InvalidInputError:
        pass
    else:
        raise AssertionError("duplicate usage entry must be rejected")
    ledger.close()

    reopened = SqliteBudgetLedger(db_path)
    snapshot: LedgerSnapshot = reopened.snapshot()
    assert len(snapshot.entries) == 1
    assert snapshot.entries[0].entry_id == entry.entry_id
    assert snapshot.entries[0].cost_status is LedgerCostStatus.UNKNOWN
    assert snapshot.entries[0].occurred_at == entry.occurred_at
    reopened.close()
