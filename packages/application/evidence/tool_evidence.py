"""ToolResult → Source → Evidence 正式准入（M12-R1 WP2）。

边界（AGENTS.md §1 / M8 Tool Plane / M10 治理链）：
- ToolResult != Evidence。工具输出只携带 digest（ToolResultRecord.output_digest），
  内容经 ArtifactStore 持久化；任何工具结果都不能直接成为可信 Evidence。
- 正式准入路径：ToolResult（已 spill 的 artifact）→ 登记
  SourceRecord(origin="tool:{tool_id}:{task_id}:{operation_key}", trust_label=由调用方
  按 provider 声明性质给值——外部取回 ⇒ `RETRIEVED`，否则 `GENERATED`；GOAL-011 EC-02)
  → 依据 artifact 内容构造 Evidence（content_digest=artifact digest，
  绑定 run_id / tool_refs / manifest_digest）→ EvidenceLedger.register_evidence。
- 防绕过：本模块是工具证据的**唯一**登记入口；未先登记 Source 的
  Evidence 无法通过本模块（provenance 前置）。VERIFIED Claim 的
  provenance 不变量由 EvidenceLedger 登记面进一步强制（M10 复审强化）。

调用方必须提供真实运行事实（run_id / manifest_digest / tool 标识），
禁止使用手工常量或 fixture 伪造内容。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import ToolResultStatus, TrustLabel
from packages.domain.evidence import Evidence, SourceRecord
from packages.domain.tools import ToolResultRecord


@dataclass(frozen=True, slots=True)
class ToolEvidenceInput:
    """一次工具结果准入的输入（参数对象，避免函数参数超限）。

    `trust_label` 是**来源性质**的**唯一**盖章点（GOAL-011 EC-02）：
    - 内容取自**系统之外**（provider 声明了 `network_domains`，调用真的打到那个域）
      ⇒ `TrustLabel.RETRIEVED`；
    - 其他（缺省）⇒ `TrustLabel.GENERATED`：**不**自称「系统取得」。
    由调用方按 provider 的**声明性质**给值——本模块不猜，读面/验收门也不在别处再推一次。
    """

    result: ToolResultRecord
    run_id: str
    manifest_digest: str | None = None
    evidence_id: str | None = None
    tool_refs: tuple[str, ...] = field(default_factory=tuple)
    extracted_by: str = "system:m12-tool-evidence"
    trust_label: TrustLabel = TrustLabel.GENERATED


def source_origin_for(result: ToolResultRecord) -> str:
    """工具结果 SourceRecord 的稳定 origin 命名。"""
    return f"tool:{result.tool_id}:{result.task_id}:{result.operation_key}"


def register_tool_evidence(
    ledger: EvidenceLedger,
    artifacts: ArtifactStore,
    *,
    input: ToolEvidenceInput,
) -> tuple[SourceRecord, Evidence]:
    """ToolResult（已 spill）→ SourceRecord → Evidence 全链登记。

    校验：
    - 工具结果必须成功（非 SUCCEEDED 无输出可采信为证据）；
    - 内容必须已 spill 到 ArtifactStore 且 digest 校验通过（内容寻址）；
    - SourceRecord 以本模块命名登记（provenance 前置，任何调用方不得
      绕过本入口直接构造 Evidence）。
    """
    result = input.result
    if result.status is not ToolResultStatus.SUCCEEDED:
        raise ValueError(
            f"cannot admit tool result {result.operation_key} with status {result.status.value}"
        )
    if result.output_digest is None:
        raise ValueError("tool result has no output digest; nothing to admit")
    artifact_id = _spilled_artifact_id(result)
    content = artifacts.get(artifact_id)
    if Digest.of_bytes(content) != result.output_digest:
        raise ValueError("spilled tool result digest mismatch; content tampered")
    origin = source_origin_for(result)
    source = SourceRecord(
        origin=origin,
        content_digest=str(result.output_digest),
        trust_label=input.trust_label,
        access_time=Timestamp.now(),
        parser_version="m12-tool-evidence-v1",
    )
    ledger.register_source(source)
    evidence = Evidence(
        id=input.evidence_id or f"evidence:{input.run_id}:{result.operation_key}",
        source_ref=origin,
        content_digest=str(result.output_digest),
        extracted_by=input.extracted_by,
        captured_at=Timestamp.now(),
        artifact_id=artifact_id,
        run_id=input.run_id,
        tool_refs=input.tool_refs or (result.tool_id,),
        manifest_digest=input.manifest_digest,
    )
    ledger.register_evidence(evidence)
    return source, evidence


def _spilled_artifact_id(result: ToolResultRecord) -> str:
    return f"tool-result:{result.task_id}:{result.operation_key}:{result.tool_id}"


__all__ = [
    "ToolEvidenceInput",
    "register_tool_evidence",
    "source_origin_for",
]
