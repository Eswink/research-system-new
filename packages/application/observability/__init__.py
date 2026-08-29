"""Research OS 内部观测词汇(packages/application/observability)。

M15 观测的自营稳定语义(ADR-0026):operation scope/outcome、span 引用派生、
闭集 attribute/metric 词汇、`operation()` 上下文管理器。无内容通道。
"""

from packages.application.observability.attributes import (
    AttributeKey,
    MetricKind,
    MetricLabel,
    MetricName,
    MetricSample,
    sanitize_attributes,
)
from packages.application.observability.scope import (
    operation,
    parent_span_ref,
    span_ref_of,
)
from packages.application.observability.signals import (
    CorrelationRef,
    OperationBegin,
    OperationEnd,
    OperationOutcome,
    OperationScope,
    ParentSpanRef,
    SpanRef,
    outcome_is_error,
)

__all__ = [
    "AttributeKey",
    "CorrelationRef",
    "MetricKind",
    "MetricLabel",
    "MetricName",
    "MetricSample",
    "OperationBegin",
    "OperationEnd",
    "OperationOutcome",
    "OperationScope",
    "ParentSpanRef",
    "SpanRef",
    "operation",
    "outcome_is_error",
    "parent_span_ref",
    "sanitize_attributes",
    "span_ref_of",
]
