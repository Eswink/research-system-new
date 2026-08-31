"""FakeExecutionBackend：可配置执行结果（timeout/失败分类注入）。"""

from __future__ import annotations

from collections.abc import Callable

from adapters.fakes.base import FakeBase
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Timestamp
from packages.domain.enums import FailureCategory
from packages.domain.workspace import ExecutionRun, ExecutionSpec, ExecutionStatus


class FakeExecutionBackend(FakeBase):
    """execute 按配置返回 ExecutionRun；timeout_seconds 生效时返回 TIMED_OUT。"""

    def __init__(
        self,
        *,
        status: ExecutionStatus = ExecutionStatus.SUCCEEDED,
        duration_seconds: int = 0,
        exit_code: int = 0,
        failure_category: FailureCategory | None = None,
        run_id_prefix: str = "run",
    ) -> None:
        super().__init__("execution_backend")
        self._status = status
        self._duration = duration_seconds
        self._exit_code = exit_code
        self._failure_category = failure_category
        self._run_id_prefix = run_id_prefix
        self._counter = 0

    def execute(
        self,
        spec: ExecutionSpec,
        timeout_seconds: int | None = None,
        *,
        cancelled: Callable[[], bool] | None = None,
    ) -> ExecutionRun:
        self._enter("execute", spec.command)
        if not spec.command:
            self._record("execute", "", error="InvalidInputError")
            raise InvalidInputError("execution command must not be empty")
        self._counter += 1
        if cancelled is not None and cancelled():
            status = ExecutionStatus.CANCELLED
            category = None
        else:
            timed_out = timeout_seconds is not None and self._duration > timeout_seconds
            status = ExecutionStatus.TIMED_OUT if timed_out else self._status
            category = self._failure_category
            if status is ExecutionStatus.FAILED and category is None:
                category = FailureCategory.EXECUTION_FAILURE
        started = Timestamp.now()
        completed = Timestamp.now()
        run = ExecutionRun(
            run_id=f"{self._run_id_prefix}-{self._counter}",
            spec=spec,
            status=status,
            started_at=started,
            completed_at=completed,
            exit_code=self._exit_code,
            failure_category=category,
        )
        self._record("execute", spec.command, result=status.value)
        return run
