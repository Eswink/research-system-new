"""LLM 装配：LLMEndpoint + SecretValue + ModelDefinition → OpenHands LLM。

三要素构造（S2 实证）：LLM(model=..., base_url=..., api_key=...)；
runtime model identifier transformation 只存在于本模块：
- 非知名 model + 自定义 base_url 时 litellm 无法推断 provider（R-08 实证），
  经 LLMProvider.from_model 探测失败后加 `openai/` 前缀强制 OpenAI-compatible
  路由（OPENAI_COMPATIBLE 是 MVP 唯一协议，AGENTS.md §1）。
不引入厂商绑定；API Key 只经 CredentialResolver 密封注入，不写日志/事件。
"""

from __future__ import annotations

from openhands.sdk.llm.llm import LLM
from openhands.sdk.llm.utils.litellm_provider import LLMProvider

from packages.application.ports.credential_resolver import SecretValue
from packages.domain.models import LLMEndpoint, ModelDefinition


def resolve_runtime_model_name(model_name: str, base_url: str) -> str:
    """runtime model identifier 变换（MVP：OPENAI_COMPATIBLE）。

    litellm 对非知名 model 无法推断 provider；探测失败时加 `openai/` 前缀，
    强制走 OpenAI-compatible 路由。已知 provider（如 openai/anthropic 前缀
    模型名）保持原样透传。
    """
    if "/" in model_name:
        return model_name
    provider = LLMProvider.from_model(model=model_name, api_base=base_url)
    if provider.name is None:
        return f"openai/{model_name}"
    return model_name


def build_llm(
    endpoint: LLMEndpoint,
    model: ModelDefinition,
    credential: SecretValue,
    *,
    max_output_tokens: int | None = None,
) -> LLM:
    """按 Research OS 配置装配 OpenHands LLM 对象。

    - base_url/api_key/model 三要素直接透传（S2 已验证 JSON 往返）；
    - request_timeout_seconds / max_retries 由 endpoint 配置显式设置，
      覆盖 SDK 默认 300s/5 次（对齐 Research OS 配置面）；
    - max_output_tokens 由调用方（M3 配置）显式设置，避免 SDK 默认
      cap 16384 与预算冲突（R-09）；
    - model 经 resolve_runtime_model_name 变换（仅本模块）。
    """
    return LLM(
        model=resolve_runtime_model_name(model.model_name, endpoint.base_url),
        base_url=endpoint.base_url,
        api_key=credential.value,
        timeout=endpoint.request_timeout_seconds,
        num_retries=endpoint.max_retries,
        max_output_tokens=max_output_tokens,
    )


__all__ = ["build_llm", "resolve_runtime_model_name"]
