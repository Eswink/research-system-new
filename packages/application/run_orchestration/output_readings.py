"""计划产物的**可数读数**（GOAL-20261111-109 EC-03）：配对消融输出侧的统计量来源。

**为什么必须是「可数」的**：消融比较的是两臂输出的**分布位移**（GOAL-082 的混淆论证
只挡子串判据，不挡组间对比）。位移要有读数才能判——本模块从计划正文（JSON envelope）
抽出三种**可数**事实：

1. **是否产出 design block**（`experiment_design` 在不在——用
   `design_from_plan.design_block_in` 这**一个**解析器，不另造第二套「怎么认设计块」）；
2. **每臂参数取值**（臂名 + 白名单参数的键值；`parse_arms` 的两种形态都认）；
3. **引用标识数**（计划正文引用了**哪些**已知 memory id——逐字点名，不是「出现过」的
   子串判断；「模型引用了前序知识」因此有可数锚点）。

**两种「空」必须分得开**（GOAL-081 的教训）：

- **`payload_absent`**：读不到计划正文（制品缺席 / 载荷不是映射）——「没有产出」；
- **`block_absent`**：正文在，但里面没有 design block——「产出里没写设计」。

两者都如实点名（`source_state` / `arms_state`），**不猜**、不互相顶替。

**不宣称的事**：本模块只读**一份**计划产物；跨 run 的分布比较在
`tools/ablation_report.py`（EC-04）。它**不判**「计划写得好不好」。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from packages.application.experiments.arms import ArmDeclaration, parse_arms
from packages.application.experiments.design_from_plan import design_block_in
from packages.application.ports.errors import InvalidInputError

#: 计划交付物信封的**正文键**（与 `design_from_plan.ENVELOPE_CONTENT_KEY` 同一形态）。
ENVELOPE_CONTENT_KEY = "content"


@dataclass(frozen=True, slots=True)
class ArmReading:
    """一臂的**可数**读数：臂名 + 白名单参数（键排序，值原样）。"""

    name: str
    parameters: tuple[tuple[str, object], ...]

    @property
    def parameter_count(self) -> int:
        return len(self.parameters)


@dataclass(frozen=True, slots=True)
class PlanOutputReadings:
    """一份计划产物的全部可数读数（**两种空各自点名**，不互相顶替）。"""

    #: `payload_present`（读到了正文）/ `payload_absent`（读不到——制品缺席或非映射）。
    source_state: str
    #: `block_present`（正文里有 design block）/ `block_absent`（正文在、没写设计）。
    design_state: str
    #: 每臂读数（`arms_parsed` / `arms_absent` / `arms_malformed` 三态，不猜）。
    arms_state: str
    arms: tuple[ArmReading, ...]
    #: 计划正文里**逐字出现**的已知 memory id（排序去重）。
    cited_memory_ids: tuple[str, ...]

    @property
    def arm_count(self) -> int:
        return len(self.arms)

    @property
    def parameter_count(self) -> int:
        return sum(arm.parameter_count for arm in self.arms)


def read_plan_payload(
    payload: Mapping[str, Any] | None,
    *,
    known_memory_ids: tuple[str, ...] = (),
) -> PlanOutputReadings:
    """计划制品载荷 → 可数读数（确定性；零出网；**不抛**——空态点名）。

    `payload` 是交付物读面的 JSON（信封或直形态，`design_block_in` 两种都认）；
    `known_memory_ids` 是本 run 前序知识段的全部 memory id（引用数的分母来源）。
    """
    if not isinstance(payload, Mapping):
        return PlanOutputReadings(
            source_state="payload_absent",
            design_state="block_absent",
            arms_state="arms_absent",
            arms=(),
            cited_memory_ids=(),
        )
    text = str(payload.get(ENVELOPE_CONTENT_KEY, "") or "")
    block = design_block_in(dict(payload))
    design_state = "block_present" if block is not None else "block_absent"
    arms, arms_state = _arm_readings(block)
    return PlanOutputReadings(
        source_state="payload_present",
        design_state=design_state,
        arms_state=arms_state,
        arms=arms,
        cited_memory_ids=_cited_ids(text, known_memory_ids),
    )


def _arm_readings(
    block: object | None,
) -> tuple[tuple[ArmReading, ...], str]:
    """design block → 每臂读数（**三态**：parsed / absent / malformed；不猜）。"""
    if not isinstance(block, Mapping):
        return (), "arms_absent"
    raw = block.get("arms")
    if raw is None:
        return (), "arms_absent"
    try:
        parsed: tuple[ArmDeclaration, ...] = parse_arms(raw)
    except InvalidInputError:
        return (), "arms_malformed"
    readings = tuple(
        ArmReading(
            name=arm.name,
            parameters=tuple(sorted(arm.parameters.items(), key=lambda item: item[0])),
        )
        for arm in parsed
    )
    return readings, "arms_parsed"


def _cited_ids(text: str, known_memory_ids: tuple[str, ...]) -> tuple[str, ...]:
    """正文里**逐字出现**的已知 memory id（排序去重；分母 = `known_memory_ids`）。

    只在**已知的 id 集合**里找：拿正则去正文里「猜标识」会把碰巧长得像 id 的词
    也数进来（GOAL-082 的混淆论证正批评这种形状）；有分母的计数才是可判的。
    """
    return tuple(sorted({mid for mid in known_memory_ids if mid and mid in text}))


__all__ = [
    "ArmReading",
    "ENVELOPE_CONTENT_KEY",
    "PlanOutputReadings",
    "read_plan_payload",
]
