"""LLM Relay + Usage 归一化测试。

覆盖：三要素构造、endpoint 配置映射（timeout/retries）、secret 密封
（repr/序列化不泄漏）、usage → UsageLedgerEntry 归一化与幂等 entry_id。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from openhands.sdk.conversation.conversation_stats import ConversationStats
from openhands.sdk.llm.utils.metrics import Metrics, ResponseLatency, TokenUsage

from adapters.openhands.llm_factory import build_llm, resolve_runtime_model_name
from adapters.openhands.usage_mapping import UsageContext, usage_entries_from_stats
from packages.application.ports.credential_resolver import SecretValue
from packages.domain.budget import LedgerCostStatus, ResourceType
from packages.domain.models import LLMEndpoint, ModelDefinition


def _endpoint() -> LLMEndpoint:
    return LLMEndpoint(
        id="relay-1",
        name="test relay",
        protocol="OPENAI_COMPATIBLE",
        base_url="https://relay.example.test/v1",
        credential_ref="TEST_RELAY_KEY",
        request_timeout_seconds=42,
        max_retries=2,
    )


def _model() -> ModelDefinition:
    return ModelDefinition(id="m-1", endpoint_id="relay-1", model_name="relay-model-x")


def _metrics(prompt: int, completion: int, requests: int, cost: float) -> Metrics:
    metrics = Metrics(model_name="relay-model-x")
    metrics.accumulated_token_usage = TokenUsage(
        model="relay-model-x",
        prompt_tokens=prompt,
        completion_tokens=completion,
    )
    metrics.accumulated_cost = cost
    metrics.response_latencies = [
        ResponseLatency(model="relay-model-x", latency=0.5, response_id=f"r{i}")
        for i in range(requests)
    ]
    return metrics


class TestBuildLLM:
    def test_three_element_construction(self) -> None:
        llm = build_llm(
            _endpoint(),
            _model(),
            SecretValue("sk-test-secret-123"),
            max_output_tokens=4096,
        )
        # 非知名 model + 自定义 base_url → openai/ 前缀变换（OPENAI_COMPATIBLE 路由）
        assert llm.model == "openai/relay-model-x"
        assert llm.base_url == "https://relay.example.test/v1"
        assert llm.timeout == 42
        assert llm.num_retries == 2
        assert llm.max_output_tokens == 4096

    def test_known_provider_model_passthrough(self) -> None:
        assert resolve_runtime_model_name("openai/gpt-5.5", "https://relay.example.test/v1") == (
            "openai/gpt-5.5"
        )

    def test_api_key_never_leaks_in_repr_or_dump(self) -> None:
        llm = build_llm(_endpoint(), _model(), SecretValue("sk-super-secret-999"))
        assert "sk-super-secret-999" not in repr(llm)
        dumped = llm.model_dump_json()
        assert "sk-super-secret-999" not in dumped
        assert "sk-super-secret-999" not in str(llm.model_dump())
        json.loads(dumped)  # 可序列化


def _usage_context(now: datetime | None = None) -> UsageContext:
    return UsageContext(source="openhands", task_id="t-1", agent_id="a-1", model_id="m-1", now=now)


class TestUsageMapping:
    def test_entries_normalize_tokens_requests_cost(self) -> None:
        stats = ConversationStats(
            usage_to_metrics={"u-1": _metrics(prompt=100, completion=50, requests=3, cost=0.02)}
        )
        now = datetime(2026, 8, 13, tzinfo=timezone.utc)
        entries = usage_entries_from_stats(stats, _usage_context(now))
        by_resource = {entry.resource_type: entry for entry in entries}
        assert by_resource[ResourceType.MODEL_TOKENS].quantity == 150
        assert by_resource[ResourceType.MODEL_TOKENS].unit == "tokens"
        assert by_resource[ResourceType.MODEL_REQUESTS].quantity == 3
        assert by_resource[ResourceType.MODEL_COST].estimated_cost_minor == 2
        # token/request 条目在映射期不套价（UNKNOWN）；中转站上报的真实金额
        # 走 MODEL_COST 条目，携带 KNOWN 状态（M15 WP3c 维度映射修正）。
        assert by_resource[ResourceType.MODEL_TOKENS].cost_status is LedgerCostStatus.UNKNOWN
        assert by_resource[ResourceType.MODEL_REQUESTS].cost_status is LedgerCostStatus.UNKNOWN
        assert by_resource[ResourceType.MODEL_COST].cost_status is LedgerCostStatus.KNOWN
        assert all(entry.source == "openhands" for entry in entries)

    def test_zero_usage_produces_no_entries(self) -> None:
        stats = ConversationStats(
            usage_to_metrics={"u-0": _metrics(prompt=0, completion=0, requests=0, cost=0)}
        )
        entries = usage_entries_from_stats(stats, _usage_context())
        assert entries == ()

    def test_entry_ids_are_idempotent(self) -> None:
        stats = ConversationStats(
            usage_to_metrics={"u-2": _metrics(prompt=10, completion=0, requests=1, cost=0)}
        )
        first = usage_entries_from_stats(stats, _usage_context())
        second = usage_entries_from_stats(stats, _usage_context())
        assert {entry.entry_id for entry in first} == {entry.entry_id for entry in second}
