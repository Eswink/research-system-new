"""会话 spec 装配的**异常边界**（GOAL-20261111-108 R-1）。

**它补哪一格**（实测的既有缺陷，GOAL-106 `F-17` 的同族）：`phase_runner._run_group_task`
在 `phase.started` 之后、任务级 `try` 之外依次调用五个 spec 装配 helper
（`with_retrieval_context` / `with_prior_knowledge` / `with_review_material` /
`with_review_outcome` / `with_review_points`）。而 `phase_runner.py` 与 `service.py`
**全仓没有 try/except** —— 任何一个 helper 抛错都会**穿透整个执行栈**：

- `run.failed` 只能由 `publish_failed_run` 发出，那条路只经 `deps.fail(...)` 可达；
- 没有 handler ⇒ 没有事件、没有状态写入、`save_run` 也不跑。

实测后果（`F-17`）：`phase.started(revision)` 之后**一条事件都没有**，进程退出时最后
一条事件就是 `phase.started`。那不是「失败」，是**静默停住** —— 20 分钟后连一句判词都
没有。

**本模块只做一件事**：把那段装配包进异常边界，抛错时**走既有的唯一分叉**
`deps.fail(...)`（与 `phase_runner.py` 里 `step.failure` 那条路同一个出口），
于是「helper 炸了」变成一条**点名**的 `run.failed`。

**三条边界**（逐条可判）：

1. **不吞异常语义**：`system_failure=True` —— 这是装配面/基础设施问题，不是被评对象不合格。
2. **不改成功路径**：没有异常时**原样返回**装配结果（`is` 相同），既有行为逐字不变。
3. **不在这里决定重试**：判词交给 `deps.fail`，重试分类仍在 `task_executor`。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar, cast

if TYPE_CHECKING:  # pragma: no cover - 只为类型
    from packages.application.run_orchestration.outcomes import RunOutcome

T = TypeVar("T")


class SpecAssemblyError(RuntimeError):
    """spec 装配失败（点名是哪个 helper）。**不是**被评对象不合格。"""


def guarded_assembly(
    step: str, build: Callable[[], T]
) -> tuple[T | None, SpecAssemblyError | None]:
    """跑一步装配；抛错 ⇒ `(None, SpecAssemblyError)`，成功 ⇒ `(值, None)`。

    `step` 是 helper 的具名（`"with_review_outcome"` 等），进判词 —— 「哪个 helper 炸了」
    与「炸了什么」必须一起可读，否则排查要重新加日志。
    """
    try:
        return build(), None
    except Exception as error:  # noqa: BLE001 - 见模块 docstring：装配面任何异常都要可见
        return None, SpecAssemblyError(
            f"spec assembly step {step!r} raised {type(error).__name__}: {error}"
        )


def failure_message(error: SpecAssemblyError, *, task_id: str) -> str:
    """`deps.fail` 的判词（点名任务 + 哪一步 + 原始异常）。

    **格式固定**：判词里必须有 `task_id` 与 `step`，因为读面只存 message 字符串。
    """
    return f"task {task_id} could not be prepared for execution: {error}"


def fail_on_assembly_error(deps: Any, ctx: Any, task: Any, error: SpecAssemblyError) -> RunOutcome:
    """把装配失败折成 `RunOutcome`（走既有的 `deps.fail`，不另造出口）。"""
    return cast(
        "RunOutcome",
        deps.fail(
            ctx.run_id,
            failure_message(error, task_id=task.id.value),
            True,
        ),
    )


__all__ = [
    "SpecAssemblyError",
    "fail_on_assembly_error",
    "failure_message",
    "guarded_assembly",
]


def prepare_spec(
    steps: tuple[tuple[str, Callable[[], T]], ...],
) -> tuple[T | None, SpecAssemblyError | None]:
    """按序执行具名装配步；任一步抛错 ⇒ 立刻返回 `(None, 错误)`（点名那一步）。

    **`steps` 由调用方给**（每项 `(名字, 无参可调用)`），且**每项的闭包捕自己的输入**
    —— 五步是链式的，调用方在构造闭包时就串好了；本模块只负责「按序跑 + 抓异常」。
    本模块**不** import 那五个 helper（否则 `phase_runner → guard → phase_runner` 成环）。

    **返回值语义**：全部成功 ⇒ `(最后一值, None)`；任一步失败 ⇒ `(None, 错误)`。
    `None` 与错误**必须分开读**：前者是「没有值」，后者是「崩了」。

    **空 `steps`** ⇒ `(None, None)`：调用方自己判非空（本函数不猜）。
    """
    value: Any = None
    for name, build in steps:
        value, error = guarded_assembly(name, build)
        if error is not None:
            return None, error
    return cast("T | None", value), None


__all__ = [
    "SpecAssemblyError",
    "assemble_spec",
    "fail_on_assembly_error",
    "failure_message",
    "guarded_assembly",
    "prepare_spec",
]


def _bind(helper: Callable[..., Any], deps: Any, task: Any, spec: Any) -> Callable[[], Any]:
    """把一次 helper 调用**绑定**成零参闭包（单列：mypy 无法推断内联 lambda 的类型）。"""

    def call() -> Any:
        return helper(deps, task, spec)

    return call


def assemble_spec(
    deps: Any, task: Any, spec_context: Any, helpers: tuple[tuple[str, Callable[..., Any]], ...]
) -> tuple[Any | None, SpecAssemblyError | None]:
    """**链式**跑几个装配 helper：每步的输出喂下一步；任一步抛错 ⇒ `(None, 错误)`。

    与 `prepare_spec` 的区别：那个收「已经捕好输入的零参闭包」，本函数收「helper 本身」，
    由它**按序串**输入 —— 五个 helper 是 `(deps, task, spec) -> spec` 的形状，串起来才是
    正确语义（都基于上一步的产物，不是都基于最初那个）。

    `helpers` 由调用方给（本模块不 import 它们，避免环）。
    """
    current = spec_context
    for name, helper in helpers:
        current, error = guarded_assembly(name, _bind(helper, deps, task, current))
        if error is not None:
            return None, error
    return current, None
