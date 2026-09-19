"""受控出网门链（GOAL-20260919-007 / EC-02 / PLAN-20260919-108）判据。

覆盖四件可判事实：

1. **URL 策略是门链第一环且先于触网**（AC-01/AC-04）：默认策略拒 localhost 时，
   注入的记录型传输替身**一次出站都没有**（不是「没抛异常」）。
2. **反证不空转**（AC-02）：同一 URL 在同一路径下把策略放开，替身**确实收到请求**。
3. **每一项都点名**（AC-03）：URL / 凭据 / 健康 / 能力四条事实各自的拒绝消息点名
   endpoint、credential_ref、health 取值、缺失能力；且 URL 被拒时链**短路**——
   同 endpoint 上不再派生 `ENDPOINT_UNHEALTHY` / `CREDENTIAL_MISSING`。
4. **策略语义单一来源**（AC-05）与 **host 判据只有一份**（AC-06）。

反证与回归对照（AC-07）里「公共域名行为不变」由既有套件承担（`tests/api` 全绿），
不在本文件重复实现。
"""

from __future__ import annotations

import os
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import httpx
from fastapi.testclient import TestClient

from adapters.fakes.credential_resolver import FakeCredentialResolver
from adapters.fakes.model_gateway import FakeModelGateway
from adapters.relay.gateway import OpenAIChatGateway
from packages.application.model_relay.endpoint_policy import (
    EndpointUrlPolicy,
    endpoint_url_refusal,
)
from packages.application.ports import CatalogSnapshot, PreflightContext
from packages.application.preflight.preflight import compile_and_preflight
from packages.domain.enums import EndpointHealth
from packages.domain.models import LLMEndpoint
from services.api.composition import ApiDeps
from services.api.preflight_support import build_endpoint_health, build_endpoint_url_denials
from services.api.settings import ApiSettings

ROOT = Path(__file__).resolve().parents[2]
_PROTOCOL = "console_demo_research_v1.yaml"
_LOCALHOST_URL = "http://127.0.0.1:9/v1"
_CREDENTIAL_REF = "LLM_MAIN_KEY"
# Computed fixture credential（源码里不出现可用字面量；与 tests/api/conftest.py 同口径）。
_FIXTURE_KEY = "fixture-" + "k" * 20


# --------------------------------------------------------------- 测试替身


class _RecordingTransport(httpx.BaseTransport):
    """记录型传输替身：出站调用**可数**，且永不触网（503 ⇒ 快照 ok=False）。"""

    def __init__(self) -> None:
        self.requests: list[str] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(str(request.url))
        return httpx.Response(503, json={"error": "offline-test-double"}, request=request)


class _ProbeDeps:
    """`build_endpoint_health` 走到的三件事实（gateway / credentials / policy）。"""

    def __init__(
        self,
        *,
        gateway: Any,
        credentials: Any,
        policy: EndpointUrlPolicy | None,
    ) -> None:
        self.gateway = gateway
        self.credentials = credentials
        self.endpoint_url_policy = policy


class _StubDeps:
    """只服务协议加载与 URL 裁决的最小 deps 面。"""

    def __init__(self, policy: EndpointUrlPolicy | None = None) -> None:
        self.protocol_draft_service = None
        self.endpoint_url_policy = policy


def _endpoint(base_url: str) -> LLMEndpoint:
    return LLMEndpoint(
        id="main",
        name="Main Relay",
        protocol="OPENAI_COMPATIBLE",
        base_url=base_url,
        credential_ref=_CREDENTIAL_REF,
        max_retries=0,
    )


def _catalog(endpoint: LLMEndpoint) -> CatalogSnapshot:
    return CatalogSnapshot(endpoints={endpoint.id: endpoint})


def _resolver(*, registered: bool = True) -> FakeCredentialResolver:
    credentials = FakeCredentialResolver()
    if registered:
        credentials.register(_CREDENTIAL_REF, _FIXTURE_KEY)
    return credentials


# ----------------------------------------------------- 传输层：出站计数（AC-01/02）


def test_denied_url_makes_zero_outbound_calls() -> None:
    """AC-01：默认策略（deny localhost）⇒ 记录型替身收到的请求数为 0。"""
    transport = _RecordingTransport()
    deps = cast(
        ApiDeps,
        _ProbeDeps(
            gateway=OpenAIChatGateway(transport=transport),
            credentials=_resolver(),
            policy=EndpointUrlPolicy(),
        ),
    )
    health = build_endpoint_health(deps, _catalog(_endpoint(_LOCALHOST_URL)))

    assert transport.requests == []
    assert health == {"main": EndpointHealth.UNKNOWN}


def test_allowed_url_does_probe_so_the_counter_is_not_vacuous() -> None:
    """AC-02 反证：同一 URL、同一路径，策略放开 ⇒ 替身确实收到请求。"""
    transport = _RecordingTransport()
    deps = cast(
        ApiDeps,
        _ProbeDeps(
            gateway=OpenAIChatGateway(transport=transport),
            credentials=_resolver(),
            policy=EndpointUrlPolicy(allow_localhost=True),
        ),
    )
    health = build_endpoint_health(deps, _catalog(_endpoint(_LOCALHOST_URL)))

    assert len(transport.requests) == 1
    assert _LOCALHOST_URL in transport.requests[0]
    assert health == {"main": EndpointHealth.DEGRADED}


def test_missing_credential_stops_before_any_outbound_call() -> None:
    """AC-01：缺配置（凭据不可解析）同样在触网**之前**收敛，出站 0。"""
    transport = _RecordingTransport()
    deps = cast(
        ApiDeps,
        _ProbeDeps(
            gateway=OpenAIChatGateway(transport=transport),
            credentials=_resolver(registered=False),
            policy=EndpointUrlPolicy(allow_localhost=True),
        ),
    )
    health = build_endpoint_health(deps, _catalog(_endpoint(_LOCALHOST_URL)))

    assert transport.requests == []
    assert health == {"main": EndpointHealth.UNKNOWN}


# ------------------------------------------------------------- 策略语义（AC-05）


def _allow_localhost_from_env(raw: str) -> bool:
    os.environ["RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS"] = raw
    try:
        return ApiSettings.from_env().allow_localhost_endpoints
    finally:
        del os.environ["RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS"]


def test_the_env_flag_is_the_single_source_for_the_policy() -> None:
    """AC-05：`RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS` 默认 `0` = deny；四态放行。"""
    from services.api.assembly import _endpoint_url_policy

    assert ApiSettings().allow_localhost_endpoints is False
    assert endpoint_url_refusal(_LOCALHOST_URL, _endpoint_url_policy(ApiSettings())) is not None

    allowed = _endpoint_url_policy(ApiSettings(allow_localhost_endpoints=True))
    assert endpoint_url_refusal(_LOCALHOST_URL, allowed) is None

    assert [_allow_localhost_from_env(raw) for raw in ("1", "true", "yes", "on")] == [
        True,
        True,
        True,
        True,
    ]
    assert _allow_localhost_from_env("0") is False


# ------------------------------------------------------------- 门链点名（AC-03/04）


def _preflight_context() -> PreflightContext:
    from adapters.fakes.budget_ledger import FakeBudgetLedger
    from tests.api.run_fixtures import _build_preflight

    return _build_preflight(_resolver(), FakeBudgetLedger())


def _report(ctx: PreflightContext) -> Any:
    from services.api.protocol_source import load_protocol_with_body

    deps = cast(ApiDeps, _StubDeps(policy=EndpointUrlPolicy()))
    protocol, _body = load_protocol_with_body(deps, _PROTOCOL, None)
    _plan, report = compile_and_preflight(protocol, ctx.catalog, ctx.project, ctx)
    return report


def _messages(report: Any) -> str:
    return " | ".join(finding.message for finding in report.findings)


def _codes(report: Any) -> set[str]:
    return {finding.code for finding in report.findings}


def _with_localhost(ctx: PreflightContext) -> PreflightContext:
    """目录里的 `main` 换成 localhost URL（其余事实不动）。"""
    endpoints = dict(ctx.catalog.endpoints)
    endpoints["main"] = _endpoint(_LOCALHOST_URL)
    return replace(ctx, catalog=replace(ctx.catalog, endpoints=endpoints))


def test_preflight_names_the_url_denial_and_stops_the_chain() -> None:
    """AC-03/AC-04：URL 被拒 ⇒ 只报 `ENDPOINT_URL_DENIED`，不派生下游事实。

    对照：同一 context 去掉裁决注入、并让 health/凭据面为空 ⇒ `ENDPOINT_UNHEALTHY`
    与 `CREDENTIAL_MISSING` **本来**都会报（证明短路不是巧合）。
    """
    blind = replace(_with_localhost(_preflight_context()), endpoint_health={}, credentials=None)
    control = _report(blind)
    assert {"ENDPOINT_UNHEALTHY", "CREDENTIAL_MISSING"} <= _codes(control)

    deps = cast(ApiDeps, _StubDeps(policy=EndpointUrlPolicy()))
    denials = build_endpoint_url_denials(deps, blind.catalog)
    assert set(denials) == {"main"}
    gated = _report(replace(blind, endpoint_url_denials=denials))

    assert "ENDPOINT_URL_DENIED" in _codes(gated)
    assert "ENDPOINT_UNHEALTHY" not in _codes(gated)
    assert "CREDENTIAL_MISSING" not in _codes(gated)
    assert gated.status.value == "FAIL"
    message = _messages(gated)
    assert _LOCALHOST_URL in message
    assert "RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS=1" in message


def test_each_remaining_link_names_its_own_fact() -> None:
    """AC-03：凭据 / 健康 / 能力三条链各自点名阻塞事实。"""
    base = _preflight_context()
    assert _report(base).status.value == "PASS", _messages(_report(base))

    missing_credential = _report(replace(base, credentials=_resolver(registered=False)))
    assert "CREDENTIAL_MISSING" in _codes(missing_credential)
    assert _CREDENTIAL_REF in _messages(missing_credential)

    unhealthy = _report(replace(base, endpoint_health={"main": EndpointHealth.DEGRADED}))
    assert "ENDPOINT_UNHEALTHY" in _codes(unhealthy)
    assert "health is DEGRADED" in _messages(unhealthy)

    models = {
        model_id: replace(model, capabilities={}) for model_id, model in base.catalog.models.items()
    }
    ineligible = _report(replace(base, catalog=replace(base.catalog, models=models)))
    assert "MODEL_ELIGIBILITY" in _codes(ineligible)
    assert "missing: CHAT" in _messages(ineligible)


# --------------------------------------------------------------- 端到端（AC-01）


def _fake_gateway(deps: ApiDeps) -> FakeModelGateway:
    """端口级计数器（`FakeBase.calls`）：出站调用在**端口**上可数。"""
    gateway = deps.gateway
    assert isinstance(gateway, FakeModelGateway)
    return gateway


def _start_demo_run(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/projects/example-project/runs",
        json={"protocol_path": _PROTOCOL},
        headers={"Idempotency-Key": f"egress-{uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    return cast(dict[str, Any], response.json())


def _override_relays(client: TestClient) -> None:
    """目录内**每个** relay 都换成 localhost URL（否则公共 relay 仍会被探测）。"""
    for name in ("main", "agnes-anthropic"):
        response = client.post(
            "/llm-endpoints",
            json={
                "name": name,
                "base_url": _LOCALHOST_URL,
                "api_key": _FIXTURE_KEY,
                "api_style": "chat_completions",
            },
            headers={"Idempotency-Key": f"ep-{uuid.uuid4()}"},
        )
        assert response.status_code == 201, response.text


def _run_failure_message(client: TestClient, run: dict[str, Any]) -> str:
    if run["state"] != "FAILED":
        return ""
    events = client.get(f"/runs/{run['id']}/events").json()
    failed = [event for event in events if event["type"] == "run.failed"]
    assert failed, events
    return str(failed[0]["payload"]["message"])


def test_run_is_refused_with_zero_probes_when_policy_denies(app_deps: ApiDeps) -> None:
    """AC-01 端到端：policy 不允许 ⇒ run 被拒、点名 URL、**端口零探测**。"""
    from services.api.app import create_app

    app_deps.endpoint_url_policy = EndpointUrlPolicy()
    with TestClient(create_app(app_deps)) as client:
        _override_relays(client)
        run = _start_demo_run(client)
        message = _run_failure_message(client, run)

    assert run["state"] == "FAILED"
    assert "ENDPOINT_URL_DENIED" in message
    assert _fake_gateway(app_deps).method_calls("probe_connectivity") == 0


def test_run_probes_when_policy_allows_the_same_url(app_deps: ApiDeps) -> None:
    """AC-02 端到端反证：同一 URL、只把策略放开 ⇒ 探测**确实发生**，且无 URL 拒绝。"""
    from services.api.app import create_app

    app_deps.endpoint_url_policy = EndpointUrlPolicy(allow_localhost=True)
    with TestClient(create_app(app_deps)) as client:
        _override_relays(client)
        run = _start_demo_run(client)
        gateway = _fake_gateway(app_deps)
        probed = {
            call.args_summary for call in gateway.calls if call.method == "probe_connectivity"
        }
        message = _run_failure_message(client, run)

    assert probed, gateway.calls
    assert "ENDPOINT_URL_DENIED" not in message


# --------------------------------------------------------------- 结构判据（AC-06）


def test_a_single_host_judgement_exists_in_the_repo() -> None:
    """AC-06：全仓非测试代码里 host 分类只出现在 `endpoint_policy.py` 一处。"""
    offenders: list[str] = []
    for package in ("packages", "services", "adapters"):
        for path in (ROOT / package).rglob("*.py"):
            if "ipaddress" in path.read_text(encoding="utf-8"):
                offenders.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    assert offenders == ["packages/application/model_relay/endpoint_policy.py"], offenders

    judge = ROOT / "packages" / "application" / "model_relay" / "endpoint_policy.py"
    text = judge.read_text(encoding="utf-8")
    assert "def validate_endpoint_url" in text
    assert "def endpoint_url_refusal" in text
