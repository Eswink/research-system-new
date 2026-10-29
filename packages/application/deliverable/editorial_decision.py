"""**编辑决定块**的解析与判定（GOAL-20261029-100 EC-02）。

**它补哪一格**：`scientific_editor` 角色（`ReviewPanelRole.WRITER`）在 `roles.yaml` 里
**早就在**，但从未被任何协议激活（建档实测：`grep -rl scientific_editor
examples/protocols/` 零命中）；决定词表当时只有验收门的 `PASS` / `REJECT` 两值。
本模块给「投稿决策」这一面一个**可判的形状**：

    {"editorial_decision": {"decision": "accept|minor_revision|major_revision|reject",
                            "rationale": "<why>",
                            "required_changes": ["<what to change>"]}}

**三条判据（每条各自点名，不合并成一句「决定块不合法」）**：

1. **取值闭集**：`decision` 必须逐字是 `EditorialDecision` 的四个成员之一
   —— 越界值**点名拒绝**并列出合法取值（含拼写错误：本模块**不**做同义词归并，
   也不做大小写/下划线的宽容匹配，否则「越界」与「拼错」不可区分）；
2. **要求返修就必须说要改什么**：`decision != accept` 而 `required_changes` 为空
   ⇒ 点名判红（「要求返修却不说什么要改」是**不可执行**的决定）；
3. **理由不得为空**：`rationale` 是「这个决定凭什么」的那句话 —— 空它等于没给理由。

**与验收门的关系（刻意分开）**：`EditorialDecision` 判的是「稿件在期刊流程里的下一步」，
`QualityGateVerdict` 判的是「这次任务的交付物满不满足合约」。两者**可以**不一致
（一份通过验收门的稿件完全可以被判 `major_revision`），因此本模块**不读**任何门判词。

**零出网 / 零模型 / 零时钟**：输入是模型输出的字节，输出是已校验的决定或点名异常。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from packages.application.ports.errors import InvalidInputError
from packages.domain.enums import EditorialDecision

#: 决定块的顶层键（**逐字**；合约与判据按它定位）。
DECISION_KEY = "editorial_decision"
#: 决定块内的三个键（**逐字**）。
DECISION_FIELD = "decision"
RATIONALE_FIELD = "rationale"
CHANGES_FIELD = "required_changes"


class EditorialDecisionError(RuntimeError):
    """决定块不可用（畸形 / 越界取值 / 要求返修却不说什么要改）—— **点名**，不回落。"""


@dataclass(frozen=True, slots=True)
class EditorialOutcome:
    """一次编辑决定（已校验；四值之一 + 理由 + 逐条要求的改动）。"""

    decision: EditorialDecision
    rationale: str
    required_changes: tuple[str, ...]

    def as_payload(self) -> dict[str, object]:
        """决定 → 落库/读面的规范载荷（与输入块同形，取值用枚举的 `value`）。"""
        return {
            DECISION_FIELD: self.decision.value,
            RATIONALE_FIELD: self.rationale,
            CHANGES_FIELD: list(self.required_changes),
        }

    def markdown(self) -> str:
        """决定 → 一页可读的编辑决定（`response_letter` 与报告读面共用同一段字节）。"""
        lines = [
            "## Editorial Decision",
            "",
            f"- Decision: **{self.decision.value}**",
            f"- Rationale: {self.rationale}",
        ]
        if self.required_changes:
            lines += ["", "### Required Changes", ""]
            lines += [f"{index}. {item}" for index, item in enumerate(self.required_changes, 1)]
        else:
            lines += ["", "_No changes required._"]
        return "\n".join(lines)


def parse_editorial_decision(content: str | None) -> EditorialOutcome:
    """模型输出 → 已校验的编辑决定（畸形 / 越界 / 空理由 / 空改动清单 ⇒ 点名）。

    **两种输入形态都认**（与 `manuscript_assembly._sections_of` 同一纪律）：
    交付物**信封**（`{content: "<模型全文>"}`）与**直形态**（顶层就是决定块）。
    信封形态先取 `content` 再解一次 JSON —— 真会话的交付物是信封，受控夹具给直形态。
    """
    payload = _object_of(content)
    block = _decision_block(payload)
    decision = _decision_of(block)
    rationale = str(block.get(RATIONALE_FIELD) or "").strip()
    if not rationale:
        raise EditorialDecisionError(
            f"editorial decision {decision.value!r} carries no rationale: a decision without "
            "a stated reason cannot be reviewed by anyone downstream"
        )
    changes = _changes_of(block)
    if decision.requires_changes and not changes:
        raise EditorialDecisionError(
            f"editorial decision {decision.value!r} requires changes but required_changes is "
            "empty: an instruction to revise that does not say what to revise is not actionable"
        )
    return EditorialOutcome(decision=decision, rationale=rationale, required_changes=changes)


def _object_of(content: str | None) -> Mapping[str, Any]:
    """模型输出 → JSON 对象（**信封 + 正文里的 JSON 块**都经既有同一处解开）。

    真实会话的制品是**信封**（`{content: "<模型全文>", declared_artifact: …}`），而模型
    全文里是**围栏代码块**（```` ```json … ``` ````）—— 两层都要解。这里**不自己写**
    第二套解包：`phase_input_material.declared_object` 是全仓那件事的唯一实现
    （按期望键 `editorial_decision` 筛块，避开合约示例块 —— GOAL-20261020-091 实测过
    的形态）。直形态（受控夹具给顶层就是决定块）原样返回。
    """
    if content is None or not str(content).strip():
        raise EditorialDecisionError("editorial decision artifact is empty")
    parsed = _loads(content)
    if DECISION_KEY in parsed:
        return parsed
    from packages.application.run_orchestration.phase_input_material import declared_object

    try:
        return declared_object(parsed, key=DECISION_KEY)
    except InvalidInputError as error:
        raise EditorialDecisionError(str(error)) from error


def _loads(content: str) -> Mapping[str, Any]:
    try:
        parsed: Any = json.loads(content)
    except ValueError as error:
        raise EditorialDecisionError(f"editorial decision is not a JSON object: {error}") from error
    if not isinstance(parsed, Mapping):
        raise EditorialDecisionError(
            f"editorial decision must be a JSON object, got {type(parsed).__name__}"
        )
    return parsed


def _decision_block(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    block = payload.get(DECISION_KEY)
    if not isinstance(block, Mapping):
        raise EditorialDecisionError(
            f"editorial decision artifact has no {DECISION_KEY!r} object (found keys: "
            f"{sorted(map(str, payload))})"
        )
    return block


def _decision_of(block: Mapping[str, Any]) -> EditorialDecision:
    try:
        return EditorialDecision.parse(block.get(DECISION_FIELD))
    except ValueError as error:
        raise EditorialDecisionError(str(error)) from error


def _changes_of(block: Mapping[str, Any]) -> tuple[str, ...]:
    """`required_changes` → 逐条非空改动（非列表 / 空串项 ⇒ 点名，不静默丢）。"""
    raw = block.get(CHANGES_FIELD)
    if raw is None:
        return ()
    if isinstance(raw, str) or not isinstance(raw, (list, tuple)):
        raise EditorialDecisionError(
            f"{CHANGES_FIELD} must be a list of strings, got {type(raw).__name__}"
        )
    items: list[str] = []
    for item in raw:
        text = str(item or "").strip()
        if not text:
            raise EditorialDecisionError(
                f"{CHANGES_FIELD} contains an empty entry: an empty change item names nothing"
            )
        items.append(text)
    return tuple(items)


__all__ = [
    "CHANGES_FIELD",
    "DECISION_FIELD",
    "DECISION_KEY",
    "RATIONALE_FIELD",
    "EditorialDecisionError",
    "EditorialOutcome",
    "parse_editorial_decision",
]
