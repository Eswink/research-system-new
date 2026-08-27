"""Postgres migration files — existence and ordering (no live DB)."""

from __future__ import annotations

from pathlib import Path


def test_migration_file_exists_and_ordered() -> None:
    mig_dir = Path("adapters/postgres/migrations")
    files = sorted(mig_dir.glob("*.sql"))
    assert len(files) >= 1, "at least 001_initial.sql must exist"
    names = [p.name for p in files]
    assert names == sorted(names), "migration files must be lexicographically ordered"
    assert names[0].startswith("001_"), "first migration must be 001_initial.sql"
    for name in names:
        prefix = name.split("_", 1)[0]
        assert prefix.isdigit() and len(prefix) == 3, f"invalid migration prefix: {name}"
