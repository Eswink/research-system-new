"""Artifact 域实体定义（内容寻址 digest + verification）。

来源：docs/architecture/DATA_LIFECYCLE.md、docs/storage/ARTIFACT_STORE.md。
sha256 内容寻址；本层只做 digest/verify，不做对象存储（M5/P1 Port）。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.domain.core import Digest
from packages.domain.enums import ArtifactState


@dataclass(frozen=True, slots=True)
class Artifact:
    id: str
    digest: Digest
    size_bytes: int
    media_type: str
    storage_uri: str | None = None
    created_by: str | None = None
    source_refs: list[str] = field(default_factory=list)
    classification: str | None = None
    retention_policy: str | None = None
    state: ArtifactState = ArtifactState.STAGED

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("artifact id must not be empty")
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be non-negative")
        if not self.media_type:
            raise ValueError("media_type must not be empty")


def verify_artifact_content(artifact: Artifact, content: bytes) -> bool:
    """校验内容与 Artifact 声明 digest 一致（内容寻址）。"""
    return Digest.of_bytes(content) == artifact.digest
