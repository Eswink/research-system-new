"""协议草稿控制面路由（PLAN-20260908-033）。

流程：HTTP → DTO → DraftService（protocol_authoring）→ ProtocolDraftStore Port。
- 模板只读受控目录；不接受任意文件系统路径；
- 保存携带 Idempotency-Key（中间件强制）+ If-Match/expected_revision；
- 校验端点零副作用；启动链路仍走 compile → preflight → freeze。
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from packages.application.ports.protocol_draft_store import (
    DraftStoreConflictError,
    DraftStoreNotFoundError,
    DraftValidationIssue,
    ProtocolDraftRecord,
)
from packages.application.protocol_authoring import (
    DraftService,
    ProtocolDraftValidationError,
)
from packages.application.protocol_authoring.service import (
    DraftTemplates,
    DraftTemplateSource,
    validate_yaml_document,
)
from services.api.catalog_merge import require_registered_project
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.protocol_drafts import (
    ProtocolDraftCreateDto,
    ProtocolDraftIssueDto,
    ProtocolDraftRevisionDto,
    ProtocolDraftRunRefDto,
    ProtocolDraftSaveDto,
    ProtocolDraftSummaryDto,
    ProtocolDraftTemplateDto,
    ProtocolDraftValidateDto,
    ProtocolDraftValidateResultDto,
    ProtocolDraftViewDto,
)
from services.api.errors import ApiError

router = APIRouter(tags=["protocol-drafts"])

_TEMPLATE_SOURCES = (
    (
        "sort-analysis",
        "Sort 分析（2-phase 参考）",
        "M7 参考场景：执行 + 独立复核",
        "sort_analysis_v1.yaml",
    ),
    ("console-demo", "Console 演示研究", "M13 控制面演示协议", "console_demo_research_v1.yaml"),
    ("ai-ml-research", "AI/ML 研究模板", "多阶段研究协议骨架", "ai_ml_research_v0_4_0.yaml"),
    ("gpu-research", "GPU 研究模板", "M17 单卡 GPU 执行场景", "m17_gpu_research_v1.yaml"),
)


def draft_service_of(request: Request) -> DraftService:
    """从装配取出 DraftService（缺失 → 503）。"""
    deps = get_deps(request)
    service: DraftService | None = deps.protocol_draft_service
    if service is None:
        raise ApiError(503, "Draft Service Unavailable", "protocol draft service not configured")
    return service


def default_templates() -> DraftTemplates:
    """受控模板目录（examples/protocols 快照；不接受任意路径）。"""
    sources = tuple(_source(*entry) for entry in _TEMPLATE_SOURCES)
    return DraftTemplates(sources)


def _source(template_id: str, display: str, description: str, path: str) -> DraftTemplateSource:
    return DraftTemplateSource(
        template_id=template_id,
        display_name=display,
        description=description,
        relative_path=path,
    )


@router.get("/protocol-templates", response_model=list[ProtocolDraftTemplateDto])
async def list_templates(request: Request) -> list[ProtocolDraftTemplateDto]:
    """受控模板目录（只读；正文来自 examples/protocols 注册源）。"""
    service = draft_service_of(request)
    return [
        ProtocolDraftTemplateDto(
            template_id=item.template_id,
            display_name=item.display_name,
            description=item.description,
            yaml_text=item.yaml_text,
            source=item.source,
        )
        for item in service.list_templates()
    ]


@router.get("/protocol-templates/{template_id}", response_model=ProtocolDraftTemplateDto)
async def get_template(template_id: str, request: Request) -> ProtocolDraftTemplateDto:
    service = draft_service_of(request)
    template = service.get_template(template_id)
    if template is None:
        raise ApiError(404, "Template Not Found", f"template unavailable: {template_id!r}")
    return ProtocolDraftTemplateDto(
        template_id=template.template_id,
        display_name=template.display_name,
        description=template.description,
        yaml_text=template.yaml_text,
        source=template.source,
    )


@router.post("/protocol-drafts/validate", response_model=ProtocolDraftValidateResultDto)
async def validate_draft(
    payload: ProtocolDraftValidateDto, request: Request
) -> ProtocolDraftValidateResultDto:
    """未保存 YAML 的服务端校验（零副作用；分析类 POST，无业务写入）。"""
    del request
    result = validate_yaml_document(payload.yaml_text)
    return ProtocolDraftValidateResultDto(
        ok=result.ok,
        issues=[
            ProtocolDraftIssueDto(
                path=issue.path, code=issue.code, message=issue.message, severity=issue.severity
            )
            for issue in result.issues
        ],
        protocol_id=result.protocol_id,
        protocol_digest=result.protocol_digest,
        phase_count=result.phase_count,
    )


@router.post(
    "/projects/{project_id}/protocol-drafts",
    response_model=ProtocolDraftViewDto,
    status_code=201,
)
async def create_draft(
    project_id: str,
    payload: ProtocolDraftCreateDto,
    request: Request,
    response: Response,
) -> ProtocolDraftViewDto:
    """创建草稿（正文必须通过校验；幂等键重放返回原记录；归属路径项目，WP-B）。"""
    deps: ApiDeps = get_deps(request)
    require_registered_project(deps, project_id)
    service = draft_service_of(request)
    try:
        record = service.create(
            name=payload.name,
            yaml_text=payload.yaml_text,
            idempotency_key=_idem_key(request),
            project_id=project_id,
        )
    except ProtocolDraftValidationError as exc:
        raise _unprocessable(exc.issues) from exc
    response.headers["ETag"] = f'"{record.revision}"'
    return _view_dto(record)


@router.get("/projects/{project_id}/protocol-drafts", response_model=list[ProtocolDraftSummaryDto])
async def list_drafts(project_id: str, request: Request) -> list[ProtocolDraftSummaryDto]:
    service = draft_service_of(request)
    return [
        ProtocolDraftSummaryDto(
            draft_id=record.draft_id,
            project_id=record.project_id,
            name=record.name,
            revision=record.revision,
            source_digest=record.source_digest,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        for record in service.list(project_id=project_id)
    ]


@router.get("/protocol-drafts/{draft_id}", response_model=ProtocolDraftViewDto)
async def get_draft(draft_id: str, request: Request, response: Response) -> ProtocolDraftViewDto:
    service = draft_service_of(request)
    record = service.get(draft_id)
    if record is None:
        raise ApiError(404, "Draft Not Found", f"protocol draft not found: {draft_id}")
    response.headers["ETag"] = f'"{record.revision}"'
    return _view_dto(record)


@router.get("/protocol-drafts/{draft_id}/revisions", response_model=list[ProtocolDraftRevisionDto])
async def list_draft_revisions(draft_id: str, request: Request) -> list[ProtocolDraftRevisionDto]:
    service = draft_service_of(request)
    try:
        return [
            ProtocolDraftRevisionDto(
                draft_id=item.draft_id,
                revision=item.revision,
                yaml_text=item.yaml_text,
                source_digest=item.source_digest,
                created_at=item.created_at,
            )
            for item in service.list_revisions(draft_id)
        ]
    except KeyError as exc:
        raise ApiError(404, "Draft Not Found", f"protocol draft not found: {draft_id}") from exc


@router.get(
    "/protocol-drafts/{draft_id}/revisions/{revision}",
    response_model=ProtocolDraftRevisionDto,
)
async def get_draft_revision(
    draft_id: str, revision: int, request: Request
) -> ProtocolDraftRevisionDto:
    service = draft_service_of(request)
    item = service.get_revision(draft_id, revision)
    if item is None:
        raise ApiError(404, "Revision Not Found", f"revision not found: {draft_id}@{revision}")
    return ProtocolDraftRevisionDto(
        draft_id=item.draft_id,
        revision=item.revision,
        yaml_text=item.yaml_text,
        source_digest=item.source_digest,
        created_at=item.created_at,
    )


@router.put("/protocol-drafts/{draft_id}", response_model=ProtocolDraftViewDto)
async def save_draft(
    draft_id: str,
    payload: ProtocolDraftSaveDto,
    request: Request,
    response: Response,
) -> ProtocolDraftViewDto:
    """保存新修订（expected_revision 乐观并发；冲突 → 412，附当前修订号）。"""
    service = draft_service_of(request)
    _require_if_match(request, payload.expected_revision)
    try:
        result = service.save(
            draft_id,
            yaml_text=payload.yaml_text,
            expected_revision=payload.expected_revision,
            idempotency_key=_idem_key(request),
        )
    except ProtocolDraftValidationError as exc:
        raise _unprocessable(exc.issues) from exc
    except DraftStoreNotFoundError as exc:
        raise ApiError(404, "Draft Not Found", str(exc)) from exc
    except DraftStoreConflictError as exc:
        raise ApiError(
            412,
            "Draft Revision Conflict",
            f"expected revision {exc.expected_revision}, current {exc.current_revision}",
        ) from exc
    response.headers["ETag"] = f'"{result.record.revision}"'
    response.headers["X-Draft-Replayed"] = "1" if result.replayed else "0"
    return _view_dto(result.record)


@router.delete("/protocol-drafts/{draft_id}", status_code=204)
async def delete_draft(draft_id: str, request: Request) -> None:
    """物理删除草稿与全部修订（G10，WP-B）。

    运行链不受影响：draft 启动 run 冻结的是启动时刻修订正文，Manifest 不
    依赖草稿存续；删除后 draft 深链 404 是正确态。
    """
    service = draft_service_of(request)
    if not service.delete(draft_id):
        raise ApiError(404, "Draft Not Found", f"protocol draft not found: {draft_id}")


def resolve_draft_revision(service: DraftService, ref: ProtocolDraftRunRefDto) -> str:
    """运行入口使用的精确修订解析：返回该修订的 YAML 文本。

    不可变性保证：一旦运行启动，草稿后续变化不改写已冻结运行。
    """
    revision = service.get_revision(ref.draft_id, ref.revision)
    if revision is None:
        raise ApiError(
            404,
            "Draft Revision Not Found",
            f"revision not found: {ref.draft_id}@{ref.revision}",
        )
    return revision.yaml_text


def _view_dto(record: ProtocolDraftRecord) -> ProtocolDraftViewDto:
    return ProtocolDraftViewDto(
        draft_id=record.draft_id,
        project_id=record.project_id,
        name=record.name,
        revision=record.revision,
        yaml_text=record.yaml_text,
        source_digest=record.source_digest,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _unprocessable(issues: "tuple[DraftValidationIssue, ...]") -> ApiError:
    detail = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
    return ApiError(422, "Protocol Draft Invalid", detail)


def _idem_key(request: Request) -> str:
    key = request.headers.get("Idempotency-Key")
    if not key:
        raise ApiError(422, "Idempotency-Key Required", "mutating requests require Idempotency-Key")
    return key


def _require_if_match(request: Request, expected_revision: int) -> None:
    header = request.headers.get("If-Match")
    if header is None:
        raise ApiError(428, "Precondition Required", "If-Match header is required for save")
    stripped = header.strip().strip('"')
    if stripped != "*" and stripped != str(expected_revision):
        raise ApiError(
            412,
            "Precondition Failed",
            f"If-Match {stripped!r} does not match expected revision {expected_revision}",
        )
