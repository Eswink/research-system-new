"""Model relay probe use case 测试共享 fixture（端点/模型常量）。

常量自 M3 relay_fakes 迁移；行为 Fake（FakeModelGateway/FakeCredentialResolver）
统一使用 adapters.fakes，不再维护第二套手工实现。
"""

from __future__ import annotations

from packages.domain.models import LLMEndpoint, ModelDefinition

ENDPOINT = LLMEndpoint(
    id="main",
    name="Main Relay",
    protocol="OPENAI_COMPATIBLE",
    base_url="https://relay.example.com/api/v1",
    credential_ref="llm_main_key",
)

LOCALHOST_ENDPOINT = LLMEndpoint(
    id="local",
    name="Local Relay",
    protocol="OPENAI_COMPATIBLE",
    base_url="http://127.0.0.1:8080/v1",
    credential_ref="llm_main_key",
)

MODEL = ModelDefinition(id="model-alpha", endpoint_id="main", model_name="model-alpha")
