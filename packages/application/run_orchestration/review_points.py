"""**评审点表 → 会话 spec**（GOAL-20261029-100 EC-03；与 `review_material` 同层同手法）。

**它补哪一格**：应答相必须**逐条**回应评审提出的每一点，而「有哪几点、各自编号是什么」
此前只存在于审稿人的自由正文里（`review_decision` 的 `weakest_link` 从未被解析成记录）。
本模块把**本 run 已落库的评审交付物**派生成点表装进本任务的 spec，于是提示词里逐条带
`P1…Pn` —— 模型不必自己数「这是第几条」（与 GOAL-099 `W-1` 的引用编号是同一类缺陷）。

**求值点**：与检索上下文 / 前序知识 / 被评对象 / 上一轮评审**同一处**（`phase_runner`
每个任务开始前）—— 上游评审产物逐步落库，下游相开始时才该看到全部。

**两个边界**：

1. **只对应答契约生效**（`task.contract_id == "author_response"`）：别的相不需要点表，
   它们的提示词因此**逐字节**不变；
2. **点表为空 ⇒ 不挂**（不是「挂一个空段」）：空段会让「本 run 没有评审点」与
   「读不到评审」不可区分 —— 那正是本仓反复修掉的那类含混。

**零出网 / 零模型**：只读 canonical（`ArtifactStore` + 证据投影）。
"""

from __future__ import annotations

from typing import Any

from packages.application.deliverable.author_response import points_of, review_remarks

#: 应答契约的 id（与 `examples/contracts/task_contracts.yaml` 的键**逐字**一致）。
RESPONSE_CONTRACT_ID = "author_response"


def wants_review_points(task: Any) -> bool:
    """本任务是否要**逐条应答**（按任务的 `contract_id` 判，不按 phase id 猜）。

    **不能看 `task.contract`**（实测踩到的坑）：`ResearchTask` 携带的是 `contract_id`
    （字符串），合约对象由调用方**另参**传入 —— 写成 `task.contract` 会拿不到东西，
    于是本函数**静默**返回 `False`、点表根本进不了提示词，而表面上一切正常
    （模型回一条「P1」应答，汇编器随后点名漏答）。这条判断必须按**在场字段**写。
    """
    return str(getattr(task, "contract_id", "") or "") == RESPONSE_CONTRACT_ID


def review_points_of_run(artifacts: Any, ledger: Any, run_id: str) -> tuple[Any, ...]:
    """本 run 的评审点表（**唯一**派生点：提示词与应答信都调它）。

    两处各派生一次的话，「模型看到的点」与「汇编器据此判漏答的点」会是两份，而它们
    必须**逐条相同** —— 否则模型照提示词逐条答完，汇编器仍会判漏答（本 GOAL 实测到
    这个形态：提示词里 17 条、汇编时 19 条）。
    """
    from packages.application.run_orchestration.report_facts import evidence_of_run

    remarks = review_remarks(artifacts, evidence_of_run(ledger, run_id))
    return tuple(points_of(remarks))


def with_review_points(deps: Any, task: Any, spec_context: Any) -> Any:
    """本 run 的评审点表装进本任务的 spec（不需要 / 无点表 ⇒ **原样返回**）。"""
    if not wants_review_points(task):
        return spec_context
    artifacts = getattr(deps, "artifacts", None)
    ledger = getattr(deps, "ledger", None)
    if artifacts is None or ledger is None:
        return spec_context
    points = review_points_of_run(artifacts, ledger, str(task.run_id.value))
    if not points:
        return spec_context
    from dataclasses import replace

    return replace(spec_context, review_points=points)


__all__ = [
    "RESPONSE_CONTRACT_ID",
    "review_points_of_run",
    "wants_review_points",
    "with_review_points",
]
