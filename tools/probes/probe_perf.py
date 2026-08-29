"""Resource/perf sanity: indexes, connections, idle-in-txn, plan checks.

M14 audit probe (RECHECK-20260828-022, section "perf/EXPLAIN"). Re-runnable.

Prerequisites: a reachable PostgreSQL instance. Override the default local
docker DSN with RESEARCHOS_POSTGRES_DSN.

Run: uv run --frozen --no-sync python -B tools/probes/probe_perf.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

import psycopg  # noqa: E402

DSN = os.environ.get(
    "RESEARCHOS_POSTGRES_DSN",
    "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
)

conn = psycopg.connect(DSN, autocommit=True)

print("=== indexes ===")
rows = conn.execute(
    "SELECT tablename, indexname FROM pg_indexes WHERE schemaname='public'"
    " ORDER BY tablename, indexname"
).fetchall()
for r in rows:
    print(f"{r[0]} -> {r[1]}")

print("\n=== connection/activity ===")
rows2 = conn.execute(
    "SELECT count(*) FROM pg_stat_activity WHERE datname=current_database()"
).fetchone()
print("active conns:", rows2[0])
rows3 = conn.execute(
    "SELECT count(*) FROM pg_stat_activity WHERE datname=current_database()"
    " AND state='idle in transaction'"
).fetchone()
print("idle-in-txn:", rows3[0])

print("\n=== EXPLAIN: lease claim (acquire path) ===")
rows4 = conn.execute(
    "EXPLAIN SELECT * FROM leases WHERE task_id = %s FOR UPDATE", ("x",)
).fetchall()
for r in rows4:
    print(r[0])

print("\n=== EXPLAIN: expired lease scan ===")
rows5 = conn.execute(
    "EXPLAIN SELECT leases.task_id FROM leases WHERE leases.expires_at < now()"
    " FOR UPDATE SKIP LOCKED"
).fetchall()
for r in rows5:
    print(r[0])

print("\n=== EXPLAIN: outbox pending scan ===")
rows6 = conn.execute(
    "EXPLAIN SELECT envelope_json FROM outbox_events WHERE published_at IS NULL ORDER BY created_at"
).fetchall()
for r in rows6:
    print(r[0])

print("\n=== EXPLAIN: run load ===")
rows7 = conn.execute(
    "EXPLAIN SELECT * FROM runs WHERE project_id = %s ORDER BY created_at DESC", ("p1",)
).fetchall()
for r in rows7:
    print(r[0])

conn.close()
