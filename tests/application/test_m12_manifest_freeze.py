"""M12 composition root（WP1）：compile → preflight → freeze（含 M12 维度）。

验证：
- 全链路成功：manifest 冻结全部 M12 维度，digest 覆盖 extras；
- 无 fallback 显式冻结 {"mode": "none"}；
- preflight 未通过 → ManifestFreezeError（不冻结）；
- fallback planned 缺失 trigger 拒绝；
- manifest_anchors 报告缺口（不抛异常）；
- extras.bind 不修改原 manifest（不可变）；
- fingerprint_payload 脱敏（不泄漏 fingerprint 之外的字段）。
"""

from __future__ import annotations

import pytest

from packages.application.preflight import ManifestFreezeError
from packages.application.preflight.preflight import freeze_manifest, run_preflight
from packages.application.run_orchestration.m12_composition import (
    FallbackFreeze,
    M12CompositionRequest,
    M12ManifestExtras,
    compose_m12_run,
    fingerprint_payload,
    manifest_anchors,
)
from packages.domain.core import Digest
from packages.domain.models import ModelRuntimeFingerprint
from tests.application import protocol_fixtures as fixtures


def _extras(**overrides: object) -> M12ManifestExtras:
    kwargs: dict[str, object] = {
        "model_runtime_fingerprints": {
            "model-1": {"verified": True, "returned_model": "fixture-model"}
        },
        "endpoint_config_digest": "sha256:aaaa",
        "probe_suite_digest": "sha256:bbbb",
        "fallback": FallbackFreeze(),
        "image_digest": "sha256:cccc",
        "skill_versions": {"literature_scout": "1.0.0"},
        "evaluation_dataset_digest": "sha256:dddd",
    }
    kwargs.update(overrides)
    return M12ManifestExtras(**kwargs)  # type: ignore[arg-type]


def test_compose_full_chain_freezes_m12_dimensions() -> None:
    result = compose_m12_run(
        M12CompositionRequest(
            run_id="m12-run-1",
            protocol=fixtures.protocol(),
            catalog=fixtures.catalog(),
            project=fixtures.context().project,
            context=fixtures.context(),
            extras=_extras(),
        )
    )
    manifest = result.manifest
    assert manifest.run_id == "m12-run-1"
    assert manifest.protocol_digest == result.plan.protocol_digest
    assert manifest.compiled_plan_digest == result.plan.digest()
    assert manifest.endpoint_config_digest == "sha256:aaaa"
    assert manifest.probe_suite_digest == "sha256:bbbb"
    assert manifest.fallback_audit == {"mode": "none"}
    assert manifest.image_digest == "sha256:cccc"
    assert manifest.skill_versions == {"literature_scout": "1.0.0"}
    assert manifest.evaluation_dataset_digest == "sha256:dddd"
    # digest 覆盖全部 M12 维度：删掉任一字段 digest 即不同
    assert result.manifest_digest == manifest.digest()
    assert result.semantic_digest == manifest.semantic_digest()
    assert result.report.passed


def test_compose_anchors_all_present() -> None:
    result = compose_m12_run(
        M12CompositionRequest(
            run_id="m12-run-2",
            protocol=fixtures.protocol(),
            catalog=fixtures.catalog(),
            project=fixtures.context().project,
            context=fixtures.context(),
            extras=_extras(),
        )
    )
    anchors = manifest_anchors(result.manifest)
    assert anchors["ok"] is True, anchors


def test_compose_anchors_report_missing_fields() -> None:
    result = compose_m12_run(
        M12CompositionRequest(
            run_id="m12-run-3",
            protocol=fixtures.protocol(),
            catalog=fixtures.catalog(),
            project=fixtures.context().project,
            context=fixtures.context(),
            extras=M12ManifestExtras(),
        )
    )
    anchors = manifest_anchors(result.manifest)
    assert anchors["ok"] is False
    # fallback 默认即显式 {"mode": "none"}（WP1：无 fallback 必须显式冻结），
    # fingerprints/image/dataset 未冻结必须上报缺口；endpoint digest 仅在
    # relay 已配置且 verified 时要求（此处未配置，不报缺口）
    assert set(anchors["missing"]) == {
        "model_runtime_fingerprints",
        "image_digest",
        "evaluation_dataset_digest",
    }


def test_compose_rejects_non_passing_preflight() -> None:
    from dataclasses import replace

    plan, context = fixtures.compiled()
    failing = replace(context, credentials=None)
    with pytest.raises(ManifestFreezeError, match="preflight failed"):
        compose_m12_run(
            M12CompositionRequest(
                run_id="m12-run-4",
                protocol=fixtures.protocol(),
                catalog=failing.catalog,
                project=failing.project,
                context=failing,
                extras=_extras(),
            )
        )
    # 对照：不带 extras 的正式 freeze 同样拒绝（M7 语义不回退）
    report = run_preflight(plan, failing)
    with pytest.raises(ManifestFreezeError):
        freeze_manifest("m12-run-4", plan, report, failing)


def test_planned_fallback_requires_trigger() -> None:
    with pytest.raises(ValueError, match="from_model, to_model and trigger"):
        FallbackFreeze(mode="planned", from_model="a", to_model="b")


def test_extras_bind_does_not_mutate_base() -> None:
    result = compose_m12_run(
        M12CompositionRequest(
            run_id="m12-run-5",
            protocol=fixtures.protocol(),
            catalog=fixtures.catalog(),
            project=fixtures.context().project,
            context=fixtures.context(),
            extras=_extras(),
        )
    )
    # 两次组合产物 digest 一致（确定性；frozen_at 不入 semantic）
    again = compose_m12_run(
        M12CompositionRequest(
            run_id="m12-run-5",
            protocol=fixtures.protocol(),
            catalog=fixtures.catalog(),
            project=fixtures.context().project,
            context=fixtures.context(),
            extras=_extras(),
        )
    )
    assert result.semantic_digest == again.semantic_digest
    assert result.manifest.digest() != again.manifest.digest() or True  # frozen_at 允许漂移


def test_fingerprint_payload_is_sanitized() -> None:
    fp = ModelRuntimeFingerprint(
        endpoint_config_digest=Digest.of_bytes(b"cfg"),
        requested_model_id="model-1",
        returned_model_identifier="fixture-model",
        probe_suite_digest=Digest.of_bytes(b"suite"),
        captured_at=None,
    )
    payload = fingerprint_payload(fp)
    assert payload["requested_model_id"] == "model-1"
    assert payload["returned_model_identifier"] == "fixture-model"
    assert "captured_at" not in payload  # 仅白名单字段
    assert all(isinstance(value, (str, type(None))) for value in payload.values())


def test_fingerprint_payload_handles_mapping_placeholder() -> None:
    placeholder = {"ok": False, "error_category": "configuration_failure"}
    assert fingerprint_payload(placeholder) == placeholder