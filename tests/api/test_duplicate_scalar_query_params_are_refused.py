"""GOAL-20261013-074（序 42）：**标量查询参数重复出现不再被静默折叠** —— EC-02 / EC-03。

**为什么单列**：序 37/40/41 接通「未知 / 未声明读面 / 写面」三面，而**同名参数重复出现**时
框架**静默取末值**（**实测**：`?limit=1&limit=2` ⇒ 200，无披露）⇒ 调用方**以为两个值都生效**。

**判的是什么**：① 标量声明的参数重复 ⇒ **422 + 点名该参数 + 明写「只接受一个值」**
（措辞与「未知参数」**分辨**）；② **多个重复逐个点名**；③ **`list` 声明的参数重复 ⇒ 照旧**
（射程边界：`/evaluations/trend?expected_digests` 是 web 客户端合法用法）；
④ **单值 / 缺省形态逐字不变**；⑤ **未知 / 未声明两面不回归**。
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.api.run_fixtures import make_run_ready_deps


def _client() -> TestClient:
    return TestClient(create_app(make_run_ready_deps()))


def test_a_repeated_scalar_param_is_named() -> None:
    """EC-02 ①：标量参数重复 ⇒ **422 + 点名 + 明写「只接受一个值」**（改动前 200 静默）。"""
    with _client() as client:
        response = client.get("/notifications?limit=1&limit=2")
        assert response.status_code == 422, response.text
        detail = response.json()["detail"]
        assert "limit" in detail, detail
        assert "accept exactly one value" in detail, (
            "措辞要与「未知参数」**分辨**（读者要能区分「名字不对」与「给多了」）",
            detail,
        )
        other = client.get("/models?endpoint_id=a&endpoint_id=b")
        assert other.status_code == 422, other.text
        assert "endpoint_id" in other.json()["detail"], other.json()


def test_several_repeated_params_are_each_named() -> None:
    """EC-02 ②：**多个重复逐个点名**（只报第一个会让「还有哪些给多了」读不出来）。"""
    with _client() as client:
        detail = client.get("/cost/daily?date_from=a&date_from=b&date_to=c&date_to=d").json()[
            "detail"
        ]
        assert "date_from" in detail and "date_to" in detail, detail


def test_the_list_declared_param_may_repeat() -> None:
    """EC-02 ③（**射程边界**）：`list` 声明的参数重复 ⇒ **照旧**（不是 422）。

    受判面 = `/evaluations/trend?expected_digests`（声明 `list[str] | None`；
    web 客户端 `params.append(...)` 循环追加 ⇒ 重复是**契约**）。
    该路由在受控装配下 503（metrics 依赖面缺失）—— 本判据只证**不是本纪律拒绝的**
    （422 带 repeated 措辞 ⇒ 会与 503 明显不同）。
    """
    with _client() as client:
        response = client.get("/evaluations/trend?expected_digests=a&expected_digests=b")
        assert response.status_code != 422 or "repeated" not in response.text, (
            "`list` 声明的重复**不得**被本纪律拒绝（射程边界）",
            response.status_code,
            response.text[:200],
        )


def test_the_single_and_default_forms_are_verbatim() -> None:
    """EC-02 ④：**单值 / 缺省逐字不变** —— 200 + 键集（EC-01 基线）。"""
    with _client() as client:
        single = client.get("/notifications?limit=5")
        assert single.status_code == 200, single.text
        assert sorted(single.json()) == ["note", "notifications"], sorted(single.json())
        default = client.get("/notifications")
        assert default.status_code == 200, default.text
        assert sorted(default.json()) == ["note", "notifications"], sorted(default.json())


def test_the_prior_faces_do_not_regress() -> None:
    """EC-03 ①：**未知 / 未声明两面不回归**（序 37/40 的靶子照旧）。"""
    with _client() as client:
        unknown = client.get("/notifications?limt=5")
        assert unknown.status_code == 422, unknown.text
        assert "known:" in unknown.json()["detail"], unknown.json()
        undeclared = client.get("/projects?zz=1")
        assert undeclared.status_code == 422, undeclared.text
        assert "accepts no query parameters" in undeclared.json()["detail"], undeclared.json()


def test_the_write_face_duplicate_is_also_refused() -> None:
    """EC-03 ②：**写面重复同样被拒**（序 41 接通写面后，重复臂自动覆盖它）。"""
    with _client() as client:
        response = client.post(
            "/projects?zz=1&zz=2",
            json={"name": "probe-dup"},
            headers={"Idempotency-Key": f"g074-{uuid.uuid4()}"},
        )
        assert response.status_code == 422, response.text


def test_a_list_declared_export_and_scalar_export_agree() -> None:
    """EC-02 ⑤（**判机制**）：射程由**声明类型**导出 —— `scalar_query_params` 判注解。

    受判面 = 提取函数本身：对 `list[...]` 注解的参数返回它、对标量**不**返回。
    **坑（实测）**：`type("R", (), {"endpoint": fn})()` 会把 `fn` 变成**绑定方法**
    ⇒ 首个形参被吞 ⇒ 必须用**静态方法包装**或**裸函数**（承序 37 的同款实测）。
    """
    from starlette.requests import Request as StarletteRequest

    from services.api.query_param_guard import scalar_query_params

    def endpoint(expected: list[str] | None = None, limit: int = 50) -> None: ...

    def scope_for() -> dict[str, object]:
        # `staticmethod` 包装（承上条的「绑定方法吞首参」坑）；类型面按 mypy 期望收窄。
        route = type("R", (), {"endpoint": staticmethod(endpoint)})()
        return {
            "type": "http",
            "method": "GET",
            "route": route,
            "path": "/x",
            "headers": [],
        }

    assert scalar_query_params(StarletteRequest(scope_for())) == frozenset({"expected"}), (
        "`list[...]` 注解的参数必须被识别（射程边界由**声明类型**导出）"
    )
    bare = {"type": "http", "method": "GET", "path": "/x", "headers": []}
    assert scalar_query_params(StarletteRequest(bare)) == frozenset(), (
        "无 endpoint ⇒ 不推断（不在射程）"
    )
