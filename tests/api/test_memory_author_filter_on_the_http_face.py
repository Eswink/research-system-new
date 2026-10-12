"""GOAL-20261013-067（序 35）：**HTTP 读面的作者筛选不再被静默忽略** —— EC-02 / EC-03 的判据。

**为什么单列**：本轮的靶子是 **HTTP 读面**（序 34 只做到查询面 + 编排消费面）；
与序 17 的 `?scope=` 判据（`tests/adapters/canonical/test_memory_read_dispositions.py`
与 `tests/api/test_memory_api.py` 的既有部分）**同族** —— 那一轮立了「按范围筛并披露」的形态，
本组判**第二个维度**（作者）**与它同形**。

**判的是什么**：序 34 让作者在查询面选得着，而 HTTP 读面**把 `?proposed_by=` 吞掉**
（**实跑**：200 + 全量 + 无披露键）⇒ 调用方**以为筛过了**。
本轮让该参数与 `?scope=` **同形**：传 ⇒ 只出那一位的 + **披露两键**；**缺省逐字不变**。
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal
from services.api.app import create_app
from tests.api.run_fixtures import make_run_ready_deps

_PROJECT = "example-project"
_PATH = f"/projects/{_PROJECT}/memory"


def _seeded_deps() -> Any:
    """两条不同作者的记忆（走 store 落 canonical）—— 受控装配（判据只读面）。

    与 `tests/api/test_memory_api.py` 的既有手法**同形**：**显式注入**一个具体的
    `FakeMemoryStore`（不是 `deps.memory` 的 `Any | None` ⇒ 顺带守住严格 mypy）。
    """
    from adapters.fakes.memory_store import FakeMemoryStore

    deps = make_run_ready_deps()
    store = FakeMemoryStore(allowed_sources=("probe:author",))
    store.allow_source("probe:author")
    deps.memory = store
    for memory_id, author in (("m-x", "agent:x"), ("m-y", "agent:y")):
        store.commit(
            MemoryWriteProposal(
                id=memory_id,
                tier=MemoryTier.PROJECT,
                kind=MemoryType.FACT,
                content=f"内容 {memory_id}",
                provenance="probe:author",
                confidence=0.9,
                proposed_by=author,
            )
        )
    return deps


def _ids(payload: dict[str, Any]) -> list[str]:
    return sorted(str(r.get("memory_id") or r.get("id")) for r in payload["records"])


def test_the_author_filter_selects_and_discloses() -> None:
    """EC-02 ①：**传作者 ⇒ 只出那一位的 + 披露两键**（改动前该参数被静默忽略）。"""
    with TestClient(create_app(_seeded_deps())) as client:
        body = client.get(f"{_PATH}?proposed_by=agent:x").json()
        assert _ids(body) == ["m-x"], body
        assert body["proposed_by"] == "agent:x", body
        assert body["filtered_out"] == 1, ("必须点名筛掉几条", body)


def test_the_default_payload_is_verbatim() -> None:
    """EC-02 ②：**不传参数** ⇒ 载荷与改动前**逐字相同**（键一个不多）。"""
    with TestClient(create_app(_seeded_deps())) as client:
        body = client.get(_PATH).json()
        assert sorted(body) == ["records", "scope_note"], body
        assert _ids(body) == ["m-x", "m-y"], body


def test_an_unknown_author_is_empty_not_everything() -> None:
    """EC-02 ③：**未知作者 ⇒ 空集**（**不猜**：**不**把未知当「全选」）。"""
    with TestClient(create_app(_seeded_deps())) as client:
        body = client.get(f"{_PATH}?proposed_by=agent:nowhere").json()
        assert body["records"] == [], body
        assert body["filtered_out"] == 2, ("筛掉的是全部", body)


def test_the_scope_disclosure_is_untouched() -> None:
    """EC-02 ④（反证臂）：**`?scope=` 的既有语义一字不动**（序 17 立的形态）。"""
    with TestClient(create_app(_seeded_deps())) as client:
        body = client.get(f"{_PATH}?scope=project").json()
        assert body["scope"] == "project", body
        assert body["filtered_out"] == 0, ("两条都在 project 范围", body)
        assert "proposed_by" not in body, ("`?scope=` 那一支不追加作者键", sorted(body))


def test_the_author_filter_composes_with_the_scope_position() -> None:
    """EC-02 ⑤：两维**可并存**（作者维优先——载荷如实报各自的值，不混成一个）。"""
    with TestClient(create_app(_seeded_deps())) as client:
        body = client.get(f"{_PATH}?scope=project&proposed_by=agent:x").json()
        assert _ids(body) == ["m-x"], body
        assert body["proposed_by"] == "agent:x", body


def test_the_three_shapes_are_distinguishable() -> None:
    """EC-03 ①：**三个形态各自的键集**（缺省 / 按范围 / 按作者）—— 逐条点名。

    受判面 = **三个形态**：少一个 ⇒ FastAPI 会把载荷**收窄**回缺省形态、**静默抹掉**该维的
    披露键（本轮**实测**踩到过：并集里漏了新形态 ⇒ `filtered_out` 读不出来）。
    """
    with TestClient(create_app(_seeded_deps())) as client:
        default = sorted(client.get(_PATH).json())
        scoped = sorted(client.get(f"{_PATH}?scope=project").json())
        authored = sorted(client.get(f"{_PATH}?proposed_by=agent:x").json())
    assert default == ["records", "scope_note"], default
    assert scoped == ["filtered_out", "records", "scope", "scope_note"], scoped
    assert authored == ["filtered_out", "proposed_by", "records", "scope_note"], authored


def test_the_snapshot_carries_the_authored_shape() -> None:
    """EC-03 ②：**OpenAPI 快照**含新形态（动 DTO ⇒ 同轮同步）。"""
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    snapshot = (root / "docs" / "api" / "openapi.m13.json").read_text(encoding="utf-8")
    assert "MemoryAuthoredListViewDto" in snapshot, "快照必须含作者形态"


def test_the_write_face_is_untouched() -> None:
    """EC-02 反证臂：**写面不受影响**（筛是读面的事）。

    与 `tests/api/test_memory_api.py` 的既有手法**同形**：来源**先注册**再直写 store
    （deny-by-default 的门链 —— 未注册 ⇒ 422 点名拒绝；本判据钉的是**读面的筛**本身）。
    """
    from adapters.fakes.memory_store import FakeMemoryStore

    deps = make_run_ready_deps()
    store = FakeMemoryStore(allowed_sources=("test:goal067",))
    store.allow_source("test:goal067")
    deps.memory = store
    store.commit(
        MemoryWriteProposal(
            id="m-writer",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="写一条带作者的",
            provenance="test:goal067",
            confidence=0.9,
            proposed_by="agent:writer",
        )
    )
    with TestClient(create_app(deps)) as client:
        body = client.get(f"{_PATH}?proposed_by=agent:writer").json()
        assert _ids(body) == ["m-writer"], body
        assert body["filtered_out"] == 0, body
