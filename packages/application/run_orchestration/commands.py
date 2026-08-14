"""RunOrchestration 强类型命令对象。

命令是应用层的输入契约（Command Query Separation）：Use Case 只接收
命令，不接收裸参数散列，保证参数不爆发、调用面可审计。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.domain.core import ID


@dataclass(frozen=True, slots=True)
class StartRunCommand:
    """启动一次 ResearchRun 的完整输入。"""

    project_id: str
    protocol_id: str
    run_id: ID
    trace_id: str
    idempotency_key: str | None = None
    notes: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.project_id:
            raise ValueError("project_id must not be empty")
        if not self.protocol_id:
            raise ValueError("protocol_id must not be empty")
        if not self.trace_id:
            raise ValueError("trace_id must not be empty")


@dataclass(frozen=True, slots=True)
class CancelRunCommand:
    """取消一次运行（协作式）。"""

    run_id: ID
    reason: str = "user requested cancellation"

    def __post_init__(self) -> None:
        if not self.reason:
            raise ValueError("cancel reason must not be empty")


@dataclass(frozen=True, slots=True)
class ResumeRunCommand:
    """恢复一次已暂停的运行；恢复必须使用原 Manifest frozen semantics。"""

    run_id: ID
    frozen_manifest_digest: str
    trace_id: str

    def __post_init__(self) -> None:
        if not self.frozen_manifest_digest:
            raise ValueError("frozen_manifest_digest must not be empty")
        if not self.trace_id:
            raise ValueError("trace_id must not be empty")
