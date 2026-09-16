"""FakeCredentialResolver：密封凭据解析（无真实凭据，纯内存映射）。"""

from __future__ import annotations

from adapters.fakes.base import FakeBase
from packages.application.ports.credential_resolver import SecretValue
from packages.application.ports.errors import InvalidInputError


class FakeCredentialResolver(FakeBase):
    """按 ref 返回预置 SecretValue；未注册 ref 抛 KeyError（Port 语义）。"""

    def __init__(self, secrets: dict[str, str] | None = None) -> None:
        super().__init__("credential_resolver")
        self._secrets = dict(secrets or {})
        self._denied_scopes: set[str] = set()

    def register(self, ref: str, value: str) -> None:
        self._secrets[ref] = value

    def deny_scope(self, ref: str) -> None:
        self._denied_scopes.add(ref)

    def has(self, credential_ref: str) -> bool:
        """存在性检查（PLAN-20260915-074）：已注册且未被 deny_scope 拒绝——与
        `resolve` 的成功条件一致，只回答布尔（记录里也只有布尔，没有值）。"""
        self._enter("has", credential_ref)
        available = credential_ref in self._secrets and credential_ref not in self._denied_scopes
        self._record("has", credential_ref, result="present" if available else "absent")
        return available

    def resolve(self, credential_ref: str) -> SecretValue:
        self._enter("resolve", credential_ref)
        if credential_ref in self._denied_scopes:
            self._record("resolve", credential_ref, error="InvalidInputError")
            raise InvalidInputError(f"credential scope denied: {credential_ref}")
        if credential_ref not in self._secrets:
            self._record("resolve", credential_ref, error="InvalidInputError")
            raise InvalidInputError(f"credential not found: {credential_ref}")
        value = SecretValue(self._secrets[credential_ref])
        self._record("resolve", credential_ref, result="<secret-redacted>")
        return value
