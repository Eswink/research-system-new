"""M7 E2E 幂等性验证（6 项）。

重复执行以下操作不得产生不可控副作用（AGENTS.md §7）：
1. task delivery（submit/acquire）→ 幂等去重；
2. artifact registration（put 同 id/digest）→ 稳定、不重复；
3. event publication（publish 同 event_id）→ outbox 单条；
4. usage recording（record_usage 同 entry_id）→ append-only 拒绝重复；
5. claim/evidence 创建 → VERIFIED 缺证据构造失败（防重复/防伪造）；
6. cancellation → 重复 cancel 幂等。
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from packages.application.ports.errors import InvalidInputError
from packages.application.run_orchestration import (
    CancelRunCommand,
    StartRunCommand,
)
from packages.domain.artifacts import Artifact
from packages.domain.budget import (
    LedgerCostStatus,
    ResourceType,
    UsageLedgerEntry,
)
from packages.domain.core import ID, Digest, Timestamp
from packages.domain.enums import ArtifactState
from packages.domain.events import EventEnvelope, EventType, digest_of_payload
from packages.domain.evidence import Claim, ClaimStatus
from packages.domain.run_state import ResearchRunState
from tests.contracts.fixtures import research_task, task_contract
from tests.e2e.scenario import M7Harness, StructuredOutputAgentRuntime, m7_protocol
from tests.e2e.scenario_catalog import (
    m7_catalog,
    m7_preflight_context,
    m7_project,
)


class TestTaskDeliveryIdempotency:
    def test_duplicate_submit_and_acquire_have_no_duplicate_side_effect(self) -> None:
        harness = M7Harness()
        try:
            task = research_task()
            harness.engine.submit(task, task_contract())
            harness.engine.submit(task, task_contract("hijacked"))
            harness.engine.acquire_lease(task.id.value)
            harness.engine.acquire_lease(task.id.value)
            assert harness.engine.deliveries[task.idempotency_key or ""] == 1
            assert len(harness.engine.list_tasks(task.run_id.value)) == 1
        finally:
            harness.close()


class TestArtifactRegistrationIdempotency:
    def test_put_same_artifact_twice_is_stable(self) -> None:
        harness = M7Harness()
        try:
            content = b"report"
            artifact = Artifact(
                id="a-1",
                digest=Digest.of_bytes(content),
                size_bytes=len(content),
                media_type="text/plain",
                state=ArtifactState.STAGED,
            )
            harness.artifacts.put(artifact, content)
            harness.artifacts.put(artifact, content)
            assert len(harness.artifacts.list_refs()) == 1
            assert harness.artifacts.verify("a-1") is True
        finally:
            harness.close()

    def test_same_content_different_id_registers_independently(self) -> None:
        harness = M7Harness()
        try:
            content = b"report"
            digest = Digest.of_bytes(content)
            for index in range(3):
                artifact = Artifact(
                    id=f"a-{index}",
                    digest=digest,
                    size_bytes=len(content),
                    media_type="text/plain",
                )
                harness.artifacts.put(artifact, content)
            assert len(harness.artifacts.list_refs()) == 3
        finally:
            harness.close()


class TestEventPublicationIdempotency:
    def test_duplicate_event_id_keeps_first_envelope(self) -> None:
        harness = M7Harness()
        try:
            payload: dict[str, object] = {"phase": "execution"}
            envelope = EventEnvelope(
                event_id="evt-dupe",
                event_type=EventType.TASK_CREATED,
                schema_version="1",
                occurred_at=Timestamp.now(),
                actor="system:test",
                scope="run:r1",
                payload=payload,
                payload_digest=digest_of_payload(payload),
            )
            harness.events.publish(envelope)
            harness.events.publish(replace(envelope, actor="system:hijacked", scope="run:evil"))
            published = harness.events.published
            assert len(published) == 1
            assert published[0].actor == "system:test"
        finally:
            harness.close()


class TestUsageRecordingIdempotency:
    def test_duplicate_entry_id_rejected(self) -> None:
        harness = M7Harness()
        try:
            entry = UsageLedgerEntry(
                entry_id="usage:dup",
                resource_type=ResourceType.AGENT_TURNS,
                quantity=1,
                unit="turns",
                cost_status=LedgerCostStatus.UNKNOWN,
                source="test",
                occurred_at=Timestamp.now().value,
            )
            harness.budget.record_usage(entry)
            with pytest.raises(InvalidInputError, match="duplicate"):
                harness.budget.record_usage(entry)
            assert len(harness.budget.snapshot().entries) == 1
        finally:
            harness.close()


class TestClaimEvidenceCreationGuard:
    def test_verified_claim_without_evidence_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="evidence"):
            Claim(
                id="claim:unsupported",
                statement="agent said it is done",
                status=ClaimStatus.VERIFIED,
            )

    def test_verified_claim_with_evidence_relation_constructs(self) -> None:
        from packages.domain.evidence import EvidenceRelationType

        claim = Claim(
            id="claim:supported",
            statement="result matches artifact",
            status=ClaimStatus.VERIFIED,
            evidence_relations=[("evidence:e1", EvidenceRelationType.SUPPORTS)],
        )
        assert claim.status is ClaimStatus.VERIFIED


class TestCancellationIdempotency:
    def test_double_cancel_is_idempotent_and_state_stable(self) -> None:
        harness = M7Harness()
        try:
            task = research_task()
            harness.engine.submit(task, task_contract())
            harness.engine.acquire_lease(task.id.value)
            command = CancelRunCommand(run_id=task.run_id, reason="stop")
            harness.service.cancel_run(command)
            harness.service.cancel_run(command)
            assert harness.engine.calls[-1].result_summary == "0 cancelled"
            assert task.id.value in harness.engine.cancelled
            rows = harness.engine.list_tasks(task.run_id.value)
            assert rows[0].task.status == "CANCELLED"
        finally:
            harness.close()


class TestFullRunIdempotency:
    def test_same_command_replay_fails_safely_without_duplicate_side_effects(self) -> None:
        """同一命令（run_id/idempotency_key）重放：第二次安全失败，不重复投递任务。"""
        runtime = StructuredOutputAgentRuntime(
            structured_output={
                "analysis_report": {"baseline": "O(n^2)"},
                "review_decision": {"verdict": "PASS"},
            }
        )
        harness = M7Harness(runtime=runtime)
        try:
            catalog = m7_catalog()
            project = m7_project()
            context = m7_preflight_context(catalog, project)
            command = StartRunCommand(
                project_id="m7-project",
                protocol_id="sort_analysis_v1",
                run_id=ID.generate(),
                trace_id="trace-replay",
                idempotency_key="run-replay-1",
            )
            first = harness.service.start_run(m7_protocol(), catalog, project, context, command)
            second = harness.service.start_run(m7_protocol(), catalog, project, context, command)
            assert first.state == ResearchRunState.State.SUCCEEDED
            # 重放：任务已存在（同 idempotency_key 去重）→ 安全失败而非崩溃
            assert second.state == ResearchRunState.State.FAILED
            # 不产生重复投递副作用：任务表只有首次执行的两条
            rows = harness.engine.list_tasks(command.run_id.value)
            assert len(rows) == 2
        finally:
            harness.close()
