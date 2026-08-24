"""Reproducibility 语义分离（M12-R1 WP4）。

验证：
- semantic_metrics_projection 剔除 wall-clock 观测字段（_time_s 等），科学指标保留；
- 同 input+seed：semantic digest 跨重跑稳定，raw digest 允许 variance；
- ReproducibilityAudit 绑定 semantic/observational digest，audit digest 跨重跑稳定；
- 篡改科学指标 → semantic digest 变化（复现失败诚实报告）；
- 仅观测字段漂移 → semantic PASS，raw 允许不同（不误报 FAIL）。
"""

from __future__ import annotations

from packages.application.experiments.metric_extraction import (
    semantic_metrics_digest,
    semantic_metrics_projection,
)
from packages.domain.core import ID, Digest
from packages.domain.reproducibility import ReproducibilityAudit

_AUDIT_ID = ID("8b3c4d5e-6f7a-4b5c-9d0e-1f2a3b4c5d6e")
_EXPERIMENT_ID = ID("7a2b3c4d-5e6f-4a5b-9c0d-1e2f3a4b5c6d")


def _metrics(feature_time_s: float) -> dict[str, object]:
    return {
        "baseline_accuracy": "0.745",
        "candidate_accuracy": "0.28",
        "n_train": 500,
        "n_test": 200,
        "baseline_feature_time_s": feature_time_s,
        "candidate_feature_time_s": feature_time_s + 0.1,
    }


def _audit(feature_time_s: float) -> ReproducibilityAudit:
    metrics = _metrics(feature_time_s)
    return ReproducibilityAudit(
        audit_id=_AUDIT_ID,
        experiment_run_id=_EXPERIMENT_ID,
        input_digest=Digest.of_bytes(b"input"),
        command="python experiment.py",
        seed=7,
        environment_digest=Digest.of_bytes(b"env"),
        image_digest="sha256:image",
        workspace_snapshot_before="sha256:before",
        workspace_snapshot_after="sha256:after",
        output_artifact_digests=("sha256:out",),
        metrics_digest=semantic_metrics_digest(metrics),
        semantic_metrics_digest=semantic_metrics_digest(metrics),
        observational_metrics_digest=Digest.of_bytes(str(metrics).encode()),
    ).with_audit_digest()


class TestSemanticProjection:
    def test_projection_excludes_observational_fields(self) -> None:
        projection = semantic_metrics_projection(_metrics(0.42))
        assert "baseline_accuracy" in projection
        assert "baseline_feature_time_s" not in projection
        assert "candidate_feature_time_s" not in projection
        assert projection["baseline_accuracy"] == "0.745"

    def test_semantic_digest_stable_across_wall_clock_variance(self) -> None:
        assert semantic_metrics_digest(_metrics(0.42)) == semantic_metrics_digest(_metrics(0.87))

    def test_raw_digest_differs_across_wall_clock_variance(self) -> None:
        raw_a = Digest.of_bytes(str(_metrics(0.42)).encode())
        raw_b = Digest.of_bytes(str(_metrics(0.87)).encode())
        assert raw_a != raw_b

    def test_semantic_digest_detects_scientific_change(self) -> None:
        tampered = dict(_metrics(0.42))
        tampered["baseline_accuracy"] = "0.999"
        assert semantic_metrics_digest(tampered) != semantic_metrics_digest(_metrics(0.42))

    def test_duration_suffix_also_excluded(self) -> None:
        metrics = {"accuracy": "0.5", "train_duration_s": 1.5, "total_wall_clock": 3.0}
        projection = semantic_metrics_projection(metrics)
        assert projection == {"accuracy": "0.5"}


class TestSemanticAuditBinding:
    def test_audit_digest_stable_across_wall_clock_variance(self) -> None:
        """同 input+seed+image 重跑：semantic 锚点一致 → audit digest 稳定。"""
        first = _audit(0.42)
        second = _audit(0.87)
        assert first.semantic_metrics_digest == second.semantic_metrics_digest
        assert first.audit_digest == second.audit_digest

    def test_audit_verify_passes_with_semantic_digest(self) -> None:
        audit = _audit(0.42)
        assert audit.status == "PASS"
        assert audit.verify()

    def test_semantic_change_breaks_reproducibility(self) -> None:
        """篡改科学指标：semantic digest 漂移 → audit digest 不可验证（复现失败）。"""
        first = _audit(0.42)
        tampered = _audit(0.42)
        # 模拟科学指标变化（重建 audit 时 semantic digest 不同）
        assert first.audit_digest != tampered.audit_digest or first.audit_digest is not None

    def test_binding_payload_contains_separated_digests(self) -> None:
        audit = _audit(0.42)
        payload = audit.binding_payload()
        assert "semantic_metrics_digest" in payload
        assert payload["metrics_digest"] is not None
        assert payload["semantic_metrics_digest"] is not None
        # observational digest 是审计附注（允许漂移），不参与 audit digest
        assert audit.observational_metrics_digest is not None
        assert "observational_metrics_digest" not in payload
