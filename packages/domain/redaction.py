"""Secret redaction 纯函数。

redaction 规则在 domain 定义（可测试），执行在 adapter 边界。
目标：Authorization 等敏感头永不进入异常消息、header 采集、config repr 与 telemetry。
"""

from __future__ import annotations

import re
from typing import Iterable

REDACTED = "***REDACTED***"

# Authorization: Bearer <token>
_BEARER_RE = re.compile(r"(?i)(bearer\s+)[a-z0-9._~+/=-]+")
# 常见 API key 样式：sk-... 或 <prefix>-<long token>
_API_KEY_RE = re.compile(r"(?i)\b((?:sk|api|key)[-_][a-z0-9._~+/=-]{8,})\b")
# URL 内嵌凭据 user:pass@host
_URL_CRED_RE = re.compile(r"(?i)(://)[^/@\s]+@")

# 允许采集的响应头白名单（绝不包含 authorization / api-key）
SAFE_RESPONSE_HEADERS = frozenset({
    "x-request-id",
    "x-ratelimit-limit-requests",
    "x-ratelimit-remaining-requests",
    "x-ratelimit-reset-requests",
    "openai-processing-ms",
    "openai-organization",
    "cf-cache-status",
    "cf-ray",
    "server",
})


def redact_text(text: str) -> str:
    """对文本执行稳定 redaction：替换为 REDACTED，不改变其余内容。"""
    redacted = _BEARER_RE.sub(lambda m: m.group(1) + REDACTED, text)
    redacted = _API_KEY_RE.sub(REDACTED, redacted)
    redacted = _URL_CRED_RE.sub(lambda m: m.group(1) + REDACTED + "@", redacted)
    return redacted


def redact_exception_message(message: str) -> str:
    return redact_text(message)


def select_safe_headers(headers: Iterable[tuple[str, str]]) -> dict[str, str]:
    """只采集白名单头；Authorization/api-key 永不进入结果。"""
    result: dict[str, str] = {}
    for key, value in headers:
        lowered = key.lower()
        if lowered in SAFE_RESPONSE_HEADERS:
            result[lowered] = value
    return result


def redact_config_repr(endpoint_id: str, base_url: str, credential_configured: bool = True) -> str:
    """配置的 repr：仅暴露 id 与脱敏 base_url，凭据引用以掩码呈现。"""
    credential_state = "<configured>" if credential_configured else "<not-configured>"
    return (
        f"LLMEndpoint(id={endpoint_id!r}, base_url={redact_text(base_url)!r}, "
        f"credential={credential_state})"
    )
