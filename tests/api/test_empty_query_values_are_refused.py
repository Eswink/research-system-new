"""GOAL-20261014-075（序 43）：**声明参数的空值形态不再被静默当成筛选值** —— EC-02 / EC-03。

**为什么单列**：序 37/40/41/42 接通「未知 / 未声明 / 写面 / 重复」四面，而**实测**：
**已声明参数给空值**时**各路由不一致** —— `?scope=` / `?proposed_by=` / `?state=`（**str 型**）
⇒ **200 且静默筛成 0 条**（调用方读作「没有匹配」），而 `?limit=` / `?at=`（**校验型**）⇒ 422
⇒ **同一形态两种行为**（分界 = 类型面）。

**判的是什么**：① 已声明参数空值 ⇒ **422 + 点名该参数 + 明写「不接受空值」**
（与「未知」「重复」**三分辨**）；② **多个空值逐个点名**；③ **缺省（不传）形态逐字不变**；
④ **已声明值**的语义不变（`?scope=project` 等）；⑤ **`list` 声明**不在射程；⑥ 另两臂不回归。
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from adapters.fakes.memory_store import FakeMemoryStore
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal
from services.api.app import create_app
from tests.api.run_fixtures import make_run_ready_deps


def _deps_with_one_memory() -> Any:
    """一条记忆 —— 让「空值筛成 0 条」可观测（空数据集上两种行为不可分）。"""
    deps = make_run_ready_deps()
    store = FakeMemoryStore(allowed_sources=("g075:probe",))
    store.allow_source("g075:probe")
    deps.memory = store
    store.commit(
        MemoryWriteProposal(
            id="m-g075",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="判据记录",
            provenance="g075:probe",
            confidence=0.9,
        )
    )
    return deps


def _client() -> TestClient:
    return TestClient(create_app(_deps_with_one_memory()))


def test_an_empty_value_on_a_declared_param_is_named() -> None:
    """EC-02 ①：空值 ⇒ **422 + 点名 + 明写「不接受空值」**（改动前 200 静默筛 0 条）。"""
    with _client() as client:
        response = client.get("/projects/example-project/memory?scope=")
        assert response.status_code == 422, response.text
        detail = response.json()["detail"]
        assert "scope" in detail, detail
        assert "does not accept an empty value" in detail, (
            "措辞要与「未知」「重复」**三分辨**",
            detail,
        )
        other = client.get("/models?endpoint_id=")
        assert other.status_code == 422, other.text
        assert "endpoint_id" in other.json()["detail"], other.json()


def test_several_empty_values_are_each_named() -> None:
    """EC-02 ②：**多个空值逐个点名**。"""
    with _client() as client:
        detail = client.get("/projects/example-project/memory?scope=&proposed_by=").json()["detail"]
        assert "scope" in detail and "proposed_by" in detail, detail


def test_the_default_and_known_value_forms_are_verbatim() -> None:
    """EC-02 ③：**缺省（不传）与已声明值逐字不变**（EC-01 基线）。"""
    with _client() as client:
        base = client.get("/projects/example-project/memory")
        assert base.status_code == 200, base.text
        assert sorted(base.json()) == ["records", "scope_note"], sorted(base.json())
        assert len(base.json()["records"]) == 1, base.json()
        scoped = client.get("/projects/example-project/memory?scope=project")
        assert scoped.status_code == 200, scoped.text
        assert "filtered_out" in scoped.json(), scoped.json()


def test_the_list_declared_param_is_not_in_this_scope() -> None:
    """EC-02 ④（**射程边界**）：`list` 声明的参数不在空值臂射程（与重复臂同一边界）。"""
    with _client() as client:
        response = client.get("/evaluations/trend?expected_digests=")
        assert response.status_code != 422 or "empty" not in response.text, (
            "`list` 声明不受空值臂（射程边界）",
            response.status_code,
            response.text[:200],
        )


def test_the_three_arms_are_distinguishable() -> None:
    """EC-03 ①（**三分辨**）：未知 / 重复 / 空值三臂的措辞各不相同（读者能分辨）。"""
    with _client() as client:
        unknown = client.get("/notifications?limt=5").json()["detail"]
        repeated = client.get("/notifications?limit=1&limit=2").json()["detail"]
        blank = client.get("/notifications?limit=").json()["detail"]
        assert "known:" in unknown, unknown
        assert "exactly one value" in repeated, repeated
        assert "does not accept an empty value" in blank, blank
        assert len({unknown, repeated, blank}) == 3, (unknown, repeated, blank)


def test_the_prior_faces_do_not_regress() -> None:
    """EC-03 ②：**前四面不回归**（未声明 / 写面 / 重复照旧）。"""
    with _client() as client:
        undeclared = client.get("/projects?zz=1")
        assert undeclared.status_code == 422, undeclared.text
        assert "accepts no query parameters" in undeclared.json()["detail"], undeclared.json()
        write = client.post(
            "/projects?zz=1",
            json={"name": "probe-075"},
            headers={"Idempotency-Key": "g075-write-1"},
        )
        assert write.status_code == 422, write.text
        repeated = client.get("/notifications?limit=1&limit=2")
        assert repeated.status_code == 422, repeated.text
        assert "exactly one value" in repeated.json()["detail"], repeated.json()
