"""Probe suite 定义与请求构造。

suite 规格见 docs/integration/MODEL_PROBE.md；probe_suite_digest 用
canonical serialization 对定义计算。本模块只负责规格，不发起请求。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.model_relay.ports import CompletionRequest
from packages.domain.enums import CapabilitySource, ModelCapability
from packages.domain.models import ProbeSuiteSpec

CHAT_FIXTURE = "Reply with the single word: pong"
STRUCTURED_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {"pong": {"type": "string"}},
    "required": ["pong"],
}


def default_probe_suite(include_vision: bool = False) -> ProbeSuiteSpec:
    """默认 probe suite 定义（docs/integration/MODEL_PROBE.md）。"""
    return ProbeSuiteSpec(
        version="probe-suite-v1",
        steps=(
            "connectivity",
            "authentication",
            "chat",
            "streaming",
            "tool_calling",
            "structured_output",
            "usage",
        ),
        fixture_message=CHAT_FIXTURE,
        structured_schema=STRUCTURED_SCHEMA,
        include_vision=include_vision,
    )


def basic_request(
    model_name: str,
    *,
    with_tools: bool,
    with_structured: bool,
    stream: bool,
) -> CompletionRequest:
    """构造 probe 请求：固定消息 + 可选 tools / response_format / stream。"""
    messages: list[dict[str, object]] = [{"role": "user", "content": CHAT_FIXTURE}]
    tools: list[dict[str, object]] | None = None
    if with_tools:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "pong",
                    "description": "Always return pong",
                    "parameters": {"type": "object", "properties": {"value": {"type": "string"}}},
                },
            }
        ]
    response_format: dict[str, object] | None = None
    if with_structured:
        response_format = {
            "type": "json_schema",
            "json_schema": {"name": "pong", "schema": STRUCTURED_SCHEMA},
        }
    return CompletionRequest(
        model=model_name,
        messages=messages,
        tools=tools,
        response_format=response_format,
        stream=stream,
    )


@dataclass(frozen=True, slots=True)
class DiscoveredModels:
    """/models 发现的候选模型（DISCOVERED 来源，默认不启用）。"""

    model_ids: tuple[str, ...]
    source: CapabilitySource = CapabilitySource.DISCOVERED

    def __post_init__(self) -> None:
        if self.source is not CapabilitySource.DISCOVERED:
            raise ValueError("discovered models must use DISCOVERED source")


def extended_capability_steps(
    model_name: str,
) -> tuple[tuple[ModelCapability, CompletionRequest], ...]:
    """非致命能力 probe 步骤：streaming / tool calling / structured output。"""
    return (
        (
            ModelCapability.STREAMING,
            basic_request(model_name, with_tools=False, with_structured=False, stream=True),
        ),
        (
            ModelCapability.TOOL_CALLING_NATIVE,
            basic_request(model_name, with_tools=True, with_structured=False, stream=False),
        ),
        (
            ModelCapability.STRUCTURED_OUTPUT_NATIVE,
            basic_request(model_name, with_tools=False, with_structured=True, stream=False),
        ),
    )
