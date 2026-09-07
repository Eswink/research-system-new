"""Root layout regression gate for repository hygiene.

Asserts the engineering-asset boundaries recorded in
docs/operations/REPOSITORY_HYGIENE.md: the root keeps only the allowlisted
YAML anchors, active Compose stacks live in infra/compose/, and no
docker-compose.*.yml remains at the root. The gate only constrains asset
layout; it never inspects or deletes credentials, runtime data or user-local
history.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE_DIR = ROOT / "infra" / "compose"
ALLOWED_ROOT_YAMLS = {
    "UPSTREAM_COMPONENTS.yaml",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
}
EXPECTED_COMPOSE_FILES = {
    "postgres-test.yaml",
    "otel-evidence.yaml",
    "personal-production.yaml",
    "research-validation.yaml",
}


def _root_yaml_names() -> set[str]:
    return {p.name for p in ROOT.glob("*.yml")} | {p.name for p in ROOT.glob("*.yaml")}


def test_root_yaml_files_stay_on_allowlist() -> None:
    assert _root_yaml_names() == ALLOWED_ROOT_YAMLS


def test_no_compose_files_left_at_root() -> None:
    stale = sorted(
        p.name
        for pattern in ("docker-compose*.yml", "docker-compose*.yaml")
        for p in ROOT.glob(pattern)
    )

    assert stale == []


def test_compose_dir_holds_the_four_active_stacks() -> None:
    assert COMPOSE_DIR.is_dir()
    assert {p.name for p in COMPOSE_DIR.glob("*.yaml")} == EXPECTED_COMPOSE_FILES
