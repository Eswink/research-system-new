"""M12 usage 归账闭环：真实 relay 代码路径（M14 debt closure, WP-B）。

两层：
1. 离线（默认 CI）：httpx.MockTransport 脚本化 relay 响应驱动
   `OpenAIChatGateway.complete` → `collect_usage` → `FakeBudgetLedger`，
   证明"真实 relay 响应的 usage 明细 → BudgetLedger"完整代码路径可达。
2. 手动（`requires_live_llm`，默认 skip）：**显式开关 `RESEARCHOS_LIVE_E2E=1`**（D-11）
   + 真实 endpoint + 真实凭据 → probe → 一次最小模型调用 → 断言 ledger 出现真实
   usage entry。真实凭据只经环境变量 `RESEARCHOS_LIVE_E2E_ENDPOINT` /
   `RESEARCHOS_LIVE_E2E_KEY` 注入，永不硬编码、不落盘。

诚实标注：真实生产成功路径（wizard 注册凭据 + relay 可达 + 真实模型调用）
不是默认 CI 依赖；本测试证明代码路径完整，真实运行由操作者显式触发。
"""

from __future__ import annotations

import os

import httpx
import pytest

from adapters.fakes import FakeBudgetLedger
from adapters.relay.gateway import OpenAIChatGateway
from packages.application.experiments.usage_collection import (
    UsageCollection,
    record_collected_usage,
)
from packages.application.ports.credential_resolver import SecretValue
from packages.application.ports.model_gateway import CompletionRequest
from packages.domain.budget import ResourceType
from packages.domain.models import LLMEndpoint
from tests.contracts.fixtures import endpoint
from tests.e2e.live_switch_support import live_e2e_switch_enabled, live_run_switch_off_reason

pytestmark = pytest.mark.requires_live_llm


def _relay_json_response(usage: dict[str, int]) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "chatcmpl-e2e",
            "model": "relay-model",
            "system_fingerprint": "fp-e2e",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "pong"}}],
            "usage": usage,
        },
        headers={"x-request-id": "req-e2e"},
    )


def _request(model: str = "relay-model") -> CompletionRequest:
    return CompletionRequest(
        model=model,
        messages=[{"role": "user", "content": "ping"}],
    )


class TestOfflineRelayUsagePath:
    """httpx.MockTransport 脚本化 relay：gateway → usage → ledger 全链。"""

    def test_gateway_completion_usage_reaches_ledger(self) -> None:
        ledger = FakeBudgetLedger()

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers.get("authorization") == "Bearer sk-test-e2e-token"
            return _relay_json_response({
                "prompt_tokens": 12,
                "completion_tokens": 7,
                "total_tokens": 19,
            })

        gateway = OpenAIChatGateway(
            default_timeout_seconds=30,
            transport=httpx.MockTransport(handler),
        )
        result = gateway.complete(endpoint(), SecretValue("sk-test-e2e-token"), _request())

        assert result.usage_reported is True
        assert result.prompt_tokens == 12
        assert result.completion_tokens == 7
        assert result.total_tokens == 19

        # usage 归集 → BudgetLedger（M12 归账闭环路径）
        summary = record_collected_usage(
            ledger,
            UsageCollection(
                run_id="run-e2e",
                model_id="relay-model",
                model_completions=(result,),
                task_id="task-e2e",
            ),
        )
        assert summary.model_tokens == 19
        snapshot = ledger.snapshot()
        entries = [e for e in snapshot.entries if e.resource_type is ResourceType.MODEL_TOKENS]
        assert len(entries) == 1
        assert entries[0].quantity == 19

    def test_provider_without_usage_is_unknown_not_fake(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "id": "chatcmpl-2",
                    "model": "relay-model",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": "pong"}}],
                },
            )

        gateway = OpenAIChatGateway(
            default_timeout_seconds=30,
            transport=httpx.MockTransport(handler),
        )
        result = gateway.complete(endpoint(), SecretValue("sk-test-e2e-token"), _request())
        assert result.usage_reported is False
        assert result.usage_unavailable_reason is not None


class TestLiveRelayUsageE2E:
    """真实 relay 路径（requires_live_llm，默认 skip）。"""

    def test_live_completion_records_usage(self) -> None:
        if not live_e2e_switch_enabled():
            pytest.skip(live_run_switch_off_reason())
        endpoint_url = os.environ.get("RESEARCHOS_LIVE_E2E_ENDPOINT")
        api_key = os.environ.get("RESEARCHOS_LIVE_E2E_KEY")
        if not endpoint_url or not api_key:
            pytest.skip(
                "live relay E2E requires RESEARCHOS_LIVE_E2E_ENDPOINT and "
                "RESEARCHOS_LIVE_E2E_KEY env vars"
            )
        ledger = FakeBudgetLedger()
        gateway = OpenAIChatGateway(default_timeout_seconds=60)
        endpoint = LLMEndpoint(
            id="live-e2e",
            name="Live E2E Relay",
            protocol="OPENAI_COMPATIBLE",
            base_url=endpoint_url,
            credential_ref="RESEARCHOS_LIVE_E2E_KEY",
        )
        result = gateway.complete(endpoint, SecretValue(api_key), _request("agnes-2.5-flash"))
        assert result.content, "live relay must return a completion"
        summary = record_collected_usage(
            ledger,
            UsageCollection(
                run_id="run-live",
                model_id="relay-model",
                model_completions=(result,),
                task_id="task-live",
            ),
        )
        # 诚实语义：provider 返回 usage 时 quantity > 0；未返回时如实 UNKNOWN
        # （collect_usage 对未报告 usage 记 0 且不伪造数字）。
        if result.usage_reported:
            assert summary.model_tokens > 0
            snapshot = ledger.snapshot()
            entries = [e for e in snapshot.entries if e.resource_type is ResourceType.MODEL_TOKENS]
            assert len(entries) == 1
            assert entries[0].quantity > 0
