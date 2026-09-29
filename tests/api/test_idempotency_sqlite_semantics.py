"""GOAL-026 EC-01（AC-1 / AC-3）：**生产** SQLite 幂等存储上的写面语义与跨会话重放。

既有判据的缺口（建档实测，不是推测）：

- `tests/api/test_idempotency_ifmatch.py` 注入的是 `InMemoryIdempotencyStore`
  ⇒ **生产实现** `SqliteIdempotencyStore` 的 replay / conflict / 拒绝语义无人证；
- `tests/api/test_api_restart_recovery.py` 的跨重启重放只断言端点 id 与列表长度
  ⇒ **状态码 / 正文 / `ETag` 三件套跨会话相等**无人证。

本判据把这两件事打在**文件库 + 生产 store** 上。`IdempotencyMiddleware` 与
`Idempotency-Key` 的语义**零改动**（承 GOAL-019 判词：该面只加判据）。
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from httpx import Response

from adapters.sqlite.idempotency_store import SqliteIdempotencyStore
from services.api.app import create_app
from services.api.composition import ApiDeps
from tests.api.conftest import make_app_deps, make_endpoint_payload

#: 一条受判载荷（合成值；不含任何真实凭据）。
_PAYLOAD_HINT = "sqlite-face"


def _production_deps(tmp_path: Path) -> ApiDeps:
    """文件库装配 + **生产** `SqliteIdempotencyStore`（替换测试用的内存实现）。"""
    deps = make_app_deps(db_path=str(tmp_path / "control.db"))
    deps.idempotency = SqliteIdempotencyStore(db_path=str(tmp_path / "idempotency.db"))
    return deps


def _triple(response: Response) -> tuple[int, object, str | None]:
    """重放三件套：**状态码 + 正文（JSON）+ `ETag`**。"""
    return response.status_code, response.json(), response.headers.get("etag")


def _assert_etag_is_real(response: Response) -> None:
    """受判面非空（承 MEM-156）：三件套里的 `ETag` **必须真的在发**。

    否则「两次都是 None」会把一条空比较读成通过。
    """
    assert response.headers.get("etag"), "首次响应必须带非空 ETag（否则三件套比较退化为空真）"


def test_replay_on_production_store_returns_identical_triple(tmp_path: Path) -> None:
    """AC-1①：重放返回**同一结果**（状态码 + 正文 + `ETag` 逐字符相等）。"""
    payload = make_endpoint_payload()
    headers = {"Idempotency-Key": f"{_PAYLOAD_HINT}-replay-1"}
    with TestClient(create_app(_production_deps(tmp_path))) as client:
        first = client.post("/llm-endpoints", json=payload, headers=headers)
        replay = client.post("/llm-endpoints", json=payload, headers=headers)
        _assert_etag_is_real(first)
        assert first.status_code == 201
        assert _triple(replay) == _triple(first)
        # 不产生第二条业务事实（canonical 面另见 tests/e2e 的计数判据）。
        assert len(client.get("/llm-endpoints").json()) == 1


def test_same_key_with_different_payload_conflicts_on_production_store(tmp_path: Path) -> None:
    """AC-1②：同键**不同载荷** ⇒ 422，**不得**静默复用首答。"""
    payload = make_endpoint_payload()
    key = f"{_PAYLOAD_HINT}-conflict-1"
    with TestClient(create_app(_production_deps(tmp_path))) as client:
        assert (
            client.post(
                "/llm-endpoints", json=payload, headers={"Idempotency-Key": key}
            ).status_code
            == 201
        )
        changed = {**payload, "name": "changed-name"}
        conflict = client.post("/llm-endpoints", json=changed, headers={"Idempotency-Key": key})
        assert conflict.status_code == 422
        assert conflict.json()["title"] == "Idempotency-Key Reused"
        # 冲突**不得**被当成重放：没有第二条业务事实。
        assert len(client.get("/llm-endpoints").json()) == 1


def test_missing_key_is_rejected_on_production_store(tmp_path: Path) -> None:
    """AC-1③：无键 ⇒ 422，**不得**落库。"""
    with TestClient(create_app(_production_deps(tmp_path))) as client:
        rejected = client.post("/llm-endpoints", json=make_endpoint_payload())
        assert rejected.status_code == 422
        assert rejected.json()["title"] == "Idempotency-Key Required"
        assert client.get("/llm-endpoints").json() == []


def test_replay_across_new_sessions_returns_identical_triple(tmp_path: Path) -> None:
    """AC-3：**新的 store 实例 + 新的应用 + 新的客户端**（同一文件）⇒ 三件套再次相等。"""
    payload = make_endpoint_payload()
    headers = {"Idempotency-Key": f"{_PAYLOAD_HINT}-cross-session-1"}
    with TestClient(create_app(_production_deps(tmp_path))) as first_client:
        first = first_client.post("/llm-endpoints", json=payload, headers=headers)
        _assert_etag_is_real(first)
        assert first.status_code == 201
    # 第一个会话已关闭：下面是一个**全新的 store 实例 + 全新的应用**，只共享文件。
    with TestClient(create_app(_production_deps(tmp_path))) as second_client:
        replay = second_client.post("/llm-endpoints", json=payload, headers=headers)
        assert _triple(replay) == _triple(first)
        assert len(second_client.get("/llm-endpoints").json()) == 1
