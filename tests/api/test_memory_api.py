"""Memory 控制面测试（PLAN-20260910-037 WP-F）。

503（SQLite 无 store）、§8 门链全阶段可分类 422、PG canonical 语义经
FakeMemoryStore 注入验证、DELETE lifecycle + 幂等键要求。
"""

from __future__ import annotations

from typing import Any, cast

from fastapi.testclient import TestClient

from adapters.fakes.memory_store import FakeMemoryStore
from packages.application.ports.errors import InvalidInputError
from packages.domain.enums import TrustLabel
from packages.domain.evidence import SourceRecord

#: 读面判定用的**显式时点**（读面不读挂钟 ⇒ 判定可复现）。
_NOW = "2026-10-11T00:00:00+00:00"


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _wire(client: TestClient) -> FakeMemoryStore:
    store = FakeMemoryStore()
    deps = _deps(client)
    deps.memory = store
    deps.ledger.register_source(
        SourceRecord(
            origin="paper://memory-wpf",
            content_digest="sha256:" + "a" * 64,
            trust_label=TrustLabel.VERIFIED_SOURCE,
        )
    )
    return store


def _proposal(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "tier": "SESSION",
        "kind": "FACT",
        "content": "observed sorting baseline is O(n log n)",
        "provenance": "paper://memory-wpf",
        "confidence": 0.8,
    }
    base.update(overrides)
    return base


def _post(client: TestClient, key: str, body: dict[str, object]) -> Any:
    return client.post("/memory/proposals", json=body, headers={"Idempotency-Key": f"mem-{key}"})


def test_sqlite_dev_path_memory_store_missing_is_503(client: TestClient) -> None:
    assert _deps(client).memory is None
    assert client.get("/projects/example-project/memory").status_code == 503
    assert _post(client, "no-store", _proposal()).status_code == 503


def test_proposal_commits_through_full_gate(client: TestClient) -> None:
    _wire(client)
    created = _post(client, "ok", _proposal())
    assert created.status_code == 201, created.text
    record = created.json()["record"]
    assert record["tier"] == "SESSION"
    assert record["active"] is True
    listed = client.get("/projects/example-project/memory")
    assert listed.status_code == 200
    assert [row["id"] for row in listed.json()["records"]] == [record["id"]]


def test_unregistered_provenance_rejected_422(client: TestClient) -> None:
    _wire(client)
    rejected = _post(client, "badprov", _proposal(provenance="paper://not-registered"))
    assert rejected.status_code == 422
    assert "provenance" in rejected.text


def test_blank_content_rejected_by_schema_stage(client: TestClient) -> None:
    _wire(client)
    rejected = _post(client, "blank", _proposal(content="   "))
    assert rejected.status_code == 422
    assert "schema" in rejected.json()["title"] or "blank" in rejected.text


def test_project_tier_requires_curator(client: TestClient) -> None:
    _wire(client)
    denied = _post(client, "curator-0", _proposal(tier="PROJECT", content="team decision"))
    assert denied.status_code == 422
    granted = _post(
        client,
        "curator-1",
        _proposal(tier="PROJECT", content="team decision", curator_approved=True),
    )
    assert granted.status_code == 201, granted.text


def test_delete_lifecycle_and_idempotency_key(client: TestClient) -> None:
    store = _wire(client)
    record_id = _post(client, "del", _proposal()).json()["record"]["id"]
    no_key = client.delete(f"/memory/{record_id}")
    assert no_key.status_code == 422  # Idempotency-Key required
    missing = client.delete("/memory/ghost", headers={"Idempotency-Key": "k-ghost"})
    assert missing.status_code == 404
    removed = client.delete(f"/memory/{record_id}", headers={"Idempotency-Key": "k-1"})
    assert removed.status_code == 204
    try:
        store.get(record_id)
    except InvalidInputError:
        pass
    else:
        raise AssertionError("deleted memory id must be unknown to the store")
    listed = client.get("/projects/example-project/memory")
    assert listed.json()["records"] == []


# --- GOAL-20261008-039 EC-02 / EC-04：读面披露 + 按时点判定 -------------------------


def test_the_list_face_discloses_the_scope(client: TestClient) -> None:
    """EC-02：列表读面逐条披露 `scope`（此前该字段根本不落库）。"""
    _wire(client)
    created = client.post(
        "/memory/proposals",
        json=_proposal(provenance="paper://memory-wpf"),
        headers={"Idempotency-Key": "mem-scope-1"},
    )
    assert created.status_code == 201, created.text
    rows = client.get("/projects/example-project/memory").json()["records"]
    assert rows and rows[0]["scope"] == "project", rows


def test_the_list_face_can_be_filtered_by_scope(client: TestClient) -> None:
    """GOAL-20261010-049 EC-03：HTTP 读面按 `scope` 筛（**可选**；缺省逐字不变）。

    三条臂：① 缺省 ⇒ 载荷**没有** `scope` / `filtered_out` 两键（既有读者看到的不变）；
    ② 传 `scope` ⇒ 只回该范围且**点名筛掉多少条**；③ 未知范围 ⇒ **422 点名**（不静默空集）。
    """
    store = _wire(client)
    _commit_with_scope(store, "mem-proj", "project")
    _commit_with_scope(store, "mem-team", "team")

    default = client.get("/projects/example-project/memory")
    assert default.status_code == 200, default.text
    body = default.json()
    assert len(body["records"]) == 2, body
    assert "scope" not in body and "filtered_out" not in body, (
        "缺省不得凭空多出键",
        sorted(body),
    )

    filtered = client.get("/projects/example-project/memory?scope=team")
    assert filtered.status_code == 200, filtered.text
    body = filtered.json()
    assert [row["id"] for row in body["records"]] == ["mem-team"], body
    assert body["scope"] == "team" and body["filtered_out"] == 1, body

    unknown = client.get("/projects/example-project/memory?scope=nope")
    assert unknown.status_code == 200, (
        "读面按范围筛**不**校验范围（那是编排面 memory.read 的职责）—— 未知范围返回空集",
        unknown.text,
    )
    assert unknown.json()["filtered_out"] == 2, unknown.json()


def _commit_with_scope(store: FakeMemoryStore, memory_id: str, scope: str) -> None:
    """直写一条指定范围的记录（钉的是**读面的筛**本身，不经提案面）。"""
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryWriteProposal

    store.allow_source("test:goal049")
    store.commit(
        MemoryWriteProposal(
            id=memory_id,
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content=f"内容 {memory_id}",
            provenance="test:goal049",
            confidence=0.9,
            scope=scope,
        )
    )


def _commit_expiring(store: Any, memory_id: str) -> None:
    """直写一条带明确到期时刻的记录（钉的是**判定面**本身，不经提案面）。"""
    from datetime import datetime, timezone

    from packages.domain.core import Timestamp
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryWriteProposal

    store.allow_source("paper://memory-wpf")
    store.commit(
        MemoryWriteProposal(
            id=memory_id,
            tier=MemoryTier.SESSION,
            kind=MemoryType.FACT,
            content="c",
            provenance="paper://memory-wpf",
            confidence=0.5,
            expires_at=Timestamp(datetime(2027, 1, 1, tzinfo=timezone.utc)),
        )
    )


def test_the_validity_face_judges_at_the_time_the_caller_gives(client: TestClient) -> None:
    """EC-04：`?at=` 显式时点 ⇒ 逐条三态判定；**不给时点的列表读面不猜**（`validity` 为 None）。"""
    store = _wire(client)
    with_expiry = _proposal(provenance="paper://memory-wpf")
    created = client.post(
        "/memory/proposals",
        json=with_expiry,
        headers={"Idempotency-Key": "mem-validity-1"},
    )
    assert created.status_code == 201, created.text
    memory_id = str(created.json()["record"]["id"])
    _commit_expiring(store, "memory-validity-explicit")
    before = client.get(
        "/projects/example-project/memory/validity", params={"at": "2026-06-01T00:00:00+00:00"}
    )
    assert before.status_code == 200, before.text
    payload = before.json()
    assert payload["at"].startswith("2026-06-01")
    assert {row["id"] for row in payload["records"]} >= {memory_id, "memory-validity-explicit"}
    by_id = {row["id"]: row for row in payload["records"]}
    assert by_id["memory-validity-explicit"]["validity"] is None, "未到期 ⇒ 不报"
    after = client.get(
        "/projects/example-project/memory/validity", params={"at": "2028-01-01T00:00:00+00:00"}
    ).json()
    by_id_after = {row["id"]: row for row in after["records"]}
    assert by_id_after["memory-validity-explicit"]["validity"] == "EXPIRED", "到期 ⇒ 必报"
    # **未声明时效的记录不被误报**（缺席不猜）。
    assert by_id_after[memory_id]["validity"] is None, (
        "未声明时效不得被误报（反证③）",
        by_id_after[memory_id],
    )
    # 不给时点的**列表**读面：`validity` 不填（未判定，不猜）。
    listed = client.get("/projects/example-project/memory").json()["records"]
    assert all(row["validity"] is None for row in listed)


def test_the_validity_face_refuses_a_bad_timestamp(client: TestClient) -> None:
    """边界：非法时点 ⇒ 422（点名，不静默按当前时间兜底）。"""
    _wire(client)
    bad = client.get("/projects/example-project/memory/validity", params={"at": "not-a-time"})
    assert bad.status_code == 422, bad.text


# --- GOAL-20261011-052：**两个读面在同一份事实上给出一致的可判定性** -----------------------


def test_the_http_face_carries_the_four_facts_the_orchestration_face_has(
    client: TestClient,
) -> None:
    """EC-02：HTTP 读面补齐**四样**（冲突 / 反向取代 / 处置 / 理由）—— **附加**，既有键不变。

    此前序 10/17/18/19 把**编排消费面**的读面做成了十三键，而 HTTP 面**这四样一样没有**
    ⇒ 同一份 canonical 事实，**一条读路径已可判定、另一条看不见**。本条钉住「补齐」。
    """
    store = _wire(client)
    _commit_with_scope(store, "m-clean", "project")
    _commit_conflicting(store, "m-conf", ["m-elsewhere"])
    rows = client.get("/projects/example-project/memory").json()["records"]
    by_id = {str(row["id"]): row for row in rows}

    for field in ("contradictions", "superseded_by", "disposition", "reason"):
        assert field in by_id["m-clean"], (
            "四样必须都在场（缺：%s）" % field,
            sorted(by_id["m-clean"]),
        )
    # **既有 13 字段一个不改名、不改语义**（逐条点名；剔除新增的四样后应与改动前的键集相等）
    legacy = sorted(
        set(by_id["m-clean"]) - {"contradictions", "superseded_by", "disposition", "reason"}
    )
    assert legacy == [
        "active",
        "confidence",
        "content",
        "expires_at",
        "id",
        "kind",
        "provenance",
        "review_after",
        "scope",
        "supersedes",
        "tier",
        "valid_from",
        "validity",
    ], ("既有字段集必须逐字不变", legacy)


def test_the_two_faces_agree_on_the_same_records(client: TestClient) -> None:
    """EC-03：**两处对同一记录给同值**（冲突 / 反向取代 / 处置 / 理由**逐项相等**）。

    **同源**是这条能成立的原因：HTTP 面**直接调**编排面那两个纯函数
    （`disposition_of` / `_reason`）+ 同一反向链接助手（`superseded_by_index`），
    **不**在路由里重写第二套判定。
    """
    from adapters.canonical.memory_read import memory_read

    store = _wire(client)
    # 复合形态：`m-old` **既被取代、又带冲突** —— 一次写好（同一 id 不得提交两次）。
    _commit_conflicting(store, "m-old", ["m-elsewhere"])
    _commit_superseding(store, "m-new", "m-old")
    rows = client.get("/projects/example-project/memory").json()["records"]
    http = {str(row["id"]): row for row in rows}
    raw = memory_read(store, {"now": _NOW})["memories"]
    assert isinstance(raw, list), raw
    orch = {str(row["memory_id"]): row for row in raw}
    for rid in ("m-old", "m-new"):
        assert http[rid]["disposition"] == orch[rid]["disposition"], rid
        assert http[rid]["reason"] == orch[rid]["reason"], rid
        assert list(http[rid]["contradictions"]) == list(orch[rid]["contradictions"]), rid
        assert list(http[rid]["superseded_by"]) == list(orch[rid]["superseded_by"]), rid
    assert http["m-old"]["superseded_by"] == ["m-new"], (
        "反向链接必须在 HTTP 面也看得见（序 18 只在编排面成立）",
        http["m-old"],
    )


def test_the_http_face_still_does_not_guess_validity(client: TestClient) -> None:
    """EC-02 的**反证臂**：不给时点 ⇒ `validity` **仍为 `None`**（**不猜** —— 逐字保持）。

    **受判面必须是「有声明时效」的记录**（本用例初版用了一条**没有任何时效声明**的记录 ⇒
    两种行为都返回 `None` ⇒ 该断言**区分不了「不猜」与「拿挂钟猜」**，按压 N-4 因此**假绿**
    —— 由反证脚本的**基线门 + 按压门**当场报出）。故这里用一条**已到复核期**的记录：
    若读面拿挂钟去猜，它会立刻报 `REVIEW_DUE`（而正确行为是 `None` = **未判定**）。
    """
    store = _wire(client)
    _commit_review_due(store, "m-due")
    row = client.get("/projects/example-project/memory").json()["records"][0]
    assert row["validity"] is None, (
        "不给时点不得猜时效（这条记录**已到**复核期 ⇒ 猜的话会报 REVIEW_DUE）",
        row,
    )


def _commit_review_due(store: FakeMemoryStore, memory_id: str) -> None:
    """直写一条**复核期已到**的记录（「不猜时效」这条判据的受判面必须**有时效声明**）。"""
    from datetime import datetime, timezone

    from packages.domain.core import Timestamp
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryWriteProposal

    store.allow_source("test:goal052")
    store.commit(
        MemoryWriteProposal(
            id=memory_id,
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content=f"内容 {memory_id}",
            provenance="test:goal052",
            confidence=0.9,
            scope="project",
            review_after=Timestamp(datetime(2020, 1, 1, tzinfo=timezone.utc)),
        )
    )


def _commit_conflicting(store: FakeMemoryStore, memory_id: str, conflicts: list[str]) -> None:
    """直写一条**声明了冲突**的记录（钉的是**读面**本身，不经提案面）。"""
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryWriteProposal

    store.allow_source("test:goal052")
    store.commit(
        MemoryWriteProposal(
            id=memory_id,
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content=f"内容 {memory_id}",
            provenance="test:goal052",
            confidence=0.9,
            scope="project",
            contradictions=list(conflicts),
        )
    )


def _commit_superseding(store: FakeMemoryStore, memory_id: str, old_id: str) -> None:
    """直写一条**取代了旧记录**的新记录（反向链接的靶子）。"""
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryWriteProposal

    store.allow_source("test:goal052")
    store.commit(
        MemoryWriteProposal(
            id=memory_id,
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content=f"内容 {memory_id}",
            provenance="test:goal052",
            confidence=0.9,
            scope="project",
            supersedes=[old_id],
        )
    )
