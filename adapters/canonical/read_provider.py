"""Canonical 读面 ToolProvider：把 PG/域实体（canonical state）接成**可执行**的工具。

**它解决什么**：`examples/config/tool_providers.yaml` 声明了两件 NATIVE provider
（`m12_artifact`：`artifact.read` / `artifact.write` / `evidence.read` / `evidence.write`；
`openhands_workspace`：`workspace.read` / …），但**全仓没有任何实现**
（只有 `FakeToolProvider` 与两个 REST adapter）⇒ 声明了能力却没有可执行的承接面。
本模块补上**读面**那一半：把 canonical 里**已经有**的数据（ArtifactStore 的制品、
EvidenceLedger 的 claim/evidence/relation）接成真去读的 provider。

**为什么读面先做**（GOAL-029 的 A 组口径）：数据都在 canonical（PostgreSQL Domain Entity
是业务真相，AGENTS.md §6），读它**零新增外部依赖、零凭据、零许可风险**；写面要动
canonical 路径属另一类决定。

**边界**：
- 参数经 `tool-args` 制品传递（与 `ncbi` / `europe_pmc` / MCP 同一口径；provider 按
  `argument_digest` 重算校验，防篡改）——本模块不新开一条参数通道。
- 结果经 `spill_large_result` 落 ArtifactStore（TOOL_RUNTIME.md §7 的阈值分流）。
- **不**判定能力是否被允许（那是 `execute_tool_call` 的策略面）；本模块只执行。
- **不**编造数据：读不到就按未知 id 点名拒绝（不返回空壳冒充"查到了但没内容"）。
"""

from __future__ import annotations

import json
from collections.abc import Mapping

from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.tool_plane.results import spill_large_result
from packages.domain.core import Digest
from packages.domain.enums import ProviderType
from packages.domain.tools import (
    ToolCallRecord,
    ToolHealthReport,
    ToolProviderSpec,
    ToolResultRecord,
    ToolSpec,
)

ARGS_ARTIFACT_PREFIX = "tool-args:"

#: provider 侧 tool id → (能力名, 说明)。**能力的名字空间是能力名**（与 `policy.yaml` 同源）。
_TOOL_DESCRIPTIONS: dict[str, str] = {
    "artifact_read": "Read an artifact (metadata + content) from the canonical artifact store.",
    "evidence_read": "Read claims / evidence / relations for a run from the canonical ledger.",
    "workspace_read": "Read the canonical workspace/run view exposed to the session.",
}


def tool_ids() -> list[str]:
    """声明的工具 id（排序后，供 schema digest 稳定复用）。"""
    return sorted(_TOOL_DESCRIPTIONS)


def describe_tools(
    provider: ToolProviderSpec, *, capabilities: Mapping[str, str]
) -> tuple[ToolSpec, ...]:
    """把声明的工具面映射成 `ToolSpec` 元组（与 `ncbi.py::list_tools` 同形）。

    `capabilities` 给每个 tool id 对应的**能力名**（本 provider 的若干工具可能承载不同能力，
    如 `artifact_read` → `artifact.read`、`evidence_read` → `evidence.read`）。
    """
    return tuple(
        ToolSpec(
            id=tool_id,
            name=tool_id,
            effect_class=provider.effect_class,
            provider_kind=ProviderType.NATIVE,
            capabilities=[capabilities[tool_id]] if tool_id in capabilities else [],
            description=description,
        )
        for tool_id, description in _TOOL_DESCRIPTIONS.items()
    )


class CanonicalReadProvider:
    """canonical 读面（ArtifactStore + EvidenceLedger）的 ToolProvider 实现。

    **只读**：本实现的 `execute` 不写任何 store（除参数/结果制品外）——
    能力集合由 `ToolProviderSpec` 声明，运行期语义由 `execute_tool_call` 的策略面约束。
    """

    def __init__(
        self,
        artifacts: ArtifactStore,
        ledger: EvidenceLedger | None = None,
        *,
        spill_threshold_bytes: int = 1,
    ) -> None:
        """构造读面 provider。

        `spill_threshold_bytes` **默认 1**（即「内容必须可取回」），不是 `spill_large_result`
        的 32 KiB 缺省 —— 理由是**消费者的要求**，与运行链同一条：

        - 会话工具桥（`adapters/openhands/session_tool_invocation.py`）**必须把内容交回模型**，
          因此结果必须落在 ArtifactStore 里可被 `fetch_spilled_result` 取回；
        - 低于阈值的结果**不落盘**（`spill_large_result` 只返回 digest）⇒ 桥拿不到内容，
          只能点名拒绝（`produced no spilled output`）—— 实测：默认阈值下**任何**小于
          32 KiB 的读结果都会走到这条失败路径，而那正是绝大多数读。
        - 同一约定在运行链侧的既有表述：`tests/e2e/literature_chain_support.py` 的
          `spill_threshold_bytes=1`（"运行链证据要求内容在场（准入会重算 digest）"）。

        「大结果不进模型上下文」的治理目标由**调用方**（会话工具面的返回长度、
        运行链的 chaining 语义）承担，不由本阈值承担 —— 在这里省掉落盘只会让工具**不可用**。
        """
        self._artifacts = artifacts
        self._ledger = ledger
        self._spill_threshold = spill_threshold_bytes

    def execute(self, provider: ToolProviderSpec, call: ToolCallRecord) -> ToolResultRecord:
        args = self._read_args(call)
        handler = {
            "artifact_read": self._artifact_read,
            "evidence_read": self._evidence_read,
            "workspace_read": self._workspace_read,
        }.get(call.tool_id)
        if handler is None:
            raise InvalidInputError(f"unknown tool id: {call.tool_id}")
        return self._to_record(call, handler(args))

    def list_tools(self, provider: ToolProviderSpec) -> tuple[ToolSpec, ...]:
        declared = set(provider.capabilities)
        capability_of = {
            tool_id: capability
            for tool_id, capability in (
                ("artifact_read", "artifact.read"),
                ("evidence_read", "evidence.read"),
                ("workspace_read", "workspace.read"),
            )
            if capability in declared
        }
        return describe_tools(provider, capabilities=capability_of)

    def check_health(self, provider: ToolProviderSpec) -> ToolHealthReport:
        """NATIVE 无外部传输可探测 ⇒ 结构性可用（与 `preflight_support` 同一口径）。

        `evidence_read` 需要 ledger：ledger 缺失时该工具**不可用**，如实报
        `UNKNOWN` 并点名缺的是什么（不伪装健康）。
        """
        from packages.domain.enums import EndpointHealth

        if self._ledger is None:
            return ToolHealthReport(
                provider_id=provider.id,
                status=EndpointHealth.UNKNOWN,
                detail="evidence_read unavailable: no EvidenceLedger in this assembly",
            )
        return ToolHealthReport(
            provider_id=provider.id,
            status=EndpointHealth.HEALTHY,
            detail="NATIVE provider：canonical store 就在进程内，无外部 transport 可探测",
        )

    # --- 工具实现 ---------------------------------------------------------------

    def _artifact_read(self, args: dict[str, object]) -> dict[str, object]:
        """读一个 artifact：元数据 + 内容（未知 id ⇒ 点名拒绝，不返回空壳）。"""
        artifact_id = str(args.get("artifact_id") or "").strip()
        if not artifact_id:
            raise InvalidInputError("artifact_read requires a non-empty artifact_id")
        meta = self._artifacts.meta(artifact_id)
        if meta is None:
            raise InvalidInputError(f"artifact {artifact_id!r} is not in the canonical store")
        raw = self._artifacts.get(artifact_id)
        media_type = str(meta.media_type)
        content: object
        if media_type.startswith("text/") or media_type.endswith("json"):
            try:
                parsed: object = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                content = raw.decode("utf-8", errors="replace")
            else:
                content = parsed
        else:
            content = {"content_base64": __import__("base64").b64encode(raw).decode("ascii")}
        return {
            "artifact_id": artifact_id,
            "digest": str(meta.digest),
            "size_bytes": meta.size_bytes,
            "media_type": media_type,
            "created_by": meta.created_by,
            "content": content,
        }

    def _evidence_read(self, args: dict[str, object]) -> dict[str, object]:
        """读 run 的 claim/evidence/relation 投影（`services/api/run_evidence` 同一口径）。

        只 register 不 attach_relation 的证据**不会**出现在这里 —— 这正是
        `MEM: evidence-read-face-claim-relation` 的口径：读面按 relation 投影，
        不看「登记过什么」。

        **run 归属判定在 evidence 一侧**：`Claim` 域类型没有 `run_id` 字段
        （claim 是全局命题，run 是证据的采集上下文）⇒ 本投影按
        `Evidence.run_id == run_id` 筛选，只保留**引用到本 run 证据**的 claim。
        """
        if self._ledger is None:
            raise InvalidInputError(
                "evidence_read requires an EvidenceLedger, which is not in this assembly"
            )
        run_id = str(args.get("run_id") or "").strip()
        if not run_id:
            raise InvalidInputError("evidence_read requires a non-empty run_id")
        claims: list[dict[str, object]] = []
        evidence: list[dict[str, object]] = []
        seen: set[str] = set()
        for claim in self._ledger.claims():
            matched: list[str] = []
            for relation in self._ledger.relations_for_claim(claim.id):
                try:
                    item = self._ledger.get_evidence(relation.evidence_id)
                except Exception:  # noqa: BLE001 - 引用可能已删除（视觉态：missing evidence）
                    continue
                if item.run_id != run_id:
                    continue
                matched.append(relation.evidence_id)
                if relation.evidence_id in seen:
                    continue
                seen.add(relation.evidence_id)
                evidence.append({
                    "id": item.id,
                    "source_ref": item.source_ref,
                    "content_digest": item.content_digest,
                    "relation": str(relation.relation),
                })
            if matched:
                claims.append({
                    "id": claim.id,
                    "status": str(claim.status),
                    "evidence_ids": sorted(matched),
                })
        return {
            "run_id": run_id,
            "claims": sorted(claims, key=lambda item: str(item["id"])),
            "evidence": sorted(evidence, key=lambda item: str(item["id"])),
        }

    def _workspace_read(self, args: dict[str, object]) -> dict[str, object]:
        """读 canonical 的 run/工作区视图（当前是 run 的存续事实，不含文件内容）。

        文件内容属 `openhands_workspace` 的**写**面（要 lease），不在本读面内 ——
        本工具如实返回「工作区读面今天有什么」，不冒充文件系统。
        """
        run_id = str(args.get("run_id") or "").strip()
        if not run_id:
            raise InvalidInputError("workspace_read requires a non-empty run_id")
        artifacts = [
            {"id": meta.id, "digest": str(meta.digest), "media_type": meta.media_type}
            for meta in self._artifacts.list_refs()
            if meta.id.startswith(f"{run_id}:")
        ]
        return {"run_id": run_id, "artifacts": sorted(artifacts, key=lambda item: str(item["id"]))}

    # --- 公共骨架 ---------------------------------------------------------------

    def _read_args(self, call: ToolCallRecord) -> dict[str, object]:
        artifact_id = f"{ARGS_ARTIFACT_PREFIX}{call.task_id}:{call.operation_key}"
        try:
            content = self._artifacts.get(artifact_id)
        except Exception as exc:  # noqa: BLE001 - 未知制品按 args 缺失收敛
            raise InvalidInputError(f"tool args missing for {call.operation_key}") from exc
        if Digest.of_bytes(content) != call.argument_digest:
            raise InvalidInputError("tool args digest mismatch")
        parsed = json.loads(content.decode("utf-8"))
        if not isinstance(parsed, dict):
            raise InvalidInputError("tool args must be a JSON object")
        return parsed

    def _to_record(self, call: ToolCallRecord, payload: dict[str, object]) -> ToolResultRecord:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return spill_large_result(
            self._artifacts, call, raw, threshold_bytes=self._spill_threshold
        ).record


__all__ = [
    "ARGS_ARTIFACT_PREFIX",
    "CanonicalReadProvider",
    "describe_tools",
    "tool_ids",
]
