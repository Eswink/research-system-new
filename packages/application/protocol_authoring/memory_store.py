"""InMemory ProtocolDraftStore：测试用实现（同 Port 契约）。

并发保护通过单线程假设 + revision 校验实现；SQLite/PostgreSQL 实现
由事务保证。修订 append-only；重复 idempotency_key 重放最近结果。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from packages.application.ports.protocol_draft_store import (
    DraftQuery,
    DraftSaveResult,
    DraftStoreConflictError,
    ProtocolDraftRecord,
    ProtocolDraftRevision,
)


def digest_of_text(text: str) -> str:
    """原文摘要（sha256；草稿摘要与协议语义摘要分开，语义摘要由校验层给出）。"""
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class _DraftState:
    project_id: str
    name: str
    created_at: str
    revisions: list[ProtocolDraftRevision] = field(default_factory=list)


class InMemoryProtocolDraftStore:
    """内存实现：契约测试与单元测试使用；语义与 SQLite/PG 实现一致。"""

    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._drafts: dict[str, _DraftState] = {}
        self._idempotency: dict[str, DraftSaveResult] = {}
        self._counter = 0
        self._clock = clock

    # ── Port 面 ──
    def create(
        self,
        project_id: str,
        name: str,
        yaml_text: str,
        source_digest: str | None,
        idempotency_key: str,
    ) -> ProtocolDraftRecord:
        replay = self._idempotency.get(idempotency_key)
        if replay is not None:
            return replay.record
        self._counter += 1
        draft_id = f"pdraft_{self._counter:08d}"
        now = self._now_iso()
        revision = ProtocolDraftRevision(
            draft_id=draft_id,
            revision=1,
            yaml_text=yaml_text,
            source_digest=source_digest if source_digest else digest_of_text(yaml_text),
            created_at=now,
        )
        self._drafts[draft_id] = _DraftState(
            project_id=project_id, name=name, created_at=now, revisions=[revision]
        )
        record = self._record(draft_id, self._drafts[draft_id])
        self._idempotency[idempotency_key] = DraftSaveResult(record=record, replayed=False)
        return record

    def get(self, draft_id: str) -> ProtocolDraftRecord | None:
        state = self._drafts.get(draft_id)
        return None if state is None else self._record(draft_id, state)

    def list(self, query: DraftQuery) -> tuple[ProtocolDraftRecord, ...]:
        matched = sorted(
            (
                (draft_id, state)
                for draft_id, state in self._drafts.items()
                if state.project_id == query.project_id
            ),
            key=lambda item: (item[1].created_at, item[0]),
            reverse=True,
        )
        window = matched[query.offset : query.offset + query.limit]
        return tuple(self._record(draft_id, state) for draft_id, state in window)

    def save(
        self,
        draft_id: str,
        *,
        yaml_text: str,
        source_digest: str | None,
        expected_revision: int,
        idempotency_key: str,
    ) -> DraftSaveResult:
        replay = self._idempotency.get(idempotency_key)
        state = self._drafts.get(draft_id)
        if state is None:
            raise KeyError(draft_id)
        current = state.revisions[-1].revision
        if replay is not None and replay.record.revision == current:
            return DraftSaveResult(record=replay.record, replayed=True)
        if expected_revision != current:
            raise DraftStoreConflictError(expected_revision, current)
        revision = ProtocolDraftRevision(
            draft_id=draft_id,
            revision=current + 1,
            yaml_text=yaml_text,
            source_digest=source_digest if source_digest else digest_of_text(yaml_text),
            created_at=self._now_iso(),
        )
        state.revisions.append(revision)
        record = self._record(draft_id, state)
        result = DraftSaveResult(record=record, replayed=False)
        self._idempotency[idempotency_key] = result
        return result

    def list_revisions(self, draft_id: str) -> tuple[ProtocolDraftRevision, ...]:
        state = self._drafts.get(draft_id)
        if state is None:
            raise KeyError(draft_id)
        return tuple(state.revisions)

    def get_revision(self, draft_id: str, revision: int) -> ProtocolDraftRevision | None:
        state = self._drafts.get(draft_id)
        if state is None:
            return None
        return next((r for r in state.revisions if r.revision == revision), None)

    def delete(self, draft_id: str) -> bool:
        removed = self._drafts.pop(draft_id, None) is not None
        self._idempotency = {
            key: result
            for key, result in self._idempotency.items()
            if result.record.draft_id != draft_id
        }
        return removed

    # ── 内部 ──
    def _now_iso(self) -> str:
        value = datetime.now(timezone.utc) if self._clock is None else self._clock()
        return value.isoformat().replace("+00:00", "Z")

    def _record(self, draft_id: str, state: _DraftState) -> ProtocolDraftRecord:
        latest = state.revisions[-1]
        return ProtocolDraftRecord(
            draft_id=draft_id,
            project_id=state.project_id,
            name=state.name,
            revision=latest.revision,
            yaml_text=latest.yaml_text,
            source_digest=latest.source_digest,
            created_at=state.created_at,
            updated_at=latest.created_at,
        )
