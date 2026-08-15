"""Artifact retention use case（M9，显式触发）。

retention 决策在 application 层编排，ArtifactStore 只暴露原子原语
（archive/delete 已有）。本用例显式触发扫描：
- RETAIN_DAYS(n)：created_at 超过 n 天 → archive（ACTIVE → ARCHIVED）；
- QUARANTINED：超过 quarantine_days → delete（对齐 retention_policy.yaml
  quarantined_artifacts 14d）；
- KEEP_FOREVER / LEGAL_HOLD：永不因时间归档/删除；
- created_at 缺失（旧数据）→ 保守跳过，不误删。

定时调度属 M14（与 recover_expired_leases 同列），M9 只提供确定性函数。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from packages.application.ports.artifact_store import ArtifactStore
from packages.domain.artifacts import Artifact, ArtifactRetentionPolicy
from packages.domain.enums import ArtifactState


@dataclass(frozen=True, slots=True)
class RetentionReport:
    """一次 retention 扫描的结果（确定性、可测试）。"""

    archived: tuple[str, ...] = ()
    deleted: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()

    @property
    def total(self) -> int:
        return len(self.archived) + len(self.deleted) + len(self.skipped)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def apply_retention(
    store: ArtifactStore,
    *,
    now: datetime | None = None,
    quarantine_days: int = 14,
) -> RetentionReport:
    """扫描 ArtifactStore 并执行保留策略；返回逐 artifact 决策报告。"""
    current = now or _utc_now()
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    archived: list[str] = []
    deleted: list[str] = []
    skipped: list[str] = []
    for artifact in store.list_refs():
        if artifact.state is ArtifactState.DELETED_TOMBSTONE:
            skipped.append(artifact.id)
            continue
        if artifact.state is ArtifactState.QUARANTINED:
            action = _quarantine_action(artifact, current, quarantine_days)
        else:
            action = _policy_action(artifact, current)
        if action == "archive":
            store.archive(artifact.id)
            archived.append(artifact.id)
        elif action == "delete":
            store.delete(artifact.id)
            deleted.append(artifact.id)
        else:
            skipped.append(artifact.id)
    return RetentionReport(
        archived=tuple(archived), deleted=tuple(deleted), skipped=tuple(skipped)
    )


def _policy_action(artifact: Artifact, now: datetime) -> str:
    policy = artifact.retention_policy
    if policy is None or policy.is_indefinite or artifact.created_at is None:
        return "keep"
    assert policy.kind is ArtifactRetentionPolicy.RETAIN_DAYS and policy.days is not None
    if now - artifact.created_at.value > timedelta(days=policy.days):
        return "archive"
    return "keep"


def _quarantine_action(artifact: Artifact, now: datetime, quarantine_days: int) -> str:
    if artifact.created_at is None:
        return "keep"
    if now - artifact.created_at.value > timedelta(days=quarantine_days):
        return "delete"
    return "keep"