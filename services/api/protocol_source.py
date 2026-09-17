"""协议来源解析（WP-B）：path 与不可变草稿修订引用二选一。

runs 与 team_protocol 共用同一加载语义（先于本模块在 routers/runs.py 内
私有实现），保证 Compile → Preflight → Freeze 链对两种来源完全同源。
错误语义：二者同给 → 422；缺一 → 422；草稿服务缺失 → 503；
修订不存在 → 404；正文非法 → 422。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from adapters.contracts.protocol_text_loader import load_protocol_from_text
from packages.domain.protocol_source import ProtocolBody, ProtocolSource
from services.api.catalog import load_protocol_definition, read_protocol_text
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


def load_protocol_with_body(
    deps: ApiDeps,
    protocol_path: str | None,
    draft_ref: tuple[str, int] | None,
) -> tuple[ProtocolDefinition, ProtocolBody]:
    """解析协议**并冻结其正文**（GOAL-004 cycle 1）。

    与 `load_protocol_for_source` 同一判据（互斥 / 缺一 422 / 草稿 503/404/422），
    区别只有一个：解析与冻结取自**同一份字节**——路径来源读文本一次再从该文本解析；
    草稿来源用修订正文（就是被解析的那段）。冻结正文随 run 落 canonical，重启续跑
    因此不再依赖那份外部文件仍在。
    """
    if draft_ref is not None and protocol_path:
        raise ApiError(422, "Ambiguous Protocol Source", "provide either path or draft revision")
    if draft_ref is not None:
        text = _draft_revision_text(deps, draft_ref)
        return _parse_draft_text(deps, text), ProtocolBody.of(text)
    if not protocol_path:
        raise ApiError(422, "Protocol Source Required", "protocol_path or draft ref required")
    text = read_protocol_text(protocol_path)
    return _parse_protocol_text(text), ProtocolBody.of(text)


def parse_frozen_protocol(body: ProtocolBody) -> ProtocolDefinition:
    """冻结正文 → ProtocolDefinition（不触碰文件系统/草稿库）。

    重建路径用它：正文是 run 自己记得的那份字节，解析失败一律 422，不静默换一份。
    正文自洽 ≠ 语义未漂移——plan/catalog/契约仍要过 `assert_semantics_frozen`。
    """
    return _parse_protocol_text(body.text)


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
    return _parse_draft_text(deps, _draft_revision_text(deps, draft_ref))


def _draft_revision_text(deps: ApiDeps, draft_ref: tuple[str, int]) -> str:
    """不可变修订的正文（503/404 语义与解析链一致）。"""
    draft_id, revision = draft_ref
    if deps.protocol_draft_service is None:
        raise ApiError(503, "Draft Service Unavailable", "protocol draft service not configured")
    revision_view = deps.protocol_draft_service.get_revision(draft_id, revision)
    if revision_view is None:
        raise ApiError(404, "Draft Revision Not Found", f"{draft_id}@{revision}")
    text: str = revision_view.yaml_text
    return text


def _parse_draft_text(deps: ApiDeps, text: str) -> ProtocolDefinition:
    service = deps.protocol_draft_service
    if service is None:  # 防御：调用方先经 _draft_revision_text 校验（503）
        raise ApiError(503, "Draft Service Unavailable", "protocol draft service not configured")
    try:
        built = service.load_protocol(text)
    except ValueError as exc:
        raise ApiError(422, "Protocol Invalid", str(exc)) from exc
    protocol: ProtocolDefinition = built
    return protocol


def _parse_protocol_text(text: str) -> ProtocolDefinition:
    """协议正文 → ProtocolDefinition（与草稿修订同一条 Text→Domain 链）。"""
    try:
        return load_protocol_from_text(text)
    except ValueError as exc:
        raise ApiError(422, "Protocol Invalid", str(exc)) from exc
