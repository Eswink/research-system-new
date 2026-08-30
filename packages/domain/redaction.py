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
# 常见 API key 样式：sk-... 或 <prefix>-<long token>。
# 不加前置 \b：M15 复审实测 `abcsk-live-…` 这类与前缀字符相连的 key 会整体逃过
# redaction。宁可过度脱敏（identity/digest 字段不含该形态）也不放过凭据。
_API_KEY_RE = re.compile(r"(?i)((?:sk|api|key)[-_][a-z0-9._~+/=-]{8,})")
# URL 内嵌凭据 user:pass@host
_URL_CRED_RE = re.compile(r"(?i)(://)[^/@\s]+@")
# 具名凭据赋值：password=/passwd=/secret=/token=/apikey= 后的值
_NAMED_SECRET_RE = re.compile(
    r"(?i)((?:password|passwd|pwd|secret|token|apikey|access[-_]?key)\s*[=:]\s*)[^\s,;&\"']+"
)
# 厂商特征凭据前缀（M15 复审：仅覆盖 bearer/sk/URL 会漏掉下列全部形态）
_VENDOR_TOKEN_RES = (
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),  # Google API key
    re.compile(r"gh[pousr]_[0-9A-Za-z]{16,}"),  # GitHub token
    re.compile(r"xox[baprse]-[0-9A-Za-z-]{10,}"),  # Slack token
    re.compile(r"(?:AKIA|ASIA)[0-9A-Z]{16}"),  # AWS access key id
    re.compile(r"hf_[0-9A-Za-z]{16,}"),  # HuggingFace token
    re.compile(r"glpat-[0-9A-Za-z_-]{16,}"),  # GitLab PAT
)

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
    """对文本执行稳定 redaction：替换为 REDACTED，不改变其余内容。

    幂等：对已脱敏文本再次调用不会引入新的 REDACTED 标记。
    """
    redacted = _BEARER_RE.sub(lambda m: m.group(1) + REDACTED, text)
    redacted = _NAMED_SECRET_RE.sub(lambda m: m.group(1) + REDACTED, redacted)
    for pattern in _VENDOR_TOKEN_RES:
        redacted = pattern.sub(REDACTED, redacted)
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
