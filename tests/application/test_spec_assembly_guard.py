"""装配面异常边界的判据（GOAL-20261111-108 EC-04）。

**它封住的失败形态**：`phase_runner._run_group_task` 的五个 spec helper 全在任务级
`try` 之外，而 `phase_runner.py` 与 `service.py` **全无 try/except** ⇒ 任一 helper 抛错
穿透整条栈，`run.failed` 发不出、`save_run` 也不跑 ⇒ **静默停住**（GOAL-106 `F-17`：
`phase.started(revision)` 之后一条事件都没有）。

四条臂（缺一即判空）：① 成功路径产物 `is` 相同；② 抛错时返回点名的错误；
③ `assemble_spec` 是**链式**的（第二步看到第一步的产物）；④ 失败走 `deps.fail`。
"""

from __future__ import annotations

from typing import Any

import pytest

from packages.application.run_orchestration.spec_assembly_guard import (
    SpecAssemblyError,
    assemble_spec,
    fail_on_assembly_error,
    guarded_assembly,
)


def test_the_success_path_returns_the_same_object() -> None:
    """① 无异常时**不新造对象** —— 既有行为逐字不变。"""
    sentinel = object()
    value, error = guarded_assembly("noop", lambda: sentinel)
    assert error is None
    assert value is sentinel


def test_a_raising_step_names_itself() -> None:
    """② 抛错 ⇒ `(None, SpecAssemblyError)`，判词点名声明的**那一步**。"""

    def boom() -> None:
        raise ValueError("ledger table is missing")

    value, error = guarded_assembly("with_review_outcome", boom)
    assert value is None
    assert isinstance(error, SpecAssemblyError)
    assert "with_review_outcome" in str(error)
    assert "ValueError" in str(error)
    assert "ledger table is missing" in str(error)


def test_assembly_is_chained_not_parallel() -> None:
    """③ **链式**：第二步收到的是第一步的产物（不是最初那个）。

    这一条防的是「五个 helper 各自基于同一个原始 spec」这种错误实现 —— 那会让
    后四步全部丢掉前一步的落点，而且**不会抛错**。
    """
    seen: list[int] = []

    def step_one(deps: Any, task: Any, spec: int) -> int:
        del deps, task
        seen.append(spec)
        return spec + 1

    def step_two(deps: Any, task: Any, spec: int) -> int:
        del deps, task
        seen.append(spec)
        return spec * 10

    value, error = assemble_spec(None, None, 1, (("one", step_one), ("two", step_two)))
    assert error is None
    assert seen == [1, 2], f"第二步看到的是 {seen}，说明没有链式传递"
    assert value == 20


def test_a_failing_step_in_the_chain_stops_there() -> None:
    """③b 链中途抛错 ⇒ 后续步骤**不执行**（不静默跳过、不继续跑）。"""
    ran: list[str] = []

    def ok(deps: Any, task: Any, spec: object) -> object:
        del deps, task
        ran.append("ok")
        return spec

    def bad(deps: Any, task: Any, spec: object) -> object:
        del deps, task
        ran.append("bad")
        raise RuntimeError("nope")

    def never(deps: Any, task: Any, spec: object) -> object:
        del deps, task
        ran.append("never")
        return spec

    value, error = assemble_spec(None, None, object(), (("ok", ok), ("bad", bad), ("never", never)))
    assert value is None
    assert error is not None and "bad" in str(error)
    assert ran == ["ok", "bad"], f"失败后仍在跑：{ran}"


def test_the_failure_goes_through_the_existing_fork() -> None:
    """④ 失败**走 `deps.fail`**（既有唯一出口），且 `system_failure=True`。"""

    class _Deps:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, bool]] = []

        def fail(self, run_id: str, message: str, system_failure: bool) -> str:
            self.calls.append((run_id, message, system_failure))
            return "RunOutcome"

    class _Ctx:
        run_id = "run-1"

    class _Task:
        class id:  # noqa: N801 - 模拟 `ID` 的 `.value`
            value = "task-1"

    deps = _Deps()
    error = SpecAssemblyError("spec assembly step 'x' raised ValueError: boom")
    outcome = fail_on_assembly_error(deps, _Ctx(), _Task(), error)

    assert isinstance(outcome, str)
    assert outcome == "RunOutcome"
    assert len(deps.calls) == 1
    run_id, message, system_failure = deps.calls[0]
    assert run_id == "run-1"
    assert "task-1" in message and "x" in message
    assert system_failure is True, "装配失败是基础设施问题，不是被评对象不合格"


def test_an_empty_chain_returns_the_input_unchanged() -> None:
    """边界：空 `steps` ⇒ **原样返回入参**，不崩、不新造。

    语义是「没有步骤要跑 = spec 不变」—— 而不是「装配结果为空」。后者会让调用方
    把「没有槽位可挂」误读成「装配失败」。
    """
    seed = object()
    value, error = assemble_spec(None, None, seed, ())
    assert error is None
    assert value is seed


def _adder(increment: int) -> Any:
    """返回一个把 spec 加上 `increment` 的 helper（避免内联 lambda 的类型推断问题）。"""

    def helper(deps: Any, task: Any, spec: int) -> int:
        del deps, task
        return spec + increment

    return helper


@pytest.mark.parametrize("helper_count", [1, 3, 5])
def test_the_chain_handles_any_length(helper_count: int) -> None:
    """arity：1 / 3 / 5 步都要成立（五步是本轮的真实用法）。"""
    steps = tuple((f"step{n}", _adder(n)) for n in range(helper_count))
    value, error = assemble_spec(None, None, 0, steps)
    assert error is None
    assert value == sum(range(helper_count))
