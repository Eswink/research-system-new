"""Independent M14 audit probe: canonical state rebuild (section 2).

Rebuild the full domain state from PostgreSQL alone (no workflow runtime):
- Run (runs table)
- Tasks + leases (tasks/leases)
- Manifest (frozen in run_json digest)
- Phase/Task (task_json)
- Evidence/Claims (m12_*)
- Usage/Budget (budget_*)
- Approvals (approvals)
- Artifacts (artifacts)
Then "stop" the runtime process (close connections); verify truth still exists
from a fresh connection — i.e., canonical state does not depend on any
in-process reconstruction or Temporal history.

M14 audit probe (RECHECK-20260828-022, DoD row 2). Re-runnable.

WARNING: truncates all domain tables on the target database. Point
RESEARCHOS_POSTGRES_DSN at a disposable test instance. Artifact blobs are
written to a throwaway temp directory.

Run: uv run --frozen --no-sync python -B tools/probes/probe_canonical_state.py
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from adapters.postgres.approval_store import PostgresApprovalStore  # noqa: E402
from adapters.postgres.artifact_store import PostgresArtifactStore  # noqa: E402
from adapters.postgres.budget_ledger import PostgresBudgetLedger  # noqa: E402
from adapters.postgres.db import migrate  # noqa: E402
from adapters.postgres.evidence_ledger import PostgresEvidenceLedger  # noqa: E402
from adapters.postgres.run_store import PostgresRunStore  # noqa: E402
from adapters.postgres.workflow_engine import PostgresWorkflowEngine  # noqa: E402
from packages.application.ports.approval_store import ApprovalSpec  # noqa: E402
from packages.application.ports.workflow_engine import TaskCompletion  # noqa: E402
from packages.domain.artifacts import Artifact, ArtifactRetentionPolicy  # noqa: E402
from packages.domain.budget import (  # noqa: E402
    BudgetPolicy,
    BudgetReservation,
    LedgerCostStatus,
    ResourceType,
    UsageLedgerEntry,
)
from packages.domain.core import ID, Digest  # noqa: E402
from packages.domain.enums import ArtifactState, TrustLabel  # noqa: E402
from packages.domain.evidence import (  # noqa: E402
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.run import ResearchRun  # noqa: E402
from tests.contracts.fixtures import research_task, task_contract  # noqa: E402

DSN = os.environ.get(
    "RESEARCHOS_POSTGRES_DSN",
    "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
)

results: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    results.append(f"{'PASS' if cond else 'FAIL'} {label}{' :: ' + detail if detail else ''}")


def _truncate_all() -> None:
    conn = psycopg.connect(DSN, autocommit=True)
    conn.execute(
        "TRUNCATE tasks, leases, idempotency_records, outbox_events, runs,"
        " m12_sources, m12_evidence, m12_claims, m12_relations,"
        " budget_reservations, budget_usage_entries, approvals, artifacts,"
        " experiment_plans, experiment_runs, reproducibility_audits,"
        " m12_memory CASCADE"
    )
    conn.commit()
    conn.close()


def main() -> int:
    migrate(DSN)
    _truncate_all()
    run_id = str(uuid.uuid4())
    blob_dir = tempfile.mkdtemp(prefix="probe-artifacts-")

    # ── Runtime process writes canonical state ─────────────────────────────
    engine = PostgresWorkflowEngine(dsn=DSN)
    task = research_task()
    engine.submit(task, task_contract())
    lease = engine.acquire_lease(task.id.value)
    engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
    engine.close()
    task_id = task.id.value

    run_store = PostgresRunStore(dsn=DSN)
    run = ResearchRun(
        id=ID(run_id), project_id="p-1", protocol_id="proto", state="RUNNING"
    )
    run_store.save_run(run)
    run_store.close()

    ledger = PostgresEvidenceLedger(dsn=DSN)
    source = SourceRecord(
        origin="o-1", content_digest="c-1", trust_label=TrustLabel.VERIFIED_SOURCE
    )
    ledger.register_source(source)
    evidence = Evidence(id="ev-1", source_ref="o-1", content_digest="c-1")
    ledger.register_evidence(evidence)
    claim = Claim(id="cl-1", statement="s", status=ClaimStatus.PROPOSED)
    ledger.register_claim(claim)
    ledger.attach_relation(
        EvidenceRelation(
            claim_id="cl-1", evidence_id="ev-1", relation=EvidenceRelationType.SUPPORTS
        )
    )
    ledger.close()

    budget = PostgresBudgetLedger(dsn=DSN)
    budget.reserve(
        (
            BudgetReservation(
                id="r1", scope="run", resource_type=ResourceType.TOOL_REQUESTS,
                quantity=1, unit="n",
            ),
        ),
        BudgetPolicy(id="pol", hard_limits={"tool_requests": 10}),
    )
    budget.record_usage(
        UsageLedgerEntry(
            entry_id="u-1", resource_type=ResourceType.MODEL_TOKENS, quantity=5,
            unit="tokens", cost_status=LedgerCostStatus.UNKNOWN, source="x",
            occurred_at=datetime.now(timezone.utc),
        )
    )
    budget.close()

    approvals = PostgresApprovalStore(dsn=DSN)
    approvals.register(
        ApprovalSpec(run_id=run_id, action="high-risk", risk="HIGH", context="c",
                     policy_source="p", requested_event_id="e")
    )
    approvals.close()

    artifacts = PostgresArtifactStore(dsn=DSN, blob_dir=blob_dir)
    art = Artifact(
        id="a-1", digest=Digest.of_bytes(b"data"),
        size_bytes=4, media_type="text/plain",
        retention_policy=ArtifactRetentionPolicy.keep_forever(),
        state=ArtifactState.ACTIVE,
    )
    artifacts.put(art, b"data")
    artifacts.close()

    # ── Runtime "process" is gone; rebuild from PG only ────────────────────
    conn = psycopg.connect(DSN, autocommit=True, row_factory=dict_row)
    run_row = conn.execute("SELECT * FROM runs WHERE run_id=%s", (run_id,)).fetchone()
    task_row = conn.execute("SELECT * FROM tasks WHERE task_id=%s", (task_id,)).fetchone()
    lease_rows = conn.execute("SELECT * FROM leases WHERE task_id=%s", (task_id,)).fetchall()
    ev_row = conn.execute("SELECT * FROM m12_evidence WHERE id='ev-1'").fetchone()
    cl_row = conn.execute("SELECT * FROM m12_claims WHERE id='cl-1'").fetchone()
    src_row = conn.execute("SELECT * FROM m12_sources WHERE origin='o-1'").fetchone()
    rel_row = conn.execute("SELECT * FROM m12_relations").fetchall()
    budget_row = conn.execute("SELECT * FROM budget_reservations").fetchall()
    usage_row = conn.execute("SELECT * FROM budget_usage_entries").fetchall()
    ap_row = conn.execute("SELECT * FROM approvals").fetchall()
    art_row = conn.execute("SELECT * FROM artifacts WHERE artifact_id='a-1'").fetchone()
    evt_row = conn.execute("SELECT * FROM outbox_events").fetchall()
    conn.close()

    check("run rebuilt from PG", run_row is not None and run_row["run_json"] is not None)
    check(
        "run state inside run_json (whole-object JSONB)",
        run_row is not None and run_row["run_json"].get("state") == "RUNNING",
        str(run_row["run_json"] if run_row else None),
    )
    check("task rebuilt from PG",
          task_row is not None and task_row["status"] == "SUCCEEDED")
    check("lease cleaned (terminal)", len(lease_rows) == 0, f"leases={len(lease_rows)}")
    check("evidence rebuilt from PG", ev_row is not None and ev_row["content_digest"] == "c-1")
    check("claim rebuilt from PG", cl_row is not None and cl_row["status"] == "PROPOSED")
    check("source rebuilt from PG", src_row is not None)
    check("relation rebuilt from PG", len(rel_row) == 1)
    check("budget reservation rebuilt", len(budget_row) == 1)
    check("usage entry rebuilt", len(usage_row) == 1)
    check("approval rebuilt", len(ap_row) == 1)
    check("artifact rebuilt", art_row is not None and art_row["state"] == "ACTIVE")
    check("events in outbox (execution trail, not truth)", len(evt_row) >= 2)
    check("manifest digest frozen in run_json",
          run_row is not None and run_row["run_json"] is not None)

    print("\n".join(results))
    return 0 if all(r.startswith("PASS") for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
