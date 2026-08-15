"""M11 Evaluation Plane 评测规格域契约（frozen、stdlib-only）。

来源（权威）：docs/roadmap/MILESTONES.md M11（Scope/DoD 唯一权威）、
docs/architecture/EVALUATION.md、docs/evaluation/EVAL_HARNESS.md。
约束：
- EvalCase 的 oracle 不允许以自由文本 description 作为唯一可执行规格
  （expected 与 rubric 至少其一）；
- EvalDataset 冻结语义：case 按 id 排序参与 digest，任何 case 内容变更、
  删除或替换都会改变 dataset digest；
- digest 复用 packages.domain.serialization 的 canonical JSON 规则
  （float/NaN 拒绝进入 digest、key 递归排序、UTF-8）。
本模块不 import application/adapter 或第三方类型。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from packages.domain.core import Digest, Version
from packages.domain.serialization import digest_of

EVAL_SPEC_FORMAT = "eval_spec.v1"

CanaryTag = "canary"


class EvalScope(StrEnum):
    """评测模式（MILESTONES.md M11 Scope：unit / integration / workflow）。"""

    UNIT = "UNIT"
    INTEGRATION = "INTEGRATION"
    WORKFLOW = "WORKFLOW"


class EvalDeterminism(StrEnum):
    """评测确定性分类；非确定性评测必须显式记录采样与聚合条件。"""

    DETERMINISTIC = "DETERMINISTIC"
    NON_DETERMINISTIC = "NON_DETERMINISTIC"


@dataclass(frozen=True, slots=True)
class ScorerRef:
    """对版本化 scorer 的引用；scorer 注册表按 scorer_id 解析实现。"""

    scorer_id: str
    version: Version


@dataclass(frozen=True, slots=True)
class RubricSpec:
    """语义评审维度（仅 Reviewer 使用；确定性判断不得依赖 rubric）。"""

    id: str
    dimension: str
    description: str
    scale: tuple[int, int] = (1, 5)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("rubric id must not be empty")
        low, high = self.scale
        if low < 0 or high <= low:
            raise ValueError(f"invalid rubric scale: {self.scale!r}")


@dataclass(frozen=True, slots=True)
class EvalCase:
    """一次可独立执行、可独立判分的评测用例。

    oracle 为可执行规格：expected（确定性期望）与 rubric（语义维度）
    至少提供其一；description 仅为可读说明，不参与 case digest。
    """

    id: str
    version: Version
    scope: EvalScope
    input_ref: str
    expected: object | None
    rubric: tuple[RubricSpec, ...] = ()
    required_artifact_digests: tuple[str, ...] = ()
    scorer_refs: tuple[ScorerRef, ...] = ()
    determinism: EvalDeterminism = EvalDeterminism.DETERMINISTIC
    tags: tuple[str, ...] = ()
    provenance: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("case id must not be empty")
        if not self.input_ref.strip():
            raise ValueError(f"case {self.id}: input_ref required")
        if self.expected is None and not self.rubric:
            raise ValueError(
                f"case {self.id}: expected or rubric required "
                "(description is not an executable oracle)"
            )
        if CanaryTag in self.tags and self.scope is EvalScope.WORKFLOW:
            raise ValueError(f"case {self.id}: canary cases must be unit/integration scope")


@dataclass(frozen=True, slots=True)
class EvalDataset:
    """冻结的 case 集合；digest 可识别静默删除/替换/内容变更。"""

    id: str
    version: Version
    cases: tuple[EvalCase, ...]
    description: str = ""

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("dataset id must not be empty")
        if not self.cases:
            raise ValueError("dataset must contain at least one case")
        seen: set[str] = set()
        for case in self.cases:
            if case.id in seen:
                raise ValueError(f"duplicate case id in dataset: {case.id}")
            seen.add(case.id)

    def sorted_cases(self) -> tuple[EvalCase, ...]:
        """按 case id 排序的视图；顺序不参与 freeze 语义。"""

        return tuple(sorted(self.cases, key=lambda case: case.id))

    def digest(self) -> Digest:
        payload = {
            "format": EVAL_SPEC_FORMAT,
            "id": self.id,
            "version": self.version.text,
            "case_digests": [str(case_digest(case)) for case in self.sorted_cases()],
        }
        return digest_of(payload)


def case_digest(case: EvalCase) -> Digest:
    """case 内容 digest；description 不参与（非可执行规格）。"""

    payload = {
        "format": EVAL_SPEC_FORMAT,
        "id": case.id,
        "version": case.version.text,
        "scope": case.scope.value,
        "input_ref": case.input_ref,
        "expected": case.expected,
        "rubric": [
            {
                "id": item.id,
                "dimension": item.dimension,
                "description": item.description,
                "scale": item.scale,
            }
            for item in case.rubric
        ],
        "required_artifact_digests": list(case.required_artifact_digests),
        "scorer_refs": [
            {"scorer_id": item.scorer_id, "version": item.version.text} for item in case.scorer_refs
        ],
        "determinism": case.determinism.value,
        "tags": list(case.tags),
        "provenance": case.provenance,
    }
    return digest_of(payload)
