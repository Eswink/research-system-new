"""Workspace 映射：WorkspaceLease → OpenHands Workspace。

R-04/R-17 承接：LocalWorkspace 是 host shell（默认 deny，显式配置 + Policy
允许才启用）；文件 API 为裸 Path（CWD 相对）解析，adapter 必须对全部文件
路径显式绝对化 + 工作区根校验，不依赖 OpenHands 内部解析基准。
DockerWorkspace 映射代码 + 环境探测 smoke（M6 计划选项 A）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openhands.sdk.workspace.local import LocalWorkspace

from packages.application.ports.errors import PermanentPortError
from packages.domain.enums import FailureCategory
from packages.domain.workspace import WorkspaceLease


class HostShellDeniedError(PermanentPortError):
    """LocalWorkspace（host shell）被策略禁用（AGENTS.md §9 默认 deny）。"""

    def __init__(self, message: str) -> None:
        super().__init__(message, failure_category=FailureCategory.WORKSPACE_FAILURE)


def absolute_path_within(root: Path, candidate: str | Path) -> Path:
    """把候选路径绝对化并强制落在 root 内（R-17 路径归一化）。"""
    resolved_root = root.resolve()
    candidate_path = Path(candidate)
    if candidate_path.is_absolute():
        resolved = candidate_path.resolve()
    else:
        resolved = (resolved_root / candidate_path).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        raise ValueError(f"path escapes workspace root: {candidate!r}") from None
    return resolved


def build_local_workspace(
    lease: WorkspaceLease | None,
    session_id: str,
    *,
    allow_host_shell: bool = False,
    base_dir: str | None = None,
) -> LocalWorkspace:
    """构造 LocalWorkspace（M6 主路径：隔离临时目录）。

    - host shell 默认 deny：allow_host_shell=False 时抛 HostShellDeniedError；
    - working_dir 使用会话级隔离目录（base_dir 可注入，测试确定性）；
    - workspace 生命周期由 Conversation/close 管理（SDK LocalWorkspace
      working_dir 即根目录，adapter 不做路径转发）。
    """
    if not allow_host_shell:
        raise HostShellDeniedError("LocalWorkspace host shell is denied by default (AGENTS.md §9)")
    root = Path(base_dir or f"workspace/{session_id}").resolve()
    root.mkdir(parents=True, exist_ok=True)
    return LocalWorkspace(working_dir=str(root))


def build_docker_workspace(
    lease: WorkspaceLease | None,
    session_id: str,
    *,
    image: str,
    network_enabled: bool = False,
) -> Any:
    """构造 DockerWorkspace（映射代码；容器链路验证延后至 M9 Real Experiment Runtime）。

    - network 默认关闭（R-05：DockerWorkspace 无默认网络隔离）；
    - 容器生命周期 = WorkspaceBackend 创建/清理面（M6_ADAPTER_DESIGN_NOTES §5）；
    - 延迟导入：openhands-workspace 为可选包，缺失时按配置错误处理。
    """
    try:
        import importlib

        docker_module = importlib.import_module("openhands.workspace.docker.workspace")
    except ImportError as exc:  # pragma: no cover - openhands-workspace 可选包
        raise PermanentPortError(
            "DockerWorkspace unavailable (openhands-workspace not installed)",
            failure_category=FailureCategory.CONFIGURATION,
        ) from exc
    docker_workspace_cls = docker_module.DockerWorkspace
    return docker_workspace_cls(
        container_name=f"research-os-{session_id}",
        image=image,
        network_enabled=network_enabled,
    )


__all__ = [
    "HostShellDeniedError",
    "absolute_path_within",
    "build_local_workspace",
    "build_docker_workspace",
]
