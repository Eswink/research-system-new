"""执行基质读面的 HTTP 形状（GOAL-007 cycle 4 = EC-04）。

事实来源是**冻结的 `manifest.frozen` 事件**（canonical outbox）：manifest 实体不落库
（run 行只有 digest），因此读面回读事件 payload 而不是另存一份基质字段——不新增迁移、
不让「读面说的」与「事件里记的」有机会分叉（AGENTS.md §4 要消灭的正是这种漂移）。

未冻结的 run ⇒ 两个字段都是 `None`，语义与既有的 `manifest_digest` 一致：**未声明**，
不得读作某一个具体执行体。
"""

from __future__ import annotations

from typing import Any

from packages.application.ports import RunProjection
from packages.domain.events import EventType
from services.api.dto.runs import RunExecutionDto, RuntimeFingerprintDto

_SUBSTRATE_KEY = "execution_backend"
_FINGERPRINT_KEY = "runtime_fingerprint"


def _frozen_payload(projection: RunProjection, run_id: str) -> dict[str, Any]:
    """该 run 的冻结 payload（没有 `manifest.frozen` ⇒ 空 dict）。"""
    for envelope in projection.events(run_id):
        if envelope.event_type is EventType.MANIFEST_FROZEN:
            return dict(envelope.payload)
    return {}


def run_execution_dto(projection: RunProjection, run_id: str) -> RunExecutionDto | None:
    """run 行 + 冻结事件 → 执行体读面；**未冻结 ⇒ `None`**。

    `None`（未冻结）与「冻结了但没声明执行体」（`execution_backend is None`）是两件事，
    读面必须分得开：前者是「这次运行还没有冻结快照」，后者是「冻结时没声明」。

    指纹同理：冻结 payload 里的**空记录**（`{}`）是「冻结时未声明该面」，读面报 `None`；
    不是「有一条状态待读」——把 `{}` 当记录会让读面要么崩、要么编出一个空状态。
    """
    payload = _frozen_payload(projection, run_id)
    if not payload:
        return None
    fingerprint = payload.get(_FINGERPRINT_KEY)
    record = (
        RuntimeFingerprintDto(**fingerprint)
        if isinstance(fingerprint, dict) and fingerprint
        else None
    )
    return RunExecutionDto(
        execution_backend=payload.get(_SUBSTRATE_KEY), runtime_fingerprint=record
    )
