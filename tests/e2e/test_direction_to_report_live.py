"""GOAL-20261024-096 **EC-04** live 判据：六相链在真实中转站上一次 run 走完。

**判什么**（一次真实 run，点名 `direction_to_report_v1.yaml`，**产品组合根**
+ `preflight_override is None` + 真实执行体 + `design_source="plan"`）：

1. 终态恰为 `SUCCEEDED`（`FAILED` 也是终态，但不在这里算通过）；
2. **六相全落库**：`research_question` / `retrieval_report` / `research_plan` /
   `review_decision` / `research_report.md` 各在制品读面上，实验经**实验读面**有落库行；
3. **问题由模型自己提出**：`research_question` 的正文里有 `research_question` 块与 `query`；
4. **检索词逐字来自那个块**：检索调用参数制品（`tool-args`）里的字符串里有那个 query，
   且命中的**真实标识**（PMID/DOI）出现在证据读面上；
5. **报告第 1 节逐字引用本 run 的问题块**（EC-03 在真实条件下的复核）；
6. **读数逐条落盘**到 `.cursor/plans/goals/evidence/GOAL-20261024-096-live-run.txt`
   （run id / 方向原文 / 问题正文 / query / 真实标识 / 实验指标 / 报告 digest / 终态）。

**默认门**：`evaluate_live_run_gate`（runtime 显式 `openhands` + 凭据可解析 + live 开关打开）。
三者缺一 ⇒ **如实 skip**（skip 不是 PASS）。

跑它（凭据由操作者注入；本文件不读值、不回显、不落盘）：

    set -a; . ./.env; set +a
    RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 \\
      uv run --frozen --no-sync python -B -m pytest \\
      tests/e2e/test_direction_to_report_live.py -q -rs

**如实边界**：本判据证明「六相在真实条件下于**一次 run** 内成链且报告站在本 run 自己的
问题上」这一条机械事实；它**不**判问题提得好不好、计划科学不科学、评审公正不公正
（那要人评 / 评审面 / 叙述质量口径 —— 后者未获授权不定义），也**不**声称报告是模型撰写的
（它是确定性汇编，谁是作者在制品 `created_by` 上可读）。

**首两次实跑失败、第三次通过**：失败签名是 `litellm.RateLimitError: Channel rate limit
reached for model`（中转站通道限流，基础设施类）—— 离线 e2e 在同样装配下六例全绿即证明
链路本身成立。两次失败的读数与通过后的读数**都留在取证文件里**，不抹平。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from packages.application.deliverable.research_report import (
    REPORT_ARTIFACT_NAME,
    SECTION_HEADINGS,
)
from packages.application.model_relay.live_run_gate import (
    evaluate_live_run_gate,
    skip_record_for_gate,
)
from services.api.app import create_app
from tests.e2e.direction_to_report_live_support import (
    DIRECTION,
    ENDPOINT,
    ENDPOINTS,
    PROTOCOL,
    question_block,
    question_text,
    read_identifiers,
    search_terms,
    wired_deps,
)
from tests.e2e.live_switch_support import live_e2e_switch_enabled

pytestmark = pytest.mark.requires_live_llm

#: EC-04 的取证文件（读数逐条落盘）。
_EVIDENCE = Path(".cursor/plans/goals/evidence/GOAL-20261024-096-live-run.txt")
#: 参数制品的 `classification`（`phase_capabilities._tool_call` 的落库值）。
_TOOL_ARGS_CLASSIFICATION = "tool-args"
_PMID = re.compile(r"\d{6,9}")


def _write_evidence(readings: dict[str, Any]) -> None:
    """读数逐条落盘（EC-04 的交付面）。"""
    _EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "GOAL-20261024-096 EC-04 — 六相链 live 真跑读数",
        "",
        f"protocol: {PROTOCOL}",
        f"direction: {DIRECTION}",
        "",
    ]
    for key, value in readings.items():
        text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
        lines.append(f"{key}: {text}")
    _EVIDENCE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _executed(deps: Any) -> dict[str, Any]:
    """起一次真实 run，读回四份读面（run / evidence / artifacts / experiments / 报告正文）。"""
    with TestClient(create_app(deps)) as client:
        created = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": PROTOCOL},
            headers={"Idempotency-Key": "goal096-ec04-live"},
        )
        assert created.status_code == 200, created.text
        run_id = str(created.json()["id"])
        reads: dict[str, Any] = {
            "run_id": run_id,
            "run": client.get(f"/runs/{run_id}").json(),
            "evidence": client.get(f"/runs/{run_id}/evidence").json(),
            "artifacts": client.get(f"/runs/{run_id}/artifacts").json(),
            "experiments": client.get(f"/runs/{run_id}/experiments").json(),
            "report": "",
        }
        report_ids = [
            str(item["id"])
            for item in reads["artifacts"]
            if str(item["id"]).endswith(f":{REPORT_ARTIFACT_NAME}")
        ]
        if report_ids:
            body = client.get(f"/artifacts/{report_ids[0]}/content")
            reads["report"] = body.content.decode("utf-8", errors="replace")
    return reads


def _readings(deps: Any, reads: dict[str, Any]) -> dict[str, Any]:
    """从读面取本轮要落盘的每一项（问题正文 / query / 检索词 / 真实标识 / digest）。"""
    ids = {str(item["id"]) for item in reads["artifacts"]}
    question_ids = sorted(item for item in ids if item.endswith(":research_question"))
    readings: dict[str, Any] = {
        "run_id": reads["run_id"],
        "state": reads["run"]["state"],
        "failures": reads["run"].get("message") or "",
        "artifact_ids": sorted(ids),
        "experiments": reads["experiments"].get("experiments", []),
        "report_digest": next(
            (
                item["digest"]
                for item in reads["artifacts"]
                if str(item["id"]).endswith(f":{REPORT_ARTIFACT_NAME}")
            ),
            "",
        ),
        "search_terms": search_terms(deps, tool_args_classification=_TOOL_ARGS_CLASSIFICATION),
        "retrieved_identifiers": read_identifiers(reads["evidence"], _PMID),
        "report_question_section": reads["report"].split(SECTION_HEADINGS[1])[0][:2000],
    }
    if question_ids:
        question = question_text(deps.artifacts, question_ids[0])
        readings["question"] = question
        readings["query"] = str(question_block(question)["query"])
    return readings


def _gate() -> Any:
    """live 门：runtime 显式 openhands + 凭据可解析 + 开关打开（缺一 ⇒ skip）。"""
    import os

    from adapters.contracts.models_loaders import load_llm_endpoints
    from adapters.relay.credential_resolver import EnvCredentialResolver
    from services.api.runtime_support import OPENHANDS_RUNTIME

    return evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=load_llm_endpoints(ENDPOINTS)[ENDPOINT],
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
        live_switch=live_e2e_switch_enabled(),
    )


def test_one_run_carries_the_whole_six_phase_chain() -> None:
    live = _gate()
    if not live.open:
        pytest.skip(f"live run skipped: {skip_record_for_gate('goal096-ec04', live).reason}")

    deps = wired_deps()
    reads = _executed(deps)
    readings = _readings(deps, reads)
    _write_evidence(readings)

    run = reads["run"]
    assert run["state"] == "SUCCEEDED", (run["state"], run.get("message"))
    # 六相：五件制品 + 实验读面的一行（实验相的落盘名是沙箱自己的）。
    ids = {str(item["id"]) for item in reads["artifacts"]}
    for suffix in (
        "research_question",
        "retrieval_report",
        "research_plan",
        "review_decision",
        REPORT_ARTIFACT_NAME,
    ):
        assert any(item.endswith(f":{suffix}") for item in ids), (suffix, sorted(ids))
    assert reads["experiments"].get("experiments"), reads["experiments"]
    # 检索词逐字来自模型写下的问题；真实标识进证据面。
    assert readings["query"] in readings["search_terms"], readings["search_terms"]
    assert readings["retrieved_identifiers"], reads["evidence"]
    # 报告第 1 节逐字引用本 run 的问题块（EC-03 在真实条件下的复核）。
    expected = json.dumps(question_block(readings["question"]), ensure_ascii=False)
    assert expected in reads["report"], reads["report"][:800]
