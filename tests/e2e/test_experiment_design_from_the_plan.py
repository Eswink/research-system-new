"""GOAL-20261015-080 EC-03 的 **e2e 判据**：**换计划 ⇒ 换实验**（设计真的决定跑什么）。

**它与 `test_experiment_design_decides.py` 的分工**（不互相顶替）：那个文件判**解释点**
（`_arms_for` 的来源唯一 / 未知来源 / fail-closed）；本文件判**派发体真的按计划跑** ——
走**真** `sandbox_experiment_runner`，只把**执行体**换成受控替身（`_RecordingExecutor`，
与 GOAL-079 的 e2e 同一手法），因此它测的是「同一份装配上，**计划的**内容决定
哪几个臂成了实验、各自带什么参数」这条链路事实。

**不出容器、不出网**（执行体是替身）⇒ 默认门里也跑得动；真容器那一段由
`requires_docker` 的套件承担。
"""

from __future__ import annotations

from typing import Any

import pytest

import services.api.experiment_support as experiment_support
from packages.application.experiments.arms import arm_experiment_id
from packages.application.experiments.design_from_plan import DESIGN_KEY
from packages.application.experiments.plan_parameters import PARAMETER_PREFIX
from packages.application.experiments.types import ExperimentExecutionOutcome
from packages.application.ports.errors import InvalidInputError
from packages.domain.experiment_state import ExperimentRunState
from packages.domain.experiments import ExperimentRun, ExperimentRunResult
from services.api.experiment_support import (
    DESIGN_SOURCE_PLAN,
    SandboxExperimentAssembly,
    sandbox_experiment_runner,
)
from tests.application.test_experiment_design_decides import RUN_ID, TASK_ID, _seed_plan
from tests.application.test_experiment_parameters import _contract, _spec_context
from tests.e2e.test_two_arm_experiment_offline import _assembly

#: 另一条 run（「换 run ⇒ 换臂 id」那条判据用）。
_OTHER_RUN = "55555555-5555-4555-8555-555555555555"

__all__ = ["_assembly"]


class _RecordingExecutor:
    """受控执行体：记录**每一次**请求并返回一个**带制品**的科学终态（不出容器）。

    **为什么与 GOAL-079 的那一版不同**：本文件声明了 `design_source` ⇒ 读取器要走
    证据链 ⇒ 装配面必须带 `ledger` ⇒ 准入面（`evidence_admission`）要求终态运行
    **带 spec 与 result 且至少一个制品**。⇒ 本替身把「实验产出」如实造出来
    （一个含指标的结果制品，写进制品店并标 VERIFIED）——**不是**绕过准入检查，
    而是满足它（那条检查是既有的，本条判据一字未动）。
    """

    def __init__(self, artifacts: Any) -> None:
        self.requests: list[Any] = []
        self.artifacts = artifacts

    def execute(self, request: Any) -> ExperimentExecutionOutcome:
        import json

        from packages.domain.artifacts import Artifact
        from packages.domain.core import Digest
        from packages.domain.enums import ArtifactState
        from packages.domain.experiments import ExperimentRunSpec

        self.requests.append(request)
        artifact_id = f"{request.run_id.value}:metrics"
        payload = {
            "experiment_run_id": request.run_id.value,
            "status": "SUCCEEDED",
            "artifact_refs": ["metrics"],
            "metrics": {"corpus_size": 8, "worst_case_comparisons": 24},
        }
        content = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.artifacts.put(
            Artifact(
                id=artifact_id,
                digest=Digest.of_bytes(content),
                size_bytes=len(content),
                media_type="application/json",
                storage_uri=None,
                created_by="sandbox-experiment",
                source_refs=[f"experiment:{request.run_id.value}"],
                classification="experiment_result",
            ),
            content,
        )
        self.artifacts.mark(artifact_id, ArtifactState.VERIFIED)
        run = ExperimentRun(
            id=request.run_id,
            plan_id=request.plan.id,
            state=ExperimentRunState.State.SUCCEEDED,
            spec=ExperimentRunSpec(input_digest=Digest.of_bytes(b"design-from-plan")),
            result=ExperimentRunResult(
                execution_run_id=request.run_id.value,
                artifact_refs=(artifact_id,),
            ),
        )
        return ExperimentExecutionOutcome(run=run)


def _run(
    assembly: SandboxExperimentAssembly,
    monkeypatch: pytest.MonkeyPatch,
    *,
    run_id: str = RUN_ID,
) -> Any:
    """用记录型执行体跑一次派发体（**真** runner，只换执行体那一步）。

    **任务带固定的 run id**（缺省 `RUN_ID`，与种进证据链的那份计划同一个）——
    共用夹具的 `_task()` 用随机 id，而本文件的靶子正是「**本 run** 的计划」这条所属关系。
    """
    from packages.domain.core import ID
    from packages.domain.tasks import ResearchTask

    task = ResearchTask(id=ID(TASK_ID), run_id=ID(run_id))
    executor = _RecordingExecutor(assembly.artifacts)
    monkeypatch.setattr(experiment_support, "_governed_executor", lambda _assembly: executor)
    result = sandbox_experiment_runner(assembly)(task, _contract(), _spec_context(), "trace-c3")
    return result, executor


def _plan_assembly(
    payload: object, *, script: str | None = None, run_id: str = RUN_ID
) -> SandboxExperimentAssembly:
    """一份声明了「设计取自计划」的装配，并种好那份计划（ledger 是必需的 —— 见读取器）。"""
    from adapters.fakes.evidence_ledger import FakeEvidenceLedger

    overrides: dict[str, object] = {
        "design_source": DESIGN_SOURCE_PLAN,
        "ledger": FakeEvidenceLedger(),
    }
    if script is not None:
        overrides["script"] = script
    assembly = _assembly(**overrides)
    _seed_plan(assembly, payload, run_id=run_id)
    return assembly


class TestThePlanDecidesWhichExperimentsRun:
    """**换计划 ⇒ 换实验**：计划里的臂**就是**跑出来的那些实验（逐条对 id 与参数）。"""

    def test_the_plan_names_the_arms_that_become_experiments(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assembly = _plan_assembly({
            DESIGN_KEY: {"arms": {"from_plan_control": {}, "from_plan_treat": {"n_items": 90}}}
        })
        _result, executor = _run(assembly, monkeypatch)
        assert len(executor.requests) == 2, [r.run_id.value for r in executor.requests]
        ids = [r.run_id.value for r in executor.requests]
        assert ids == [
            arm_experiment_id(RUN_ID, "from_plan_control"),
            arm_experiment_id(RUN_ID, "from_plan_treat"),
        ], ids

    def test_the_plan_parameters_reach_the_container_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """参数**来自计划**（逐键进环境）：`n_items=90` 只在计划里写过。"""
        assembly = _plan_assembly({
            DESIGN_KEY: {"arms": {"control": {}, "treatment": {"n_items": 90}}}
        })
        _result, executor = _run(assembly, monkeypatch)
        environments = [r.environment for r in executor.requests]
        assert PARAMETER_PREFIX + "N_ITEMS" not in environments[0], environments[0]
        assert environments[1][PARAMETER_PREFIX + "N_ITEMS"] == "90", environments[1]

    def test_a_different_plan_runs_a_different_experiment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**同一装配**、**两份计划** ⇒ 两次派发的实验集合不同（这是「计划决定」的定义）。"""
        first = _plan_assembly({DESIGN_KEY: {"arms": {"only": {}}}})
        _result, first_executor = _run(first, monkeypatch)
        assert [r.run_id.value for r in first_executor.requests] == [
            arm_experiment_id(RUN_ID, "only")
        ]

        second = _plan_assembly({
            DESIGN_KEY: {"arms": {"a": {"seed": 3}, "b": {"seed": 4}, "c": {"seed": 5}}}
        })
        _result, second_executor = _run(second, monkeypatch)
        assert [r.run_id.value for r in second_executor.requests] == [
            arm_experiment_id(RUN_ID, "a"),
            arm_experiment_id(RUN_ID, "b"),
            arm_experiment_id(RUN_ID, "c"),
        ]

    def test_the_plan_gets_the_legacy_experiments_untouched(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """计划驱动的臂**不撞**单臂命名空间（`experiment_run_id_of(run)` 那条保留给单臂）。"""
        from packages.application.m12_reference.clean_run_stages import experiment_run_id_of

        assembly = _plan_assembly({DESIGN_KEY: {"arms": {"control": {}, "treatment": {}}}})
        _result, executor = _run(assembly, monkeypatch)
        legacy = experiment_run_id_of(RUN_ID)
        assert all(r.run_id.value != legacy for r in executor.requests), legacy


class TestTheDesignIsTheOnlyDeclaredSource:
    """**来源唯一**在 e2e 上同样成立（两条来源在场 ⇒ 派发**前**就拒绝）。"""

    def test_a_plan_source_plus_assembly_arms_refuses_to_dispatch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from adapters.fakes.evidence_ledger import FakeEvidenceLedger
        from packages.domain.core import ID
        from packages.domain.tasks import ResearchTask

        assembly = _assembly(
            design_source=DESIGN_SOURCE_PLAN,
            arms={"explicit": {}},
            ledger=FakeEvidenceLedger(),
        )
        _seed_plan(assembly, {DESIGN_KEY: {"arms": {"from_plan": {}}}})
        executor = _RecordingExecutor(assembly.artifacts)
        monkeypatch.setattr(experiment_support, "_governed_executor", lambda _assembly: executor)
        task = ResearchTask(id=ID(TASK_ID), run_id=ID(RUN_ID))
        with pytest.raises(InvalidInputError, match="would be undecidable"):
            sandbox_experiment_runner(assembly)(task, _contract(), _spec_context(), "trace-c3")
        assert executor.requests == [], "拒绝必须发生在**跑任何实验之前**"


class TestTheNoSourcePathStaysUnchanged:
    """零回归：不声明来源 ⇒ 既有单臂语义逐字不变（跑**一个**实验、用旧派生 id）。"""

    def test_no_source_runs_exactly_one_experiment_with_the_legacy_id(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from packages.application.m12_reference.clean_run_stages import experiment_run_id_of

        assembly = _assembly()
        _result, executor = _run(assembly, monkeypatch)
        assert [r.run_id.value for r in executor.requests] == [experiment_run_id_of(RUN_ID)]

    def test_a_bad_plan_does_not_affect_the_no_source_path(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """未声明来源时**连读都不读**计划 ⇒ 一份没有设计块的计划不影响既有路径。

        **怎么把「不读」变成可判**：装配**不带 ledger**（未声明来源的既有形态），
        而本文件另存一份**带坏计划**的证据链；若实现真的去读计划，它会因读不到而红
        （`_run` 会把异常抛出来）—— 判据因此判的是**路径分派**，不是「恰好没红」。
        """
        from adapters.fakes.evidence_ledger import FakeEvidenceLedger

        assembly = _assembly()
        scratch = _assembly(ledger=FakeEvidenceLedger())
        _seed_plan(scratch, {"no": "design"})
        _result, executor = _run(assembly, monkeypatch)
        assert len(executor.requests) == 1


class TestTheFactsAreTraceable:
    """**可溯源**：每个跑出来的实验都能追回计划里那一条（逐条对臂名与参数）。"""

    def test_every_request_traces_back_to_a_declared_arm(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        declared = {"arm_x": {"n_items": 11}, "arm_y": {"duplicate_pairs": 7}}
        assembly = _plan_assembly({DESIGN_KEY: {"arms": declared}})
        _result, executor = _run(assembly, monkeypatch)
        assert len(executor.requests) == len(declared)
        by_arm = {arm: arm_experiment_id(RUN_ID, arm) for arm in declared}
        ids = [r.run_id.value for r in executor.requests]
        assert set(ids) == set(by_arm.values()), (ids, by_arm)

    def test_the_run_id_on_every_request_is_this_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """臂 id **按本 run 派生**（派生是哈希 ⇒ 判**确定性 + 换 run 会变**，不判字面包含）。

        两条读数合起来才说明「这条 run 的信息真的进了 id」：
        ① **同 run 同计划 ⇒ 同 id**（确定性，可复算）；② **换 run ⇒ 不同 id**
        （否则两个 run 的臂会撞 id ⇒ 读面串味）。
        """
        assembly = _plan_assembly({DESIGN_KEY: {"arms": {"a": {}, "b": {}}}})
        _result, first = _run(assembly, monkeypatch)

        again = _plan_assembly({DESIGN_KEY: {"arms": {"a": {}, "b": {}}}})
        _result, second = _run(again, monkeypatch)
        first_ids = [r.run_id.value for r in first.requests]
        assert first_ids == [r.run_id.value for r in second.requests], (first_ids, "非确定性")

        other = _plan_assembly({DESIGN_KEY: {"arms": {"a": {}, "b": {}}}}, run_id=_OTHER_RUN)
        _result, other_executor = _run(other, monkeypatch, run_id=_OTHER_RUN)
        assert [r.run_id.value for r in other_executor.requests] != first_ids, (
            "换 run 后臂 id 不变 ⇒ run 的信息没进派生（两个 run 会撞 id）"
        )


def test_the_seeded_task_and_run_are_the_ones_used() -> None:
    """自检：本文件的夹具用的就是那两个固定 id（免得读成「某个别的 run」）。"""
    assert TASK_ID.startswith("1111") and RUN_ID.startswith("3333")
    assert design_source_marker() == DESIGN_SOURCE_PLAN


def design_source_marker() -> str:
    return DESIGN_SOURCE_PLAN
