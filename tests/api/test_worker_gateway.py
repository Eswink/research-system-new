"""Worker gateway auth + lifecycle tests (M16 WP1).

Uses the in-process TestClient against a FakeWorkerRegistry + Fake credential
resolver. Covers enrollment gating, session-token issuance/binding, handshake
fail-closed, anti-impersonation, anti-replay, and the non-loopback TLS guard.
"""

from __future__ import annotations

from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from adapters.fakes.credential_resolver import FakeCredentialResolver
from adapters.fakes.worker_registry import FakeWorkerRegistry
from packages.application.ports.credential_resolver import SecretValue
from services.api.worker_gateway import auth
from services.api.worker_gateway.app import create_worker_app
from services.api.worker_gateway.deps import WorkerGatewayDeps
from services.api.worker_gateway.settings import WorkerGatewaySettings

_ENROLLMENT = "enroll-secret-xyz"


def _as_dict(body: Any) -> dict[str, object]:
    return cast(dict[str, object], body)


def _deps(**overrides: object) -> WorkerGatewayDeps:
    settings = WorkerGatewaySettings(enrollment_credential_ref="WORKER_ENROLLMENT_SECRET")
    creds = FakeCredentialResolver({"WORKER_ENROLLMENT_SECRET": _ENROLLMENT})
    kwargs: dict[str, object] = {
        "registry": FakeWorkerRegistry(),
        "credentials": creds,
        "settings": settings,
    }
    kwargs.update(overrides)
    return WorkerGatewayDeps(**kwargs)  # type: ignore[arg-type]


def _client(deps: WorkerGatewayDeps) -> TestClient:
    return TestClient(create_worker_app(deps))


def _register(client: TestClient, worker_id: str = "worker-a") -> dict[str, object]:
    resp = client.post(
        "/worker/v1/register",
        headers={"X-Worker-Enrollment": _ENROLLMENT},
        json={
            "worker_id": worker_id,
            "protocol_version": "1",
            "runtime_version": "0.1.0",
            "capabilities": ["docker"],
            "backend_kinds": ["DOCKER"],
            "platform": "linux/amd64",
            "partition_slots": [0, 1],
            "max_concurrency": 2,
        },
    )
    assert resp.status_code == 200, resp.text
    return _as_dict(resp.json())


def test_health_is_open() -> None:
    client = _client(_deps())
    assert client.get("/worker/v1/health").json() == {"status": "ok"}


def test_register_returns_token_and_ready_state() -> None:
    client = _client(_deps())
    body = _register(client)
    assert body["state"] == "READY"
    assert body["registration_generation"] == 1
    assert isinstance(body["session_token"], str) and len(body["session_token"]) >= 32


def test_register_without_enrollment_rejected() -> None:
    client = _client(_deps())
    resp = client.post(
        "/worker/v1/register",
        json={
            "worker_id": "w",
            "protocol_version": "1",
            "runtime_version": "0.1.0",
            "capabilities": [],
            "backend_kinds": ["DOCKER"],
            "platform": "linux/amd64",
            "partition_slots": [],
            "max_concurrency": 1,
        },
    )
    assert resp.status_code == 401


def test_register_wrong_enrollment_rejected() -> None:
    client = _client(_deps())
    resp = client.post(
        "/worker/v1/register",
        headers={"X-Worker-Enrollment": "wrong"},
        json={
            "worker_id": "w",
            "protocol_version": "1",
            "runtime_version": "0.1.0",
            "capabilities": [],
            "backend_kinds": ["DOCKER"],
            "platform": "linux/amd64",
            "partition_slots": [],
            "max_concurrency": 1,
        },
    )
    assert resp.status_code == 401


def test_register_unsupported_protocol_fails_closed() -> None:
    client = _client(_deps())
    resp = client.post(
        "/worker/v1/register",
        headers={"X-Worker-Enrollment": _ENROLLMENT},
        json={
            "worker_id": "w",
            "protocol_version": "999",
            "runtime_version": "0.1.0",
            "capabilities": [],
            "backend_kinds": ["DOCKER"],
            "platform": "linux/amd64",
            "partition_slots": [],
            "max_concurrency": 1,
        },
    )
    assert resp.status_code == 409


def test_register_unsupported_backend_fails_closed() -> None:
    client = _client(_deps())
    resp = client.post(
        "/worker/v1/register",
        headers={"X-Worker-Enrollment": _ENROLLMENT},
        json={
            "worker_id": "w",
            "protocol_version": "1",
            "runtime_version": "0.1.0",
            "capabilities": [],
            "backend_kinds": ["MODAL"],
            "platform": "linux/amd64",
            "partition_slots": [],
            "max_concurrency": 1,
        },
    )
    assert resp.status_code == 409


def test_heartbeat_with_valid_token_accepted() -> None:
    client = _client(_deps())
    body = _register(client)
    resp = client.post(
        "/worker/v1/heartbeat",
        headers={"Authorization": f"Bearer {body['session_token']}"},
        json={"worker_id": "worker-a", "registration_generation": 1},
    )
    assert resp.status_code == 200
    assert resp.json()["accepted"] is True


def test_heartbeat_without_token_rejected() -> None:
    client = _client(_deps())
    _register(client)
    resp = client.post(
        "/worker/v1/heartbeat",
        json={"worker_id": "worker-a", "registration_generation": 1},
    )
    assert resp.status_code == 401


def test_heartbeat_impersonation_rejected() -> None:
    client = _client(_deps())
    body = _register(client, "worker-a")
    resp = client.post(
        "/worker/v1/heartbeat",
        headers={"Authorization": f"Bearer {body['session_token']}"},
        json={"worker_id": "worker-victim", "registration_generation": 1},
    )
    assert resp.status_code == 401


def test_heartbeat_stale_generation_rejected() -> None:
    client = _client(_deps())
    body = _register(client, "worker-a")
    resp = client.post(
        "/worker/v1/heartbeat",
        headers={"Authorization": f"Bearer {body['session_token']}"},
        json={"worker_id": "worker-a", "registration_generation": 0},
    )
    assert resp.status_code == 401


def test_reregister_voids_previous_session_token() -> None:
    client = _client(_deps())
    first = _register(client, "worker-a")
    second = _register(client, "worker-a")
    assert second["registration_generation"] == 2
    # old token no longer authenticates
    resp = client.post(
        "/worker/v1/heartbeat",
        headers={"Authorization": f"Bearer {first['session_token']}"},
        json={"worker_id": "worker-a", "registration_generation": 1},
    )
    assert resp.status_code == 401


def test_non_loopback_bind_without_tls_refuses_to_start() -> None:
    deps = _deps(bind_host="0.0.0.0")
    with pytest.raises(auth.WorkerGatewayTlsError):
        create_worker_app(deps)


def test_non_loopback_bind_with_tls_allowed() -> None:
    settings = WorkerGatewaySettings(
        enrollment_credential_ref="WORKER_ENROLLMENT_SECRET", require_tls=True
    )
    deps = WorkerGatewayDeps(
        registry=FakeWorkerRegistry(),
        credentials=FakeCredentialResolver({"WORKER_ENROLLMENT_SECRET": _ENROLLMENT}),
        settings=settings,
        bind_host="10.0.0.5",
    )
    app = create_worker_app(deps)
    assert app is not None


def test_auth_helpers_constant_time_and_hashing() -> None:
    assert auth.verify_enrollment(_ENROLLMENT, _ENROLLMENT) is True
    assert auth.verify_enrollment("nope", _ENROLLMENT) is False
    assert auth.verify_enrollment(None, _ENROLLMENT) is False
    assert auth.verify_enrollment("", "") is False
    digest = auth.hash_session_token("abc")
    assert digest == auth.hash_session_token("abc")
    assert digest != auth.hash_session_token("abd")
    assert auth.extract_bearer("Bearer xyz") == "xyz"
    assert auth.extract_bearer("Basic xyz") is None
    assert auth.extract_bearer(None) is None


def test_secret_value_repr_never_leaks_enrollment() -> None:
    secret = SecretValue(_ENROLLMENT)
    assert _ENROLLMENT not in repr(secret)
