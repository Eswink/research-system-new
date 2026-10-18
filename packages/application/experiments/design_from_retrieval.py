"""实验设计的**第二个来源**：从本 run 的**检索结果**里读出设计（GOAL-20261018-088 EC-01）。

**它补哪一格**（阶梯「实验」域的 `下一级`：`实验设计本身由检索派生`）：GOAL-080 让设计
可以取自**计划产物**（`design_source="plan"`），而计划本身又是**模型写的正文** —— 于是
「设计由检索派生」实际是「设计由**计划作者**派生」。本模块把来源换成**系统真的取回了什么**：
从本 run 的**系统取得证据**（`TrustLabel.RETRIEVED`，与覆盖门同一口径）的制品内容里读设计。

**三条纪律**（与 `design_from_plan` 逐条同形 —— 这是有意的：同一件陈述，两个来源）：

1. **确定性、零出网**：只读 `ArtifactStore` 与本 run 的证据投影；不建会话、不发请求；
2. **run 作用域**：只认**本 run** 的系统取得证据（`evidence.run_id` 逐条过滤，
   并且要求 `trust_label is RETRIEVED`）—— 他 run 的记录读不到，模型自产的也不算；
3. **fail-closed**：声明了检索来源而设计**缺席 / 畸形 / 越白名单** ⇒ **点名拒绝**
   （`ExperimentDesignUnreadableError`）—— **不**回落装配常量、**不**回落到计划。

**与 `design_source="plan"` 的关系**：两者**互斥**（同时声明 ⇒ 点名拒绝，与「臂 / 计划」
那一对同一条理由：`哪个说了算` 不可判定）。缺省 `None` ⇒ 本模块**不被调用**。

**设计块的落点**：同样认 `experiment_design` 这个键（`DESIGN_KEY`），从**检索记录的正文**
里读 —— 检索 provider 返回的 JSON（`articles` / 记录层）逐条可读，设计块挂在其中；
也认交付物信封形态（`content` 里一段可解析的 JSON），与计划来源共用同一个解析器。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from packages.application.experiments.arms import ArmDeclaration, parse_arms
from packages.application.experiments.design_from_plan import (
    DESIGN_KEY,
    ExperimentDesignUnreadableError,
    design_block_in,
)
from packages.application.experiments.plan_parameters import ALLOWED_PARAMETERS
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.evidence_ledger import EvidenceLedger

#: 工具结果制品的**id 前缀**（与 `report_facts.TOOL_SOURCE_PREFIX` 同一口径：
#: 系统取得的那一类证据的制品 id 都以它开头）。
TOOL_RESULT_PREFIX = "tool-result:"

#: 设计来源在装配面的声明值（与 `experiment_support.DESIGN_SOURCE_RETRIEVAL` 逐字一致）。
DESIGN_SOURCE_RETRIEVAL = "retrieval"


@dataclass(frozen=True, slots=True)
class RetrievalDerivedDesign:
    """从检索结果里读出的设计：**臂 + 它们的参数**，**外加来源**（哪些证据被读过）。"""

    run_id: str
    arm_source_evidence: tuple[str, ...]
    arms: tuple[ArmDeclaration, ...]


def read_design_from_retrieval(
    artifacts: ArtifactStore,
    ledger: EvidenceLedger,
    *,
    run_id: str,
    max_chars: int = 200_000,
) -> RetrievalDerivedDesign:
    """本 run 的**检索结果** → `RetrievalDerivedDesign`（**按 run + 性质过滤**，fail-closed）。

    - 没有任何**系统取得**的证据 ⇒ 点名拒绝（「这个 run 没取回过东西」与「取回了但设计
      不在里面」是两件事，前者说明声明写错了）；
    - 有证据但没有一条带设计块 ⇒ 点名拒绝（**不**回落成空臂）；
    - 设计块的参数**逐键过白名单**（`ALLOWED_PARAMETERS`）—— 越界点名拒绝。
    """
    in_view = _retrieved_in_view(artifacts, ledger, run_id)
    if not in_view:
        raise ExperimentDesignUnreadableError(
            f"run {run_id!r} declared a retrieval-derived experiment design, but it has "
            "no system-retrieved evidence (nothing was fetched with a RETRIEVED trust label)"
        )
    designs: list[tuple[str, object]] = []
    for evidence_id, artifact_id in in_view:
        payload = _json_object(artifacts, artifact_id, max_chars=max_chars)
        if payload is None:
            continue
        design = design_block_in(payload)
        if design is not None:
            designs.append((evidence_id, design))
    if not designs:
        raise ExperimentDesignUnreadableError(
            f"run {run_id!r} declared a retrieval-derived experiment design, but none of "
            f"its {len(in_view)} retrieved record(s) carries a {DESIGN_KEY!r} block"
        )
    # 多份设计 ⇒ 点名（哪一个说了算不可判定：本模块**不**猜「最后一条」）。
    if len(designs) > 1:
        raise ExperimentDesignUnreadableError(
            "more than one retrieved record carries an experiment design; which one decides "
            f"the experiment would be undecidable: {sorted(item[0] for item in designs)}"
        )
    evidence_id, design = designs[0]
    return RetrievalDerivedDesign(
        run_id=run_id,
        arm_source_evidence=(evidence_id,),
        arms=_arms_of(design, evidence_id),
    )


def _retrieved_in_view(
    artifacts: ArtifactStore, ledger: EvidenceLedger, run_id: str
) -> list[tuple[str, str]]:
    """本 run 的 `(证据 id, 制品 id)` 序列（只收**系统取得**的工具结果）。

    与 `retrieval_context._retrieved_evidence` 同一口径的**只读**取法：经 claim→relation
    投影、按 `run_id` 过滤、并要求来源性质是 `RETRIEVED`。制品不在场的不进列
    （读不到内容 = 没有设计，不是错误 —— 错误由「一条都没有」那处点名）。
    """
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for claim in ledger.claims():
        for relation in ledger.relations_for_claim(claim.id):
            evidence_id = relation.evidence_id
            if evidence_id in seen:
                continue
            seen.add(evidence_id)
            try:
                item = ledger.get_evidence(evidence_id)
            except Exception:  # noqa: BLE001 - 引用可能已删除（与既有读面同一口径）
                continue
            if item.run_id != run_id or not item.artifact_id:
                continue
            if not str(item.artifact_id).startswith(TOOL_RESULT_PREFIX):
                continue
            if not _is_retrieved(ledger, item):
                continue
            if artifacts.meta(str(item.artifact_id)) is None:
                continue
            found.append((str(evidence_id), str(item.artifact_id)))
    return sorted(found)


def _is_retrieved(ledger: EvidenceLedger, evidence: Any) -> bool:
    """该证据的来源性质是否「系统取得」（与覆盖门同一判据）。"""
    from packages.domain.enums import TrustLabel

    if not ledger.has_source(evidence.source_ref):
        return False
    return ledger.get_source(evidence.source_ref).trust_label is TrustLabel.RETRIEVED


def _arms_of(design: object, evidence_id: str) -> tuple[ArmDeclaration, ...]:
    """设计块 → 臂（形状经 `parse_arms`；参数逐键过白名单）。"""
    if not isinstance(design, Mapping) or "arms" not in design:
        raise ExperimentDesignUnreadableError(
            f"the {DESIGN_KEY!r} block in retrieved record {evidence_id!r} must be an object "
            f"with an 'arms' entry (got {type(design).__name__})"
        )
    try:
        arms = parse_arms(design["arms"])
    except InvalidInputError as error:
        raise ExperimentDesignUnreadableError(
            f"the {DESIGN_KEY!r} block in retrieved record {evidence_id!r} is malformed: {error}"
        ) from error
    if not arms:
        raise ExperimentDesignUnreadableError(
            f"the {DESIGN_KEY!r} block in retrieved record {evidence_id!r} declares no arms "
            "(an empty design is indistinguishable from 'the retrieval forgot to carry one')"
        )
    for arm in arms:
        unknown = sorted(set(arm.parameters) - ALLOWED_PARAMETERS)
        if unknown:
            raise ExperimentDesignUnreadableError(
                f"arm {arm.name!r} in retrieved record {evidence_id!r} declares parameters "
                f"outside the whitelist: {', '.join(unknown)} "
                f"(allowed: {', '.join(sorted(ALLOWED_PARAMETERS))})"
            )
    return arms


def _json_object(
    artifacts: ArtifactStore, artifact_id: str, *, max_chars: int
) -> Mapping[str, Any] | None:
    """制品内容 → JSON 对象（不在场 / 非 JSON / 非对象 / 超界 ⇒ `None`）。"""
    if artifacts.meta(artifact_id) is None:
        return None
    raw = artifacts.get(artifact_id)
    if len(raw) > max_chars:
        return None
    import json

    try:
        parsed: Any = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    return parsed if isinstance(parsed, Mapping) else None


__all__ = [
    "DESIGN_SOURCE_RETRIEVAL",
    "RetrievalDerivedDesign",
    "read_design_from_retrieval",
]
