"""GOAL-20261026-097 EC-03：契约 pin 的 `script` / `image` **真的生效**（声明优先，装配面兜底）。

**它补哪一格**（本轮建档实测）：`ExperimentExecutionSpec` 的 docstring 逐字写「给了就**必须**
照用（装配方不得覆盖契约 pin 的量）」，而 `services/api/experiment_support.py` 的
`_request_builder` 只读 `declaration.command` 与 `declaration.timeout_seconds` ——
`rg "declaration\\.(script|image)" services/ packages/` **零命中**。后果：
`examples/contracts/task_contracts.yaml` 里 `m12_experiment_execution` pin 的
`script: examples/experiments/m12_reference_classification.py` +
`image: research-os-sandbox:m9-test` **从未生效**（装配面给什么就跑什么）。

**两向 + 一反证**（缺一即判红）：

1. 契约 pin 了 ⇒ 用契约的（**按压**：改契约里的路径 ⇒ 解析结果随之变 —— 不是「恰好等于」）；
2. 契约空（`experiment_execution: {}` 的既有语义）⇒ **逐字**回到装配面（既有行为不变）；
3. 反证：摘掉「声明优先」分支 ⇒ 判据**点名**判红。

判据只读**解析函数**（纯函数、零 Docker、零出网）与**出厂契约文件**，不起容器。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

from packages.domain.tasks import ExperimentExecutionSpec, TaskContract
from services.api.experiment_support import (
    SandboxExperimentAssembly,
    declared_or_assembled,
)

_ROOT = Path(__file__).resolve().parents[2]
_CONTRACTS = _ROOT / "examples" / "contracts" / "task_contracts.yaml"
_SUPPORT = _ROOT / "services" / "api" / "experiment_support.py"
#: 出厂契约里**真的 pin 了**脚本/镜像的那一份（建档实测只有它）。
_PINNED_CONTRACT = "m12_experiment_execution"
#: 出厂契约里声明为空映射的那一份（`experiment: {}`）。
_EMPTY_CONTRACT = "experiment_execution"


def _assembly(script: Any = "assembly-default.py", image: str = "assembly:default") -> Any:
    return SandboxExperimentAssembly(
        execution=None,
        execution_factory=lambda image: None,
        artifacts=None,
        policy=None,
        image=image,
        script=script,
    )


def _contract(experiment: ExperimentExecutionSpec) -> TaskContract:
    from packages.domain.enums import AcceptanceCriterionType
    from packages.domain.tasks import AcceptanceCriterion

    return TaskContract(
        id="probe",
        version="1.0.0",
        purpose="probe",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.TEST_PASSES)],
        experiment=experiment,
    )


def test_a_pinned_contract_decides_the_script_and_image() -> None:
    """(1) 契约 pin 了 ⇒ 用契约的（两件都换）。"""
    script, image = declared_or_assembled(
        _assembly(),
        _contract(ExperimentExecutionSpec(script="pinned.py", image="pinned:1")),
    )
    assert (script, image) == ("pinned.py", "pinned:1")


def test_pressing_the_pinned_path_moves_the_answer() -> None:
    """(1) 的**按压**：改契约里的路径 ⇒ 解析结果跟着变（不是常量巧合）。"""
    first = declared_or_assembled(
        _assembly(), _contract(ExperimentExecutionSpec(script="a.py", image="a:1"))
    )
    second = declared_or_assembled(
        _assembly(), _contract(ExperimentExecutionSpec(script="b.py", image="b:2"))
    )
    assert first != second
    assert second == ("b.py", "b:2")


def test_an_empty_declaration_falls_back_to_the_assembly_verbatim() -> None:
    """(2) 契约空 ⇒ **逐字**回到装配面（既有行为不变）。"""
    script, image = declared_or_assembled(_assembly(), _contract(ExperimentExecutionSpec()))
    assert (script, image) == ("assembly-default.py", "assembly:default")


def test_the_two_fields_are_decided_independently() -> None:
    """只 pin 其中一个字段 ⇒ 另一个仍用装配面的（**各自独立**，不是整块二选一）。"""
    script, image = declared_or_assembled(
        _assembly(), _contract(ExperimentExecutionSpec(script="only-script.py"))
    )
    assert (script, image) == ("only-script.py", "assembly:default")


def test_an_assembly_without_a_script_stays_without_one() -> None:
    """装配面也没脚本（组合根的形态）⇒ 仍返回 `None`（不猜一个脚本）。"""
    script, image = declared_or_assembled(
        _assembly(script=None), _contract(ExperimentExecutionSpec())
    )
    assert script is None
    assert image == "assembly:default"


def test_the_shipped_contracts_mean_what_they_say() -> None:
    """出厂契约面：pin 的那份真的有值，空的那份真的是空映射（判据不靠手写常量）。"""
    contracts: Any = yaml.safe_load(_CONTRACTS.read_text(encoding="utf-8"))["task_contracts"]
    pinned = contracts[_PINNED_CONTRACT]["experiment"]
    assert pinned["script"] == "examples/experiments/m12_reference_classification.py"
    assert pinned["image"] == "research-os-sandbox:m9-test"
    assert contracts[_EMPTY_CONTRACT]["experiment"] == {}


def test_the_pinned_script_exists_in_the_tree() -> None:
    """pin 的脚本**在树**里（pin 一个不存在的文件等于没 pin）。"""
    contracts: Any = yaml.safe_load(_CONTRACTS.read_text(encoding="utf-8"))["task_contracts"]
    pinned = contracts[_PINNED_CONTRACT]["experiment"]["script"]
    assert (_ROOT / pinned).is_file(), pinned


def test_removing_the_declaration_priority_is_named_red() -> None:
    """(3) 反证：摘掉「声明优先」分支 ⇒ 判据**点名**判红。

    按压的是**函数体**（源码文本），断言的仍是**行为**：按压后的函数对 pin 了脚本的契约
    会返回装配面的值。判词点名「契约 pin 的 script 被装配面覆盖」。
    """
    source = _SUPPORT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    target = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "declared_or_assembled"
    )
    block = ast.get_source_segment(source, target)
    assert block is not None
    assert "declaration.script or script" in block, (
        "declared_or_assembled 里没有「声明优先」那一行 —— EC-03 的核心分支不在"
    )
    # 按压：把「声明优先」换成「装配面优先」——行为必须随之改变（否则那行是死代码）。
    pressed = block.replace("declaration.script or script", "script")
    namespace: dict[str, Any] = {"TaskContract": TaskContract}
    exec(compile(pressed, "<pressed>", "exec"), namespace)  # noqa: S102 - 判据内部的按压执行
    pressed_fn = cast(Any, namespace["declared_or_assembled"])
    with_assembly_first = pressed_fn(
        _assembly(), _contract(ExperimentExecutionSpec(script="pinned.py"))
    )
    assert with_assembly_first[0] == "assembly-default.py", (
        "按压后仍返回契约的值 ⇒ 「声明优先」那行没有被判据咬住"
    )
    assert with_assembly_first[0] != "pinned.py"


def test_the_runner_really_uses_the_resolved_values(monkeypatch: Any) -> None:
    """(1)+(2) 的**装配面取证**：派发器把解析后的脚本/镜像真的交给了执行体。

    判据不真跑容器：把 `_governed_executor` 换成一个记录参数的替身，断言它收到的
    `assembly.script` / `assembly.image` 是**解析后**的值（不是构造时的原始值）。
    """
    from services.api import experiment_support as support

    seen: list[tuple[Any, Any]] = []

    class _Stop(Exception):
        pass

    def fake_governed(assembly: Any, *, execution: Any = None) -> Any:
        seen.append((assembly.script, assembly.image))
        raise _Stop

    monkeypatch.setattr(support, "_governed_executor", fake_governed)
    runner = support.sandbox_experiment_runner(_assembly())
    with pytest.raises(_Stop):
        runner(
            _task(),
            _contract(ExperimentExecutionSpec(script="pinned.py", image="pinned:1")),
            _spec_context(),
            "trace-ec03",
        )
    assert seen == [("pinned.py", "pinned:1")], seen


def _task() -> Any:
    from packages.domain.core import ID
    from packages.domain.tasks import ResearchTask

    return ResearchTask(
        id=ID("3c4d5e6f-7a8b-4c9d-8e0f-1a2b3c4d5e6f"),
        run_id=ID("4d5e6f7a-8b9c-4d0e-9f1a-2b3c4d5e6f70"),
    )


def _spec_context() -> Any:
    from types import SimpleNamespace

    return SimpleNamespace(phase_id="experiment", role=SimpleNamespace(review_panel_role=None))
