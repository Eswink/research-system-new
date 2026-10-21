"""GOAL-20261022-093 判据的**共享支持件**（规模门：单文件 ≤ 450 行）。

**为什么单独成模块**：判据文件本身会被规模门判（`tests/**` 同样受 450/50 两条约束），
而「造一条判词」「接产品闭包」这两件事在**纯视图**判据与**产品路径**判据里各用一次，
逐字复制会让两份实现漂 —— 与 `tests/e2e/review_read_support.py` 的拆分同一手法。

**如实边界**：本模块不含用例，只放装配与夹具。`_splitting()` 造的是**判词**（两位评审者
在两个不同执行目标上各说一句），**不是**被评对象的结论 —— 后者由真实 run 自己产生。
"""

from __future__ import annotations

from typing import Any

from packages.application.ports.review_finding_store import ScopedReviewFinding
from packages.domain.evidence import ReviewFinding

#: 本 GOAL 判据用的协议（与 GOAL-082 EC-04 的跨 run 判据同一份：三段都有真实会话）。
PROTOCOL = "grounded_report_chain_v1.yaml"
#: 立题格的合约 id（判据按它取那一次会话的 spec）。
PLAN_CONTRACT = "research_report_plan"
#: 两个评审者的执行目标（与 GOAL-084/091 出厂目录里的两个模型同名）。
GLM = "main/glm-5.3"
KIMI = "main/kimi-k2.6"


class Scope:
    """一份判词的作用域（参数对象，守住函数签名 <= 5）。"""

    def __init__(
        self,
        *,
        run_id: str = "run-1",
        task_id: str = "task-1",
        contract_id: str = "contract-1",
        reviewer: str = "reviewer_a",
        phase_id: str | None = "review",
    ) -> None:
        self.run_id = run_id
        self.task_id = task_id
        self.contract_id = contract_id
        self.reviewer = reviewer
        self.phase_id = phase_id


def scoped(
    finding_id: str,
    *,
    scope: Scope | None = None,
    verdict: str = "PASS",
    model: str | None = GLM,
    findings: list[str] | None = None,
) -> ScopedReviewFinding:
    """一条落库形态的判词（`reviewed_by` 是 `gate:<agent>`，`reviewer_model` 是执行目标）。"""
    where = scope or Scope()
    return ScopedReviewFinding(
        finding=ReviewFinding(
            id=finding_id,
            review_type="acceptance_gate",
            verdict=verdict,
            findings=list(findings or [f"{finding_id} wording"]),
            reviewed_by=f"gate:{where.reviewer}",
            reviewer_model=model,
        ),
        run_id=where.run_id,
        task_id=where.task_id,
        contract_id=where.contract_id,
        phase_id=where.phase_id,
    )


def splitting() -> tuple[ScopedReviewFinding, ScopedReviewFinding]:
    """一负一过（两位**不同的执行目标**）—— GOAL-091 真跑读到的那个形态。"""
    first = scoped("f-a", verdict="REJECT", model=GLM, findings=["too shallow"])
    second = scoped(
        "f-b",
        scope=Scope(reviewer="reviewer_b"),
        verdict="PASS",
        model=KIMI,
        findings=["adequate"],
    )
    return first, second


def write_findings(store: Any, run_id: str, records: tuple[ScopedReviewFinding, ...]) -> None:
    """把判词落到**指定的** run 上（原记录的作用域在这里被替换成真实 run id）。"""
    for record in records:
        store.put(
            ScopedReviewFinding(
                finding=record.finding,
                run_id=run_id,
                task_id=record.task_id,
                contract_id=record.contract_id,
                phase_id=record.phase_id,
            )
        )


def product_read(deps: Any, run_id: str) -> Any:
    """经**产品闭包**问一次（与两个组合根同一处装配；判据不自己造闭包）。"""
    from services.api.review_outcome_support import review_outcome_builder

    return review_outcome_builder({
        "runs_store": deps.runs_store,
        "review_findings": deps.review_findings,
    })(run_id)


__all__ = [
    "GLM",
    "KIMI",
    "PLAN_CONTRACT",
    "PROTOCOL",
    "Scope",
    "product_read",
    "scoped",
    "splitting",
    "write_findings",
]
