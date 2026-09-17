"""M5 domain 增量类型不变量与确定性序列化测试。

覆盖：ToolResultRecord、ExecutionRun、EventType/EventEnvelope
（docs/architecture/EVENT_MODEL.md §1/§2、docs/architecture/DOMAIN_MODEL.md §7）。
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from packages.domain.core import Digest, Timestamp
from packages.domain.enums import FailureCategory, ToolResultStatus
from packages.domain.events import (
    EventEnvelope,
    EventType,
    digest_of_payload,
    event_payload_digest_roundtrip,
)
from packages.domain.serialization import digest_of
from packages.domain.tools import ToolResultRecord
from packages.domain.workspace import (
    ExecutionRun,
    ExecutionSpec,
    ExecutionStatus,
)

DOCUMENTED_EVENT_TYPES = {
    "protocol.compiled",
    "preflight.completed",
    "manifest.frozen",
    "team.resolved",
    "role.activated",
    "model.probed",
    "model.resolved",
    "model.drift_detected",
    "budget.reserved",
    "task.created",
    "task.leased",
    "task.heartbeat",
    "task.retry_scheduled",
    "task.completed",
    "task.failed",
    "task.cancelled",
    "handoff.created",
    "approval.requested",
    "approval.decided",
    "memory.proposed",
    "memory.committed",
    "tool_pack.installed",
    "tool_pack.updated",
    "tool_pack.revoked",
    "tool_call.started",
    "tool_call.completed",
    "workspace.snapshot.created",
    "artifact.verified",
    "claim.verified",
    "claim.disputed",
    "memory.deleted",
    "run.forked",
    "run.completed",
    "run.cancelled",
    "run.failed",
    "run.degraded",
}


def _utc(dt: datetime) -> Timestamp:
    return Timestamp(dt)


NOW = datetime(2026, 8, 12, 10, 0, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 8, 12, 10, 5, 0, tzinfo=timezone.utc)


class TestToolResultRecord:
    def test_success_record_allows_missing_output(self) -> None:
        record = ToolResultRecord(
            task_id="task-1",
            attempt=1,
            operation_key="op-1",
            tool_id="tool-a",
            status=ToolResultStatus.SUCCEEDED,
        )
        assert record.status is ToolResultStatus.SUCCEEDED
        assert record.failure_category is None

    def test_requires_task_and_operation_keys(self) -> None:
        with pytest.raises(ValueError):
            ToolResultRecord(
                task_id="",
                attempt=1,
                operation_key="op-1",
                tool_id="tool-a",
                status=ToolResultStatus.SUCCEEDED,
            )
        with pytest.raises(ValueError):
            ToolResultRecord(
                task_id="task-1",
                attempt=1,
                operation_key="",
                tool_id="tool-a",
                status=ToolResultStatus.SUCCEEDED,
            )

    def test_failure_requires_redacted_message(self) -> None:
        with pytest.raises(ValueError):
            ToolResultRecord(
                task_id="task-1",
                attempt=1,
                operation_key="op-1",
                tool_id="tool-a",
                status=ToolResultStatus.FAILED,
                failure_category=FailureCategory.TOOL_UNAVAILABLE,
            )

    def test_success_record_carries_output_digest(self) -> None:
        digest = Digest.of_bytes(b"result")
        record = ToolResultRecord(
            task_id="task-1",
            attempt=1,
            operation_key="op-1",
            tool_id="tool-a",
            status=ToolResultStatus.SUCCEEDED,
            output_digest=digest,
        )
        assert record.output_digest == digest


class TestExecutionRun:
    def test_success_requires_completed_at(self) -> None:
        spec = ExecutionSpec(backend_kind="sandbox", command="run")
        with pytest.raises(ValueError):
            ExecutionRun(
                run_id="run-1",
                spec=spec,
                status=ExecutionStatus.SUCCEEDED,
                started_at=_utc(NOW),
            )

    def test_failure_requires_category(self) -> None:
        spec = ExecutionSpec(backend_kind="sandbox", command="run")
        with pytest.raises(ValueError):
            ExecutionRun(
                run_id="run-1",
                spec=spec,
                status=ExecutionStatus.FAILED,
                started_at=_utc(NOW),
                completed_at=_utc(LATER),
            )

    def test_rejects_negative_exit_code(self) -> None:
        spec = ExecutionSpec(backend_kind="sandbox", command="run")
        with pytest.raises(ValueError):
            ExecutionRun(
                run_id="run-1",
                spec=spec,
                status=ExecutionStatus.FAILED,
                started_at=_utc(NOW),
                completed_at=_utc(LATER),
                exit_code=-1,
                failure_category=FailureCategory.EXECUTION_FAILURE,
            )

    def test_rejects_completed_before_started(self) -> None:
        spec = ExecutionSpec(backend_kind="sandbox", command="run")
        with pytest.raises(ValueError):
            ExecutionRun(
                run_id="run-1",
                spec=spec,
                status=ExecutionStatus.SUCCEEDED,
                started_at=_utc(LATER),
                completed_at=_utc(NOW),
            )

    def test_valid_success_run(self) -> None:
        spec = ExecutionSpec(backend_kind="sandbox", command="run")
        run = ExecutionRun(
            run_id="run-1",
            spec=spec,
            status=ExecutionStatus.SUCCEEDED,
            started_at=_utc(NOW),
            completed_at=_utc(LATER),
            exit_code=0,
        )
        assert run.spec == spec
        assert run.exit_code == 0


class TestEventEnvelope:
    def _payload(self) -> dict[str, object]:
        return {"phase": "collect", "count": 3}

    def test_valid_envelope_with_matching_digest(self) -> None:
        payload = self._payload()
        envelope = EventEnvelope(
            event_id="evt-1",
            event_type=EventType.TASK_CREATED,
            schema_version="1",
            occurred_at=_utc(NOW),
            actor="project:demo",
            scope="run:r1",
            payload=payload,
            payload_digest=digest_of_payload(payload),
        )
        assert envelope.event_type is EventType.TASK_CREATED

    def test_rejects_mismatched_digest(self) -> None:
        payload = self._payload()
        wrong = digest_of({"phase": "other"})
        with pytest.raises(ValueError, match="payload_digest does not match"):
            EventEnvelope(
                event_id="evt-1",
                event_type=EventType.TASK_CREATED,
                schema_version="1",
                occurred_at=_utc(NOW),
                actor="project:demo",
                scope="run:r1",
                payload=payload,
                payload_digest=wrong,
            )

    def test_requires_envelope_fields(self) -> None:
        payload = self._payload()
        digest = digest_of_payload(payload)
        with pytest.raises(ValueError):
            EventEnvelope(
                event_id="",
                event_type=EventType.TASK_CREATED,
                schema_version="1",
                occurred_at=_utc(NOW),
                actor="project:demo",
                scope="run:r1",
                payload=payload,
                payload_digest=digest,
            )
        with pytest.raises(ValueError):
            EventEnvelope(
                event_id="evt-1",
                event_type=EventType.TASK_CREATED,
                schema_version="",
                occurred_at=_utc(NOW),
                actor="project:demo",
                scope="run:r1",
                payload=payload,
                payload_digest=digest,
            )

    def test_payload_digest_is_deterministic(self) -> None:
        assert digest_of_payload({"a": 1, "b": [2, 3]}) == digest_of_payload({"b": [2, 3], "a": 1})
        assert event_payload_digest_roundtrip({"a": 1}) == b'{"a":1}'


class TestEventTypeInventory:
    def test_covers_documented_event_types(self) -> None:
        actual = {event.value for event in EventType}
        assert actual == DOCUMENTED_EVENT_TYPES
        # 34 → 36（GOAL-004 cycle 3 新增 run.degraded / task.failed 两个**已写进
        # EVENT_MODEL.md 词表**的事件类型；门禁本身不变，只是随词表同步）。
        assert len(actual) == 36
