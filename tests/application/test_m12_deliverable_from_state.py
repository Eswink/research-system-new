"""Deliverable from persisted state（M12-R1 WP3）。

验证：
- 报告事实全部来自持久状态（artifact digest 重算 / claim / memory / budget /
  eval / audit），无代码内常量；
- 空/缺失状态 → DeliverableBuildError（不静默降级）；
- 篡改 artifact 内容 → digest 不一致，报告反映真实状态；
- 基于同一 run_id 两次重建报告一致（确定性 render）；
- budget 段只读 ledger entries，不虚构 reservation 一致性。

fixtures：tests/application/m12_deliverable_fixtures.py（标识与生产链一致）。
"""

from __future__ import annotations

from typing import cast

import pytest

from packages.application.deliverable.builder import (
    DeliverableBuildError,
    DeliverableInputs,
    build_deliverable,
)
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from tests.application.m12_deliverable_fixtures import (
    ARTIFACT_ID,
    EVIDENCE_ID,
    MEMORY_ID,
    artifact_content,
    populate,
)

_Report = dict[str, object]


def _report(inputs: DeliverableInputs) -> _Report:
    return build_deliverable(inputs)


def _experiment(report: _Report) -> _Report:
    return cast(_Report, report["experiment"])


def _evidence_chain(report: _Report) -> _Report:
    return cast(_Report, report["evidence_chain"])


def _budget(report: _Report) -> _Report:
    return cast(_Report, report["budget"])


def _memory(report: _Report) -> _Report:
    return cast(_Report, report["memory"])


class TestDeliverableFromState:
    def test_full_report_from_persisted_state(self) -> None:
        inputs, _, _, _ = populate()
        report = _report(inputs)
        assert _experiment(report)["artifact_digest"] == str(Digest.of_bytes(artifact_content()))
        metrics = cast(_Report, _experiment(report)["metrics"])
        assert metrics["baseline_accuracy"] == "0.745"
        assert _evidence_chain(report)["claim_status"] == "VERIFIED"
        assert _evidence_chain(report)["evidence_ids"] == (EVIDENCE_ID,)
        sources = cast(_Report, _evidence_chain(report)["evidence_sources"])
        assert str(sources[EVIDENCE_ID]).startswith(ARTIFACT_ID[:16])
        assert _memory(report)["memory_id"] == MEMORY_ID
        assert _budget(report)["total_model_tokens"] == 2000
        assert _budget(report)["tool_requests"] == 2
        assert cast(_Report, report["evaluation"])["dataset"] == "m12_research_v1"
        assert cast(_Report, report["reproduction"])["semantic_metrics_digest"] is not None
        assert cast(_Report, report["protocol"])["manifest_digest"] == str(inputs.manifest.digest())

    def test_missing_artifact_fails(self) -> None:
        inputs, _, _, _ = populate(with_artifact=False)
        with pytest.raises(DeliverableBuildError):
            build_deliverable(inputs)

    def test_missing_claim_fails(self) -> None:
        inputs, _, _, _ = populate(with_claim=False)
        with pytest.raises(DeliverableBuildError):
            build_deliverable(inputs)

    def test_missing_memory_fails(self) -> None:
        inputs, _, _, _ = populate(with_memory=False)
        with pytest.raises(DeliverableBuildError):
            build_deliverable(inputs)

    def test_missing_eval_report_fails(self) -> None:
        inputs, _, _, _ = populate(with_eval=False)
        with pytest.raises(DeliverableBuildError):
            build_deliverable(inputs)

    def test_missing_audit_fails(self) -> None:
        inputs, _, _, _ = populate(with_audit=False)
        with pytest.raises(DeliverableBuildError):
            build_deliverable(inputs)

    def test_deterministic_rebuild_from_same_state(self) -> None:
        first = _report(populate()[0])
        second = _report(populate()[0])
        assert first == second

    def test_tampered_artifact_changes_digest(self) -> None:
        inputs, artifacts, _, _ = populate()
        tampered = b'{"status": "SUCCEEDED", "metrics": {"baseline_accuracy": "0.999"}}'
        artifacts.put(
            Artifact(
                id=ARTIFACT_ID,
                digest=Digest.of_bytes(tampered),
                size_bytes=len(tampered),
                media_type="application/json",
            ),
            tampered,
        )
        report = _report(inputs)
        assert _experiment(report)["artifact_digest"] == str(Digest.of_bytes(tampered))
        metrics = cast(_Report, _experiment(report)["metrics"])
        assert metrics["baseline_accuracy"] == "0.999"

    def test_budget_from_ledger_not_constants(self) -> None:
        inputs, _, _, budget = populate()
        report = _report(inputs)
        snapshot = budget.snapshot()
        assert _budget(report)["entries"] == len(snapshot.entries)
        assert _budget(report)["reservations"] == 0
