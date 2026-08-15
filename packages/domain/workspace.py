"""Workspace / Execution 域实体定义。

来源：docs/architecture/WORKSPACE_RUNTIME.md。
无 WorkspaceLease 不得写入；可写 Agent 默认独立工作区。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping

from packages.domain.core import Digest, Timestamp
from packages.domain.enums import FailureCategory, TrustProfile


@dataclass(frozen=True, slots=True)
class Workspace:
    id: str
    name: str
    backend_type: str | None = None
    trust_profile: TrustProfile = TrustProfile.SANDBOXED_STANDARD
    read_scopes: list[str] = field(default_factory=list)
    write_scopes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("workspace id must not be empty")
        if not self.name:
            raise ValueError("workspace name must not be empty")


@dataclass(frozen=True, slots=True)
class WorkspaceLease:
    workspace_id: str
    agent_session_id: str
    base_snapshot: str | None = None
    read_scopes: list[str] = field(default_factory=list)
    write_scopes: list[str] = field(default_factory=list)
    network_profile: str | None = None
    compute_profile: str | None = None
    expires_at: Timestamp | None = None
    heartbeat: Timestamp | None = None

    def __post_init__(self) -> None:
        if not self.workspace_id:
            raise ValueError("workspace_id must not be empty")
        if not self.agent_session_id:
            raise ValueError("agent_session_id must not be empty")
        if self.expires_at is not None and self.heartbeat is not None:
            if self.heartbeat.value > self.expires_at.value:
                raise ValueError("heartbeat must not be after expires_at")


@dataclass(frozen=True, slots=True)
class WorkspaceSnapshot:
    workspace_id: str
    digest: str
    created_at: Timestamp | None = None

    def __post_init__(self) -> None:
        if not self.workspace_id:
            raise ValueError("workspace_id must not be empty")
        if not self.digest:
            raise ValueError("snapshot digest must not be empty")


@dataclass(frozen=True, slots=True)
class ExecutionSpec:
    backend_kind: str
    command: str
    resource_profile: str | None = None
    environment_digest: str | None = None
    workspace_path: str | None = None
    environment: Mapping[str, str] = field(default_factory=dict)
    workdir: str = "/workspace"

    def __post_init__(self) -> None:
        if not self.backend_kind:
            raise ValueError("backend_kind must not be empty")
        if not self.command:
            raise ValueError("command must not be empty")
        if not self.workdir.startswith("/"):
            raise ValueError("workdir must be an absolute path")


class ExecutionStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class ExecutionRun:
    """一次 ExecutionSpec 执行的归一化结果（M5 ExecutionBackend 输出）。"""

    run_id: str
    spec: ExecutionSpec
    status: ExecutionStatus
    started_at: Timestamp | None = None
    completed_at: Timestamp | None = None
    exit_code: int | None = None
    failure_category: FailureCategory | None = None
    stdout_digest: Digest | None = None
    stderr_digest: Digest | None = None
    compute_usage_summary: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must not be empty")
        if self.exit_code is not None and self.exit_code < 0:
            raise ValueError("exit_code must be non-negative")
        if (
            self.started_at is not None
            and self.completed_at is not None
            and self.completed_at.value < self.started_at.value
        ):
            raise ValueError("completed_at must not be before started_at")
        if self.status is ExecutionStatus.SUCCEEDED and self.completed_at is None:
            raise ValueError("SUCCEEDED run must carry completed_at")
        if self.status is ExecutionStatus.FAILED and self.failure_category is None:
            raise ValueError("FAILED run must carry failure_category")
