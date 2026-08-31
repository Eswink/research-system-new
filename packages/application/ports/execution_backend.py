"""ExecutionBackend Port：执行命令/脚本（WORKSPACE_RUNTIME.md §5）。

职责：执行 ExecutionSpec（command/backend_kind/resource_profile），返回
归一化 ExecutionRun；支持 timeout 与资源限制；compute usage 以摘要形式
返回（记账由 application 归账后入 BudgetLedger，本 Port 不记账）。
非职责：不管理文件布局与 Lease（WorkspaceBackend）；不解析凭据。

M5 决策 D2：同步语义；timeout 产生 ExecutionStatus.TIMED_OUT 而不是异常。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from packages.domain.workspace import ExecutionRun, ExecutionSpec


@runtime_checkable
class ExecutionBackend(Protocol):
    """沙箱/后端执行契约。"""

    def execute(
        self,
        spec: ExecutionSpec,
        timeout_seconds: int | None = None,
        *,
        cancelled: Callable[[], bool] | None = None,
    ) -> ExecutionRun:
        """执行 spec；`cancelled` 是可选协作式取消探针（M16）。

        默认 None = 既有行为不变。提供时，实现应在轮询/等待期间周期性调用它，
        返回 True 则停止执行并产出 `ExecutionStatus.CANCELLED`。与
        `GovernedExperimentExecutor` 的取消回调模式一致，避免为取消再造机制。
        """
        ...

    def close(self) -> None: ...
