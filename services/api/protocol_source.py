"""协议来源解析（WP-B）：path 与不可变草稿修订引用二选一。

runs 与 team_protocol 共用同一加载语义（先于本模块在 routers/runs.py 内
私有实现），保证 Compile → Preflight → Freeze 链对两种来源完全同源。
错误语义：二者同给 → 422；缺一 → 422；草稿服务缺失 → 503；
修订不存在 → 404；正文非法 → 422。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from packages.domain.protocol_source import ProtocolSource
from services.api.catalog import load_protocol_definition
from services.api.errors import ApiError

if TYPE_CHECKING:
    from packages.domain.protocols import ProtocolDefinition
    from services.api.composition import ApiDeps


def draft_ref_of(
    draft_id: str | None,
    draft_revision: int | None,
) -> tuple[str, int] | None:
    """从 DTO 字段构建草稿引用；任一给出即要求二者齐全。"""
    if draft_id is None and draft_revision is None:
        return None
    if draft_id is None or draft_revision is None:
        raise ApiError(
            422,
            "Incomplete Draft Reference",
            "draft_id and draft_revision are both required",
        )
    return draft_id, draft_revision


def load_protocol_for_source(
    deps: ApiDeps,
    protocol_path: str | None,
    draft_ref: tuple[str, int] | None,
) -> ProtocolDefinition:
    """协议解析：草稿修订引用优先；二者互斥；缺一报 422。"""
    if draft_ref is not None and protocol_path:
        raise ApiError(422, "Ambiguous Protocol Source", "provide either path or draft revision")
    if draft_ref is not None:
        return _load_draft_revision(deps, draft_ref)
    if not protocol_path:
        raise ApiError(422, "Protocol Source Required", "protocol_path or draft ref required")
    loaded: ProtocolDefinition = load_protocol_definition(protocol_path)
    return loaded


def protocol_source_of(
    protocol_path: str | None,
    draft_ref: tuple[str, int] | None,
) -> ProtocolSource:
    """把已校验的来源参数落成领域值对象（与 `load_protocol_for_source` 同判据）。

    GOAL-003 cycle 20：run 行要记住"这份 run 用哪份协议装配"，重启后的续跑才有
    重建入口；判据与解析链一致（二者互斥、缺一报 422），不在这里放宽任何一条。
    """
    if draft_ref is not None and protocol_path:
        raise ApiError(422, "Ambiguous Protocol Source", "provide either path or draft revision")
    if draft_ref is not None:
        return ProtocolSource(draft_id=draft_ref[0], draft_revision=draft_ref[1])
    if not protocol_path:
        raise ApiError(422, "Protocol Source Required", "protocol_path or draft ref required")
    return ProtocolSource(protocol_path=protocol_path)


def _load_draft_revision(deps: ApiDeps, draft_ref: tuple[str, int]) -> ProtocolDefinition:
    draft_id, revision = draft_ref
    if deps.protocol_draft_service is None:
        raise ApiError(503, "Draft Service Unavailable", "protocol draft service not configured")
    revision_view = deps.protocol_draft_service.get_revision(draft_id, revision)
    if revision_view is None:
        raise ApiError(404, "Draft Revision Not Found", f"{draft_id}@{revision}")
    try:
        built = deps.protocol_draft_service.load_protocol(revision_view.yaml_text)
    except ValueError as exc:
        raise ApiError(422, "Protocol Invalid", str(exc)) from exc
    protocol: ProtocolDefinition = built
    return protocol
