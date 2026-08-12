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
