"""执行基质读面的 HTTP 形状（GOAL-007 cycle 4 = EC-04；GOAL-010 EC-04 加实测合并）。

事实来源是**冻结的 `manifest.frozen` 事件**（canonical outbox）：manifest 实体不落库
（run 行只有 digest），因此读面回读事件 payload 而不是另存一份基质字段——不新增迁移、
不让「读面说的」与「事件里记的」有机会分叉（AGENTS.md §4 要消灭的正是这种漂移）。

GOAL-010 EC-04 的补充：指纹四要素（返回 model 名 / 端点头 / probe 版本 / 兼容性结论）
**只在一次真实调用之后**才存在，而 manifest 冻结在调用**之前** ⇒ 它们落在一条**调用后**
的 canonical 事实里（`model.probed`，见 `run_orchestration.runtime_fingerprint`）。
读面把两份事实合并呈现，并**标明是哪一份**（`source`）：冻结占位不可变、也不被覆写，
实测记录只覆盖呈现。取「最近一次」`model.probed`——run 可以续跑后再次收敛，后落的
事实更完整；事件链顺序即时间序。

未冻结的 run ⇒ 两个字段都是 `None`，语义与既有的 `manifest_digest` 一致：**未声明**，
不得读作某一个具体执行体。
"""

from __future__ import annotations

from typing import Any

from packages.application.ports import RunProjection
from packages.domain.events import EventType
from services.api.dto.runs import (
    FINGERPRINT_ELEMENT_FIELDS,
    FINGERPRINT_SOURCE_FROZEN,
    FINGERPRINT_SOURCE_OBSERVED,
    RunExecutionDto,
    RuntimeFingerprintDto,
)

_SUBSTRATE_KEY = "execution_backend"
_FINGERPRINT_KEY = "runtime_fingerprint"
_VERDICT_KEY = "verdict"
_MISSING_KEY = "missing_fields"
_NOT_VERIFIED = "NOT_VERIFIED"


def _text(value: object) -> str | None:
    """非字符串 / 空串 ⇒ `None`（读面不把空值当成一个值）。"""
    return value if isinstance(value, str) and value else None


def _frozen_payload(projection: RunProjection, run_id: str) -> dict[str, Any]:
    """该 run 的冻结 payload（没有 `manifest.frozen` ⇒ 空 dict）。"""
    for envelope in projection.events(run_id):
        if envelope.event_type is EventType.MANIFEST_FROZEN:
            return dict(envelope.payload)
    return {}


def _measured_payload(projection: RunProjection, run_id: str) -> dict[str, Any] | None:
    """该 run **最近一次**落下的实测指纹（`model.probed` payload）；没有 ⇒ `None`。"""
    measured: dict[str, Any] | None = None
    for envelope in projection.events(run_id):
        if envelope.event_type is EventType.MODEL_PROBED:
            measured = dict(envelope.payload)
    return measured


def _observed_identifiers(measured: dict[str, Any]) -> list[str]:
    """实测记录里的观测 model 名集合（只收非空字符串，去重、排序）。"""
    raw = measured.get("observed_model_identifiers")
    if not isinstance(raw, (list, tuple)):
        return []
    return sorted({name for name in raw if isinstance(name, str) and name})


def _missing(measured: dict[str, Any], empty: list[str]) -> list[str]:
    """缺项 = 读面呈现为空的那几项 ∪ 记录自报的缺项（只增不减，**不隐藏缺口**）。"""
    reported = measured.get(_MISSING_KEY)
    names = (
        {name for name in reported if isinstance(name, str)}
        if isinstance(reported, (list, tuple))
        else set()
    )
    return sorted(names | set(empty))


def _observed_dto(
    placeholder: dict[str, Any] | None, measured: dict[str, Any]
) -> RuntimeFingerprintDto:
    """实测记录 → 读面；四要素逐项取，取不到就留在 `missing_fields` 里点名。"""
    values = {name: _text(measured.get(name)) for name in FINGERPRINT_ELEMENT_FIELDS}
    return RuntimeFingerprintDto(
        status=_text(measured.get(_VERDICT_KEY)) or _NOT_VERIFIED,
        substrate=_text(placeholder.get("substrate")) if placeholder else None,
        reason=_text(measured.get("reason")),
        source=FINGERPRINT_SOURCE_OBSERVED,
        observed_model_identifiers=_observed_identifiers(measured),
        missing_fields=_missing(measured, [n for n, v in values.items() if v is None]),
        **values,
    )


def _placeholder_dto(placeholder: dict[str, Any]) -> RuntimeFingerprintDto:
    """冻结占位 → 读面：它**不带任何指纹值**，所以四要素全点名（有序，便于比对）。"""
    return RuntimeFingerprintDto(
        status=_text(placeholder.get("status")) or _NOT_VERIFIED,
        substrate=_text(placeholder.get("substrate")),
        reason=_text(placeholder.get("reason")),
        source=FINGERPRINT_SOURCE_FROZEN,
        missing_fields=sorted(FINGERPRINT_ELEMENT_FIELDS),
    )


def run_execution_dto(projection: RunProjection, run_id: str) -> RunExecutionDto | None:
    """run 行 + 冻结事件 + 实测事件 → 执行体读面；**未冻结 ⇒ `None`**。

    `None`（未冻结）与「冻结了但没声明执行体」（`execution_backend is None`）是两件事，
    读面必须分得开：前者是「这次运行还没有冻结快照」，后者是「冻结时没声明」。

    指纹同理：冻结 payload 里的**空记录**（`{}`）是「冻结时未声明该面」，读面报 `None`；
    不是「有一条状态待读」——把 `{}` 当记录会让读面要么崩、要么编出一个空状态。
    既无占位又无实测记录 ⇒ 指纹仍是 `None`；只有占位 ⇒ 冻结占位读面（有缺口点名）。
    """
    payload = _frozen_payload(projection, run_id)
    if not payload:
        return None
    fingerprint = payload.get(_FINGERPRINT_KEY)
    placeholder = fingerprint if isinstance(fingerprint, dict) and fingerprint else None
    measured = _measured_payload(projection, run_id)
    record: RuntimeFingerprintDto | None
    if measured is not None:
        record = _observed_dto(placeholder, measured)
    else:
        record = _placeholder_dto(placeholder) if placeholder is not None else None
    return RunExecutionDto(
        execution_backend=payload.get(_SUBSTRATE_KEY), runtime_fingerprint=record
    )
