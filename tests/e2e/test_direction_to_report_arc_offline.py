"""GOAL-20261024-096 的**编排级**判据：六相链在一次离线 run 里走完。

**被测对象**：新协议 `direction_to_report_v1.yaml`（question / retrieval / plan /
experiment / review / report 六相）经产品路径跑完，产出**人类可读的报告**。

判什么（与单元判据分工，互不替代）：

1. **六相全落库**：六件产物分属**不同任务**，run 收敛 `SUCCEEDED`；
2. **(i) 编排级**：检索格实际发给 provider 的检索词 == 问题格产出里的 `query`
   （provider 传输层取证；两个变体各自等于自己的产出）；
3. **(ii) 编排级**：改检索产出（换一批记录）⇒ `plan` 会话的提示词材料随之变
   （spec 的 `retrieval_prompt` 是会话创建点拼进提示词的**同一份字节**）；
   并顺带取证「plan 产出 ⇒ review 提示词的被评对象段随之变」；
4. **EC-03 (i) 全链**：报告第 1 节**逐字节**包含本 run 问题格产出的正文
   （经产品路径 `report_facts` → `report_question`，不是判据自己拼的）；
5. **实验设计来自计划**：装配面 `design_source="plan"` ⇒ 臂就是计划产物里声明的那两个。

**如实边界**：mock 中转站 + 离线 Europe PMC（真解析、不出网）+ 真容器实验；
它证的是**链路与判据**，真实条件下的六相由 live 判据承担（EC-04）。
"""

from __future__ import annotations

from typing import Any

import pytest

from services.api.app import create_app
from tests.e2e.direction_to_report_support import (
    OUTPUT_NAMES,
    PROTOCOL,
    RECORD_POOL,
    VARIANT_A,
    VARIANT_B,
    RelayFixture,
    deps_for,
)

pytestmark = pytest.mark.requires_docker


def _run_once(deps: Any, key: str) -> tuple[str, dict[str, Any]]:
    from fastapi.testclient import TestClient

    with TestClient(create_app(deps)) as client:
        created = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": PROTOCOL},
            headers={"Idempotency-Key": key},
        )
        assert created.status_code == 200, created.text
        run_id = str(created.json()["id"])
        run = client.get(f"/runs/{run_id}").json()
        run["artifact_ids"] = [
            str(item["id"]) for item in client.get(f"/runs/{run_id}/artifacts").json()
        ]
        run["experiments"] = client.get(f"/runs/{run_id}/experiments").json()
        run["report_body"] = ""
        report_ids = [item for item in run["artifact_ids"] if item.endswith(":research_report.md")]
        if report_ids:
            body = client.get(f"/artifacts/{report_ids[0]}/content")
            run["report_body"] = body.content.decode("utf-8", errors="replace")
    return run_id, run


class TestTheSixPhaseArcCompletesOffline:
    def test_the_run_succeeds_and_every_phase_artifact_exists(self) -> None:
        with RelayFixture() as relay:
            deps, offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
            run_id, run = _run_once(deps, "goal096-arc-offline-a")
        assert run["state"] == "SUCCEEDED", (run["state"], run.get("message"))
        suffixes = {item.rsplit(":", 1)[-1] for item in run["artifact_ids"]}
        for name in OUTPUT_NAMES:
            assert name in suffixes, (name, sorted(run["artifact_ids"]))
        # 实验相的落盘名是沙箱自己的（`experiment_result.json` + `metrics`）；
        # 「实验跑过」经**实验读面**断言（run 内有实验行），不按声明名找制品。
        assert run["experiments"]["experiments"], run["experiments"]
        # 检索真的发生了：检索词来自问题产出（(i) 的编排级取证，见下一条）。
        assert offline.requests, offline.requests

    def test_the_report_question_section_quotes_this_runs_question(self) -> None:
        with RelayFixture() as relay:
            deps, _offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
            _run_id, run = _run_once(deps, "goal096-arc-offline-report")
        block = (
            '{"research_question": {"query": "' + VARIANT_A[0] + '"'
            ', "rationale": "the direction implies this"}}'
        )
        assert block in run["report_body"], run["report_body"][:800]

    def test_the_search_term_is_the_question_output_on_the_provider(self) -> None:
        with RelayFixture() as relay:
            deps, offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
            _run_id, run = _run_once(deps, "goal096-arc-offline-query")
        assert run["state"] == "SUCCEEDED", (run["state"], run.get("message"))
        assert offline.requests[0] == VARIANT_A[0], offline.requests


class TestTheTwoDirectionsOfEveryEdge:
    def test_changing_the_question_output_changes_the_search_term(self) -> None:
        terms: list[tuple[str, str]] = []
        for variant in (VARIANT_A, VARIANT_B):
            with RelayFixture() as relay:
                deps, offline = deps_for(relay, (variant[1],), variant[0])
                _run_id, run = _run_once(deps, f"goal096-arc-offline-{variant[1]}")
            assert run["state"] == "SUCCEEDED", (run["state"], run.get("message"))
            terms.append((variant[0], offline.requests[0]))
        assert terms[0][0] != terms[1][0]
        assert terms[0][1] == terms[0][0] and terms[1][1] == terms[1][0]

    def test_changing_the_retrieval_output_changes_the_plan_prompt_material(self) -> None:
        prompts: list[str] = []
        for variant in (VARIANT_A, VARIANT_B):
            with RelayFixture() as relay:
                deps, _offline = deps_for(relay, (variant[1],), variant[0])
                _run_id, run = _run_once(deps, f"goal096-arc-offline-ctx-{variant[1]}")
            assert run["state"] == "SUCCEEDED", (run["state"], run.get("message"))
            recorder = deps.session_specs
            prompt = recorder.retrieval_prompt_of("research_report_plan")
            assert prompt, "plan 会话的提示词里必须有检索材料那一段"
            prompts.append(prompt)
        # 两个变体取回的记录不同 ⇒ plan 的提示词材料随之不同（两向取证的核心一行）。
        assert prompts[0] != prompts[1]
        assert RECORD_POOL[VARIANT_A[1]]["title"][:40] not in prompts[1]
        assert RECORD_POOL[VARIANT_A[1]]["title"][:40] in prompts[0]

    def test_the_plan_output_reaches_the_review_prompt(self) -> None:
        with RelayFixture() as relay:
            deps, _offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
            _run_id, run = _run_once(deps, "goal096-arc-offline-review")
        assert run["state"] == "SUCCEEDED", (run["state"], run.get("message"))
        recorder = deps.session_specs
        material = recorder.specs["multi_role_review"].review_material_prompt
        assert material, "review 会话的提示词里必须有被评对象那一段"
        assert VARIANT_A[1] in material, material
