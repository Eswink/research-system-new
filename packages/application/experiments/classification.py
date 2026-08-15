"""实验执行结果分类（纯函数，M9）。

NEGATIVE_RESULT 语义（DoD）：科学负结论 ≠ 执行失败。
- exit 0 + 声明 NEGATIVE_RESULT/FAILED → NEGATIVE_RESULT（科学结论）；
- 非零退出 / timeout / crash → FAILED / TIMED_OUT（执行失败），即使
  输出自称 NEGATIVE_RESULT 也不采信；
- exit 0 但缺 experiment_result.json → 输出契约违约 → FAILED。
"""

from __future__ import annotations

from packages.application.experiments.types import RESULT_FILE
from packages.domain.experiment_state import ExperimentRunState
from packages.domain.workspace import ExecutionRun, ExecutionStatus


def image_digest_from_run(execution_run: ExecutionRun) -> str | None:
    """从 ExecutionRun.compute_usage_summary 提取实际镜像 digest。"""
    image_digest = execution_run.compute_usage_summary.get("image_digest")
    return str(image_digest) if isinstance(image_digest, str) and image_digest else None


def execution_failure_reason(status: ExecutionStatus) -> str | None:
    if status is ExecutionStatus.TIMED_OUT:
        return "execution timed out"
    if status is ExecutionStatus.FAILED:
        return "execution failed"
    return None


def classify_outcome(
    execution_status: ExecutionStatus, declared_status: str | None
) -> tuple[str, str | None]:
    """execution 终态 + 声明科学结论 → (ExperimentRun event, failure_reason)。"""
    if execution_status is ExecutionStatus.TIMED_OUT:
        return ExperimentRunState.Transition.COMPLETE_TIMED_OUT, None
    if execution_status is ExecutionStatus.CANCELLED:
        return ExperimentRunState.Transition.CANCEL, None
    if execution_status is ExecutionStatus.FAILED:
        return ExperimentRunState.Transition.COMPLETE_FAILED, None
    if declared_status is None:
        return (
            ExperimentRunState.Transition.COMPLETE_FAILED,
            f"missing {RESULT_FILE} (experiment output contract violation)",
        )
    if declared_status == "SUCCEEDED":
        return ExperimentRunState.Transition.COMPLETE_SUCCESS, None
    return (
        ExperimentRunState.Transition.COMPLETE_NEGATIVE,
        f"declared scientific outcome: {declared_status}",
    )
