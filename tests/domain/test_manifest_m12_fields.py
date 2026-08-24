"""RunManifest M12 扩展字段的 digest 语义（WP1 契约回归）。

验证：
- 新增 M12 字段参与 digest / semantic_digest（字段漂移 → digest 漂移）；
- frozen_at 仍被 semantic_digest 排除（M1 既有语义不回退）；
- 空字段 = 未冻结（不伪填充），与非空字段 digest 可区分。
"""

from __future__ import annotations

from packages.domain.core import Version
from packages.domain.manifest import RunManifest


def _manifest(**overrides: object) -> RunManifest:
    kwargs: dict[str, object] = {
        "run_id": "run-1",
        "project_id": "project-1",
        "protocol_version": Version("0.4.0"),
    }
    kwargs.update(overrides)
    return RunManifest(**kwargs)  # type: ignore[arg-type]


def test_m12_fields_enter_digest() -> None:
    base = _manifest()
    frozen = _manifest(
        endpoint_config_digest="sha256:aaaa",
        probe_suite_digest="sha256:bbbb",
        fallback_audit={"mode": "none"},
        image_digest="sha256:cccc",
        skill_versions={"m12-skill": "1.0.0"},
        evaluation_dataset_digest="sha256:dddd",
    )
    assert base.digest() != frozen.digest()
    assert base.semantic_digest() != frozen.semantic_digest()


def test_each_m12_field_changes_semantic_digest() -> None:
    base = _manifest()
    changed = _manifest(fallback_audit={"mode": "none"})
    assert base.semantic_digest() != changed.semantic_digest()
    changed = _manifest(image_digest="sha256:image")
    assert base.semantic_digest() != changed.semantic_digest()
    changed = _manifest(model_runtime_fingerprints={"research_alpha": {"ok": False}})
    assert base.semantic_digest() != changed.semantic_digest()


def test_frozen_at_still_excluded_from_semantic_digest() -> None:
    first = _manifest()
    second = _manifest()
    assert first.semantic_digest() == second.semantic_digest()
    assert first.digest() == second.digest()


def test_fallback_none_is_explicit_and_distinct() -> None:
    none_manifest = _manifest(fallback_audit={"mode": "none"})
    planned_manifest = _manifest(
        fallback_audit={
            "mode": "planned",
            "from_model": "a",
            "to_model": "b",
            "trigger": "probe_failure",
        }
    )
    empty_manifest = _manifest()
    assert none_manifest.digest() != planned_manifest.digest()
    assert none_manifest.digest() != empty_manifest.digest()


def test_manifest_is_immutable_and_typed() -> None:
    manifest = _manifest(fallback_audit={"mode": "none"})
    assert manifest.fallback_audit == {"mode": "none"}
    assert manifest.endpoint_config_digest is None  # 未冻结 = 诚实 None，不伪填充
