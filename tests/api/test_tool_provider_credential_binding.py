"""provider 凭据绑定测试（PLAN-20260915-074 / GOAL-003 cycle 11）。

`ToolProviderSpec` 此前**无法表达**"这个 provider 需要哪个凭据"（要求只活在 adapter
构造参数里，注册面写不了、读面看不见）。本文件钉住四件事：

1. **只查存在性，不物化明文**：判定走 `CredentialResolver.has`，**不调用 `resolve`**
   ——用"`resolve` 一旦被调用就断言失败"的替身把这条口径变成可执行判据（AC-02）；
2. **执法**：声明了 `credential_ref` 而凭据当前解析不到 ⇒ 探测不探测、如实 UNKNOWN
   并点名引用；凭据出现/消失时同一 fixture 结论随之改变；**去掉声明** ⇒ 行为回到
   从前（门槛挂在声明上）（AC-03）；
3. **不泄漏**：凭据值不出现在 DTO 序列化、健康 detail、`repr`、异常消息里（AC-04）；
4. **可见**：注册读面带绑定四态，凭据从不在于在时立刻反映（AC-05）。
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from fastapi.testclient import TestClient

from adapters.fakes.tool_provider import FakeToolProvider
from packages.application.ports.credential_resolver import SecretValue
from packages.domain.enums import EffectClass, EndpointHealth, ProviderType, TrustLevel
from packages.domain.tools import ToolProviderSpec
from services.api.app import create_app
from services.api.dto.tool_providers import ToolProviderCredentialBindingDto
from services.api.tool_provider_credentials import (
    ABSENT,
    NOT_DECLARED,
    PRESENT,
    UNCHECKED,
    CredentialBinding,
    missing_reason,
    resolve_credential_binding,
)

PIN = "sha256:" + "c" * 64
CREDENTIAL_REF = "RESEARCHOS_TEST_PROVIDER_TOKEN"
# 可识别的哨兵值：任何读面/日志里出现它都算泄漏（不是真实凭据）。
SENTINEL = "sentinel-token-not-a-real-secret-0001"
PROVIDER_ID = "credential-bound-probe"


def _spec(
    *, credential_ref: str | None = CREDENTIAL_REF, kind: ProviderType = ProviderType.REST
) -> ToolProviderSpec:
    return ToolProviderSpec(
        id=PROVIDER_ID,
        kind=kind,
        trust_level=TrustLevel.VERIFIED,
        capabilities=["literature.search"],
        effect_class=EffectClass.READ_ONLY,
        transport="rest",
        credential_ref=credential_ref,
        health_check=True,
    )


class _PresenceOnlyResolver:
    """只实现存在性检查的替身；`resolve` 一旦被调用就失败。

    本轮口径是"判定只查存在性、不物化明文"：用一个会炸的 `resolve` 把这条口径变成
    可执行断言——探测/投影路径若偷偷取值，用例立刻红，而不是靠人读代码。
    """

    def __init__(self, refs: set[str]) -> None:
        self._refs = set(refs)
        self.has_calls: list[str] = []

    def grant(self, credential_ref: str) -> None:
        """让凭据出现（模拟用户在 wizard 里录入 / 密钥服务恢复）。"""
        self._refs.add(credential_ref)

    def revoke(self, credential_ref: str) -> None:
        """让凭据消失（模拟进程重启后注册表清空 / 凭据被撤回）。"""
        self._refs.discard(credential_ref)

    def has(self, credential_ref: str) -> bool:
        self.has_calls.append(credential_ref)
        return credential_ref in self._refs

    def resolve(self, credential_ref: str) -> SecretValue:
        raise AssertionError("凭据判定不得调用 resolve（存在性检查不物化明文）")


class _BrokenResolver:
    """存在性检查不可用的替身（凭据边界故障）：不猜，如实 UNCHECKED。"""

    def has(self, credential_ref: str) -> bool:
        raise RuntimeError("credential boundary unavailable")

    def resolve(self, credential_ref: str) -> SecretValue:
        raise RuntimeError("credential boundary unavailable")


def _deps(credentials: Any = None) -> Any:
    from tests.api.conftest import make_base_deps

    deps = make_base_deps()
    deps.tool_providers = {PROVIDER_ID: FakeToolProvider()}
    if credentials is not None:
        deps.credentials = credentials
    return deps


def _headers(key: str) -> dict[str, str]:
    return {"Idempotency-Key": key}


def test_binding_states_and_presence_only_lookup() -> None:
    """AC-02：四态判定；判定过程只调 `has`，`resolve` 一次都没被调用。"""
    resolver = _PresenceOnlyResolver({CREDENTIAL_REF})

    present = resolve_credential_binding(_spec(), resolver=resolver)
    assert present.state == PRESENT
    assert present.credential_ref == CREDENTIAL_REF
    assert present.present is True
    assert missing_reason(present) is None

    absent = resolve_credential_binding(_spec(), resolver=_PresenceOnlyResolver(set()))
    assert absent.state == ABSENT
    assert absent.credential_ref == CREDENTIAL_REF
    assert absent.present is False
    assert missing_reason(absent) == (
        f"provider 声明必需凭据 {CREDENTIAL_REF!r}，但凭据边界当前解析不到它（provider 不可用）"
    )

    not_declared = resolve_credential_binding(
        _spec(credential_ref=None), resolver=_PresenceOnlyResolver(set())
    )
    assert not_declared == CredentialBinding(state=NOT_DECLARED)
    assert missing_reason(not_declared) is None

    # 未声明时**不查**凭据边界（门槛挂在声明上，不是全局收紧）
    undeclared_resolver = _PresenceOnlyResolver(set())
    resolve_credential_binding(_spec(credential_ref=None), resolver=undeclared_resolver)
    assert undeclared_resolver.has_calls == []

    # 空白引用等同未声明（空串不是凭据引用）
    assert (
        resolve_credential_binding(
            _spec(credential_ref=""), resolver=_PresenceOnlyResolver(set())
        ).state
        == NOT_DECLARED
    )

    # 存在性检查抛错 ⇒ 不猜：UNCHECKED，且原因说明"不可证明"
    unchecked = resolve_credential_binding(_spec(), resolver=_BrokenResolver())
    assert unchecked.state == UNCHECKED
    assert unchecked.present is False
    assert missing_reason(unchecked) == (
        f"provider 声明必需凭据 {CREDENTIAL_REF!r}，但凭据存在性检查不可用（已按不可证明收敛）"
    )

    assert resolver.has_calls == [CREDENTIAL_REF]


def test_binding_projection_never_carries_the_secret() -> None:
    """AC-04：值不出现在绑定对象 / DTO / 原因文本里——只回答"在不在"。"""
    resolver = _PresenceOnlyResolver({CREDENTIAL_REF})
    binding = resolve_credential_binding(_spec(), resolver=resolver)
    dto = ToolProviderCredentialBindingDto(
        state=binding.state,
        credential_ref=binding.credential_ref,
        present=binding.present,
    )
    for blob in (repr(binding), repr(dto), str(dto.model_dump()), str(missing_reason(binding))):
        assert SENTINEL not in blob
        assert "value" not in blob


def test_credential_binding_rejects_inconsistent_states() -> None:
    """读面的三个字段必须自洽：只有 PRESENT 才允许 present=True。"""
    for bad in (
        {"state": PRESENT},
        {"state": ABSENT, "credential_ref": CREDENTIAL_REF, "present": True},
        {"state": PRESENT, "credential_ref": CREDENTIAL_REF, "present": False},
        {"state": NOT_DECLARED, "credential_ref": CREDENTIAL_REF},
        {"state": "UNKNOWN_STATE"},
    ):
        try:
            CredentialBinding(**cast(Any, bad))
        except ValueError:
            continue
        raise AssertionError(f"应当拒绝不自洽的绑定：{bad}")


def test_declared_but_absent_credential_blocks_the_probe() -> None:
    """AC-03：声明了必需凭据而它不在 ⇒ 探测不探测、如实 UNKNOWN；去掉声明则不变。"""
    from services.api.preflight_support import probe_provider_spec

    deps = _deps(_PresenceOnlyResolver(set()))

    blocked = probe_provider_spec(deps, _spec())
    assert blocked.status is EndpointHealth.UNKNOWN
    assert CREDENTIAL_REF in blocked.detail
    assert blocked.observed_schema_digest is None

    # 同一 fixture、同一 kind，只是**没有声明** ⇒ 走原来的探测路径（门槛挂在声明上）
    undeclared = probe_provider_spec(deps, replace(_spec(), credential_ref=None))
    assert undeclared.status is EndpointHealth.HEALTHY
    assert CREDENTIAL_REF not in undeclared.detail

    # 凭据出现后回到正常探测路径，且 detail 不泄漏值
    present = probe_provider_spec(_deps(_PresenceOnlyResolver({CREDENTIAL_REF})), _spec())
    assert present.status is EndpointHealth.HEALTHY
    assert SENTINEL not in present.detail

    # 凭据边界抛错 ⇒ 不可证明（不是"可用"也不是"不可用"的伪装）
    broken = probe_provider_spec(_deps(_BrokenResolver()), _spec())
    assert broken.status is EndpointHealth.UNKNOWN
    assert CREDENTIAL_REF in broken.detail


def test_credential_gate_applies_to_native_too() -> None:
    """与端点门槛故意的不对称：NATIVE 跳过 endpoint_env，但**不**跳过凭据。

    端点门槛跳过 NATIVE 是因为 NATIVE 没有外部端点可解析；"声明的必需凭据不在"
    是凭据事实，与传输形态无关——NATIVE provider 同样会因此不可用。
    """
    from services.api.preflight_support import NATIVE_PROBE_DETAIL, probe_provider_spec

    deps = _deps(_PresenceOnlyResolver(set()))

    native_without_declaration = probe_provider_spec(
        deps, replace(_spec(kind=ProviderType.NATIVE), credential_ref=None)
    )
    assert native_without_declaration.status is EndpointHealth.HEALTHY
    assert native_without_declaration.detail == NATIVE_PROBE_DETAIL

    native_blocked = probe_provider_spec(deps, _spec(kind=ProviderType.NATIVE))
    assert native_blocked.status is EndpointHealth.UNKNOWN
    assert CREDENTIAL_REF in native_blocked.detail


def _register(
    client: TestClient, *, provider_id: str, credential_ref: str | None
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": provider_id,
        "kind": "REST",
        "capabilities": ["literature.search"],
        "pinned_revision": PIN,
        "effect_class": "READ_ONLY",
        "transport": "rest",
        "health_check": True,
    }
    if credential_ref is not None:
        payload["credential_ref"] = credential_ref
    response = client.post(
        "/tool-provider-registrations", json=payload, headers=_headers(f"reg-{provider_id}")
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def _registration(client: TestClient, provider_id: str) -> dict[str, Any]:
    """按 id 取注册（不依赖列表顺序）。"""
    registrations = client.get("/tool-provider-registrations").json()["registrations"]
    return cast(dict[str, Any], {item["id"]: item for item in registrations}[provider_id])


def test_registration_read_surface_carries_the_credential_binding() -> None:
    """AC-05：注册读面带凭据绑定；凭据从不在于在时立刻反映，且**不出现值**。"""
    resolver = _PresenceOnlyResolver(set())
    deps = _deps(resolver)
    with TestClient(create_app(deps)) as client:
        declared = _register(client, provider_id="needs-token", credential_ref=CREDENTIAL_REF)
        assert declared["credential_binding"] == {
            "state": ABSENT,
            "credential_ref": CREDENTIAL_REF,
            "present": False,
        }

        # 声明跨存储往返（读的是同一份注册，不是内存里的请求对象）
        stored = _registration(client, "needs-token")
        assert stored["credential_binding"]["state"] == ABSENT

        # 凭据出现后，同一份注册（声明不变）立刻显示 PRESENT
        resolver.grant(CREDENTIAL_REF)
        rebound = _registration(client, "needs-token")
        assert rebound["credential_binding"] == {
            "state": PRESENT,
            "credential_ref": CREDENTIAL_REF,
            "present": True,
        }
        assert SENTINEL not in str(rebound)

        # 凭据消失（进程重启/凭据撤回）⇒ 立刻回到 ABSENT
        resolver.revoke(CREDENTIAL_REF)
        assert _registration(client, "needs-token")["credential_binding"]["state"] == ABSENT

        plain = _register(client, provider_id="no-credential", credential_ref=None)
        assert plain["credential_binding"] == {
            "state": NOT_DECLARED,
            "credential_ref": None,
            "present": False,
        }


def test_health_check_writes_the_credential_gap_into_the_registration() -> None:
    """AC-03/AC-05：health-check 写下的必须是读面看到的那个事实（同一路径，两套真相禁止）。"""
    resolver = _PresenceOnlyResolver(set())
    deps = _deps(resolver)
    with TestClient(create_app(deps)) as client:
        _register(client, provider_id="needs-token", credential_ref=CREDENTIAL_REF)
        checked = client.post(
            "/tool-provider-registrations/needs-token/health-check", headers=_headers("hc-1")
        )
        assert checked.status_code == 200, checked.text
        body = checked.json()
        assert body["last_health"] == EndpointHealth.UNKNOWN.value
        assert CREDENTIAL_REF in body["health_detail"]
        assert body["credential_binding"]["state"] == ABSENT


def test_example_config_keeps_the_optional_ncbi_key_undeclared() -> None:
    """AC-05：示例配置不给 ncbi_eutils 声明 `credential_ref`。

    理由是可验证的：NCBI E-utilities 无 key 也能用（只是限速更严），
    `tests/contracts/test_ncbi_provider_contract.py::test_no_credential_means_no_api_key_param`
    就钉着"无凭据时请求不带 api_key"；而声明 `credential_ref` 的语义是**必需**，
    声明了会让一个可用的 provider 被判不可用。
    """
    import yaml

    root = Path(__file__).resolve().parents[2]
    config = root.joinpath("examples", "config", "tool_providers.yaml")
    providers = yaml.safe_load(config.read_text(encoding="utf-8"))["tool_providers"]
    assert "credential_ref" not in providers["ncbi_eutils"]
    for provider_id, body in providers.items():
        assert "credential_ref" not in body or body["credential_ref"], (
            f"credential_ref 不得为空串（空声明不是声明）：{provider_id}"
        )
