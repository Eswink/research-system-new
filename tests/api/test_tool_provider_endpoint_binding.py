"""provider 端点绑定测试（PLAN-20260915-072 / GOAL-003 cycle 10）。

`endpoint_env` 此前是**声明了没人消费**的字段（示例配置甚至把凭据名写进端点位）。
本文件钉住四件事：

1. 三态解析（未声明 / 变量未设置 / 已设置）且**只读进程环境**——同名值放在文件里
   不被采信（AC-01）；
2. **不泄漏**：端点明文不进 DTO、不进健康 detail、不进 `repr`（AC-02）；
3. **执法**：声明了 `endpoint_env` 而未设置 ⇒ 健康探测不探测、如实 UNKNOWN 并
   点名变量；**去掉声明** ⇒ 同一 fixture 行为不变（门槛挂在声明上）（AC-03）；
4. **可见**：注册读面带绑定三态与指纹，环境变化立刻反映在读面上（AC-04）。
"""

from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from fastapi.testclient import TestClient

from adapters.fakes.tool_provider import FakeToolProvider
from packages.domain.enums import EffectClass, EndpointHealth, ProviderType, TrustLevel
from packages.domain.tools import ToolProviderSpec
from services.api.app import create_app
from services.api.dto.tool_providers import ToolProviderEndpointBindingDto
from services.api.tool_provider_endpoints import (
    BOUND,
    ENV_UNSET,
    NOT_DECLARED,
    EndpointBinding,
    resolve_endpoint_binding,
    unbound_reason,
)

PIN = "sha256:" + "b" * 64
ENDPOINT_ENV = "RESEARCHOS_TEST_PROVIDER_ENDPOINT"
ENDPOINT_VALUE = "http://endpoint.internal.example:8080/v1/rest"
PROVIDER_ID = "bound-probe"


def _spec(
    *, endpoint_env: str | None = ENDPOINT_ENV, kind: ProviderType = ProviderType.REST
) -> ToolProviderSpec:
    return ToolProviderSpec(
        id=PROVIDER_ID,
        kind=kind,
        trust_level=TrustLevel.VERIFIED,
        capabilities=["literature.search"],
        effect_class=EffectClass.READ_ONLY,
        transport="rest",
        endpoint_env=endpoint_env,
        health_check=True,
    )


def _deps() -> Any:
    from tests.api.conftest import make_base_deps

    deps = make_base_deps()
    deps.tool_providers = {PROVIDER_ID: FakeToolProvider()}
    return deps


def _headers(key: str) -> dict[str, str]:
    return {"Idempotency-Key": key}


def test_binding_states_read_the_process_environment_only(tmp_path: Path) -> None:
    """AC-01：三态；解析只认传入的映射（默认进程环境），文件里的同名值不算数。"""
    not_declared = resolve_endpoint_binding(_spec(endpoint_env=None), environ={})
    assert not_declared.state == NOT_DECLARED
    assert not_declared.env_name is None and not_declared.endpoint_digest is None

    unset = resolve_endpoint_binding(_spec(), environ={})
    assert unset.state == ENV_UNSET
    assert unset.env_name == ENDPOINT_ENV
    assert unset.endpoint_digest is None
    assert unbound_reason(unset) == (
        f"provider 声明端点来自环境变量 {ENDPOINT_ENV}，"
        "但进程环境里未设置（endpoint_env 指端点 URL）"
    )

    # 空白值等同未设置（空串不是端点）
    assert resolve_endpoint_binding(_spec(), environ={ENDPOINT_ENV: "   "}).state == ENV_UNSET

    # 同名值放在**文件**里不构成绑定
    endpoint_file = tmp_path.joinpath("endpoint.txt")
    endpoint_file.write_text(ENDPOINT_VALUE, encoding="utf-8")
    assert endpoint_file.read_text(encoding="utf-8") == ENDPOINT_VALUE
    assert resolve_endpoint_binding(_spec(), environ={}).state == ENV_UNSET
    assert resolve_endpoint_binding(_spec(), environ={ENDPOINT_ENV: ENDPOINT_VALUE}).state == BOUND


def test_bound_state_exposes_only_a_fingerprint() -> None:
    """AC-02：绑定后只有指纹；端点明文不出现在 DTO / detail / repr。"""
    binding = resolve_endpoint_binding(_spec(), environ={ENDPOINT_ENV: ENDPOINT_VALUE})
    assert binding.state == BOUND
    assert binding.endpoint_digest is not None and binding.endpoint_digest.startswith("sha256:")
    assert unbound_reason(binding) is None

    # 指纹稳定；换一个值就换一个指纹（"换没换"可被看见）
    again = resolve_endpoint_binding(_spec(), environ={ENDPOINT_ENV: ENDPOINT_VALUE})
    assert again.endpoint_digest == binding.endpoint_digest
    moved = resolve_endpoint_binding(_spec(), environ={ENDPOINT_ENV: ENDPOINT_VALUE + "?x=1"})
    assert moved.endpoint_digest != binding.endpoint_digest

    dto = ToolProviderEndpointBindingDto(
        state=binding.state,
        env_name=binding.env_name,
        endpoint_digest=binding.endpoint_digest,
    )
    for blob in (repr(binding), repr(dto), str(dto.model_dump())):
        assert ENDPOINT_VALUE not in blob
        assert "endpoint.internal.example" not in blob


def test_endpoint_binding_rejects_inconsistent_states() -> None:
    """读面的三个字段必须自洽：只有 BOUND 才允许带指纹。"""
    for bad in (
        {"state": BOUND},
        {"state": ENV_UNSET, "env_name": ENDPOINT_ENV, "endpoint_digest": "sha256:" + "0" * 64},
        {"state": NOT_DECLARED, "env_name": ENDPOINT_ENV},
        {"state": "UNKNOWN_STATE"},
    ):
        try:
            EndpointBinding(**cast(Any, bad))
        except ValueError:
            continue
        raise AssertionError(f"应当拒绝不自洽的绑定：{bad}")


def test_declared_but_unset_endpoint_blocks_the_probe(monkeypatch: Any) -> None:
    """AC-03：声明了 `endpoint_env` 而未设置 ⇒ 不探测、如实 UNKNOWN；去掉声明则不变。"""
    from services.api.preflight_support import NATIVE_PROBE_DETAIL, probe_provider_spec

    monkeypatch.delenv(ENDPOINT_ENV, raising=False)
    deps = _deps()

    blocked = probe_provider_spec(deps, _spec())
    assert blocked.status is EndpointHealth.UNKNOWN
    assert ENDPOINT_ENV in blocked.detail
    assert blocked.observed_schema_digest is None

    # 同一 fixture、同一 kind，只是**没有声明** ⇒ 走原来的探测路径（门槛挂在声明上）
    undeclared = probe_provider_spec(deps, replace(_spec(), endpoint_env=None))
    assert undeclared.status is EndpointHealth.HEALTHY
    assert ENDPOINT_ENV not in undeclared.detail

    # NATIVE 不看端点声明（内置能力没有外部 transport）
    native = probe_provider_spec(deps, replace(_spec(), kind=ProviderType.NATIVE))
    assert native.status is EndpointHealth.HEALTHY
    assert native.detail == NATIVE_PROBE_DETAIL

    # 设置环境变量后回到正常探测路径，且 detail 不泄漏端点
    monkeypatch.setenv(ENDPOINT_ENV, ENDPOINT_VALUE)
    bound = probe_provider_spec(deps, _spec())
    assert bound.status is EndpointHealth.HEALTHY
    assert ENDPOINT_VALUE not in bound.detail


def _register(client: TestClient, *, provider_id: str, endpoint_env: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": provider_id,
        "kind": "REST",
        "capabilities": ["literature.search"],
        "pinned_revision": PIN,
        "effect_class": "READ_ONLY",
        "transport": "rest",
        "health_check": True,
    }
    if endpoint_env is not None:
        payload["endpoint_env"] = endpoint_env
    response = client.post(
        "/tool-provider-registrations", json=payload, headers=_headers(f"reg-{provider_id}")
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def _binding_of(client: TestClient, provider_id: str) -> dict[str, Any]:
    registrations = client.get("/tool-provider-registrations").json()["registrations"]
    found = {item["id"]: item for item in registrations}[provider_id]
    return cast(dict[str, Any], found["endpoint_binding"])


def test_registration_read_surface_carries_the_binding(monkeypatch: Any) -> None:
    """AC-04：注册读面带绑定三态；声明跨存储往返；未声明时是 NOT_DECLARED。"""
    monkeypatch.delenv(ENDPOINT_ENV, raising=False)
    with TestClient(create_app(_deps())) as client:
        declared = _register(client, provider_id="declared-endpoint", endpoint_env=ENDPOINT_ENV)
        assert declared["endpoint_binding"] == {
            "state": ENV_UNSET,
            "env_name": ENDPOINT_ENV,
            "endpoint_digest": None,
        }
        assert _binding_of(client, "declared-endpoint")["state"] == ENV_UNSET

        # 环境变量出现后，同一份注册（声明不变）立刻显示 BOUND + 指纹
        monkeypatch.setenv(ENDPOINT_ENV, ENDPOINT_VALUE)
        rebound = client.get("/tool-provider-registrations").json()["registrations"][0]
        assert rebound["endpoint_binding"]["state"] == BOUND
        assert rebound["endpoint_binding"]["endpoint_digest"] is not None
        assert ENDPOINT_VALUE not in str(rebound)

        plain = _register(client, provider_id="no-endpoint", endpoint_env=None)
        assert plain["endpoint_binding"] == {
            "state": NOT_DECLARED,
            "env_name": None,
            "endpoint_digest": None,
        }


def test_example_config_keeps_credentials_out_of_endpoint_env() -> None:
    """AC-05：随仓库发布的示例配置不得把**凭据名**写进 `endpoint_env`。

    这不是通用启发式门禁，而是钉住本轮修掉的那次真实漂移：示例曾写
    `endpoint_env: NCBI_API_KEY`——字段名说"端点"，值却是凭据名，且没有任何东西会因此报错。
    """
    root = Path(__file__).resolve().parents[2]
    config = root.joinpath("examples", "config", "tool_providers.yaml")
    text = config.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("endpoint_env:"):
            continue
        value = stripped.split(":", 1)[1].strip().upper()
        assert not value.endswith(("_KEY", "_TOKEN", "_SECRET", "_PASSWORD")), (
            f"endpoint_env 承载端点 URL，不承载凭据：{stripped}"
        )


def test_resolver_reads_the_real_process_environment_by_default(monkeypatch: Any) -> None:
    """默认（不传 environ）确实读进程环境——否则前面的注入会掩盖"其实没接线"。"""
    monkeypatch.setenv(ENDPOINT_ENV, ENDPOINT_VALUE)
    assert resolve_endpoint_binding(_spec()).state == BOUND
    monkeypatch.delenv(ENDPOINT_ENV)
    assert resolve_endpoint_binding(_spec()).state == ENV_UNSET
    assert os.environ.get(ENDPOINT_ENV) is None
