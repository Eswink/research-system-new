"""GOAL-20261019-089 EC-02：**研究方向进 canonical，并且真的进会话提示词**。

**判什么**（逐条可证伪）：

1. **域字段**：`ProjectDefinition.direction` 可选、缺省 `None`；空串/超长 ⇒ 点名拒绝；
   `with_direction()` 与 `renamed()` **互不影响**（改方向不改名、改名不丢方向）。
2. **落库往返**：SQLite 编码/解码保留方向；**旧行**（本轮之前写入、没有该键）读回 `None`
   （不是 `""` —— 「未声明」与「空」必须分得开）。
3. **两端点**：`POST /projects` 可带方向；`PATCH /projects/{id}` 三态（不出现 = 不动 /
   `null` = 清除 / 字符串 = 声明）；`PUT /projects/{id}/direction` **只**改方向。
4. **进提示词**：`compose_prompt(direction=...)` 产出带标题的那一段；**未声明 ⇒ 逐字**
   返回 purpose（零回归）；它排在**前序知识与检索摘录之前**（顺序是契约）。
5. **`name` 不被占用**：方向只出现在 `direction` 字段上 —— 创建/更新带方向时
   `name` 逐字不变（「方向塞进 name」在结构上做不到）。
"""

from __future__ import annotations

import json
from typing import Any, cast

from fastapi.testclient import TestClient

from adapters.sqlite.project_store import SqliteProjectStore
from packages.application.run_orchestration.retrieval_prompt import (
    DIRECTION_SECTION_TITLE,
    PRIOR_SECTION_TITLE,
    PROMPT_SECTION_TITLE,
    compose_prompt,
)
from packages.domain.core import Timestamp
from packages.domain.projects import (
    MAX_PROJECT_DIRECTION_LENGTH,
    ProjectDefinition,
    ProjectStatus,
)


def _project(**overrides: Any) -> ProjectDefinition:
    values: dict[str, Any] = {
        "id": "p-1",
        "name": "Example",
        "status": ProjectStatus.ACTIVE,
        "created_at": Timestamp.now(),
        "updated_at": Timestamp.now(),
    }
    values.update(overrides)
    return ProjectDefinition(**values)


def _idem() -> dict[str, str]:
    import uuid

    return {"Idempotency-Key": f"goal089-{uuid.uuid4().hex}"}


# ---------------------------------------------------------------- (1) 域字段


def test_direction_defaults_to_none_and_is_optional() -> None:
    """既有五字段构造仍然成立（缺省 `None`）⇒ 本轮之前的所有调用点逐字可用。"""
    assert _project().direction is None


def test_renamed_keeps_the_direction_and_with_direction_keeps_the_name() -> None:
    """两个动作**互不影响**：改名不丢方向、改方向不改名（这是「分开」的机械含义）。"""
    declared = _project(direction="retrieval for planning")
    renamed = declared.renamed("New name", at=Timestamp.now())
    assert renamed.name == "New name"
    assert renamed.direction == "retrieval for planning"

    redirected = declared.with_direction("a different direction", at=Timestamp.now())
    assert redirected.name == "Example"
    assert redirected.direction == "a different direction"

    cleared = declared.with_direction(None, at=Timestamp.now())
    assert cleared.direction is None
    assert cleared.name == "Example"


def test_blank_and_overlong_directions_are_refused() -> None:
    for bad in ("   ", "", "x" * (MAX_PROJECT_DIRECTION_LENGTH + 1)):
        try:
            _project(direction=bad)
        except ValueError:
            continue
        raise AssertionError(f"direction {bad[:12]!r}… must be refused")


def test_direction_is_stripped_when_declared() -> None:
    assert _project(direction="  spaced  ").direction == "spaced"


# ---------------------------------------------------------------- (2) 落库往返


def test_sqlite_round_trip_keeps_the_direction() -> None:
    store = SqliteProjectStore()
    store.save_project(_project(direction="declared direction"))
    assert store.get_project("p-1").direction == "declared direction"


def test_a_legacy_row_without_the_key_reads_back_as_none() -> None:
    """旧行（没有 `direction` 键）⇒ `None`（未声明），**不是** `""`。"""
    store = SqliteProjectStore()
    legacy = {
        "id": "p-legacy",
        "name": "Legacy",
        "status": "ACTIVE",
        "created_at": Timestamp.now().value.isoformat(),
        "updated_at": Timestamp.now().value.isoformat(),
    }
    with store._conn:
        store._run(
            "INSERT INTO projects (project_id, project_json, created_at, updated_at)"
            " VALUES (?, ?, ?, ?)",
            ("p-legacy", json.dumps(legacy), legacy["created_at"], legacy["updated_at"]),
        )
    loaded = store.get_project("p-legacy")
    assert loaded.direction is None
    assert loaded.name == "Legacy"


# ---------------------------------------------------------------- (3) 两端点


def _created(client: TestClient, **body: Any) -> dict[str, Any]:
    response = client.post("/projects", json=body, headers=_idem())
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def test_create_accepts_a_direction_without_touching_the_name(client: TestClient) -> None:
    created = _created(client, name="Study", direction="does retrieval help planning?")
    assert created["direction"] == "does retrieval help planning?"
    assert created["name"] == "Study", "方向不得改写 name（改名是另一件事）"

    listed = {item["id"]: item for item in client.get("/projects").json()}
    assert listed[created["id"]]["direction"] == "does retrieval help planning?"


def test_patch_has_three_distinguishable_direction_states(client: TestClient) -> None:
    """**不出现** = 不动；`null` = 清除；字符串 = 声明。"""
    created = _created(client, name="Study")
    pid = created["id"]
    assert created["direction"] is None

    declared = client.patch(
        f"/projects/{pid}", json={"direction": "first direction"}, headers=_idem()
    )
    assert declared.status_code == 200, declared.text
    assert declared.json()["direction"] == "first direction"

    # 只改名字：方向**不动**（不出现 ≠ 清除）
    renamed = client.patch(f"/projects/{pid}", json={"name": "Renamed"}, headers=_idem())
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["name"] == "Renamed"
    assert renamed.json()["direction"] == "first direction", "改名不得静默清掉方向"

    cleared = client.patch(f"/projects/{pid}", json={"direction": None}, headers=_idem())
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["direction"] is None


def test_the_dedicated_direction_route_only_touches_the_direction(client: TestClient) -> None:
    created = _created(client, name="Keep me")
    pid = created["id"]

    response = client.put(
        f"/projects/{pid}/direction",
        json={"direction": "only the direction"},
        headers=_idem(),
    )
    assert response.status_code == 200, response.text
    assert response.json()["direction"] == "only the direction"
    assert response.json()["name"] == "Keep me"
    assert response.json()["status"] == "ACTIVE"


def test_patch_with_only_direction_is_not_an_empty_patch(client: TestClient) -> None:
    """只给方向**不是**空载荷（否则这条写面在结构上不可用）。"""
    pid = _created(client, name="Study")["id"]
    response = client.patch(f"/projects/{pid}", json={"direction": "x"}, headers=_idem())
    assert response.status_code == 200, response.text


# ---------------------------------------------------------------- (4) 进提示词


def test_the_direction_reaches_the_prompt_with_its_own_section() -> None:
    prompt = compose_prompt("PURPOSE", direction="does retrieval help planning?")
    assert DIRECTION_SECTION_TITLE in prompt
    assert "does retrieval help planning?" in prompt
    assert prompt.startswith("PURPOSE"), prompt


def test_no_direction_keeps_the_prompt_byte_identical() -> None:
    """未声明 ⇒ 提示词**逐字**等于 purpose（三段共同的零回归口径）。"""
    assert compose_prompt("PURPOSE", direction=None) == "PURPOSE"
    assert compose_prompt("PURPOSE", direction="   ") == "PURPOSE"


def test_the_direction_section_precedes_prior_knowledge_and_retrieval() -> None:
    """顺序是契约：方向 → 前序知识 → 检索摘录。"""

    class _Entry:
        identifier = "PMID:1"
        shown = "snippet"
        truncated = False
        memory_id = "mem-1"
        provenance = "run-1"
        review_due = False

    class _View:
        entries = (_Entry(),)

    prompt = compose_prompt(
        "PURPOSE", direction="the direction", prior_knowledge=_View(), retrieval=_View()
    )
    positions = [
        prompt.index(DIRECTION_SECTION_TITLE),
        prompt.index(PRIOR_SECTION_TITLE),
        prompt.index(PROMPT_SECTION_TITLE),
    ]
    assert positions == sorted(positions), positions
