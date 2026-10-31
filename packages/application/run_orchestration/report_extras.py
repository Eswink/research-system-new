"""报告相的**附加装配链**（GOAL-20261031-102；v1 手稿装完之后依次执行）。

**为什么单列一个模块**：`manuscript_assembly.py` 贴着 450 行硬上限（规模门），而附加链
的**编排**（谁先谁后、缺件时各自怎么收）是一段可独立读的逻辑。本模块只做编排 ——
每一件附加产物的实现住在自己的模块里：

1. **改稿闭环**（`revision_assembly.revision_closure_step`）：本 run 带改稿正文 ⇒
   装 `manuscript_v2.md`（`supersedes` → v1，父指针经域层链校验）+ **校验每一条
   `action_taken` 的引用**。它在应答信**之前**：信的引用判据要指着 v2 在场的状态。
2. **投稿包**（`submission_assembly.maybe_assemble_submission`）：本 run 带投稿会话
   产物 ⇒ 装五件投稿制品（`cover_letter.md` 等经装配路径落到 canonical）。
3. **应答信**（`manuscript_assembly.maybe_assemble_response_letter`，既有行为）：最后写。

**顺序即判据**：改稿闭环在前（引用校验失败 ⇒ 报告任务 `EXECUTION_FAILURE`，不应答信
不会被产出）；投稿包在改稿之后（`data_availability.md` 的制品清单要读到 v2 在场的
状态 —— 投稿包 accompany 的是**改完之后**的稿子）。

每一格都遵守同一纪律：本 run 没有那格的前置产物 ⇒ 那格是 `None`（正确读数，不是失败）；
前置产物在但不可用 ⇒ 点名抛错，由报告任务以 `EXECUTION_FAILURE` 收敛。
"""

from __future__ import annotations

from typing import Any


def assemble_report_extras(deps: Any, spec_context: Any, run_id: str, result: Any) -> Any:
    """v1 手稿装完后的附加链；`result` 原样透传（报告任务的返回值不变）。

    `deps` 是 `ReportTaskDeps`（artifacts / ledger / reviews 已接；缺装配的判法在
    各实现模块里，本函数不重复判）。`spec_context.run` 是**在场的那份 run 实体**
    （执行期间控制面还没把 run 行落库，去存储读只会读到「未知 run」）。
    """
    from packages.application.run_orchestration.manuscript_assembly import (
        maybe_assemble_response_letter,
    )
    from packages.application.run_orchestration.revision_assembly import revision_closure_step
    from packages.application.run_orchestration.submission_assembly import (
        maybe_assemble_submission,
    )

    revision_closure_step(
        deps.artifacts,
        deps.ledger,
        deps.reviews,
        spec_context.run,
        run_id,
        created_by=spec_context.agent.id,
    )
    maybe_assemble_submission(deps.artifacts, deps.ledger, spec_context.run, run_id)
    maybe_assemble_response_letter(deps.artifacts, deps.ledger, deps.reviews, run_id)
    return result


__all__ = ["assemble_report_extras"]
