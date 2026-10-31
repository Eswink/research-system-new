"""Artifact 内容寻址 digest / verify 专项测试。"""

from __future__ import annotations

import pytest

from packages.domain.artifacts import (
    Artifact,
    ArtifactRetentionPolicy,
    SupersedesError,
    validate_supersedes,
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


class TestSupersedes:
    """GOAL-20261031-102 EC-01：改稿闭环的**父指针**（域面判据）。

    `supersedes` 是「它替代的那个制品 id」：缺省 `None`（既有构造点零回归）、
    digest 不受影响（父指针是元数据不是内容）、链校验逐跳点名三类违例
    （目标缺席 / 跨 run / 成环）。
    """

    @staticmethod
    def _artifact(artifact_id: str, *, supersedes: str | None = None) -> Artifact:
        content = f"payload of {artifact_id}".encode("utf-8")
        return Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="text/markdown",
            supersedes=supersedes,
        )

    def test_supersedes_defaults_to_none_and_does_not_touch_the_digest(self) -> None:
        """缺省 `None`（既有构造点零回归）且父指针不进内容哈希。"""
        plain = self._artifact("run-1:manuscript.md")
        assert plain.supersedes is None
        child = self._artifact("run-1:manuscript_v2.md", supersedes="run-1:manuscript.md")
        same = self._artifact("run-1:manuscript_v2.md")
        assert child.digest == same.digest, "父指针改变了内容哈希 ⇒ digest 不再是内容寻址"

    def test_self_reference_is_refused_at_construction(self) -> None:
        with pytest.raises(ValueError, match="cannot supersede itself"):
            self._artifact("run-1:manuscript.md", supersedes="run-1:manuscript.md")

    def test_chain_resolves_inside_one_run(self) -> None:
        """A ⊳ B 且 B 在场 ⇒ 链校验通过（正臂）。"""
        v1 = self._artifact("run-1:manuscript.md")
        v2 = self._artifact("run-1:manuscript_v2.md", supersedes=v1.id)
        store: dict[str, Artifact] = {v1.id: v1, v2.id: v2}
        validate_supersedes(v2, run_id="run-1", resolve=lambda key: store.get(key))

    def test_missing_target_is_named(self) -> None:
        """目标解析不出来 ⇒ 点名缺席的那一个 id。"""
        v2 = self._artifact("run-1:manuscript_v2.md", supersedes="run-1:manuscript.md")
        with pytest.raises(SupersedesError, match="does not exist in run run-1"):
            validate_supersedes(v2, run_id="run-1", resolve=lambda _key: None)

    def test_cross_run_target_is_named(self) -> None:
        """跨 run 引用属另一轮 ⇒ 点名拒绝（不在场之前先判）。"""
        other = self._artifact("run-9:manuscript.md")
        v2 = self._artifact("run-1:manuscript_v2.md", supersedes=other.id)
        with pytest.raises(SupersedesError, match="outside run run-1"):
            validate_supersedes(v2, run_id="run-1", resolve={other.id: other}.get)

    def test_two_node_cycle_is_named(self) -> None:
        """A ⊳ B 且 B ⊳ A ⇒ 成环点名（判据 (v) 的域面反证）。"""
        a = self._artifact("run-1:a.md")
        b = self._artifact("run-1:b.md", supersedes=a.id)
        a = Artifact(
            id=a.id,
            digest=a.digest,
            size_bytes=a.size_bytes,
            media_type=a.media_type,
            supersedes=b.id,
        )
        store: dict[str, Artifact] = {a.id: a, b.id: b}
        with pytest.raises(SupersedesError, match="supersedes cycle"):
            validate_supersedes(a, run_id="run-1", resolve=lambda key: store.get(key))

    def test_longer_chain_cycle_is_named(self) -> None:
        """A ⊳ B ⊳ C ⊳ A ⇒ 三环同样被链游走抓到（不是只判二环）。"""
        a = self._artifact("run-1:a.md")
        b = self._artifact("run-1:b.md", supersedes=a.id)
        c = self._artifact("run-1:c.md", supersedes=b.id)
        a = Artifact(
            id=a.id,
            digest=a.digest,
            size_bytes=a.size_bytes,
            media_type=a.media_type,
            supersedes=c.id,
        )
        store: dict[str, Artifact] = {a.id: a, b.id: b, c.id: c}
        with pytest.raises(SupersedesError, match="supersedes cycle"):
            validate_supersedes(a, run_id="run-1", resolve=lambda key: store.get(key))
