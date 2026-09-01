"""实验输出解析（纯函数，M9）。

把容器工作区中的 experiment_result.json 解析为类型化数据，
对齐 schemas/experiment_run_output_v1.schema.json：
{experiment_run_id, status(SUCCEEDED|FAILED|NEGATIVE_RESULT),
 artifact_refs[], metrics{name→number|string|boolean|null}, failure_ref?}

- JSON number 以 Decimal 解析（digest 确定性，拒绝 float）；
- schema 违规抛 InvalidInputError（调用方 bug / 实验输出契约违约），
  由 executor 分类为实验级 FAILED；
- 不依赖 jsonschema 运行时（手工校验字段，少一个运行时依赖）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Digest
from packages.domain.experiments import MetricValue, metric_values_from_mapping
from packages.domain.serialization import digest_of

_DECLARED_STATUSES = frozenset({"SUCCEEDED", "FAILED", "NEGATIVE_RESULT"})
# M17 WP3c 第 4 层（证据层）：compute_device.kind 的闭集
_COMPUTE_DEVICE_KINDS = frozenset({"cuda", "cpu"})
_MAX_COMPUTE_DEVICE_NAME = 128
_MAX_CUDA_VERSION_LENGTH = 32

# 非确定性观测字段后缀（M12-R1 WP4）：wall-clock / duration 测量不进入
# semantic reproducibility digest（允许重跑 variance），但仍保留在 raw
# artifact 中供审计。
_OBSERVATIONAL_SUFFIXES = ("_time_s", "_duration_s", "_wall_clock")

_OutputScalar = Decimal | str | bool | None


@dataclass(frozen=True, slots=True)
class ExperimentResultPayload:
    """experiment_result.json 的类型化解析结果。"""

    experiment_run_id: str
    declared_status: str
    artifact_refs: tuple[str, ...]
    metric_values: tuple[MetricValue, ...]
    metrics_digest: Digest
    semantic_metrics_digest: Digest
    failure_ref: str | None = None
    # M17：实验自报的执行设备（可选；GPU profile 下缺失/非 cuda 即违约）
    compute_device_kind: str | None = None
    compute_device_name: str | None = None


def _parse_compute_device(data: dict[str, Any]) -> tuple[str | None, str | None]:
    """解析可选 compute_device 对象；越界/类型错 fail-closed 抛违约。"""
    device = data.get("compute_device")
    if device is None:
        return None, None
    if not isinstance(device, dict):
        raise InvalidInputError("compute_device must be an object")
    kind = device.get("kind")
    if kind not in _COMPUTE_DEVICE_KINDS:
        raise InvalidInputError(
            f"compute_device.kind must be one of {sorted(_COMPUTE_DEVICE_KINDS)}"
        )
    name = device.get("name")
    if name is not None and (not isinstance(name, str) or len(name) > _MAX_COMPUTE_DEVICE_NAME):
        raise InvalidInputError("compute_device.name must be a string <= 128 chars")
    version = device.get("cuda_runtime_version")
    if version is not None and (
        not isinstance(version, str) or len(version) > _MAX_CUDA_VERSION_LENGTH
    ):
        raise InvalidInputError("compute_device.cuda_runtime_version must be a short string")
    return str(kind), str(name) if isinstance(name, str) else None


def semantic_metrics_projection(metrics: dict[str, Any]) -> dict[str, Any]:
    """科学语义投影：剔除 wall-clock 等非确定性观测字段。

    规则：键名以 _OBSERVATIONAL_SUFFIXES 结尾的字段属于运行时观测，
    不进入 semantic reproducibility digest；其余科学指标全部保留。
    """
    return {
        name: value for name, value in metrics.items() if not name.endswith(_OBSERVATIONAL_SUFFIXES)
    }


def semantic_metrics_digest(metrics: dict[str, Any]) -> Digest:
    """scientific 子集的 canonical digest（跨重跑稳定）。"""
    return digest_of(semantic_metrics_projection(metrics))


def parse_experiment_result_json(
    raw: str | bytes,
    *,
    expected_run_id: str,
) -> ExperimentResultPayload:
    """解析并校验实验输出；JSON 非法/字段缺失/类型错抛 InvalidInputError。"""
    text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    try:
        data: Any = json.loads(text, parse_float=Decimal)
    except (json.JSONDecodeError, ValueError) as exc:
        raise InvalidInputError(f"experiment_result.json is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise InvalidInputError("experiment_result.json must be a JSON object")
    run_id = data.get("experiment_run_id")
    if not isinstance(run_id, str) or not run_id:
        raise InvalidInputError("experiment_result.json missing experiment_run_id")
    if run_id != expected_run_id:
        raise InvalidInputError(
            f"experiment_run_id mismatch: declared {run_id!r}, expected {expected_run_id!r}"
        )
    status = data.get("status")
    if status not in _DECLARED_STATUSES:
        raise InvalidInputError(f"invalid declared status: {status!r}")
    refs = data.get("artifact_refs")
    if not isinstance(refs, list) or not all(isinstance(item, str) for item in refs):
        raise InvalidInputError("artifact_refs must be a list of strings")
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        raise InvalidInputError("metrics must be an object")
    metric_values = _metric_values(metrics)
    failure_ref = data.get("failure_ref")
    if failure_ref is not None and not isinstance(failure_ref, str):
        raise InvalidInputError("failure_ref must be a string or null")
    device_kind, device_name = _parse_compute_device(data)
    return ExperimentResultPayload(
        experiment_run_id=run_id,
        declared_status=str(status),
        artifact_refs=tuple(refs),
        metric_values=metric_values,
        metrics_digest=_metrics_digest(metrics),
        semantic_metrics_digest=semantic_metrics_digest(metrics),
        failure_ref=failure_ref,
        compute_device_kind=device_kind,
        compute_device_name=device_name,
    )


def _metric_values(metrics: dict[str, Any]) -> tuple[MetricValue, ...]:
    for name, value in metrics.items():
        if not isinstance(value, (str, bool, int, Decimal)) and value is not None:
            raise InvalidInputError(
                f"metric {name!r} has unsupported value type {type(value).__name__}"
            )
    try:
        return metric_values_from_mapping(metrics)
    except ValueError as exc:
        raise InvalidInputError(str(exc)) from exc


def _metrics_digest(metrics: dict[str, Any]) -> Digest:
    """metrics 原始映射的 canonical digest（Decimal 支持）。"""
    return digest_of(metrics)
