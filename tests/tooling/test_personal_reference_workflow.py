"""Personal-production Reference Workflow entrypoint contract."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from adapters.contracts.protocol_loaders import load_protocol
from adapters.execution.gpu_probe import GPU_SANDBOX_IMAGE_DEFAULT
from packages.application.preflight.preflight import compile_and_preflight
from tools.personal_reference_workflow import _catalog, _context, _project

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ROOT / "tools" / "personal_reference_workflow.py"
_GPU_DOCKERFILE = _ROOT / "adapters" / "execution" / "sandbox" / "Dockerfile.gpu"
_ENV_EXAMPLE = _ROOT / ".env.example"
_PERSONAL_COMPOSE = _ROOT / "docker-compose.personal.yml"
_DEPLOYMENT_DOC = _ROOT / "docs" / "operations" / "PERSONAL_DEPLOYMENT.md"


def test_personal_reference_workflow_has_explicit_production_cli() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(_SCRIPT), "--help"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "--run-id" in completed.stdout
    assert "--gpu-image" in completed.stdout
    assert "--live-relay" in completed.stdout


def test_personal_reference_workflow_does_not_compose_fake_or_sqlite_state() -> None:
    source = _SCRIPT.read_text(encoding="utf-8")

    assert "adapters.fakes" not in source
    assert "adapters.sqlite" not in source
    assert "PostgresRunStore" in source
    assert "RemoteExecutionBackend" in source


def test_gpu_image_recipe_normalizes_generated_account_timestamps() -> None:
    source = _GPU_DOCKERFILE.read_text(encoding="utf-8")

    assert "ARG SOURCE_DATE_EPOCH=0" in source
    assert 'touch --date="@${SOURCE_DATE_EPOCH}"' in source
    for generated_path in (
        "/etc/passwd",
        "/etc/group",
        "/etc/shadow",
        "/etc/gshadow",
        "/etc/subuid",
        "/etc/subgid",
        "/var/log/faillog",
        "/var/log/lastlog",
        "/home/researcher",
    ):
        assert generated_path in source


def test_default_gpu_reference_is_digest_pinned_to_upstream_registry() -> None:
    registry = yaml.safe_load(
        _ROOT.joinpath("UPSTREAM_COMPONENTS.yaml").read_text(encoding="utf-8")
    )
    component = next(
        item for item in registry["components"] if item["id"] == "research_os_gpu_base_image"
    )
    digest = component["resolution"]["application_image_digest"]
    expected = f"research-os-gpu-sandbox@{digest}"

    assert GPU_SANDBOX_IMAGE_DEFAULT == expected
    assert expected in _ENV_EXAMPLE.read_text(encoding="utf-8")


def test_personal_environment_declares_formal_catalog_credential() -> None:
    source = _ENV_EXAMPLE.read_text(encoding="utf-8")

    assert "LLM_MAIN_KEY=" in source
    assert "DEV_LLM_API_KEY" in source
    assert "not an alias" in source


def test_personal_postgres_host_port_is_loopback_only() -> None:
    source = _PERSONAL_COMPOSE.read_text(encoding="utf-8")

    assert "127.0.0.1:${RESEARCHOS_POSTGRES_HOST_PORT:-15432}:5432" in source
    assert '"${RESEARCHOS_POSTGRES_HOST_PORT:-15432}:5432"' not in source


def test_deployment_doc_covers_cross_platform_durable_reconstruction() -> None:
    source = _DEPLOYMENT_DOC.read_text(encoding="utf-8")

    for required in (
        "PowerShell",
        "docker buildx build",
        "--build-arg SOURCE_DATE_EPOCH=0",
        "tools/personal_reference_workflow.py",
        "tools/backup.py",
        "tools/restore.py",
        "uv run --frozen --no-sync",
        "LLM_MAIN_KEY",
    ):
        assert required in source


def test_formal_m17_protocol_preflights_with_formal_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_MAIN_KEY", "canary-not-a-real-credential")
    catalog = _catalog()
    project = _project()
    protocol = load_protocol("examples/protocols/m17_gpu_research_v1.yaml")

    plan, report = compile_and_preflight(
        protocol,
        catalog,
        project,
        _context(catalog, project),
    )

    assert plan is not None
    assert report.passed is True
