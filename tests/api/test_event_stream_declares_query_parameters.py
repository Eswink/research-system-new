"""GOAL-20261013-070（序 38）：**事件流路由声明它消费的查询参数** —— EC-02 / EC-03。

**为什么单列**：序 37 的守卫**按签名**决定射程（这是对的），但它**暴露**了更上游的缺陷 ——
`GET /runs/{run_id}/events` 从**原始 `request.query_params`** 读 `cursor` / `poll`，
**却一个都没声明** ⇒ ① OpenAPI 不可见（契约面不完整）；② 守卫按签名跳过它 ⇒ 打错名字
**静默吞掉**（**SSE 模式下更糟**：打错 `poll` ⇒ 静默保持轮询）。

**判的是什么**：① 两个参数**声明进签名**（OpenAPI `parameters[in=query]` 反映）；
② 序 37 的守卫**自动**接管（未知参数 422 + 逐个点名 + 已知集）；③ **正确形态逐字不变**
（`?poll=0` / `?cursor=` / 缺省）；④ **头路径不变**（`Last-Event-ID` 不是查询参数）。
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.api.run_fixtures import make_run_ready_deps

_PROTOCOL = "m12_reference_research_v1.yaml"


def _client() -> TestClient:
    return TestClient(create_app(make_run_ready_deps()))


def _run(client: TestClient, tag: str = "078") -> str:
    response = client.post(
        "/projects/example-project/runs",
        json={"protocol_path": _PROTOCOL},
        headers={"Idempotency-Key": f"goal070-{tag}-{uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    return str(response.json()["id"])


def test_the_stream_declares_the_parameters_it_consumes() -> None:
    """EC-02 ①：签名**声明** `cursor` / `poll` ⇒ OpenAPI 的 `parameters[in=query]` 反映。"""
    spec = create_app(make_run_ready_deps()).openapi()
    params = spec["paths"]["/runs/{run_id}/events"]["get"].get("parameters", [])
    query = sorted(p["name"] for p in params if p["in"] == "query")
    assert query == ["cursor", "poll"], query


def test_an_unknown_parameter_on_the_stream_is_named() -> None:
    """EC-02 ②：**守卫自动接管** —— 打错名字 ⇒ 422 + 点名 + 已知集（改动前 200 静默）。"""
    with _client() as client:
        rid = _run(client)
        response = client.get(f"/runs/{rid}/events?po11=0")
        assert response.status_code == 422, response.text
        detail = response.json()["detail"]
        assert "po11" in detail, detail
        assert "cursor" in detail and "poll" in detail, ("正文给出已知集", detail)
        junk = client.get(f"/runs/{rid}/events?nonsense=1")
        assert junk.status_code == 422, junk.text
        assert "nonsense" in junk.json()["detail"], junk.json()


def test_the_known_forms_are_verbatim() -> None:
    """EC-02 ③：**正确形态逐字不变** —— `?poll=0`（有界快照）与 `?cursor=`（续传裁剪）。"""
    with _client() as client:
        rid = _run(client)
        bounded = client.get(f"/runs/{rid}/events?poll=0", headers={"Accept": "text/event-stream"})
        assert bounded.status_code == 200, bounded.text
        assert bounded.headers["content-type"].startswith("text/event-stream"), bounded.headers
        assert "event:" in bounded.text, ("poll=0 仍发快照帧", bounded.text[:200])
        cursor = client.get(f"/runs/{rid}/events?cursor=zzz")
        assert cursor.status_code == 200, cursor.text
        assert cursor.json() == [], ("`?cursor=zzz` 裁剪语义（zzz 之后无事件）", cursor.json())


def test_the_header_path_is_untouched() -> None:
    """EC-02 ④：**`Last-Event-ID` 头路径不变**（头不是查询参数；本轮不动它）。"""
    with _client() as client:
        rid = _run(client)
        header = client.get(f"/runs/{rid}/events", headers={"Last-Event-ID": "zzz"})
        assert header.status_code == 200, header.text
        assert header.json() == [], ("头路径的裁剪语义与 `?cursor=` 同形", header.json())
        # 头与查询参数**同时**给 ⇒ 头**优先**（解析顺序逐字沿用：`or` 的短路）
        both = client.get(f"/runs/{rid}/events?cursor=aaa", headers={"Last-Event-ID": "zzz"})
        assert both.status_code == 200, both.text
        assert both.json() == [], ("头优先（既有语义逐字保留）", both.json())


def test_the_default_form_is_verbatim() -> None:
    """EC-02 ⑤：**缺省形态逐字不变** —— 不传参数 ⇒ 全量 replay（JSON 数组）。"""
    with _client() as client:
        rid = _run(client)
        body = client.get(f"/runs/{rid}/events")
        assert body.status_code == 200, body.text
        assert isinstance(body.json(), list) and body.json(), body.json()
        assert all("event_id" in item for item in body.json()), body.json()


def test_the_sse_frames_still_carry_id_and_named_events() -> None:
    """EC-03 ①：**SSE 帧格式一字不动**（`id:` / `event:` / `data:` —— 既有客户端契约）。"""
    with _client() as client:
        rid = _run(client)
        text = client.get(
            f"/runs/{rid}/events?poll=0", headers={"Accept": "text/event-stream"}
        ).text
        assert "id: " in text and "event: " in text and "data: " in text, text[:200]


def test_a_second_run_is_not_affected_by_the_first() -> None:
    """EC-03 ②（反证臂）：声明**不**改变路由的**行为边界**（另一条 run 照旧全量）。

    **不**比较事件内容（每次 run 的 `run_id` / digest / 时间戳必然不同 —— 那是
    受控装配的事实，不是本轮的靶子）；比较**形态**：两条 run 的 replay **结构相同**
    （同为非空数组、键集相同）⇒ 声明**没有**把载荷收窄或改写。
    """
    with _client() as client:
        first = _run(client, tag="a")
        second = _run(client, tag="b")
        first_body = client.get(f"/runs/{first}/events").json()
        second_body = client.get(f"/runs/{second}/events").json()
        assert first_body and second_body, (first_body, second_body)
        assert set(first_body[0]) == set(second_body[0]), (
            "两条 run 的事件**键集**必须相同（声明没有改载荷形态）",
            sorted(set(first_body[0]) ^ set(second_body[0])),
        )
