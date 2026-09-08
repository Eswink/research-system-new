"""协议草稿 REST DTO（PLAN-20260908-033）。

与 docs/frontend/CONSOLE_REBUILD.md §4 的映射对应：保存返回草稿 ID、
修订号、资源版本（ETag）与摘要；原文摘要与协议语义摘要分开。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProtocolDraftCreateDto(BaseModel):
    """创建草稿（正文必须通过服务端校验）。"""

    name: str = Field(min_length=1, max_length=120)
    yaml_text: str = Field(min_length=1, max_length=131072)


class ProtocolDraftSaveDto(BaseModel):
    """保存新修订（expected_revision 乐观并发；配合 If-Match）。"""

    yaml_text: str = Field(min_length=1, max_length=131072)
    expected_revision: int = Field(ge=1)


class ProtocolDraftValidateDto(BaseModel):
    """未保存 YAML 的服务端校验请求。"""

    yaml_text: str = Field(min_length=1, max_length=131072)


class ProtocolDraftViewDto(BaseModel):
    """草稿当前状态视图。"""

    draft_id: str
    project_id: str
    name: str
    revision: int
    yaml_text: str
    source_digest: str
    created_at: str
    updated_at: str


class ProtocolDraftSummaryDto(BaseModel):
    """草稿列表项（不含正文）。"""

    draft_id: str
    project_id: str
    name: str
    revision: int
    source_digest: str
    created_at: str
    updated_at: str


class ProtocolDraftRevisionDto(BaseModel):
    """不可变修订视图。"""

    draft_id: str
    revision: int
    yaml_text: str
    source_digest: str
    created_at: str


class ProtocolDraftIssueDto(BaseModel):
    """校验问题（可定位路径 + 稳定错误码）。"""

    path: str
    code: str
    message: str
    severity: str = "error"


class ProtocolDraftValidateResultDto(BaseModel):
    """校验结果（ok=false 时 issues 非空）。"""

    ok: bool
    issues: list[ProtocolDraftIssueDto] = Field(default_factory=list)
    protocol_id: str | None = None
    protocol_digest: str | None = None
    phase_count: int = 0


class ProtocolDraftTemplateDto(BaseModel):
    """模板目录条目。"""

    template_id: str
    display_name: str
    description: str
    yaml_text: str
    source: str


class ProtocolDraftRunRefDto(BaseModel):
    """已保存草稿修订引用（运行入口扩展；与 path 二选一）。"""

    draft_id: str = Field(min_length=1, max_length=120)
    revision: int = Field(ge=1)
