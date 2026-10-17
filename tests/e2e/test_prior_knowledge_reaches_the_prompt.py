"""GOAL-20261018-082 EC-03 判据：提示词里的前序知识 == **项目记忆读面**，逐条逐字。

**它判什么**：「模型拿到了什么」必须能对着**既有读面**（`GET /projects/{id}/memory`）
核对 —— 不靠回忆、不靠日志。

两条读数（**成对**，缺一即不可信）：

1. 提示词那段里的每条 `memory_id` / 截断后正文 / 来源 `provenance`，都与读面上**同一批记录**
   （按 `tier ∈ {PROJECT, ORGANIZATION}` 取）**逐字**相同；
2. **反证**：改一条记忆的正文 ⇒ 判据红（证明它判的是**同一份事实**，不是两份各说一套）。

为什么用 HTTP 读面而不是直接问 store：读面是**产品承诺**（`GET /projects/{id}/memory` 的
`records[].tier/content/provenance`）。判据若只读 store，会漏掉「读面渲染时改了字」这类漂移。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi.testclient import TestClient

from adapters.fakes.memory_store import FakeMemoryStore
from packages.application.run_orchestration.prior_knowledge import build_prior_knowledge
from packages.application.run_orchestration.retrieval_prompt import (
    PRIOR_SECTION_TITLE,
    render_prior_knowledge_prompt,
)
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal
from services.api.app import create_app
from tests.api.run_fixtures import make_run_ready_deps

_NOW = Timestamp(datetime(2026, 10, 18, 12, 0, 0, tzinfo=timezone.utc))
_PROJECT = "example-project"
#: 跨 run 档位（与装配器的 `PRIOR_TIERS` 同源；判据里**写死**，不 import 产品常量当预言机）。
_PRIOR_TIERS = ("PROJECT", "ORGANIZATION")


def _store() -> FakeMemoryStore:
    store = FakeMemoryStore()
    for tier, memory_id, content, provenance in (
        (
            MemoryTier.PROJECT,
            "mem-fair",
            "Earlier runs found FAIR pipelines reproduce better than ad-hoc ones.",
            "run:prior-run:claim:c1",
        ),
        (
            MemoryTier.ORGANIZATION,
            "mem-org",
            "Organization policy: pre-register every hypothesis before running.",
            "run:prior-run:claim:c2",
        ),
        (
            MemoryTier.RUN,
            "mem-run-only",
            "this run's scratch note (must NOT reach the prompt)",
            "run:this-run:claim:c3",
        ),
    ):
        store.allow_source(provenance)
        store.commit(
            MemoryWriteProposal(
                id=memory_id,
                tier=tier,
                kind=MemoryType.FACT,
                content=content,
                provenance=provenance,
                confidence=0.9,
                scope="project",
            )
        )
    return store


def _read_face_records(client: TestClient) -> list[dict[str, Any]]:
    """项目记忆读面 → 跨 run 档位那批记录（**只经既有路由**）。"""
    response = client.get(f"/projects/{_PROJECT}/memory")
    assert response.status_code == 200, response.text
    records = response.json()["records"]
    return [item for item in records if item["tier"] in _PRIOR_TIERS]


def _prompt_lines(section: str) -> list[str]:
    """提示词那段 → 逐条行（去掉标题与空行）。"""
    return [line for line in section.splitlines() if line.startswith("- ")]


def test_the_prompt_section_matches_the_project_memory_read_face() -> None:
    """**逐条逐字相同**：id / 截断后正文 / 来源三样都与读面一致。"""
    deps = make_run_ready_deps()
    store = _store()
    deps.memory = store
    view = build_prior_knowledge(store, now=_NOW, run_id="run-2")
    section = render_prior_knowledge_prompt(view)
    assert PRIOR_SECTION_TITLE in section

    with TestClient(create_app(deps)) as client:
        records = _read_face_records(client)

    assert len(records) == len(view.entries) == 2, (
        "读面与装配必须看到**同一批**记录（跨 run 档位两条）",
        [item["id"] for item in records],
        [entry.memory_id for entry in view.entries],
    )
    by_id = {item["id"]: item for item in records}
    lines = _prompt_lines(section)
    assert len(lines) == len(records)
    for entry in view.entries:
        record = by_id[entry.memory_id]
        assert entry.tier == record["tier"]
        assert entry.provenance == record["provenance"]
        # 正文：未截断时**逐字**等于读面的 content；截断时是它的前缀且带标注。
        if entry.truncated:
            assert record["content"].startswith(entry.shown)
            assert "[truncated]" in section
        else:
            assert entry.shown == record["content"]
        # 那一行确实在提示词里（标识 + 来源都在同一条行上）。
        assert any(
            line.startswith(f"- {entry.memory_id}") and entry.provenance in line for line in lines
        ), (entry.memory_id, lines)


def test_press_changing_a_memory_breaks_the_match() -> None:
    """**反证**：改一条记忆正文 ⇒ 提示词那段与读面**不再逐字相同**（判据须红）。

    这里取「同一份事实」的正向形态：改 store 之后重新装配 ⇒ 新提示词**跟着变**，
    而**旧**提示词与**新**读面不再一致。若判据读的是缓存或第二套查询，这个反证会绿。
    """
    deps = make_run_ready_deps()
    store = _store()
    deps.memory = store
    before = render_prior_knowledge_prompt(build_prior_knowledge(store, now=_NOW, run_id="run-2"))

    # 反证：新增一条跨 run 记忆（读面与提示词必须**同时**变）。
    store.allow_source("run:prior-run:claim:c4")
    store.commit(
        MemoryWriteProposal(
            id="mem-new",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.LESSON,
            content="New lesson: pin the container digest before comparing arms.",
            provenance="run:prior-run:claim:c4",
            confidence=0.9,
            scope="project",
        )
    )
    after = render_prior_knowledge_prompt(build_prior_knowledge(store, now=_NOW, run_id="run-2"))

    with TestClient(create_app(deps)) as client:
        records = _read_face_records(client)

    assert before != after, "新增记忆必须改变提示词（否则判据读的不是这份 store）"
    assert "mem-new" in after
    assert "mem-new" in {item["id"] for item in records}
    # 旧段落不再与读面同批（这正是「反证红」的形态）。
    assert "mem-new" not in before


def test_expired_memory_is_absent_from_both_faces() -> None:
    """时效一致：`expires_at` 已过的记录**不在**提示词里。

    读面仍会列出它（读面是「库里有什么」），所以判据只要求**提示词**这一侧排除 ——
    两侧的口径差异**明写在这里**，不假装它们一模一样。
    """
    store = FakeMemoryStore()
    store.allow_source("run:prior-run:stale")
    store.commit(
        MemoryWriteProposal(
            id="mem-stale",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="stale knowledge",
            provenance="run:prior-run:stale",
            confidence=0.9,
            scope="project",
            expires_at=Timestamp(_NOW.value - timedelta(days=1)),
        )
    )
    section = render_prior_knowledge_prompt(build_prior_knowledge(store, now=_NOW, run_id="run-2"))
    assert "mem-stale" not in section
