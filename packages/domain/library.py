"""Library 域：用户标注库目录条目（PLAN-20260914-044 / EC-03 第一批）。

`LibraryResource` 是 prompts / datasets / notebooks 三页共享的**目录事实**：
用户为某一项目登记的一个具名条目（提示词模板、数据集引用、notebook 文档），
带描述、标签与可选内容引用。

诚实边界：本域只承载元数据与**不透明引用**（content_ref 可为空，不解析、
不下载、不做版本树/A-B/发布）；datasets 的**评测输入**由既有 eval spec 承载，
不与本域耦合（避免第二套真相）。生命周期极简：ACTIVE ⇄ ARCHIVED（归档非删除，
历史保留）。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from packages.domain.core import Timestamp

MAX_RESOURCE_ID_LENGTH = 128
MAX_RESOURCE_NAME_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000
MAX_CONTENT_REF_LENGTH = 512
MAX_TAGS = 32
MAX_TAG_LENGTH = 64


class ResourceKind(StrEnum):
    PROMPT = "prompt"
    DATASET = "dataset"
    NOTEBOOK = "notebook"


class ResourceStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True, slots=True)
class LibraryResource:
    id: str
    project_id: str
    kind: ResourceKind
    name: str
    description: str
    content_ref: str | None
    tags: tuple[str, ...]
    status: ResourceStatus
    created_at: Timestamp
    updated_at: Timestamp

    def __post_init__(self) -> None:
        self._check_id()
        if not self.project_id.strip():
            raise ValueError("project_id must not be empty")
        if not isinstance(self.kind, ResourceKind):
            raise ValueError(f"unknown resource kind: {self.kind!r}")
        name = self.name.strip()
        if not name or len(name) > MAX_RESOURCE_NAME_LENGTH:
            raise ValueError(
                f"name must be non-empty and <= {MAX_RESOURCE_NAME_LENGTH} chars",
            )
        if len(self.description) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(f"description must be <= {MAX_DESCRIPTION_LENGTH} chars")
        if self.content_ref is not None and len(self.content_ref) > MAX_CONTENT_REF_LENGTH:
            raise ValueError(f"content_ref must be <= {MAX_CONTENT_REF_LENGTH} chars")
        if len(self.tags) > MAX_TAGS:
            raise ValueError(f"tags must be <= {MAX_TAGS} entries")
        for tag in self.tags:
            if not tag.strip() or len(tag) > MAX_TAG_LENGTH:
                raise ValueError(f"invalid tag: {tag!r}")
        if not isinstance(self.status, ResourceStatus):
            raise ValueError(f"unknown resource status: {self.status!r}")

    def _check_id(self) -> None:
        if not self.id or len(self.id) > MAX_RESOURCE_ID_LENGTH:
            raise ValueError(
                f"id must be non-empty and <= {MAX_RESOURCE_ID_LENGTH} chars",
            )

    def renamed(self, name: str, *, at: Timestamp) -> "LibraryResource":
        return replace(self, name=name, updated_at=at)

    def with_status(self, status: ResourceStatus, *, at: Timestamp) -> "LibraryResource":
        """ACTIVE ⇄ ARCHIVED；同值幂等（返回新对象，updated_at 前进）。"""
        return replace(self, status=ResourceStatus(status), updated_at=at)
