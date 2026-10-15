"""实验设计的**来源面**：从本 run 的**计划产物**里读出设计（GOAL-20261015-080 EC-01）。

**它补哪一环**：GOAL-20261015-079 让**参数与臂**由声明给出 —— 而声明的**写者**是装配面
（live run 里就是 `_LIVE_ARMS` 这个测试常量）。本模块把设计的**来源**变成可声明的事：
声明「取自计划产物」之后，臂与参数从**本 run 的计划制品内容**里读出。

**为什么是执行期 run 作用域读（而不是 phase 的 `inputs:`）**：建档期实测判定 ——
`test_declared_input_sources.py` 的两条判据要求 `inputs` 声明的是**仓库文件字节可重算 +
组合根种入**的制品（`created_by == "composition-root"`），而计划产物是**本 run 的模型
产物**；`inputs` 的既有口径逐字写着「只声明**外部供应**的输入，**不解析** phase 间的
产物引用」（`services/api/demo.py`）。⇒ 本模块走**执行期读**（与 GOAL-20261014-078 的
`retrieval_context` 同一形态），**一条既有判据都不动**。

**三条纪律**（逐条可判）：

1. **确定性、零出网**：只读 `ArtifactStore`（canonical）与传入的 run id —— 不建会话、
   不发请求、不重跑实验；
2. **run 作用域**：只认**本 run** 的制品（经 claim → relation 投影，`evidence.run_id`
   逐条过滤；他 run 的同名制品**读不到**）；
3. **fail-closed**：声明了计划来源而设计**缺席 / 畸形 / 越白名单** ⇒ **点名拒绝**
   （`ExperimentDesignUnreadableError`）—— **不**回落装配常量：静默回落会把「计划没写」
   伪装成「计划驱动」。

**零回归**：未声明来源（缺省）⇒ 本模块**不被调用**，装配面的既有语义逐字不变。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from packages.application.experiments.arms import ArmDeclaration, parse_arms
from packages.application.experiments.plan_parameters import ALLOWED_PARAMETERS
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError

#: 计划制品在**会话交付物**里的固定标识（`research_plan`；协议 `outputs` 逐字如此）。
PLAN_ARTIFACT_NAME = "research_plan"

#: 设计块在计划产物 JSON 里的键（**唯一**认可的落点；别处一律不认）。
DESIGN_KEY = "experiment_design"


class ExperimentDesignUnreadableError(InvalidInputError):
    """声明了计划来源而设计不可读（缺席 / 畸形 / 越白名单）—— 点名，**不**回落。"""


@dataclass(frozen=True, slots=True)
class PlanDerivedDesign:
    """从计划产物里读出的设计：**臂 + 它们的参数**，**外加来源**（制品 id 与 run）。"""

    artifact_id: str
    run_id: str
    arms: tuple[ArmDeclaration, ...]


def plan_artifact_id(task_id: str) -> str:
    """计划制品的 id 形态（`{task_id}:research_plan`，与结果注册面同一约定）。"""
    return f"{task_id}:{PLAN_ARTIFACT_NAME}"


def read_design_from_plan(
    artifacts: ArtifactStore,
    ledger: Any,
    *,
    run_id: str,
    max_chars: int = 200_000,
) -> PlanDerivedDesign:
    """本 run 的**计划产物** → `PlanDerivedDesign`（**按 run 过滤**，fail-closed）。

    **怎么按 run 过滤**（与 `retrieval_context._retrieved_evidence` 同一口径）：
    经 claim → relation 投影找出**本 run** 的证据（`evidence.run_id == run_id`），
    只看它们指向的制品 —— 也就是说，一个计划产物对本 run「在场」的判据是
    **它已被本 run 的证据链登记过**。他 run 的同名制品不在本 run 的投影里 ⇒ **读不到**。
    （不用「按 task 前缀猜」：执行期那需要一张 run→tasks 表，而本层不该持有它。）

    - 找不到计划制品 ⇒ `ExperimentDesignUnreadableError`（点名 run 与声明面）；
    - 制品在场但设计块缺席 / 非映射 ⇒ 点名（**不**回落成空臂）；
    - 设计块里的参数**逐键过既有白名单**（`ALLOWED_PARAMETERS`）—— 越界点名拒绝；
    - 臂声明本身用既有 `parse_arms` 解析（两种形态 / 重复名 / 畸形各自点名）。

    `max_chars` 是**上界**（§10 的有界口径）：制品超过它 ⇒ 点名拒绝（不是截断 ——
    截断一个设计会让「读到一半」看起来像「读到了」）。
    """
    in_view = _run_artifact_ids(ledger, run_id)
    if not in_view:
        raise ExperimentDesignUnreadableError(
            f"run {run_id!r} declared a plan-derived experiment design, but nothing is "
            "registered for it in the evidence ledger ⇒ the plan cannot be located"
        )
    found: list[tuple[str, Mapping[str, Any]]] = []
    for artifact_id in sorted(in_view):
        if not artifact_id.endswith(f":{PLAN_ARTIFACT_NAME}"):
            continue
        payload = _json_object(artifacts, artifact_id, max_chars=max_chars)
        if payload is not None:
            found.append((artifact_id, payload))
    if not found:
        raise ExperimentDesignUnreadableError(
            f"run {run_id!r} declared a plan-derived experiment design, but no "
            f"readable '{PLAN_ARTIFACT_NAME}' artifact is registered for it "
            f"(in view: {len(in_view)} artifact(s))"
        )
    # 多个计划制品（理论上不应有：一个 run 一个计划 phase）⇒ 点名，不猜。
    if len(found) > 1:
        raise ExperimentDesignUnreadableError(
            "more than one plan artifact is in view; the design source would be "
            f"undecidable: {sorted(item[0] for item in found)}"
        )
    artifact_id, payload = found[0]
    design = payload.get(DESIGN_KEY)
    if design is None:
        raise ExperimentDesignUnreadableError(
            f"the plan artifact {artifact_id!r} carries no {DESIGN_KEY!r} block "
            "(declare the design in the plan, or do not declare a plan-derived source)"
        )
    arms = _arms_of(design, artifact_id)
    return PlanDerivedDesign(artifact_id=artifact_id, run_id=run_id, arms=arms)


def _run_artifact_ids(ledger: Any, run_id: str) -> set[str]:
    """本 run 的**制品 id 集**：经 claim → relation 投影（既有读面口径）。

    与 `GET /runs/{id}/evidence` 同一取法：只登记证据**不挂关系**的读不到 ——
    既有语义，本处不另开一条（`retrieval_context` 的注释逐字写着同一句）。
    """
    found: set[str] = set()
    for claim in ledger.claims():
        for relation in ledger.relations_for_claim(claim.id):
            try:
                item = ledger.get_evidence(relation.evidence_id)
            except Exception:  # noqa: BLE001 - 引用可能已删除（视觉态）
                continue
            if item.run_id != run_id or not item.artifact_id:
                continue
            found.add(str(item.artifact_id))
    return found


def _arms_of(design: object, artifact_id: str) -> tuple[ArmDeclaration, ...]:
    """设计块 → 臂（形状经 `parse_arms`；参数逐键过白名单）。"""
    if not isinstance(design, Mapping) or "arms" not in design:
        raise ExperimentDesignUnreadableError(
            f"the {DESIGN_KEY!r} block in {artifact_id!r} must be an object with an "
            f"'arms' entry (got {type(design).__name__})"
        )
    try:
        arms = parse_arms(design["arms"])
    except Exception as error:  # noqa: BLE001 - 既有解析器的点名拒绝原样上抛（带来源）
        raise ExperimentDesignUnreadableError(
            f"the {DESIGN_KEY!r} block in {artifact_id!r} is malformed: {error}"
        ) from error
    if not arms:
        raise ExperimentDesignUnreadableError(
            f"the {DESIGN_KEY!r} block in {artifact_id!r} declares no arms "
            "(an empty design is indistinguishable from 'the plan forgot to write one')"
        )
    for arm in arms:
        unknown = sorted(set(arm.parameters) - ALLOWED_PARAMETERS)
        if unknown:
            raise ExperimentDesignUnreadableError(
                f"arm {arm.name!r} in {artifact_id!r} declares parameters outside the "
                f"whitelist: {', '.join(unknown)} "
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
    try:
        parsed: Any = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    return parsed if isinstance(parsed, Mapping) else None


__all__ = [
    "DESIGN_KEY",
    "PLAN_ARTIFACT_NAME",
    "ExperimentDesignUnreadableError",
    "PlanDerivedDesign",
    "plan_artifact_id",
    "read_design_from_plan",
]
