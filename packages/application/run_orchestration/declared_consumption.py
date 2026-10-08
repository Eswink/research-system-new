"""`CUSTOM_EVALUATOR` 的**编排层求值**：跨轮消费成为可判定（GOAL-20261008-038 EC-02/EC-03）。

**它补哪一环**：域层的 `_evaluate_custom_evaluator` 从来只做一件事 —— **恒判负**并明说
「must be executed by the orchestration layer」（那是它的**设计**：域不执行外部求值器）。
本模块就是那一层：把「本轮产物**声明**它消费了前序结论」落成**结构化比对**。

**判定链（三步，全部结构化；不做文本巧合）**：

1. **声明**：合约的 `CUSTOM_EVALUATOR` 判据用**既有** `metric` 字段声明「本轮结构化输出里
   哪条路径承载前序结论」（点分路径，如 `meta_review.prior_verdict`）；`evaluator` 字段是
   求值器 id（本轮只认 `cross_run_consumption`）。
2. **取值**：按声明路径从**本轮**的结构化输出里取出那个值（`_lookup`，与运行链同一取法）。
3. **比对**：与**前序 run 落库的结论逐字**比（`prior_conclusion`，由调用方从 canonical 读面
   取来）。相等 ⇒ 判过并留痕（判词含来源 run id 与逐字值）；不等 ⇒ 判负并**点名期望值与
   实际值**。

**fail-closed 三态（缺席一律点名，**不**回落默认值）**：

- 没声明路径（`metric` 空）⇒ 点名「未声明消费路径」；
- 声明了但本轮产物里**没有**那条路径 ⇒ 点名「声明路径缺失」；
- 有前序 run 但**读不到落库结论** ⇒ 点名（fail-closed：不得把「没有结论」当成「判过」）；
- **本轮结构上就没有前序 run**（程序的第一轮）⇒ 判据**不适用**（判过 + 点名）——
  与「有前序但未携带」严格区分；判成判负会让每个程序的第 1 轮必然失败。

**为什么在这里而不是域层**：域层的既有返回值语义**逐字不动**（它有既有判据把守，且它
明说该由编排层执行）；本模块是**唯一**编排层实现，由验收门求值点调用。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from packages.domain.enums import AcceptanceCriterionType
from packages.domain.tasks import AcceptanceCriterion, TaskContract

#: 本轮认得的求值器 id（逐字；未认得的 id ⇒ 点名，不静默当成「无此判据」）。
EVALUATOR_ID = "cross_run_consumption"

#: 被消费事实的**来源**标识（前序 run 的落库结论；判词里逐字给出）。
SOURCE_LABEL = "prior_run_conclusion"


@dataclass(frozen=True, slots=True)
class ConsumptionVerdict:
    """一次跨轮消费比对的结论（`reason` 是判词原文，进既有读面）。"""

    passed: bool
    reason: str
    #: 逐字值（判过时是**消费到的**那个值；判负时是**实际**值，可为空）。
    observed: str | None = None


def _lookup(payload: Any, path: str) -> Any:
    """按点分路径取值（与运行链 `lookup_path` 同一取法；缺任一段返回 `None`）。"""
    current: Any = payload
    for segment in path.split("."):
        if isinstance(current, dict):
            current = current.get(segment)
        else:
            return None
    return current


def _as_text(value: Any) -> str | None:
    """值 → 逐字文本（字符串直接取；其余用 `str()`；`None` 仍是 `None`）。"""
    if value is None:
        return None
    return value if isinstance(value, str) else str(value)


def declared_consumption_criteria(contract: TaskContract) -> tuple[AcceptanceCriterion, ...]:
    """合约里声明了「跨轮消费」求值器的判据（按声明顺序）。"""
    return tuple(
        criterion
        for criterion in contract.acceptance_criteria
        if criterion.type is AcceptanceCriterionType.CUSTOM_EVALUATOR
        and criterion.evaluator == EVALUATOR_ID
    )


def _absent_source(observed: str | None, prior_run_id: str | None) -> ConsumptionVerdict:
    """前序结论缺席时的两种形态（**严格区分**；与「有前序但未携带」也不同）。

    - **结构上无前序**（程序的第一轮）⇒ 判据**不适用**（判过 + 点名理由）。判成判负会让
      **每个程序的第 1 轮**必然失败 —— 那不是更严，那是把判据做成噪声；
    - **有前序但读不到结论** ⇒ 判负（fail-closed：不得把「没有结论」当成「判过」）。
    """
    if prior_run_id is None:
        return ConsumptionVerdict(
            True,
            f"custom evaluator {EVALUATOR_ID}: 本轮没有前序 run（结构上无可消费）"
            f"⇒ 判据不适用（已点名；{SOURCE_LABEL} 缺席不是「未携带」）",
            observed=observed,
        )
    return ConsumptionVerdict(
        False,
        f"custom evaluator {EVALUATOR_ID}: 有前序 run {prior_run_id} 但**读不到落库结论**"
        f"（{SOURCE_LABEL} 缺席）⇒ 不得把「没有结论」当成「判过」（fail-closed）",
        observed=observed,
    )


def resolve_consumption(
    criterion: AcceptanceCriterion,
    *,
    structured_output: Any,
    prior_conclusion: str | None,
    prior_run_id: str | None = None,
) -> ConsumptionVerdict:
    """一条 `CUSTOM_EVALUATOR`（`cross_run_consumption`）判据的编排层求值。"""
    path = (criterion.metric or "").strip()
    if not path:
        return ConsumptionVerdict(
            False,
            f"custom evaluator {EVALUATOR_ID}: 未声明消费路径（`metric` 为空）⇒ 无法比对",
        )
    observed = _as_text(_lookup(structured_output, path))
    if observed is None:
        return ConsumptionVerdict(
            False,
            f"custom evaluator {EVALUATOR_ID}: 声明路径 {path!r} 在本轮产物里缺失"
            "（点名：配置错误或产物未带该字段；不回落到默认值）",
        )
    if prior_conclusion is None:
        return _absent_source(observed, prior_run_id)
    source = f"{SOURCE_LABEL}" + (f" (run {prior_run_id})" if prior_run_id else "")
    if observed == prior_conclusion:
        return ConsumptionVerdict(
            True,
            f"custom evaluator {EVALUATOR_ID}: 本轮产物 {path}={observed!r} 与前序结论逐字一致"
            f"（来源：{source}）⇒ 消费成立",
            observed=observed,
        )
    return ConsumptionVerdict(
        False,
        f"custom evaluator {EVALUATOR_ID}: 本轮产物 {path}={observed!r} 与前序结论"
        f"{prior_conclusion!r} 不一致（来源：{source}）⇒ 消费不成立",
        observed=observed,
    )


def resolve_consumption_evaluations(
    contract: TaskContract,
    structured_output: Any,
    prior_conclusion: str | None,
    prior_run_id: str | None,
) -> dict[int, ConsumptionVerdict]:
    """按判据**下标**给出编排层结论（键 = `contract.acceptance_criteria` 的下标）。

    用下标当键（而不是判据对象）：同一条声明可以出现两次，且求值结果要按**原顺序**贴回
    （`evaluate_contract` 的返回值与声明同序）。
    """
    resolved: dict[int, ConsumptionVerdict] = {}
    for index, criterion in enumerate(contract.acceptance_criteria):
        if criterion.type is not AcceptanceCriterionType.CUSTOM_EVALUATOR:
            continue
        if criterion.evaluator != EVALUATOR_ID:
            resolved[index] = ConsumptionVerdict(
                False,
                f"custom evaluator {criterion.evaluator!r}: 编排层不认识这个求值器 id"
                f"（本轮只实现 {EVALUATOR_ID!r}）⇒ 点名，不静默当作无此判据",
            )
            continue
        resolved[index] = resolve_consumption(
            criterion,
            structured_output=structured_output,
            prior_conclusion=prior_conclusion,
            prior_run_id=prior_run_id,
        )
    return resolved


def prior_conclusion_reader(runs: Any, findings: Any) -> Any:
    """造一个「本 run 的前序结论」读取器（组合根接线用；GOAL-20261008-038 EC-04）。

    返回的闭包 `(run_id) -> (prior_conclusion, prior_run_id)` 读的是**同一程序内序号
    最大的那个前序 run** 的落库评审结论（逐字；取不到 ⇒ `(None, None)`，由求值器点名）。
    与 GOAL-037 的 `research_state_read` 同一入口（run_id → 程序归属 → 前序 run），
    区别只是把结论**取成文本**交给门（那里是整份读面载荷）。

    缺依赖（`RunStore` / `ReviewFindingStore` / 程序归属）⇒ 一律给 `(None, None)`：
    「读不到前序」是**事实**，由求值器按 fail-closed 点名 —— 不在这里猜、不在这里断。
    """

    def _read(run_id: str) -> tuple[str | None, str | None]:
        if runs is None or findings is None or not run_id:
            return (None, None)
        try:
            run = runs.get_run(run_id)
        except KeyError:
            return (None, None)
        program_id = getattr(run, "program_id", None)
        if not program_id:
            return (None, None)
        prior = [item for item in runs.for_program(program_id) if item.id.value != run_id]
        if not prior:
            return (None, None)
        last = prior[-1]
        for record in findings.for_run(last.id.value):
            verdict = getattr(record.finding, "verdict", None)
            if verdict:
                return (str(verdict), last.id.value)
        return (None, last.id.value)

    return _read


def consumption_inputs(deps: Any, tctx: Any, session_result: Any) -> dict[int, Any]:
    """合约声明了跨轮消费判据时，算好编排层结论（否则给空映射 ⇒ 域层既有判词保留）。

    从 `task_phase_helpers` 移到这里：那个模块卡在 450 行硬上限上（GOAL-037 也因同一理由
    把运行链实现分列出去）。本函数是**声明面**的一部分，与求值器同居是自然切法。
    """
    contract = tctx.contract
    if not declared_consumption_criteria(contract):
        return {}
    reader = getattr(deps, "prior_conclusion", None)
    run_id = getattr(getattr(tctx, "task", None), "run_id", None)
    prior_conclusion: str | None = None
    prior_run_id: str | None = None
    if reader is not None and run_id is not None:
        prior_conclusion, prior_run_id = reader(run_id.value)
    return resolve_consumption_evaluations(
        contract,
        session_result.structured_output,
        prior_conclusion,
        prior_run_id,
    )


__all__ = [
    "EVALUATOR_ID",
    "SOURCE_LABEL",
    "ConsumptionVerdict",
    "consumption_inputs",
    "declared_consumption_criteria",
    "prior_conclusion_reader",
    "resolve_consumption",
    "resolve_consumption_evaluations",
]
