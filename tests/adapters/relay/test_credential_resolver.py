"""env credential resolver 测试。"""

from __future__ import annotations

import pytest

from adapters.relay.credential_resolver import EnvCredentialResolver
from packages.application.ports import InvalidInputError


class TestEnvCredentialResolver:
    def test_resolves_secret_value(self) -> None:
        resolver = EnvCredentialResolver({"llm_main_key": "sk-test-token-123"})
        secret = resolver.resolve("llm_main_key")
        assert secret.value == "sk-test-token-123"

    def test_missing_ref_raises(self) -> None:
        resolver = EnvCredentialResolver({})
        with pytest.raises(InvalidInputError):
            resolver.resolve("missing_key")

    def test_empty_value_raises(self) -> None:
        resolver = EnvCredentialResolver({"llm_main_key": ""})
        with pytest.raises(InvalidInputError):
            resolver.resolve("llm_main_key")

    def test_secret_repr_never_exposes_value(self) -> None:
        resolver = EnvCredentialResolver({"llm_main_key": "sk-super-secret"})
        secret = resolver.resolve("llm_main_key")
        assert "sk-super-secret" not in repr(secret)
