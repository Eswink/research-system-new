"""Postgres migration files — existence, ordering, and migration gate behavior.

Expected version sets are **derived** from the real migrations directory, never
frozen as literals: a hardcoded list silently rots every time a milestone adds
a migration (that is exactly how the M14 audit probe started failing after 005
landed, and how this file drifted to a stale 4-entry `_MIG_EXPECT`).
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest

import adapters.postgres.db as dbmod
from adapters.postgres.db import bootstrap, migrate
from packages.application.ports.errors import PermanentPortError

pytestmark = pytest.mark.postgres

_MIGRATIONS_DIR = Path("adapters/postgres/migrations")


def _migration_versions() -> list[int]:
    """Ordered versions discovered from the real migrations directory."""
    versions: list[int] = []
    for path in sorted(_MIGRATIONS_DIR.glob("*.sql")):
        prefix = path.stem.split("_", 1)[0]
        if prefix.isdigit():
            versions.append(int(prefix))
    return sorted(versions)


def _next_version() -> int:
    versions = _migration_versions()
    return (max(versions) if versions else 0) + 1


def test_migration_file_exists_and_ordered() -> None:
    files = sorted(_MIGRATIONS_DIR.glob("*.sql"))
    assert len(files) >= 2, "001_initial.sql and 002_domain_state.sql must exist"
    names = [p.name for p in files]
    assert names == sorted(names), "migration files must be lexicographically ordered"
    assert names[0].startswith("001_"), "first migration must be 001_initial.sql"
    for name in names:
        prefix = name.split("_", 1)[0]
        assert prefix.isdigit() and len(prefix) == 3, f"invalid migration prefix: {name}"
    versions = _migration_versions()
    assert versions == list(range(1, len(versions) + 1)), (
        f"migration versions must be a gapless 1..N sequence, got {versions}"
    )


def _dsn() -> str:
    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
    )


def _drop_schema() -> None:
    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public")
    conn.commit()
    conn.close()


@pytest.fixture(autouse=True)
def _restore_schema_after_dropping() -> Iterator[None]:
    """After any migration test that drops the schema, force clean re-migrate.

    Unconditional drop+migrate keeps the shared DB in a consistent state for
    other postgres tests (the migration tests are the only ones that drop).
    """
    yield
    _drop_schema()
    migrate(_dsn())


def test_bootstrap_from_empty_creates_all_tables() -> None:
    _drop_schema()
    expected = _migration_versions()
    applied = bootstrap(_dsn())
    assert applied == expected, f"expected {expected}, got {applied}"
    conn = psycopg.connect(_dsn(), autocommit=True)
    cur = conn.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
    )
    tables = {r[0] for r in cur.fetchall()}
    conn.close()
    for table in (
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
        "eval_reports",
        "pricing_snapshots",
        "migration_version",
    ):
        assert table in tables, f"missing table {table} after bootstrap"


def test_migrate_idempotent_rerun() -> None:
    _drop_schema()
    expected = _migration_versions()
    first = migrate(_dsn())
    second = migrate(_dsn())
    assert first == expected
    assert second == []


def test_migrate_fails_on_incompatible_schema_without_partial_apply() -> None:
    _drop_schema()
    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("CREATE TABLE tasks (task_id INTEGER PRIMARY KEY, garbage TEXT)")
    conn.commit()
    conn.close()
    with pytest.raises(PermanentPortError):
        migrate(_dsn())
    conn = psycopg.connect(_dsn(), autocommit=True)
    row = conn.execute("SELECT count(*) AS n FROM migration_version").fetchone()
    conn.close()
    assert row is not None
    assert row[0] == 0, "no partial migration rows should remain"


def test_late_migration_failure_keeps_prior_files_committed() -> None:
    """A failing migration must not roll back earlier successfully applied files.

    Regression for the M14 audit finding: the previous runner used nested
    savepoints on a non-autocommit connection, so a failure in file N aborted
    files 1..N-1 too (DB left at version 0). After the fix, each file commits
    independently; a failed file leaves the DB at the last applied version.
    """
    _drop_schema()
    prior = _migration_versions()
    broken_version = _next_version()
    _scratch, broken, original = _scratch_with_broken_migration(broken_version)
    try:
        with pytest.raises(PermanentPortError):
            migrate(_dsn())
        versions, tables = _versions_and_tables()
        assert versions == set(prior), f"prior files must stay committed: {versions}"
        assert "t_partial" not in tables, "failed file must be fully rolled back"
        assert broken_version not in versions
        # Fix the file; re-run must apply only the missing version.
        _fix_broken_migration(broken)
        applied = migrate(_dsn())
        assert applied == [broken_version], f"expected only [{broken_version}], got {applied}"
    finally:
        _restore_migrations_dir(original)
    _drop_schema()
    migrate(_dsn())


def _scratch_with_broken_migration(version: int) -> tuple[Path, Path, Path]:
    """Copy real migrations + inject a failing migration file (given version)."""
    scratch = Path(tempfile.mkdtemp(prefix="mig-late-fail-"))
    for f in sorted(_MIGRATIONS_DIR.glob("*.sql")):
        (scratch / f.name).write_bytes(f.read_bytes())
    broken = scratch / f"{version:03d}_broken.sql"
    broken.write_text(
        "CREATE TABLE IF NOT EXISTS t_partial (id TEXT);\n"
        "INSERT INTO t_partial VALUES ('x');\n"
        "CREATE TABLE IF NOT EXISTS t_partial_2 (id TEXT, broken);\n",
        encoding="utf-8",
    )
    original = dbmod._MIGRATIONS_DIR
    dbmod._MIGRATIONS_DIR = scratch
    return scratch, broken, original


def _versions_and_tables() -> tuple[set[int], set[str]]:
    conn = psycopg.connect(_dsn(), autocommit=True)
    rows = conn.execute("SELECT version FROM migration_version").fetchall()
    tables = {
        r[0]
        for r in conn.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname='public'"
        ).fetchall()
    }
    conn.close()
    return {int(r[0]) for r in rows}, tables


def _fix_broken_migration(broken: Path) -> None:
    broken.write_text(
        "CREATE TABLE IF NOT EXISTS t_partial (id TEXT);\nINSERT INTO t_partial VALUES ('x');\n",
        encoding="utf-8",
    )


def _restore_migrations_dir(original: Path) -> None:
    dbmod._MIGRATIONS_DIR = original
