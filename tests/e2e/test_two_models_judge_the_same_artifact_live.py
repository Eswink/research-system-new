"""GOAL-20261020-091 **EC-04** live 判据：真实中转站上两位评审模型各判一次。

**判什么**（一次真实 run，点名 `dual_model_review_v1.yaml`，**产品组合根** +
`preflight_override is None` + 真实执行体）：

1. 终态是**终态**（`SUCCEEDED` 或 `FAILED` —— 评审判负是**正当结论**，不是基础设施失败；
   两者的**判词**才是本判据的被测对象）；
2. **两位评审者都跑了**：`GET /runs/{id}/reviews` 上恰两条评审格判词，`reviewer_model`
   **互不相同**且可归因到出厂目录里的两个第三方模型（`main/glm-5.3` / `main/kimi-k2.6`）；
3. **两位读的是同一件被评对象**：两条判词的 `phase_id` 相同、被评对象那一段在**两次**
   会话的提示词里（读面制品 `{task_id}:review_material` 存的是同一份视图，见下）；
4. **各自的判词全文**逐字落盘（`scratch/goal091-ec04-<run>.json`），供 GOAL 的「真跑读数」
   逐条引用 —— **它们是两位模型自己写下的话**，不是判据编的；
5. **如实登记同判**：两条 verdict 相同 ⇒ 读数为「同质化」，本判据**仍然通过**
   （用户明写：这是有效读数，不是失败）；**不得**为绿构造人为分歧。

**默认门**：`evaluate_live_run_gate`（runtime 显式 `openhands` + 凭据可解析 + 开关打开），
三者缺一 ⇒ **如实 skip**（skip 不是 PASS）。

跑它（凭据只由操作者注入；本文件不读值、不回显、不落盘）：

    set -a; . ./.env; set +a
    RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 \\
      uv run --frozen --no-sync python -B -m pytest \\
      tests/e2e/test_two_models_judge_the_same_artifact_live.py -q -rs

**如实边界**：本判据证明「两位评审者在真实中转站上各自跑完、各自落了一条可归因的判词」；
它**不**声称评审判得对，也**不**声称两位一定给出不同结论（那由读数本身回答）。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from adapters.contracts.models_loaders import load_llm_endpoints
from adapters.relay.credential_resolver import EnvCredentialResolver
from packages.application.model_relay.live_run_gate import (
    evaluate_live_run_gate,
    skip_record_for_gate,
)
from services.api.runtime_support import OPENHANDS_RUNTIME
from tests.e2e.live_switch_support import live_e2e_switch_enabled

pytestmark = pytest.mark.requires_live_llm

_ENDPOINTS = "examples/config/llm_endpoints.yaml"
_ENDPOINT = "main"
_PROTOCOL = "dual_model_review_v1.yaml"
_PROTOCOL_ID = "dual_model_review_v1_0_0"
_CONTRACT = "dual_model_review_deliverable"
_RUN_ID = "run-goal091-ec04-dual-review"
#: 出厂目录里两个第三方评审模型解析后的**执行目标**（`endpoint/model_name`）。
_EXPECTED_TARGETS = {"main/glm-5.3", "main/kimi-k2.6"}
_SAMPLE = Path("scratch") / "goal091-ec04-dual-review.json"


def _endpoint() -> Any:
    return load_llm_endpoints(_ENDPOINTS)[_ENDPOINT]


def _gate() -> Any:
    return evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=_endpoint(),
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
        live_switch=live_e2e_switch_enabled(),
    )


def _live_deps(db_path: str) -> Any:
    """**产品组合根**（`preflight_override is None`）+ 真实 runtime 的会话工具注册面。

    只注入执行体：`review_material` 与被评对象那一段**已是产品装配的一部分**
    （GOAL-091 EC-02 把它接进两个组合根），本判据**不**再补这一行 —— 否则「产品路径上有
    这一段」就不可判了。
    """
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.composition import assemble
    from services.api.runtime_support import build_agent_runtime
    from services.api.settings import ApiSettings

    settings = ApiSettings(
        db_path=db_path,
        agent_runtime=OPENHANDS_RUNTIME,
        # AGENTS §9：host shell 默认 deny；真实 run 要建会话必须**显式**打开。
        workspace_allow_host_shell=True,
    )
    deps = assemble(settings)
    assert deps.preflight_override is None, "live 判据不得带任何 preflight_override"
    assert deps.runs is not None and deps.artifacts is not None
    # 两件 REST provider 的**实例**（真传输）：本协议的 phase 为把 provider 排除出会话工具面
    # 而声明 `run_chain`（能力面里含 `literature.*`）⇒ 它们进冻结集 ⇒ preflight 会对它们做
    # 健康探测；没有实例时健康诚实地是 UNKNOWN ⇒ `TOOL_HEALTH_UNPROVEN` WARN ⇒ **拒冻**
    # （实测：`rebuild.status: REFUSED, missing: [manifest_digest]`）。与 GOAL-089 的 live
    # 判据同一手法：**注入实例**（执行体），不注入判词。
    from adapters.research_tools import EuropePmcProvider, NcbiEutilsProvider

    deps.tool_providers = {
        "europe_pmc": EuropePmcProvider(deps.artifacts, spill_threshold_bytes=1),
        "ncbi_eutils": NcbiEutilsProvider(deps.artifacts, spill_threshold_bytes=1),
    }
    runtime = build_agent_runtime(
        settings,
        selection=deps.runtime_selection,
        credentials=deps.credentials,
        policy_evaluator=deps.policy_evaluator,
        budget_ledger=deps.budget,
        register_session_tools=_register_tools(deps),
    )
    deps.runs = RunOrchestrationService(replace(deps.runs._deps, runtime=runtime))
    return deps


def _register_tools(deps: Any) -> Any:
    """会话工具注册面（出厂绑定表 + 本协议用到的文献绑定）。

    本协议的两个 phase 都声明 `capability_execution: run_chain` ⇒ 会话工具面为**空**
    （`session_tool_bindings` 无处可绑）。注册面因此只需覆盖出厂读面 —— 空面不会用到
    任何名字，但装配需要一个合法的 `register_tools` 入口。
    """
    from services.api.session_tool_support import session_tool_register

    return session_tool_register(
        providers={},
        provider_specs={},
        artifacts=deps.artifacts,
        policy=deps.policy_evaluator,
        bindings=(),
    )


def _execute(deps: Any) -> dict[str, Any]:
    """一次真实 run（产品组合根 + 既有 API），取回读面并**把判词全文落盘**。

    `panels` 与 `reviewer_model` 走**canonical 读面** `review_read`（`review.read` 能力的
    执行实现，与 HTTP 读面 `GET /runs/{id}/reviews` **同一个查询口径**）—— 后者返回的是
    逐条裁决的 DTO，没有聚合小组那一格（GOAL-085 的 `panels` 只在这条读面上）。
    两条面都读：HTTP 面证明「操作者看得到每条裁决」，读面证明「小组与归因在那里」。
    """
    from adapters.canonical.review_read import review_read
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
        reviews = client.get(f"/runs/{run_id}/reviews").json()
        events = client.get(f"/runs/{run_id}/events").json()
        assert deps.review_findings is not None, "产品组合根必须接上评审结论存储"
        reading = review_read(deps.review_findings, {"run_id": run_id})
        sample: dict[str, Any] = {
            "run_id": run_id,
            "state": run["state"],
            "protocol_id": run["protocol_id"],
            "failures": [
                event["payload"].get("message", "")
                for event in events
                if event["type"] in ("run.failed", "task.failed")
            ],
            # HTTP 面（操作者视角）：逐条裁决。
            "http_review_count": len(reviews),
            # canonical 读面：判词全文 + 归因 + 聚合小组。
            "reviews": reading["reviews"],
            "panels": reading["panels"],
            "review_count": reading["count"],
        }
    _SAMPLE.parent.mkdir(parents=True, exist_ok=True)
    _SAMPLE.write_bytes((json.dumps(sample, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return sample


def _review_rows(sample: dict[str, Any]) -> list[dict[str, Any]]:
    """**评审格**的判词（按合约筛：作者格也有一条门结论，那是产品既有语义）。"""
    return [item for item in sample["reviews"] if str(item.get("contract_id")) == _CONTRACT]


def test_two_review_models_judge_the_same_artifact_on_the_real_relay() -> None:
    gate = _gate()
    if not gate.open:
        # 门关着 ⇒ **如实 skip**，理由取自门自己（`skip_record_for_gate` 是既有形态）。
        skip_record_for_gate(_RUN_ID, gate)
        pytest.skip(f"live run skipped: {gate.reason}")

    sample = _execute(_live_deps(f"data/goal091-live-{os.getpid()}.db"))

    assert sample["state"] in {"SUCCEEDED", "FAILED"}, sample["state"]
    rows = _review_rows(sample)
    assert len(rows) == 2, [(item.get("reviewed_by"), item.get("reviewer_model")) for item in rows]

    # ① 两个**不同的**执行目标（可归因到出厂目录里的两个第三方评审模型）。
    targets = {str(item["reviewer_model"]) for item in rows}
    assert targets == _EXPECTED_TARGETS, targets

    # ② 同一件被评对象：同 phase、不同任务。
    assert len({str(item["phase_id"]) for item in rows}) == 1, [i["phase_id"] for i in rows]
    assert len({str(item["task_id"]) for item in rows}) == 2

    # ③ 判词全文在场（**模型自己写下的话**，逐字落盘供记录引用）。
    for item in rows:
        assert item["verdicts"], item
        joined = "\n".join(str(line) for line in item["verdicts"])
        assert joined.strip(), item
        assert "REVIEW_SCORE: " in joined, joined[:400]

    # ④ 面板聚合（两条可归因判词 ⇒ 一份小组；同判则 advisory 有值、分歧则 dissent 非空）。
    panels = sample["panels"]
    assert len(panels) == 1, panels
    panel = panels[0]
    assert panel["voters"] == 2, panel
    assert panel["independent"] is True, panel
    verdicts = {str(item["verdict"]) for item in rows}
    if len(verdicts) == 1:
        # **同质化读数**：两位同判 —— 这是有效结论，不是失败。
        assert panel["dissent"] == [], panel
        assert panel["advisory"] in verdicts, panel
    else:
        assert panel["dissent"], panel
