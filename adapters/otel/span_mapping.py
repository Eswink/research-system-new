"""OperationBegin/End → OTel Span 映射(adapters/otel 私有)。

- 显式 parent context(经 `NonRecordingSpan` 携带父 SpanContext)与显式
  start/end 时间戳;不依赖 ambient context(`opentelemetry.context.Context()`
  空上下文 = 显式 root)。
- in-flight span 按 `span_ref` 索引;end 无对应 begin(乱序)或超出 in-flight
  上限时丢弃并计入 drop(fail-open,telemetry 永不抛出)。
- correlation 业务 id 以 `research_os.correlation.*` 属性落在 span 上
  (业务 id 只通过 span correlation 传递,绝不进入 metric label);
  operation attributes 已由词汇层 `sanitize_attributes` 白名单化。
"""

from __future__ import annotations

from datetime import datetime

from opentelemetry import context as otel_context
from opentelemetry import trace as otel_trace
from opentelemetry.trace import Span, SpanContext, Status, StatusCode

from packages.application.observability.signals import (
    OperationBegin,
    OperationEnd,
    OperationOutcome,
)

_CORRELATION_PREFIX = "research_os.correlation."
_SCOPE_ATTRIBUTE = "research_os.scope"
_OUTCOME_ATTRIBUTE = "research_os.outcome"
_FAILURE_CATEGORY_ATTRIBUTE = "research_os.failure_category"
_CORRELATION_FIELDS = (
    "project_id",
    "run_id",
    "phase_run_id",
    "task_id",
    "agent_session_id",
    "tool_call_id",
    "experiment_run_id",
    "eval_run_id",
    "trace_id",
)
_MAX_IN_FLIGHT = 4096

_ERROR_OUTCOMES = frozenset({
    OperationOutcome.FAILED,
    OperationOutcome.TIMEOUT,
    OperationOutcome.CANCELLED,
})

# 空上下文 = 显式 root;绝不读取 ambient/current span,杜绝隐式耦合
_EMPTY_CONTEXT = otel_context.Context()


def _to_nanoseconds(moment: datetime | None) -> int | None:
    """datetime → OTel 纳秒时间戳(整型确定性;None 表示交由 SDK 取当前)。"""
    if moment is None:
        return None
    return int(moment.timestamp()) * 1_000_000_000 + moment.microsecond * 1_000


class SpanMapper:
    """begin/end 信号到真实 OTel Span 的一对一映射。

    两个计数器语义不同,不可合并(M15 复审:原先合并导致健康 run 报幻影 drop):
    - `dropped`:信号**真的丢了**(映射抛错、乱序 end 无对应 begin、in-flight 淘汰);
    - `unlinked`:父引用存在但不可解析,span 仍按 root 正常导出,只是链接降级。
    """

    def __init__(self, tracer: otel_trace.Tracer) -> None:
        self._tracer = tracer
        self._spans: dict[str, Span] = {}
        self._contexts: dict[str, SpanContext] = {}
        self.dropped = 0
        self.unlinked = 0

    def begin(self, begin: OperationBegin) -> None:
        span_ref = begin.span_ref.value
        self._evict_overflow()
        parent_context = self._parent_context(begin.parent_span_ref.value)
        span = self._tracer.start_span(
            begin.name,
            context=parent_context,
            attributes=_begin_attributes(begin),
            start_time=_to_nanoseconds(begin.started_at),
        )
        self._spans[span_ref] = span
        self._contexts[span_ref] = span.get_span_context()

    def end(self, end: OperationEnd) -> bool:
        """结束 span;`span_ref` 未知(乱序 end)时返回 False 并计 drop。"""
        span = self._spans.pop(end.span_ref.value, None)
        if span is None:
            self.dropped += 1
            return False
        self._contexts.pop(end.span_ref.value, None)
        span.set_attribute(_OUTCOME_ATTRIBUTE, end.outcome.value)
        if end.failure_category is not None:
            span.set_attribute(_FAILURE_CATEGORY_ATTRIBUTE, end.failure_category)
        for key, value in end.attributes.items():
            span.set_attribute(key, value)
        span.set_status(_status_for(end))
        span.end(end_time=_to_nanoseconds(end.ended_at))
        return True

    def _parent_context(self, parent_ref: str | None) -> otel_context.Context:
        """父 span 引用 → 显式 parent context;未知父按 root 处理。

        未知父只计 `unlinked`:span 本身照常导出,是链接降级而不是信号丢失。
        典型来源是层级中缺失的祖先(例如未创建 PROJECT span 时的 `run` span)。
        """
        if parent_ref is None:
            return _EMPTY_CONTEXT
        parent_span_context = self._contexts.get(parent_ref)
        if parent_span_context is None:
            self.unlinked += 1
            return _EMPTY_CONTEXT
        return otel_trace.set_span_in_context(
            otel_trace.NonRecordingSpan(parent_span_context),
            _EMPTY_CONTEXT,
        )

    def _evict_overflow(self) -> None:
        while len(self._spans) >= _MAX_IN_FLIGHT:
            oldest = next(iter(self._spans))
            self._spans.pop(oldest)
            self._contexts.pop(oldest, None)
            self.dropped += 1


def _begin_attributes(begin: OperationBegin) -> dict[str, str | int | bool]:
    attributes: dict[str, str | int | bool] = dict(begin.attributes)
    attributes[_SCOPE_ATTRIBUTE] = begin.scope.value
    for field_name in _CORRELATION_FIELDS:
        value = getattr(begin.correlation, field_name)
        if value is not None:
            attributes[_CORRELATION_PREFIX + field_name] = value
    return attributes


def _status_for(end: OperationEnd) -> Status:
    if end.outcome in _ERROR_OUTCOMES:
        return Status(StatusCode.ERROR, description=end.failure_category)
    if end.outcome is OperationOutcome.OK:
        return Status(StatusCode.OK)
    return Status(StatusCode.UNSET)
