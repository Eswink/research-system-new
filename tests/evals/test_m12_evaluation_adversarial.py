"""M12 Evaluation adversarial regression（M12-R1 WP5）。

8 类伪造输入必须被相应 scorer / gate 拦截（FAIL 或 INFRA_ERROR，
整体 verdict 不得 PASS）。禁止通过修改 expected 跟随 candidate 通过测试：
- expected 已从 dataset 删除 0.745 字面量（独立 ground truth 来自 ArtifactStore）。
"""

from __future__ import annotations

import json

from adapters.contracts.eval_loaders import load_eval_dataset
from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger
from packages.application.evaluation.runner import RunRequest, run_evaluation
from packages.application.evaluation.scorer_types import ScorerContext, ScorerInput
from packages.application.evaluation.scorers_evidence import evidence_provenance_scorer
from packages.application.evaluation.scorers_m12_truth import (
    citation_source_scorer,
    direction_improvement_scorer,
    metric_correctness_scorer,
    unsupported_claim_scorer,
)
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest, Version
from packages.domain.enums import QualityGateVerdict, TrustLabel
from packages.domain.eval_gate import GateConfig
from packages.domain.eval_result import EvalFindingStatus
from packages.domain.eval_spec import EvalCase, EvalScope
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)

DATASET_PATH = "examples/eval/datasets/m12_research_v1.yaml"
RUN_ID = "12121212-2222-4333-8444-555555555555"
EXPERIMENT_RUN_ID = "5a1c6a8e-9b2d-4f3a-8c5e-2b2c3d4e5f6a"
ARTIFACT_ID = f"{RUN_ID}:experiment_result.json"
CLAIM_ID = f"claim:{RUN_ID}"
EVIDENCE_ID = f"evidence:{RUN_ID}:{EXPERIMENT_RUN_ID}"
SOURCE_ORIGIN = f"experiment:{EXPERIMENT_RUN_ID}:experiment_result.json"

_BASE_INPUTS: dict[str, object] = {
    "input://m12/task_completion": {"status": "SUCCEEDED"},
    "input://m12/evidence_support": {"sources": 2},
    "input://m12/experimental_validity": {
        "status": "SUCCEEDED",
        "metrics": {"baseline_accuracy": "0.745", "candidate_accuracy": "0.28"},
        "seed": 7,
    },
    "input://m12/result_correctness": "0.745",
    "input://m12/reproducibility": {
        "audit_status": "PASS",
        "image_digest": "sha256:ab",
        "workspace_snapshot_before": "sha256:cd",
        "workspace_snapshot_after": "sha256:ef",
        "metrics_digest": "sha256:12",
    },
    "input://m12/claim_calibration": {"claim_status": "VERIFIED"},
    "input://m12/citation_correctness": "00" * 32,
    "input://m12/unsupported_conclusion": {"unsupported_claims": []},
    "input://m12/deliverable_quality": {"claim_id": CLAIM_ID},
    "input://m12/cost_efficiency": {
        "model_tokens": 0,
        "tool_requests": 1,
        "experiment_runs": 2,
        "evaluation_runs": 1,
    },
}


def _artifact_content(baseline: str = "0.745") -> bytes:
    return json.dumps(
        {
            "experiment_run_id": EXPERIMENT_RUN_ID,
            "status": "SUCCEEDED",
            "metrics": {"baseline_accuracy": baseline, "candidate_accuracy": "0.28"},
            "seed": 7,
        },
        sort_keys=True,
    ).encode("utf-8")


def _artifacts(content: bytes | None = None) -> FakeArtifactStore:
    store = FakeArtifactStore()
    content = content or _artifact_content()
    store.put(
        Artifact(
            id=ARTIFACT_ID,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
        ),
        content,
    )
    return store


def _ledger(
    *,
    with_claim: bool = True,
    evidence_run_id: str = RUN_ID,
    relation: EvidenceRelationType = EvidenceRelationType.SUPPORTS,
    claim_status: ClaimStatus = ClaimStatus.PROPOSED,
) -> FakeEvidenceLedger:
    ledger = FakeEvidenceLedger()
    ledger.register_source(
        SourceRecord(
            origin=SOURCE_ORIGIN,
            content_digest=str(Digest.of_bytes(_artifact_content())),
            trust_label=TrustLabel.GENERATED,
        )
    )
    ledger.register_evidence(
        Evidence(
            id=EVIDENCE_ID,
            source_ref=SOURCE_ORIGIN,
            content_digest=str(Digest.of_bytes(_artifact_content())),
            artifact_id=ARTIFACT_ID,
            run_id=evidence_run_id,
            experiment_run_id=EXPERIMENT_RUN_ID,
        )
    )
    if with_claim:
        ledger.register_claim(
            Claim(
                id=CLAIM_ID,
                statement="baseline outperforms candidate",
                status=claim_status,
                evidence_relations=[(EVIDENCE_ID, relation)],
            )
        )
        ledger.attach_relation(
            EvidenceRelation(
                claim_id=CLAIM_ID,
                evidence_id=EVIDENCE_ID,
                relation=relation,
            )
        )
    return ledger


def _run_evaluation(
    inputs: dict[str, object],
    *,
    artifacts: FakeArtifactStore | None = None,
    ledger: FakeEvidenceLedger | None = None,
) -> object:
    artifacts = artifacts or _artifacts()
    ledger = ledger or _ledger()
    dataset = load_eval_dataset(DATASET_PATH)
    outcome = run_evaluation(
        RunRequest(
            dataset=dataset,
            config=GateConfig(
                id="m12-independent-gate",
                version=Version("1.0.0"),
                min_pass_ratio=__import__("decimal").Decimal("0.8"),
            ),
            mode="OFFLINE_FAKE",
            system_version="0.4.0",
            inputs=inputs,
            evidence={
                "input://m12/evidence_support": {
                    SOURCE_ORIGIN: "sha256:ab",
                }
            },
            runtime_scorers={
                ("metric_correctness", "1.0.0"): metric_correctness_scorer(artifacts),
                ("direction_improvement", "1.0.0"): direction_improvement_scorer(),
                ("citation_source", "1.0.0"): citation_source_scorer(ledger, RUN_ID),
                ("unsupported_claim", "1.0.0"): unsupported_claim_scorer(ledger),
            },
        )
    )
    return outcome.report


def _case(case_id: str, expected: object) -> EvalCase:
    return EvalCase(
        id=case_id,
        version=Version("1.0.0"),
        scope=EvalScope.WORKFLOW,
        input_ref=f"input://{case_id}",
        expected=expected,
        scorer_refs=(),
    )


class TestM12Adversarial:
    def test_direction_reversed_fails(self) -> None:
        """1. 方向反转：candidate 声称更好但实际更差 → FAIL。"""
        report = _run_evaluation(
            {
                **_BASE_INPUTS,
                "input://m12/experimental_validity": {
                    "status": "SUCCEEDED",
                    "metrics": {"baseline_accuracy": "0.20", "candidate_accuracy": "0.75"},
                    "seed": 7,
                },
            }
        )
        result = next(
            item for item in report.results if item.case_id == "direction_improvement_001"
        )
        assert result.scorer_findings[0].status is EvalFindingStatus.FAIL

    def test_metric_exaggerated_to_0999_fails(self) -> None:
        """2. metric 夸大：报告 0.999，artifact 重算 0.745 → FAIL。"""
        report = _run_evaluation({**_BASE_INPUTS, "input://m12/result_correctness": "0.999"})
        result = next(
            item for item in report.results if item.case_id == "result_correctness_001"
        )
        assert result.scorer_findings[0].status is EvalFindingStatus.FAIL

    def test_wrong_artifact_digest_fails(self) -> None:
        """3. artifact 内容被替换（digest 漂移）→ 独立 ground truth 重算不符，
        且整体 verdict 不得 PASS（篡改必须被拦截）。"""
        tampered = _artifact_content(baseline="0.500")
        report = _run_evaluation(
            {**_BASE_INPUTS, "input://m12/result_correctness": "0.500"},
            artifacts=_artifacts(tampered),
        )
        assert report.gate_verdict is not QualityGateVerdict.PASS
        # 被替换的 artifact 使依赖真实状态的 case 失败/设施错误（非自证通过）

    def test_missing_evidence_fails(self) -> None:
        """4. 缺 Evidence：claim 无 relations → unsupported_claim FAIL。"""
        report = _run_evaluation(
            _BASE_INPUTS,
            ledger=_ledger(with_claim=False),
        )
        result = next(
            item for item in report.results if item.case_id == "claim_calibration_001"
        )
        assert any(
            finding.status in (EvalFindingStatus.FAIL, EvalFindingStatus.INFRA_ERROR)
            for finding in result.scorer_findings
        )

    def test_unsupported_claim_fails(self) -> None:
        """5. unsupported claim：仅 REFUTES 无 SUPPORTS → FAIL。"""
        ledger = _ledger(relation=EvidenceRelationType.REFUTES)
        report = _run_evaluation(_BASE_INPUTS, ledger=ledger)
        result = next(
            item for item in report.results if item.case_id == "claim_calibration_001"
        )
        assert any(
            finding.status is EvalFindingStatus.FAIL for finding in result.scorer_findings
        )

    def test_contradictory_evidence_fails(self) -> None:
        """6. 矛盾证据：claim DISPUTED → evidence_provenance FAIL。"""
        ledger = _ledger(claim_status=ClaimStatus.DISPUTED)
        scorer = evidence_provenance_scorer(ledger)
        finding = scorer(
            ScorerContext(
                case=_case("c1", {"claim_id": CLAIM_ID, "minimum_sources": 1}),
                input=ScorerInput(actual={}),
            )
        )
        assert finding.status is EvalFindingStatus.FAIL
        assert "disputed" in finding.detail

    def test_fake_reproduction_fails(self) -> None:
        """7. fake reproduction：audit 缺 metrics_digest 锚点 → required_fields FAIL。"""
        report = _run_evaluation(
            {
                **_BASE_INPUTS,
                "input://m12/reproducibility": {
                    "audit_status": "PASS",
                    "image_digest": "sha256:ab",
                    "workspace_snapshot_before": "sha256:cd",
                    "workspace_snapshot_after": "sha256:ef",
                    # metrics_digest 缺失 → 伪造的 PASS 不成立
                },
            }
        )
        result = next(
            item for item in report.results if item.case_id == "reproducibility_001"
        )
        assert result.scorer_findings[0].status is EvalFindingStatus.FAIL

    def test_wrong_source_id_fails(self) -> None:
        """8. wrong source id：evidence 属于其他 run → citation_source FAIL。"""
        report = _run_evaluation(
            _BASE_INPUTS,
            ledger=_ledger(evidence_run_id="99999999-2222-4333-8444-555555555555"),
        )
        result = next(
            item for item in report.results if item.case_id == "claim_calibration_001"
        )
        assert any(
            finding.status is EvalFindingStatus.FAIL for finding in result.scorer_findings
        )