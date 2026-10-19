"""程序推进的**守护线程**（自 `scheduler.py` 拆出：规模门 + GOAL-20261019-089 EC-03）。

拆法与全仓一致：「执行体定义」与「调度基础设施（`PeriodicDaemon` / 其余线程）」分列。
**语义逐字未动**：本类只把 `PeriodicDaemon` 与 `program_advance.advance_for` 接起来。
"""

from __future__ import annotations

from typing import Any

from packages.application.observability.scope import operation
from packages.application.observability.signals import OperationOutcome, OperationScope
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.domain.schedules import ScheduleJob
from services.api.scheduler import PeriodicDaemon


class ProgramAdvanceScheduler(PeriodicDaemon):
    """按落库事实**周期推进研究程序**（GOAL-20261019-089 EC-03）。

    **它补哪一格**：`ResearchProgram` 域与 `advance_program` 早就齐备，但唯一的产品
    调用点是 `POST /programs/{id}/advance` —— 程序在**第 N 轮终态后必须有人点一下**
    才进入第 N+1 轮。本守护线程周期地调**同一个装配**（`program_advance.advance_for`），
    因此「自动」与「手动」的判词、幂等去重（`DEDUP`）与失败面**逐字相同**。

    **三条边界**（不越界）：

    - **不新增闸门语义**：声明的闸门（`WAIT_FOR_APPROVAL` / 判词条件式 / 多点 / 混合式）
      由 `advance_program` 原样判定；本类只负责**调用**它；
    - **单程序失败不中断整轮**：一个程序的推进抛错 ⇒ 记在该轮的计数里继续下一个
      （与既有派发线程同一纪律）；整轮失败才让 `last_outcome=FAILED`；
    - **没有 program store 就没有执行体**：组合根不接时 `executor_attached=false`
      （读面如实标注，不伪装）。
    """

    job = ScheduleJob.PROGRAM_ADVANCE
    thread_name = "program-advance"

    def __init__(
        self,
        deps: Any,
        *,
        interval_seconds: float = 30.0,
        telemetry: TelemetrySink | None = None,
        control: Any = None,
    ) -> None:
        super().__init__(interval_seconds=interval_seconds, control=control)
        self._deps = deps
        self._telemetry = telemetry
        #: 最近一轮的读数（判据与读面可核：推进了几个、失败几个）。
        self.last_report: dict[str, int] = {}

    def _execute_pass(self) -> dict[str, int]:
        """一轮：对每个已登记程序调用**同一条**推进装配（单程序失败不清零整轮）。"""
        from services.api.program_advance import advance_for

        with operation(
            self._telemetry,
            scope=OperationScope.WORKFLOW_QUEUE,
            name="program.advance_pass",
        ) as op:
            store = getattr(self._deps, "program_store", None)
            if store is None:
                self.last_report = {"advanced": 0, "started": 0, "failed": 0}
                return self.last_report
            advanced = started = failed = 0
            for program in self._programs(store):
                try:
                    result = advance_for(self._deps, program.id)
                except Exception:  # noqa: BLE001 - 单个程序失败不拖垮整轮
                    failed += 1
                    continue
                advanced += 1
                if result.started_run_id is not None:
                    started += 1
            self.last_report = {"advanced": advanced, "started": started, "failed": failed}
            if failed:
                op.set_outcome(OperationOutcome.FAILED, "program_advance_partial")
            return self.last_report

    def _programs(self, store: Any) -> list[Any]:
        """**全部**已登记程序（按 id 排序：装配顺序不渗进推进顺序）。

        枚举面来自**项目注册表**（`ProjectStore.list_projects`，与 `GET /projects` 同一读面）
        + 内置 `example-project`（它由 examples 合约合成、可能不在注册行里）。
        **不**用 run 存储反推：程序可以先于任何 run 存在（那时它正需要被推进）。
        """
        project_ids = {"example-project"}
        project_store = getattr(self._deps, "project_store", None)
        if project_store is not None:
            project_ids.update(item.id for item in project_store.list_projects())
        programs: list[Any] = []
        for project_id in sorted(project_ids):
            programs.extend(store.for_project(project_id))
        return sorted(programs, key=lambda item: item.id)
