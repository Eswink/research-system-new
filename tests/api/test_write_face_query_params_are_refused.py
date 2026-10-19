"""GOAL-20261013-073（序 41）：**写面路由也不再静默吞掉查询参数** —— EC-02 / EC-03。

**为什么单列**：序 37/38 接通「已声明读面」、序 40 接通「未声明读面」、序 39 做写面**请求体** ——
而**实测**：写面带查询参数**照样成功**（`POST /projects?definitely_unknown=1` ⇒ 201、
`PATCH /projects/{id}?zz=1` ⇒ 200）⇒ 调用方**以为带了控制参数**。

**判的是什么**：① 写面带**任何**查询参数 ⇒ **422 + 逐个点名 + 明写「不接受查询参数」**；
② **多个未知逐个点名**；③ **缺省形态逐字不变**（不带查询串的写请求 ⇒ 201/200 + 键集）；
④ **读面不回归**（已声明给 known 清单 / 未声明的同样拒绝）；⑤ **无路由**路径 ⇒ 404（既有语义）。
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.api.run_fixtures import make_run_ready_deps


def _client() -> TestClient:
    return TestClient(create_app(make_run_ready_deps()))


def _project(client: TestClient) -> str:
    response = client.post(
        "/projects",
        json={"name": "probe-g073"},
        headers={"Idempotency-Key": f"g073-{uuid.uuid4()}"},
    )
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def test_a_write_route_refuses_any_query_parameter() -> None:
    """EC-02 ①：非读面 ⇒ **任何**查询参数都 422 + 点名（改动前 201/200 静默）。"""
    with _client() as client:
        created = client.post(
            "/projects?definitely_unknown=1",
            json={"name": "probe-post"},
            headers={"Idempotency-Key": f"g073-{uuid.uuid4()}"},
        )
        assert created.status_code == 422, created.text
        detail = created.json()["detail"]
        assert "definitely_unknown" in detail, detail
        assert "accepts no query parameters" in detail, detail

        project_id = _project(client)
        patched = client.patch(
            f"/projects/{project_id}?zz=1",
            json={"name": "probe-patch"},
            headers={"Idempotency-Key": f"g073-{uuid.uuid4()}"},
        )
        assert patched.status_code == 422, patched.text
        assert "zz" in patched.json()["detail"], patched.json()


def test_several_unknown_parameters_are_each_named() -> None:
    """EC-02 ②：**多个未知逐个点名**（只报第一个会让「还有哪些打错了」读不出来）。"""
    with _client() as client:
        detail = client.post(
            "/projects?alpha=1&beta=2",
            json={"name": "probe-multi"},
            headers={"Idempotency-Key": f"g073-{uuid.uuid4()}"},
        ).json()["detail"]
        assert "alpha" in detail and "beta" in detail, detail


def test_the_default_write_forms_are_verbatim() -> None:
    """EC-02 ③：**缺省形态逐字不变** —— 不带查询串的写请求 ⇒ 201/200 + 键集（EC-01 基线）。"""
    with _client() as client:
        created = client.post(
            "/projects",
            json={"name": "probe-default"},
            headers={"Idempotency-Key": f"g073-{uuid.uuid4()}"},
        )
        assert created.status_code == 201, created.text
        # GOAL-20261019-089 EC-02：读面新增 `direction`（项目方向）；**键集**是这条判据的
        # 受判事实，「缺省形态逐字不变」在这里的含义是「不因查询串而改变」——新增的
        # 响应字段由 EC-02 的判据单独钉住（`tests/api/test_project_direction.py`）。
        assert sorted(created.json()) == [
            "created_at",
            "direction",
            "id",
            "name",
            "status",
            "updated_at",
        ], sorted(created.json())
        patched = client.patch(
            f"/projects/{created.json()['id']}",
            json={"name": "probe-default-x"},
            headers={"Idempotency-Key": f"g073-{uuid.uuid4()}"},
        )
        assert patched.status_code == 200, patched.text
        assert sorted(patched.json()) == [
            "created_at",
            "direction",
            "id",
            "name",
            "status",
            "updated_at",
        ], sorted(patched.json())


def test_the_read_faces_do_not_regress() -> None:
    """EC-03 ①：**读面不回归** —— 已声明给 known 清单；未声明的同样拒绝（序 40 的靶子）。"""
    with _client() as client:
        declared = client.get("/notifications?limt=5")
        assert declared.status_code == 422, declared.text
        assert "known:" in declared.json()["detail"], declared.json()
        undeclared = client.get("/projects?zz=1")
        assert undeclared.status_code == 422, undeclared.text
        assert "accepts no query parameters" in undeclared.json()["detail"], undeclared.json()
        assert client.get("/notifications?limit=5").status_code == 200
        assert client.get("/projects").status_code == 200


def test_a_non_api_path_is_unaffected() -> None:
    """EC-03 ②（射程反证臂）：**无匹配路由**的路径 ⇒ 404（既有语义，与本纪律无关）。"""
    with _client() as client:
        assert client.get("/nope?zz=1").status_code == 404
        assert (
            client.post(
                "/nope?zz=1", json={}, headers={"Idempotency-Key": f"g073-{uuid.uuid4()}"}
            ).status_code
            == 404
        )


def test_the_body_discipline_is_not_regressed() -> None:
    """EC-03 ③（反证臂）：写面**请求体**纪律（序 39）不回归 —— 打错字段名仍 422 点名。"""
    with _client() as client:
        response = client.post(
            "/projects",
            json={"name": "probe-body", "nam": "typo"},
            headers={"Idempotency-Key": f"g073-{uuid.uuid4()}"},
        )
        assert response.status_code == 422, response.text
        assert any("nam" in str(item.get("loc", [])) for item in response.json()["detail"]), (
            response.json()
        )
