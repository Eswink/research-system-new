"""GOAL-012 EC-02 的**离线**判据：实验执行链在真实 preflight / 冻结 / 编排路径上跑到底。

判的是**链**，不是容器本身（容器那一段由 `test_sandbox_experiment_seam_docker.py` 单独判）：

1. 主判据（出网零、容器真起）：`sort_analysis_v1` 经**既有 API**启动 ⇒ preflight 如实
   `WARN`（EXECUTE 风险）⇒ 冻结门按 GOAL-012 的**显式策略通道**接受 ⇒ 执行阶段的合约
   **声明了沙箱实验** ⇒ 派发到**既有 Docker 后端** ⇒ 验收门的 `ARTIFACT_EXISTS(analysis_report)`
   由容器产出的 `analysis_report` 满足 ⇒ review 阶段会话登记 ⇒ run 终态**恰为** `SUCCEEDED`；
   三项读面（实验产物 / 证据 / 预算）/ 一起可读。
2. 成对反证（先红后绿）：**撤掉** `code.execute` 的显式允许 ⇒ 同一条路径**拒冻**，run 终止在
   **执行之前**：零 task、零 experiment、零交付物。这条判的是「本 GOAL 的通道不是无条件放行」。

**W-B 的处置**（cycle 1 登记）：冻结之后的堵点是「会话结果无结构化输出」⇒
`register_session_result` **如实拒绝**（那是既有语义，本判据**不动**）。离线判据因此显式给
受控执行体**声明**它交付了什么——空手交付本来就该被拒，替它伪造才是错。

**挂 `requires_docker`**：主判据走真实装配（`DockerExecutionBackend` 构造即连 daemon），
在非 Linux 可用的 daemon 下如实 skip，由 `container-quality` 作业真跑。
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from tests.e2e.live_run_support import (
    EXPERIMENT_IMAGE,
    EXPERIMENT_SCRIPT,
    start_run,
    with_sandbox_experiment,
)

pytestmark = pytest.mark.requires_docker

_PROTOCOL = "sort_analysis_v1.yaml"
#: 受控执行体**声明**的会话交付物：review 阶段（`sort_analysis_review`）的会话结果。
#: 只有 review 阶段跑会话——执行阶段由合约声明交给沙箱实验（`dispatch_experiment`）。
_REVIEW_DELIVERABLE: dict[str, object] = {
    "review_decision": {
        "verdict": "ACCEPT",
        "rationale": "controlled fake session output (offline EC-02 chain)",
    }
}


def _deps() -> Any:
    """run-ready 装配 + 实验缝 + **会交付**的受控执行体（三者同一装配，缺一不可）。"""
    from adapters.fakes.agent_runtime import FakeAgentRuntime
    from tests.api.run_fixtures import make_run_ready_deps

    deps = make_run_ready_deps()
    with_sandbox_experiment(
        deps,
        script=EXPERIMENT_SCRIPT,
        image=EXPERIMENT_IMAGE,
        runtime=FakeAgentRuntime(structured_output=_REVIEW_DELIVERABLE),
    )
    return deps


def test_the_declared_experiment_chain_runs_to_a_successful_terminal() -> None:
    """主干：WARN ⇒ 显式允许 ⇒ 冻结 ⇒ 沙箱实验 ⇒ 验收门 ⇒ `SUCCEEDED`（三项读面齐备）。"""
    from fastapi.testclient import TestClient

    from services.api.app import create_app

    deps = _deps()
    with TestClient(create_app(deps)) as client:
        run = start_run(client, _PROTOCOL)
        run_id = str(run["id"])
        assert run["manifest_digest"], ("冻结必须真的发生（GOAL-012 EC-01）", run)
        detail = client.get(f"/runs/{run_id}").json()
        assert detail["state"] == "SUCCEEDED", (
            "只有 SUCCEEDED 是成功（FAILED 也是终态，但不是通过）",
            detail,
            _tasks(client, run_id),
        )

        experiment = _experiments(client, run_id)
        _assert_experiment_products(experiment)
        _assert_evidence(client, run_id)
        _assert_budget(client, run_id)


def test_withdrawing_the_allowance_stops_the_run_before_anything_executes() -> None:
    """**成对反证**：撤掉显式允许 ⇒ 拒冻 ⇒ 零 task / 零 experiment / 无 digest。"""
    from fastapi.testclient import TestClient

    from packages.domain.enums import PolicyDecision
    from services.api.app import create_app

    deps = _deps()
    evaluator = deps.preflight_override.policy_evaluator
    evaluator.set_decision("code.execute", PolicyDecision.REQUIRE_APPROVAL)
    with TestClient(create_app(deps)) as client:
        run = start_run(client, _PROTOCOL)
        run_id = str(run["id"])
        assert run["state"] == "FAILED", run
        assert run["manifest_digest"] is None, "未获允许即不得冻结"
        assert _tasks(client, run_id) == [], "执行前终止：不得留下 task"
        assert _experiments(client, run_id)["experiments"] == [], "执行前终止：不得起实验"


def _tasks(client: Any, run_id: str) -> list[dict[str, Any]]:
    return list(client.get(f"/runs/{run_id}/tasks").json())


def _experiments(client: Any, run_id: str) -> dict[str, Any]:
    return dict(client.get(f"/runs/{run_id}/experiments").json())


def _assert_experiment_products(view: dict[str, Any]) -> None:
    """读面段 1：实验产物可读，且产物**来自容器**（镜像摘要 + 声明的交付物名）。"""
    experiments = view["experiments"]
    assert len(experiments) == 1, view
    experiment = experiments[0]
    assert experiment["image_digest"], experiment
    assert experiment["environment_digest"], experiment
    names = {str(item).rsplit(":", 1)[-1] for item in experiment["artifact_ids"]}
    assert "analysis_report" in names, ("验收门判的就是它", names)
    assert "experiment_result.json" in names, names
    # 指标名由**被执行的脚本**决定（`examples/experiments/sort_analysis_baseline.py`：
    # 确定性排序基线的语料规模与比较次数），不是别处实验的指标名。
    metrics = experiment["metrics"]
    assert {"corpus_size", "worst_case_comparisons"} <= set(metrics), metrics


def _assert_evidence(client: Any, run_id: str) -> None:
    """读面段 2：证据可读，且证据指向本 run 的制品（不是空读面）。"""
    evidence = client.get(f"/runs/{run_id}/evidence").json()
    assert evidence, "实验证据必须可读"
    assert all(item["artifact_id"] for item in evidence), evidence
    artifact_ids = {str(item["artifact_id"]) for item in evidence}
    assert any(item.endswith(":experiment_result.json") for item in artifact_ids), artifact_ids


def _assert_budget(client: Any, run_id: str) -> None:
    """读面段 3：预算归账可读（不把 UNKNOWN 补齐成 0——本判据只要求面能读且自洽）。"""
    usage = client.get(f"/runs/{run_id}/usage").json()
    assert isinstance(usage["entries"], list), usage
    assert usage["unknown_cost_entries"] >= 0, usage
    assert usage["entries"] or usage["unknown_cost_entries"] > 0, (
        "要么有归账条目，要么如实登记了未定价条目——空且零未知是「没记账」的伪装",
        usage,
    )
    assert json.dumps(usage)  # 可序列化（读面契约）
