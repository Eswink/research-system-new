"""RegistryCredentialResolver：内存注册 + 环境变量回退的凭据解析。

M13 控制面凭据机制（M19 central Secret Manager 前的最小合法实现）：
- API Key 从用户输入（POST /llm-endpoints 的 api_key 字段）经 register()
  进入进程内密封注册表，永不落盘、永不回显、repr 脱敏；
- credential_ref 优先命中注册表，其次回退环境变量（EnvCredentialResolver
  语义，供既有 YAML 配置的 credential_ref 使用）；
- 服务重启后注册表清空：UI 显示 credential missing，wizard 重新输入
  （诚实声明，不伪装 Secret Manager）。
"""

from __future__ import annotations

import os
from typing import Mapping

from packages.application.ports.credential_resolver import SecretValue
from packages.application.ports.errors import InvalidInputError


class RegistryCredentialResolver:
    """register(ref, value) 注入；resolve(ref) 先查注册表再查环境变量。"""

    def __init__(self, environment: Mapping[str, str] | None = None) -> None:
        self._environment = dict(environment if environment is not None else os.environ)
        self._registry: dict[str, str] = {}

    def register(self, credential_ref: str, value: str) -> None:
        if not credential_ref:
            raise InvalidInputError("credential_ref must not be empty")
        if not value:
            raise InvalidInputError("credential value must not be empty")
        self._registry[credential_ref] = value

    def unregister(self, credential_ref: str) -> None:
        self._registry.pop(credential_ref, None)

    def has(self, credential_ref: str) -> bool:
        return credential_ref in self._registry or credential_ref in self._environment

    def resolve(self, credential_ref: str) -> SecretValue:
        if credential_ref in self._registry:
            return SecretValue(self._registry[credential_ref])
        if credential_ref in self._environment:
            value = self._environment[credential_ref]
            if value:
                return SecretValue(value)
        raise InvalidInputError(f"credential_ref not found: {credential_ref!r}")
