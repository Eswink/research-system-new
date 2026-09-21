"""M10 E2E：gate PASS 后 Claim 升级为 VERIFIED 并发布 CLAIM_VERIFIED。

验证 EvidenceLedger 接入 M7 编排链：SourceRecord/Evidence/Claim 登记、
Claim 升级授权、事件审计，以及 ledger 未装配时的安全降级。
"""

from __future__ import annotations

from collections.abc import Generator

import pytest

from adapters.fakes import FakeEvidenceLedger
from packages.application.run_orchestration import RunOutcome, StartRunCommand
from packages.domain.core import ID
from packages.domain.events import EventType
from packages.domain.evidence import ClaimStatus
from tests.e2e.scenario import M7Harness, StructuredOutputAgentRuntime, m7_protocol
from tests.e2e.scenario_catalog import (
    m7_catalog,
    m7_preflight_context,
    m7_project,
)

#: 按合约区分的产出：`sort_analysis_v1` 的 review phase 声明要交 `review_decision`
#: （合约里的 `ARTIFACT_EXISTS`，GOAL-010 EC-02 补齐），所以 Fake 也得按合约产出——
#: 单一 `structured_output` 会让 review 拿不到自己的交付物，run 会如实判拒。
_HAPPY_OUTPUTS: dict[str, dict[str, object]] = {
    "sort_analysis_execution": {
        "analysis_report": {"baseline": "O(n^2)", "recommendation": "use TimSort"},
    },
    "sort_analysis_review": {
        "review_decision": {"verdict": "PASS", "score": 0.95},
    },
}


@pytest.fixture
def harness() -> Generator[M7Harness, None, None]:
    runtime = StructuredOutputAgentRuntime(outputs_by_contract=_HAPPY_OUTPUTS)
    instance = M7Harness(runtime=runtime, ledger=FakeEvidenceLedger())
    yield instance
    instance.close()


def _start(harness: M7Harness) -> RunOutcome:
    return harness.service.start_run(
        m7_protocol(),
        m7_catalog(),
        m7_project(),
        m7_preflight_context(m7_catalog(), m7_project()),
        StartRunCommand(
            project_id="m7-project",
            protocol_id="sort_analysis_v1",
            run_id=ID.generate(),
            trace_id="trace-claim-1",
            idempotency_key="run-claim-1",
        ),
    )


class TestClaimVerificationE2E:
    def test_gate_pass_promotes_claims_and_publishes_event(self, harness: M7Harness) -> None:
        outcome = _start(harness)
        assert outcome.state == "SUCCEEDED"
        assert harness.ledger is not None
        claims = harness.ledger.claims()
        assert claims, "ledger must hold registered claims"
        assert all(claim.status is ClaimStatus.VERIFIED for claim in claims)
        for claim in claims:
            assert claim.evidence_relations
            relations = harness.ledger.relations_for_claim(claim.id)
            assert len(relations) == len(claim.evidence_relations)
            for relation in relations:
                evidence = harness.ledger.get_evidence(relation.evidence_id)
                assert harness.ledger.has_source(evidence.source_ref)
        verified_events = [
            envelope
            for envelope in harness.events.published
            if envelope.event_type is EventType.CLAIM_VERIFIED
        ]
        assert len(verified_events) == len(claims)
        assert all(envelope.run_id == outcome.run_id for envelope in verified_events)
        assert all(envelope.task_id is not None for envelope in verified_events)

    def test_claim_event_payload_carries_audit_fields(self, harness: M7Harness) -> None:
        _start(harness)
        events = [
            envelope
            for envelope in harness.events.published
            if envelope.event_type is EventType.CLAIM_VERIFIED
        ]
        assert events
        payload = events[0].payload
        reviewer = payload["reviewer"]
        assert isinstance(reviewer, str) and reviewer.startswith("gate:")
        assert payload["claim_id"]
        assert payload["task_id"]


class TestClaimVerificationDegradation:
    def test_without_ledger_claims_stay_proposed(self) -> None:
        runtime = StructuredOutputAgentRuntime(outputs_by_contract=_HAPPY_OUTPUTS)
        harness = M7Harness(runtime=runtime)
        try:
            outcome = harness.service.start_run(
                m7_protocol(),
                m7_catalog(),
                m7_project(),
                m7_preflight_context(m7_catalog(), m7_project()),
                StartRunCommand(
                    project_id="m7-project",
                    protocol_id="sort_analysis_v1",
                    run_id=ID.generate(),
                    trace_id="trace-claim-2",
                    idempotency_key="run-claim-2",
                ),
            )
            assert outcome.state == "SUCCEEDED"
            events = [
                envelope
                for envelope in harness.events.published
                if envelope.event_type is EventType.CLAIM_VERIFIED
            ]
            assert not events, "no ledger means no claim promotion (safe degradation)"
        finally:
            harness.close()
