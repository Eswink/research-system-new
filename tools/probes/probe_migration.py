"""Independent M14 audit probe: migration/bootstrap failure handling (section 4).

- interrupted migration: a migration file that fails mid-way must roll back
  completely (no partial tables) and leave migration_version at prior state.
- repeat behavior: re-running migrate() after success returns [] and is a no-op.
- bootstrap from empty yields deterministic order [1,2,3,4].
- failure must not be silently repaired by hand SQL — the failed file must
  remain un-applied so the operator fixes the file and re-runs.

M14 audit probe (RECHECK-20260828-022, DoD row 4). Re-runnable.

WARNING: this probe DROPS AND RECREATES the public schema of the target
database several times. Point RESEARCHOS_POSTGRES_DSN at a disposable test
instance, never at a production database.

Run: uv run --frozen --no-sync python -B tools/probes/probe_migration.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

import psycopg  # noqa: E402

import adapters.postgres.db as dbmod  # noqa: E402
from adapters.postgres.db import bootstrap, migrate  # noqa: E402

DSN = os.environ.get(
    "RESEARCHOS_POSTGRES_DSN",
    "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
)
_REAL_MIGRATIONS_DIR = _REPO_ROOT / "adapters" / "postgres" / "migrations"

results: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    results.append(f"{'PASS' if cond else 'FAIL'} {label}{' :: ' + detail if detail else ''}")


def _tables() -> set[str]:
    conn = psycopg.connect(DSN, autocommit=True)
    rows = conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'").fetchall()
    conn.close()
    return {r[0] for r in rows}


def _versions() -> set[int]:
    conn = psycopg.connect(DSN, autocommit=True)
    rows = conn.execute("SELECT version FROM migration_version").fetchall()
    conn.close()
    return {int(r[0]) for r in rows}


def _drop_schema() -> None:
    conn = psycopg.connect(DSN, autocommit=True)
    conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public")
    conn.commit()
    conn.close()


def scenario_empty_bootstrap() -> None:
    _drop_schema()
    applied = bootstrap(DSN)
    check("bootstrap from empty applies [1,2,3,4] in order", applied == [1, 2, 3, 4], str(applied))
    tables = _tables()
    for expected in (
        "tasks",
        "leases",
        "idempotency_records",
        "outbox_events",
        "artifacts",
        "runs",
        "m12_sources",
        "m12_evidence",
        "m12_claims",
        "m12_relations",
        "budget_reservations",
        "budget_usage_entries",
        "approvals",
        "m12_memory",
        "experiment_plans",
        "experiment_runs",
        "reproducibility_audits",
        "migration_version",
    ):
        check(f"table {expected} exists", expected in tables)
    second = migrate(DSN)
    check("re-run migrate is no-op", second == [], str(second))


def scenario_interrupted_migration_rolls_back() -> None:
    """Inject a broken migration file; migrate must fail AND roll back fully."""
    _drop_schema()

    staging = Path(tempfile.mkdtemp(prefix="mig-"))
    # copy real files
    for f in sorted(_REAL_MIGRATIONS_DIR.glob("*.sql")):
        (staging / f.name).write_bytes(f.read_bytes())
    broken = staging / "006_broken.sql"
    broken.write_text(
        "CREATE TABLE IF NOT EXISTS t_partial (id TEXT);\n"
        "INSERT INTO t_partial VALUES ('x');\n"
        "CREATE TABLE IF NOT EXISTS t_partial_2 (id TEXT, broken);\n",  # syntax error
        encoding="utf-8",
    )
    original = dbmod._MIGRATIONS_DIR
    dbmod._MIGRATIONS_DIR = staging
    captured: str = ""
    try:
        try:
            migrate(DSN)
            check("interrupted migration raises", False, "no exception")
        except Exception as exc:
            check("interrupted migration raises", True)
            captured = repr(exc)
        tables = _tables()
        check(
            "no partial table t_partial (rolled back)",
            "t_partial" not in tables,
            f"tables has t_partial={'t_partial' in tables}",
        )
        check("no partial table t_partial_2", "t_partial_2" not in tables)
        check("version 006 not recorded", 6 not in _versions(), str(_versions()))
        # Prior migrations must still have been applied (fail-fast AFTER 001-005)
        check("prior versions 1-5 applied", _versions() == {1, 2, 3, 4, 5}, str(_versions()))
        if captured:
            results.append(f"INFO interrupted migration exception: {captured}")
    finally:
        dbmod._MIGRATIONS_DIR = original
    # After fixing the file, re-running must apply cleanly (no manual SQL).
    broken.write_text(
        "CREATE TABLE IF NOT EXISTS t_partial (id TEXT);\nINSERT INTO t_partial VALUES ('x');\n",
        encoding="utf-8",
    )
    dbmod._MIGRATIONS_DIR = staging
    try:
        applied = migrate(DSN)
        check("fixed migration re-run applies only [6]", applied == [6], str(applied))
        check("re-run no-op again", migrate(DSN) == [])
    finally:
        dbmod._MIGRATIONS_DIR = original
    _drop_schema()
    migrate(DSN)  # restore shared DB state


def scenario_incompatible_schema() -> None:
    _drop_schema()
    conn = psycopg.connect(DSN, autocommit=True)
    conn.execute("CREATE TABLE tasks (task_id INTEGER PRIMARY KEY, garbage TEXT)")
    conn.commit()
    conn.close()
    try:
        migrate(DSN)
        check("incompatible schema raises", False, "no exception")
    except Exception:
        check("incompatible schema raises", True)
    check("no partial version rows", _versions() == set(), str(_versions()))
    _drop_schema()
    migrate(DSN)


def main() -> int:
    scenario_empty_bootstrap()
    scenario_interrupted_migration_rolls_back()
    scenario_incompatible_schema()
    print("\n".join(results))
    # INFO lines are diagnostic context, not failures.
    return 0 if all(r.startswith(("PASS", "INFO")) for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
