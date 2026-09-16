"""provider 端点绑定：`endpoint_env` 的解析与三态（PLAN-20260915-072）。

`ToolProviderSpec.endpoint_env` 此前是**声明了但没有任何消费者**的字段：配置作者写下
"这个 provider 的端点来自环境变量 X"，既不被执行也不被看见（示例配置甚至把**凭据**名
写进了端点位）。本模块把它变成**准入条件 + 可见状态**：

    NOT_DECLARED  未声明 endpoint_env —— 与从前一致，不做任何判断
    ENV_UNSET     声明了，但进程环境里没有这个变量（或为空）—— provider 不可用
    BOUND         声明了且取到非空值 —— 可用，且只暴露**指纹**

**语义**：环境变量的值是**端点 URL**；**env-only**（只读 `os.environ`，不读文件、
不落盘、不进日志/异常/repr）。凭据不在这里：凭据仍只经 `CredentialResolver`
（`credential_ref`），本模块不解析、不转发任何密钥。

**为什么只给指纹**：读面（注册表 DTO / 控制台）需要回答"绑定没绑、换没换"，
但端点可能含内网主机名或带 token 的查询串，因此只给 `sha256` 指纹，
不给明文也不给 host（见 RECHECK-072 的范围注记）。
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from packages.domain.core import Digest
from packages.domain.tools import ToolProviderSpec

NOT_DECLARED = "NOT_DECLARED"
ENV_UNSET = "ENV_UNSET"
BOUND = "BOUND"
STATES = (NOT_DECLARED, ENV_UNSET, BOUND)


@dataclass(frozen=True, slots=True)
class EndpointBinding:
    """端点绑定的可读投影：状态 + 变量名 + 指纹；**永不**携带端点明文。"""

    state: str
    env_name: str | None = None
    endpoint_digest: str | None = None

    def __post_init__(self) -> None:
        if self.state not in STATES:
            raise ValueError(f"unknown endpoint binding state: {self.state!r}")
        # 只有 BOUND 才允许有指纹：否则读面会把"没绑定"误读成"绑定了某个东西"
        if (self.endpoint_digest is not None) != (self.state == BOUND):
            raise ValueError("endpoint digest is only set for the BOUND state")
        if (self.env_name is not None) == (self.state == NOT_DECLARED):
            raise ValueError("env name is set exactly when an env var was declared")


def resolve_endpoint_binding(
    spec: ToolProviderSpec, *, environ: Mapping[str, str] | None = None
) -> EndpointBinding:
    """按 `spec.endpoint_env` 解析端点绑定；`environ` 仅用于测试注入，默认进程环境。"""
    name = spec.endpoint_env
    if name is None or name == "":
        return EndpointBinding(state=NOT_DECLARED)
    source = os.environ if environ is None else environ
    raw = source.get(name, "")
    if raw.strip() == "":
        return EndpointBinding(state=ENV_UNSET, env_name=name)
    digest = Digest.of_bytes(raw.strip().encode("utf-8"))
    return EndpointBinding(state=BOUND, env_name=name, endpoint_digest=str(digest))


def unbound_reason(binding: EndpointBinding) -> str | None:
    """未绑定时的**可读原因**（点名变量，不点值）；已绑定/未声明返回 None。"""
    if binding.state != ENV_UNSET:
        return None
    return (
        f"provider 声明端点来自环境变量 {binding.env_name}，"
        "但进程环境里未设置（endpoint_env 指端点 URL）"
    )
