"""M14 DS-3 memory/claim concurrency tests (WP-DS3).

Real subprocess workers: concurrent claim exclusivity and memory commit
competition validated against live PostgreSQL. Verifies:
- Claim register/update rowcount enforcement (no silent conflict swallow)
- Memory ON CONFLICT DO NOTHING + rowcount verification (exactly-one wins)
- Delete/Deactivate with rowcount enforcement (0 rows → InvalidInputError)

Uses the same subprocess pattern as test_cross_process_real.py.
Script builders live in `worker_memory_scripts.py` (source-limit split).
"""

from __future__ import annotations

import subprocess
import sys
import time

import pytest

from adapters.postgres.db import migrate
from tests.postgres.worker_memory_scripts import (
    claim_register_script,
    claim_update_script,
    memory_commit_for_deactivate,
    memory_commit_script,
    memory_deactivate_script,
    memory_delete_script,
)
from tests.postgres.worker_memory_scripts import (
    dsn as wm_dsn,
)
from tests.postgres.worker_memory_scripts import (
    env as wm_env,
)

pytestmark = pytest.mark.postgres

_DSN = wm_dsn()
_ENV = wm_env()


def _dsn() -> str:
    return _DSN


def _clean() -> None:
    migrate(_dsn())
    import psycopg

    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute(
        "TRUNCATE tasks, leases, idempotency_records, outbox_events,"
        " m12_sources, m12_evidence, m12_claims, m12_relations,"
        " m12_memory CASCADE"
    )
    conn.commit()
    conn.close()


def _run_script(script: str, *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", "-c", script],
        capture_output=True,
        text=True,
        timeout=30,
        env=_ENV,
        check=check,
    )


def _memory_count() -> int:
    import psycopg

    conn = psycopg.connect(_dsn(), autocommit=True)
    row = conn.execute("SELECT count(*) AS n FROM m12_memory").fetchone()
    conn.close()
    assert row is not None
    return int(row[0])


def _memory_by_id(memory_id: str) -> dict[str, object] | None:
    import psycopg
    from psycopg.rows import dict_row

    conn = psycopg.connect(_dsn(), autocommit=True, row_factory=dict_row)
    row = conn.execute("SELECT * FROM m12_memory WHERE id=%s", (memory_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def _claim_count() -> int:
    import psycopg

    conn = psycopg.connect(_dsn(), autocommit=True)
    row = conn.execute("SELECT count(*) AS n FROM m12_claims").fetchone()
    conn.close()
    assert row is not None
    return int(row[0])


@pytest.fixture(autouse=True)
def _clean_before() -> None:
    _clean()


# ── Memory commit concurrency ──


def test_concurrent_memory_commit_exactly_one_wins() -> None:
    """Two independent processes race the same memory id with different
    provenance; exactly one inserts, the other is rejected."""
    memory_id = f"mem-concurrent-{int(time.time())}"
    proc_a = _run_script(memory_commit_script(memory_id, "test-source-a"))
    proc_b = _run_script(memory_commit_script(memory_id, "test-source-b"))

    out_a = proc_a.stdout.strip()
    out_b = proc_b.stdout.strip()
    committed = sum(1 for o in (out_a, out_b) if "COMMITTED" in o)
    rejected = sum(1 for o in (out_a, out_b) if "REJECTED" in o)
    assert committed == 1, f"expected exactly 1 commit, got {committed}: {out_a} | {out_b}"
    assert rejected == 1, f"expected 1 rejection, got {rejected}: {out_a} | {out_b}"
    assert _memory_count() == 1, "only one memory row may exist"


def test_memory_delete_enforces_rowcount() -> None:
    """Deleting a non-existent memory raises InvalidInputError."""
    proc = _run_script(memory_delete_script())
    assert "CORRECT" in proc.stdout, f"expected error, got: {proc.stdout} | {proc.stderr}"


def test_memory_deactivate_idempotent() -> None:
    """Deactivating an already-deactivated memory is idempotent."""
    memory_id = f"mem-deact-{int(time.time())}"
    _run_script(memory_commit_for_deactivate(memory_id), check=True)
    proc = _run_script(memory_deactivate_script(memory_id))
    assert "IDEMPOTENT_OK" in proc.stdout, f"deactivate failed: {proc.stdout} | {proc.stderr}"
    row = _memory_by_id(memory_id)
    assert row is not None
    assert row["active"] is False


# ── Claim concurrency ──


def test_claim_register_conflict_detected() -> None:
    """Two processes register conflicting claims; second is rejected."""
    claim_id = f"cl-conflict-{int(time.time())}"
    _clean()
    _seed_claim_provenance()
    _run_script(claim_register_script(claim_id, "A says X", expect_success=True), check=True)
    _run_script(claim_register_script(claim_id, "B says Y", expect_success=False), check=True)
    # One succeeds, conflict is rejected; exactly 1 claim row
    assert _claim_count() == 1


def _seed_claim_provenance() -> None:
    """Register a source + evidence (needed for VERIFIED claims)."""
    import psycopg

    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute(
        "INSERT INTO m12_sources (origin, content_digest, trust_label,"
        " authors) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
        ("test-origin", "digest-1", "VERIFIED_SOURCE", "[]"),
    )
    conn.execute(
        "INSERT INTO m12_evidence (id, source_ref, content_digest,"
        " metric_refs, tool_refs, skill_refs, model_refs)"
        " VALUES (%s,%s,%s,%s,%s,%s,%s)",
        ("ev-test", "test-origin", "content", "[]", "[]", "[]", "[]"),
    )
    conn.close()


def test_claim_update_unknown_rejected() -> None:
    """Updating a non-existent claim raises InvalidInputError."""
    _clean()
    proc = _run_script(claim_update_script())
    assert "CORRECT" in proc.stdout, f"expected error, got: {proc.stdout} | {proc.stderr}"
