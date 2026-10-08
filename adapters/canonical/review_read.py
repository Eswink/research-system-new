"""`review.read` 的**执行实现**（GOAL-20261008-036 EC-02；与 `read_provider.py` 分列）。

**为什么单列**：`read_provider.py` 有 **450 行硬上限**（规模门），本轮再往上接一条读能力
就越界。拆分的切法与 `run_read.py` 同：本模块只放 `review.read` 这一条的实现，
`read_provider.py` 只留一行委派。

**它读什么**：`ReviewFindingStore`（GOAL-035 EC-01 建立的 canonical 记录面）的
`for_run(run_id)` —— 与 HTTP 读面 `GET /runs/{run_id}/reviews` **同一个**查询口径，
**不新造第二套**。

**为什么这条能力是「研究循环真正需要」的**：验收门的逐条判词此前只在**被拒路径**带进失败
消息；GOAL-035 把它落 canonical 并给了只读 HTTP 面，但 **agent 的能力面读不到** ⇒ 后续
phase / 后续轮次无法消费上一轮的评审结论（它也是 GOAL-035 登记的未覆盖 `N-3`
「多评审者聚合」的前置）。

**边界**（与既有读面同一条纪律）：

- `ReviewFindingStore` 缺失 ⇒ **点名拒绝**（**不**返回空列表冒充「没有评审结论」）；
- run_id 缺失 / 空白 ⇒ 点名拒绝；
- **只读**：本模块不写任何 store；**不重算**判据 —— 「门判过」与「门根本没跑」必须可区分
  （那是 GOAL-035 EC-01 把结论放在**求值点**落库的理由）。
"""

from __future__ import annotations

from typing import Any

from packages.application.ports.errors import InvalidInputError


def _finding_row(scoped: Any) -> dict[str, object]:
    """一条评审结论的投影（字段名直白：**一次裁决** + 它的**逐条判词**）。

    为什么 `verdicts` 而不是沿用域字段名 `findings`：外层集合也叫「评审结论」，
    同名会让模型/消费者把「有多少条裁决」与「一条裁决里有几条判据」混起来 ——
    读面命名撞车是**消费方**最先踩到的坑，在这里用不同名字把两层分开。
    """
    finding = scoped.finding
    timestamp = finding.reviewed_at
    return {
        "finding_id": finding.id,
        "task_id": scoped.task_id,
        "contract_id": scoped.contract_id,
        "review_type": finding.review_type,
        "verdict": finding.verdict,
        #: 逐条判词（**逐字**：域在求值点落下的原文，读面不重排、不重算）。
        "verdicts": list(finding.findings),
        "reviewed_by": finding.reviewed_by,
        "reviewed_at": timestamp.value.isoformat() if timestamp else None,
    }


def review_read(findings: Any | None, args: dict[str, object]) -> dict[str, object]:
    """读一次 run 的评审结论（逐条判词 + 它的作用域）。

    计数与逐条**同时**给：只给计数会让「读到了什么」不可复核；只给逐条会让
    「一条都没有」与「读面不可用」不可区分 —— 后者由**点名拒绝**承担（不在这里）。
    """
    if findings is None:
        raise InvalidInputError(
            "review_read requires a ReviewFindingStore, which is not in this assembly"
        )
    run_id = str(args.get("run_id") or "").strip()
    if not run_id:
        raise InvalidInputError("review_read requires a non-empty run_id")
    records = findings.for_run(run_id)
    return {
        "run_id": run_id,
        "count": len(records),
        "reviews": [_finding_row(scoped) for scoped in records],
    }


__all__ = ["review_read"]
