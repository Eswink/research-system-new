"""OpenAIChatGateway 离线测试共享工具（httpx.MockTransport，无真实网络）。"""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx

from adapters.relay.gateway import OpenAIChatGateway
from packages.application.ports import SecretValue
from packages.domain.models import LLMEndpoint

ENDPOINT = LLMEndpoint(
    id="main",
    name="Main Relay",
    protocol="OPENAI_COMPATIBLE",
    base_url="https://relay.example.com/api/v1",
    credential_ref="llm_main_key",
    max_retries=0,
)

RESPONSES_ENDPOINT = LLMEndpoint(
    id="main",
    name="Main Relay",
    protocol="OPENAI_COMPATIBLE",
    base_url="https://relay.example.com/api/v1",
    credential_ref="llm_main_key",
    max_retries=0,
    api_style="responses",
)

RETRY_ENDPOINT = LLMEndpoint(
    id="main",
    name="Main Relay",
    protocol="OPENAI_COMPATIBLE",
    base_url="https://relay.example.com/api/v1",
    credential_ref="llm_main_key",
    max_retries=2,
)

CREDENTIAL = SecretValue("sk-test-token-123456")


def json_response(
    payload: dict[str, object], status: int = 200, headers: dict[str, str] | None = None
) -> httpx.Response:
    return httpx.Response(status, json=payload, headers=headers or {})


def sse_response(
    chunks: list[dict[str, object]], headers: dict[str, str] | None = None
) -> httpx.Response:
    body = "".join(f"data: {json.dumps(chunk)}\n\n" for chunk in chunks) + "data: [DONE]\n\n"
    return httpx.Response(200, text=body, headers=headers or {})


def gateway(handler: Callable[[httpx.Request], httpx.Response]) -> OpenAIChatGateway:
    return OpenAIChatGateway(transport=httpx.MockTransport(handler))
