"""GOAL-20261013-071（序 39）：**写面请求体里打错的字段名不再被静默吞掉** —— EC-02 / EC-03。

**为什么单列**：序 36/37/38 把「未知查询参数」的纪律做成两条读面事实，而**写面**
（POST/PUT 的 JSON 体）打错字段名**照样 200 + 无声丢弃**（**实测**：
`{"protocol_path": …, "trace_di": "typo"}` ⇒ 200）⇒ 调用方**以为设了那个字段**。

**判的是什么**：① 未知字段 ⇒ **422 + 点名那个字段**（`loc` 里出现字段名）；
② **多个未知逐个点名**；③ **已知/缺省形态逐字不变**（正确请求的状态码 + 键集）；
④ **射程**：响应模型**不**受此纪律（我们自己的输出照旧）；⑤ **共享受判面**：
样本 DTO 覆盖多个模块（不是单点）。
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from services.api.app import create_app
from services.api.dto.common import StrictRequestDto
from services.api.dto.runs import RunStartDto
from tests.api.run_fixtures import make_run_ready_deps

_PROTOCOL = "m12_reference_research_v1.yaml"


def _client() -> TestClient:
    return TestClient(create_app(make_run_ready_deps()))


def test_an_unknown_write_body_field_is_named() -> None:
    """EC-02 ①：**未知字段 ⇒ 422 + 点名**（改动前 200 + 无声丢弃）。"""
    with _client() as client:
        response = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": _PROTOCOL, "trace_di": "typo"},
            headers={"Idempotency-Key": f"g071-{uuid.uuid4()}"},
        )
        assert response.status_code == 422, response.text
        detail = response.json()["detail"]
        assert any("trace_di" in str(item.get("loc", [])) for item in detail), (
            "正文必须**点名那个字段**（`loc` 里出现）",
            detail,
        )


def test_several_unknown_fields_are_each_named() -> None:
    """EC-02 ②：**多个未知 ⇒ 逐个点名**（只报第一个会让「还有哪些打错了」读不出来）。"""
    with _client() as client:
        response = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": _PROTOCOL, "alpha": 1, "beta": 2},
            headers={"Idempotency-Key": f"g071-{uuid.uuid4()}"},
        )
        assert response.status_code == 422, response.text
        joined = str(response.json()["detail"])
        assert "alpha" in joined and "beta" in joined, joined


def test_the_known_forms_are_verbatim() -> None:
    """EC-02 ③：**已知/缺省形态逐字不变** —— 正确请求的状态码与键集（EC-01 基线）。"""
    with _client() as client:
        response = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": _PROTOCOL},
            headers={"Idempotency-Key": f"g071-{uuid.uuid4()}"},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert "id" in body and body["state"], body
        assert len(body) == 15, ("键数逐字（EC-01 基线 = 15 键）", sorted(body))


def test_a_second_module_dto_is_covered_too() -> None:
    """EC-02 ④：**射程覆盖多个模块的 DTO**（不是只修了 runs 这一处）。"""
    with _client() as client:
        response = client.post(
            "/projects",
            json={"name": "probe", "nam": "typo"},  # `nam` 打错（正确名 `name`）
            headers={"Idempotency-Key": f"g071-{uuid.uuid4()}"},
        )
        assert response.status_code == 422, response.text
        assert any("nam" in str(item.get("loc", [])) for item in response.json()["detail"]), (
            response.json()
        )


def test_the_shared_strict_base_is_the_mechanism() -> None:
    """EC-02 ⑤（**判机制**）：纪律落在**共享基类**上（不是逐路由校验）。

    受判面 = 基类配置与继承关系：`StrictRequestDto.model_config['extra'] == 'forbid'`
    且样本 DTO 继承它（逐条样本覆盖多模块）。
    """
    assert StrictRequestDto.model_config.get("extra") == "forbid", StrictRequestDto.model_config
    assert issubclass(RunStartDto, StrictRequestDto), (
        "请求体 DTO 必须继承共享严格基类（一处声明、按类生效 —— EC-01 实测选定）"
    )
    from services.api.dto.models import ModelCreateDto
    from services.api.dto.team_protocol import AgentCreateDto

    for dto in (ModelCreateDto, AgentCreateDto):
        assert issubclass(dto, StrictRequestDto), dto.__name__


def test_response_models_are_not_strict() -> None:
    """EC-03 ①（**射程反证臂**）：**响应**模型**不**继承严格基类。

    响应由我们生成 ⇒ 禁字段没有调用方受益面；若响应模型也 strict，我们自己的输出
    会被判红（那是另一面）。受判面 = 响应 DTO 的继承关系。
    """
    from services.api.dto.common import ProblemDto
    from services.api.dto.runs import RunDetailDto

    for dto in (RunDetailDto, ProblemDto):
        assert not issubclass(dto, StrictRequestDto), (
            f"{dto.__name__} 是响应模型 ⇒ 不该受写面纪律（射程如实）"
        )
