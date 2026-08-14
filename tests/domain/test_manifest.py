"""RunManifest / Revision / digest 专项测试。"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from packages.domain.core import Digest, Timestamp, Version
from packages.domain.manifest import RunManifest, RunManifestRevision


def _frozen() -> Timestamp:
    return Timestamp(datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc))


def _base_manifest() -> RunManifest:
    return RunManifest(run_id="run-1", project_id="project-1", protocol_version=Version("0.4.0"))


def _manifest_with_roles(roles: dict[str, object]) -> RunManifest:
    return RunManifest(
        run_id="run-1",
        project_id="project-1",
        protocol_version=Version("0.4.0"),
        role_definitions=roles,
    )


def test_manifest_digest_is_stable_across_equivalent_objects() -> None:
    first = _manifest_with_roles({"scout": {"category": "discovery"}})
    second = _manifest_with_roles({"scout": {"category": "discovery"}})
    assert first.digest() == second.digest()


def test_manifest_digest_changes_when_content_changes() -> None:
    base = _manifest_with_roles({"scout": {"category": "discovery"}})
    changed = _manifest_with_roles({"scout": {"category": "exploration"}})
    assert base.digest() != changed.digest()


def test_manifest_digest_matches_manual_canonical_digest() -> None:
    manifest = _base_manifest()
    from packages.domain.serialization import digest_of

    assert manifest.digest() == digest_of(manifest)


def test_manifest_digest_ignores_key_order_in_nested_dicts() -> None:
    left = _manifest_with_roles({"scout": {"b": 1, "a": 2}})
    right = _manifest_with_roles({"scout": {"a": 2, "b": 1}})
    assert left.digest() == right.digest()


def test_manifest_is_immutable() -> None:
    manifest = _base_manifest()
    with pytest.raises(Exception):
        manifest.run_id = "mutated"  # type: ignore[misc]


def test_manifest_digest_is_string_prefixable() -> None:
    manifest = _base_manifest()
    assert str(manifest.digest()).startswith("sha256:")
    assert Digest.parse(str(manifest.digest())).hex_value == manifest.digest().hex_value


def test_revision_records_approval_and_audit() -> None:
    base = _base_manifest()
    revision = RunManifestRevision(
        manifest_digest=Digest("cd" * 32),
        base_digest=base.digest(),
        revision_number=1,
        reason="replace model due to drift",
        changes={"model": {"from": "alpha", "to": "beta"}},
        approved_by="human-owner",
        approved_at=_frozen(),
        audit_ref="audit/trail/2026-08-11/001",
    )
    assert revision.revision_number == 1
    assert revision.base_digest != revision.manifest_digest


def test_revision_rejects_same_digest() -> None:
    base = _base_manifest()
    digest = base.digest()
    with pytest.raises(ValueError):
        RunManifestRevision(
            manifest_digest=digest,
            base_digest=digest,
            revision_number=1,
            reason="no actual change",
            changes={},
            approved_by="human",
            approved_at=_frozen(),
            audit_ref="audit-1",
        )


def test_revision_requires_approval_fields() -> None:
    base = _base_manifest()
    with pytest.raises(ValueError):
        RunManifestRevision(
            manifest_digest=Digest("cd" * 32),
            base_digest=base.digest(),
            revision_number=1,
            reason="model change",
            changes={},
            approved_by="",
            approved_at=_frozen(),
            audit_ref="audit-1",
        )
    with pytest.raises(ValueError):
        RunManifestRevision(
            manifest_digest=Digest("cd" * 32),
            base_digest=base.digest(),
            revision_number=1,
            reason="model change",
            changes={},
            approved_by="human",
            approved_at=_frozen(),
            audit_ref="",
        )


def test_manifest_requires_run_and_project_ids() -> None:
    with pytest.raises(ValueError):
        RunManifest(run_id="", project_id="p", protocol_version=Version("0.4.0"))
    with pytest.raises(ValueError):
        RunManifest(run_id="r", project_id="", protocol_version=Version("0.4.0"))


def _revision(changes: dict[str, object]) -> RunManifestRevision:
    base = _base_manifest()
    return RunManifestRevision(
        manifest_digest=Digest("cd" * 32),
        base_digest=base.digest(),
        revision_number=1,
        reason="model change",
        changes=changes,
        approved_by="human",
        approved_at=_frozen(),
        audit_ref="audit-1",
    )


def test_revision_rejects_empty_changes() -> None:
    """空 changes 的修订无意义：必须拒绝（M7 技术债清偿）。"""
    with pytest.raises(ValueError, match="must not be empty"):
        _revision({})


def test_revision_rejects_non_string_change_keys() -> None:
    """changes 的 key 必须为 str（可审计、可序列化）。"""
    with pytest.raises(ValueError, match="keys must be strings"):
        _revision({123: "value"})  # type: ignore[dict-item]


def test_revision_accepts_structured_changes() -> None:
    revision = _revision({"model": {"from": "alpha", "to": "beta"}})
    assert revision.changes == {"model": {"from": "alpha", "to": "beta"}}
