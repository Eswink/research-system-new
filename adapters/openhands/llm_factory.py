"""LLM 装配：LLMEndpoint + SecretValue + ModelDefinition → OpenHands LLM。

三要素构造（S2 实证）：LLM(model=..., base_url=..., api_key=...)；
runtime model identifier transformation 只存在于本模块：
- 非知名 model + 自定义 base_url 时 litellm 无法推断 provider（R-08 实证），
  经 LLMProvider.from_model 探测失败后加 `openai/` 前缀强制 OpenAI-compatible 路由；
- `protocol=ANTHROPIC` 的端点改用 `anthropic/` 前缀（Messages 形态），
  未知协议**点名拒绝**，不无声套用 OpenAI 前缀。
不引入厂商绑定；API Key 只经 CredentialResolver 密封注入，不写日志/事件。
"""

from __future__ import annotations

from openhands.sdk.llm.llm import LLM
from openhands.sdk.llm.utils.litellm_provider import LLMProvider

from packages.application.ports.credential_resolver import SecretValue
from packages.domain.enums import LLMProtocol
from packages.domain.models import LLMEndpoint, ModelDefinition

_LEGAL_PROTOCOLS = ", ".join(sorted(member.value for member in LLMProtocol))


def resolve_runtime_model_name(model_name: str, base_url: str, *, protocol: str) -> str:
    """runtime model identifier 变换，按 `endpoint.protocol` 选前缀。

    - 已带 `/` 的名字（显式 provider 前缀）原样透传；
    - `ANTHROPIC` ⇒ `anthropic/` 前缀（litellm 的 Messages 路由约定）；
    - `OPENAI_COMPATIBLE` ⇒ 探测失败时加 `openai/` 前缀（既有行为不变）；
    - 其余取值 ⇒ 点名拒绝：无声套用 OpenAI 前缀会把「配了别的协议」变成假象。
    """
    if protocol not in {member.value for member in LLMProtocol}:
        raise ValueError(f"endpoint protocol must be one of {_LEGAL_PROTOCOLS}: {protocol!r}")
    if "/" in model_name:
        return model_name
    if protocol == LLMProtocol.ANTHROPIC.value:
        return f"anthropic/{model_name}"
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
        model=resolve_runtime_model_name(
            model.model_name, endpoint.base_url, protocol=endpoint.protocol
        ),
        base_url=endpoint.base_url,
        api_key=credential.value,
        timeout=endpoint.request_timeout_seconds,
        num_retries=endpoint.max_retries,
        max_output_tokens=max_output_tokens,
    )


__all__ = ["build_llm", "resolve_runtime_model_name"]
