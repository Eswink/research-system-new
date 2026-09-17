"""Port 错误模型：跨 Port 的统一失败分类与 retry 语义。

所有 Port 实现（Fake 与真实 adapter）必须抛出本层次内的异常，
禁止把 provider-specific 异常泄漏到 application/domain。
异常消息统一经过 redaction（packages.domain.redaction）。

- TransientPortError：可重试（网络、限流、超时、worker 丢失）。
- PermanentPortError：不可重试（配置、auth、schema 不匹配、损坏）。
- InvalidInputError：调用方输入非法，属调用方 bug。
- PortCancelledError：调用被取消。取消不属于 FailureCategory taxonomy
  （docs/reliability/FAILURE_MODEL.md 无取消类），因此 failure_category 为 None，
  调用方以独立信号识别，绝不当作 transient 重试。
"""

from __future__ import annotations

from packages.domain.enums import FailureCategory
from packages.domain.redaction import redact_exception_message


class PortError(Exception):
    """Port 失败基类；message 已 redaction。"""

    failure_category: FailureCategory | None
    retryable: bool

    def __init__(
        self,
        message: str,
        *,
        failure_category: FailureCategory | None,
        retryable: bool,
    ) -> None:
        super().__init__(redact_exception_message(message))
        self.failure_category = failure_category
        self.retryable = retryable


class TransientPortError(PortError):
    """瞬时失败；调用方可按 retry policy 重试。"""

    def __init__(self, message: str, *, failure_category: FailureCategory) -> None:
        super().__init__(message, failure_category=failure_category, retryable=True)


class PermanentPortError(PortError):
    """永久失败；重试不会改变结果。"""

    def __init__(self, message: str, *, failure_category: FailureCategory) -> None:
        super().__init__(message, failure_category=failure_category, retryable=False)


class InvalidInputError(PermanentPortError):
    """输入非法（调用方 bug）；重试无意义。"""

    def __init__(self, message: str) -> None:
        super().__init__(message, failure_category=FailureCategory.VALIDATION_FAILURE)


class RetryNotDueError(InvalidInputError):
    """重排还没到 `retry_at`：现在不是交付时机，**不是**调用方 bug。

    与别的 InvalidInputError 区分开，调用方据此重新停车（等 deadline）而不是把 run
    判失败（PLAN-20260915-081）。对既有调用方它仍然是一个 InvalidInputError——
    "deadline 之前不得交付"这条不变量对外语义不变。
    """


class PortTimeoutError(TransientPortError):
    """超时；属于瞬时失败，可重试。"""

    def __init__(self, message: str, *, failure_category: FailureCategory) -> None:
        super().__init__(message, failure_category=failure_category)


class PortCancelledError(PortError):
    """调用已被取消；不得作为 transient 失败重试。"""

    def __init__(self, message: str) -> None:
        super().__init__(message, failure_category=None, retryable=False)
