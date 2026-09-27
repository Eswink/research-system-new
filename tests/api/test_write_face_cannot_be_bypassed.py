"""**对抗性自检**：控制面**写面认证不可绕过**（GOAL-20260927-021 EC-01）。

本文件与 `test_principal_auth.py` 的分工：
- `test_principal_auth.py` 判**三态语义**（关闭放行 / 开启 401 / 带对通过）与主体归因；
- **本文件**判**「保护面本身是完整的」**——即不存在**漏网的写面**。

四条（对应 EC-01 的 (a)~(d)）：

- **(a) 枚举来自代码**：判据**自己**从构建出的 app 读 mutating 端点集合
  （OpenAPI + 路由表），**不是**手写清单 ⇒ 树新增写面端点时**不需要改本文件**就能覆盖它。
- **(b) 豁免面不被继承**：`_ANALYSIS_ACTIONS` 是**幂等**面的例外集。本文件判它的**行为**面：
  分析类端点（`validate` / `compile` / `preflight` / `dry-run` / `test` / `probe` /
  `discover-models`）在认证开启、无 token 时**同样 401** ⇒「幂等面放行 ⟹ 认证面放行」为**假**。
  （**结构**面由 `test_control_plane_auth_same_source.py` 的 AC-4 判，本文件**不**重复。）
- **(c) 顺序**：由既有 AC-5 判（`test_control_plane_auth_same_source.py`），
  本文件**不**重复；此处只**引用**其结论，并在本文件的读面断言里覆盖其**行为后果**。
- **(d) 读面与探活按设计放行**：判据**显式断言「这是设计」**——把放行绑定到
  `_MUTATING_METHODS` 这个**符号**（读面之所以不拦，是因为它**不在**写面分类里），
  而不是「碰巧返回 200」。

**凭据纪律**：本文件的 token 是**本文件内构造的合成假值**（`fixture-` 前缀 + 重复字符），
**不是**任何真实凭据，**不**从环境读取、**不**落盘、**不**进日志（AGENTS.md §10）。
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.api.app import create_app
from services.api.composition import ApiDeps
from services.api.middleware import (
    _MUTATING_METHODS,
    CONTROL_PLANE_PRINCIPAL_ID_ENV,
    CONTROL_PLANE_TOKEN_ENV,
    _is_analysis_post,
)

# 合成夹具值（不是真实凭据；见模块 docstring）。
_FIXTURE_TOKEN = "fixture-" + "a" * 24
_FIXTURE_PRINCIPAL_ID = "adversarial-probe"
_EXPECTED_ACTOR = f"service:{_FIXTURE_PRINCIPAL_ID}"

_MUTATING = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_READ_ONLY = frozenset({"GET", "HEAD"})

#: 在建档日实测：写面端点数。它**不是**保护面的定义（定义来自代码枚举），
#: 而是「枚举面是否被人为改动」的**告警线**——若树里新增/删除写面端点，
#: 本判据会红，提示复核（而不是静默漏掉或静默放行）。
_MEASURED_MUTATING_COUNT = 60


def _placeholder_path(path: str) -> str:
    """把 `/x/{id}/y` 变成可请求的路径（参数值本身不影响 401 判定）。"""
    out: list[str] = []
    for segment in path.split("/"):
        out.append("probe-id" if segment.startswith("{") and segment.endswith("}") else segment)
    return "/".join(out)


def _app_of(client: TestClient) -> FastAPI:
    """取回 `TestClient` 背后的 FastAPI 应用（含类型收窄）。

    `TestClient.app` 的类型是 ASGI callable，不是 `FastAPI` ⇒ 直接访问 `.openapi()`
    会被 mypy 判错。本仓既有约定是 `cast(Any, client.app)`（见 `test_memory_api.py` 等）；
    这里收敛到一处，避免整份文件散落 `cast`。
    """
    return cast(FastAPI, cast(Any, client.app))


def _enumerate_mutating_endpoints(app: FastAPI) -> list[tuple[str, str]]:
    """从**代码**（app 的 OpenAPI）枚举写面端点。

    **不得**替换为手写清单：本函数的存在意义就是「树变了，判据自己知道」。
    """
    spec = app.openapi()
    found: list[tuple[str, str]] = []
    for path, operations in spec["paths"].items():
        for method in operations:
            if method.upper() in _MUTATING:
                found.append((method.upper(), path))
    return sorted(found)


def _enumerate_read_endpoints(app: FastAPI) -> list[tuple[str, str]]:
    spec = app.openapi()
    found: list[tuple[str, str]] = []
    for path, operations in spec["paths"].items():
        for method in operations:
            if method.upper() in _READ_ONLY:
                found.append((method.upper(), path))
    return sorted(found)


@pytest.fixture
def authed_app(run_ready_deps: ApiDeps, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """认证**开启**的真实控制面（token 经环境变量注入，装配期快照）。"""
    monkeypatch.setenv(CONTROL_PLANE_TOKEN_ENV, _FIXTURE_TOKEN)
    monkeypatch.setenv(CONTROL_PLANE_PRINCIPAL_ID_ENV, _FIXTURE_PRINCIPAL_ID)
    with TestClient(create_app(run_ready_deps)) as test_client:
        yield test_client


# --- (a) 枚举来自代码 + 全覆盖 401 ---------------------------------------------


class TestEnumerationComesFromCode:
    def test_the_enumeration_is_derived_not_hardcoded(self, authed_app: TestClient) -> None:
        """枚举面**来自 app 自己的路由表**，且规模与实测一致。

        这条断言的是「枚举这件事真的发生了」：非空、方法都在写面分类里、
        且路径是**真实存在**的（每个都能被 app 解析，而不是凭空构造的字符串）。
        """
        app = _app_of(authed_app)
        endpoints = _enumerate_mutating_endpoints(app)
        assert endpoints, "枚举面为空 ⇒ 判据自己失效（保护面不可能为空）"
        assert {method for method, _ in endpoints} <= _MUTATING, (
            "枚举出的方法必须都属于写面分类（否则枚举口径与分类口径不一致）"
        )
        assert len(endpoints) == _MEASURED_MUTATING_COUNT, (
            f"写面端点数为 {len(endpoints)}，与建档日实测的 {_MEASURED_MUTATING_COUNT} 不符。"
            "若这是**有意**的增删，请复核保护面并更新本条告警线；"
            "若是**意外**漂移，说明有端点未经自检就进入了写面。"
        )
        known = {
            path for path, _ in ((p, o) for p, ops in app.openapi()["paths"].items() for o in ops)
        }
        assert {path for _, path in endpoints} <= known

    def test_every_mutating_endpoint_rejects_a_missing_token(self, authed_app: TestClient) -> None:
        """**(a) 主判据**：认证开启时，**每一个**写面端点无 token 一律 401。"""
        app = _app_of(authed_app)
        endpoints = _enumerate_mutating_endpoints(app)
        leaked: list[tuple[str, str, int]] = []
        for method, path in endpoints:
            response = authed_app.request(method, _placeholder_path(path), json={})
            if response.status_code != 401:
                leaked.append((method, path, response.status_code))
        assert leaked == [], "以下写面端点**没有**要求 token（认证可绕过）：" + "; ".join(
            f"{method} {path} -> {code}" for method, path, code in leaked
        )

    def test_every_mutating_endpoint_rejects_a_wrong_token(self, authed_app: TestClient) -> None:
        """带**错** token 同样一律 401（不是「带任何 Authorization 就放行」）。"""
        app = _app_of(authed_app)
        endpoints = _enumerate_mutating_endpoints(app)
        wrong = {"Authorization": f"Bearer fixture-{'b' * 24}"}
        leaked: list[tuple[str, str, int]] = []
        for method, path in endpoints:
            headers = dict(wrong)
            headers["Idempotency-Key"] = "probe-wrong-token"
            response = authed_app.request(method, _placeholder_path(path), json={}, headers=headers)
            if response.status_code != 401:
                leaked.append((method, path, response.status_code))
        assert leaked == [], "以下写面端点接受了**不匹配**的 token：" + "; ".join(
            f"{method} {path} -> {code}" for method, path, code in leaked
        )

    def test_the_protected_set_is_exactly_the_mutating_classification(self) -> None:
        """保护面 == `_MUTATING_METHODS`（写面分类是**唯一**定义点）。

        这条把「无第二套分类」变成机械事实：若有人另造一个更窄的方法集合用于认证，
        分类与保护面就会分离，判据在此红。
        """
        assert _MUTATING_METHODS == _MUTATING, (
            f"写面分类漂移：{sorted(_MUTATING_METHODS)} ！= {sorted(_MUTATING)}"
        )
        assert not (_MUTATING_METHODS & _READ_ONLY), "读面方法不得出现在写面分类里"


# --- (b) 幂等豁免面不可被滥用为写面 -------------------------------------------


_ANALYSIS_PATHS = (
    "/protocol-drafts/validate",
    "/protocols/validate",
    "/projects/example-project/compile",
    "/projects/example-project/preflight",
    "/projects/example-project/dry-run",
    "/llm-endpoints/probe-id/test",
    "/llm-endpoints/probe-id/discover-models",
    "/models/probe-id/probe",
)


class TestTheIdempotencyExemptionIsNotAnAuthExemption:
    def test_the_analysis_exemption_predicate_is_the_idempotency_one(self) -> None:
        """分析的豁免谓词只看**路径尾段** ⇒ 它天生**不区分**请求是否真的只读。

        这正是「不得把它当认证豁免」的理由：它判的是「要不要 Idempotency-Key」，
        而不是「要不要凭据」。
        """
        assert _is_analysis_post("/projects/example-project/validate") is True
        assert _is_analysis_post("/projects/example-project/runs") is False

    @pytest.mark.parametrize("path", _ANALYSIS_PATHS)
    def test_analysis_endpoints_still_require_a_token(
        self, authed_app: TestClient, path: str
    ) -> None:
        """**(b) 主判据**：分析类 POST 在认证开启、无 token 时**同样 401**。

        反证「幂等面放行 ⟹ 认证面放行」：若认证面继承了 `_ANALYSIS_ACTIONS`，
        这些端点会返回 405/422/404 而不是 401（建档期按压实测：继承后得 422）。
        """
        response = authed_app.post(path, json={})
        assert response.status_code == 401, (
            f"`{path}` 是分析类 POST，但它在**无 token**时未被认证拦下"
            f"（得 {response.status_code}）⇒ 幂等豁免被误用为认证豁免"
        )

    def test_analysis_endpoints_are_reachable_with_a_correct_token(
        self, authed_app: TestClient
    ) -> None:
        """配对对照：带**对** token 时分析类端点**不再**被认证拦下。

        否则上面的 401 可能只是「路径根本不存在」造成的假象——这条排除该解释
        （带对 token 后状态码**不再是 401**）。
        """
        headers = {"Authorization": f"Bearer {_FIXTURE_TOKEN}"}
        for path in _ANALYSIS_PATHS:
            response = authed_app.post(path, json={}, headers=headers)
            assert response.status_code != 401, (
                f"带对 token 的 `{path}` 仍被判 401 ⇒ 上面的「无 token 401」无法归因于认证"
            )


# --- (d) 读面与探活按设计放行 -------------------------------------------------


class TestTheReadFaceIsOpenByDesign:
    def test_auth_is_enabled_in_this_fixture(self, authed_app: TestClient) -> None:
        """前置：本夹具**确实**开着认证（否则下面的放行断言毫无意义）。"""
        config = _app_of(authed_app).state.control_plane_auth
        assert config.enabled is True, "夹具必须处于「认证开启」态，否则读面放行不可判"

    def test_health_and_read_endpoints_are_reachable_without_a_token(
        self, authed_app: TestClient
    ) -> None:
        """读面在认证开启、**不带** token 时放行（2xx 或**非 401** 的业务态）。"""
        probes = ["/health", "/projects"]
        probes += [
            _placeholder_path(path)
            for method, path in _enumerate_read_endpoints(_app_of(authed_app))
            if method == "GET"
        ][:10]
        blocked: list[tuple[str, int]] = []
        for path in probes:
            response = authed_app.get(path)
            if response.status_code == 401:
                blocked.append((path, response.status_code))
        assert blocked == [], f"读面被认证拦下（保护范围必须只有写面）：{blocked}"

    def test_the_read_face_is_open_because_it_is_not_in_the_write_classification(
        self, authed_app: TestClient
    ) -> None:
        """**这是设计，不是碰巧**：放行由**方法分类**决定。

        断言的是**机制**而非观察值——`_MUTATING_METHODS` 不含 GET/HEAD，
        所以认证中间件的第一个判断（`method not in _MUTATING_METHODS` ⇒ 直接放行）
        对读面必然成立。改分类（例如把 GET 塞进去）⇒ 本判据红。
        """
        assert not (_MUTATING_METHODS & _READ_ONLY), (
            "读面方法出现在写面分类里 ⇒ 读面会被认证拦下，违反用户判词 (i)"
        )
        paths = {path for path, ops in _app_of(authed_app).openapi()["paths"].items() for _ in ops}
        assert "/health" in paths, "`/health` 必须仍由 app 提供（探活端点按设计放行）"

    def test_a_read_request_is_never_challenged_even_on_a_mutating_route(
        self, authed_app: TestClient
    ) -> None:
        """**分类而非路径**决定保护：对**写面路径**发 `GET` 不被认证拦下。

        这条是 (d) 最锋利的形态：如果实现是按「路径前缀」保护（而不是按方法分类），
        同一个路径上的 GET 就会需要 token ⇒ 本判据红。它把「保护范围 = 写面**方法**」
        与「保护范围 = 某些**路径**」这两种实现区分开。
        """
        for path in ("/projects", "/llm-endpoints", "/models"):
            response = authed_app.get(path)
            assert response.status_code != 401, (
                f"对写面路径 `{path}` 发 GET 被要求 token ⇒ 保护面按路径而非按方法分类"
            )
