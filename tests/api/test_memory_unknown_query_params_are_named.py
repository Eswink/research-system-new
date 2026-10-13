"""GOAL-20261013-068（序 36）：**未知查询参数不再被静默吞掉（记忆读面）** —— EC-02 / EC-03。

**为什么单列**：本轮的靶子是**未知参数**（与已知参数的**语义**无关）；与
`test_memory_author_filter_on_the_http_face.py`（序 35 判**已知**参数的筛与披露）
**分工不同** —— 那一组判「名字对的参数做了什么」，本组判「**打错名字**的参数会被点名」。

**判的是什么**：序 35 让**名字对的**参数通到了 Port，而**打错名字的**照样 200 + 全量
（**实跑**：键仍只有 `['records','scope_note']`）⇒ 调用方**以为筛过了**。
本轮让未知参数**点名拒绝**（422 + 把参数名写进正文），**已知**与**缺省**形态**逐字不变**，
且**射程只**覆盖记忆读面的**两个 GET**（对照组逐条仍照旧 —— 有意边界，非遗漏）。
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi.testclient import TestClient

from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal
from services.api.app import create_app
from tests.api.run_fixtures import make_run_ready_deps

_PROJECT = "example-project"
_MEMORY = f"/projects/{_PROJECT}/memory"
_VALIDITY = f"/projects/{_PROJECT}/memory/validity"
_AT = "2026-05-01T12:00:00%2B00:00"  # `+` 必须编码（否则被解成空格）


def _deps() -> Any:
    """一条记忆（走 store 落 canonical）—— 受控装配（判据只读面）。"""
    from adapters.fakes.memory_store import FakeMemoryStore

    deps = make_run_ready_deps()
    store = FakeMemoryStore(allowed_sources=("probe:unknown-param",))
    store.allow_source("probe:unknown-param")
    deps.memory = store
    store.commit(
        MemoryWriteProposal(
            id="m-one",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="内容 m-one",
            provenance="probe:unknown-param",
            confidence=0.9,
        )
    )
    return deps


def test_an_unknown_query_parameter_is_named() -> None:
    """EC-02 ①：**未知参数 ⇒ 422 + 正文点名**（改动前 200 + 静默吞掉）。"""
    with TestClient(create_app(_deps())) as client:
        response = client.get(f"{_MEMORY}?definitely_not_a_param=1")
        assert response.status_code == 422, response.text
        detail = response.json()["detail"]
        assert "definitely_not_a_param" in detail, ("必须点名那个参数", detail)
        assert "known:" in detail, ("正文要给出**已知**参数（可自纠）", detail)


def test_the_second_memory_get_is_covered_too() -> None:
    """EC-02 ②：**射程的那两条 GET 都受判**（`/memory/validity` 同样点名）。"""
    with TestClient(create_app(_deps())) as client:
        response = client.get(f"{_VALIDITY}?at={_AT}&junk=1")
        assert response.status_code == 422, response.text
        assert "junk" in response.json()["detail"], response.json()


def test_several_unknown_parameters_are_each_named() -> None:
    """EC-02 ③：**多个未知 ⇒ 逐个点名**（只报第一个会让「还有哪些打错了」读不出来）。"""
    with TestClient(create_app(_deps())) as client:
        response = client.get(f"{_MEMORY}?alpha=1&beta=2")
        assert response.status_code == 422, response.text
        detail = response.json()["detail"]
        assert "alpha" in detail and "beta" in detail, ("两个都要点名", detail)


def test_the_known_parameters_still_work_verbatim() -> None:
    """EC-02 ④：**已知参数一字不动**（受判面与上条**只差参数名**）。"""
    with TestClient(create_app(_deps())) as client:
        scoped = client.get(f"{_MEMORY}?scope=project")
        assert scoped.status_code == 200, scoped.text
        assert "filtered_out" in scoped.json(), scoped.json()
        authored = client.get(f"{_MEMORY}?proposed_by=agent:x")
        assert authored.status_code == 200, authored.text
        validity = client.get(_VALIDITY, params={"at": "2026-05-01T12:00:00+00:00"})
        assert validity.status_code == 200, validity.text


def test_the_default_form_is_verbatim() -> None:
    """EC-02 ⑤：**不传参数** ⇒ 载荷与改动前**逐字相同**（键一个不多）。"""
    with TestClient(create_app(_deps())) as client:
        body = client.get(_MEMORY).json()
        assert sorted(body) == ["records", "scope_note"], body


def test_the_range_is_the_two_memory_gets_only() -> None:
    """EC-03 ①：**射程如实**（GOAL-20261013-072 起**改签**：对照臂语义变了）。

    **改动申报（逐条）**：本轮（序 40）把「未声明查询参数」的读面**同样**接通纪律
    ⇒ 原先的对照组断言「其他路由收到无关参数**不**被打断」（`(200,404,405,422)` 模糊集）
    **不再是本轮的射程含义**。改签为：**非读面**才是真对照（写面一字不动，由序 39 的
    DTO 纪律处理）；而 `/projects`（**未声明**读面）现在**也**拒绝 —— 这正是序 40 的靶子。
    本组仍守序 36 的**原始受判面**：两个记忆 GET 都点名。
    """
    deps = _deps()
    with TestClient(create_app(deps)) as client:
        # 未声明**读面** `/projects` 现在**也**拒绝（序 40 的射程扩大，非回归）；
        # 序 41 起**写面**也在射程（注释更正：`declared_query_params` 不再按方法跳过）。

        control = client.get("/projects?unknown_here=1")
        assert control.status_code == 422, (
            "序 40 起：未声明参数的读面**同样**拒绝（射程扩大；此前模糊集断言已改签）",
            control.status_code,
        )
        # 受判面：两个记忆 GET **都**拒绝了。
        assert client.get(f"{_MEMORY}?unknown_here=1").status_code == 422
        assert client.get(f"{_VALIDITY}?at={_AT}&unknown_here=1").status_code == 422


def test_the_known_parameter_set_is_declared_explicitly() -> None:
    """EC-03 ②（**判关系**）：已知参数集**显式登记**（加参数必须同步改它）。

    受判面 = 那个**集合常量**与**路由签名**的一致性：签名里的查询参数必须都在集合里
    （漏一个 ⇒ 正确请求会被误拒；这正是 `Z-2` 反证臂的形态）。
    """
    import inspect
    from pathlib import Path

    from services.api.memory_query_guard import _KNOWN_QUERY_PARAMS
    from services.api.routers.memory import list_project_memory

    signature = inspect.signature(list_project_memory)
    # `project_id` / `request` 是路径参数与框架注入，不是查询参数。
    query_params = {
        name
        for name, param in signature.parameters.items()
        if name not in ("project_id", "request")
    }
    assert query_params <= set(_KNOWN_QUERY_PARAMS), (
        "签名里的查询参数必须都在已知集合里（否则正确请求会被误拒）",
        sorted(query_params - set(_KNOWN_QUERY_PARAMS)),
    )
    source = (
        Path(__file__).resolve().parents[2] / "services" / "api" / "memory_query_guard.py"
    ).read_text(encoding="utf-8")
    for name in ("scope", "proposed_by", "at"):
        assert f'"{name}"' in source, name


def test_a_write_still_works() -> None:
    """EC-02 反证臂：**写面不受影响**（本轮只动读面的参数校验）。

    与 `tests/api/test_memory_api.py` 的既有手法**同形**：来源要**同时**注册到
    store 白名单**与** ledger（`SourceRecord`）—— denies-by-default 的门链两处都查。
    """
    from adapters.fakes.memory_store import FakeMemoryStore
    from packages.domain.enums import TrustLabel
    from packages.domain.evidence import SourceRecord

    deps = make_run_ready_deps()
    store = FakeMemoryStore()
    deps.memory = store
    ledger = deps.ledger
    assert ledger is not None, "受控装配必须带 ledger（否则写入面无来源可查）"
    ledger.register_source(
        SourceRecord(
            origin="paper://goal068-write",
            content_digest="sha256:" + "b" * 64,
            trust_label=TrustLabel.VERIFIED_SOURCE,
        )
    )
    with TestClient(create_app(deps)) as client:
        response = client.post(
            "/memory/proposals",
            json={
                # `PROJECT` 层级要**策展人批准**（门链的既有纪律）⇒ 这里走 `SESSION`
                # （本轮判的是**参数校验面**，不是层级门）。
                "tier": "SESSION",
                "kind": "FACT",
                "content": "写一条",
                "provenance": "paper://goal068-write",
                "confidence": 0.9,
                "curator_approved": True,
            },
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        assert response.status_code == 201, response.text
