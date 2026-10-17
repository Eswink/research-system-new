"""GOAL-20261018-082 EC-04 的 **live 判据**：真实模型**用上了**前序知识。

**它判什么**（本 GOAL 的最终一格）：离线判据（`test_prior_knowledge_changes_the_next_round.py`）
证了「产品路径把前序知识送到了会话门口」；本判据判**真实模型侧的下一步** ——
**模型是否真的引用/沿用了它看到的前序知识**。

三条读数（**成对**，缺一即不可信）：

1. **它看到了什么**：立题会话（`research_report_plan`）的提示词里带**本次前置**的记忆
   `memory_id` 与 `provenance`（`provenance` 指向**前一轮 run**，不是同 run 内传递）；
2. **它用上了什么**：模型的**计划正文**里引用了那条记忆的 `memory_id`（「立题因前序知识
   而不同」的最小可判证据）；
3. **按压**（离线侧已有；这里如实声明不重复跑）：清空记忆库 ⇒ 提示词里没有那一段 ——
   由 `test_prior_knowledge_changes_the_next_round.py::test_press_without_prior_memory...` 承担。

**降级梯**（GOAL 原文逐字）：模型侧不可用**或模型不引用** ⇒ 记 PENDING + 点名阻塞点，
**不得**伪造。

**离线纪律**：默认门下如实 skip（`requires_live_llm` + 显式开关）。

用法（与既有 live 判据同一口令形态）：

    set -a; . ./.env; set +a
    RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 \
      uv run --frozen --no-sync python -B -m pytest \
      tests/e2e/test_prior_knowledge_changes_the_plan_live.py -q --no-header
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

_RUN_ID = "run-goal082-ec04-live-prior-knowledge"
_PROTOCOL = "grounded_report_chain_v1.yaml"
#: 立题格的合约（判据按它取那一次会话的 spec 与计划正文）。
_PLAN_CONTRACT = "research_report_plan"
#: 预置的前序知识（**PROJECT 档**= 跨 run 才读得到）。
_PRIOR_MEMORY_ID = "mem-live-prior-lesson"
_PRIOR_PROVENANCE = "run:live-round-1:claim:result"
_PRIOR_CONTENT = (
    "Prior round lesson: reproducibility improves when the duplicate_pairs parameter is "
    "pinned before comparing arms, because unpinned duplicate generation dominates variance."
)

pytestmark = pytest.mark.requires_live_llm


def _gate() -> Any:
    import os

    from adapters.relay.credential_resolver import EnvCredentialResolver
    from packages.application.model_relay.live_run_gate import evaluate_live_run_gate
    from services.api.runtime_support import OPENHANDS_RUNTIME
    from tests.e2e.live_switch_support import live_e2e_switch_enabled
    from tests.e2e.test_research_report_chain_live import _endpoint

    return evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=_endpoint(),
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
        live_switch=live_e2e_switch_enabled(),
    )


def _seed_prior_knowledge(deps: Any) -> None:
    """把「前一轮 run 的结论」落成一条 PROJECT 档记忆（走**既有**写入链）。"""
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryWriteProposal

    store = deps.memory
    assert store is not None, "产品组合根必须给出记忆面（本判据的前提）"
    store.allow_source(_PRIOR_PROVENANCE)
    store.commit(
        MemoryWriteProposal(
            id=_PRIOR_MEMORY_ID,
            tier=MemoryTier.PROJECT,
            kind=MemoryType.LESSON,
            content=_PRIOR_CONTENT,
            provenance=_PRIOR_PROVENANCE,
            confidence=0.9,
            scope="project",
        )
    )


def _live_deps(db_path: str) -> Any:
    """**既有 live 装配** + 前序知识接线 + 预置的一条跨 run 记忆。

    与 GOAL-081 EC-04 的 live 判据同源（`_live_deps` 那段已经把三段执行体缝接好）；
    本判据只**追加**两条：① 前序知识的装配闭包；② 一条 PROJECT 档记忆。
    """
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.prior_knowledge_support import prior_knowledge_builder
    from tests.e2e.test_research_report_chain_live import _live_deps as _base

    deps = _base(db_path)
    store = deps.memory
    assert store is not None, "产品组合根必须给出记忆面"
    deps.runs = RunOrchestrationService(
        replace(deps.runs._deps, prior_knowledge=prior_knowledge_builder(memory_store=store))
    )
    _seed_prior_knowledge(deps)
    return deps


def _plan_artifacts(client: Any, run_id: str) -> dict[str, Any]:
    """读面：计划制品（模型写的那份）。"""
    artifacts = client.get(f"/runs/{run_id}/artifacts").json()
    plan_ids = [str(item["id"]) for item in artifacts if str(item["id"]).endswith(":research_plan")]
    where: dict[str, Any] = {"plan_artifact_id": plan_ids[0] if plan_ids else None}
    if not plan_ids:
        return where
    body = client.get(f"/artifacts/{plan_ids[0]}/content")
    where["plan_status"] = body.status_code
    if body.status_code == 200:
        raw = json.loads(body.content.decode("utf-8", errors="replace"))
        if isinstance(raw, Mapping):
            where["plan_content"] = str(raw.get("content") or "")
    return where


def _run_once(deps: Any) -> dict[str, Any]:
    """跑一次真实 run，取回本判据要的三样：提示词那段 / 计划正文 / 读面记忆。"""
    from fastapi.testclient import TestClient

    from services.api.app import create_app

    with TestClient(create_app(deps)) as client:
        created = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": _PROTOCOL},
            headers={"Idempotency-Key": _RUN_ID},
        )
        assert created.status_code == 200, created.text
        run_id = str(created.json()["id"])
        run = client.get(f"/runs/{run_id}").json()
        sample: dict[str, Any] = {"run_id": run_id, "state": run["state"]}
        sample.update(_plan_artifacts(client, run_id))
        memory = client.get("/projects/example-project/memory").json()
        sample["prior_memories"] = [
            item
            for item in memory.get("records", ())
            if item["tier"] in ("PROJECT", "ORGANIZATION")
        ]

    recorder = getattr(deps, "session_specs", None)
    spec = recorder.specs.get(_PLAN_CONTRACT) if recorder is not None else None
    sample["prior_prompt"] = (
        str(getattr(spec, "prior_knowledge_prompt", None) or "") if spec is not None else ""
    )
    # 诊断面：检索段**也**取样（两段应当**同时**在场；缺一段时判据能指出是哪一段）。
    sample["retrieval_prompt"] = (
        str(getattr(spec, "retrieval_prompt", None) or "") if spec is not None else ""
    )
    sample["contracts_with_prompts"] = {
        contract_id: bool(getattr(item, "prior_knowledge_prompt", None))
        for contract_id, item in (recorder.specs.items() if recorder is not None else ())
    }
    return sample


def _assert_the_model_used_the_prior_knowledge(sample: dict[str, Any]) -> None:
    """两条成对读数：**看到了**（提示词带前序记忆）+ **用上了**（正文引用其 `memory_id`）。"""
    assert sample["state"] == "SUCCEEDED", (sample["state"], sample)

    prompt = sample.get("prior_prompt") or ""
    assert prompt, (
        "**它看到了什么**：立题会话的提示词里必须有**前序知识那段**",
        sorted(item.get("id") for item in sample.get("prior_memories") or ()),
    )
    assert _PRIOR_MEMORY_ID in prompt, (prompt[:400],)
    assert _PRIOR_PROVENANCE in prompt, (
        "来源必须指向**前一轮 run**（跨 run，不是同 run 内传递）",
        prompt[:400],
    )

    content = sample.get("plan_content") or ""
    assert content, (
        "模型必须留下计划正文",
        sample.get("plan_artifact_id"),
        sample.get("plan_status"),
    )
    assert _PRIOR_MEMORY_ID in content, (
        "**它用上了什么**：计划正文必须**引用**那条前序记忆的 `memory_id` —— "
        "这正是「立题因前序知识而不同」的最小可判证据。",
        _PRIOR_MEMORY_ID,
        content[:600],
    )


def test_the_model_uses_prior_run_knowledge(tmp_path: Path) -> None:
    """真实 run：模型**看到了**前序知识，且在计划里**引用了**它。"""
    gate = _gate()
    if not gate.open:
        from packages.application.model_relay.live_run_gate import skip_record_for_gate

        pytest.skip(f"live run skipped: {skip_record_for_gate(_RUN_ID, gate).reason}")

    deps = _live_deps(str(tmp_path / "control-plane.db"))
    sample = _run_once(deps)
    Path("scratch").mkdir(exist_ok=True)
    (Path("scratch") / f"goal082-ec04-{sample['run_id']}.json").write_text(
        json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _assert_the_model_used_the_prior_knowledge(sample)
