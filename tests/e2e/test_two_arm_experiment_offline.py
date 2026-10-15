"""GOAL-20261015-079 EC-02 的 **e2e 判据**：多臂实验经**产品装配**真跑。

**它与 `test_experiment_arms.py` 的分工**（不互相顶替，承 MEM-159）：
那个文件判**声明面与请求面**（臂怎么解析、id 怎么派生、参数怎么合并）；
本文件判**派发体真的逐臂各跑一次** —— 走**真** `sandbox_experiment_runner`，
只把**执行体**换成受控替身（`GovernedExperimentExecutor` 内部那一步），
因此它测的是「同一个装配上，两个臂各自成为一次实验」这条链路事实。

**为什么不跑真容器**：本判据的靶子是**臂编排**，不是容器；容器那一段由
`requires_docker` 的套件承担（`test_ec02_experiment_chain_offline` /
`test_sandbox_experiment_seam_docker`）。
本文件**不出容器、不出网**，因此它在默认门里也跑得动。
"""

from __future__ import annotations

from typing import Any

import pytest

import services.api.experiment_support as experiment_support
from adapters.fakes.artifact_store import FakeArtifactStore
from packages.application.experiments.plan_parameters import PARAMETER_PREFIX
from packages.application.experiments.types import ExperimentExecutionOutcome
from packages.domain.experiment_state import ExperimentRunState
from packages.domain.experiments import ExperimentRun, ExperimentRunResult
from services.api.experiment_support import (
    SandboxExperimentAssembly,
    sandbox_experiment_runner,
)
from tests.application.test_experiment_parameters import _contract, _spec_context, _task

# `mock_relay` 夹具与既有离线 e2e 同源（同一套装配，避免两处各写一份）。
from tests.e2e.test_ec03_real_runtime_offline_chain import mock_relay

__all__ = ["mock_relay"]


class _RecordingExecutor:
    """受控执行体：记录**每一次**请求并返回一个科学终态（不出容器）。"""

    def __init__(self) -> None:
        self.requests: list[Any] = []

    def execute(self, request: Any) -> ExperimentExecutionOutcome:
        self.requests.append(request)
        run = ExperimentRun(
            id=request.run_id,
            plan_id=request.plan.id,
            state=ExperimentRunState.State.SUCCEEDED,
            spec=None,
            result=ExperimentRunResult(execution_run_id=request.run_id.value),
        )
        return ExperimentExecutionOutcome(run=run)


def _assembly(**overrides: object) -> SandboxExperimentAssembly:
    base: dict[str, object] = {
        "execution": object(),
        "artifacts": FakeArtifactStore(),
        "policy": object(),
        "image": "research-os-sandbox:m9-test",
        "script": "examples/experiments/exact_match_index_benchmark.py",
    }
    base.update(overrides)
    return SandboxExperimentAssembly(**base)  # type: ignore[arg-type]


def _run(assembly: SandboxExperimentAssembly, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, Any]:
    """用记录型执行体跑一次派发体（**真** runner，只换执行体那一步）。"""
    executor = _RecordingExecutor()
    monkeypatch.setattr(experiment_support, "_governed_executor", lambda _assembly: executor)
    result = sandbox_experiment_runner(assembly)(
        _task(), _contract(), _spec_context(), "trace-arms"
    )
    return result, executor


class TestTwoArmsReallyRun:
    """① 声明两个臂 ⇒ **两次**实验（各自请求、各自实验 id）。"""

    def test_two_declared_arms_produce_two_distinct_experiments(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assembly = _assembly(arms={"control": {}, "treatment": {"n_items": 120}})
        result, executor = _run(assembly, monkeypatch)

        assert result.outcome == "SUCCEEDED", (result.outcome, result.message)
        assert len(executor.requests) == 2, [r.run_id.value for r in executor.requests]
        ids = [request.run_id.value for request in executor.requests]
        assert len(set(ids)) == 2, ids
        # 计划也不共用（同一个计划 id 被两臂复用会让「哪个计划属于哪个臂」不可判）。
        plan_ids = [request.plan.id.value for request in executor.requests]
        assert len(set(plan_ids)) == 2, plan_ids

    def test_the_arm_parameters_land_on_the_right_arm(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**逐臂**：对照臂无参数（脚本回落缺省）、处理臂带声明参数。"""
        assembly = _assembly(arms={"control": {}, "treatment": {"n_items": 120}})
        _result, executor = _run(assembly, monkeypatch)
        by_params = [
            sorted(key for key in request.environment if key.startswith(PARAMETER_PREFIX))
            for request in executor.requests
        ]
        assert by_params[0] == [], by_params
        assert by_params[1] == [f"{PARAMETER_PREFIX}N_ITEMS"], by_params
        assert executor.requests[1].environment[f"{PARAMETER_PREFIX}N_ITEMS"] == "120", (
            executor.requests[1].environment
        )

    def test_the_message_names_every_arm(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """结果消息**点名全部臂**（读消息的人不必回查读面也知道跑了几个）。"""
        assembly = _assembly(arms={"control": {}, "treatment": {}})
        result, executor = _run(assembly, monkeypatch)
        assert "(arms: " in result.message, result.message
        for request in executor.requests:
            assert request.run_id.value in result.message, (request.run_id.value, result.message)


class TestTheRefutationArm:
    """② 反证：**只声明一个臂** ⇒ 只有一次实验（「两臂」不是无条件成立的）。"""

    def test_a_single_declared_arm_runs_once(self, monkeypatch: pytest.MonkeyPatch) -> None:
        assembly = _assembly(arms={"only": {}})
        result, executor = _run(assembly, monkeypatch)
        assert result.outcome == "SUCCEEDED", result.message
        assert len(executor.requests) == 1, [r.run_id.value for r in executor.requests]


class TestTheNoArmPathIsUnchanged:
    """③ 零回归：未声明臂 ⇒ 单臂路径（一次实验、既有实验 id）。"""

    def test_no_declaration_runs_exactly_one_experiment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from packages.application.m12_reference.clean_run_stages import experiment_run_id_of

        assembly = _assembly()
        task = _task()
        executor = _RecordingExecutor()
        monkeypatch.setattr(experiment_support, "_governed_executor", lambda _assembly: executor)
        result = sandbox_experiment_runner(assembly)(task, _contract(), _spec_context(), "trace-1")

        assert result.outcome == "SUCCEEDED", result.message
        assert len(executor.requests) == 1, executor.requests
        assert executor.requests[0].run_id.value == experiment_run_id_of(str(task.run_id.value)), (
            "未声明臂 ⇒ 实验 id 逐字沿用既有派生",
        )
        assert "(arms: " not in result.message, result.message


@pytest.mark.requires_docker
class TestTheTwoArmsLandOnTheRunReadFace:
    """④ 经**产品路径**的一次 run：两个臂各自落库，读面上逐臂可读（**真容器**）。"""

    def _run_with_arms(self, mock_relay: str) -> tuple[Any, dict[str, Any], list[dict[str, Any]]]:
        """跑一次带两个臂的 run（既有协议 + 既有装配，只加臂声明）。"""
        from dataclasses import replace

        from fastapi.testclient import TestClient

        from packages.application.run_orchestration.service import RunOrchestrationService
        from services.api.app import create_app
        from services.api.assembly import policy_bindings
        from services.api.experiment_support import (
            docker_experiment_assembly,
            sandbox_experiment_runner,
        )
        from tests.e2e.literature_chain_support import OfflineEuropePmc
        from tests.e2e.live_run_support import start_run
        from tests.e2e.test_research_report_arc_offline import _PROTOCOL, _assembled_deps

        deps, _recorder = _assembled_deps(mock_relay, OfflineEuropePmc(requests=[]))
        policy = policy_bindings().get("policy_evaluator")
        assert policy is not None, "policy.yaml must be loadable for the two-arm experiment"
        runner = sandbox_experiment_runner(
            docker_experiment_assembly(
                artifacts=deps.artifacts,
                ledger=deps.ledger,
                policy=policy,
                script="examples/experiments/exact_match_index_benchmark.py",
                image="research-os-sandbox:m9-test",
                experiment_store=deps.experiment_store,
                arms={"control": {}, "treatment": {"n_items": 120}},
            )
        )
        deps.runs = RunOrchestrationService(replace(deps.runs._deps, experiment_task=runner))
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            run_id = str(run["id"])
            detail = client.get(f"/runs/{run_id}").json()
            experiments = list(client.get(f"/runs/{run_id}/experiments").json()["experiments"])
        return deps, detail, experiments

    def test_both_arms_are_recorded_and_their_metrics_differ(self, mock_relay: str) -> None:
        _deps, detail, experiments = self._run_with_arms(mock_relay)

        assert detail["state"] == "SUCCEEDED", detail
        assert len(experiments) == 2, [e["experiment_run_id"] for e in experiments]
        ids = [str(item["experiment_run_id"]) for item in experiments]
        assert len(set(ids)) == 2, ids
        # **逐臂的指标各自落库**，且**两臂的值不同**（同一指标、不同参数 ⇒ 不同读数）。
        ratios = [
            (item.get("metrics") or {}).get("comparison_reduction_ratio") for item in experiments
        ]
        assert all(value is not None for value in ratios), ratios
        assert ratios[0] != ratios[1], (
            "两臂的参数不同 ⇒ 同一指标的落库值必须不同（否则「臂」没有生效）",
            ratios,
        )
        # 每条记录都带镜像指纹（制品来自容器，不是桩）与制品清单。
        for item in experiments:
            assert item["image_digest"], item
            assert item["artifact_ids"], item
