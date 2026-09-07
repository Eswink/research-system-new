"""Static security and topology contract for the local Research Compose stack."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "infra" / "compose" / "research-validation.yaml"
PYTHON_DOCKERFILE = ROOT / "infra" / "docker" / "research" / "Dockerfile.python"
CONSOLE_DOCKERFILE = ROOT / "infra" / "docker" / "research" / "Dockerfile.console"
POSTGRES_DOCKERFILE = ROOT / "infra" / "docker" / "research" / "Dockerfile.postgres"
LOOPBACK_PROXY = ROOT / "infra" / "docker" / "research" / "loopback_proxy.py"
DOCKERIGNORE = ROOT / ".dockerignore"
COMPOSE_DOC = ROOT / "docs" / "operations" / "RESEARCH_COMPOSE.md"
EXPECTED_SERVICES = {
    "postgres",
    "otel-collector",
    "api",
    "worker-gateway",
    "worker",
    "console",
    "host-proxy",
}


def _compose() -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(COMPOSE.read_text(encoding="utf-8")))


def _environment(service: dict[str, Any]) -> dict[str, str]:
    environment = service.get("environment", {})
    assert isinstance(environment, dict)
    return {str(key): str(value) for key, value in environment.items()}


def test_research_compose_assets_exist() -> None:
    expected = (
        COMPOSE,
        PYTHON_DOCKERFILE,
        CONSOLE_DOCKERFILE,
        POSTGRES_DOCKERFILE,
        LOOPBACK_PROXY,
        DOCKERIGNORE,
        COMPOSE_DOC,
    )

    missing = [path.relative_to(ROOT).as_posix() for path in expected if not path.is_file()]

    assert missing == []


def test_research_compose_declares_complete_internal_stack() -> None:
    compose = _compose()

    assert set(compose["services"]) == EXPECTED_SERVICES
    assert compose["networks"]["research_internal"]["internal"] is True
    edge_options = compose["networks"]["research_edge"]["driver_opts"]
    assert edge_options["com.docker.network.bridge.enable_ip_masquerade"] == "false"
    assert set(compose["volumes"]) == {
        "research_os_postgres",
        "research_os_control_data",
        "research_os_artifacts",
    }
    assert compose["services"]["otel-collector"]["volumes"] == ["./data/otel:/var/lib/otelcol"]


def test_host_ports_are_loopback_only_and_gateway_is_not_published() -> None:
    services = _compose()["services"]

    for service_name in ("postgres", "otel-collector", "api", "console"):
        assert "ports" not in services[service_name]
    proxy_ports = services["host-proxy"]["ports"]
    assert len(proxy_ports) == 4
    assert all(str(port).startswith("127.0.0.1:") for port in proxy_ports)
    assert "ports" not in services["worker-gateway"]
    assert "ports" not in services["worker"]


def test_host_proxy_has_fixed_targets_and_no_credentials() -> None:
    proxy = _compose()["services"]["host-proxy"]
    rendered_command = " ".join(str(part) for part in proxy["command"])

    assert set(proxy["networks"]) == {"research_internal", "research_edge"}
    assert "environment" not in proxy
    for target in ("api:8000", "console:5173", "postgres:5432", "otel-collector:4318"):
        assert target in rendered_command


def test_worker_shares_gateway_loopback_without_privileged_docker_access() -> None:
    compose = _compose()
    services = compose["services"]
    rendered = COMPOSE.read_text(encoding="utf-8").lower()

    assert services["worker-gateway"]["environment"]["RESEARCHOS_WORKER_GATEWAY_HOST"] == (
        "127.0.0.1"
    )
    assert services["worker"]["network_mode"] == "service:worker-gateway"
    assert services["worker"]["environment"]["RESEARCHOS_WORKER_GATEWAY_URL"] == (
        "http://127.0.0.1:8081"
    )
    assert services["worker"]["environment"]["RESEARCHOS_WORKER_EXECUTION_BACKEND"] == (
        "deterministic"
    )
    assert "docker.sock" not in rendered
    assert "privileged: true" not in rendered


def test_process_environments_keep_worker_credentials_separate() -> None:
    services = _compose()["services"]
    api_environment = _environment(services["api"])
    gateway_environment = _environment(services["worker-gateway"])
    worker_environment = _environment(services["worker"])

    assert "RESEARCHOS_POSTGRES_DSN" in api_environment
    assert "RESEARCHOS_POSTGRES_DSN" in gateway_environment
    assert "WORKER_ENROLLMENT_SECRET" in gateway_environment
    assert "WORKER_ENROLLMENT_SECRET" not in api_environment
    assert "RESEARCHOS_WORKER_ENROLLMENT_SECRET" in worker_environment
    for forbidden in (
        "RESEARCHOS_POSTGRES_PASSWORD",
        "RESEARCHOS_POSTGRES_DSN",
        "RESEARCHOS_DATABASE_URL",
        "DATABASE_URL",
        "POSTGRES_DSN",
        "LLM_MAIN_KEY",
        "DEV_LLM_API_KEY",
    ):
        assert forbidden not in worker_environment


def test_application_containers_are_read_only_and_drop_capabilities() -> None:
    services = _compose()["services"]

    for service_name in ("api", "worker-gateway", "worker", "console", "host-proxy"):
        service = services[service_name]
        assert service["read_only"] is True
        assert service["cap_drop"] == ["ALL"]
        assert "no-new-privileges:true" in service["security_opt"]
        assert service["init"] is True
    assert any(
        str(mount).startswith("/app/apps/web/node_modules/.vite-temp:")
        for mount in services["console"]["tmpfs"]
    )


def test_external_images_and_build_stages_are_digest_pinned() -> None:
    compose = _compose()
    python_dockerfile = PYTHON_DOCKERFILE.read_text(encoding="utf-8")
    console_dockerfile = CONSOLE_DOCKERFILE.read_text(encoding="utf-8")
    postgres_dockerfile = POSTGRES_DOCKERFILE.read_text(encoding="utf-8")

    assert compose["services"]["postgres"]["image"].startswith("research-os/postgres:")
    assert "postgres:16-alpine@sha256:" in postgres_dockerfile
    assert "python:3.12-slim@sha256:" in python_dockerfile
    assert "ghcr.io/astral-sh/uv:0.11.18@sha256:" in python_dockerfile
    assert "node:22.18.0-bookworm-slim@sha256:" in console_dockerfile
    assert "pnpm@9.15.1" in console_dockerfile
    assert 'CMD ["node", "/app/apps/web/node_modules/vite/bin/vite.js"' in console_dockerfile
    assert ":latest" not in "\n".join((python_dockerfile, console_dockerfile, postgres_dockerfile))


def test_research_dockerfiles_do_not_resolve_external_frontends() -> None:
    dockerfiles = (PYTHON_DOCKERFILE, CONSOLE_DOCKERFILE, POSTGRES_DOCKERFILE)

    for dockerfile in dockerfiles:
        source = dockerfile.read_text(encoding="utf-8")
        assert not any(line.startswith("# syntax=") for line in source.splitlines())


def test_python_container_runtime_dependencies_are_direct_and_exact() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = set(pyproject["project"]["dependencies"])

    assert {
        "jsonschema==4.26.0",
        "pydantic==2.13.4",
        "pyyaml==6.0.3",
    } <= dependencies


def test_build_context_excludes_credentials_and_runtime_state() -> None:
    patterns = {
        line.strip()
        for line in DOCKERIGNORE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    for required in (
        ".env",
        ".env.*",
        ".git",
        ".venv",
        "data",
        "scratch",
        "secrets",
        ".cursor/runtime",
    ):
        assert required in patterns


def test_console_proxy_target_is_runtime_configurable() -> None:
    source = (ROOT / "apps" / "web" / "vite.config.ts").read_text(encoding="utf-8")

    assert "RESEARCHOS_API_PROXY_TARGET" in source
    assert "preview:" in source
    assert "target: apiProxyTarget" in source
