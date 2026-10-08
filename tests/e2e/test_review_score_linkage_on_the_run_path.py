"""GOAL-20261008-035 EC-03 判据：**评审结论进入判据面**（`REVIEW_SCORE` 三态 + 反证）。

靶子（EC-03 (c)(d)）：出厂合约 `review_scored_deliverable` 声明 `REVIEW_SCORE`
（`metric: review_decision.score`，`operator: GTE`，`threshold: 0.8`），实跑时：

- ① **判过**：分数 ≥ 阈值 ⇒ 验收门 `PASS`，判词**逐字**给出分数与阈值；
- ② **判负**：分数 < 阈值 ⇒ `REJECT`，判词**点名那个分数**（不是笼统「评审不通过」）；
- ③ **缺来源**：结构化输出里没有那条被声明的路径 ⇒ 维持既有 fail-closed 判词
  `review score unknown` —— **不得**回落到默认分（「没有评审结论」与「评审结论很差」
  是相反的两件事）。

判词经**既有读面**读（`GET /runs/{id}/reviews`，GOAL-035 EC-01 建的）——不是读内部对象。

**为什么另立协议**（`review_scored_research_v1.yaml`）：给 `sort_analysis_review` 加这条判据
会让多条既有判据的夹具（其评审输出没有分数）连环判负 ⇒ 那是改既有受判面。

**如实边界**：分数来源是**评审交付物自己给的那个数**（模型自述的评审结论）——本判据证明的是
「结论能进判据面且三态可判」，**不是**「分数一定正确」。真实控制面那一次不在本文件范围。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.api.run_fixtures import make_run_ready_deps
from tests.e2e.live_run_support import start_run
from tests.e2e.scenario import StructuredOutputAgentRuntime

_PROTOCOL = "review_scored_research_v1.yaml"
_THRESHOLD = "0.8"


def _deps_with_review(result: dict[str, Any]) -> Any:
    """受控执行体**声明**它交付了什么（分数来自它）；其余走 run-ready 装配。"""
    from packages.application.run_orchestration.service import RunOrchestrationService

    deps = make_run_ready_deps()
    old = deps.runs
    assert old is not None
    deps.runs = RunOrchestrationService(
        replace(old._deps, runtime=StructuredOutputAgentRuntime(structured_output=result))
    )
    return deps


def _run_and_read(result: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    with TestClient(create_app(_deps_with_review(result))) as client:
        run = start_run(client, _PROTOCOL)
        reviews = client.get(f"/runs/{run['id']}/reviews").json()
    return run, reviews


def _review_line(reviews: list[dict[str, Any]]) -> str:
    lines = [line for line in reviews[0]["findings"] if line.startswith("REVIEW_SCORE: ")]
    assert len(lines) == 1, reviews
    return str(lines[0])


def test_the_declared_review_score_is_judged_and_readable() -> None:
    """① 判过：分数 ≥ 阈值 ⇒ `PASS`，判词逐字给出分数与阈值。"""
    run, reviews = _run_and_read({"review_decision": {"verdict": "ACCEPT", "score": 0.95}})
    assert run["state"] == "SUCCEEDED", (run, reviews)
    assert len(reviews) == 1, reviews
    assert reviews[0]["verdict"] == "PASS", reviews[0]
    down = _review_line(reviews)
    assert f"review score 0.95 GTE {_THRESHOLD}" in down, down


def test_a_below_threshold_score_rejects_and_names_the_score() -> None:
    """② 判负：分数 < 阈值 ⇒ `REJECT` 且判词点名那个分数（不是笼统判负）。"""
    run, reviews = _run_and_read({"review_decision": {"verdict": "ACCEPT", "score": 0.5}})
    assert run["state"] == "FAILED", (run, reviews)
    assert reviews[0]["verdict"] == "REJECT", reviews[0]
    down = _review_line(reviews)
    assert f"review score 0.5 GTE {_THRESHOLD}" in down, down


def test_a_missing_score_stays_fail_closed_and_never_defaults() -> None:
    """③ 缺来源：没有那条被声明的路径 ⇒ 既有 fail-closed 判词（**不**回落默认分）。"""
    run, reviews = _run_and_read({"review_decision": {"verdict": "ACCEPT"}})
    assert run["state"] == "FAILED", (run, reviews)
    assert reviews[0]["verdict"] == "REJECT", reviews[0]
    down = _review_line(reviews)
    assert "review score unknown" in down, down
    # 反证面：判词里**不得**出现任何数字分数（回落默认分会让它出现）
    assert "GTE" not in down, down
