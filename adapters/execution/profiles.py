"""资源 profile → 容器限额的确定性映射（adapters/execution）。

resource_profile 是 Domain 层弱类型字符串（ExecutionSpec.resource_profile），
其到容器 CPU/memory/pids 限额的映射属于基础设施策略，位于 adapter 层。
映射表确定性：同名 profile 永远解析出相同限额，供 ReproducibilityAudit
把资源配置 digest 纳入审计。

安全边界（AGENTS.md §9 / WORKSPACE_RUNTIME.md §6 Trust Profiles）：
- 所有 profile 均默认 deny 网络（容器 network none）、非 privileged、
  capability 全 drop、no-new-privileges；
- 本表只控制 CPU/memory/pids 数值与 GPU 需求契约，不开放任何宿主资源。
  GPU profile 与 CPU profile 的 host_config 差异**只有** DeviceRequests
  （WP0 T2/T4 实测 readonly rootfs 与 nvidia hook 无冲突，见
  docs/references/upstream/M17_GPU_RUNTIME_QUALIFICATION.md）。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports.errors import InvalidInputError
from packages.domain.workers import (
    GPU_CAPABILITY,
    GPU_RESOURCE_PROFILES,
    is_gpu_resource_profile,
)
from packages.domain.workspace import ExecutionSpec

DEFAULT_PROFILE = "default"
# 非 GPU 执行平面的调度 token：与 worker 默认声明（services/worker
# __main__ RESEARCHOS_WORKER_CAPABILITIES 默认 "docker"）一致。
# M17 修复：原 `spec.backend_kind.lower()` 派生出 "sandbox"，真实实验的
# 远程分发永远匹配不到 worker —— 见 RemoteExecutionBackend._submit。
DOCKER_CAPABILITY = "docker"

_SECOND_NANOS = 1_000_000_000
_MIB = 1024 * 1024
_GIB = 1024 * _MIB


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    """容器资源限额（单位与 docker host_config 一致）。"""

    cpu_nanos: int
    memory_bytes: int
    pids_limit: int


@dataclass(frozen=True, slots=True)
class GpuRequirements:
    """GPU profile 的执行期显式契约（WP3c 第 3 层断言依据）。

    调度键只有单 token `gpu`（ADR-0029）：单 worker 环境为 VRAM/CUDA
    版本发明第二套数值调度谓词属于 theater。这些需求由
    DockerExecutionBackend 注入容器环境，实验入口在设备上强制断言。
    """

    device_count: int
    min_total_vram_bytes: int
    min_cuda_runtime_version: str
    framework: str


@dataclass(frozen=True, slots=True)
class GpuProfile:
    """GPU profile = 容器限额（含 DeviceRequests 语义）+ 执行期契约。"""

    limits: ResourceLimits
    requirements: GpuRequirements


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

# GPU profile 限额：CPU/RAM 是宿主侧容器限额；显存契约由 requirements 表达
# （DeviceRequests 与计数由 DockerExecutionBackend 按 GPU profile 注入）。
_GPU_PROFILES: dict[str, GpuProfile] = {
    "gpu-small": GpuProfile(
        limits=ResourceLimits(
            cpu_nanos=4 * _SECOND_NANOS,          # 4 vCPU
            memory_bytes=8 * _GIB,                # 8 GiB host RAM
            pids_limit=512,
        ),
        requirements=GpuRequirements(
            device_count=1,
            min_total_vram_bytes=6 * _GIB,        # 契约按设备总量断言
            min_cuda_runtime_version="12.8",
            framework="torch",
        ),
    ),
    # 受控 OOM 探针（WP4b）：同 gpu-small 限额；分块分配上限在容器内按
    # 实测 free VRAM 动态计算，这里只表达最低入场契约。
    "gpu-oom-probe": GpuProfile(
        limits=ResourceLimits(
            cpu_nanos=2 * _SECOND_NANOS,
            memory_bytes=8 * _GIB,
            pids_limit=512,
        ),
        requirements=GpuRequirements(
            device_count=1,
            min_total_vram_bytes=6 * _GIB,
            min_cuda_runtime_version="12.8",
            framework="torch",
        ),
    ),
}
# fmt: on

# 与 domain 单一事实源同步：adapter GPU 表的键必须等于域内声明的集合
# （漂移由 test_gpu_dispatch 契约测试锁定）。
assert set(_GPU_PROFILES) == set(GPU_RESOURCE_PROFILES), (
    "GPU profile drift: adapters/execution/profiles.py keys must equal "
    "packages.domain.workers.GPU_RESOURCE_PROFILES"
)


def resolve_resource_profile(name: str | None) -> ResourceLimits:
    """解析 profile 名称；未知名称是调用方 bug（InvalidInputError）。"""
    gpu = _GPU_PROFILES.get(name or DEFAULT_PROFILE)
    if gpu is not None:
        return gpu.limits
    try:
        return _RESOURCE_PROFILES[name or DEFAULT_PROFILE]
    except KeyError:
        raise InvalidInputError(
            f"unknown resource profile {name!r}; "
            f"known profiles: {sorted(set(_RESOURCE_PROFILES) | set(_GPU_PROFILES))}"
        ) from None


def is_gpu_profile(name: str | None) -> bool:
    """该 profile 是否要求 GPU（决定 DeviceRequests 与调度 token）。

    委托 domain 单一事实源（application 证据门禁使用同一判定）。
    """
    return is_gpu_resource_profile(name)


def resolve_gpu_requirements(name: str) -> GpuRequirements:
    """GPU profile 的执行期契约；非 GPU profile 是调用方 bug。"""
    try:
        return _GPU_PROFILES[name].requirements
    except KeyError:
        raise InvalidInputError(
            f"resource profile {name!r} is not a GPU profile; "
            f"known GPU profiles: {sorted(_GPU_PROFILES)}"
        ) from None


def derive_required_capability(spec: ExecutionSpec) -> str:
    """spec → 调度 token（M17 WP2，修复 backend_kind.lower() 缺陷）。

    GPU profile → `gpu`；其余 → `docker`（worker 默认声明的执行平面
    token）。未知 profile fail-closed（与 resolve_resource_profile 一致）。
    """
    if is_gpu_profile(spec.resource_profile):
        return GPU_CAPABILITY
    if spec.resource_profile is None or spec.resource_profile in _RESOURCE_PROFILES:
        return DOCKER_CAPABILITY
    raise InvalidInputError(f"unknown resource profile {spec.resource_profile!r}")
