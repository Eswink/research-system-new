"""operation() 上下文管理器与 span 引用派生。

- `span_ref_of(correlation, scope, name)`:以业务标识的确定性摘要派生 span reference
  (不含原文);trace_id 参与摘要,同一 correlation+scope+name 在不同 trace 得到
  不同 span ref(每次运行独立 span)。
- `parent_span_ref(...)`:按真实因果层级向上取最近存在的父 span(ref)。
  project → run → phase → task → agent_session → {llm, tool, experiment};
  eval_run 挂在 run;queue/outbox/lease 挂 run/project。
  规则:对 scope 的候选父集合按层级从里向外取第一个在 correlation 中有对应
  id 的 scope,以其 `span_ref_of` 作为 parent;找不到则 root(None)。
- `operation(...)`:上下文管理器,始终 emit `OperationEnd`,duration_ms 以 clock
  计算,sink 错误由调用方吞掉(End 不抛出)。
"""

from __future__ import annotations

import hashlib
import time
import uuid
from contextlib import AbstractContextManager
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Literal

from packages.application.observability.attributes import sanitize_attributes
from packages.application.observability.signals import (
    CorrelationRef,
    OperationBegin,
    OperationEnd,
    OperationOutcome,
    OperationScope,
    ParentSpanRef,
    SpanRef,
)

if TYPE_CHECKING:
    # 仅类型依赖;运行时导入会与 ports.telemetry_sink 形成循环
    # (ports → observability → ports)。
    from packages.application.ports.telemetry_sink import TelemetrySink


def _id_field(scope: OperationScope) -> str:
    return _SCOPE_ID_FIELD.get(scope, "run_id")


_SCOPE_ID_FIELD: dict[OperationScope, str] = {
    OperationScope.PROJECT: "project_id",
    OperationScope.RUN: "run_id",
    OperationScope.PHASE: "phase_run_id",
    OperationScope.TASK: "task_id",
    OperationScope.AGENT_SESSION: "agent_session_id",
    OperationScope.LLM_CALL: "tool_call_id",
    OperationScope.TOOL_CALL: "tool_call_id",
    OperationScope.EXPERIMENT_RUN: "experiment_run_id",
    OperationScope.EVAL_RUN: "eval_run_id",
    OperationScope.WORKFLOW_QUEUE: "run_id",
    OperationScope.OUTBOX_RELAY: "run_id",
    OperationScope.LEASE_RECOVERY: "run_id",
}

# 父候选按从里向外排序;调用 _parent_candidates(scope) 后按序取第一个存在者。
_PARENT_CANDIDATES: dict[OperationScope, tuple[OperationScope, ...]] = {
    OperationScope.RUN: (OperationScope.PROJECT,),
    OperationScope.PHASE: (OperationScope.RUN, OperationScope.PROJECT),
    OperationScope.TASK: (OperationScope.PHASE, OperationScope.RUN, OperationScope.PROJECT),
    OperationScope.AGENT_SESSION: (
        OperationScope.TASK,
        OperationScope.PHASE,
        OperationScope.RUN,
    ),
    OperationScope.LLM_CALL: (
        OperationScope.AGENT_SESSION,
        OperationScope.TASK,
        OperationScope.RUN,
    ),
    OperationScope.TOOL_CALL: (
        OperationScope.AGENT_SESSION,
        OperationScope.TASK,
        OperationScope.RUN,
    ),
    OperationScope.EXPERIMENT_RUN: (
        OperationScope.TASK,
        OperationScope.PHASE,
        OperationScope.RUN,
    ),
    OperationScope.EVAL_RUN: (OperationScope.RUN, OperationScope.PROJECT),
    OperationScope.WORKFLOW_QUEUE: (OperationScope.RUN, OperationScope.PROJECT),
    OperationScope.OUTBOX_RELAY: (OperationScope.RUN, OperationScope.PROJECT),
    OperationScope.LEASE_RECOVERY: (OperationScope.RUN, OperationScope.PROJECT),
}

# 引用必须确定性的 scope(子操作经 parent_span_ref 反推其引用)——即全部
# 出现在父候选中的 scope。它们的引用只摘要"该 scope 层级字段集 + trace_id"
# (父引用从子 correlation 投影到父字段集,两侧一致,父子链接才能成立)。
# 其余 scope(叶子)的引用携带 per-invocation nonce,重复/并发调用不碰撞
# (SpanMapper in-flight 表按 span_ref 索引)。
_REF_FIELDS_BY_SCOPE: dict[OperationScope, tuple[str, ...]] = {
    OperationScope.PROJECT: ("project_id",),
    OperationScope.RUN: ("run_id",),
    OperationScope.PHASE: ("run_id", "phase_run_id"),
    OperationScope.TASK: ("run_id", "phase_run_id", "task_id"),
    OperationScope.AGENT_SESSION: ("run_id", "phase_run_id", "task_id", "agent_session_id"),
}

_LEAF_FIELDS = (
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


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def span_ref_of(
    correlation: CorrelationRef,
    scope: OperationScope,
    name: str,
    nonce: str = "",
) -> SpanRef:
    """由 business correlation + scope + name 的确定性摘要派生 span reference。

    不含原文。父候选 scope(PROJECT/RUN/PHASE/TASK/AGENT_SESSION):只摘要
    其层级字段集 + `trace_id`(确定性,子操作可反推父引用;更深的 id 不参与,
    保证"子 correlation 投影 == 父自身引用")。叶子 scope:摘要全 correlation
    并混入 `nonce`,使重复/并发调用互不碰撞。
    """
    parts = [scope.value, name]
    hierarchy_fields = _REF_FIELDS_BY_SCOPE.get(scope)
    if hierarchy_fields is None:
        parts += [getattr(correlation, field) or "" for field in _LEAF_FIELDS]
        parts.append(nonce)
    else:
        parts += [getattr(correlation, field) or "" for field in hierarchy_fields]
        parts.append(correlation.trace_id or "")
    digest = _digest("|".join(parts).encode("utf-8"))
    return SpanRef(value=digest[:32])


def parent_span_ref(
    correlation: CorrelationRef,
    scope: OperationScope,
    name: str,
) -> ParentSpanRef:
    """按真实因果层级取最近存在的父 span;无父则 root(None)。

    对候选父 scope 从里向外:首个在 correlation 中存在 id 的 scope 作为 parent。
    命名约定:父候选 scope(PROJECT/RUN/PHASE/TASK/AGENT_SESSION)的 span 必须
    以 `scope.value` 作为 name 创建,子操作的 parent 引用才能与之匹配;不匹配时
    SpanMapper 按 root 处理(不断链失败)。
    """
    for parent_scope in _PARENT_CANDIDATES.get(scope, ()):
        field = _id_field(parent_scope)
        if getattr(correlation, field, None) is not None:
            ref = span_ref_of(correlation, parent_scope, parent_scope.value)
            return ParentSpanRef(value=ref.value)
    return ParentSpanRef(value=None)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class _Operation(AbstractContextManager["_Operation"]):
    def __init__(
        self,
        sink: TelemetrySink | None,
        *,
        begin: OperationBegin,
        attributes: dict[str, object],
    ) -> None:
        self._sink = sink
        self._begin = begin
        self._start = time.monotonic()
        self._outcome = OperationOutcome.OK
        self._failure_category: str | None = None
        self._attributes: dict[str, str | int | bool] = sanitize_attributes(attributes)

    def set_outcome(
        self,
        outcome: OperationOutcome,
        failure_category: str | None = None,
        *,
        extra: dict[str, object] | None = None,
    ) -> None:
        self._outcome = outcome
        self._failure_category = failure_category
        if extra:
            # 合并而非替换:补充属性(token 数、attempt 等)不抹掉 begin identity
            self._attributes = {**self._attributes, **sanitize_attributes(extra)}

    def __enter__(self) -> "_Operation":
        if self._sink is not None:
            self._sink.begin_operation(self._begin)
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> Literal[False]:
        if exc is not None and self._outcome is OperationOutcome.OK:
            self._outcome = OperationOutcome.FAILED
        end = OperationEnd(
            span_ref=self._begin.span_ref,
            outcome=self._outcome,
            failure_category=self._failure_category,
            attributes=self._attributes,
            duration_ms=int((time.monotonic() - self._start) * 1000),
            ended_at=_now_utc(),
        )
        if self._sink is not None:
            try:
                self._sink.end_operation(end)
            except Exception:
                # fail-open:sink 失败不得影响业务路径(ADR-0026 / OBSERVABILITY.md)
                pass
        return False


def operation(
    sink: TelemetrySink | None,
    *,
    scope: OperationScope,
    name: str,
    correlation: CorrelationRef | None = None,
    attributes: dict[str, object] | None = None,
) -> _Operation:
    """开启一次观测操作;sink 为 None 时全空实现(telemetry off)。

    `sink` 接收 OperationBegin/OperationEnd;实现应为已经过 sanitize 的
    attributes(内部 enforce)。返回上下文管理器,退出时必定 emit OperationEnd。

    span 引用规则:父候选 scope(PROJECT/RUN/PHASE/TASK/AGENT_SESSION)只摘要
    其层级字段集 + trace_id(确定性,子操作可反推父引用;层级链上的 span 必须
    携带一致的 trace_id);其余(叶子)scope 自动附加 per-invocation nonce,
    重复/并发调用互不碰撞。
    """
    effective_correlation = correlation or CorrelationRef()
    nonce = "" if scope in _REF_FIELDS_BY_SCOPE else uuid.uuid4().hex[:12]
    begin = OperationBegin(
        span_ref=span_ref_of(effective_correlation, scope, name, nonce=nonce),
        parent_span_ref=parent_span_ref(effective_correlation, scope, name),
        scope=scope,
        name=name,
        correlation=effective_correlation,
        attributes=sanitize_attributes(attributes or {}),
        started_at=_now_utc(),
    )
    return _Operation(
        sink,
        begin=begin,
        attributes=attributes or {},
    )
