"""`run.completed` 载荷的**唯一构造点**（GOAL-20261009-042 EC-03 抽出）。

**为什么抽出**：这条载荷此前有**两处**手写构造（单遍在 `phase_runner`、循环收尾在
`round_loop_runner` 里**逐字重建**一份），两处的字段清单靠注释约定同步 —— 实测的
后果是：往一处加字段就可能在另一处**丢掉**（`round_loop_runner` 的注释自己写着
「否则跑循环的 run 会**丢掉**跳过事实」）。字段清单因此收进本模块一处，
两个调用点都用它 ⇒ 新增字段不可能只到一边。

**载荷口径**（缺省不带键 ⇒ 既有载荷逐字节不变）：

- `run_id`：恒在；
- `skipped`：**声明式跳过**的理由（有才带）——「哪条工具因上一步的哪个字段没跑」；
- `annotated`：**记忆时效门**的标注（有才带）——「哪条工具被哪几条待复核记忆标注」
  （GOAL-20261009-042 EC-03：待复核**不跳过**，但必须可读）。

两个键**互不混用**：`skipped` 是「这一步没执行」，`annotated` 是「执行了但带标注」。
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Protocol


class _TaskLike(Protocol):
    """构造载荷所需的任务面（只读两个字段，避免与 `outcomes` 形成导入环）。"""

    @property
    def task(self) -> Any: ...

    @property
    def annotations(self) -> tuple[str, ...]: ...

    @property
    def skipped(self) -> tuple[str, ...]: ...


def _reasons(key: str, tasks: Iterable[_TaskLike]) -> list[dict[str, object]]:
    """各任务的某条理由通道（逐任务点名；空通道的任务不进表）。"""
    return [
        {"task_id": outcome.task.id.value, "reasons": list(getattr(outcome, key))}
        for outcome in tasks
        if getattr(outcome, key)
    ]


def run_completion_payload(run_id: str, tasks: Iterable[_TaskLike]) -> dict[str, object]:
    """本 run 的 `run.completed` 载荷（**两处调用点共用**，字段清单只此一份）。"""
    outcomes = tuple(tasks)
    payload: dict[str, object] = {"run_id": run_id}
    skips = _reasons("skipped", outcomes)
    if skips:
        payload["skipped"] = skips
    annotations = _reasons("annotations", outcomes)
    if annotations:
        payload["annotated"] = annotations
    return payload


__all__ = ["run_completion_payload"]
