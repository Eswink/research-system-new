"""GOAL-20261018-082 EC-04 判据：**前序知识来自前一个 run**，且第二轮立题看得见它。

**它判什么**（本 GOAL 的落点）：一次 run 的立题会话在开工前看到**前序 run 落库的记忆**。
判据走**完整 run 路径**（`compile → preflight → freeze → execute_phases`），不是只测装配器：

1. **第一轮**：run 正常跑完，其结论经 `MemoryWriteProposal → gate → commit` 落成记忆
   （**PROJECT** 档 —— 跨 run 才读得到）；
2. **第二轮**：立题会话的 spec 上，`prior_knowledge_prompt` **在场**且含第一轮那条记忆的
   `memory_id` 与 `provenance`（后者指向前一轮 run）；
3. **按压**：清空记忆库 ⇒ 第二轮提示词里**没有**那一段（不伪造、不留空壳）。

**为什么用 spec 而不是模型正文**：「模型是否引用了前序知识」属 live 判据（要真实中转站）；
本判据判**产品路径**把知识送到了会话门口 —— 那是可离线判定、且必须为真的一步。

**如实边界**：本文件用 run-ready 夹具（受控记忆 + 离线端点），证的是**链路与判据**；
真实模型侧由 `tests/e2e/test_prior_knowledge_changes_the_plan_live.py` 承担。
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from adapters.fakes.memory_store import FakeMemoryStore
from packages.application.run_orchestration.prior_knowledge import build_prior_knowledge
from packages.application.run_orchestration.retrieval_prompt import PRIOR_SECTION_TITLE
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal
from services.api.app import create_app
from tests.e2e.retrieval_context_support import install_spec_recorder
from tests.e2e.test_ec03_real_runtime_offline_chain import mock_relay  # noqa: F401 - fixture
from tests.e2e.test_research_report_arc_offline import _assembled_deps

__all__ = ["mock_relay"]

pytestmark = pytest.mark.requires_docker

_PROTOCOL = "grounded_report_chain_v1.yaml"
#: 立题格的合约（判据按它取那一次会话的 spec）。
_PLAN_CONTRACT = "research_report_plan"


def _seed_prior_run(
    store: FakeMemoryStore, *, content: str, provenance: str, memory_id: str
) -> None:
    """一轮 run 的结论 → **PROJECT** 档记忆（跨 run 才读得到）。"""
    store.allow_source(provenance)
    store.commit(
        MemoryWriteProposal(
            id=memory_id,
            tier=MemoryTier.PROJECT,
            kind=MemoryType.LESSON,
            content=content,
            provenance=provenance,
            confidence=0.9,
            scope="project",
        )
    )


def _wire(deps: Any, store: FakeMemoryStore) -> None:
    """把**产品装配**接上：记忆面 + 它的读取闭包（与两个组合根同一处决策）。"""
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.prior_knowledge_support import prior_knowledge_builder

    deps.memory = store
    deps.runs = RunOrchestrationService(
        replace(deps.runs._deps, prior_knowledge=prior_knowledge_builder(memory_store=store))
    )
    install_spec_recorder(deps)


def _run_once(client: TestClient, key: str) -> dict[str, Any]:
    created = client.post(
        "/projects/example-project/runs",
        json={"protocol_path": _PROTOCOL},
        headers={"Idempotency-Key": key},
    )
    assert created.status_code == 200, created.text
    payload: dict[str, Any] = created.json()
    return payload


def _plan_prompt(deps: Any) -> str | None:
    """立题那次会话的**前序知识段**（经 spec 记录器，读的是交给 runtime 的那份事实）。"""
    recorder = getattr(deps, "session_specs", None)
    if recorder is None:
        return None
    spec = recorder.specs.get(_PLAN_CONTRACT)
    if spec is None:
        return None
    prompt = getattr(spec, "prior_knowledge_prompt", None)
    return str(prompt) if prompt else None


def test_the_second_run_sees_the_first_runs_knowledge(mock_relay: str) -> None:  # noqa: F811
    """**跨 run**：第二轮立题会话的提示词里带第一轮落库的那条记忆。"""
    from tests.e2e.literature_chain_support import OfflineEuropePmc

    deps, _recorder = _assembled_deps(mock_relay, OfflineEuropePmc(requests=[]))
    store = FakeMemoryStore()
    _seed_prior_run(
        store,
        memory_id="mem-prior-lesson",
        content="First round lesson: duplicate_pairs must be pinned before comparing arms.",
        provenance="run:round-1:claim:result",
    )
    _wire(deps, store)

    with TestClient(create_app(deps)) as client:
        run = _run_once(client, "goal082-ec04-round-2")
        state = client.get(f"/runs/{run['id']}").json()["state"]

    assert state == "SUCCEEDED", state
    prompt = _plan_prompt(deps)
    assert prompt, "立题会话必须带**前序知识段**（跨 run 的 PROJECT 档记忆）"
    assert PRIOR_SECTION_TITLE in prompt
    assert "mem-prior-lesson" in prompt
    # 来源指向前一个 run（「前序」不是同 run 内的传递）。
    assert "run:round-1:claim:result" in prompt


def test_press_without_prior_memory_the_plan_sees_no_section(mock_relay: str) -> None:  # noqa: F811
    """**按压**：清空记忆库 ⇒ 立题提示词里**没有**那一段（不伪造、不留空壳）。"""
    from tests.e2e.literature_chain_support import OfflineEuropePmc

    deps, _recorder = _assembled_deps(mock_relay, OfflineEuropePmc(requests=[]))
    _wire(deps, FakeMemoryStore())  # 空库：与上一条只差「有没有那条记忆」

    with TestClient(create_app(deps)) as client:
        run = _run_once(client, "goal082-ec04-round-2-press")
        state = client.get(f"/runs/{run['id']}").json()["state"]

    assert state == "SUCCEEDED", state
    assert _plan_prompt(deps) is None, (
        "空库时必须**没有**那一段（空集合渲染成空串 ⇒ spec 上是 None）",
        _plan_prompt(deps),
    )


def test_a_run_tier_memory_does_not_satisfy_the_prompt() -> None:
    """**只认跨 run 档位**：`RUN` 档记忆不构成前序知识（那是本 run 内的东西）。"""
    store = FakeMemoryStore()
    store.allow_source("run:this-run:claim:x")
    store.commit(
        MemoryWriteProposal(
            id="mem-run-tier",
            tier=MemoryTier.RUN,
            kind=MemoryType.FACT,
            content="this run's scratch",
            provenance="run:this-run:claim:x",
            confidence=0.9,
            scope="run",
        )
    )
    from datetime import datetime, timezone

    view = build_prior_knowledge(store, now=Timestamp(datetime.now(timezone.utc)))
    assert view.entries == ()
    assert view.reason
