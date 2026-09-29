"""GOAL-026 EC-04（AC-3）：补偿判定 —— 唯一可调用的补偿做成可复核判据 + 缺失面登记。

§7 义务「compensation for non-idempotent actions」在本仓的现实是**收窄的**：
仓内唯一有产品驱动的补偿是「续跑失败的 canonical 状态回滚」
（`packages/application/run_orchestration/run_terminals.py::compensate_failed_resume`）——
把 run 从「续跑失败」放回 `PAUSED` 并发 `run.resume_failed`。本文件把这条做成判据：

1. 补偿**执行**：状态真的回到 `PAUSED`，且**恰好一条**事件，payload 键与
   docstring 声明一致（名词事实可核对，不靠散文）；
2. 补偿**不产生第二次副作用**：对已 `PAUSED` 的 run 再补一次 ⇒ **结构化拒绝**
   （`InvalidTransitionError`）且事件数不变 ⇒ 补偿不是「可重复扣款」的动作；
3. **缺失面登记**（结构化、带受判面下界）：`CancellationState` 的
   `COMPENSATE` / `COMPENSATING` 在**产品代码**里**没有驱动点**（只出现在域定义里）、
   `compensation_actions` **只存在于文档**（产品代码零命中）⇒ 「非幂等副作用的补偿」
   是**登记边界**而不是实现 —— 本判据**不实现**新补偿（新能力，超出授权）。
"""

from __future__ import annotations

import os
import re

import pytest

from packages.application.run_orchestration import run_terminals
from packages.domain.core import ID
from packages.domain.events import EventType
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from packages.domain.state_base import InvalidTransitionError

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
PRODUCT_ROOTS = ("packages", "adapters", "services", "apps")
_SKIP_DIRS = {"node_modules", "__pycache__", ".venv", "dist", ".git"}
_MIN_SCANNED = 400
_DEFINITION_FILE = "packages/domain/session_state.py"
_COMPENSATING_LEMMA = re.compile(r"\bCOMPENSATING\b|\bCOMPENSATE\b")
_ACTIONS_TABLE = "compensation_actions"
_DOCS_FILE = "docs/storage/DATABASE_SCHEMA.md"


class _RecordingPublish:
    """与真实 `publish` 同形的记录器（只记录，不落库）。"""

    def __init__(self) -> None:
        self.calls: list[tuple[object, dict[str, object], dict[str, object]]] = []

    def __call__(self, event_type: object, payload: dict[str, object], **kwargs: object) -> None:
        self.calls.append((event_type, dict(payload), dict(kwargs)))


def _running_run() -> ResearchRun:
    return ResearchRun(
        id=ID.generate(),
        project_id="project-ec04",
        protocol_id="protocol-ec04",
        state=ResearchRunState.State.RUNNING,
    )


def _product_sources() -> list[str]:
    sources: list[str] = []
    for root in PRODUCT_ROOTS:
        base = os.path.join(REPO_ROOT, root)
        for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
            dirnames[:] = [name for name in dirnames if name not in _SKIP_DIRS]
            for name in filenames:
                if name.endswith(".py"):
                    sources.append(os.path.join(dirpath, name))
    return sources


def _relative(path: str) -> str:
    return os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")


def test_failed_resume_is_compensated_to_paused_with_one_event() -> None:
    """补偿**执行**：状态回 `PAUSED`，**恰好一条** `run.resume_failed`，发件箱字段可核对。"""
    publish = _RecordingPublish()
    run = _running_run()

    compensated = run_terminals.compensate_failed_resume(publish, run, RuntimeError("resume boom"))

    assert compensated.state == ResearchRunState.State.PAUSED, "补偿必须把 canonical 放回停车"
    assert run.state == ResearchRunState.State.RUNNING, "原实例不可变（证据保留）"
    assert len(publish.calls) == 1, "补偿只允许一条事件"
    event_type, payload, kwargs = publish.calls[0]
    assert event_type is EventType.RUN_RESUME_FAILED
    assert set(payload) == {"run_id", "failure_type", "message", "compensated_to"}
    assert payload["run_id"] == run.id.value
    assert payload["failure_type"] == "RuntimeError"
    assert payload["compensated_to"] == ResearchRunState.State.PAUSED
    assert kwargs.get("run_id") == run.id.value


def test_second_compensation_is_rejected_and_adds_no_event() -> None:
    """补偿**不可重复施加**：对已停车的 run 再补一次 ⇒ 结构化拒绝且事件不增。"""
    publish = _RecordingPublish()
    compensated = run_terminals.compensate_failed_resume(
        publish, _running_run(), RuntimeError("resume boom")
    )

    with pytest.raises(InvalidTransitionError):
        run_terminals.compensate_failed_resume(publish, compensated, RuntimeError("resume boom"))

    assert len(publish.calls) == 1, "被拒的补偿不得发出第二条事件"


def test_side_effect_compensation_has_no_product_driver_nor_storage() -> None:
    """缺失面**结构化**登记：`COMPENSATING` 无产品驱动；`compensation_actions` 只在文档。"""
    sources = _product_sources()
    assert len(sources) >= _MIN_SCANNED, f"扫描面过低（{len(sources)}）⇒ 受判面不成立"

    driver_hits: list[str] = []
    table_hits: list[str] = []
    for path in sources:
        with open(path, encoding="utf-8", errors="ignore") as handle:
            text = handle.read()
        if _COMPENSATING_LEMMA.search(text):
            driver_hits.append(_relative(path))
        if _ACTIONS_TABLE in text:
            table_hits.append(_relative(path))

    assert driver_hits == [_DEFINITION_FILE], (
        f"补偿会话态只允许出现在域定义里（实测：{driver_hits}）"
    )
    assert table_hits == [], f"`compensation_actions` 不得在产品代码里出现（实测：{table_hits}）"

    with open(os.path.join(REPO_ROOT, _DOCS_FILE), encoding="utf-8") as handle:
        assert _ACTIONS_TABLE in handle.read(), "文档面必须仍然登记这张表（否则是抹掉证据）"
