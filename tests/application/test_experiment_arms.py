"""GOAL-20261015-079 EC-02 判据：**多臂/对照真跑**（臂由声明决定）。

**被测对象**：`experiments/arms.py` 的臂声明 + 装配面（`SandboxExperimentAssembly.arms`）
+ 派发体（`sandbox_experiment_runner` 逐臂各跑一次）。

**五件事逐条取证**：

1. **臂由声明决定**（不是按顺序猜）：`{臂名: 参数}` 与 `[{name, parameters}]` 两种声明形态
   都读得出；**重复臂名点名拒绝**（不静默取其 一）；形态不符点名拒绝；
2. **臂间实验 id 不同**（**建档实测的关键约束**）：既有 `experiment_run_id_of(run_id)`
   是**一 run 一实验**（两个臂会**撞同一个 id**）⇒ 臂用 `arm_experiment_id(run_id, arm)`
   （按 run + 臂确定性派生）；判据断言两臂 id 不同、且都**不等于**单臂那条；
3. **臂间参数不同**：`control` 不带参数（脚本回落缺省）、`treatment` 带声明参数
   ⇒ 环境里的参数键**逐臂可判**；
4. **臂的**计划**也不共用**：每个臂的计划 id 不同（同一个计划 id 被两臂复用会让
   「哪个计划属于哪个臂」不可判）；
5. **零回归**：未声明臂 ⇒ 单臂路径**逐字不变**（实验 id = `experiment_run_id_of(run_id)`、
   环境只有执行器自己的键）。
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from adapters.fakes.artifact_store import FakeArtifactStore
from packages.application.experiments.arms import (
    arm_experiment_id,
    declare_arms,
    parse_arms,
)
from packages.application.experiments.plan_parameters import PARAMETER_PREFIX
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import ID
from services.api.experiment_support import SandboxExperimentAssembly, _request_builder
from tests.application.test_experiment_parameters import _contract, _spec_context, _task


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


class TestTheArmsComeFromTheDeclaration:
    """① 臂由声明决定（两种形态 + 非法形态点名）。"""

    def test_a_mapping_declaration_names_the_arms_and_their_parameters(self) -> None:
        arms = parse_arms({"control": {}, "treatment": {"n_items": 120}})
        assert [(arm.name, dict(arm.parameters)) for arm in arms] == [
            ("control", {}),
            ("treatment", {"n_items": 120}),
        ], arms

    def test_an_explicit_list_declaration_carries_the_order(self) -> None:
        """显式形态携带**顺序**（主臂 = 第一个 ⇒ 顺序是语义的一部分）。"""
        arms = parse_arms([{"name": "b", "parameters": {"seed": 2}}, {"name": "a"}])
        assert [arm.name for arm in arms] == ["b", "a"], arms

    def test_a_duplicate_arm_name_is_refused(self) -> None:
        with pytest.raises(InvalidInputError, match="duplicate arm names"):
            parse_arms([{"name": "a"}, {"name": "a"}])

    def test_a_malformed_declaration_is_refused_by_name(self) -> None:
        with pytest.raises(InvalidInputError, match="mapping"):
            parse_arms(42)
        with pytest.raises(InvalidInputError, match="name"):
            parse_arms([{"parameters": {"seed": 1}}])
        with pytest.raises(InvalidInputError, match="parameters"):
            parse_arms([{"name": "a", "parameters": 3}])

    def test_no_declaration_means_no_arms(self) -> None:
        assert parse_arms(None) == ()
        assert parse_arms({}) == ()
        assert declare_arms(_assembly()) == ()


class TestTheArmsGetDistinctIdentities:
    """② 臂间实验 id 不同（**建档实测的关键约束**：既有派生是「一 run 一实验」）。"""

    def test_the_arm_ids_differ_and_avoid_the_single_arm_id(self) -> None:
        from packages.application.m12_reference.clean_run_stages import experiment_run_id_of

        run_id = str(uuid4())
        control = arm_experiment_id(run_id, "control")
        treatment = arm_experiment_id(run_id, "treatment")
        assert control != treatment, (control, treatment)
        assert experiment_run_id_of(run_id) not in {control, treatment}, (
            "臂的实验 id 不得撞上「整条 run 的单实验」那条既有 id",
        )

    def test_the_arm_ids_are_deterministic_and_are_valid_ids(self) -> None:
        run_id = str(uuid4())
        first = arm_experiment_id(run_id, "control")
        second = arm_experiment_id(run_id, "control")
        assert first == second, "按 run + 臂确定性派生（重启后可复算）"
        ID(first)  # 合法 UUID4 布局（域不变量）——不合法会在这一行抛

    def test_two_runs_do_not_collide_on_the_same_arm_name(self) -> None:
        first = arm_experiment_id(str(uuid4()), "control")
        second = arm_experiment_id(str(uuid4()), "control")
        assert first != second, (first, second)


class TestTheArmsDifferInParametersAndPlans:
    """③④ 臂间参数与计划**逐臂可判**。"""

    def _requests(self, **overrides: object) -> list[object]:
        assembly = _assembly(
            arms={"control": {}, "treatment": {"n_items": 120, "duplicate_pairs": 6}},
            **overrides,
        )
        arms = declare_arms(assembly)
        assert len(arms) == 2, arms
        return [
            _request_builder(assembly, arm=arm)(_task(), _contract(), _spec_context())
            for arm in arms
        ]

    def test_the_control_arm_gets_no_parameters_and_the_treatment_gets_its_own(self) -> None:
        control, treatment = self._requests()
        control_env = dict(control.environment)  # type: ignore[attr-defined]
        treatment_env = dict(treatment.environment)  # type: ignore[attr-defined]
        # 对照臂：只有执行器自己的键（脚本回落**既有缺省**）。
        assert set(control_env) == {"EXPERIMENT_RUN_ID"}, control_env
        # 处理臂：声明参数逐键在场。
        assert treatment_env.get(f"{PARAMETER_PREFIX}N_ITEMS") == "120", treatment_env
        assert treatment_env.get(f"{PARAMETER_PREFIX}DUPLICATE_PAIRS") == "6", treatment_env
        assert f"{PARAMETER_PREFIX}N_ITEMS" not in control_env, control_env

    def test_each_arm_carries_its_own_experiment_and_plan_id(self) -> None:
        control, treatment = self._requests()
        assert control.run_id != treatment.run_id, (control, treatment)  # type: ignore[attr-defined]
        assert control.plan.id != treatment.plan.id, (control.plan, treatment.plan)  # type: ignore[attr-defined]

    def test_assembly_defaults_merge_under_the_arm_parameters(self) -> None:
        """装配缺省 + 臂参数**合并**（臂可只给差异）；臂的键优先。"""
        control, treatment = self._requests(parameters={"seed": 3, "n_items": 999})
        control_env = dict(control.environment)  # type: ignore[attr-defined]
        treatment_env = dict(treatment.environment)  # type: ignore[attr-defined]
        assert control_env.get(f"{PARAMETER_PREFIX}SEED") == "3", control_env
        assert control_env.get(f"{PARAMETER_PREFIX}N_ITEMS") == "999", control_env
        assert treatment_env.get(f"{PARAMETER_PREFIX}SEED") == "3", treatment_env
        assert treatment_env.get(f"{PARAMETER_PREFIX}N_ITEMS") == "120", (
            "臂声明的键优先于装配缺省",
            treatment_env,
        )


class TestTheSingleArmPathIsUnchanged:
    """⑤ 零回归：未声明臂 ⇒ 既有单臂路径逐字不变。"""

    def test_the_single_arm_request_matches_the_legacy_derivation(self) -> None:
        from packages.application.m12_reference.clean_run_stages import experiment_run_id_of

        assembly = _assembly()
        task = _task()
        request = _request_builder(assembly)(task, _contract(), _spec_context())
        assert str(request.run_id.value) == experiment_run_id_of(str(task.run_id.value)), request
        assert set(request.environment) == {"EXPERIMENT_RUN_ID"}, request.environment

    def test_a_declared_arm_never_reuses_the_legacy_namespace(self) -> None:
        """有臂时**不**走既有派生（否则两臂会撞同一个实验 id）。"""
        from packages.application.m12_reference.clean_run_stages import experiment_run_id_of

        assembly = _assembly(arms={"only": {}})
        arm = declare_arms(assembly)[0]
        request = _request_builder(assembly, arm=arm)(_task(), _contract(), _spec_context())
        assert str(request.run_id.value) != experiment_run_id_of(str(_task().run_id.value))


def test_the_arm_name_is_part_of_the_derivation() -> None:
    """派生**含臂名**：换个名字 ⇒ 换个 id（否则「哪个臂」不可判）。"""
    run_id = str(uuid4())
    assert arm_experiment_id(run_id, "a") != arm_experiment_id(run_id, "b")
