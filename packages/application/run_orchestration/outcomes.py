"""执行链的结果值对象（GOAL-004 cycle 3：从 `phase_runner` 拆出，供多个模块共用）。

`phase_runner` 触到 450 行硬上限，把两个**纯数据**结果对象搬到这里；`phase_runner`
仍然从本模块导入并对外保持同名可见（既有 `from ...phase_runner import RunOutcome`
不受影响），依赖方向是 phase_runner → outcomes，无环。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.domain.tasks import ResearchTask


@dataclass(frozen=True, slots=True)
class TaskOutcome:
    task: ResearchTask
    outcome: str
    verdict: str | None = None
    message: str = ""
    # GOAL-004 cycle 3：这条终局失败是**哪条策略允许的**（None = 成功 / 未走策略；
    # "CONTINUE" = 契约声明容忍 ⇒ 失败被记账但没停住 run）。
    failure_policy: str | None = None


@dataclass(frozen=True, slots=True)
class RunOutcome:
    run_id: str
    state: str
    message: str = ""
    tasks: tuple[TaskOutcome, ...] = ()
    manifest_digest: str | None = None
    # cycle 20：语义 digest 与定价引用同源处理——不随执行结果回填，HTTP 边界就会
    # 静默丢字段，而 resume 的漂移校验（assert_semantics_frozen）恰恰只认它。
    manifest_semantic_digest: str | None = None
    # M15 定价冻结引用(BLOCKER-6):service 在 Manifest freeze 后把这两个
    # 字段回填执行结果，API 再持久化到 ResearchRun；不能只存 manifest digest
    # 否则 run 行会在 HTTP 边界静默丢失冻结价格引用。
    pricing_version: str | None = None
    pricing_digest: str | None = None
    handoff_digests: tuple[str, ...] = ()
    system_failure: bool = False
