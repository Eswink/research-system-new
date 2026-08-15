"""M11 EvalReport 编解码（canonical dict 往返，stdlib-only）。

从 eval_result.py 拆出以保持单文件行数阈值。依赖方向：
本模块 import eval_result 的类型（单向）；eval_result.EvalReport.digest
对 report_digest 延迟 import（受控循环，运行时单向安全）。
解析 fail-closed：字段缺失/类型错误一律 ValueError。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Mapping

from packages.domain.core import Digest, Version
from packages.domain.enums import QualityGateVerdict
from packages.domain.eval_result import (
    EVAL_REPORT_FORMAT,
    EvalFindingStatus,
    EvalReport,
    EvalResult,
    FrozenConditions,
    ReviewerFinding,
    ReviewerVerdict,
    ScorerFinding,
)
from packages.domain.eval_spec import EvalScope
from packages.domain.serialization import digest_of


def report_to_dict(report: EvalReport) -> dict[str, object]:
    """报告 canonical 形式；文件写入与 digest 共用同一来源。"""

    return {
        "format": EVAL_REPORT_FORMAT,
        "report_id": report.report_id,
        "generated_at": report.generated_at,
        "mode": report.mode,
        "scope": report.scope.value,
        "gate_verdict": report.gate_verdict.value,
        "frozen_conditions": _frozen_to_dict(report.frozen_conditions),
        "results": [_result_to_dict(item) for item in report.results],
    }


def report_digest(report: EvalReport) -> Digest:
    """report_id 与 generated_at 不参与 digest（volatile 标识）。"""

    payload = {
        key: value
        for key, value in report_to_dict(report).items()
        if key not in ("report_id", "generated_at")
    }
    return digest_of(payload)


def report_from_dict(data: Mapping[str, object]) -> EvalReport:
    """从 JSON 负载重建报告；字段缺失/类型错误一律 fail-closed。"""

    frozen = _require_mapping(data, "frozen_conditions")
    raw_results = _require_list(data, "results")
    results = tuple(_result_from_dict(_as_mapping(item, "results")) for item in raw_results)
    return EvalReport(
        report_id=_require_str(data, "report_id"),
        generated_at=_require_str(data, "generated_at"),
        mode=_require_str(data, "mode"),
        scope=EvalScope(_require_str(data, "scope")),
        gate_verdict=QualityGateVerdict(_require_str(data, "gate_verdict")),
        frozen_conditions=_frozen_from_dict(frozen),
        results=results,
    )


def _frozen_to_dict(frozen: FrozenConditions) -> dict[str, object]:
    return {
        "dataset_id": frozen.dataset_id,
        "dataset_version": frozen.dataset_version.text,
        "dataset_digest": str(frozen.dataset_digest),
        "gate_config_id": frozen.gate_config_id,
        "gate_config_version": frozen.gate_config_version.text,
        "gate_config_digest": str(frozen.gate_config_digest),
        "system_version": frozen.system_version,
        "scorer_versions": dict(frozen.scorer_versions),
        "input_digests": dict(frozen.input_digests),
    }


def _result_to_dict(result: EvalResult) -> dict[str, object]:
    return {
        "case_id": result.case_id,
        "case_version": result.case_version.text,
        "case_digest": str(result.case_digest),
        "scope": result.scope.value,
        "input_ref": result.input_ref,
        "scorer_findings": [
            {
                "scorer_id": item.scorer_id,
                "scorer_version": item.scorer_version.text,
                "case_id": item.case_id,
                "status": item.status.value,
                "detail": item.detail,
                "value": item.value,
            }
            for item in result.scorer_findings
        ],
        "reviewer_findings": [
            {
                "reviewer_id": item.reviewer_id,
                "model_identity": item.model_identity,
                "rubric_id": item.rubric_id,
                "verdict": item.verdict.value,
                "rationale": item.rationale,
                "score": item.score,
                "failure": item.failure,
                "temperature": item.temperature,
                "repetitions": item.repetitions,
            }
            for item in result.reviewer_findings
        ],
        "usage": dict(result.usage),
    }


def _frozen_from_dict(data: Mapping[str, object]) -> FrozenConditions:
    scorer_versions = _require_mapping(data, "scorer_versions")
    input_digests = _require_mapping(data, "input_digests")
    return FrozenConditions(
        dataset_id=_require_str(data, "dataset_id"),
        dataset_version=Version(_require_str(data, "dataset_version")),
        dataset_digest=Digest.parse(_require_str(data, "dataset_digest")),
        gate_config_id=_require_str(data, "gate_config_id"),
        gate_config_version=Version(_require_str(data, "gate_config_version")),
        gate_config_digest=Digest.parse(_require_str(data, "gate_config_digest")),
        system_version=_require_str(data, "system_version"),
        scorer_versions={key: str(value) for key, value in scorer_versions.items()},
        input_digests={key: str(value) for key, value in input_digests.items()},
    )


def _result_from_dict(data: Mapping[str, object]) -> EvalResult:
    scorer_items = _require_list(data, "scorer_findings")
    reviewer_items = _require_list(data, "reviewer_findings")
    return EvalResult(
        case_id=_require_str(data, "case_id"),
        case_version=Version(_require_str(data, "case_version")),
        case_digest=Digest.parse(_require_str(data, "case_digest")),
        scope=EvalScope(_require_str(data, "scope")),
        input_ref=_require_str(data, "input_ref"),
        scorer_findings=tuple(
            _scorer_finding_from_dict(_as_mapping(item, "scorer_findings")) for item in scorer_items
        ),
        reviewer_findings=tuple(
            _reviewer_finding_from_dict(_as_mapping(item, "reviewer_findings"))
            for item in reviewer_items
        ),
        usage=dict(_require_mapping(data, "usage")),
    )


def _scorer_finding_from_dict(data: Mapping[str, object]) -> ScorerFinding:
    return ScorerFinding(
        scorer_id=_require_str(data, "scorer_id"),
        scorer_version=Version(_require_str(data, "scorer_version")),
        case_id=_require_str(data, "case_id"),
        status=EvalFindingStatus(_require_str(data, "status")),
        detail=_require_str(data, "detail"),
        value=data.get("value"),
    )


def _reviewer_finding_from_dict(data: Mapping[str, object]) -> ReviewerFinding:
    score = data.get("score")
    if score is not None and not isinstance(score, str):
        raise ValueError("reviewer score must be a string in eval report")
    failure = data.get("failure")
    if failure is not None and not isinstance(failure, str):
        raise ValueError("reviewer failure must be a string in eval report")
    temperature = data.get("temperature")
    if temperature is not None and not isinstance(temperature, str):
        raise ValueError("reviewer temperature must be a string in eval report")
    repetitions = data.get("repetitions", 1)
    if isinstance(repetitions, bool) or not isinstance(repetitions, int):
        raise ValueError("reviewer repetitions must be an int in eval report")
    return ReviewerFinding(
        reviewer_id=_require_str(data, "reviewer_id"),
        model_identity=_require_str(data, "model_identity"),
        rubric_id=_require_str(data, "rubric_id"),
        verdict=ReviewerVerdict(_require_str(data, "verdict")),
        rationale=_require_str(data, "rationale"),
        score=Decimal(score) if isinstance(score, str) else None,
        failure=failure,
        temperature=temperature,
        repetitions=repetitions,
    )


def _as_mapping(value: object, where: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"each {where!r} entry must be a mapping in eval report")
    return value


def _require_str(data: Mapping[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ValueError(f"eval report field {key!r} must be a string")
    return value


def _require_list(data: Mapping[str, object], key: str) -> list[object]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ValueError(f"eval report field {key!r} must be a list")
    return value


def _require_mapping(data: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"eval report field {key!r} must be a mapping")
    return value
