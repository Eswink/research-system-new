"""失败策略的读面（GOAL-004 cycle 3 = EC-03）。

`TaskContract.failure_policy` 是一个自由 dict（YAML 里写的键值对）。自由声明的代价是
**没人知道哪条被消费了**：运行时要么悄悄忽略（运维以为生效了），要么瞎猜语义。
这里把它收敛成一份**冻结视图**：能消费的键给出取值，不能消费的键原样点名。

本轮真正消费的只有 run 级的一根轴：

```text
on_task_failure: FAIL_RUN   # 缺省：终局失败 ⇒ 立刻失败 run（既有隐式 fail-fast）
                 CONTINUE   # 声明：失败被记为"被容忍"，剩余工作照跑，最后 DEGRADED
```

其余键（用户契约里任何不在 `KNOWN_KEYS` 的键）**不假装消费**：它们进 `unhonored`，由文档
点名原因。`on_validation_failure` 的消费需要"完成任务行之后再写一次"（验收门在 durable
完成之后才跑，改写一条 `SUCCEEDED` 行属 canonical 状态机改动），属后继入口——如实登记比
默默忽略更安全。平台自带的示例契约因此只声明**被消费**的键（GOAL-005 cycle 3 = EC-03），
但用户契约里再写 `on_validation_failure` 照样被点名。

**待拍板的决策在哪**（GOAL-20260918-006 cycle 2 = EC-02）：`on_validation_failure` 的处置
是 `docs/adr/ADR-0030-validation-failure-consumption.md`（Status: Proposed）——该 ADR 给出
`SUCCEEDED` 不可回头的状态机事实、选项 A–E 的代价与收益、以及"何时必须拍板"的触发条件。
在它被接受之前，"声明它不改变任何判定"就是**当前口径**（本模块与示例契约都是这个口径）。
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


class OnTaskFailure:
    """run 级：一个任务**终局失败**之后，剩余工作还跑不跑。"""

    FAIL_RUN = "FAIL_RUN"
    CONTINUE = "CONTINUE"

    VALUES = frozenset({FAIL_RUN, CONTINUE})


class ReviewPanelFailure:
    """评审 phase 级：一位评审者判负时，**同批评审**还评不评得完（GOAL-20261018-087）。

    **与 `on_task_failure` 是两件事**（混用会把「判负」说成「可容忍的瑕疵」）：

    - `on_task_failure: CONTINUE` ⇒ 失败被**容忍**（run 收敛 `DEGRADED`，判负成了
      「可以带着走」的瑕疵）；
    - 本键 ⇒ 先把**同批**评审者都评完并落库（分歧因此可读），**再**按全体结论判定：
      只要有任一位判负，run 仍 `FAILED`。改的是**时机与可见性**，不是后果。
    """

    COMPLETE_THEN_JUDGE = "COMPLETE_THEN_JUDGE"

    VALUES = frozenset({COMPLETE_THEN_JUDGE})


# 已知键 → 取值域（确定性来源；新增消费点时必须同时进这里与文档）
KNOWN_KEYS: dict[str, frozenset[str]] = {
    "on_task_failure": OnTaskFailure.VALUES,
    "review_panel": ReviewPanelFailure.VALUES,
}

_FAILURE_POLICY_VALUE = str | bool | int | list[str]


@dataclass(frozen=True, slots=True)
class FailurePolicyView:
    """一次执行**实际消费**的失败策略 + 契约里声明了但没人消费的键。

    `declared`/`unhonored` 都是确定性排序，便于写进事件与断言。
    """

    on_task_failure: str = OnTaskFailure.FAIL_RUN
    #: 空串 = 未声明该面（既有语义；逐字不变）。
    review_panel: str = ""
    declared: tuple[str, ...] = ()
    unhonored: tuple[str, ...] = ()

    @property
    def tolerated(self) -> bool:
        """被容忍的失败是否允许 run 继续跑完剩余工作。"""
        return self.on_task_failure == OnTaskFailure.CONTINUE

    @property
    def panel_completes_before_judging(self) -> bool:
        """同批评审是否要**先评完再判**（GOAL-20261018-087 EC-02）。

        假 ⇒ 既有 fail-fast（第一个判负就停，同批后续评审者不跑）。这条**不是**
        `tolerated` 的别名：两者可以同时为假（各自独立的声明面）。
        """
        return self.review_panel == ReviewPanelFailure.COMPLETE_THEN_JUDGE


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
    return FailurePolicyView(
        # 缺省 `FAIL_RUN`（既有隐式 fail-fast）：**不**随新增键而漂成空串。
        on_task_failure=_value(policy, "on_task_failure", OnTaskFailure.VALUES)
        or OnTaskFailure.FAIL_RUN,
        review_panel=_value(policy, "review_panel", ReviewPanelFailure.VALUES),
        declared=declared,
        unhonored=unhonored,
    )


def _value(policy: Mapping[str, _FAILURE_POLICY_VALUE], key: str, values: frozenset[str]) -> str:
    """一个已知键的取值（**缺席 ⇒ 空串**；非法 ⇒ 响亮失败，不静默回退）。"""
    raw = policy.get(key)
    if raw is None or key not in policy:
        return ""
    value = str(raw)
    if value not in values:
        allowed = ", ".join(sorted(values))
        raise ValueError(f"unsupported {key} value: {value!r} (allowed: {allowed})")
    return value
