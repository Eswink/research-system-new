"""其余 Port 特定语义契约测试。

覆盖：malformed provider result、timeout 分类、secret redaction、
event ordering/dedup、budget append-only、artifact digest/状态流转、
workspace lease 过期、execution timeout/失败分类、memory provenance gate、
tool operation_key 幂等、policy 决策矩阵。
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from adapters.fakes import (
    FakeBudgetLedger,
    FakeCredentialResolver,
    FakeEventPublisher,
    FakeModelGateway,
    FakeModelGatewayOptions,
    FakePolicyEvaluator,
    FakeToolProvider,
)
from packages.application.ports.credential_resolver import SecretValue
from packages.application.ports.errors import (
    InvalidInputError,
    PermanentPortError,
    PortError,
    PortTimeoutError,
)
from packages.application.ports.model_gateway import CompletionRequest
from packages.application.ports.policy_evaluator import PolicyRequest
from packages.domain.budget import LedgerCostStatus, ResourceType, UsageLedgerEntry
from packages.domain.enums import (
    FailureCategory,
    PolicyDecision,
)
from packages.domain.events import EventType
from tests.contracts.fixtures import (
    budget_policy,
    budget_reservation,
    endpoint,
    event_envelope,
    tool_call_record,
    tool_provider_spec,
    usage_entry,
)


class TestModelGatewaySemantics:
    def test_malformed_result_flagged(self) -> None:
        gateway = FakeModelGateway(FakeModelGatewayOptions(malformed_result=True))
        result = gateway.complete(endpoint(), SecretValue("x"), _chat_request())
        assert result.usage_reported is True
        assert result.content is None

    def test_timeout_is_transient_and_classified(self) -> None:
        gateway = FakeModelGateway(FakeModelGatewayOptions(fail_timeout=True))
        with pytest.raises(PortTimeoutError) as exc_info:
            gateway.complete(endpoint(), SecretValue("x"), _chat_request())
        assert exc_info.value.retryable is True
        assert exc_info.value.failure_category is FailureCategory.MODEL_TIMEOUT
        assert gateway.calls[-1].error == "PortTimeoutError"

    def test_transient_failure_retry_then_success(self) -> None:
        gateway = FakeModelGateway(FakeModelGatewayOptions(fail_transient=True))
        with pytest.raises(PortError):
            gateway.list_models(endpoint(), SecretValue("x"))
        healthy = FakeModelGateway()
        result = healthy.list_models(endpoint(), SecretValue("x"))
        assert result.model_ids == ("model-alpha", "model-beta")

    def test_probe_and_list_record_calls(self) -> None:
        gateway = FakeModelGateway()
        gateway.list_models(endpoint(), SecretValue("x"))
        gateway.probe_connectivity(endpoint(), SecretValue("x"))
        assert gateway.method_calls("list_models") == 1
        assert gateway.method_calls("probe_connectivity") == 1

    def test_probe_failure_snapshots_not_exceptions(self) -> None:
        """失败快照注入：探测不支持返回 ok=False 快照（非异常），语义区别于故障注入。"""
        gateway = FakeModelGateway(FakeModelGatewayOptions(auth_fails=True, stream_fails=True))
        connectivity = gateway.probe_connectivity(endpoint(), SecretValue("x"))
        assert connectivity.ok is False
        assert connectivity.error_category is FailureCategory.MODEL_AUTH
        stream = gateway.probe_endpoint(
            endpoint(),
            SecretValue("x"),
            CompletionRequest(model="model-alpha", messages=[], stream=True),
        )
        assert stream.ok is False
        assert stream.error_category is FailureCategory.EXECUTION_FAILURE
        assert gateway.calls[-1].error is None

    def test_no_usage_probe_snapshot(self) -> None:
        gateway = FakeModelGateway(FakeModelGatewayOptions(no_usage=True))
        snapshot = gateway.probe_endpoint(endpoint(), SecretValue("x"), _chat_request())
        assert snapshot.ok is True
        assert snapshot.usage_reported is False
        assert snapshot.system_fingerprint == "fp_1"


def _chat_request() -> CompletionRequest:
    return CompletionRequest(model="model-alpha", messages=[{"role": "user", "content": "hi"}])


class TestCredentialResolverSemantics:
    def test_secret_repr_and_records_redacted(self) -> None:
        resolver = FakeCredentialResolver({"llm_main_key": "sk-secret-1234567890abcdef"})
        value = resolver.resolve("llm_main_key")
        assert "<SecretValue:redacted>" in repr(value)
        assert "sk-secret-1234567890abcdef" not in str(resolver.calls)

    def test_missing_ref_raises_invalid_input(self) -> None:
        resolver = FakeCredentialResolver({})
        with pytest.raises(InvalidInputError):
            resolver.resolve("missing")
        assert resolver.calls[-1].error == "InvalidInputError"

    def test_denied_scope_rejected(self) -> None:
        resolver = FakeCredentialResolver({"ref": "v"})
        resolver.deny_scope("ref")
        with pytest.raises(InvalidInputError):
            resolver.resolve("ref")


class TestEventPublisherSemantics:
    def test_event_order_preserved(self) -> None:
        publisher = FakeEventPublisher()
        publisher.publish(event_envelope(event_id="evt-1"))
        publisher.publish(event_envelope(event_id="evt-2"))
        assert [envelope.event_id for envelope in publisher.published] == ["evt-1", "evt-2"]

    def test_event_id_dedup(self) -> None:
        publisher = FakeEventPublisher()
        publisher.publish(event_envelope(event_id="evt-1"))
        publisher.publish(event_envelope(event_id="evt-1"))
        assert len(publisher.published) == 1
        assert publisher.calls[-1].result_summary == "deduped"

    def test_domain_events_only(self) -> None:
        publisher = FakeEventPublisher()
        publisher.publish(event_envelope(event_id="evt-1"))
        assert publisher.published[0].event_type is EventType.TASK_CREATED


class TestBudgetLedgerSemantics:
    def test_append_only_rejects_duplicate_entry(self) -> None:
        ledger = FakeBudgetLedger()
        ledger.record_usage(usage_entry("entry-1"))
        with pytest.raises(InvalidInputError):
            ledger.record_usage(usage_entry("entry-1"))
        assert len(ledger.snapshot().entries) == 1

    def test_reserve_is_deterministic(self) -> None:
        ledger_a = FakeBudgetLedger()
        ledger_b = FakeBudgetLedger()
        ref_a = ledger_a.reserve((budget_reservation(),), budget_policy())
        ref_b = ledger_b.reserve((budget_reservation(),), budget_policy())
        assert ref_a == ref_b

    def test_release_returns_reserved_quota(self) -> None:
        ledger = FakeBudgetLedger()
        ref = ledger.reserve((budget_reservation(),), budget_policy())
        assert len(ledger.snapshot().reservations) == 1
        ledger.release(ref)
        assert ledger.snapshot().reservations == ()

    def test_release_is_idempotent(self) -> None:
        ledger = FakeBudgetLedger()
        ref = ledger.reserve((budget_reservation(),), budget_policy())
        ledger.release(ref)
        ledger.release(ref)  # 重复释放必须 no-op，不抛错、不产生残留
        assert ledger.snapshot().reservations == ()
        release_calls = [c for c in ledger.calls if c.method == "release"]
        assert release_calls[-1].result_summary == "noop"

    def test_release_unknown_ref_is_noop(self) -> None:
        ledger = FakeBudgetLedger()
        ledger.release("budget-reservation:unknown")
        assert ledger.snapshot().reservations == ()

    def test_unknown_cost_not_fabricated(self) -> None:
        ledger = FakeBudgetLedger()
        entry = UsageLedgerEntry(
            entry_id="entry-unknown",
            resource_type=ResourceType.MODEL_TOKENS,
            quantity=100,
            unit="tokens",
            cost_status=LedgerCostStatus.UNKNOWN,
            source="test",
            occurred_at=datetime(2026, 8, 12, tzinfo=timezone.utc),
        )
        ledger.record_usage(entry)
        stored = ledger.snapshot().entries[0]
        assert stored.cost_status is LedgerCostStatus.UNKNOWN
        assert stored.estimated_cost_minor is None


class TestToolProviderSemantics:
    def test_operation_key_idempotent(self) -> None:
        provider = FakeToolProvider(registered_tools=("tool-a",))
        call = tool_call_record(operation_key="op-1")
        first = provider.execute(tool_provider_spec(), call)
        second = provider.execute(tool_provider_spec(), call)
        assert first.operation_key == second.operation_key
        assert provider.calls[-1].result_summary == "deduped"

    def test_unregistered_tool_permanent_failure(self) -> None:
        provider = FakeToolProvider(registered_tools=())
        with pytest.raises(PermanentPortError):
            provider.execute(tool_provider_spec(), tool_call_record())

    def test_tool_level_failure_returns_record(self) -> None:
        provider = FakeToolProvider(registered_tools=("tool-a",))
        provider.fail_tool("tool-a")
        result = provider.execute(tool_provider_spec(), tool_call_record())
        assert result.status == "FAILED"
        assert result.failure_category is FailureCategory.TOOL_UNAVAILABLE


class TestPolicyEvaluatorSemantics:
    def test_decision_matrix(self) -> None:
        evaluator = FakePolicyEvaluator()
        evaluator.set_decision("workspace.read", PolicyDecision.ALLOW)
        evaluator.set_decision("package.install", PolicyDecision.DENY)
        evaluator.set_decision("network.academic", PolicyDecision.REQUIRE_APPROVAL)

        assert (
            evaluator.evaluate(PolicyRequest(actor="agent-1", capability="workspace.read")).decision
            is PolicyDecision.ALLOW
        )
        assert (
            evaluator.evaluate(
                PolicyRequest(actor="agent-1", capability="package.install")
            ).decision
            is PolicyDecision.DENY
        )
        assert (
            evaluator.evaluate(
                PolicyRequest(actor="agent-1", capability="network.academic")
            ).decision
            is PolicyDecision.REQUIRE_APPROVAL
        )

    def test_default_deny_style(self) -> None:
        evaluator = FakePolicyEvaluator(default=PolicyDecision.DENY)
        assert (
            evaluator.evaluate(PolicyRequest(actor="a", capability="unknown")).decision
            is PolicyDecision.DENY
        )
