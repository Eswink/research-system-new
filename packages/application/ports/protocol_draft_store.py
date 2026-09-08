"""ProtocolDraftStore Port：协议草稿与不可变修订存储（PLAN-20260908-033）。

语义（docs/frontend/CONSOLE_REBUILD.md §4）：
- 草稿是运行前工件；修订一旦保存即不可变（append-only）。
- 保存必须携带 expected_revision（乐观并发）；陈旧写入由实现拒绝。
- 修订号是草稿内部版本，不是工程版本，也不是 RunManifest Revision。
- 生产 PostgreSQL / 开发 SQLite / 测试内存三实现，同一 Port 契约。

Canonical State 边界：草稿表是控制面新增持久化结构；Domain 状态机、
RunManifest 与既有表不受影响。回退应用后草稿数据保留。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


class DraftStoreConflictError(Exception):
    """乐观并发冲突：expected_revision 与当前草稿版本不一致（API 层映射 412）。"""

    def __init__(self, expected_revision: int, current_revision: int) -> None:
        super().__init__(
            f"revision mismatch: expected {expected_revision}, current {current_revision}"
        )
        self.expected_revision = expected_revision
        self.current_revision = current_revision


class DraftStoreNotFoundError(Exception):
    """草稿不存在。"""


@dataclass(frozen=True, slots=True)
class ProtocolDraftRecord:
    """草稿当前状态（含最新修订引用）。"""

    draft_id: str
    project_id: str
    name: str
    revision: int
    yaml_text: str
    source_digest: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class ProtocolDraftRevision:
    """不可变修订快照。"""

    draft_id: str
    revision: int
    yaml_text: str
    source_digest: str
    created_at: str


@dataclass(frozen=True, slots=True)
class DraftSaveInput:
    """保存输入：新草稿 revision 从 1 开始，已有草稿 revision + 1。"""

    draft_id: str
    project_id: str
    name: str
    yaml_text: str
    source_digest: str
    expected_revision: int | None  # None = 首次创建
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class DraftSaveResult:
    """保存结果：返回草稿当前修订视图。"""

    record: ProtocolDraftRecord
    replayed: bool = False  # 幂等重放标记（同 key 重复提交不产生新修订）


@dataclass(frozen=True, slots=True)
class DraftQuery:
    """草稿列表过滤条件（参数对象，规避参数爆发）。"""

    project_id: str
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True, slots=True)
class DraftTemplate:
    """受控模板目录条目（正文只来自受控来源，不接受任意路径）。"""

    template_id: str
    display_name: str
    description: str
    yaml_text: str
    source: str  # 来源标注（如 examples/protocols 快照）


@dataclass(frozen=True, slots=True)
class DraftRevisionRef:
    """运行入口使用的精确修订引用。"""

    draft_id: str
    revision: int

    def __post_init__(self) -> None:
        if not self.draft_id:
            raise ValueError("draft_id must not be empty")
        if self.revision < 1:
            raise ValueError("revision must be >= 1")


@dataclass(frozen=True, slots=True)
class DraftValidationIssue:
    """服务端校验问题（可定位路径 + 稳定错误码）。"""

    path: str
    code: str
    message: str
    severity: str = "error"  # error | warning


@dataclass(frozen=True, slots=True)
class DraftValidationResult:
    """服务端 YAML 校验结果（解析 + Schema + 编译前静态检查）。"""

    ok: bool
    issues: tuple[DraftValidationIssue, ...] = field(default_factory=tuple)
    protocol_id: str | None = None
    protocol_digest: str | None = None
    phase_count: int = 0


@runtime_checkable
class ProtocolDraftStore(Protocol):
    """草稿存储 Port（PostgreSQL / SQLite / InMemory 同契约）。"""

    def create(
        self, project_id: str, name: str, yaml_text: str, source_digest: str, idempotency_key: str
    ) -> ProtocolDraftRecord: ...

    def get(self, draft_id: str) -> ProtocolDraftRecord | None: ...

    def list(self, query: DraftQuery) -> tuple[ProtocolDraftRecord, ...]: ...

    def save(
        self,
        draft_id: str,
        *,
        yaml_text: str,
        source_digest: str,
        expected_revision: int,
        idempotency_key: str,
    ) -> DraftSaveResult: ...

    def list_revisions(self, draft_id: str) -> tuple[ProtocolDraftRevision, ...]: ...

    def get_revision(self, draft_id: str, revision: int) -> ProtocolDraftRevision | None: ...
