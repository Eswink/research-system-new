"""ExecutionBackend 容器实现（adapters/execution）。

M9 Real Experiment Runtime：真实隔离容器执行，清偿 M7 遗留 P1 债
（ExecutionBackend 容器执行 + DockerWorkspace 容器链路验证）。
"""

from adapters.execution.docker_backend import DockerExecutionBackend
from adapters.execution.profiles import ResourceLimits, resolve_resource_profile

__all__ = [
    "DockerExecutionBackend",
    "ResourceLimits",
    "resolve_resource_profile",
]
