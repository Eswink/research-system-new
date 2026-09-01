"""FakeArtifactStore：内容寻址 Artifact 存储（digest 校验 + 状态流转）。"""

from __future__ import annotations

from adapters.fakes.base import FakeBase
from packages.application.ports.errors import InvalidInputError
from packages.domain.artifacts import Artifact, verify_artifact_content
from packages.domain.enums import ArtifactState

_VALID_TRANSITIONS: dict[ArtifactState, frozenset[ArtifactState]] = {
    ArtifactState.STAGED: frozenset({ArtifactState.VERIFIED, ArtifactState.QUARANTINED}),
    ArtifactState.VERIFIED: frozenset({ArtifactState.ACTIVE, ArtifactState.QUARANTINED}),
    ArtifactState.QUARANTINED: frozenset({
        ArtifactState.ACTIVE,
        ArtifactState.VERIFIED,
        ArtifactState.DELETED_TOMBSTONE,
    }),
    ArtifactState.ACTIVE: frozenset({ArtifactState.ARCHIVED, ArtifactState.DELETED_TOMBSTONE}),
    ArtifactState.ARCHIVED: frozenset({ArtifactState.DELETED_TOMBSTONE}),
    ArtifactState.DELETED_TOMBSTONE: frozenset(),
}


class FakeArtifactStore(FakeBase):
    """put 校验内容 digest；mark 强制合法状态流转。"""

    def __init__(self) -> None:
        super().__init__("artifact_store")
        self._content: dict[str, bytes] = {}
        self._metadata: dict[str, Artifact] = {}

    def put(self, artifact: Artifact, content: bytes) -> None:
        self._enter("put", artifact.id)
        if not verify_artifact_content(artifact, content):
            self._record("put", artifact.id, error="InvalidInputError")
            raise InvalidInputError(f"artifact content digest mismatch for {artifact.id}")
        self._content[artifact.id] = content
        self._metadata[artifact.id] = artifact
        self._record("put", f"{artifact.id}/{len(content)}", result="stored")

    def get(self, artifact_id: str) -> bytes:
        self._enter("get", artifact_id)
        self._require_readable("get", artifact_id)
        self._record("get", artifact_id, result=str(len(self._content[artifact_id])))
        return self._content[artifact_id]

    def verify(self, artifact_id: str) -> bool:
        self._enter("verify", artifact_id)
        if artifact_id not in self._content or artifact_id not in self._metadata:
            self._record("verify", artifact_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown artifact id: {artifact_id}")
        ok = verify_artifact_content(self._metadata[artifact_id], self._content[artifact_id])
        self._record("verify", artifact_id, result=str(ok))
        return ok

    def meta(self, artifact_id: str) -> Artifact | None:
        self._enter("meta", artifact_id)
        artifact = self._metadata.get(artifact_id)
        self._record("meta", artifact_id, result="found" if artifact is not None else "none")
        return artifact

    def _require_readable(self, method: str, artifact_id: str) -> None:
        if artifact_id not in self._content:
            self._record(method, artifact_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown artifact id: {artifact_id}")
        state = self._metadata[artifact_id].state
        if state is ArtifactState.DELETED_TOMBSTONE:
            self._record(method, artifact_id, error="InvalidInputError")
            raise InvalidInputError(f"artifact deleted: {artifact_id}")

    def mark(self, artifact_id: str, state: ArtifactState) -> None:
        self._enter("mark", artifact_id)
        if artifact_id not in self._metadata:
            self._record("mark", artifact_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown artifact id: {artifact_id}")
        current = self._metadata[artifact_id]
        if state not in _VALID_TRANSITIONS[current.state]:
            self._record("mark", artifact_id, error="InvalidInputError")
            raise InvalidInputError(
                f"illegal artifact state transition {current.state.value} -> {state.value}",
            )
        self._metadata[artifact_id] = Artifact(
            id=current.id,
            digest=current.digest,
            size_bytes=current.size_bytes,
            media_type=current.media_type,
            storage_uri=current.storage_uri,
            created_by=current.created_by,
            source_refs=list(current.source_refs),
            classification=current.classification,
            retention_policy=current.retention_policy,
            state=state,
            created_at=current.created_at,
        )
        self._record("mark", f"{artifact_id}/{state.value}")

    def list_refs(self) -> tuple[Artifact, ...]:
        self._enter("list_refs", "")
        self._record("list_refs", "")
        return tuple(self._metadata.values())

    def archive(self, artifact_id: str) -> None:
        self.mark(artifact_id, ArtifactState.ARCHIVED)

    def delete(self, artifact_id: str) -> None:
        # tombstone 语义：内容立即不可读，元数据保留 DELETED_TOMBSTONE 记录。
        self.mark(artifact_id, ArtifactState.DELETED_TOMBSTONE)
        self._content.pop(artifact_id, None)
