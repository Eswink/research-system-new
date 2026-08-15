"""M11 EvalReport 编解码域契约测试：digest 稳定性与 fail-closed 解析。"""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

from packages.domain.enums import QualityGateVerdict
from packages.domain.eval_report_codec import (
    report_digest,
    report_from_dict,
    report_to_dict,
)
from packages.domain.eval_result import (
    EvalFindingStatus,
    EvalReport,
    EvalResult,
    ReviewerFinding,
    ReviewerVerdict,
)
from packages.domain.serialization import canonical_json_bytes
from tests.domain.eval_contracts_support import make_report


def test_frozen_conditions_digest_stable() -> None:
    report = make_report()
    assert report.frozen_conditions.digest() == report.frozen_conditions.digest()


def test_frozen_conditions_comparison_digest_excludes_inputs() -> None:
    report = make_report()
    assert report.frozen_conditions.digest() != report.frozen_conditions.comparison_digest()


def test_report_digest_ignores_volatile_fields() -> None:
    a = make_report(report_id="r1", generated_at="2026-08-15T00:00:00Z")
    b = make_report(report_id="r2", generated_at="2026-08-16T12:00:00Z")
    assert report_digest(a) == report_digest(b)


def test_report_digest_detects_finding_status_change() -> None:
    a = make_report(status=EvalFindingStatus.PASS)
    b = make_report(status=EvalFindingStatus.FAIL)
    assert report_digest(a) != report_digest(b)


def test_report_digest_detects_verdict_change() -> None:
    a = make_report(verdict=QualityGateVerdict.PASS)
    b = make_report(verdict=QualityGateVerdict.REVISE)
    assert report_digest(a) != report_digest(b)


def test_report_json_roundtrip() -> None:
    original = make_report()
    payload = json.loads(canonical_json_bytes(report_to_dict(original)).decode("utf-8"))
    restored = report_from_dict(payload)
    assert restored == original
    assert restored.digest() == original.digest()


def test_report_roundtrip_with_reviewer_findings() -> None:
    report = make_report()
    case = report.results[0]
    with_reviewer = EvalReport(
        report_id=report.report_id,
        generated_at=report.generated_at,
        mode=report.mode,
        scope=report.scope,
        gate_verdict=report.gate_verdict,
        frozen_conditions=report.frozen_conditions,
        results=(
            EvalResult(
                case_id=case.case_id,
                case_version=case.case_version,
                case_digest=case.case_digest,
                scope=case.scope,
                input_ref=case.input_ref,
                scorer_findings=case.scorer_findings,
                reviewer_findings=(
                    ReviewerFinding(
                        reviewer_id="scientific_reviewer",
                        model_identity="mock-model-v1",
                        rubric_id="soundness",
                        verdict=ReviewerVerdict.PASS,
                        rationale="ok",
                        score=Decimal("0.8"),
                        temperature="0",
                        repetitions=3,
                    ),
                ),
            ),
        ),
    )
    payload = json.loads(canonical_json_bytes(report_to_dict(with_reviewer)).decode("utf-8"))
    restored = report_from_dict(payload)
    assert restored == with_reviewer
    assert restored.digest() == with_reviewer.digest()


def test_report_in_memory_roundtrip_with_reviewer_score() -> None:
    # 不经过 JSON 文本的 dict 往返：score Decimal 必须编码为字符串
    # （eval_report_codec 契约），否则 report_from_dict 拒绝自身输出。
    report = make_report()
    case = report.results[0]
    with_reviewer = EvalReport(
        report_id=report.report_id,
        generated_at=report.generated_at,
        mode=report.mode,
        scope=report.scope,
        gate_verdict=report.gate_verdict,
        frozen_conditions=report.frozen_conditions,
        results=(
            EvalResult(
                case_id=case.case_id,
                case_version=case.case_version,
                case_digest=case.case_digest,
                scope=case.scope,
                input_ref=case.input_ref,
                scorer_findings=case.scorer_findings,
                reviewer_findings=(
                    ReviewerFinding(
                        reviewer_id="scientific_reviewer",
                        model_identity="mock-model-v1",
                        rubric_id="soundness",
                        verdict=ReviewerVerdict.PASS,
                        rationale="ok",
                        score=Decimal("0.8"),
                        temperature="0",
                        repetitions=3,
                    ),
                ),
            ),
        ),
    )
    restored = report_from_dict(report_to_dict(with_reviewer))
    assert restored == with_reviewer
    assert restored.digest() == with_reviewer.digest()


def test_report_from_dict_rejects_missing_field() -> None:
    payload = json.loads(canonical_json_bytes(report_to_dict(make_report())).decode("utf-8"))
    del payload["gate_verdict"]
    with pytest.raises(ValueError, match="gate_verdict"):
        report_from_dict(payload)


def test_report_from_dict_rejects_malformed_reviewer() -> None:
    payload = json.loads(canonical_json_bytes(report_to_dict(make_report())).decode("utf-8"))
    payload["results"][0]["reviewer_findings"] = [
        {
            "reviewer_id": "r",
            "model_identity": "m",
            "rubric_id": "x",
            "verdict": "PASS",
            "rationale": "",
            "score": 8,
            "failure": None,
            "temperature": None,
            "repetitions": 1,
        }
    ]
    with pytest.raises(ValueError, match="score"):
        report_from_dict(payload)
