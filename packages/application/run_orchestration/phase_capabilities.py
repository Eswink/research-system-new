"""运行链能力步：phase 声明的 run-chain 能力**由运行链执行**（GOAL-011 EC-01）。

为什么是运行链、不是"模型自己调工具"：会话里 `provider id → SDK 工具` 的映射在生产
装配里是空操作（缺映射时会话创建**点名失败**，`test_unmapped_tool_set_is_named_not_silently_dropped`
固定该行为）。把证据押在"模型恰好调用了工具"上既概率化、又会红在装配缺失；运行链执行
是**确定性**的——能力声明在协议里，每次 run 都真的执行。

四段全部**复用既有件**，不新造第二套：

1. **解析**：`SessionSpecContext.run_chain_tool_ids`（协议 phase 的
   `capability_execution: run_chain`，见 `CapabilityExecution`）给出本 phase 由运行链
   执行的 provider id；本模块只跑其中**装配方声明过**的 `RunChainCall`。
2. **策略**：`execute_tool_call`（执行期**唯一**策略裁决点）——本模块不自行裁决，
   只经 `ScopedPolicy` 把「capability → scope」这张既有映射补进请求。
3. **执行**：`require_frozen_tool_set`（ADR-0004 冻结集）后交给 provider。
4. **证据**：`register_tool_evidence`（工具证据的**唯一**准入入口）→ SourceRecord +
   Evidence。**只登记不挂 relation 的读不到**（`GET /runs/{id}/evidence` 走 claim
   relations 投影）：调用方把返回的 evidence 并入会话结果的 claim（`register_and_gate`）。

两条**如实边界**（本模块不声称已解决）：

- 证据的准入要求**内容寻址的内容在场**（`register_tool_evidence` 会重算 digest）。
  工具结果只有超过 provider 的 spill 阈值才落 ArtifactStore ⇒ 装配方必须让运行链
  provider **总是 spill**（`NcbiEutilsProvider(spill_threshold_bytes=1)`），否则本步
  fail closed 而不是伪造 digest。
- 检索到的内容**不进模型上下文**（会话工具面在生产装配里仍是惰性的）⇒ 交付物与检索
  结果之间只有 claim relation 这一条 grounded 关系，没有"模型读到了文献"这层主张。
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from packages.application.evidence.tool_evidence import (
    ToolEvidenceInput,
    register_tool_evidence,
)
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import (
    InvalidInputError,
    PermanentPortError,
    TransientPortError,
)
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.ports.policy_evaluator import (
    PolicyEvaluation,
    PolicyEvaluator,
    PolicyRequest,
)
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.application.ports.tool_provider import ToolProvider
from packages.application.preflight.policy_check import policy_scope_for
from packages.application.tool_plane.execution import execute_tool_call, require_frozen_tool_set
from packages.application.tool_plane.results import fetch_spilled_result
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import ToolCallStatus
from packages.domain.evidence import Evidence
from packages.domain.tasks import ResearchTask
from packages.domain.tools import ToolCallRecord, ToolProviderSpec, ToolResultRecord

if TYPE_CHECKING:  # 只为类型：避免与 task_executor 形成导入环
    from packages.application.run_orchestration.task_executor import SessionSpecContext

ARGS_ARTIFACT_PREFIX = "tool-args:"


@dataclass(frozen=True, slots=True)
class RunChainCall:
    """运行链要执行的一次工具调用（**装配方**声明；应用层不内置任何厂商工具知识）。

    参数来源三类，全部**声明式**、缺一即 fail closed（不猜、不编造）：

    - `arguments_from_input`：声明输入制品 JSON 里的字段（点分路径，如 `retrieval.query`）；
    - `fixed_arguments`：协议/操作者决定的量（如 `retmax`）——只放量，不放内容；
    - `ids_from_previous`：**上一步结果**里的 id 列表字段（如 `ids`）→ 本步的 `ids`
      （检索→读取的真实链条：读取的是**检索结果里真实出现的**标识）。
    """

    provider_id: str
    tool_id: str
    capability: str
    arguments_from_input: tuple[str, ...] = ()
    fixed_arguments: Mapping[str, object] = field(default_factory=dict)
    ids_from_previous: str | None = None


@dataclass(frozen=True, slots=True)
class CapabilityDeps:
    """运行链能力步的装配面（组合根/装配方注入；**缺省 None ⇒ 本步不启用**）。"""

    calls: tuple[RunChainCall, ...]
    providers: Mapping[str, ToolProvider]
    provider_specs: Mapping[str, ToolProviderSpec]
    policy: PolicyEvaluator
    artifacts: ArtifactStore
    ledger: EvidenceLedger
    actor: str = "system:run-chain"
    telemetry: TelemetrySink | None = None


@dataclass(frozen=True, slots=True)
class CapabilityStepOutcome:
    """一次能力步的结果：证据（挂到 claim 用）或失败消息（**不**静默降级）。"""

    evidences: tuple[Evidence, ...] = ()
    failure_message: str | None = None
    system_failure: bool = True


@dataclass(frozen=True, slots=True)
class ScopedPolicy:
    """把「capability → scope」补进执行期策略请求（与 preflight **同一张表**）。

    `execute_tool_call` 构造的 `PolicyRequest` 不带 scope，而 policy.yaml 里带 scope 的
    allow 规则（`literature.search@approved_tool_providers`）要求 scope 相等 ⇒ 不补这一
    字段就会出现「preflight 放行、执行期落到 `default_effect: DENY`」的分裂。本包装只
    补齐这一个字段：裁决仍由既有 evaluator 做，执行仍由既有 `execute_tool_call` 做。
    """

    inner: PolicyEvaluator

    def evaluate(self, request: PolicyRequest) -> PolicyEvaluation:
        if request.scope is None:
            scope = policy_scope_for(request.capability)
            if scope is not None:
                request = replace(request, scope=scope)
        return self.inner.evaluate(request)


def execute_run_chain_capabilities(
    deps: CapabilityDeps | None,
    task: ResearchTask,
    spec: SessionSpecContext,
) -> CapabilityStepOutcome:
    """执行本 phase 声明为 run-chain 的调用（按声明顺序，逐步把前一步结果带入下一步）。

    没有装配（`deps is None`）或本 phase 没有 run-chain 声明 ⇒ 什么都不做（既有语义
    逐字节不变）。任何失败**如实上报**：`failure_message` 由调用方交给
    `failure_step`（容忍策略/失败分类与既有失败路径同一个分叉点）。
    """
    if deps is None:
        return CapabilityStepOutcome()
    planned = tuple(call for call in deps.calls if call.provider_id in spec.run_chain_tool_ids)
    if not planned:
        return CapabilityStepOutcome()
    evidences: list[Evidence] = []
    previous: Mapping[str, object] | None = None
    try:
        material = _input_material(deps, spec)
        for call in planned:
            previous, evidence = _execute_one(
                deps, task, spec, call, _StepInputs(material=material, previous=previous)
            )
            evidences.append(evidence)
    except (InvalidInputError, PermanentPortError, TransientPortError) as error:
        return CapabilityStepOutcome(
            failure_message=f"run-chain capability step failed: {error}",
            system_failure=isinstance(error, TransientPortError),
        )
    return CapabilityStepOutcome(evidences=tuple(evidences))


@dataclass(frozen=True, slots=True)
class _StepInputs:
    """一步的输入材料：声明输入制品的字段 + 上一步的结果（链式传参用参数对象）。"""

    material: Mapping[str, object]
    previous: Mapping[str, object] | None = None


def _execute_one(
    deps: CapabilityDeps,
    task: ResearchTask,
    spec: SessionSpecContext,
    call: RunChainCall,
    inputs: _StepInputs,
) -> tuple[Mapping[str, object], Evidence]:
    """一步：参数 → 冻结集 → 策略+执行 → 内容寻址证据 → 返回（可链式传递的）结果。"""
    provider = deps.providers.get(call.provider_id)
    provider_spec = deps.provider_specs.get(call.provider_id)
    if provider is None or provider_spec is None:
        raise InvalidInputError(
            f"run-chain provider {call.provider_id!r} has no registered instance in this assembly"
        )
    require_frozen_tool_set(spec.frozen_tool_set, call.provider_id)
    record = _tool_call(deps, task, call, _arguments(call, inputs))

    outcome = execute_tool_call(
        provider,
        provider_spec,
        record,
        ScopedPolicy(deps.policy),
        deps.actor,
        telemetry=deps.telemetry,
    )
    result = outcome.result
    if result is None:
        raise InvalidInputError(f"run-chain tool {call.tool_id} returned no result record")
    _source, evidence = register_tool_evidence(
        deps.ledger,
        deps.artifacts,
        input=ToolEvidenceInput(
            result=result,
            run_id=task.run_id.value,
            manifest_digest=spec.frozen_manifest_digest,
            tool_refs=(call.provider_id, call.tool_id),
        ),
    )
    return _payload(deps, result, call), evidence


def _tool_call(
    deps: CapabilityDeps,
    task: ResearchTask,
    call: RunChainCall,
    args: Mapping[str, object],
) -> ToolCallRecord:
    """参数经 ArtifactStore 传递（provider 按 `argument_digest` 重算校验，防篡改）。"""
    operation_key = _operation_key(call, args)
    content = json.dumps(dict(args), ensure_ascii=False, sort_keys=True).encode("utf-8")
    artifact_id = f"{ARGS_ARTIFACT_PREFIX}{task.id.value}:{operation_key}"
    deps.artifacts.put(
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            created_by=deps.actor,
            source_refs=[f"task:{task.id.value}"],
            classification="tool-args",
        ),
        content,
    )
    return ToolCallRecord(
        task_id=task.id.value,
        attempt=1,
        operation_key=operation_key,
        tool_id=call.tool_id,
        capability=call.capability,
        argument_digest=Digest.of_bytes(content),
        status=ToolCallStatus.REQUESTED,
        recorded_at=Timestamp.now(),
    )


def _operation_key(call: RunChainCall, args: Mapping[str, object]) -> str:
    """操作键（幂等键）：工具 id + **本次调用的真实标识**——外部标识因此在证据链里可读。

    例：读取 PMID 39612345 的那次调用，其 evidence id / source_ref 都含 `39612345`。
    """
    ids = args.get("ids")
    if isinstance(ids, list) and ids:
        return f"{call.tool_id}:{'+'.join(str(item) for item in ids)}"
    return call.tool_id


def _lookup(material: Mapping[str, object], path: str) -> object:
    """点分路径取值（如 `retrieval.query`）；任一层缺失 ⇒ 抛错（fail closed，不猜）。"""
    current: object = material
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise InvalidInputError(f"declared input carries no {path!r}")
        current = current[part]
    return current


def _arguments(
    call: RunChainCall,
    inputs: _StepInputs,
) -> dict[str, object]:
    args: dict[str, object] = dict(call.fixed_arguments)
    for path in call.arguments_from_input:
        # 点分路径的最后一段就是 provider 看到的参数名（`retrieval.query` → `query`）。
        args[path.rsplit(".", 1)[-1]] = _lookup(inputs.material, path)
    if call.ids_from_previous is not None:
        ids = (inputs.previous or {}).get(call.ids_from_previous)

        if not isinstance(ids, list) or not ids:
            raise InvalidInputError(
                f"previous step carries no {call.ids_from_previous!r} ids "
                f"for run-chain tool {call.tool_id}"
            )
        args["ids"] = [str(item) for item in ids]
    return args


def _input_material(deps: CapabilityDeps, spec: SessionSpecContext) -> dict[str, object]:
    """本 phase 声明输入的 JSON 顶层字段合并成一份参数材料（缺件 ⇒ fail closed）。"""
    material: dict[str, object] = {}
    for artifact_id in spec.declared_input_artifacts:
        parsed = json.loads(deps.artifacts.get(artifact_id).decode("utf-8"))
        if not isinstance(parsed, dict):
            raise InvalidInputError(f"declared input {artifact_id} is not a JSON object")
        material.update(parsed)
    return material


def _payload(
    deps: CapabilityDeps,
    result: ToolResultRecord,
    call: RunChainCall,
) -> Mapping[str, object]:
    """工具内容（内容寻址，digest 重算）→ 供下一步取标识的 JSON 对象。"""
    if result.output_digest is None:
        raise InvalidInputError(
            f"run-chain tool {call.tool_id} returned no spilled content; nothing to chain"
        )
    content = fetch_spilled_result(deps.artifacts, result)
    if content is None:  # pragma: no cover - fetch 只在无 digest 时给 None（上面已挡）
        raise InvalidInputError(f"run-chain tool {call.tool_id} result is not retrievable")
    parsed = json.loads(content.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise InvalidInputError(f"run-chain tool {call.tool_id} content is not a JSON object")
    return parsed


__all__ = [
    "ARGS_ARTIFACT_PREFIX",
    "CapabilityDeps",
    "CapabilityStepOutcome",
    "RunChainCall",
    "ScopedPolicy",
    "execute_run_chain_capabilities",
]
