"""M12 Independent Evaluation E2E：M11 harness 独立评测 M12 workflow 产物。

用真实 M12 实验/证据链产物作为冻结输入，跑 `m12_research_v1` 评测集
（deterministic scorer + independent ground truth scorer），验证：
- 冻结数据集 digest 校验（篡改拒绝）；
- 全部 case PASS → gate verdict PASS（metric 与 ArtifactStore 独立重算一致）；
- 输入缺失 → INFRA_ERROR（不判被评对象失败）；
- 报告 digest 可复现（同输入同 digest）；
- baseline vs candidate 方向与 Claim 语义一致（M12-R1 WP5：无 0.745 自证常量）。
"""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

from adapters.contracts.eval_loaders import load_eval_dataset
from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger
from packages.application.evaluation.runner import RunRequest, run_evaluation
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
from packages.domain.eval_result import EvalFindingStatus, EvalReport
from packages.domain.eval_spec import EvalDataset
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)

DATASET_PATH = "examples/eval/datasets/m12_research_v1.yaml"
SYSTEM_VERSION = "0.4.0"
RUN_ID = "12121212-2222-4333-8444-555555555555"
EXPERIMENT_RUN_ID = "5a1c6a8e-9b2d-4f3a-8c5e-2b2c3d4e5f6a"
ARTIFACT_ID = f"{RUN_ID}:experiment_result.json"
CLAIM_ID = f"claim:{RUN_ID}"
EVIDENCE_ID = f"evidence:{RUN_ID}:{EXPERIMENT_RUN_ID}"
SOURCE_ORIGIN = f"experiment:{EXPERIMENT_RUN_ID}:experiment_result.json"


def _artifact_content() -> bytes:
    return json.dumps(
        {
            "experiment_run_id": EXPERIMENT_RUN_ID,
            "status": "SUCCEEDED",
            "metrics": {
                "baseline_accuracy": "0.745",
                "candidate_accuracy": "0.28",
                "n_train": 500,
                "n_test": 200,
            },
            "seed": 7,
        },
        sort_keys=True,
    ).encode("utf-8")


def _artifacts() -> FakeArtifactStore:
    store = FakeArtifactStore()
    content = _artifact_content()
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


def _ledger() -> FakeEvidenceLedger:
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
            run_id=RUN_ID,
            experiment_run_id=EXPERIMENT_RUN_ID,
        )
    )
    ledger.register_claim(
        Claim(
            id=CLAIM_ID,
            statement="baseline outperforms candidate",
            status=ClaimStatus.PROPOSED,
            evidence_relations=[(EVIDENCE_ID, EvidenceRelationType.SUPPORTS)],
        )
    )
    ledger.attach_relation(
        EvidenceRelation(
            claim_id=CLAIM_ID,
            evidence_id=EVIDENCE_ID,
            relation=EvidenceRelationType.SUPPORTS,
        )
    )
    return ledger


_REAL_EXPERIMENT = {
    "status": "SUCCEEDED",
    "metrics": {
        "baseline_accuracy": "0.745",
        "candidate_accuracy": "0.28",
        "n_train": 500,
        "n_test": 200,
    },
    "hypothesis": "hash-embedding+linear classifier beats tfidf on low-resource subset",
    "seed": 7,
}

_REAL_EVIDENCE = {
    "claim_status": "VERIFIED",
    "evidence_ids": (EVIDENCE_ID,),
    "relation_types": ("SUPPORTS",),
}

_REAL_REPRO = {
    "audit_status": "PASS",
    "image_digest": "sha256:" + "ab" * 32,
    "workspace_snapshot_before": "sha256:" + "cd" * 32,
    "workspace_snapshot_after": "sha256:" + "ef" * 32,
    "metrics_digest": "sha256:" + "12" * 32,
}

_REAL_CITATION: dict[str, str] = {"algorithm": "sha256", "hex": "00" * 32}

_REAL_UNSUPPORTED: dict[str, object] = {"unsupported_claims": []}

_REAL_DELIVERABLE = {
    "claim_id": CLAIM_ID,
    "evidence_ids": (EVIDENCE_ID,),
    "metrics": {"baseline_accuracy": "0.745", "candidate_accuracy": "0.28"},
}

_REAL_COST = {
    "model_tokens": 0,
    "tool_requests": 1,
    "experiment_runs": 2,
    "evaluation_runs": 1,
}

_INPUTS: dict[str, object] = {
    "input://m12/task_completion": {"status": "SUCCEEDED"},
    "input://m12/evidence_support": {"sources": 2},
    "input://m12/experimental_validity": _REAL_EXPERIMENT,
    # 报告自报值；metric_correctness 从 ArtifactStore 独立重算比对
    "input://m12/result_correctness": "0.745",
    "input://m12/reproducibility": _REAL_REPRO,
    "input://m12/claim_calibration": _REAL_EVIDENCE,
    "input://m12/citation_correctness": "00" * 32,
    "input://m12/unsupported_conclusion": _REAL_UNSUPPORTED,
    "input://m12/deliverable_quality": _REAL_DELIVERABLE,
    "input://m12/cost_efficiency": _REAL_COST,
}

# evidence_source_distinct 读取 ScorerInput.evidence_sources（来自 RunRequest.evidence）
_EVIDENCE: dict[str, dict[str, str]] = {
    "input://m12/evidence_support": {
        SOURCE_ORIGIN: "sha256:" + "ab" * 32,
        f"experiment:{EXPERIMENT_RUN_ID}:repro-2": "sha256:" + "cd" * 32,
    }
}


def _dataset() -> EvalDataset:
    return load_eval_dataset(DATASET_PATH)


def _gate() -> GateConfig:
    return GateConfig(
        id="m12-independent-gate",
        version=Version("1.0.0"),
        min_pass_ratio=Decimal("0.8"),
    )


def _runtime_scorers(
    artifacts: FakeArtifactStore, ledger: FakeEvidenceLedger
) -> dict[tuple[str, str], object]:
    return {
        ("metric_correctness", "1.0.0"): metric_correctness_scorer(artifacts),
        ("direction_improvement", "1.0.0"): direction_improvement_scorer(),
        ("citation_source", "1.0.0"): citation_source_scorer(ledger, RUN_ID),
        ("unsupported_claim", "1.0.0"): unsupported_claim_scorer(ledger),
    }


def _run(
    dataset: EvalDataset,
    inputs: dict[str, object],
    *,
    artifacts: FakeArtifactStore | None = None,
    ledger: FakeEvidenceLedger | None = None,
) -> EvalReport:
    artifacts = artifacts or _artifacts()
    ledger = ledger or _ledger()
    outcome = run_evaluation(
        RunRequest(
            dataset=dataset,
            config=_gate(),
            mode="OFFLINE_FAKE",
            system_version=SYSTEM_VERSION,
            inputs=inputs,
            evidence=_EVIDENCE,
            runtime_scorers=_runtime_scorers(artifacts, ledger),
        )
    )
    assert outcome.missing_inputs == ()
    return outcome.report


class TestM12IndependentEvaluation:
    def test_all_cases_pass_with_real_artifacts(self) -> None:
        report = _run(_dataset(), _INPUTS)
        assert report.gate_verdict is QualityGateVerdict.PASS
        assert len(report.results) == 11
        for result in report.results:
            assert result.passed, f"case {result.case_id} failed: {result.scorer_findings}"

    def test_missing_input_is_infra_error_not_fail(self) -> None:
        dataset = _dataset()
        inputs = dict(_INPUTS)
        inputs.pop("input://m12/result_correctness")
        outcome = run_evaluation(
            RunRequest(
                dataset=dataset,
                config=_gate(),
                mode="OFFLINE_FAKE",
                system_version=SYSTEM_VERSION,
                inputs=inputs,
                evidence=_EVIDENCE,
                runtime_scorers=_runtime_scorers(_artifacts(), _ledger()),
            )
        )
        assert outcome.missing_inputs == ("input://m12/result_correctness",)
        missing = [
            result
            for result in outcome.report.results
            if result.case_id == "result_correctness_001"
        ][0]
        assert missing.scorer_findings[0].status is EvalFindingStatus.INFRA_ERROR
        # 设施失败 → REVISE 而非 BLOCK（不把设施故障映射为被评对象失败）
        assert outcome.report.gate_verdict is QualityGateVerdict.REVISE

    def test_report_digest_reproducible(self) -> None:
        first = _run(_dataset(), _INPUTS)
        second = _run(_dataset(), _INPUTS)
        assert first.digest() == second.digest()

    def test_dataset_tampering_rejected(self) -> None:
        # 篡改 digest → load 拒绝（fail-closed）
        raw = _dataset_path_text().replace("result_correctness_001", "result_correctness_002")
        with pytest.raises(Exception):
            from packages.application.evaluation.registry import dataset_from_dict

            dataset_from_dict(_parse(raw), declared_digest="sha256:" + "0" * 64)

    def test_metric_ground_truth_from_artifact_not_expected_constant(self) -> None:
        """0.745 不再以 expected 常量形式存在于 dataset（自证循环消除）。

        dataset expected 只含 artifact_id + metric 路径；报告自报值由
        metric_correctness 从 ArtifactStore 独立重算比对。
        """
        raw = _dataset_path_text()
        assert "'0.745'" not in raw
        assert "metric: metrics.baseline_accuracy" in raw
        assert "artifact_id:" in raw

    def test_reported_metric_must_match_artifact(self) -> None:
        """伪造报告值（0.999）→ metric_correctness FAIL。"""
        report = _run(_dataset(), {**_INPUTS, "input://m12/result_correctness": "0.999"})
        result = next(
            item for item in report.results if item.case_id == "result_correctness_001"
        )
        assert not result.passed
        assert result.scorer_findings[0].status is EvalFindingStatus.FAIL

    def test_reversed_direction_fails(self) -> None:
        """方向反转（candidate 0.75 > baseline 0.20）→ direction_improvement FAIL。"""
        reversed_experiment = {
            "status": "SUCCEEDED",
            "metrics": {
                "baseline_accuracy": "0.20",
                "candidate_accuracy": "0.75",
                "n_train": 500,
                "n_test": 200,
            },
            "seed": 7,
        }
        report = _run(
            _dataset(),
            {**_INPUTS, "input://m12/experimental_validity": reversed_experiment},
        )
        result = next(
            item for item in report.results if item.case_id == "direction_improvement_001"
        )
        assert not result.passed
        assert result.scorer_findings[0].status is EvalFindingStatus.FAIL


def _dataset_path_text() -> str:
    from pathlib import Path

    return Path(DATASET_PATH).read_text(encoding="utf-8")


def _parse(text: str) -> dict[str, object]:
    import yaml

    parsed = yaml.safe_load(text)
    if not isinstance(parsed, dict):
        raise ValueError("dataset must be a mapping")
    return parsed
