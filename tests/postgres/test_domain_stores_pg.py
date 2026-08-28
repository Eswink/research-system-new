"""M14 PG domain store contract tests (runs/approvals/budget/evidence).

Runs against live PG (postgres marker). Mirrors tests/contracts/test_m13_r1_store_contracts.py
semantics for the PG implementations.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from adapters.postgres.approval_store import PostgresApprovalStore
from adapters.postgres.budget_ledger import PostgresBudgetLedger
from adapters.postgres.db import migrate
from adapters.postgres.evidence_ledger import PostgresEvidenceLedger
from adapters.postgres.run_store import PostgresRunStore
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
from packages.domain.enums import TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.run import ResearchRun

pytestmark = pytest.mark.postgres


def _dsn() -> str:
    import os

    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
    )


def _clean() -> None:
    import psycopg

    migrate(_dsn())
    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute(
        "TRUNCATE runs, approvals, budget_reservations, budget_usage_entries,"
        " m12_sources, m12_evidence, m12_claims, m12_relations,"
        " tasks, leases, idempotency_records, outbox_events CASCADE"
    )
    conn.commit()
    conn.close()


def _run(state: str = "RUNNING", with_manifest: bool = False) -> ResearchRun:
    return ResearchRun(
        id=ID.generate(),
        project_id="project-1",
        protocol_id="console_demo_research_v1_0_1",
        state=state,
        manifest_digest=Digest.parse("sha256:" + "a" * 64) if with_manifest else None,
        manifest_semantic_digest=Digest.parse("sha256:" + "b" * 64) if with_manifest else None,
    )


def test_run_store_roundtrip() -> None:
    _clean()
    rs = PostgresRunStore(dsn=_dsn())
    run = _run(state="SUCCEEDED", with_manifest=True)
    rs.save_run(run)
    assert rs.get_run(run.id.value).state == "SUCCEEDED"
    assert rs.get_run(run.id.value).manifest_digest == run.manifest_digest
    assert rs.list_runs("project-1")[0].id == run.id
    try:
        rs.get_run("missing")
    except KeyError:
        pass
    else:
        raise AssertionError("missing run must raise KeyError")
    rs.close()


def test_approval_store_roundtrip() -> None:
    _clean()
    store = PostgresApprovalStore(dsn=_dsn())
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
    store.replace(decided)
    assert store.list_pending() == ()
    restored = store.get(approval.id)
    assert restored is not None and restored.status == "APPROVED"
    assert store.get("missing") is None
    store.close()


def test_budget_ledger_roundtrip() -> None:
    _clean()
    ledger = PostgresBudgetLedger(dsn=_dsn())
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
    ledger.release(ref)  # idempotent
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
    snapshot: LedgerSnapshot = ledger.snapshot()
    assert len(snapshot.entries) == 1
    assert snapshot.entries[0].entry_id == entry.entry_id
    ledger.close()


def test_evidence_ledger_roundtrip() -> None:
    _clean()
    ledger = PostgresEvidenceLedger(dsn=_dsn())
    source = SourceRecord(
        origin="origin-1", content_digest="digest-1", trust_label=TrustLabel.VERIFIED_SOURCE
    )
    ledger.register_source(source)
    assert ledger.has_source("origin-1")
    evidence = Evidence(id="ev-1", source_ref="origin-1", content_digest="content-1")
    ledger.register_evidence(evidence)
    assert ledger.get_evidence("ev-1").content_digest == "content-1"
    claim = Claim(id="cl-1", statement="s", status=ClaimStatus.PROPOSED)
    ledger.register_claim(claim)
    ledger.attach_relation(
        EvidenceRelation(
            claim_id="cl-1", evidence_id="ev-1", relation=EvidenceRelationType.SUPPORTS
        )
    )
    rels = ledger.relations_for_claim("cl-1")
    assert len(rels) == 1
    verified = Claim(
        id="cl-2",
        statement="s2",
        status=ClaimStatus.VERIFIED,
        evidence_relations=[("ev-1", EvidenceRelationType.SUPPORTS)],
    )
    ledger.register_claim(verified)
    assert ledger.get_claim("cl-2").status is ClaimStatus.VERIFIED
    assert {c.id for c in ledger.claims()} == {"cl-1", "cl-2"}
    ledger.close()
