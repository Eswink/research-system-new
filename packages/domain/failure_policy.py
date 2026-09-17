"""失败策略的读面（GOAL-004 cycle 3 = EC-03）。

`TaskContract.failure_policy` 是一个自由 dict（YAML 里写的键值对）。自由声明的代价是
**没人知道哪条被消费了**：运行时要么悄悄忽略（运维以为生效了），要么瞎猜语义。
这里把它收敛成一份**冻结视图**：能消费的键给出取值，不能消费的键原样点名。

本轮真正消费的只有 run 级的一根轴：

```text
on_task_failure: FAIL_RUN   # 缺省：终局失败 ⇒ 立刻失败 run（既有隐式 fail-fast）
                 CONTINUE   # 声明：失败被记为"被容忍"，剩余工作照跑，最后 DEGRADED
```

其余键（如示例里的 `on_validation_failure` / `allow_partial_evidence`）**不假装消费**：
它们进 `unhonored`，由文档点名原因。`on_validation_failure` 的消费需要"完成任务行之后再
写一次"（验收门在 durable 完成之后才跑），属后继入口——如实登记比默默忽略更安全。
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


class OnTaskFailure:
    """run 级：一个任务**终局失败**之后，剩余工作还跑不跑。"""

    FAIL_RUN = "FAIL_RUN"
    CONTINUE = "CONTINUE"

    VALUES = frozenset({FAIL_RUN, CONTINUE})


# 已知键 → 取值域（确定性来源；新增消费点时必须同时进这里与文档）
KNOWN_KEYS: dict[str, frozenset[str]] = {"on_task_failure": OnTaskFailure.VALUES}

_FAILURE_POLICY_VALUE = str | bool | int | list[str]


@dataclass(frozen=True, slots=True)
class FailurePolicyView:
    """一次执行**实际消费**的失败策略 + 契约里声明了但没人消费的键。

    `declared`/`unhonored` 都是确定性排序，便于写进事件与断言。
    """

    on_task_failure: str = OnTaskFailure.FAIL_RUN
    declared: tuple[str, ...] = ()
    unhonored: tuple[str, ...] = ()

    @property
    def tolerated(self) -> bool:
        """被容忍的失败是否允许 run 继续跑完剩余工作。"""
        return self.on_task_failure == OnTaskFailure.CONTINUE


def failure_policy_view(
    policy: Mapping[str, _FAILURE_POLICY_VALUE] | None,
) -> FailurePolicyView:
    """契约声明的 dict → 冻结视图。

    - 缺省（空/None）：`FAIL_RUN`——既有隐式 fail-fast，行为与基线逐字一致。
    - 已知键取值非法：`ValueError`（响亮失败，不静默回退）——运维写了
      `on_task_failure: MAYBE` 必须有人知道这是错的。
    - 未知键：进 `unhonored`，不影响取值（不猜语义）。
    """
    declared = tuple(sorted(str(key) for key in (policy or {})))
    if not policy:
        return FailurePolicyView(declared=declared)
    unhonored = tuple(sorted(key for key in declared if key not in KNOWN_KEYS))
    raw = policy.get("on_task_failure")
    if raw is None or "on_task_failure" not in policy:
        return FailurePolicyView(declared=declared, unhonored=unhonored)
    value = str(raw)
    if value not in OnTaskFailure.VALUES:
        allowed = ", ".join(sorted(OnTaskFailure.VALUES))
        raise ValueError(f"unsupported on_task_failure value: {value!r} (allowed: {allowed})")
    return FailurePolicyView(on_task_failure=value, declared=declared, unhonored=unhonored)
