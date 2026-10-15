"""GOAL-20261015-080 EC-04 的 **live 判据**：真实模型写出的**设计**驱动实验。

**它与既有 live 判据的关系**（不互相顶替）：`test_research_report_chain_live.py` 判
「报告链在真实中转站上跑通 + 多臂 + 检索内容进上下文」；本文件判**同一件事的另一半**：
**臂与参数来自计划产物**（而不是装配常量）。

**为什么要单列一个文件**：EC-04 的前提是「模型真的把设计写进计划产物」——
那要求**合约的 purpose 里明写设计块**（否则模型无从知道要写它）。本判据用**同一份**
既有协议与合约，只把 `design_source` 从「装配声明臂」换成 `"plan"`，
并把「设计块该长什么样」写进合约 purpose（**产品面的一行**，见下）。

**★ 本 GOAL 的实测缺口（cycle 4 建档时读出）**：真实 run 的计划制品是**交付物信封**
（`real_research_deliverable_v1`：模型正文在 `content` 里，经 redact + 截断）而不是
「模型直接写的一段 JSON」⇒ 读取器若不认信封，**真实路径永远读不到**（而受控夹具全绿）。
该缺口已由 `9f037821` 修掉（读取器认两种形态 + 四条判据）。

**离线纪律**：本文件在默认门下 **skip**（`requires_live_llm` + 显式开关），
真实 run 只在显式传 `RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1` 时跑。
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

_RUN_ID = "run-goal080-ec04-live-design-from-plan"
_DESIGN_KEY = "experiment_design"
#: 装配方给出的脚本与镜像（与既有 live 判据同源，避免两处各写一份）。
from tests.e2e.test_research_report_chain_live import (  # noqa: E402
    _EXPERIMENT_IMAGE,
    _EXPERIMENT_SCRIPT,
)

pytestmark = pytest.mark.requires_live_llm


def _gate() -> Any:
    """live 门（与既有 live 判据**同一判定**：凭据 + 端点 + runtime + 显式开关）。"""
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


def _sandbox_runner(deps: Any) -> Any:
    """沙箱实验执行体：**臂来自计划产物**（`design_source="plan"`）。

    这是本判据的**唯一**与既有 live 判据不同之处：不声明 `arms`，只声明来源。
    """
    from services.api.experiment_support import (
        DESIGN_SOURCE_PLAN,
        docker_experiment_assembly,
        sandbox_experiment_runner,
    )

    return sandbox_experiment_runner(
        docker_experiment_assembly(
            artifacts=deps.artifacts,
            ledger=deps.ledger,
            policy=deps.policy_evaluator,
            script=_EXPERIMENT_SCRIPT,
            image=_EXPERIMENT_IMAGE,
            experiment_store=deps.experiment_store,
            design_source=DESIGN_SOURCE_PLAN,
        )
    )


def _runs_the_chain(deps: Any) -> dict[str, Any]:
    """跑一次真实 run 并取回**设计面**的读数（计划制品正文 + 读面上的臂与参数）。"""
    from fastapi.testclient import TestClient

    from services.api.app import create_app

    with TestClient(create_app(deps)) as client:
        created = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": "research_report_chain_v1.yaml"},
            headers={"Idempotency-Key": _RUN_ID},
        )
        assert created.status_code == 200, created.text
        run_id = str(created.json()["id"])
        run = client.get(f"/runs/{run_id}").json()
        experiments = client.get(f"/runs/{run_id}/experiments").json()
        artifacts = client.get(f"/runs/{run_id}/artifacts").json()
        events = client.get(f"/runs/{run_id}/events").json()
        sample: dict[str, Any] = {
            "run_id": run_id,
            "state": run["state"],
            "failures": [
                event["payload"].get("message", "")
                for event in events
                if event["type"] in ("run.failed", "task.failed")
            ],
            "experiments": experiments,
            "artifact_ids": [str(item["id"]) for item in artifacts],
        }
        plan_ids = [item for item in sample["artifact_ids"] if item.endswith(":research_plan")]
        assert plan_ids, ("真实 run 必须留下计划制品", sample["artifact_ids"])
        body = client.get(f"/artifacts/{plan_ids[0]}/content")
        sample["plan_artifact_id"] = plan_ids[0]
        sample["plan_status"] = body.status_code
        if body.status_code == 200:
            sample["plan_body"] = body.content.decode("utf-8", errors="replace")
    return sample


def _assert_the_design_came_from_the_plan(sample: dict[str, Any]) -> None:
    """EC-04：计划产物里**写着设计**，且**读面跑出来的臂就是它**。"""
    import json

    from packages.application.experiments.design_from_plan import (
        ENVELOPE_CONTENT_KEY,
        _design_block,
    )

    assert sample["state"] == "SUCCEEDED", (sample["failures"], sample)
    assert not sample["failures"], sample["failures"]
    assert sample["plan_status"] == 200, sample

    raw: object = json.loads(sample["plan_body"])
    assert isinstance(raw, Mapping), raw
    design = _design_block(raw)
    assert design is not None, (
        "**模型必须把设计块写进计划产物**（合约 purpose 已明写它的形状）",
        sorted(raw),
        str(raw.get(ENVELOPE_CONTENT_KEY))[:400],
    )
    assert isinstance(design, Mapping), design
    arms = design.get("arms")
    assert isinstance(arms, Mapping | list) and arms, ("设计块必须带臂", design)

    experiments = list(sample["experiments"]["experiments"])
    assert len(experiments) == len(arms), (
        "跑出来的实验数必须等于计划里声明的臂数",
        len(experiments),
        list(arms),
    )
    listed = {str(item.get("experiment_run_id")) for item in experiments}
    from packages.application.experiments.arms import arm_experiment_id

    expected = {arm_experiment_id(sample["run_id"], name) for name in arms}
    assert listed == expected, (
        "读面上的臂必须**就是**计划里那些",
        sorted(listed),
        sorted(expected),
    )


def test_the_plan_the_model_wrote_drives_the_experiment(tmp_path: Path) -> None:
    """真实 run：**模型写的设计**决定跑哪些实验，且读面逐臂可读。"""

    gate = _gate()
    if not gate.open:
        from packages.application.model_relay.live_run_gate import skip_record_for_gate

        pytest.skip(f"live run skipped: {skip_record_for_gate(_RUN_ID, gate).reason}")

    deps = _live_deps(str(tmp_path / "control-plane.db"))
    import json

    sample = _runs_the_chain(deps)
    Path("scratch").mkdir(exist_ok=True)
    (Path("scratch") / f"goal080-ec04-{sample['run_id']}.json").write_text(
        json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _assert_the_design_came_from_the_plan(sample)


def _live_deps(db_path: str) -> Any:
    """**既有 live 装配** + 本判据唯一要变的那一行（实验段换成「设计取自计划」）。

    **为什么直接复用**：既有 live 判据的 `_live_deps` 已经把三段执行体缝（运行链检索 /
    沙箱实验 / 报告汇编）与检索上下文都接好了 —— 那些是**本协议跑通的既有前提**
    （缺运行链检索 ⇒ 立题格的 `EVIDENCE_COVERAGE: minimum_retrieved_sources` **点名判拒**，
    实测第一次真实跑即命中 ⇒ 如实登记）。本判据只改**实验段**：把「装配声明臂」换成
    「设计取自计划」。**一行不同**，其余同源 ⇒ 两个判据不会各说一套。
    """
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from tests.e2e.test_research_report_chain_live import _live_deps as _base_live_deps

    deps = _base_live_deps(db_path)
    inner = deps.runs._deps
    deps.runs = RunOrchestrationService(
        replace(
            inner,
            experiment_task=_sandbox_runner(deps),
        )
    )
    return deps
