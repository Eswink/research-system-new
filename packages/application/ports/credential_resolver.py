"""CredentialResolver Port：按引用解析密封凭据。

职责：把 credential_ref 解析为 SecretValue（repr 永不输出明文）。
非职责：不持久化凭据；不把 Secret 明文暴露给 Agent/日志/异常/telemetry。
生产实现可接 Vault/Infisical/云 Secret Manager（docs/security/SECRET_MANAGEMENT.md）。

`has` 是**存在性检查**（PLAN-20260915-074）：回答"这个 ref 此刻可不可解析"，
用于状态判定/准入（"provider 声明的必需凭据在不在"），**不解析、不物化明文**。
实现方必须保证 `has` 不会把值带出边界（只回答布尔）；`has` 为真时 `resolve`
必须能成功。它与 `resolve` 的关系是"先问能不能，再要值"，不是另一条取密通道：
调用方只能问自己已经持有的 ref，且本 Port 不提供枚举能力。
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

    def has(self, credential_ref: str) -> bool:
        """该 ref 此刻是否**可解析**（存在且非空，且未被凭据边界拒绝）。

        只回答布尔，不返回、不缓存、不记录值。不得抛异常：不可解析即 False。
        """
        ...

    def resolve(self, credential_ref: str) -> SecretValue: ...
