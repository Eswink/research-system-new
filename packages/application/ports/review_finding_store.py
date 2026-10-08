"""ReviewFindingStore Port：验收门求值结论的 canonical 记录（GOAL-20261008-035 EC-01）。

为什么需要它：`GateOutcome.evaluations`（逐条判据 + 逐字判词）此前**只有被拒的路径**
带进失败消息（`gate_rejection_reason`），通过的路径上判词哪里都读不到 —— `ReviewFinding`
与 `Decision` 都是纯内存对象、从不持久化。于是「覆盖判据在这一次 run 里真的判过、
两个维度各自的数是多少」不可复核。

**记录，不是重算**：读面必须能区分「门判过」与「门根本没跑」。派生式读面（读取时按
canonical 事实重跑一遍判据）做不到这一点 —— 它会在一扇从未求值的门上照样给出结论。
因此结论在**求值点**落库，读面只读。

作用域（`ScopedReviewFinding`）与结论分开：`ReviewFinding` 是既有域类型（它不含
run/task 归属），归属由存储面承担，不改域类型。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from packages.domain.evidence import ReviewFinding


@dataclass(frozen=True, slots=True)
class ScopedReviewFinding:
    """一条评审结论 + 它的作用域（哪个 run 的哪个 task、按哪份合约判的）。"""

    finding: ReviewFinding
    run_id: str
    task_id: str
    contract_id: str


@runtime_checkable
class ReviewFindingStore(Protocol):
    """append-only 的评审结论存储（同一 finding id 重复写是幂等空操作）。"""

    def put(self, scoped: ScopedReviewFinding) -> None: ...

    def for_run(self, run_id: str) -> tuple[ScopedReviewFinding, ...]: ...

    def close(self) -> None: ...
