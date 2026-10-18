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

from packages.application.evaluation.panel_verdict import aggregate_panel
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
        #: **被评对象**的那一格（GOAL-20261018-086 EC-02）。`None` = 该记录没有这一格
        #: （迁移前的既有行 / 调用方未提供）⇒ 它只参与 `scope="TASK"` 的小组，
        #: 不被并进任何 phase 小组。
        "phase_id": getattr(scoped, "phase_id", None),
        "review_type": finding.review_type,
        "verdict": finding.verdict,
        #: 逐条判词（**逐字**：域在求值点落下的原文，读面不重排、不重算）。
        "verdicts": list(finding.findings),
        "reviewed_by": finding.reviewed_by,
        #: 评审者**跑在哪个模型上**（`endpoint/model_name`；GOAL-20261018-085 EC-01）。
        #: `None` = 该条判词未声明该面 —— **不是**「同一个模型」，也不得读成「独立」。
        "reviewer_model": finding.reviewer_model,
        "reviewed_at": timestamp.value.isoformat() if timestamp else None,
    }


def _panel_rows(records: tuple[Any, ...]) -> list[dict[str, object]]:
    """本 run 的**评审小组**聚合（advisory；GOAL-20261018-085 EC-02/EC-03）。

    少于两份可归因的判词 ⇒ 该组不出现（**单评审不聚合**：既有读面逐字不变）。

    **分组键是被评对象，不是「谁在评」**（GOAL-20261018-086 EC-01）：运行链给同一 phase 的
    **每个**评审 agent 各生成一个 `ResearchTask`（`resolve_sessions` 逐个 agent 展开），
    而判词 id 又是 `finding:{task_id}:gate` ⇒ 按 `task_id` 分组时，每个任务下**至多一条**
    判词，多评审阶段的小组因此**永远不存在**（实测：两位评审者 ⇒ `count: 2, panels: 0`）。

    于是分两档，**各自都明写射程**：

    - 记录带 `phase_id` ⇒ 按 `(phase, contract)` 分组，`scope="PHASE"` —— 覆盖同一 phase
      上**全部**评审者（多评审阶段要的正是这个）；
    - 记录没有 `phase_id`（迁移前的既有行 / 调用方未提供）⇒ 沿用 `(task, contract)`，
      `scope="TASK"` —— **迁移前语义逐字保留**，不把旧行并进别人的组。

    **不把两档混成一组**：键的第一位就是档位名，混组会让「多数票」的口径在同一行里漂移。
    组序按键排序 ⇒ 稳定。
    """
    groups: dict[tuple[str, str, str], list[Any]] = {}
    for scoped in records:
        phase_id = getattr(scoped, "phase_id", None)
        key = (
            ("PHASE", str(phase_id), str(scoped.contract_id))
            if phase_id
            else ("TASK", str(scoped.task_id), str(scoped.contract_id))
        )
        groups.setdefault(key, []).append(scoped.finding)
    rows: list[dict[str, object]] = []
    for key, group in sorted(groups.items()):
        verdict = aggregate_panel(group)
        if verdict is None:
            continue
        scope, owner, contract_id = key
        #: 这一行的**射程**（`PHASE` = 同 phase 全部评审者；`TASK` = 单个任务）。
        #: 调用方据此判断「多数票」覆盖了谁 —— 少了这一格，两种口径在载荷上不可区分。
        row: dict[str, object] = {"scope": scope, "contract_id": contract_id}
        row["phase_id" if scope == "PHASE" else "task_id"] = owner
        rows.append({**row, **verdict.as_payload()})
    return rows


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
    panels = _panel_rows(records)
    return {
        "run_id": run_id,
        "count": len(records),
        "reviews": [_finding_row(scoped) for scoped in records],
        #: 评审小组的 advisory 聚合（逐票 + 分歧 + 独立性）。**空列表** = 本 run 没有任何
        #: 被评对象上存在两份及以上可归因判词 —— 那是「没有小组」这个事实，不是读面失败
        #: （读面失败由 `InvalidInputError` 点名，两者不可混淆）。每行带 `scope`
        #: （`PHASE` / `TASK`）：两种聚合口径的射程**不同**，载荷上必须可区分。
        "panels": panels,
        "panel_count": len(panels),
    }


__all__ = ["review_read"]
