"""M11 scorer 共享类型（纯数据，无依赖、无副作用）。

拆分原因：schema_scorer 与 scorers 均需 ScorerContext/ScorerRegistration，
共享类型模块避免循环 import 与内联 import。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping

from packages.domain.core import Version
from packages.domain.eval_result import EvalFindingStatus, ScorerFinding
from packages.domain.eval_spec import EvalCase

V1 = Version("1.0.0")

InvariantPredicate = Callable[[object, Mapping[str, object]], bool]


@dataclass(frozen=True, slots=True)
class ScorerInput:
    """确定性 scorer 的显式输入（由 runner 按 case.input_ref 组装）。"""

    actual: object
    evidence_sources: Mapping[str, str] = field(default_factory=dict)
    extra: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ScorerContext:
    """scorer 求值上下文：case + 输入 + 谓词注册表（显式依赖）。"""

    case: EvalCase
    input: ScorerInput
    predicates: Mapping[str, InvariantPredicate] = field(default_factory=dict)


ScorerFn = Callable[[ScorerContext], ScorerFinding]


@dataclass(frozen=True, slots=True)
class ScorerRegistration:
    scorer_id: str
    version: Version
    fn: ScorerFn


def make_finding(
    scorer_id: str,
    ctx: ScorerContext,
    status: EvalFindingStatus,
    detail: str,
    value: object | None = None,
) -> ScorerFinding:
    """构造结构化 finding；不修改被评对象。"""

    return ScorerFinding(
        scorer_id=scorer_id,
        scorer_version=V1,
        case_id=ctx.case.id,
        status=status,
        detail=detail,
        value=value,
    )
