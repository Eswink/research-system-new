"""ArtifactStore / WorkspaceBackend / ExecutionBackend / MemoryStore 语义契约测试。

覆盖：digest 校验、状态流转合法性、lease 过期/续期、timeout/失败分类、
provenance gate。
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from adapters.fakes import (
    FakeArtifactStore,
    FakeExecutionBackend,
    FakeMemoryStore,
    FakeWorkspaceBackend,
)
from packages.application.ports.errors import InvalidInputError
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from packages.domain.enums import ArtifactState, FailureCategory
from packages.domain.workspace import ExecutionStatus
from tests.contracts.fixtures import (
    execution_spec,
    memory_proposal,
    workspace,
)


class TestArtifactStoreSemantics:
    def test_put_verifies_digest(self) -> None:
        store = FakeArtifactStore()
        content = b"data"
        artifact = Artifact(
            id="a-1",
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/octet-stream",
        )
        store.put(artifact, content)
        assert store.verify("a-1") is True

    def test_put_rejects_corrupted_content(self) -> None:
        store = FakeArtifactStore()
        artifact = Artifact(
            id="a-1",
            digest=Digest.of_bytes(b"expected"),
            size_bytes=4,
            media_type="application/octet-stream",
        )
        with pytest.raises(InvalidInputError):
            store.put(artifact, b"tampered")

    def test_state_transitions_are_legal(self) -> None:
        store = FakeArtifactStore()
        content = b"data"
        artifact = Artifact(
            id="a-1",
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/octet-stream",
            state=ArtifactState.STAGED,
        )
        store.put(artifact, content)
        store.mark("a-1", ArtifactState.VERIFIED)
        store.mark("a-1", ArtifactState.ACTIVE)
        store.archive("a-1")
        assert store.list_refs()[0].state is ArtifactState.ARCHIVED

    def test_illegal_transition_rejected(self) -> None:
        store = FakeArtifactStore()
        content = b"data"
        artifact = Artifact(
            id="a-1",
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/octet-stream",
            state=ArtifactState.STAGED,
        )
        store.put(artifact, content)
        with pytest.raises(InvalidInputError):
            store.mark("a-1", ArtifactState.ARCHIVED)


class TestWorkspaceBackendSemantics:
    def test_lease_required_for_snapshot(self) -> None:
        backend = FakeWorkspaceBackend()
        backend.create_workspace(workspace())
        lease = backend.acquire_lease(workspace(), "session-1")
        snapshot = backend.snapshot(lease)
        backend.restore(lease, snapshot)
        backend.merge(lease, snapshot)

    def test_lease_expiry_rejects_operations(self) -> None:
        start = datetime(2026, 8, 12, 10, 0, 0, tzinfo=timezone.utc)
        clock = {"now": start}

        def now() -> datetime:
            return clock["now"]

        backend = FakeWorkspaceBackend(lease_ttl_seconds=60, now=now)
        backend.create_workspace(workspace())
        lease = backend.acquire_lease(workspace(), "session-1")
        clock["now"] = start + timedelta(seconds=61)
        with pytest.raises(InvalidInputError):
            backend.snapshot(lease)

    def test_renew_extends_expiry(self) -> None:
        start = datetime(2026, 8, 12, 10, 0, 0, tzinfo=timezone.utc)
        clock = {"now": start}

        def now() -> datetime:
            return clock["now"]

        backend = FakeWorkspaceBackend(lease_ttl_seconds=60, now=now)
        backend.create_workspace(workspace())
        lease = backend.acquire_lease(workspace(), "session-1")
        clock["now"] = start + timedelta(seconds=30)
        renewed = backend.renew_lease(lease)
        clock["now"] = start + timedelta(seconds=90)
        assert renewed.expires_at is not None and renewed.expires_at.value >= clock["now"]


class TestExecutionBackendSemantics:
    def test_timeout_produces_timed_out_status(self) -> None:
        backend = FakeExecutionBackend(duration_seconds=30)
        run = backend.execute(execution_spec(), timeout_seconds=10)
        assert run.status is ExecutionStatus.TIMED_OUT

    def test_failed_run_carries_category(self) -> None:
        backend = FakeExecutionBackend(
            status=ExecutionStatus.FAILED,
            failure_category=FailureCategory.EXECUTION_FAILURE,
        )
        run = backend.execute(execution_spec())
        assert run.status is ExecutionStatus.FAILED
        assert run.failure_category is FailureCategory.EXECUTION_FAILURE

    def test_failed_run_defaults_category(self) -> None:
        backend = FakeExecutionBackend(status=ExecutionStatus.FAILED)
        run = backend.execute(execution_spec())
        assert run.failure_category is FailureCategory.EXECUTION_FAILURE


class TestMemoryStoreSemantics:
    def test_provenance_gate_rejects_unknown_source(self) -> None:
        store = FakeMemoryStore(allowed_sources=("source:article-1",))
        unknown = replace(memory_proposal("mem-1"), provenance="source:untrusted")
        with pytest.raises(InvalidInputError):
            store.commit(unknown)

    def test_provenance_gate_allows_known_source(self) -> None:
        store = FakeMemoryStore(allowed_sources=("source:article-1",))
        record = store.commit(memory_proposal("mem-1"))
        assert record.id == "mem-1"
        assert record.provenance == "source:article-1"

    def test_empty_allowlist_denies_commit(self) -> None:
        """deny-by-default 契约：无参构造不得放行任何 provenance。"""
        store = FakeMemoryStore()
        with pytest.raises(InvalidInputError, match="deny by default"):
            store.commit(memory_proposal("mem-1"))

    def test_duplicate_commit_rejected(self) -> None:
        """同 id 重复 commit 拒绝且原记录不变（防静默覆盖）。"""
        store = FakeMemoryStore(allowed_sources=("source:article-1",))
        store.commit(memory_proposal("mem-1"))
        with pytest.raises(InvalidInputError, match="already committed"):
            store.commit(memory_proposal("mem-1"))
        assert store.get("mem-1").content == memory_proposal("mem-1").content
