"""闭集 attribute / metric 词汇与 sanitize 守卫。

- `AttributeKey`:span attributes 的闭集 allow-list(新增键必须显式审计隐私与
  cardinality)。`sanitize_attributes` 只保留白名单键、强制为稳定标量、对指定
  键做 `redact_text` 并截断到 256 字符。
- `MetricName` / `MetricKind` / `MetricLabel`:metrics 的闭集;metric label 绝不
  含高基数业务 id(run/task/trace/phase/experiment/eval id 或任意原文/path/body)。
  业务 id 只通过 span attributes (correlation) 传递。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from packages.domain.redaction import redact_text

_MAX_ATTRIBUTE_LENGTH = 256


class AttributeKey(StrEnum):
    provider = "provider"
    endpoint_id = "endpoint_id"
    model_id = "model_id"
    tool_id = "tool_id"
    resource_type = "resource_type"
    attempt = "attempt"
    retry_count = "retry_count"
    status_code_class = "status_code_class"
    failure_category = "failure_category"
    prompt_tokens = "prompt_tokens"
    completion_tokens = "completion_tokens"
    total_tokens = "total_tokens"
    payload_digest = "payload_digest"
    payload_size = "payload_size"
    queue_lag_ms = "queue_lag_ms"
    lease_ttl_seconds = "lease_ttl_seconds"
    circuit_state = "circuit_state"
    verdict = "verdict"
    scorer_count = "scorer_count"
    reviewer_count = "reviewer_count"
    dataset_digest = "dataset_digest"
    image_digest = "image_digest"
    exit_code = "exit_code"
    oom_killed = "oom_killed"
    scheduled_retry = "scheduled_retry"
    dropped = "dropped"
    drained = "drained"


_ALL_ATTR_KEYS = frozenset(AttributeKey)

# 字符串型键经 redaction 的集合(provider/model/tool identity 不进原文)
_REDACTED_ATTRS = frozenset({AttributeKey.provider, AttributeKey.model_id, AttributeKey.tool_id})


def sanitize_attributes(attributes: dict[str, Any]) -> dict[str, str | int | bool]:
    """闭集 allow-list + 标量强制 + redaction/截断;未知键与一切非标量被丢弃。

    `_REDACTED_ATTRS` 中的字符串值需先经 `redact_text` 再截断;其余字符串只截断。
    """
    sanitized: dict[str, str | int | bool] = {}
    for key, value in attributes.items():
        try:
            attr_key = AttributeKey(key)
        except ValueError:
            continue
        if isinstance(value, bool):
            sanitized[key] = value
        elif isinstance(value, int) and not isinstance(value, bool):
            sanitized[key] = value
        elif isinstance(value, str):
            text = value
            if len(text) > _MAX_ATTRIBUTE_LENGTH:
                text = text[:_MAX_ATTRIBUTE_LENGTH]
            if attr_key in _REDACTED_ATTRS:
                text = redact_text(text)
            sanitized[key] = text
    return sanitized


class MetricKind(StrEnum):
    COUNTER = "COUNTER"
    HISTOGRAM = "HISTOGRAM"


class MetricLabel(StrEnum):
    """闭集 metric label allow-list;绝不含高基数 id 或原文。"""

    provider = "provider"
    model_id = "model_id"
    tool_id = "tool_id"
    scope = "scope"
    outcome = "outcome"
    failure_category = "failure_category"
    resource_type = "resource_type"


_ALL_METRIC_LABELS = frozenset(MetricLabel)


class MetricName(StrEnum):
    LLM_CALL_DURATION_MS = "research_os.llm_call.duration_ms"
    LLM_CALL_RETRY_ATTEMPTS = "research_os.llm_call.retry_attempts"
    TOOL_CALL_DURATION_MS = "research_os.tool_call.duration_ms"
    WORKFLOW_TASK_DURATION_MS = "research_os.workflow.task.duration_ms"
    WORKFLOW_QUEUE_LAG_MS = "research_os.workflow.queue_lag_ms"
    WORKFLOW_LEASE_EXPIRED = "research_os.workflow.lease.expired_total"
    OUTBOX_BACKLOG = "research_os.outbox.backlog"
    OUTBOX_DRAINED = "research_os.outbox.drained_total"
    EXPERIMENT_DURATION_SECONDS = "research_os.experiment.duration_seconds"
    EVAL_RUN_DURATION_MS = "research_os.eval_run.duration_ms"
    EVAL_INFRA_ERRORS = "research_os.eval_run.infra_errors_total"
    EVAL_MISSING_EVALUATIONS = "research_os.eval_run.missing_evaluations_total"
    SCHEDULER_PASS = "research_os.scheduler.pass_total"
    TELEMETRY_DROPPED = "research_os.telemetry.dropped_total"
    TELEMETRY_EXPORT_QUEUE_DEPTH = "research_os.telemetry.export_queue_depth"


@dataclass(frozen=True, slots=True)
class MetricSample:
    """一次 metric 采样;label 必须全部属于 `MetricLabel`。"""

    name: MetricName
    kind: MetricKind
    value: int | float
    labels: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.labels and (set(self.labels) - _ALL_METRIC_LABELS):
            unknown = sorted(set(self.labels) - _ALL_METRIC_LABELS)
            raise ValueError(f"metric labels must be from MetricLabel: {unknown}")
        if self.kind is MetricKind.COUNTER and isinstance(self.value, float):
            raise ValueError("COUNTER metrics must have int values")
