"""ExperimentPlan/ExperimentRun/ReproducibilityAudit row mapping（store 共享 codec）.

纯 domain ↔ dict 映射，无数据库依赖；由 `adapters/postgres/experiment_store.py`
与 `adapters/sqlite/experiment_store.py` 共享（whole-object JSON 行）。
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from packages.domain.core import ID, Digest, Timestamp
from packages.domain.experiments import (
    ExperimentPlan,
    ExperimentRun,
    ExperimentRunResult,
    ExperimentRunSpec,
    Metric,
    MetricKind,
    MetricValue,
    metric_value_from_raw,
)
from packages.domain.reproducibility import ReproducibilityAudit


def _opt_digest(value: Any) -> Digest | None:
    return Digest.parse(value) if value else None


def _opt_ts(value: Any) -> Timestamp | None:
    return Timestamp(datetime.fromisoformat(value)) if value else None


# --- ExperimentPlan ---


def encode_plan(plan: ExperimentPlan) -> dict[str, Any]:
    return {
        "id": plan.id.value,
        "name": plan.name,
        "hypothesis": plan.hypothesis,
        "task_contract_ref": plan.task_contract_ref,
        "input_spec_digest": (str(plan.input_spec_digest) if plan.input_spec_digest else None),
        "state": plan.state,
        "created_at": plan.created_at.value.isoformat(),
        "updated_at": plan.updated_at.value.isoformat(),
    }


def decode_plan(record: dict[str, Any]) -> ExperimentPlan:
    return ExperimentPlan(
        id=ID(record["id"]),
        name=record["name"],
        hypothesis=record.get("hypothesis"),
        task_contract_ref=record.get("task_contract_ref"),
        input_spec_digest=_opt_digest(record.get("input_spec_digest")),
        state=record["state"],
        created_at=Timestamp(datetime.fromisoformat(record["created_at"])),
        updated_at=Timestamp(datetime.fromisoformat(record["updated_at"])),
    )


# --- ExperimentRunSpec ---


def encode_spec(spec: ExperimentRunSpec) -> dict[str, Any]:
    return {
        "input_digest": str(spec.input_digest),
        "command": spec.command,
        "code_digest": str(spec.code_digest) if spec.code_digest else None,
        "environment_digest": str(spec.environment_digest) if spec.environment_digest else None,
        "seed": spec.seed,
        "resource_profile": spec.resource_profile,
    }


def decode_spec(record: dict[str, Any]) -> ExperimentRunSpec:
    return ExperimentRunSpec(
        input_digest=Digest.parse(record["input_digest"]),
        command=record.get("command"),
        code_digest=_opt_digest(record.get("code_digest")),
        environment_digest=_opt_digest(record.get("environment_digest")),
        seed=record.get("seed"),
        resource_profile=record.get("resource_profile"),
    )


# --- MetricValue ---


def encode_metric_value(mv: MetricValue) -> dict[str, Any]:
    # NUMBER 的 Decimal 以字符串存（JSON 无 Decimal；str 往返确定）。
    value: Any = str(mv.value) if mv.metric.kind is MetricKind.NUMBER else mv.value
    return {
        "name": mv.metric.name,
        "unit": mv.metric.unit,
        "kind": mv.metric.kind.value,
        "value": value,
        "source_ref": mv.source_ref,
    }


def decode_metric_value(record: dict[str, Any]) -> MetricValue:
    kind = MetricKind(record["kind"])
    if kind is MetricKind.NUMBER:
        return MetricValue(
            metric=Metric(name=record["name"], unit=record.get("unit"), kind=kind),
            value=Decimal(str(record["value"])),
            source_ref=record.get("source_ref"),
        )
    # STRING/BOOLEAN/NULL 走类型推断构造（int 不可能出现：kind 已定）。
    return metric_value_from_raw(
        record["name"],
        record["value"],
        unit=record.get("unit"),
        source_ref=record.get("source_ref"),
    )


# --- ExperimentRun ---


def encode_result(result: ExperimentRunResult) -> dict[str, Any]:
    return {
        "execution_run_id": result.execution_run_id,
        "image_digest": result.image_digest,
        "workspace_snapshot_before": result.workspace_snapshot_before,
        "workspace_snapshot_after": result.workspace_snapshot_after,
        "elapsed_seconds": result.elapsed_seconds,
        "stdout_digest": str(result.stdout_digest) if result.stdout_digest else None,
        "stderr_digest": str(result.stderr_digest) if result.stderr_digest else None,
        "metrics": [encode_metric_value(mv) for mv in result.metrics],
        "metrics_digest": str(result.metrics_digest) if result.metrics_digest else None,
        "semantic_metrics_digest": (
            str(result.semantic_metrics_digest) if result.semantic_metrics_digest else None
        ),
        "artifact_refs": list(result.artifact_refs),
        "failure_reason": result.failure_reason,
    }


def decode_result(record: dict[str, Any]) -> ExperimentRunResult:
    return ExperimentRunResult(
        execution_run_id=record["execution_run_id"],
        image_digest=record.get("image_digest"),
        workspace_snapshot_before=record.get("workspace_snapshot_before"),
        workspace_snapshot_after=record.get("workspace_snapshot_after"),
        elapsed_seconds=record.get("elapsed_seconds"),
        stdout_digest=_opt_digest(record.get("stdout_digest")),
        stderr_digest=_opt_digest(record.get("stderr_digest")),
        metrics=tuple(decode_metric_value(item) for item in record.get("metrics", ())),
        metrics_digest=_opt_digest(record.get("metrics_digest")),
        semantic_metrics_digest=_opt_digest(record.get("semantic_metrics_digest")),
        artifact_refs=tuple(record.get("artifact_refs", ())),
        failure_reason=record.get("failure_reason"),
    )


def encode_run(run: ExperimentRun) -> dict[str, Any]:
    return {
        "id": run.id.value,
        "plan_id": run.plan_id.value,
        "spec": encode_spec(run.spec) if run.spec else None,
        "result": encode_result(run.result) if run.result else None,
        "state": run.state,
        "created_at": run.created_at.value.isoformat(),
        "started_at": run.started_at.value.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.value.isoformat() if run.completed_at else None,
    }


def decode_run(record: dict[str, Any]) -> ExperimentRun:
    return ExperimentRun(
        id=ID(record["id"]),
        plan_id=ID(record["plan_id"]),
        spec=decode_spec(record["spec"]) if record.get("spec") else None,
        result=decode_result(record["result"]) if record.get("result") else None,
        state=record["state"],
        created_at=Timestamp(datetime.fromisoformat(record["created_at"])),
        started_at=_opt_ts(record.get("started_at")),
        completed_at=_opt_ts(record.get("completed_at")),
    )


# --- ReproducibilityAudit ---


def encode_audit(audit: ReproducibilityAudit) -> dict[str, Any]:
    return {
        "audit_id": audit.audit_id.value,
        "experiment_run_id": audit.experiment_run_id.value,
        "input_digest": str(audit.input_digest),
        "command": audit.command,
        "code_digest": str(audit.code_digest) if audit.code_digest else None,
        "environment_digest": str(audit.environment_digest) if audit.environment_digest else None,
        "seed": audit.seed,
        "resource_profile": audit.resource_profile,
        "image_digest": audit.image_digest,
        "workspace_snapshot_before": audit.workspace_snapshot_before,
        "workspace_snapshot_after": audit.workspace_snapshot_after,
        "output_artifact_digests": list(audit.output_artifact_digests),
        "metrics_digest": str(audit.metrics_digest) if audit.metrics_digest else None,
        "semantic_metrics_digest": (
            str(audit.semantic_metrics_digest) if audit.semantic_metrics_digest else None
        ),
        "observational_metrics_digest": (
            str(audit.observational_metrics_digest) if audit.observational_metrics_digest else None
        ),
        "audit_digest": str(audit.audit_digest) if audit.audit_digest else None,
        "created_at": audit.created_at.value.isoformat(),
    }


def decode_audit(record: dict[str, Any]) -> ReproducibilityAudit:
    return ReproducibilityAudit(
        audit_id=ID(record["audit_id"]),
        experiment_run_id=ID(record["experiment_run_id"]),
        input_digest=Digest.parse(record["input_digest"]),
        command=record.get("command"),
        code_digest=_opt_digest(record.get("code_digest")),
        environment_digest=_opt_digest(record.get("environment_digest")),
        seed=record.get("seed"),
        resource_profile=record.get("resource_profile"),
        image_digest=record.get("image_digest"),
        workspace_snapshot_before=record.get("workspace_snapshot_before"),
        workspace_snapshot_after=record.get("workspace_snapshot_after"),
        output_artifact_digests=tuple(record.get("output_artifact_digests", ())),
        metrics_digest=_opt_digest(record.get("metrics_digest")),
        semantic_metrics_digest=_opt_digest(record.get("semantic_metrics_digest")),
        observational_metrics_digest=_opt_digest(record.get("observational_metrics_digest")),
        audit_digest=_opt_digest(record.get("audit_digest")),
        created_at=Timestamp(datetime.fromisoformat(record["created_at"])),
    )
