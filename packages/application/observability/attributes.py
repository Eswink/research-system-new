"""闭集 attribute / metric 词汇与 sanitize 守卫。

- `AttributeKey`:span attributes 的闭集 allow-list(新增键必须显式审计隐私与
  cardinality)。`sanitize_attributes` 只保留白名单键、强制为稳定标量、对**全部**
  字符串键先 `redact_text` 再截断到 256 字符。
  顺序很重要:先截断后脱敏会把凭据切断,使 redaction 正则失配并泄漏残片
  (M15 复审实测 24 位 DSN 密码泄漏 20 位)。
- `MetricName` / `MetricKind` / `MetricLabel`:metrics 的闭集;metric label 绝不
  含高基数业务 id(run/task/trace/phase/experiment/eval id 或任意原文/path/body)。
  业务 id 只通过 span attributes (correlation) 传递。label **值**同样有界:
  脱敏 + 64 字符上限,`scope`/`outcome` 强制落在对应枚举内(越界折叠为 `other`),
  避免 metric backend 因无界标签值失控。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from packages.application.observability.signals import (
    OperationOutcome,
    OperationScope,
    is_allowed_failure_category,
)
from packages.domain.redaction import redact_text

_MAX_ATTRIBUTE_LENGTH = 256
_MAX_LABEL_LENGTH = 64
_LABEL_OVERFLOW_SENTINEL = "other"


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


def sanitize_attributes(attributes: dict[str, Any]) -> dict[str, str | int | bool]:
    """闭集 allow-list + 标量强制 + redaction/截断;未知键与一切非标量被丢弃。

    **全部**字符串值先经 `redact_text` 再截断——顺序反了会把凭据切成正则失配的
    残片（M15 复审实测）。原先只有 provider/model_id/tool_id 三键脱敏，其余九个
    字符串键（endpoint_id / status_code_class / circuit_state / verdict /
    payload_digest / dataset_digest / image_digest / failure_category /
    resource_type）明文导出。
    """
    sanitized: dict[str, str | int | bool] = {}
    for key, value in attributes.items():
        try:
            AttributeKey(key)
        except ValueError:
            continue
        if isinstance(value, bool):
            sanitized[key] = value
        elif isinstance(value, int) and not isinstance(value, bool):
            sanitized[key] = value
        elif isinstance(value, str):
            sanitized[key] = redact_text(value)[:_MAX_ATTRIBUTE_LENGTH]
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
_ENUM_LABEL_DOMAINS: dict[str, frozenset[str]] = {
    MetricLabel.scope.value: frozenset(member.value for member in OperationScope),
    MetricLabel.outcome.value: frozenset(member.value for member in OperationOutcome),
}


def sanitize_metric_labels(labels: dict[str, str]) -> dict[str, str]:
    """metric label 值定界:脱敏 + 64 字符上限 + 枚举域折叠。

    键的闭集由 `MetricSample.__post_init__` 强制;本函数只处理**值**——
    M15 复审实测 `record_metric` 对值零校验,完整 `Bearer …` / `sk-…` / DSN
    可作为 label 导出,且 `scope`/`outcome` 可为任意自由文本(无界基数)。
    越界枚举值折叠为 `other` 而非抛错:label 由业务路径构造,抛错会在
    fail-open 外壳**之外**制造新的崩溃面。
    """
    sanitized: dict[str, str] = {}
    for key, value in labels.items():
        domain = _ENUM_LABEL_DOMAINS.get(key)
        if domain is not None:
            sanitized[key] = value if value in domain else _LABEL_OVERFLOW_SENTINEL
            continue
        if key == MetricLabel.failure_category.value and not is_allowed_failure_category(value):
            sanitized[key] = _LABEL_OVERFLOW_SENTINEL
            continue
        sanitized[key] = redact_text(value)[:_MAX_LABEL_LENGTH]
    return sanitized


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
    """一次 metric 采样;label 键必须属于 `MetricLabel`,值经 sanitize 定界。"""

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
        if self.labels:
            object.__setattr__(self, "labels", sanitize_metric_labels(self.labels))
