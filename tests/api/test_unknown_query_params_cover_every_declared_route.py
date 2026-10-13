"""GOAL-20261013-069（序 37）：**未知查询参数在每条已声明路由上点名拒绝** —— EC-02 / EC-03。

**为什么单列**：序 36（`test_memory_unknown_query_params_are_named.py`）判的是**记忆读面**
那两个 GET（**有意**收窄的射程）；本组判**扩散到全体**：全仓**已声明查询参数**的读面路由
都受同一纪律，且已知集**从签名导出**（不手写清单 ⇒ 加参数自动跟着走）。

**判的是什么**：① 守卫本身在位且**从签名导出**（不读手写常量）；② **逐条**已声明路由
都能点名拒绝（**受判面 = 实测的 9 条**，逐条点名，不是抽样）；③ **多个未知逐个点名**；
④ **已知参数与缺省形态逐字不变**；⑤ **未声明参数**的路由**一字不动**（对照臂）。
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from services.api.app import create_app
from services.api.query_param_guard import declared_query_params
from tests.api.run_fixtures import make_run_ready_deps

#: **受判面 = 实测的 9 条已声明查询参数的读面路由**（探针第 1 段的两面交叉读数）。
#: 每格 =（路径, 该路由的**已知集**, 一个**打错**的名字, **必带**的既有参数片段）。
#: 第 4 格非空 = 该路由有**必填**查询参数（否则 422 可能来自「缺必填」而不是点名）。
_DECLARED: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
    ("/cost/daily", ("date_from", "date_to"), "date_fromm", ""),
    ("/evaluations/trend", ("dataset_id", "expected_digests", "limit"), "datasets_id", ""),
    ("/experiment-plans", ("state",), "states", ""),
    ("/models", ("endpoint_id",), "endpoint", ""),
    (
        "/projects/example-project/cost-forecast",
        ("date_from", "date_to", "horizon_days"),
        "horizon_day",
        "",
    ),
    ("/projects/example-project/library", ("kind",), "kinds", ""),
    ("/projects/example-project/memory", ("proposed_by", "scope"), "proposedby", ""),
    (
        "/projects/example-project/memory/validity",
        ("at",),
        "att",
        "at=2026-05-01T12:00:00%2B00:00",
    ),
    ("/notifications", ("limit",), "limt", ""),
    # GOAL-070（序 38）：事件流路由**声明**了它消费的 `cursor` / `poll`
    # ⇒ 守卫**自动**接管（本清单是「app 声明面」的投影，故**必须**跟着长）。
    ("/runs/run-missing/events", ("cursor", "poll"), "po11", ""),
)

#: 无查询声明的读面（对照臂：**不**受此纪律）。
_UNDECLARED: tuple[str, ...] = (
    "/projects",
    "/health",
    "/runs/run-missing/telemetry",
)


def _client() -> TestClient:
    return TestClient(create_app(make_run_ready_deps()))


def test_every_declared_read_route_names_its_unknown_parameters() -> None:
    """EC-02 ①：**逐条**已声明路由打错参数名 ⇒ **422 + 点名**（不是抽样）。

    第 4 格（必带片段）保证 422 是**点名**打错的那个参数，而非「缺必填参数」
    （`Z-2` 形态：判据要能分辨「拒绝的原因」）。
    """
    failures: list[str] = []
    with _client() as client:
        for path, _, typo, required in _DECLARED:
            suffix = f"&{required}" if required else ""
            response = client.get(f"{path}?{typo}=1{suffix}")
            if response.status_code != 422:
                failures.append(f"{path}?{typo}=1 ⇒ {response.status_code}（应 422）")
                continue
            if typo not in response.json().get("detail", ""):
                failures.append(f"{path}?{typo}=1 未点名 {typo}")
    assert failures == [], failures


def test_the_verdict_gives_that_routes_own_known_set() -> None:
    """EC-02 ②：正文给出**该路由自己**的已知集（供自纠）；不是某个全局集合。"""
    with _client() as client:
        detail = client.get("/notifications?limt=5").json()["detail"]
        assert "limit" in detail, detail
        assert "horizon_days" not in detail, ("给的是**该路由**的已知集", detail)
        detail2 = client.get("/projects/example-project/cost-forecast?horizon_day=7").json()[
            "detail"
        ]
        assert "horizon_days" in detail2, detail2
        assert "limit" not in detail2.replace("horizon_days", ""), detail2


def test_several_unknown_parameters_are_each_named() -> None:
    """EC-02 ③：**多个未知 ⇒ 逐个点名**（只报第一个会让「还有哪些打错了」读不出来）。"""
    with _client() as client:
        detail = client.get("/models?endpoint=1&endpint=2").json()["detail"]
        assert "endpoint" in detail and "endpint" in detail, detail


def test_the_known_forms_are_verbatim() -> None:
    """EC-02 ④：**已知参数逐字仍工作**（受判面与①只差参数名）。"""
    with _client() as client:
        assert client.get("/notifications?limit=5").status_code == 200
        assert client.get("/experiment-plans?state=ARCHIVED").status_code == 200
        assert client.get("/projects/example-project/library?kind=prompt").status_code == 200
        assert client.get("/cost/daily?date_from=2026-01-01").status_code == 200
        assert client.get("/projects/example-project/memory?scope=project").status_code == 200


def test_the_default_form_is_verbatim() -> None:
    """EC-02 ⑤：**不传参数** ⇒ 逐字不变（含序 36 的既有载荷形状）。"""
    with _client() as client:
        body = client.get("/projects/example-project/memory").json()
        assert sorted(body) == ["records", "scope_note"], body
        assert client.get("/notifications").status_code == 200
        assert client.get("/experiment-plans").status_code == 200


def test_routes_without_declared_parameters_are_untouched() -> None:
    """EC-03 ①（GOAL-20261013-072 起**改签**：射程扩大 = 未声明读面**同样**拒绝）。

    **改动申报（逐条）**：序 40 把「未声明查询参数」的读面接通纪律 ⇒ 原先断言
    「未声明读面**不**被打断」正是序 40 要**改变**的行为。改签为：
    ① **未声明读面**收到查询参数 ⇒ **422**（序 40 的靶子，逐条点名）；
    ② **缺省形态**（不传参数）⇒ 逐字不变（非 422）；
    ③ **非 API 路径**（如 `/nope`）⇒ 与纪律无关（404）。
    """
    with _client() as client:
        for path in (*_UNDECLARED, "/nope"):
            bare = client.get(path).status_code
            assert bare != 422, (f"{path} 缺省形态不该 422（逐字不变）", bare)
            if path == "/nope":
                continue  # 非 API 路径无路由 ⇒ 不受本纪律
            probed = client.get(f"{path}?definitely_unknown=1").status_code
            assert probed == 422, (
                f"{path} 未声明查询参数 ⇒ 序 40 起**同样**拒绝（射程扩大，非回归）",
                probed,
            )


def test_the_known_set_is_exported_from_the_signature_not_hand_written() -> None:
    """EC-03 ②（**判关系**）：已知集**从匹配路由的签名导出** —— 加参数自动跟着走。

    受判面 = **导出函数 + 应用装配**：① 导出函数在树且被 app 依赖引用；
    ② 它不是「手写常量」形态（模块里**不**出现已知参数的字面量清单，如 `"limit"`）。
    """
    import inspect
    from pathlib import Path

    from services.api import app as app_module

    root = Path(__file__).resolve().parents[2]
    guard_source = (root / "services" / "api" / "query_param_guard.py").read_text(encoding="utf-8")
    for literal in ('"limit"', "'limit'", '"scope"', '"horizon_days"'):
        assert literal not in guard_source, (
            "导出面**不得**手写已知参数（会漂：加参数忘改 ⇒ 正确请求被误拒）",
            literal,
        )
    assert "dependant" in guard_source and "query_params" in guard_source, (
        "已知集必须**从匹配路由的签名**读（`scope['route'].dependant.query_params`）"
    )
    assert "Depends(reject_unknown_query_params)" in inspect.getsource(app_module), (
        "应用级**构造期**依赖是生效的注册点（事后 append 不生效 —— 实测）"
    )


def test_the_guard_is_inert_for_non_read_methods() -> None:
    """EC-03 ③（反证臂）：**写面不受影响** —— 非 GET/HEAD 上导出面返回 `None`。

    与「未知参数」纪律的边界一致：写面的额外字段是 pydantic 的既有校验面
    （本 GOAL 明确不做）。
    """
    from starlette.requests import Request as StarletteRequest

    dependant = type("D", (), {"query_params": [type("F", (), {"alias": "alpha"})()]})()
    scope = {
        "type": "http",
        "method": "POST",
        "route": type("R", (), {"dependant": dependant})(),
        "path": "/x",
        "headers": [],
    }
    assert declared_query_params(StarletteRequest(scope)) is None, (
        "写面不该被本守卫覆盖（`None` = 不在射程内）"
    )


def test_the_export_helper_reads_the_matched_route_not_a_global() -> None:
    """EC-03 ④：导出面**随路由变化**（不是全局/固定集）—— 同一提取函数，两种路由两种读数。"""
    from starlette.requests import Request as StarletteRequest

    def scope_for(names: list[str]) -> Any:
        dependant = type(
            "D", (), {"query_params": [type("F", (), {"alias": n})() for n in names]}
        )()
        return {
            "type": "http",
            "method": "GET",
            "route": type("R", (), {"dependant": dependant})(),
            "path": "/x",
            "headers": [],
        }

    wide = declared_query_params(StarletteRequest(scope_for(["a", "b"])))
    narrow = declared_query_params(StarletteRequest(scope_for(["c"])))
    assert wide == frozenset({"a", "b"}), wide
    assert narrow == frozenset({"c"}), narrow
    assert wide != narrow, "导出面必须随**该路由**的签名变化（否则是手写清单的形态）"


def test_a_route_added_later_is_covered_without_editing_any_list() -> None:
    """EC-02 ⑦（**漂移自证**）：**事后注册**的新路由（带全新参数名）**自动**受纪律。

    这一条是「**不**手写清单」的**行为证据**（静态取证在 ⑥/EC-03②）：新路由**没有**任何
    人改过本组清单或守卫常量 ⇒ 若纪律靠手写清单，这里会 200（静默吞掉）。
    """
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient as TC

    from services.api.errors import register_error_handlers
    from services.api.query_param_guard import reject_unknown_query_params

    app = FastAPI(dependencies=[Depends(reject_unknown_query_params)])
    register_error_handlers(app)

    def brand_new_route(a_brand_new_param: str = "v") -> dict[str, str]:
        return {"ok": "1"}

    app.add_api_route("/brand-new", brand_new_route, methods=["GET"])
    with TC(app) as client:
        assert client.get("/brand-new?a_brand_new_param=x").status_code == 200
        typo = client.get("/brand-new?a_brand_new_para=x")
        assert typo.status_code == 422, ("新路由**自动**受纪律（不靠手写清单）", typo.text)
        assert "a_brand_new_para" in typo.json()["detail"], typo.json()
        assert "a_brand_new_param" in typo.json()["detail"], ("正文给出该路由的已知集", typo.json())


def test_the_judged_list_matches_every_declared_route_in_the_app() -> None:
    """EC-02 ⑥（**受判面非空且不窄**）：本组的清单 = app 里**全部**已声明路由。

    受判面 = **应用解析后的声明面**（`app.openapi()` 的 `parameters[in=query]`）：
    ① 本组清单的路径集合**等于**应用里已声明查询参数的 GET 路径集合（少一条 ⇒ 漏判；
    ② 若应用新增一条已声明路由而本清单没跟上 ⇒ **判红**（不是静默漏掉）。
    """
    spec = create_app(make_run_ready_deps()).openapi()
    declared_in_app = {
        path
        for path, ops in spec["paths"].items()
        if "get" in ops and any(p.get("in") == "query" for p in ops["get"].get("parameters", []))
    }

    # OpenAPI 用**路径模板**（`{project_id}` / `{run_id}`），本组用**具体值**
    # （`example-project` / `run-missing`）⇒ 归一化到同一形态再比（否则是
    # 「拿两种写法比」的假红）。
    def _template(path: str) -> str:
        return path.replace("example-project", "{project_id}").replace("run-missing", "{run_id}")

    judged = {_template(path) for path, _, _, _ in _DECLARED}
    assert judged == declared_in_app, (
        "受判面必须 = 应用里全部已声明路由（漏判即判红）",
        "本组缺:",
        sorted(declared_in_app - judged),
        "本组多:",
        sorted(judged - declared_in_app),
    )
    assert declared_in_app, "受判面为空 ⇒ 本组退化为空真"
