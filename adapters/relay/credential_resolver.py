"""env-based credential resolver。

credential_ref 指向环境变量名；值以 SecretValue 密封，永不落盘/log。
未解析或空值抛 InvalidInputError（Port 统一错误模型）。
"""

from __future__ import annotations

import os

from packages.application.ports import InvalidInputError, SecretValue


class EnvCredentialResolver:
    """从环境变量解析凭据。"""

    def __init__(self, environment: dict[str, str] | None = None) -> None:
        self._environment = environment if environment is not None else dict(os.environ)

    def has(self, credential_ref: str) -> bool:
        """存在性检查（PLAN-20260915-074）：变量存在且非空——与 `resolve` 的成功条件
        一致，只回答布尔，不把值带出边界。"""
        return bool(self._environment.get(credential_ref, ""))

    def resolve(self, credential_ref: str) -> SecretValue:
        if credential_ref not in self._environment:
            raise InvalidInputError(f"credential_ref not found in environment: {credential_ref!r}")
        value = self._environment[credential_ref]
        if not value:
            raise InvalidInputError(f"credential_ref is empty in environment: {credential_ref!r}")
        return SecretValue(value)
