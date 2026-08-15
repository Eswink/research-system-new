"""M11 EvalScore 报告往返与 schema 校验测试。"""

from __future__ import annotations

import pathlib

import pytest

from adapters.contracts.base import ContractLoadError
from adapters.contracts.eval_report_io import read_report, write_report
from packages.application.evaluation.runner import (
    RunRequest,
    run_evaluation,
)
from packages.domain.core import Version
from packages.domain.eval_gate import GateConfig
from packages.domain.eval_result import EvalReport
from packages.domain.eval_spec import EvalCase, EvalDataset, EvalScope, ScorerRef

_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _dataset() -> EvalDataset:
    return EvalDataset(
        id="report-ds",
        version=Version("1.0.0"),
        cases=(
            EvalCase(
                id="c1",
                version=Version("1.0.0"),
                scope=EvalScope.UNIT,
                input_ref="input://c1",
                expected={"answer": 42},
                scorer_refs=(ScorerRef("exact_match", Version("1.0.0")),),
            ),
        ),
    )


def _report() -> EvalReport:
    outcome = run_evaluation(
        RunRequest(
            dataset=_dataset(),
            config=GateConfig(id="gate", version=Version("1.0.0")),
            mode="OFFLINE_FAKE",
            system_version="0.4.0",
            inputs={"input://c1": {"answer": 42}},
        )
    )
    return outcome.report


def test_report_roundtrip_preserves_digest(tmp_path: pathlib.Path) -> None:
    report = _report()
    path = tmp_path / "eval-report.json"
    write_report(path, report)
    restored = read_report(path)
    assert restored == report
    assert restored.digest() == report.digest()


def test_report_file_is_stable_across_writes(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "eval-report.json"
    write_report(path, _report())
    first = path.read_bytes()
    write_report(path, _report())
    second = path.read_bytes()
    assert first == second


def test_read_rejects_malformed_json(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ContractLoadError, match="not valid JSON"):
        read_report(path)


def test_read_rejects_schema_violation(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "bad-schema.json"
    write_report(path, _report())
    text = path.read_text(encoding="utf-8")
    tampered = text.replace('"gate_verdict":"PASS"', '"gate_verdict":"MAYBE"', 1)
    assert tampered != text
    path.write_text(tampered, encoding="utf-8")
    with pytest.raises(ContractLoadError):
        read_report(path)


def test_read_rejects_missing_file(tmp_path: pathlib.Path) -> None:
    with pytest.raises(ContractLoadError, match="not readable"):
        read_report(tmp_path / "missing.json")


def test_report_schema_covers_required_fields(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "eval-report.json"
    write_report(path, _report())
    text = path.read_text(encoding="utf-8")
    assert '"format":"eval_report.v1"' in text
    assert '"frozen_conditions"' in text
    assert '"scorer_findings"' in text
