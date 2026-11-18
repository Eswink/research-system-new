"""计划读数 → **消融观测**的唯一映射（GOAL-20261117-114 EC-04）。

**它补哪一道缝**：GOAL-109 交付了两半 —— `output_readings.read_plan_payload`（从计划
制品抽可数读数）与 `tools/ablation_report.py`（四列位移 + `MIN_CORPUS=3` 门），
但**中间那一步没人写**：报告工具要求的是 `{design_block, arm_count, parameter_count,
citation_count}` 四个 **`int`** + 一个 `comparison_digest`，而读数侧给出的是三态**字符串**
（`payload_present` / `block_present` / `arms_parsed`）。缺了这一步，抓一次真实 run
之后没有任何代码能把它的产物变成一份可喂给门的观测。

**为什么映射必须自持、不能塞进 `tools/`**：反方向 —— 让 `tools/ablation_report.py` 认三态
字符串，会把「怎么认计划读数」这份知识复制到第二个模块（`design_block_in` 的教训：
同一个概念只许有一个解析器）。本模块依赖产品侧读数，`tools/` 只吃它的**output**（JSON）。

**三态 → 四列的规则**（每一条都是「不猜」）：

| 读数状态 | `design_block` | `arm_count` / `parameter_count` |
| --- | --- | --- |
| `block_present` + `arms_parsed` | 1 | 逐臂实数 |
| `block_present` + `arms_absent` | 1 | 0 / 0（设计写了、没写臂 —— 是**事实**） |
| `block_present` + `arms_malformed` | 1 | 0 / 0（臂写坏了 —— 也是事实，畸形不改数） |
| `block_absent`（任何 arms 态） | 0 | 0 / 0 |
| `payload_absent` | 0 | 0 / 0 |

**四列必须是 `int`，不能是 `bool`**：`ablation_report._observation` 显式拒
`isinstance(value, bool)`（`tools/ablation_report.py:134`）。而 `design_state ==
"block_present"` 天然产 bool —— 直接把它塞进 `design_block` 会**在真实 run 上**被门拒绝，
而在单测夹具里（`design_block: 1`）永远不会暴露。这是本模块最容易假绿的一处，故
`observation_from` **显式** `int(...)`，并由判据逐列断言 `type(value) is int`。

**未知状态点名拒绝**：`source_state` / `design_state` 是闭集；读到集合外的值 ⇒ 抛
`AblationObservationError`（不回落成 0 —— 「没读到」与「没有」必须分得开，GOAL-081）。
"""

from __future__ import annotations

from typing import Any

from packages.application.run_orchestration.output_readings import PlanOutputReadings

#: `source_state` 的闭集（与 `read_plan_payload` 产出的两个值同源）。
SOURCE_STATES: tuple[str, ...] = ("payload_present", "payload_absent")
#: `design_state` 的闭集。
DESIGN_STATES: tuple[str, ...] = ("block_present", "block_absent")

#: 四列读数的键（**逐字**等于 `tools/ablation_report.READING_FIELDS`；不 import 该工具）。
READING_KEYS: tuple[str, ...] = ("design_block", "arm_count", "parameter_count", "citation_count")


class AblationObservationError(ValueError):
    """读数状态不在闭集里（点名，不猜）。

    **不**继承 `InvalidInputError`：那是 **Port** 面的错误词表（`PermanentPortError`），
    本模块是纯映射、不碰任何 Port；把映射错误塞进 Port 错误词表会让「适配器拒绝了输入」
    与「观测映射不认这个状态」在上层同一分类里收口。与 `tools/ablation_report.AblationError`
    同一姿态（那里也显式选了 `ValueError` 并写明了理由）。
    """


def observation_from(readings: PlanOutputReadings, *, comparison_digest: str) -> dict[str, Any]:
    """一份计划读数 → 一份消融观测（四列 `int` + 一个可比键）。

    `comparison_digest` 由调用方从该 run 的冻结快照里取（`manifest.frozen` 事件的
    `comparison_digest` 键）——本模块**不**自己去读事件链（那是调用方的取证面）。
    """
    if not comparison_digest or not isinstance(comparison_digest, str):
        raise AblationObservationError("comparison_digest must be a non-empty string")
    _require(readings.source_state, SOURCE_STATES, "source_state")
    _require(readings.design_state, DESIGN_STATES, "design_state")
    has_block = readings.design_state == "block_present"
    # `int(...)` 而不是 `has_block`：bool 是 int 的子类，直接放进去会在门那里被拒。
    return {
        "comparison_digest": comparison_digest,
        "design_block": int(has_block),
        "arm_count": int(readings.arm_count),
        "parameter_count": int(readings.parameter_count),
        "citation_count": int(len(readings.cited_memory_ids)),
    }


def _require(value: str, allowed: tuple[str, ...], name: str) -> None:
    if value not in allowed:
        raise AblationObservationError(
            f"{name} {value!r} is not one of {list(allowed)}"
            "（闭集外的状态不猜成 0：『没读到』与『没有』必须分得开）"
        )


__all__ = [
    "AblationObservationError",
    "DESIGN_STATES",
    "READING_KEYS",
    "SOURCE_STATES",
    "observation_from",
]
