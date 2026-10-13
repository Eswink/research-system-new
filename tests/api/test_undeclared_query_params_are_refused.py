"""GOAL-20261013-072（序 40）：**未声明查询参数的路由也不再静默吞掉查询参数** —— EC-02 / EC-03。

**为什么单列**：序 36/37 判「已声明」读面、序 38 让事件流声明它消费的参数、序 39 做写面 ——
而**实测**：全仓 **58 条** GET **未声明**任何查询参数，其中收到查询串时**照样 200**
（`/projects?definitely_unknown=1` ⇒ 200）⇒ 调用方**以为设了筛选**而拿到全量。

**判的是什么**：① 未声明读面收到**任何**查询参数 ⇒ **422 + 逐个点名**（正文明写
「该路由不接受查询参数」—— 空集的已知集清单是空串，要说清楚）；② **多个未知逐个点名**；
③ **缺省形态逐字不变**（不传参数 ⇒ 非 422，且关键键不变）；④ **非 API 路径**不受影响；
⑤ 已声明面（序 37/38）与**写面**（序 39）**不回归**。
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.api.run_fixtures import make_run_ready_deps

#: **未声明**查询参数的读面（受判面；来自 EC-01 的 58 条清单，取跨模块样本）。
_UNDECLARED: tuple[str, ...] = (
    "/projects",
    "/health",
    "/policy/capabilities",
    "/cluster/workers",
)

#: **已声明**的读面（对照臂：纪律形态不同 —— 给已知集清单）。
_DECLARED: tuple[tuple[str, str], ...] = (
    ("/notifications", "limit"),
    ("/models", "endpoint_id"),
)


def _client() -> TestClient:
    return TestClient(create_app(make_run_ready_deps()))


def test_an_undeclared_read_route_refuses_any_query_parameter() -> None:
    """EC-02 ①：未声明读面 ⇒ **任何**查询参数都 422 + 点名（改动前 200 静默）。"""
    failures: list[str] = []
    with _client() as client:
        for path in _UNDECLARED:
            response = client.get(f"{path}?definitely_unknown=1")
            if response.status_code != 422:
                failures.append(f"{path}?definitely_unknown=1 ⇒ {response.status_code}（应 422）")
                continue
            detail = response.json().get("detail", "")
            if "definitely_unknown" not in detail:
                failures.append(f"{path} 未点名 definitely_unknown：{detail}")
            if "accepts no query parameters" not in detail:
                failures.append(f"{path} 正文未明写「不接受查询参数」：{detail}")
    assert failures == [], failures


def test_several_unknown_parameters_are_each_named() -> None:
    """EC-02 ②：**多个未知逐个点名**（只报第一个会让「还有哪些打错了」读不出来）。"""
    with _client() as client:
        detail = client.get("/projects?alpha=1&beta=2").json()["detail"]
        assert "alpha" in detail and "beta" in detail, detail


def test_the_default_form_is_verbatim() -> None:
    """EC-02 ③：**缺省形态逐字不变** —— 不传参数 ⇒ 非 422，且关键键不变（EC-01 基线）。"""
    with _client() as client:
        projects = client.get("/projects")
        assert projects.status_code == 200, projects.text
        assert isinstance(projects.json(), list), projects.json()
        health = client.get("/health")
        assert health.status_code == 200, health.text
        assert sorted(health.json()) == ["composition", "pricing_degraded", "status", "version"], (
            sorted(health.json())
        )


def test_a_non_api_path_is_unaffected() -> None:
    """EC-03 ①（射程反证臂）：**无匹配路由**的路径 ⇒ 404（与本纪律无关）。"""
    with _client() as client:
        assert client.get("/nope?zz=1").status_code == 404


def test_the_declared_routes_keep_their_own_shape() -> None:
    """EC-03 ②：**已声明**读面照旧（给**该路由的**已知集，不是「不接受」措辞）。"""
    with _client() as client:
        for path, known in _DECLARED:
            response = client.get(f"{path}?definitely_unknown=1")
            assert response.status_code == 422, response.text
            detail = response.json()["detail"]
            assert "known:" in detail and known in detail, (path, detail)
            assert "accepts no query parameters" not in detail, (path, detail)


def test_the_write_face_is_not_in_this_scope() -> None:
    """EC-03 ③（射程反证臂）：**写面**不受本纪律（序 39 的 DTO 纪律另有其面）。

    受判面两臂（`Y-4` 反证臂的受判面）：① 正确的写请求（**不带**查询参数）照旧成功；
    ② 写请求**带**查询参数 ⇒ **不**被本守卫打断（`declared_query_params` 对非读面
    返回 `None` ⇒ 不在射程）；若序列 40 把 `None` 支也纳入 ⇒ ② 立刻变红。
    """
    with _client() as client:
        response = client.post(
            "/projects",
            json={"name": "probe-scope"},
            headers={"Idempotency-Key": f"g072-{uuid.uuid4()}"},
        )
        assert response.status_code == 201, response.text
        with_query = client.post(
            "/projects?zz=1",
            json={"name": "probe-scope-2"},
            headers={"Idempotency-Key": f"g072-{uuid.uuid4()}"},
        )
        assert with_query.status_code == 201, (
            "写面**不**在本纪律射程内（`None` 支一字不动）—— 射程越界会误伤",
            with_query.status_code,
            with_query.text[:200],
        )
