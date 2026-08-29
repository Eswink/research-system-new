"""EvalReport → 存储索引派生与 verbatim 正文编码(M15 WP3)。

正文编码:codec `report_to_dict` 的 JSON(sort_keys 确定性)——`report_digest`
可由正文重建并校验(rebuild-from-bodies)。所有 index 列均为正文派生,不产生
任何判断;INFRA_ERROR 保留为独立计数(不折算、不丢弃)。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from packages.application.ports.eval_report_store import EvalReportIndexEntry, StoredEvalReport
from packages.domain.eval_report_codec import report_to_dict
from packages.domain.eval_result import EvalFindingStatus, EvalReport


def encode_report_body(report: EvalReport) -> bytes:
    """报告 → verbatim canonical bytes(JSON,sort_keys)。"""
    return json.dumps(
        report_to_dict(report),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def decode_report_body(body: bytes) -> EvalReport:
    """verbatim bytes → 报告(重建路径;格式错误 fail-closed)。"""
    from packages.domain.eval_report_codec import report_from_dict

    return report_from_dict(json.loads(body.decode("utf-8")))


def build_index_entry(
    report: EvalReport,
    *,
    run_id: str | None = None,
    usage_ref: str | None = None,
    cost_ref: str | None = None,
    recorded_at: datetime | None = None,
) -> EvalReportIndexEntry:
    """报告正文 → 派生索引(全部字段由正文计算,无外部输入)。"""
    frozen = report.frozen_conditions
    pass_count = 0
    fail_count = 0
    infra_error_count = 0
    identities: set[str] = set()
    for result in report.results:
        for finding in result.scorer_findings:
            if finding.status is EvalFindingStatus.PASS:
                pass_count += 1
            elif finding.status is EvalFindingStatus.INFRA_ERROR:
                infra_error_count += 1
            else:
                fail_count += 1
        for reviewer in result.reviewer_findings:
            if reviewer.model_identity:
                identities.add(reviewer.model_identity)
    return EvalReportIndexEntry(
        report_digest=str(report.digest()),
        comparison_digest=str(frozen.comparison_digest()),
        dataset_id=frozen.dataset_id,
        dataset_version=frozen.dataset_version.text,
        dataset_digest=str(frozen.dataset_digest),
        gate_config_id=frozen.gate_config_id,
        gate_config_version=frozen.gate_config_version.text,
        gate_config_digest=str(frozen.gate_config_digest),
        scorer_versions=tuple(sorted(frozen.scorer_versions.items())),
        system_version=frozen.system_version,
        case_ids=tuple(result.case_id for result in report.results),
        evaluator_identities=tuple(sorted(identities)),
        verdict=report.gate_verdict.value,
        pass_count=pass_count,
        fail_count=fail_count,
        infra_error_count=infra_error_count,
        usage_ref=usage_ref,
        cost_ref=cost_ref,
        run_id=run_id,
        recorded_at=recorded_at or datetime.now(timezone.utc),
    )


def stored_from_report(
    report: EvalReport,
    *,
    run_id: str | None = None,
    usage_ref: str | None = None,
    cost_ref: str | None = None,
    recorded_at: datetime | None = None,
) -> StoredEvalReport:
    """报告 → StoredEvalReport(index + verbatim body)。"""
    from packages.application.ports.eval_report_store import StoredEvalReport

    index = build_index_entry(
        report,
        run_id=run_id,
        usage_ref=usage_ref,
        cost_ref=cost_ref,
        recorded_at=recorded_at,
    )
    return StoredEvalReport(index=index, body=encode_report_body(report))
