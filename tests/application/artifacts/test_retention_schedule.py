"""Retention scheduling tests (M14 DS-2).

Two layers:
- apply_retention robustness: a single artifact whose archive/delete raises
  InvalidInputError (concurrent state drift) is skipped, and the scan
  continues to later artifacts (no half-aborted pass);
- RetentionScheduler smoke: interval > 0 validation, run_once applies the
  policy through the ArtifactStore port, start/stop joins the thread.

Mirrors the lease-recovery scheduler test pattern (deterministic, no sleeps
on the periodic path — the loop is exercised via run_once directly).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from packages.application.artifacts.retention import RetentionReport, apply_retention
from packages.domain.artifacts import Artifact, ArtifactRetentionPolicy
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import ArtifactState
from services.api.scheduler import RetentionScheduler

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _artifact(
    artifact_id: str,
    content: bytes,
    *,
    policy: ArtifactRetentionPolicy | None,
    state: ArtifactState = ArtifactState.ACTIVE,
    created_at: Timestamp | None = None,
) -> Artifact:
    return Artifact(
        id=artifact_id,
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type="text/plain",
        retention_policy=policy,
        state=state,
        created_at=created_at,
    )


class _FlakyArchiveStore:
    """FakeArtifactStore-shaped stub: first archive raises, later ones succeed.

    Also exercises created_at missing on one artifact (conservative skip).
    """

    def __init__(self, artifacts: tuple[Artifact, ...]) -> None:
        self._artifacts = {a.id: a for a in artifacts}
        self.archive_calls: list[str] = []

    def put(self, artifact: Artifact, content: bytes) -> None:  # pragma: no cover
        raise NotImplementedError

    def get(self, artifact_id: str) -> bytes:  # pragma: no cover
        raise NotImplementedError

    def verify(self, artifact_id: str) -> bool:  # pragma: no cover
        raise NotImplementedError

    def meta(self, artifact_id: str) -> Artifact | None:
        return self._artifacts.get(artifact_id)

    def mark(self, artifact_id: str, state: ArtifactState) -> None:  # pragma: no cover
        raise NotImplementedError

    def close(self) -> None:  # pragma: no cover
        return None

    def list_refs(self) -> tuple[Artifact, ...]:
        return tuple(self._artifacts.values())

    def archive(self, artifact_id: str) -> None:
        from packages.application.ports.errors import InvalidInputError

        self.archive_calls.append(artifact_id)
        if artifact_id == "a-flaky":
            raise InvalidInputError(f"concurrent state drift on {artifact_id}")
        current = self._artifacts[artifact_id]
        self._artifacts[artifact_id] = Artifact(
            id=current.id,
            digest=current.digest,
            size_bytes=current.size_bytes,
            media_type=current.media_type,
            storage_uri=current.storage_uri,
            created_by=current.created_by,
            source_refs=list(current.source_refs),
            classification=current.classification,
            retention_policy=current.retention_policy,
            state=ArtifactState.ARCHIVED,
            created_at=current.created_at,
        )

    def delete(self, artifact_id: str) -> None:
        from packages.application.ports.errors import InvalidInputError

        if artifact_id == "a-dead":
            raise InvalidInputError(f"already tombstoned: {artifact_id}")
        raise AssertionError("delete not expected in this stub")


class TestApplyRetentionRobustness:
    def test_archive_failure_skips_and_scan_continues(self) -> None:
        flaky = _artifact(
            "a-flaky",
            b"1",
            policy=ArtifactRetentionPolicy.retain_days(30),
            created_at=Timestamp(_EPOCH - timedelta(days=31)),
        )
        healthy = _artifact(
            "a-ok",
            b"2",
            policy=ArtifactRetentionPolicy.retain_days(30),
            created_at=Timestamp(_EPOCH - timedelta(days=40)),
        )
        store = _FlakyArchiveStore((flaky, healthy))
        report = apply_retention(store, now=_EPOCH)
        assert "a-flaky" in report.skipped
        assert "a-flaky" not in report.archived
        assert report.archived == ("a-ok",)

    def test_missing_created_at_is_conservatively_skipped(self) -> None:
        legacy = _artifact("a-legacy", b"3", policy=ArtifactRetentionPolicy.retain_days(30))
        store = _FlakyArchiveStore((legacy,))
        report = apply_retention(store, now=_EPOCH)
        assert report.skipped == ("a-legacy",)
        assert report.archived == () and report.deleted == ()

    def test_delete_failure_skips_without_raising(self) -> None:
        dead = _artifact(
            "a-dead",
            b"4",
            policy=ArtifactRetentionPolicy.keep_forever(),
            state=ArtifactState.QUARANTINED,
            created_at=Timestamp(_EPOCH - timedelta(days=20)),
        )
        store = _FlakyArchiveStore((dead,))
        report = apply_retention(store, now=_EPOCH, quarantine_days=14)
        assert "a-dead" in report.skipped
        assert report.deleted == ()


class _RecordingStore:
    """Minimal ArtifactStore stub for scheduler smoke; run_once drives policy."""

    def __init__(self) -> None:
        self.archived: list[str] = []
        expired = _artifact(
            "sched-expired",
            b"x",
            policy=ArtifactRetentionPolicy.retain_days(7),
            created_at=Timestamp(datetime.now(timezone.utc) - timedelta(days=10)),
        )
        indefinite = _artifact(
            "sched-forever",
            b"y",
            policy=ArtifactRetentionPolicy.keep_forever(),
            created_at=Timestamp(datetime.now(timezone.utc) - timedelta(days=3650)),
        )
        self._artifacts: dict[str, Artifact] = {
            expired.id: expired,
            indefinite.id: indefinite,
        }

    def put(self, artifact: Artifact, content: bytes) -> None:  # pragma: no cover
        raise NotImplementedError

    def get(self, artifact_id: str) -> bytes:  # pragma: no cover
        raise NotImplementedError

    def verify(self, artifact_id: str) -> bool:  # pragma: no cover
        raise NotImplementedError

    def meta(self, artifact_id: str) -> Artifact | None:
        return self._artifacts.get(artifact_id)

    def mark(self, artifact_id: str, state: ArtifactState) -> None:  # pragma: no cover
        raise NotImplementedError

    def close(self) -> None:  # pragma: no cover
        return None

    def list_refs(self) -> tuple[Artifact, ...]:
        return tuple(self._artifacts.values())

    def archive(self, artifact_id: str) -> None:
        self.archived.append(artifact_id)

    def delete(self, artifact_id: str) -> None:
        raise AssertionError(f"unexpected delete: {artifact_id}")


class TestRetentionScheduler:
    def test_interval_must_be_positive(self) -> None:
        with pytest.raises(ValueError):
            RetentionScheduler(_RecordingStore(), interval_seconds=0)

    def test_run_once_applies_policy_and_records_report(self) -> None:
        store = _RecordingStore()
        scheduler = RetentionScheduler(store, interval_seconds=3600.0)
        report = scheduler.run_once()
        assert isinstance(report, RetentionReport)
        assert report.archived == ("sched-expired",)
        assert "sched-forever" in report.skipped
        assert scheduler.last_report is report

    def test_start_stop_roundtrip(self) -> None:
        scheduler = RetentionScheduler(_RecordingStore(), interval_seconds=3600.0)
        scheduler.start()
        assert scheduler._thread is not None  # noqa: SLF001 — smoke assert on wiring
        scheduler.stop()
        assert scheduler._thread is None  # noqa: SLF001
