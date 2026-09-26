"""控制面**写面认证**与**请求主体归因**（GOAL-20260926-019 EC-01 / EC-02）。

证明：
- 三态——**未设 token**（认证关闭 + 启动显式警告 + 写面放行）/ **设了 token + 不带或
  带错**（401 且**点名**）/ **设了 token + 带对**（放行且主体进请求上下文）；
- **读面不受保护**（设了 token 但 GET 不带 token 仍 2xx）——保护范围**只有写面**；
- **主体落 canonical**：带 token 的 `decide` 产出的 `approval.decided` 的 actor
  是**配置的主体**，而**不是**占位常量 `user:console`；
- **向后兼容**：认证关闭时 actor **逐字**仍是 `user:console`（显式对照，不靠"套件没红"）。

夹具 token 是**计算出来的合成值**（与 `tests/api/conftest.py` 的
`_FIXTURE_ENDPOINT_KEY` 同纪律）：它**不是**任何真实凭据，生产 token **绝不入仓**
（源码只登记**变量名**，值只存在于运行进程的环境变量里）。
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response

from packages.application.principal_context import current_principal
from services.api.app import create_app
from services.api.approvals import ApprovalSpec
from services.api.composition import ApiDeps
from services.api.middleware import (
    CONTROL_PLANE_PRINCIPAL_ID_ENV,
    CONTROL_PLANE_TOKEN_ENV,
    ControlPlaneAuth,
    PrincipalAuthMiddleware,
    auth_disabled_warning,
    control_plane_auth_from_env,
    verify_control_plane_token,
)

# 合成夹具值（不是真实凭据；见模块 docstring）。
_FIXTURE_TOKEN = "fixture-" + "t" * 24
_FIXTURE_PRINCIPAL_ID = "fixture-principal"
_WRONG_TOKEN = "fixture-" + "x" * 24
_EXPECTED_ACTOR = f"service:{_FIXTURE_PRINCIPAL_ID}"


def _probe_app(config: ControlPlaneAuth) -> FastAPI:
    """最小受控应用：两个端点各自回报「当前请求是否带主体」。

    `/write` 是 POST（写面），`/read` 是 GET（读面）——两侧读的是**同一个**
    `current_principal()`，因此这组用例同时证明**上下文传播**（中间件在
    `call_next` 之前设置 ⇒ 下游处理可见）。
    """
    app = FastAPI()
    app.state.control_plane_auth = config

    def _snapshot() -> dict[str, str | None]:
        principal = current_principal()
        return {"actor": principal.actor if principal is not None else None}

    app.add_api_route("/read", lambda: _snapshot(), methods=["GET"])
    app.add_api_route("/write", lambda: _snapshot(), methods=["POST"])
    # 注册顺序 = 认证在**外层**（本应用只有这一个中间件，顺序即其自身）。
    app.add_middleware(PrincipalAuthMiddleware, config=config)
    return app


def _probe_client(config: ControlPlaneAuth) -> TestClient:
    return TestClient(_probe_app(config))


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestConfigResolution:
    def test_env_leaves_auth_disabled_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(CONTROL_PLANE_TOKEN_ENV, raising=False)
        config = control_plane_auth_from_env()
        assert config.enabled is False
        assert config.token is None

    def test_env_blank_string_is_disabled_not_a_valid_token(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """留空 = 关闭（**不是**「空 token 也算配了」——那会让带空串的请求通过）。"""
        monkeypatch.setenv(CONTROL_PLANE_TOKEN_ENV, "   ")
        assert control_plane_auth_from_env().enabled is False

    def test_env_token_enables_and_principal_id_is_configurable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(CONTROL_PLANE_TOKEN_ENV, _FIXTURE_TOKEN)
        monkeypatch.setenv(CONTROL_PLANE_PRINCIPAL_ID_ENV, _FIXTURE_PRINCIPAL_ID)
        config = control_plane_auth_from_env()
        assert config.enabled is True
        assert config.principal.actor == _EXPECTED_ACTOR

    def test_warning_text_says_auth_is_disabled(self) -> None:
        """警告必须**明确说「无认证」**，且**点名变量**（只说"检查配置"不够）。"""
        text = auth_disabled_warning()
        assert "AUTH IS DISABLED" in text
        assert CONTROL_PLANE_TOKEN_ENV in text
        assert "NOT a statement that the project is secure" in text

    def test_warning_never_echoes_a_token_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """警告文案**只**出现变量名，**不**回显任何 token 值。"""
        monkeypatch.setenv(CONTROL_PLANE_TOKEN_ENV, _FIXTURE_TOKEN)
        config = control_plane_auth_from_env()
        text = auth_disabled_warning()
        assert _FIXTURE_TOKEN not in text
        assert _FIXTURE_TOKEN not in f"{config.principal.actor} {config.enabled}"


class TestTokenComparisonDiscipline:
    def test_empty_never_matches(self) -> None:
        assert verify_control_plane_token(None, _FIXTURE_TOKEN) is False
        assert verify_control_plane_token("", _FIXTURE_TOKEN) is False
        assert verify_control_plane_token(_FIXTURE_TOKEN, None) is False
        assert verify_control_plane_token(_FIXTURE_TOKEN, "") is False

    def test_exact_match_only(self) -> None:
        assert verify_control_plane_token(_FIXTURE_TOKEN, _FIXTURE_TOKEN) is True
        assert verify_control_plane_token(_WRONG_TOKEN, _FIXTURE_TOKEN) is False
        # 前缀不算匹配（长度不同的比较也必须收敛到 False）
        assert verify_control_plane_token(_FIXTURE_TOKEN[:-1], _FIXTURE_TOKEN) is False


class TestThreeStatesAtTheEdge:
    def test_disabled_auth_lets_mutating_requests_through_without_principal(self) -> None:
        with _probe_client(ControlPlaneAuth(token=None)) as client:
            response = client.post("/write")
        assert response.status_code == 200, response.text
        # 放行时**没有**主体 —— 这是「无认证」而不是「已认证」。
        assert response.json()["actor"] is None

    def test_enabled_auth_rejects_missing_token_and_names_the_header(self) -> None:
        config = ControlPlaneAuth(token=_FIXTURE_TOKEN, principal_id=_FIXTURE_PRINCIPAL_ID)
        with _probe_client(config) as client:
            response = client.post("/write")
        assert response.status_code == 401, response.text
        assert "Bearer" in response.json()["detail"]

    def test_enabled_auth_rejects_wrong_token_and_names_the_mismatch(self) -> None:
        config = ControlPlaneAuth(token=_FIXTURE_TOKEN, principal_id=_FIXTURE_PRINCIPAL_ID)
        with _probe_client(config) as client:
            response = client.post("/write", headers=_bearer(_WRONG_TOKEN))
        assert response.status_code == 401, response.text
        assert "does not match" in response.json()["detail"]

    def test_enabled_auth_rejects_non_bearer_scheme(self) -> None:
        config = ControlPlaneAuth(token=_FIXTURE_TOKEN, principal_id=_FIXTURE_PRINCIPAL_ID)
        with _probe_client(config) as client:
            response = client.post("/write", headers={"Authorization": f"Basic {_FIXTURE_TOKEN}"})
        assert response.status_code == 401, response.text

    def test_enabled_auth_allows_correct_token_and_propagates_principal(self) -> None:
        config = ControlPlaneAuth(token=_FIXTURE_TOKEN, principal_id=_FIXTURE_PRINCIPAL_ID)
        with _probe_client(config) as client:
            response = client.post("/write", headers=_bearer(_FIXTURE_TOKEN))
        assert response.status_code == 200, response.text
        # 主体确实传到了端点（上下文在 call_next 之前设置）
        assert response.json()["actor"] == _EXPECTED_ACTOR

    def test_read_face_is_not_protected(self) -> None:
        """设了 token 时，**读面**不带 token 仍然放行（保护范围只有写面）。"""
        config = ControlPlaneAuth(token=_FIXTURE_TOKEN, principal_id=_FIXTURE_PRINCIPAL_ID)
        with _probe_client(config) as client:
            response = client.get("/read")
        assert response.status_code == 200, response.text
        assert response.json()["actor"] is None


# --- 真实控制面：主体落 canonical（EC-01） -------------------------------------


@pytest.fixture
def authed_client(run_ready_deps: ApiDeps, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """认证**开启**的真实控制面（token 经环境变量注入，装配期快照）。"""
    monkeypatch.setenv(CONTROL_PLANE_TOKEN_ENV, _FIXTURE_TOKEN)
    monkeypatch.setenv(CONTROL_PLANE_PRINCIPAL_ID_ENV, _FIXTURE_PRINCIPAL_ID)
    with TestClient(create_app(run_ready_deps)) as test_client:
        yield test_client


def _stage_approval(client: TestClient) -> dict[str, Any]:
    """把一条 run 推进到 WAITING_FOR_APPROVAL 并注册待决审批。"""
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun
    from packages.domain.run_state import ResearchRunState

    deps = cast(Any, client.app).state.deps
    assert deps.approvals is not None
    run_id = str(ID.generate().value)
    run = ResearchRun(
        id=ID(run_id),
        project_id="example-project",
        protocol_id="test_protocol",
        state=ResearchRunState.State.RUNNING,
    )
    deps.run_registry[run_id] = run.transition(ResearchRunState.Transition.REQUEST_APPROVAL)
    approval = deps.approvals.register(
        ApprovalSpec(
            run_id=run_id,
            action="high-risk-tool",
            risk="HIGH",
            context="tool requires human approval",
            policy_source="project-policy:require_approval",
            requested_event_id=f"evt-{uuid.uuid4().hex}",
        )
    )
    return {"run_id": run_id, "approval_id": approval.id, "version": approval.version}


def _decide(client: TestClient, approval_id: str, version: str, *, token: str | None) -> Response:
    headers = {
        "If-Match": version,
        "Idempotency-Key": f"decide-{approval_id}-deny-{uuid.uuid4()}",
    }
    if token is not None:
        headers.update(_bearer(token))
    return cast(
        Response,
        client.post(f"/approvals/{approval_id}/decide", json={"decision": "deny"}, headers=headers),
    )


def _decided_actors(client: TestClient, run_id: str) -> list[str]:
    events = client.get(f"/runs/{run_id}/events").json()
    return [item["actor"] for item in events if item["type"] == "approval.decided"]


def test_authenticated_decision_records_the_configured_principal(authed_client: TestClient) -> None:
    """**EC-01 主判据**：带对 token 的写请求 ⇒ canonical 里的主体是**请求带来的那个**。"""
    staged = _stage_approval(authed_client)
    response = _decide(
        authed_client, staged["approval_id"], staged["version"], token=_FIXTURE_TOKEN
    )
    assert response.status_code == 200, response.text
    actors = _decided_actors(authed_client, staged["run_id"])
    assert actors == [_EXPECTED_ACTOR], actors
    # 反证：占位常量**不再**出现
    assert "user:console" not in actors


def test_unauthenticated_decision_is_rejected_and_writes_nothing(
    authed_client: TestClient,
) -> None:
    """**配对反证**：不带 token 的同一请求 ⇒ 被拒，且 canonical 里**不留**任何决策。"""
    staged = _stage_approval(authed_client)
    response = _decide(authed_client, staged["approval_id"], staged["version"], token=None)
    assert response.status_code == 401, response.text
    # 不能「拒了但写了」：既没有决策事件，run 也还停在等待审批
    assert _decided_actors(authed_client, staged["run_id"]) == []
    assert authed_client.get(f"/runs/{staged['run_id']}").json()["state"] == "WAITING_FOR_APPROVAL"


def test_wrong_token_decision_is_rejected_and_writes_nothing(authed_client: TestClient) -> None:
    staged = _stage_approval(authed_client)
    response = _decide(authed_client, staged["approval_id"], staged["version"], token=_WRONG_TOKEN)
    assert response.status_code == 401, response.text
    assert _decided_actors(authed_client, staged["run_id"]) == []


def test_auth_disabled_keeps_the_baseline_actor_verbatim(run_ready_client: TestClient) -> None:
    """**向后兼容对照**：认证关闭时 actor **逐字**仍是历史常量（实测取值，非推定）。"""
    staged = _stage_approval(run_ready_client)
    response = _decide(run_ready_client, staged["approval_id"], staged["version"], token=None)
    assert response.status_code == 200, response.text
    assert _decided_actors(run_ready_client, staged["run_id"]) == ["user:console"]


def test_read_face_of_the_real_app_stays_open_when_auth_is_enabled(
    authed_client: TestClient,
) -> None:
    """真实 app + 认证开启：`/health` 与普通 GET **不带** token 仍放行。"""
    staged = _stage_approval(authed_client)
    assert authed_client.get("/health").status_code == 200
    assert authed_client.get(f"/runs/{staged['run_id']}").status_code == 200
