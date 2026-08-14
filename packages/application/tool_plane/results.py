"""大型 Tool Result 的 Artifact indirection（TOOL_RUNTIME.md §7）。

阈值分流：payload 超过阈值时写入 ArtifactStore（内容寻址），
ToolResultRecord 只携带 output_digest 与引用；小结果直接 digest 化，
不额外落盘。大结果永不进入 Domain JSON 或模型上下文。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports.artifact_store import ArtifactStore
from packages.domain.artifacts import Artifact, verify_artifact_content
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import ArtifactState, ToolResultStatus
from packages.domain.tools import ToolCallRecord, ToolResultRecord

DEFAULT_SPILL_THRESHOLD_BYTES = 32 * 1024
MEDIA_TYPE_JSON = "application/json"


@dataclass(frozen=True, slots=True)
class ToolOutputResult:
    record: ToolResultRecord
    spilled: bool
    artifact_ref: str | None = None


def _artifact_id(call: ToolCallRecord) -> str:
    return f"tool-result:{call.task_id}:{call.operation_key}:{call.tool_id}"


def _result_record(
    call: ToolCallRecord,
    output_digest: Digest,
) -> ToolResultRecord:
    return ToolResultRecord(
        task_id=call.task_id,
        attempt=call.attempt,
        operation_key=call.operation_key,
        tool_id=call.tool_id,
        status=ToolResultStatus.SUCCEEDED,
        output_digest=output_digest,
        recorded_at=Timestamp.now(),
    )


def spill_large_result(
    store: ArtifactStore,
    call: ToolCallRecord,
    payload: bytes,
    threshold_bytes: int = DEFAULT_SPILL_THRESHOLD_BYTES,
) -> ToolOutputResult:
    """payload 超阈值时写 Artifact 并返回 reference；否则只返回 digest。"""
    if threshold_bytes < 1:
        raise ValueError("threshold_bytes must be >= 1")
    digest = Digest.of_bytes(payload)
    if len(payload) <= threshold_bytes:
        return ToolOutputResult(record=_result_record(call, digest), spilled=False)
    artifact = Artifact(
        id=_artifact_id(call),
        digest=digest,
        size_bytes=len(payload),
        media_type=MEDIA_TYPE_JSON,
        created_by=f"tool:{call.tool_id}",
        classification="tool-result",
    )
    if not verify_artifact_content(artifact, payload):
        raise ValueError("artifact digest mismatch")
    store.put(artifact, payload)
    store.mark(artifact.id, ArtifactState.VERIFIED)
    return ToolOutputResult(
        record=_result_record(call, digest),
        spilled=True,
        artifact_ref=artifact.id,
    )


def fetch_spilled_result(
    store: ArtifactStore,
    record: ToolResultRecord,
) -> bytes | None:
    """按 record 的 output_digest 取回溢出内容（校验内容寻址）。"""
    if record.output_digest is None:
        return None
    artifact_id = f"tool-result:{record.task_id}:{record.operation_key}:{record.tool_id}"
    content = store.get(artifact_id)
    if Digest.of_bytes(content) != record.output_digest:
        raise ValueError("spilled result digest mismatch")
    return content
