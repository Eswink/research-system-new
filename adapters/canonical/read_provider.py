"""Canonical 读面 ToolProvider：把 canonical state（PG 域实体）接成**可执行**的工具。

**它解决什么**：`examples/config/tool_providers.yaml` 声明了 NATIVE provider 的读能力
（`artifact.read` / `evidence.read` / `workspace.read` / `budget.read` / `deliverable.read` /
`claim.read` / `experiment.read` / `experiment_plan.read`），但**全仓没有实现**
（只有 `FakeToolProvider` 与两个 REST adapter）⇒ 声明了能力却没有可执行的承接面。
本模块补上**读面**：把 canonical 里**已经有**的数据接成真去读的 provider。
**为什么读面先做**：数据都在 canonical（AGENTS.md §6），读它零新增依赖、零凭据、零许可风险。

**边界**：参数经 `tool-args` 制品传递（与 `ncbi` / MCP 同口径，`argument_digest` 重算校验）；
结果经 `spill_large_result` 落盘；**不**判定能力是否被允许（那是策略面）；**不**编造数据
（读不到就按未知 id 点名拒绝）。工具面描述子在 `read_surface.py`（本文件只管执行）。
"""

from __future__ import annotations

import json
from typing import Any

# 工具面描述子（纯声明；与执行实现分列以守住文件规模门）
from adapters.canonical.read_projection import project_run
from adapters.canonical.read_surface import (
    _DELIVERABLE_ARTIFACT,
    _TOOL_CAPABILITIES,
    describe_tools,
    read_tool_args,
    spill_tool_result,
)
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.domain.tools import (
    ToolCallRecord,
    ToolHealthReport,
    ToolProviderSpec,
    ToolResultRecord,
    ToolSpec,
)

#: `spill_threshold_bytes` **默认 1**（即「内容必须可取回」）的取值理由 —— 不是
#: `spill_large_result` 的 32 KiB 缺省，理由是**消费者的要求**（与运行链同一条）：
#:
#: - 会话工具桥（`adapters/openhands/session_tool_invocation.py`）**必须把内容交回模型**，
#:   因此结果必须落在 ArtifactStore 里可被 `fetch_spilled_result` 取回；
#: - 低于阈值的结果**不落盘**（`spill_large_result` 只返回 digest）⇒ 桥拿不到内容，
#:   只能点名拒绝（`produced no spilled output`）—— 实测：默认阈值下**任何**小于
#:   32 KiB 的读结果都会走到这条失败路径，而那正是绝大多数读；
#: - 同一约定在运行链侧的既有表述：`tests/e2e/literature_chain_support.py` 的
#:   `spill_threshold_bytes=1`（"运行链证据要求内容在场（准入会重算 digest）"）。
#:
#: 「大结果不进模型上下文」的治理目标由**调用方**（会话工具面的返回长度、运行链的
#: chaining 语义）承担，不由本阈值承担 —— 在这里省掉落盘只会让工具**不可用**。
_SPILL_RATIONALE = True


class CanonicalReadProvider:
    """canonical 读面（ArtifactStore + EvidenceLedger）的 ToolProvider 实现。

    **只读**：本实现的 `execute` 不写任何 store（除参数/结果制品外）——
    能力集合由 `ToolProviderSpec` 声明，运行期语义由 `execute_tool_call` 的策略面约束。
    """

    def __init__(  # noqa: PLR0913 - provider 的 Port 依赖就这么几件（齐了才叫承接）
        self,
        artifacts: ArtifactStore,
        ledger: EvidenceLedger | None = None,
        *,
        budget_ledger: Any | None = None,
        experiment_store: Any | None = None,
        run_store: Any | None = None,
        review_store: Any | None = None,
        program_store: Any | None = None,
        memory_store: Any | None = None,
        spill_threshold_bytes: int = 1,
    ) -> None:
        """构造读面 provider（`spill_threshold_bytes` 的取值理由见 `_SPILL_RATIONALE`）。"""
        self._artifacts = artifacts
        self._ledger = ledger
        #: 预算账本（`budget.read` 的**真实**来源）。缺省 None ⇒ 该工具**点名**不可用，
        #: 不返回空账本冒充「没有用量」。
        self._budget = budget_ledger
        #: 实验域存储（`experiment.read` / `experiment_plan.read` 的**真实**来源）。
        #: 缺省 None ⇒ 这两个工具**点名**不可用，不返回空列表冒充「没有实验」。
        self._experiments = experiment_store
        #: run 存储（`run.read` 的**真实**来源；`RunStore` 是既有 Port，两个组合根都持有）。
        #: 缺省 None ⇒ 该工具**点名**不可用，不返回空壳冒充「没有这个 run」。
        self._runs = run_store
        #: 评审结论存储（`review.read` 的**真实**来源；GOAL-035 EC-01 的 canonical 记录面）。
        #: 缺省 None ⇒ 该工具**点名**不可用，不返回空列表冒充「没有评审结论」。
        self._reviews = review_store
        #: 程序存储（`research_state.read` 的**入口**来源之一；GOAL-037 EC-01 的 canonical
        #: 记录面）。本读面用 `RunStore.for_program` 取前序 run，program_store 只作装配
        #: 标记位（在场 = 该装配认得「程序」这个概念）。
        self._programs = program_store
        #: 记忆存储（`memory.read` 的**真实**来源；GOAL-20261009-042 EC-02 的承接）。
        #: 缺省 None ⇒ 该工具**点名**不可用，不返回空列表冒充「没有记忆」。
        self._memories = memory_store
        self._spill_threshold = spill_threshold_bytes

    def execute(self, provider: ToolProviderSpec, call: ToolCallRecord) -> ToolResultRecord:
        args = read_tool_args(self._artifacts, call)
        handler = {
            "artifact_read": self._artifact_read,
            "evidence_read": self._evidence_read,
            "claim_read": self._claim_read,
            "workspace_read": self._workspace_read,
            "budget_read": self._budget_read,
            "experiment_read": self._experiment_read,
            "experiment_plan_read": self._experiment_plan_read,
            "deliverable_read": self._deliverable_read,
            "run_read": self._run_read,
            "review_read": self._review_read,
            "research_state_read": self._research_state_read,
            "memory_read": self._memory_read,
        }.get(call.tool_id)
        if handler is None:
            raise InvalidInputError(f"unknown tool id: {call.tool_id}")
        return spill_tool_result(
            self._artifacts, call, handler(args), threshold_bytes=self._spill_threshold
        )

    def list_tools(self, provider: ToolProviderSpec) -> tuple[ToolSpec, ...]:
        """只列**本 provider 真声明了**的能力对应的工具（未声明的不进工具面）。"""
        declared = set(provider.capabilities)
        capability_of = {
            tool_id: capability
            for tool_id, capability in _TOOL_CAPABILITIES.items()
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
        return project_run(self._ledger, run_id)

    def _budget_read(self, args: dict[str, object]) -> dict[str, object]:
        """读 canonical 预算账本快照（预留 + 用量条目；**只读**，不动账）。

        账本缺失 ⇒ 点名拒绝（不返回空账本冒充「没有用量」—— 那会让「没接账本」与
        「真没有用量」不可区分）。可按 `run_id` 过滤：**预留按其 `scope` 归 run**
        （实测：reservation ref 是内容摘要 `budget-reservation:<hex>`，**不含** run 标识
        —— 归属信息只在 `BudgetReservation.scope`，如 `run:<id>`），用量按条目里出现的
        run 标识归 run。两者都读既有字段，不新造第二套归属口径。
        """
        if self._budget is None:
            raise InvalidInputError(
                "budget_read requires a BudgetLedger, which is not in this assembly"
            )
        run_id = str(args.get("run_id") or "").strip()
        snapshot = self._budget.snapshot()
        reservations = [
            {
                "reservation_ref": ref,
                "reservation_id": item.id,
                "scope": item.scope,
                "resource_type": str(item.resource_type),
                "quantity": str(item.quantity),
            }
            for ref, items in snapshot.reservations_by_ref.items()
            for item in items
            if not run_id or run_id in item.scope
        ]
        entries = [
            {
                "entry_id": entry.entry_id,
                "resource_type": str(entry.resource_type),
                "quantity": str(entry.quantity),
                "unit": entry.unit,
                "cost_status": str(entry.cost_status),
            }
            for entry in snapshot.entries
            if not run_id or getattr(entry, "run_id", None) == run_id
        ]
        return {
            "run_id": run_id or None,
            "reservations": sorted(reservations, key=lambda item: str(item["reservation_ref"])),
            "entries": sorted(entries, key=lambda item: str(item["entry_id"])),
        }

    def _deliverable_read(self, args: dict[str, object]) -> dict[str, object]:
        """读 run 的持久化交付物（`persist_completion` 写的 `{run_id}:deliverable.json`）。

        **与读面路由同一个落点**（`services/api/routers/deliverable.py` 的 `_artifact_ref`）
        —— 本工具不新造第二个名字、也不生成空报告冒充。未产出 ⇒ 点名拒绝（读面路由那边
        用 `available=false` 表达同一事实，两者**同源**）。
        """
        run_id = str(args.get("run_id") or "").strip()
        if not run_id:
            raise InvalidInputError("deliverable_read requires a non-empty run_id")
        artifact_id = f"{run_id}:{_DELIVERABLE_ARTIFACT}"
        meta = self._artifacts.meta(artifact_id)
        if meta is None:
            raise InvalidInputError(
                f"run {run_id!r} has no persisted deliverable at {artifact_id!r}"
            )
        payload: object = json.loads(self._artifacts.get(artifact_id).decode("utf-8"))
        return {
            "run_id": run_id,
            "artifact_id": artifact_id,
            "artifact_digest": str(meta.digest),
            "deliverable": payload,
        }

    def _claim_read(self, args: dict[str, object]) -> dict[str, object]:
        """读 canonical 的 claim 及其 evidence relation（**只读**）。

        与 `evidence_read` 的分工：那条以**证据**为主体（按 run 过滤 evidence），
        本条以**命题**为主体（列出 claim 与它引用的证据 id / 关系类型）。
        两条共用同一份 relation 投影口径（不新造第二套）。

        `run_id` 可选：给了就只列**引用到该 run 证据**的 claim；不给列全部 claim
        （claim 是全局命题，run 只是证据的采集上下文）。
        """
        if self._ledger is None:
            raise InvalidInputError(
                "claim_read requires an EvidenceLedger, which is not in this assembly"
            )
        run_id = str(args.get("run_id") or "").strip()
        claims: list[dict[str, object]] = []
        for claim in self._ledger.claims():
            relations: list[dict[str, object]] = []
            for relation in self._ledger.relations_for_claim(claim.id):
                evidence_id = relation.evidence_id
                if run_id:
                    try:
                        item = self._ledger.get_evidence(evidence_id)
                    except Exception:  # noqa: BLE001 - 引用可能已删除（视觉态）
                        continue
                    if item.run_id != run_id:
                        continue
                relations.append({"evidence_id": evidence_id, "relation": str(relation.relation)})
            if run_id and not relations:
                continue
            claims.append({
                "id": claim.id,
                "statement": claim.statement,
                "status": str(claim.status),
                "relations": sorted(relations, key=lambda item: str(item["evidence_id"])),
            })
        return {
            "run_id": run_id or None,
            "claims": sorted(claims, key=lambda item: str(item["id"])),
        }

    def _experiment_plan_read(self, args: dict[str, object]) -> dict[str, object]:
        """读 canonical 的实验计划（`ExperimentStore.list_plans`；可按状态过滤）。

        与 HTTP 读面同源：`GET /experiment-plans` 走同一个 store 方法（本工具不新造第二套
        查询口径）。store 缺失 ⇒ 点名拒绝（不返回空列表冒充「没有计划」）。
        """
        if self._experiments is None:
            raise InvalidInputError(
                "experiment_plan_read requires an ExperimentStore, which is not in this assembly"
            )
        state = str(args.get("state") or "").strip() or None
        plans = self._experiments.list_plans(state=state)
        return {
            "state": state,
            "plans": [
                {
                    "id": str(plan.id),
                    "name": plan.name,
                    "state": str(plan.state),
                    "hypothesis": plan.hypothesis,
                    "task_contract_ref": plan.task_contract_ref,
                    "created_at": str(plan.created_at),
                }
                for plan in sorted(plans, key=lambda item: str(item.id))
            ],
        }

    def _experiment_read(self, args: dict[str, object]) -> dict[str, object]:
        """读某 run 的**实验执行记录**（与 HTTP 读面 `GET /runs/{id}/experiments` 同源）。

        同源的含义是**两步一致**（HTTP 面就是这么做的）：
        ① `EvidenceLedger` 的证据里发现 `experiment_run_id`（哪次实验与这个 run 有关）；
        ② `ExperimentStore.get_run(...)` 取该次执行的**域事实**（state / plan_id）。
        本工具不新造第三个查询面，也不替代 HTTP 面已有的 metrics 投影
        （那要读 metrics artifact，属运行链已完成的部分；这里如实**不含** metrics）。
        """
        if self._ledger is None:
            raise InvalidInputError(
                "experiment_read requires an EvidenceLedger, which is not in this assembly"
            )
        if self._experiments is None:
            raise InvalidInputError(
                "experiment_read requires an ExperimentStore, which is not in this assembly"
            )
        run_id = str(args.get("run_id") or "").strip()
        if not run_id:
            raise InvalidInputError("experiment_read requires a non-empty run_id")
        return {"run_id": run_id, "experiments": self._experiments_of_run(run_id)}

    def _experiments_of_run(self, run_id: str) -> list[dict[str, object]]:
        """证据里发现 `experiment_run_id` → store 取域事实（缺 store 记录则如实标注）。"""
        assert self._ledger is not None and self._experiments is not None
        discovered: list[dict[str, object]] = []
        seen: set[str] = set()
        for claim in self._ledger.claims():
            for relation in self._ledger.relations_for_claim(claim.id):
                try:
                    evidence = self._ledger.get_evidence(relation.evidence_id)
                except Exception:  # noqa: BLE001 - 引用可能已删除（视觉态）
                    continue
                experiment_run_id = evidence.experiment_run_id
                if evidence.run_id != run_id or not experiment_run_id:
                    continue
                if experiment_run_id in seen:
                    continue
                seen.add(experiment_run_id)
                discovered.append(self._experiment_fact(experiment_run_id, evidence))
        return sorted(discovered, key=lambda item: str(item["experiment_run_id"]))

    def _experiment_fact(self, experiment_run_id: str, evidence: Any) -> dict[str, object]:
        """一次实验的可读事实：证据侧（artifact/镜像摘要）+ 域侧（state/plan_id）。"""
        assert self._experiments is not None
        fact: dict[str, object] = {
            "experiment_run_id": experiment_run_id,
            "artifact_id": evidence.artifact_id,
            "image_digest": evidence.image_digest,
            "environment_digest": evidence.environment_digest,
        }
        try:
            run = self._experiments.get_run(experiment_run_id)
        except Exception:  # noqa: BLE001 - store 无此记录时如实标注，不编造域字段
            fact["domain_record"] = None
            fact["domain_record_reason"] = "no ExperimentRun in the canonical store for this id"
            return fact
        fact["domain_record"] = {
            "id": str(run.id),
            "plan_id": str(run.plan_id),
            "state": str(run.state),
        }
        return fact

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

    def _run_read(self, args: dict[str, object]) -> dict[str, object]:
        """读一个 canonical run（实现见 `adapters/canonical/run_read.py`，本行只委派）。"""
        from adapters.canonical.run_read import run_read

        return run_read(self._runs, args)

    def _review_read(self, args: dict[str, object]) -> dict[str, object]:
        """读一次 run 的评审结论（实现见 `adapters/canonical/review_read.py`，本行只委派）。"""
        from adapters.canonical.review_read import review_read

        return review_read(self._reviews, args)

    def _research_state_read(self, args: dict[str, object]) -> dict[str, object]:
        """读程序内**前序** run 的落库结论（实现见 `research_state_read.py`，本行只委派）。"""
        from adapters.canonical.research_state_read import research_state_read

        return research_state_read(self._runs, self._reviews, args)

    def _memory_read(self, args: dict[str, object]) -> dict[str, object]:
        """读 governed memory 并按**调用方给的时点**给出时效与处置（实现见
        `memory_read.py`，本行只委派）。"""
        from adapters.canonical.memory_read import memory_read

        return memory_read(self._memories, args)


__all__ = ["CanonicalReadProvider"]
