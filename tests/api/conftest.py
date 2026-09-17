"""Control Plane API 测试夹具（基础装配；run 相关见 run_fixtures.py）。"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, cast

import pytest
from fastapi.testclient import TestClient

from adapters.fakes.credential_resolver import FakeCredentialResolver
from adapters.fakes.model_gateway import FakeModelGateway
from services.api.app import create_app
from services.api.composition import ApiDeps

# Computed fixture credential (never a real secret).
_FIXTURE_ENDPOINT_KEY = "fixture-" + "k" * 20

if TYPE_CHECKING:
    pass


def make_app_deps(
    *,
    gateway: FakeModelGateway | None = None,
    run_ready: bool = False,
    db_path: str = ":memory:",
) -> ApiDeps:
    """测试装配：Sqlite 配置存储（默认 `:memory:`）+ Fakes + 内存幂等。

    run_ready=True 时装配可冻结 Manifest 的完整 preflight context
    （定义在 run_fixtures.py，避免本文件超行数阈值）。
    `db_path` 传文件路径 ⇒ 控制面走**每线程一条连接**（GOAL-004 cycle 5 = EC-05）；
    默认 `:memory:` 仍共用一条（内存库属于连接）。
    """
    from tests.api.run_fixtures import make_run_ready_deps

    if run_ready:
        return make_run_ready_deps(gateway=gateway)
    return make_base_deps(gateway=gateway, db_path=db_path)


def make_base_deps(
    *, gateway: FakeModelGateway | None = None, db_path: str = ":memory:"
) -> ApiDeps:
    """基础装配（endpoint/model CRUD + probe + run 测试用）。

    连接统一走 `ThreadLocalConnection`：`:memory:` 时它退化成一条共享连接（与既有
    行为逐字一致），文件路径时才真的每线程一条（GOAL-004 cycle 5 = EC-05）。
    实现在 `base_fixtures.py`（本文件的 50 行/函数硬上限）。
    """
    from tests.api.base_fixtures import build_base_deps

    return build_base_deps(gateway=gateway, db_path=db_path)


@pytest.fixture
def app_deps() -> ApiDeps:
    return make_app_deps()


@pytest.fixture
def client(app_deps: ApiDeps) -> Iterator[TestClient]:
    app = create_app(app_deps)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def gateway(app_deps: ApiDeps) -> FakeModelGateway:
    gateway = app_deps.gateway
    assert isinstance(gateway, FakeModelGateway)
    return gateway


@pytest.fixture
def credentials(app_deps: ApiDeps) -> FakeCredentialResolver:
    credentials = app_deps.credentials
    assert isinstance(credentials, FakeCredentialResolver)
    return credentials


@pytest.fixture
def run_ready_deps() -> ApiDeps:
    """可冻结 Manifest 的 run 测试装配（受控 pin；定义见 run_fixtures.py）。"""
    from tests.api.run_fixtures import make_run_ready_deps

    return make_run_ready_deps()


@pytest.fixture
def run_ready_client(run_ready_deps: ApiDeps) -> Iterator[TestClient]:
    app = create_app(run_ready_deps)
    with TestClient(app) as test_client:
        yield test_client


def make_endpoint_payload(name: str = "relay-a", **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": name,
        "base_url": "https://relay.example.com/api/v1",
        "api_key": _FIXTURE_ENDPOINT_KEY,
        "api_style": "chat_completions",
    }
    payload.update(overrides)
    return payload


def create_endpoint(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload = {**make_endpoint_payload(), **overrides}
    response = client.post(
        "/llm-endpoints",
        json=payload,
        headers={"Idempotency-Key": f"k-{uuid.uuid4()}"},
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())
