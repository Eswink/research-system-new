"""Experiment 域实体（M9 Real Experiment Runtime）。

把 `ExperimentPlan → ExperimentRun → Metric → Artifact` 落为类型化实体：
- ExperimentPlan：预注册的实验计划（input spec digest 绑定）；
- ExperimentRun：一次实验执行（spec/result 拆分，状态机驱动）；
- Metric / MetricValue：类型化指标（NUMBER 用 Decimal，可进 canonical
  digest；不用裸 dict 冒充）；
- Artifact 只以引用（digest/id）进入本模块，内容持久化归 ArtifactStore，
  不建立第二套实验模型（M9 边界）。

ReproducibilityAudit 见 packages.domain.reproducibility。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Mapping

from packages.domain.core import ID, Digest, Timestamp
from packages.domain.experiment_state import ExperimentPlanState, ExperimentRunState


@dataclass(frozen=True, slots=True)
class ExperimentPlan:
    """预注册的实验计划；input_spec_digest 绑定实验输入快照。"""

    id: ID
    name: str
    hypothesis: str | None = None
    task_contract_ref: str | None = None
    input_spec_digest: Digest | None = None
    state: str = ExperimentPlanState.State.DRAFT
    created_at: Timestamp = field(default_factory=Timestamp.now)
    updated_at: Timestamp = field(default_factory=Timestamp.now)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("plan name must not be empty")

    def transition(self, event: str) -> ExperimentPlan:
        next_state = ExperimentPlanState.transition(self.state, event)
        return ExperimentPlan(
            id=self.id,
            name=self.name,
            hypothesis=self.hypothesis,
            task_contract_ref=self.task_contract_ref,
            input_spec_digest=self.input_spec_digest,
            state=next_state,
            created_at=self.created_at,
            updated_at=Timestamp.now(),
        )

    @property
    def is_terminal(self) -> bool:
        return self.state in ExperimentPlanState.terminal()


@dataclass(frozen=True, slots=True)
class ExperimentRunSpec:
    """实验执行的输入绑定（可复现性锚点：command/input/code/env/seed/资源）。"""

    input_digest: Digest
    command: str | None = None
    code_digest: Digest | None = None
    environment_digest: Digest | None = None
    seed: int | None = None
    resource_profile: str | None = None

    def __post_init__(self) -> None:
        if self.command is not None and not self.command:
            raise ValueError("command must not be empty when provided")
        if self.seed is not None and self.seed < 0:
            raise ValueError("seed must be non-negative")


@dataclass(frozen=True, slots=True)
class ExperimentRunResult:
    """实验执行的产出绑定（执行/镜像/snapshot/指标/artifact 引用）。

    M12-R1 WP4 扩展：metrics_digest 保留 raw digest（含 wall-clock 观测），
    semantic_metrics_digest 只覆盖科学指标投影（同 input+seed+image 重跑稳定）。
    """

    execution_run_id: str
    image_digest: str | None = None
    workspace_snapshot_before: str | None = None
    workspace_snapshot_after: str | None = None
    stdout_digest: Digest | None = None
    stderr_digest: Digest | None = None
    metrics: tuple[MetricValue, ...] = ()
    metrics_digest: Digest | None = None
    semantic_metrics_digest: Digest | None = None
    artifact_refs: tuple[str, ...] = ()
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.execution_run_id:
            raise ValueError("execution_run_id must not be empty")


@dataclass(frozen=True, slots=True)
class ExperimentRun:
    """一次实验执行；状态迁移构造新实例，旧实例保留历史。"""

    id: ID
    plan_id: ID
    spec: ExperimentRunSpec | None = None
    result: ExperimentRunResult | None = None
    state: str = ExperimentRunState.State.PENDING
    created_at: Timestamp = field(default_factory=Timestamp.now)
    started_at: Timestamp | None = None
    completed_at: Timestamp | None = None

    def transition(self, event: str) -> ExperimentRun:
        next_state = ExperimentRunState.transition(self.state, event)
        now = Timestamp.now()
        return ExperimentRun(
            id=self.id,
            plan_id=self.plan_id,
            spec=self.spec,
            result=self.result,
            state=next_state,
            created_at=self.created_at,
            started_at=self.started_at if self.started_at is not None else now,
            completed_at=now if next_state in ExperimentRunState.terminal() else None,
        )

    def with_result(self, result: ExperimentRunResult) -> ExperimentRun:
        return ExperimentRun(
            id=self.id,
            plan_id=self.plan_id,
            spec=self.spec,
            result=result,
            state=self.state,
            created_at=self.created_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
        )

    @property
    def is_terminal(self) -> bool:
        return self.state in ExperimentRunState.terminal()


class MetricKind(StrEnum):
    NUMBER = "NUMBER"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    NULL = "NULL"


@dataclass(frozen=True, slots=True)
class Metric:
    """指标定义（名称/单位/取值类型）。"""

    name: str
    unit: str | None = None
    kind: MetricKind = MetricKind.NUMBER

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("metric name must not be empty")


MetricScalar = Decimal | str | bool | None


@dataclass(frozen=True, slots=True)
class MetricValue:
    """一次实验执行的类型化指标值；NUMBER 用 Decimal 保证 digest 确定性。"""

    metric: Metric
    value: MetricScalar
    source_ref: str | None = None

    def __post_init__(self) -> None:
        expected = {
            MetricKind.NUMBER: (Decimal, int),
            MetricKind.STRING: (str,),
            MetricKind.BOOLEAN: (bool,),
            MetricKind.NULL: (type(None),),
        }
        if not isinstance(self.value, expected[self.metric.kind]):
            raise ValueError(
                f"metric {self.metric.name!r} kind {self.metric.kind.value} "
                f"rejects value of type {type(self.value).__name__}",
            )


def metric_from_raw(name: str, value: object, *, unit: str | None = None) -> Metric:
    """按 JSON 值类型推断 MetricKind（int 归入 NUMBER，内部转 Decimal）。"""
    if isinstance(value, bool):
        return Metric(name=name, unit=unit, kind=MetricKind.BOOLEAN)
    if value is None:
        return Metric(name=name, unit=unit, kind=MetricKind.NULL)
    if isinstance(value, str):
        return Metric(name=name, unit=unit, kind=MetricKind.STRING)
    if isinstance(value, (int, Decimal)) and not isinstance(value, bool):
        return Metric(name=name, unit=unit, kind=MetricKind.NUMBER)
    raise ValueError(f"unsupported metric value type for {name!r}: {type(value).__name__}")


def metric_value_from_raw(
    name: str,
    value: object,
    *,
    unit: str | None = None,
    source_ref: str | None = None,
) -> MetricValue:
    """按 JSON 值构造 MetricValue；NUMBER 归一为 Decimal。"""
    metric = metric_from_raw(name, value, unit=unit)
    normalized: MetricScalar
    if metric.kind is MetricKind.NUMBER:
        normalized = value if isinstance(value, Decimal) else Decimal(str(value))
    elif metric.kind is MetricKind.NULL:
        normalized = None
    else:
        assert isinstance(value, (str, bool))
        normalized = value
    return MetricValue(metric=metric, value=normalized, source_ref=source_ref)


def metric_values_from_mapping(mapping: Mapping[str, object]) -> tuple[MetricValue, ...]:
    """把指标 dict 转为类型化 MetricValue 序列（确定性 key 排序）。"""
    return tuple(metric_value_from_raw(name, mapping[name]) for name in sorted(mapping))
