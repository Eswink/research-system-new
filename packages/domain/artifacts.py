"""Artifact 域实体定义（内容寻址 digest + verification + retention policy）。

来源：docs/architecture/DATA_LIFECYCLE.md、docs/storage/ARTIFACT_STORE.md。
sha256 内容寻址；本层只做 digest/verify，不做对象存储（M5/P1 Port）。

M9：retention_policy 从裸字符串升级为类型化 ArtifactRetentionPolicy
（KEEP_FOREVER / RETAIN_DAYS(n) / LEGAL_HOLD，对齐
examples/config/retention_policy.yaml）；Artifact 增加 created_at 供
retention 用例按时间判定。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.domain.core import Digest, Timestamp
from packages.domain.enums import ArtifactState

KEEP_FOREVER = "KEEP_FOREVER"
LEGAL_HOLD = "LEGAL_HOLD"
RETAIN_DAYS = "RETAIN_DAYS"

_RETAIN_DAYS_PREFIX = f"{RETAIN_DAYS}:"


@dataclass(frozen=True, slots=True)
class ArtifactRetentionPolicy:
    """类型化保留策略；kind ∈ {KEEP_FOREVER, RETAIN_DAYS, LEGAL_HOLD}。"""

    KEEP_FOREVER = "KEEP_FOREVER"
    LEGAL_HOLD = "LEGAL_HOLD"
    RETAIN_DAYS = "RETAIN_DAYS"

    kind: str
    days: int | None = None

    def __post_init__(self) -> None:
        if self.kind not in (self.KEEP_FOREVER, self.RETAIN_DAYS, self.LEGAL_HOLD):
            raise ValueError(f"unknown retention policy kind: {self.kind!r}")
        if self.kind is self.RETAIN_DAYS:
            if self.days is None or self.days < 0:
                raise ValueError("RETAIN_DAYS policy requires non-negative days")
        elif self.days is not None:
            raise ValueError(f"{self.kind} policy must not carry days")

    @classmethod
    def keep_forever(cls) -> ArtifactRetentionPolicy:
        return cls(kind=cls.KEEP_FOREVER)

    @classmethod
    def retain_days(cls, days: int) -> ArtifactRetentionPolicy:
        return cls(kind=cls.RETAIN_DAYS, days=days)

    @classmethod
    def legal_hold(cls) -> ArtifactRetentionPolicy:
        return cls(kind=cls.LEGAL_HOLD)

    @classmethod
    def parse(cls, text: str) -> ArtifactRetentionPolicy:
        if text == cls.KEEP_FOREVER:
            return cls.keep_forever()
        if text == cls.LEGAL_HOLD:
            return cls.legal_hold()
        if text.startswith(_RETAIN_DAYS_PREFIX):
            try:
                days = int(text[len(_RETAIN_DAYS_PREFIX) :])
            except ValueError:
                raise ValueError(f"invalid retention policy literal: {text!r}") from None
            return cls.retain_days(days)
        raise ValueError(f"invalid retention policy literal: {text!r}")

    def to_str(self) -> str:
        if self.kind is self.RETAIN_DAYS:
            return f"{RETAIN_DAYS}:{self.days}"
        return self.kind

    @property
    def is_indefinite(self) -> bool:
        """LEGAL_HOLD 与 KEEP_FOREVER 永不因时间被归档/删除。"""
        return self.kind in (KEEP_FOREVER, LEGAL_HOLD)


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
    retention_policy: ArtifactRetentionPolicy | None = None
    state: ArtifactState = ArtifactState.STAGED
    created_at: Timestamp | None = None

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
