"""配对消融的两臂（GOAL-20261111-109 EC-02）：**「只差一个 slot」的机械证明**。

**它配什么**：`AblationPair(slot, present, absent)` —— 两臂由**同一份装配**产出
（manifest 级用 `comparison_digest` 证明同装配），差异**只有那一个 slot**
（prompt 级用「其余 section digest 逐字相等」证明）。

**为什么证明必须机械**：GOAL-082 的混淆论证说「子串判据无区分力」。配对设计的第一步
就是让「两臂只差一个变量」**不需要人眼判断**——除该 slot 外，每个 slot 各自经产品的
唯一拼装点 `compose_prompt` 单独渲染，两臂逐字相等；被消融的 slot 一臂有、一臂没有。

**slot 词表就是产品的六个并列段**（`retrieval_prompt.compose_prompt` 的形参），
不另造第二套段名 —— 消融的两臂必须能直接喂给产品渲染器，否则「实验里跑的」与
「产品里跑的」是两个东西。

**不宣称的事**：`only_slot_differs` 证明的是**输入侧**「只差一个变量」；输出侧
「分布是否位移」在 `output_readings.py`（EC-03）与 `tools/ablation_report.py`（EC-04）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping

from packages.application.run_orchestration.comparison_digest import (
    comparable as manifests_comparable,
)
from packages.application.run_orchestration.comparison_digest import comparison_digest
from packages.domain.serialization import digest_of

if TYPE_CHECKING:  # pragma: no cover - 仅类型
    from packages.application.run_orchestration.comparison_digest import ComparisonKey
    from packages.domain.manifest import RunManifest

#: 六个并列段的**产品词表**（`compose_prompt` 的形参名，顺序 = 拼装顺序）。
SLOT_ORDER: tuple[str, ...] = (
    "direction",
    "prior_knowledge",
    "retrieval",
    "review_outcome",
    "review_points",
    "review_material",
)

#: 单独渲染某段时的 purpose 占位（渲染是「前缀 + \n\n + 段文本」，空 purpose 只留段）。
_ISOLATION_PURPOSE = ""

#: 段与段之间的分隔符（`compose_prompt` 的拼法；分解正确性的前提，判据按压它）。
SECTION_SEPARATOR = "\n\n"


@dataclass(frozen=True, slots=True)
class PromptArm:
    """消融的一臂：**一份装配**（manifest + 六段已渲染文本）。

    `slots` 的值是 `str | None` —— **就是 `AgentSessionSpec` 各 prompt 字段携带的形状**
    （`session_prompts.*_prompt` 的返回：渲染好的段文本；`None` = 该段缺席）。
    消融因此作用在**会话真正收到的那份提示词**上，不另造中间形态；段与段之间
    共享除被消融段外的全部字符串对象，比较按字节判。
    """

    manifest: "RunManifest"
    slots: Mapping[str, str | None]

    def __post_init__(self) -> None:
        unknown = set(self.slots) - set(SLOT_ORDER)
        if unknown:
            raise ValueError(f"unknown prompt slots: {sorted(unknown)} (known: {SLOT_ORDER})")
        for name, value in self.slots.items():
            if value is not None and not isinstance(value, str):
                raise ValueError(
                    f"slot {name!r} must be a rendered str or None, got {type(value).__name__}"
                )

    def key(self) -> "ComparisonKey":
        """本臂装配的 run 级可比键（剔除 run_id / frozen_at / project_id）。"""
        return comparison_digest(self.manifest)

    def render(self, purpose: str) -> str:
        """经产品的**唯一拼装点**渲染（不重写第二套拼法）。"""
        from packages.application.run_orchestration.retrieval_prompt import compose_prompt

        kwargs = {name: self.slots.get(name) for name in SLOT_ORDER}
        return compose_prompt(purpose, **kwargs)

    def section_digests(self) -> dict[str, str]:
        """每段**单独渲染**的 digest（空段 = `None` 的固定占位）。

        「其余 section digest 逐字相等」的**字节来源**：每段经同一个 `compose_prompt`
        单独渲染（purpose 置空）——段的贡献文本由产品的拼装函数给出，
        不是本模块重新拼一遍。
        """
        out: dict[str, str] = {}
        for name in SLOT_ORDER:
            payload = self.slots.get(name)
            if payload is None:
                out[name] = _absent_digest()
                continue
            rendered = self.render_slot(name)
            out[name] = str(digest_of(rendered))
        return out

    def render_slot(self, name: str) -> str:
        """单段渲染（其余段置 `None`；被点名的段必须**在场**）。"""
        if self.slots.get(name) is None:
            raise ValueError(f"slot {name!r} is absent in this arm")
        payload: str = self.slots[name] or ""
        kwargs: dict[str, str | None] = {other: None for other in SLOT_ORDER}
        kwargs[name] = payload
        from packages.application.run_orchestration.retrieval_prompt import compose_prompt

        return compose_prompt(_ISOLATION_PURPOSE, **kwargs)


_ABSENT_SENTINEL = "absent"


def _absent_digest() -> str:
    """缺席段的固定 digest（与任何在场段的 digest 可区分）。"""
    return str(digest_of(_ABSENT_SENTINEL))


@dataclass(frozen=True, slots=True)
class AblationPair:
    """一对消融臂：`present` 有 `slot`，`absent` 没有；其余**逐字同一份装配**。"""

    slot: str
    present: PromptArm
    absent: PromptArm

    def __post_init__(self) -> None:
        if self.slot not in SLOT_ORDER:
            raise ValueError(f"unknown ablation slot: {self.slot!r} (known: {SLOT_ORDER})")
        if self.present.slots.get(self.slot) is None:
            raise ValueError(f"present arm must carry slot {self.slot!r}")
        if self.absent.slots.get(self.slot) is not None:
            raise ValueError(f"absent arm must not carry slot {self.slot!r}")
        if not manifests_comparable(self.present.manifest, self.absent.manifest):
            raise ValueError(
                "the two arms are not the same assembly: "
                f"{self.present.key().digest} != {self.absent.key().digest}"
            )

    def renders(self, purpose: str) -> tuple[str, str]:
        """两臂的**完整提示词**（产品拼装点渲染；消融实验实际发给模型的就是它）。"""
        return self.present.render(purpose), self.absent.render(purpose)

    def only_slot_differs(self) -> bool:
        """**机械证明**：除 `slot` 外每段 digest 逐字相等，且 `slot` 本身不同。

        三个合取，缺一即 `False`：
        ① 两臂同装配（构造期已断言，这里重判防构造后换对象）；
        ② 其余五段的单独渲染 digest **逐字相等**（含「缺席 vs 缺席」）；
        ③ 被消融段：present 在场、absent 缺席（digest 必不等）。
        """
        if not manifests_comparable(self.present.manifest, self.absent.manifest):
            return False
        left, right = self.present.section_digests(), self.absent.section_digests()
        for name in SLOT_ORDER:
            if name == self.slot:
                continue
            if left[name] != right[name]:
                return False
        return left[self.slot] != right[self.slot]

    def differing_sections(self) -> tuple[str, ...]:
        """两臂 digest 不同的段名（= `{slot}` 当且仅当证明成立；诊断面）。"""
        left, right = self.present.section_digests(), self.absent.section_digests()
        return tuple(name for name in SLOT_ORDER if left[name] != right[name])


def build_pair(
    manifest: "RunManifest",
    slots: Mapping[str, str | None],
    slot: str,
) -> AblationPair:
    """从**同一份装配**造两臂：present = 原样；absent = 只把 `slot` 置 `None`。

    `absent` 的 slots **逐段复制**原映射再改一格，其余五段是**同一批字符串对象**
    （可变性由此归调用方；本模块只读）。
    """
    if slot not in SLOT_ORDER:
        raise ValueError(f"unknown ablation slot: {slot!r} (known: {SLOT_ORDER})")
    if slots.get(slot) is None:
        raise ValueError(f"slot {slot!r} is already absent; nothing to ablate")
    absent_slots = {name: slots.get(name) for name in SLOT_ORDER}
    absent_slots[slot] = None
    return AblationPair(
        slot=slot,
        present=PromptArm(manifest=manifest, slots=dict(slots)),
        absent=PromptArm(manifest=manifest, slots=absent_slots),
    )


__all__ = [
    "SLOT_ORDER",
    "SECTION_SEPARATOR",
    "AblationPair",
    "PromptArm",
    "build_pair",
]
