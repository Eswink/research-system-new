"""GOAL-010 EC-04：运行时指纹四要素在产品路径上的读面（含按压）。

这一条判的是**读面**：`GET /runs/{id}` 的 `execution.runtime_fingerprint` 能不能取到
「返回 model 名 / 端点头 / probe 版本 / 兼容性结论」，取不到时**有没有点名缺哪几项**。

**成对**（AC-3 的先红后绿）：同一份协议、同一套装配，只改**执行体有没有观测到 model 名**：

- 有观测 ⇒ `source=RUN_OBSERVATION`，单值槽位 = 观测到的那个名字，端点头与 probe 版本非空，
  结论 `REPEATABLE_CONFIGURATION`（provider 侧的 `system_fingerprint` 缺失**不**降级、
  只点名）；
- 无观测 ⇒ `source=FROZEN_PLACEHOLDER`，结论 `NOT_VERIFIED` 且四要素**逐项点名**。

两向都断言，判据因此不可能是常量。**不声称**：这条链路是**离线受控执行体**驱动的
（Fake 报告 provider 侧名字），它判的是**接线**；「真实 provider 真的报告了什么」由
live 分支取样（PLAN-130 WP3），不由本文件声称。
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, cast

from fastapi.testclient import TestClient

from adapters.fakes.agent_runtime import FakeAgentRuntime
from services.api.app import create_app
from services.api.demo import demo_session_output
from services.api.runtime_support import resolve_runtime_selection
from services.api.settings import ApiSettings
from tests.api.conftest import make_app_deps

#: GOAL-010 EC-03 的真实协议（本判据只关心它的执行目标与合约，不重复判身份）。
_PROTOCOL = "real_research_task_v1.yaml"
#: provider 侧**报告过的** model 名（与请求里写的 model id 无关——那条由别的判据判）。
_OBSERVED = "relay-model-alpha"
#: 冻结占位**不带**指纹值 ⇒ 读面必须点名的四要素（判据里的字面量，不 import 被测实现；
#: 顺序按读面的既定排序）。
_ELEMENTS = [
    "endpoint_config_digest",
    "probe_suite_digest",
    "returned_model_identifier",
    "system_fingerprint",
]


def _runtime(observed: tuple[str, ...]) -> FakeAgentRuntime:
    """受控执行体：会话结局与交付物固定，**只改**它报告的 model 名。"""
    return FakeAgentRuntime(
        structured_output=demo_session_output(), observed_model_identifiers=observed
    )


@contextmanager
def _run(observed: tuple[str, ...]) -> Iterator[tuple[dict[str, Any], list[dict[str, Any]]]]:
    """在产品路径（默认装配）上起一次 run，回读详情与事件链。

    `runtime_selection` 显式给上：**两条生产组合根都会填它**（没有选择面的装配里
    指纹槽位是「未声明」的 `{}`，那种装配本来就产不出占位，也就无所谓「合并」）。
    """
    deps = make_app_deps(runtime=_runtime(observed))
    deps.runtime_selection = resolve_runtime_selection(ApiSettings())
    # 受控凭据面：本判据只关心指纹，凭据是否存在是别的判据的事（`register` 不在 Port 上）。
    cast(Any, deps.credentials).register("LLM_MAIN_KEY", "sk-demo-key-0001")
    with TestClient(create_app(deps)) as client:
        started = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": _PROTOCOL},
            headers={"Idempotency-Key": f"fingerprint-{uuid.uuid4()}"},
        )
        assert started.status_code == 200, started.text
        run_id = started.json()["id"]
        detail = cast(dict[str, Any], client.get(f"/runs/{run_id}").json())
        events = cast(list[dict[str, Any]], client.get(f"/runs/{run_id}/events").json())
    yield detail, events


def _fingerprint(detail: dict[str, Any]) -> dict[str, Any]:
    execution = detail["execution"]
    assert execution is not None, "run 已冻结 ⇒ 执行体读面必须在场"
    fingerprint = execution["runtime_fingerprint"]
    assert fingerprint is not None, "冻结快照带指纹槽位 ⇒ 读面必须给出这条状态"
    return cast(dict[str, Any], fingerprint)


def test_the_observed_fingerprint_is_readable_and_named_by_its_source() -> None:
    """有观测：四要素里的三项取到实测值，结论 `REPEATABLE_CONFIGURATION`（**绿**）。"""
    with _run((_OBSERVED,)) as (detail, _events):
        assert detail["state"] == "SUCCEEDED", detail
        fingerprint = _fingerprint(detail)
        assert fingerprint["source"] == "RUN_OBSERVATION"
        assert fingerprint["status"] == "REPEATABLE_CONFIGURATION"
        assert fingerprint["returned_model_identifier"] == _OBSERVED
        assert fingerprint["observed_model_identifiers"] == [_OBSERVED]
        assert fingerprint["endpoint_config_digest"], fingerprint
        assert fingerprint["probe_suite_digest"], fingerprint
        # provider 是否给 system_fingerprint 不取决于我们：缺失只**点名**，不降级结论。
        assert "system_fingerprint" in fingerprint["missing_fields"], fingerprint
        assert "returned_model_identifier" not in fingerprint["missing_fields"], fingerprint


def test_without_any_observation_the_read_face_names_the_four_gaps() -> None:
    """无观测：读面**逐项点名**缺哪四要素并报 `NOT_VERIFIED`（**红**／降级）。"""
    with _run(()) as (detail, _events):
        assert detail["state"] == "SUCCEEDED", "run 照样成功——指纹缺项不是 run 的失败"
        fingerprint = _fingerprint(detail)
        assert fingerprint["source"] == "FROZEN_PLACEHOLDER"
        assert fingerprint["status"] == "NOT_VERIFIED"
        assert fingerprint["missing_fields"] == _ELEMENTS
        assert fingerprint["returned_model_identifier"] is None
        assert fingerprint["observed_model_identifiers"] == []


def test_the_frozen_placeholder_is_never_rewritten_by_the_measured_fact() -> None:
    """冻结即不可变：实测记录**不**改写冻结 payload，读面只是合并呈现两份事实。"""
    with _run((_OBSERVED,)) as (_detail, events):
        frozen = [event for event in events if event["type"] == "manifest.frozen"]
        assert frozen, "run 必须冻结过 manifest"
        slot = frozen[0]["payload"]["runtime_fingerprint"]
        assert slot["status"] == "NOT_VERIFIED", slot
        assert "returned_model_identifier" not in slot, slot
        assert [event for event in events if event["type"] == "model.probed"], (
            "实测事实必须以 canonical 事件落链，而不是只活在内存里"
        )
