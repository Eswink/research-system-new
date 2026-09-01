"""ArtifactStore Port：Artifact 内容寻址持久化（storage/ARTIFACT_STORE.md）。

职责：put/get/verify/list/mark/archive/delete；digest 校验（内容寻址）；
状态流转 STAGED→VERIFIED/QUARANTINED→ACTIVE（合法迁移由实现强制）。
非职责：不承担 Evidence/Claim truth（DATA_LIFECYCLE.md 事实源划分：
PostgreSQL 实体为真相，对象存储只保存内容）；不做 retention 决策
（domain ArtifactRetentionPolicy 定义）。

M5 决策 D2：同步语义；put 时内容与声明 digest 不一致即失败。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.artifacts import Artifact
from packages.domain.enums import ArtifactState


@runtime_checkable
class ArtifactStore(Protocol):
    """内容寻址 Artifact 存储。"""

    def put(self, artifact: Artifact, content: bytes) -> None: ...

    def get(self, artifact_id: str) -> bytes: ...

    def meta(self, artifact_id: str) -> Artifact | None:
        """Read the Artifact record (digest/created_by/state) without the blob.

        Returns None for unknown ids. Server-side provenance checks (M16
        re-audit F-4) use this instead of trusting worker self-reports.
        """
        ...

    def verify(self, artifact_id: str) -> bool: ...

    def mark(self, artifact_id: str, state: ArtifactState) -> None: ...

    def list_refs(self) -> tuple[Artifact, ...]: ...

    def archive(self, artifact_id: str) -> None: ...

    def delete(self, artifact_id: str) -> None: ...

    def close(self) -> None: ...
