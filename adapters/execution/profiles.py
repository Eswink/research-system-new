"""资源 profile → 容器限额的确定性映射（adapters/execution）。

resource_profile 是 Domain 层弱类型字符串（ExecutionSpec.resource_profile），
其到容器 CPU/memory/pids 限额的映射属于基础设施策略，位于 adapter 层。
映射表确定性：同名 profile 永远解析出相同限额，供 ReproducibilityAudit
把资源配置 digest 纳入审计。

安全边界（AGENTS.md §9 / WORKSPACE_RUNTIME.md §6 Trust Profiles）：
- 所有 profile 均默认 deny 网络（容器 network none）、非 privileged、
  capability 全 drop、no-new-privileges；
- 本表只控制 CPU/memory/pids 数值，不开放任何宿主资源。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports.errors import InvalidInputError

DEFAULT_PROFILE = "default"

_SECOND_NANOS = 1_000_000_000
_MIB = 1024 * 1024


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    """容器资源限额（单位与 docker host_config 一致）。"""

    cpu_nanos: int
    memory_bytes: int
    pids_limit: int


# fmt: off
_RESOURCE_PROFILES: dict[str, ResourceLimits] = {
    DEFAULT_PROFILE: ResourceLimits(
        cpu_nanos=2 * _SECOND_NANOS,      # 2 vCPU
        memory_bytes=2 * 1024 * _MIB,     # 2 GiB
        pids_limit=512,
    ),
    "small": ResourceLimits(
        cpu_nanos=1 * _SECOND_NANOS,      # 1 vCPU
        memory_bytes=512 * _MIB,          # 512 MiB
        pids_limit=256,
    ),
    "large": ResourceLimits(
        cpu_nanos=4 * _SECOND_NANOS,      # 4 vCPU
        memory_bytes=8 * 1024 * _MIB,     # 8 GiB
        pids_limit=1024,
    ),
}
# fmt: on


def resolve_resource_profile(name: str | None) -> ResourceLimits:
    """解析 profile 名称；未知名称是调用方 bug（InvalidInputError）。"""
    profile_name = name or DEFAULT_PROFILE
    try:
        return _RESOURCE_PROFILES[profile_name]
    except KeyError:
        raise InvalidInputError(
            f"unknown resource profile {profile_name!r}; "
            f"known profiles: {sorted(_RESOURCE_PROFILES)}"
        ) from None
