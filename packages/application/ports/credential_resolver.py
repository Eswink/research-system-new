"""CredentialResolver Port：按引用解析密封凭据。

职责：把 credential_ref 解析为 SecretValue（repr 永不输出明文）。
非职责：不持久化凭据；不把 Secret 明文暴露给 Agent/日志/异常/telemetry。
生产实现可接 Vault/Infisical/云 Secret Manager（docs/security/SECRET_MANAGEMENT.md）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class SecretValue:
    """密封的密钥值；repr 永不输出明文。"""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("secret value must not be empty")

    def __repr__(self) -> str:
        return "<SecretValue:redacted>"


@runtime_checkable
class CredentialResolver(Protocol):
    """按 credential_ref 解析密钥；未解析抛 InvalidInputError。"""

    def resolve(self, credential_ref: str) -> SecretValue: ...
