"""Artifact 内容寻址 digest / verify 专项测试。"""

from __future__ import annotations

import pytest

from packages.domain.artifacts import (
    Artifact,
    ArtifactRetentionPolicy,
    verify_artifact_content,
)
from packages.domain.core import Digest
from packages.domain.enums import ArtifactState


def _content() -> bytes:
    return b"research-os artifact payload"


def _artifact() -> Artifact:
    content = _content()
    return Artifact(
        id="artifact-1",
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type="text/plain",
        storage_uri="s3://bucket/artifact-1",
        created_by="agent-domain-a",
        classification="internal",
        retention_policy=ArtifactRetentionPolicy.retain_days(30),
    )


def test_artifact_digest_matches_content() -> None:
    artifact = _artifact()
    assert verify_artifact_content(artifact, _content())


def test_artifact_digest_rejects_tampered_content() -> None:
    artifact = _artifact()
    tampered = _content() + b"!"
    assert not verify_artifact_content(artifact, tampered)


def test_artifact_digest_is_sha256_prefixed() -> None:
    artifact = _artifact()
    assert str(artifact.digest).startswith("sha256:")
    assert len(artifact.digest.hex_value) == 64


def test_artifact_same_content_dedupes() -> None:
    content = _content()
    first = Digest.of_bytes(content)
    second = Digest.of_bytes(content)
    assert first == second


def test_artifact_state_defaults_to_staged() -> None:
    artifact = _artifact()
    assert artifact.state is ArtifactState.STAGED


def test_artifact_requires_media_type() -> None:
    content = _content()
    with pytest.raises(ValueError):
        Artifact(
            id="artifact-2",
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="",
        )


def test_artifact_negative_size_rejected() -> None:
    content = _content()
    with pytest.raises(ValueError):
        Artifact(
            id="artifact-3",
            digest=Digest.of_bytes(content),
            size_bytes=-1,
            media_type="text/plain",
        )


class TestArtifactRetentionPolicy:
    def test_keep_forever_and_legal_hold_are_indefinite(self) -> None:
        assert ArtifactRetentionPolicy.keep_forever().is_indefinite
        assert ArtifactRetentionPolicy.legal_hold().is_indefinite
        assert not ArtifactRetentionPolicy.retain_days(30).is_indefinite

    def test_retain_days_requires_non_negative_days(self) -> None:
        with pytest.raises(ValueError):
            ArtifactRetentionPolicy.retain_days(-1)

    def test_indefinite_kinds_reject_days(self) -> None:
        with pytest.raises(ValueError):
            ArtifactRetentionPolicy(kind=ArtifactRetentionPolicy.KEEP_FOREVER, days=5)

    def test_roundtrip_serialization(self) -> None:
        for policy in (
            ArtifactRetentionPolicy.keep_forever(),
            ArtifactRetentionPolicy.legal_hold(),
            ArtifactRetentionPolicy.retain_days(365),
        ):
            assert ArtifactRetentionPolicy.parse(policy.to_str()) == policy

    def test_invalid_literal_rejected(self) -> None:
        with pytest.raises(ValueError):
            ArtifactRetentionPolicy.parse("delete-immediately")
