"""枚举门禁：任务状态机里的每个状态，要么**有生产驱动方**，要么**写明为什么没有**。

GOAL-003 cycle 15（PLAN-20260915-078）的起因就是这个缺口：`RETRY_SCHEDULED` 与
`DEAD_LETTER` 早就写在 Domain 状态机里，却**没有任何生产调用方**——失败一律被写成
FAILED，`TaskContract.retry_policy`（`max_attempts` 是必填字段）零消费者。
状态机会"接受"这些状态，但没人会走进它们，而这一点在代码里看不出来。

这条门禁把"状态 → 谁驱动它"钉成字面量：新加一个状态却不接线时，用例会红，逼一次
"它由谁设置"的决定，而不是让它悄悄躺在状态机里当摆设。
"""

from __future__ import annotations

import re
from pathlib import Path

from packages.domain.task_state import ResearchTaskState

# 由 adapter/服务等**生产代码**驱动的状态：状态名 → 驱动方所在模块（不含 tests）。
_DRIVEN_BY = {
    "CREATED": "packages/domain/tasks.py（ResearchTask 的默认状态，构造期初值）",
    "QUEUED": "adapters/sqlite/workflow_ops.py（submit 落库 / lease 过期回收）",
    "LEASED": "adapters/sqlite/workflow_ops.py + postgres/workflow_claim.py（claim）",
    "RETRY_SCHEDULED": "adapters/*/workflow_ops.py（可重试失败的重排）",
    "SUCCEEDED": "adapters/*/workflow_ops.py（成功完成）",
    "FAILED": "adapters/*/workflow_ops.py（不可重试失败）",
    "DEAD_LETTER": "adapters/*/workflow_ops.py（重试次数用尽的失败）",
    "CANCELLED": "adapters/sqlite/workflow_ops.py + postgres/cancel_run.py（取消传播）",
}

# 没有生产驱动方的状态：**必须**写下理由，否则门禁判红。
_UNDRIVEN_REASON = {
    "RUNNING": "agent 会话侧状态：任务行的生命周期只覆盖派发，运行中不写回 task 行",
    "WAITING_FOR_TOOL": "同上（会话侧）",
    "WAITING_FOR_APPROVAL": "同上（会话侧）",
}

_PRODUCTION_ROOTS = ("adapters", "services", "packages", "apps", "tools", "scripts")


def _production_files() -> list[Path]:
    root = Path(__file__).resolve().parents[2]
    files: list[Path] = []
    for name in _PRODUCTION_ROOTS:
        base = root / name
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if "fakes" in path.parts or "__pycache__" in path.parts:
                continue
            files.append(path)
    return files


def _drivers(state: str, files: list[Path]) -> list[Path]:
    """哪些生产文件设置了 `ResearchTaskState.State.<state>`（限定写法，避免同名误命中）。"""
    pattern = re.compile(rf"ResearchTaskState\.State\.{state}\b")
    return [path for path in files if pattern.search(path.read_text(encoding="utf-8"))]


def test_every_task_state_is_either_driven_or_explained() -> None:
    states = [name for name in vars(ResearchTaskState.State) if not name.startswith("_")]
    registered = [*_DRIVEN_BY, *_UNDRIVEN_REASON]
    assert sorted(states) == sorted(registered), (
        "状态机与登记表不一致：新增/改名状态必须同步这张表。"
        f"表里多出的：{sorted(set(registered) - set(states))}；"
        f"表里缺的：{sorted(set(states) - set(registered))}"
    )


def test_states_declared_driven_really_have_a_production_driver() -> None:
    files = _production_files()
    undriven = [state for state in _DRIVEN_BY if not _drivers(state, files)]
    assert undriven == [], (
        f"这些状态被登记为'有生产驱动方'，但生产代码里找不到：{undriven}。"
        "要么接线，要么移到 _UNDRIVEN_REASON 并写明理由。"
    )


def test_states_declared_undriven_really_have_no_driver() -> None:
    files = _production_files()
    driven = [state for state in _UNDRIVEN_REASON if _drivers(state, files)]
    assert driven == [], (
        f"这些状态被登记为'没有生产驱动方'，但生产代码已经在设置它们：{driven}。"
        "把它们移进 _DRIVEN_BY（这条门禁的作用就是不让登记表悄悄过期）。"
    )
