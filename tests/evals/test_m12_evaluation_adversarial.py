"""M12 Evaluation adversarial regression（M12-R1 WP5）。

8+ 类伪造输入必须被相应 scorer / gate 拦截（FAIL 或 INFRA_ERROR，
整体 verdict 不得 PASS）。禁止通过修改 expected 跟随 candidate 通过测试：
- expected 已从 dataset 删除 0.745 字面量（独立 ground truth 来自 ArtifactStore）；
- artifact 篡改由 evidence_artifact scorer 从 Evidence 登记 digest 独立拦截。

fixtures/标识与生产链一致（tests/evals/m12_eval_fixtures.py）。
"""

from __future__ import annotations

from packages.application.evaluation.scorer_types import ScorerContext, ScorerInput
from packages.application.evaluation.scorers_evidence import evidence_provenance_scorer
from packages.domain.enums import QualityGateVerdict
from packages.domain.eval_result import EvalFindingStatus
from packages.domain.eval_spec import EvalCase, EvalScope
from packages.domain.evidence import (
    ClaimStatus,
    EvidenceRelationType,
)
from tests.evals.m12_eval_fixtures import (
    CLAIM_ID,
    artifact_content,
    base_inputs,
    make_artifacts,
    make_ledger,
    run,
)


class TestM12Adversarial:
    def test_direction_reversed_fails(self) -> None:
        """1. 方向反转：candidate 声称更好但实际更差 → FAIL。"""
        report = run({
            **base_inputs(),
            "input://m12/experimental_validity": {
                "status": "SUCCEEDED",
                "metrics": {"baseline_accuracy": "0.20", "candidate_accuracy": "0.75"},
                "seed": 7,
            },
        })
        result = next(
            item for item in report.results if item.case_id == "direction_improvement_001"
        )
        assert result.scorer_findings[0].status is EvalFindingStatus.FAIL

    def test_metric_exaggerated_to_0999_fails(self) -> None:
        """2. metric 夸大：报告 0.999，artifact 重算 0.745 → FAIL。"""
        report = run({**base_inputs(), "input://m12/result_correctness": "0.999"})
        result = next(item for item in report.results if item.case_id == "result_correctness_001")
        assert result.scorer_findings[0].status is EvalFindingStatus.FAIL

    def test_wrong_artifact_digest_fails(self) -> None:
        """3. artifact 内容被替换（digest 漂移）→ evidence_artifact FAIL（Evidence
        登记 digest 与当前存储不一致），整体 verdict 不得 PASS。"""
        tampered = artifact_content(baseline="0.500")
        report = run(
            base_inputs(),
            artifacts=make_artifacts(tampered),
        )
        assert report.gate_verdict is not QualityGateVerdict.PASS
        result = next(item for item in report.results if item.case_id == "evidence_artifact_001")
        assert result.scorer_findings[0].status is EvalFindingStatus.FAIL

    def test_missing_evidence_fails(self) -> None:
        """4. 缺 Evidence：claim 无 relations → unsupported_claim FAIL。"""
        report = run(base_inputs(), ledger=make_ledger(with_claim=False))
        result = next(item for item in report.results if item.case_id == "claim_calibration_001")
        assert any(
            finding.status in (EvalFindingStatus.FAIL, EvalFindingStatus.INFRA_ERROR)
            for finding in result.scorer_findings
        )

    def test_unsupported_claim_fails(self) -> None:
        """5. unsupported claim：仅 REFUTES 无 SUPPORTS → FAIL。"""
        report = run(base_inputs(), ledger=make_ledger(relation=EvidenceRelationType.REFUTES))
        result = next(item for item in report.results if item.case_id == "claim_calibration_001")
        assert any(finding.status is EvalFindingStatus.FAIL for finding in result.scorer_findings)

    def test_contradictory_evidence_fails(self) -> None:
        """6. 矛盾证据：claim DISPUTED → evidence_provenance FAIL。"""
        ledger = make_ledger(claim_status=ClaimStatus.DISPUTED)
        scorer = evidence_provenance_scorer(ledger)
        finding = scorer(
            ScorerContext(
                case=_case({"claim_id": CLAIM_ID, "minimum_sources": 1}),
                input=ScorerInput(actual={}),
            )
        )
        assert finding.status is EvalFindingStatus.FAIL
        assert "disputed" in finding.detail

    def test_fake_reproduction_fails(self) -> None:
        """7. fake reproduction：audit 缺 metrics_digest 锚点 → required_fields FAIL。"""
        inputs = base_inputs()
        inputs["input://m12/reproducibility"] = {
            "audit_status": "PASS",
            "image_digest": "sha256:" + "ab" * 32,
            "workspace_snapshot_before": "sha256:" + "cd" * 32,
            "workspace_snapshot_after": "sha256:" + "ef" * 32,
        }
        report = run(inputs)
        result = next(item for item in report.results if item.case_id == "reproducibility_001")
        assert result.scorer_findings[0].status is EvalFindingStatus.FAIL

    def test_wrong_source_id_fails(self) -> None:
        """8. wrong source id：evidence 属于其他 run → citation_source FAIL。"""
        report = run(
            base_inputs(),
            ledger=make_ledger(evidence_run_id="99999999-2222-4333-8444-555555555555"),
        )
        result = next(item for item in report.results if item.case_id == "claim_calibration_001")
        assert any(finding.status is EvalFindingStatus.FAIL for finding in result.scorer_findings)

    def test_citation_hallucination_fails(self) -> None:
        """9. 引文内容与冻结 claim statement 不一致 → digest_match FAIL。"""
        report = run({**base_inputs(), "input://m12/citation_correctness": "a fabricated citation"})
        result = next(item for item in report.results if item.case_id == "citation_correctness_001")
        assert result.scorer_findings[0].status is EvalFindingStatus.FAIL


def _case(expected: object) -> EvalCase:
    from packages.domain.core import Version

    return EvalCase(
        id="c1",
        version=Version("1.0.0"),
        scope=EvalScope.WORKFLOW,
        input_ref="input://c1",
        expected=expected,
        scorer_refs=(),
    )
