"""ToolPack 供应链写面（GOAL-003 / EC-02：install / approve-update / revoke）。

```text
GET    /tool-packs                            已安装 pack（生效版本 + 待批准版本分开呈现）
POST   /tool-packs/install                    安装；同 id 无扩张 → 直接更新；扩张 → 待批准
POST   /tool-packs/{pack_id}/approve-update   应用待批准更新（此刻扩张才生效）
POST   /tool-packs/{pack_id}/revoke           终态吊销（reason 必填）
```

**被消费**：state=INSTALLED 的 pack 把 digest 合入 `CatalogSnapshot.tool_pack_digests`
（`catalog_merge`），于是同一份草稿协议的 preflight `SUPPLY_CHAIN_UNPINNED` 结论随
install / pending / revoke 改变——"写面被读面消费"在这里是可证伪的，不是声明。

诚实边界：store/policy/词表未装配 → 503；未知 pack → 404；终态再处置 / 无待批准更新
→ 409；平台自带 pack id 被占用 → 409；manifest 形状或内容 digest 不符、capability
不在平台词表、required 凭据非 TOOL 域 → 422；policy 拒绝 → 403。
控制面重算 digest 证明的是"提交内容与声明的 pin 自洽"，**不是**"pin 与上游实际交付物一致"
（后者需要远端取证，不在本层）。
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from packages.application.ports.errors import InvalidInputError, PermanentPortError
from packages.application.ports.tool_pack_store import ToolPackRecord
from packages.application.tool_plane.lifecycle import ToolPackLifecycle
from packages.domain.enums import FailureCategory, ToolPackState
from packages.domain.tools import ToolPackManifest, manifest_from_document
from services.api import tool_pack_support as support
from services.api.deps import get_deps
from services.api.dto.tool_packs import (
    ToolPackDto,
    ToolPackListDto,
    ToolPackRevokeDto,
    ToolPackSubmitDto,
    ToolPackSubmitResultDto,
)
from services.api.errors import ApiError

router = APIRouter(tags=["tool-packs"])


def _lifecycle(request: Request) -> ToolPackLifecycle:
    deps = get_deps(request)
    return ToolPackLifecycle(
        support.pack_store_of(deps),
        support.policy_of(deps),
        deps.events,
        actor="console",
    )


def _pack_dto(record: ToolPackRecord) -> ToolPackDto:
    """INSTALLED 才会把 digest 交给目录（PENDING 更新不贡献任何东西）。"""
    return support.pack_dto(record, catalog_active=record.state is ToolPackState.INSTALLED)


def _result_dto(record: ToolPackRecord, status: str) -> ToolPackSubmitResultDto:
    return ToolPackSubmitResultDto(status=status, pack=_pack_dto(record), note=support.PACK_NOTE)


def _translate(error: Exception) -> ApiError:
    """域/端口异常 → HTTP：内容不符 → 422，policy 拒绝 → 403，冲突 → 409，未知 → 404。

    注意 `InvalidInputError` 是 `PermanentPortError` 的子类，必须先判子类（否则
    "未知 pack" 会被当成"内容不符"返回 422）。
    """
    message = str(error)
    if isinstance(error, InvalidInputError):
        if "not installed" in message:
            return ApiError(404, "ToolPack Not Found", message)
        return ApiError(409, "ToolPack Conflict", message)
    if isinstance(error, PermanentPortError):
        if error.failure_category is FailureCategory.POLICY_DENIED:
            return ApiError(403, "ToolPack Policy Denied", message)
        return ApiError(422, "Invalid ToolPack Manifest", message)
    return ApiError(500, "ToolPack Failure", message)


def _manifest(payload: dict[str, object]) -> ToolPackManifest:
    """形状由域唯一定义（控制面不复制第二份 schema）；非法 → 422。"""
    try:
        return manifest_from_document(payload)
    except ValueError as exc:
        raise ApiError(422, "Invalid ToolPack Manifest", str(exc)) from exc


def _reject_unknown_capabilities(manifest: ToolPackManifest) -> None:
    unknown = support.load_capability_vocabulary().unknown(support.manifest_capabilities(manifest))
    if unknown:
        raise ApiError(
            422,
            "Unknown Capability",
            f"capabilities not in the platform vocabulary: {', '.join(unknown)}",
        )


@router.get("/tool-packs", response_model=ToolPackListDto)
def list_tool_packs(request: Request) -> ToolPackListDto:
    """已安装的 ToolPack：生效版本、待批准更新（若有）与"digest 是否进入目录"。"""
    deps = get_deps(request)
    if deps.tool_pack_store is None:
        return ToolPackListDto(
            packs=[],
            note=support.PACK_NOTE,
            unavailable_reason=support.STORE_UNAVAILABLE_REASON,
        )
    records = deps.tool_pack_store.snapshot()
    return ToolPackListDto(
        packs=[_pack_dto(record) for record in records.values()],
        note=support.PACK_NOTE,
    )


@router.post("/tool-packs/install", response_model=ToolPackSubmitResultDto, status_code=201)
def install_tool_pack(request: Request, body: ToolPackSubmitDto) -> ToolPackSubmitResultDto:
    """安装或提交 ToolPack 更新。

    控制面**重算** manifest 内容 digest 并要求与请求里的 `digest` 相等（不采信字面量），
    因此内容与 pin 不符 → 422；capability 不在平台词表 → 422 并点名；平台自带 pack id → 409。
    同 id 且内容相同 → `unchanged`（不改写任何东西）；同 id 且**扩张权限**
    （新增 capability / network domain / credential）→ `pending_approval`（**不生效**，
    需 `approve-update`）；无扩张的更新直接生效 → `updated`。
    """
    manifest = _manifest(body.manifest)
    _reject_unknown_capabilities(manifest)
    if manifest.id in support.builtin_pack_ids():
        raise ApiError(
            409,
            "Builtin ToolPack",
            f"pack id {manifest.id!r} is reserved by a platform-provided tool pack",
        )
    try:
        outcome = _lifecycle(request).submit(manifest)
    except (InvalidInputError, PermanentPortError) as exc:
        raise _translate(exc) from exc
    result = _result_dto(outcome.record, outcome.status)
    return result.model_copy(
        update={"diff": None if outcome.diff is None else support.diff_dto(outcome.diff)}
    )


@router.post("/tool-packs/{pack_id}/approve-update", response_model=ToolPackSubmitResultDto)
def approve_tool_pack_update(request: Request, pack_id: str) -> ToolPackSubmitResultDto:
    """批准待批准的权限扩张：此刻新版本才成为生效版本（此前目录里仍是旧 digest）。

    无待批准更新或已 REVOKED → 409；未知 pack → 404；policy 拒绝 → 403。
    """
    try:
        record = _lifecycle(request).approve_update(pack_id)
    except (InvalidInputError, PermanentPortError) as exc:
        raise _translate(exc) from exc
    return _result_dto(record, "updated")


@router.post("/tool-packs/{pack_id}/revoke", response_model=ToolPackSubmitResultDto)
def revoke_tool_pack(
    request: Request, pack_id: str, body: ToolPackRevokeDto
) -> ToolPackSubmitResultDto:
    """终态吊销：digest 退出目录（供应链检查重新报警）、待批准更新清空。

    已 REVOKED → 409（终态不可重复处置）；未知 pack → 404；reason 必填（缺 → 422）。
    """
    try:
        record = _lifecycle(request).revoke(pack_id, body.reason)
    except (InvalidInputError, PermanentPortError) as exc:
        raise _translate(exc) from exc
    return _result_dto(record, "revoked")
