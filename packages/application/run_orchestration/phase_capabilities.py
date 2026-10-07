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
from packages.application.run_orchestration.phase_call_arguments import (
    arguments_for,
)
from packages.application.run_orchestration.phase_call_arguments import (
    lookup_path as _lookup,
)
from packages.application.run_orchestration.phase_capability_triggers import (
    planned_in_this_phase,
    should_skip,
    skip_reason,
)
from packages.application.tool_plane.execution import execute_tool_call, require_frozen_tool_set
from packages.application.tool_plane.results import fetch_spilled_result
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import ToolCallStatus, TrustLabel
from packages.domain.evidence import Evidence
from packages.domain.tasks import ResearchTask
from packages.domain.tools import ToolCallRecord, ToolProviderSpec, ToolResultRecord

if TYPE_CHECKING:  # 只为类型：避免与 task_executor 形成导入环
    from packages.application.run_orchestration.task_executor import SessionSpecContext

ARGS_ARTIFACT_PREFIX = "tool-args:"


@dataclass(frozen=True, slots=True)
class RunChainCall:
    """运行链要执行的一次工具调用（**装配方**声明；应用层不内置任何厂商工具知识）。

    参数来源四类，全部**声明式**、缺一即 fail closed（不猜、不编造）：

    - `arguments_from_input`：声明输入制品 JSON 里的字段（点分路径，如 `retrieval.query`）；
    - `fixed_arguments`：协议/操作者决定的量（如 `retmax`）——只放量，不放内容；
    - `ids_from_previous`：**上一步结果**里的 id 列表字段（如 `ids`；支持点分路径，
      如 `structured.ids` —— MCP provider 的溢出内容是一层信封，机器可读的一半在
      `structured` 下，链式传参因此需要路径而不仅是顶层键）→ 本步的 `ids`
      （检索→读取的真实链条：读取的是**检索结果里真实出现的**标识）；
    - `run_id_argument`：本步要不要拿到**本次 run 的标识**（GOAL-20261005-030）。
      canonical 读面的若干工具以 `run_id` 为查询键（`evidence_read` / `workspace_read` /
      `experiment_read` / `deliverable_read`），而 run id **只在执行期存在**
      （`ResearchTask.run_id`，由编排生成）——协议/装配方**无从**在声明里写死它。
      这个字段因此不是「值」而是「**取值的来源**」：置真 ⇒ 运行时把 `task.run_id.value`
      作为该参数注入，名字就叫 `run_id`（与 provider 侧参数名同源）。
      缺省 `False` ⇒ 该参数不注入，既有行为**逐字节不变**。
    - `requires_previous_ids`：本步是否**要求**上一步真的给出 id 列表
      （GOAL-20261006-031 EC-03 的**声明式触发面**）。

      语义（两种情况**都点名**，没有第三种走向）：
      * `True`（缺省）：上一步没给 id 列表 ⇒ **失败**并点名（既有行为，逐字节不变）；
      * `False`：上一步没给 id 列表 ⇒ 本步**跳过**（不执行工具），跳过**带理由**回传
        （`CapabilityStepOutcome.skipped`），由调用方登记 —— 这是「派生链的第二轮
        按第一轮结果决定跑不跑」的声明式形态：**判断依据是声明字段的在场性**，
        不是应用层硬编码「如果就」。

      为什么放在这里而不是编译期：触发条件读的是**上一步的结果**（执行期才知道），
      编译期无从判定；这个字段因此与 `ids_from_previous` 同层 —— 都是「取值的来源 /
      条件」，不是值本身。缺省 `True` ⇒ 既有行为**逐字节不变**。
    - `phase_id`：本调用属于**哪个 phase**（GOAL-20261006-031 EC-03）。
      既有过滤只按 **provider**（`call.provider_id in spec.run_chain_tool_ids`）——一次 run
      的多个 phase 若声明**同一个 provider 的不同调用**，两个 phase 都会执行**全部**调用：
      第一轮 phase 因此会去跑第二轮的调用（实测：跳过臂的判定会落在错误的 phase 上，
      且「第二轮没跑」这件事无法从任务归属上判）。本字段把过滤细化到 **phase 级**：
      非空 ⇒ 只在本 phase 执行；缺省 `None` ⇒ 沿用 provider 级过滤（既有行为逐字节不变）。
    - `artifact_from_previous`：本步读**哪一个制品**由**上一步的读面结果**决定
      （GOAL-20261006-031 EC-03 的**派生**面）：值是制品 id 的**声明后缀**
      （如 `discovery_report`，合约声明的产出名）；运行时从上一步结果的 `evidence[]`
      里按 `source_ref` 后缀选中**恰好一条**（零条 / 多条 ⇒ 点名失败），把该
      `source_ref` 作为本步的 `artifact_id` 参数。

      为什么是「后缀选择」而不是写死 id：制品 id 含**执行期才生成**的 task id，
      装配方无从写死；而「产出名」是**声明事实**。这个字段因此与 `ids_from_previous`
      同层 —— 都是「**取值的来源**」（一个从 id 列表取，一个从证据列表选），不是值本身。
      缺省 `None` ⇒ 该参数不注入（既有行为逐字节不变）。
    """

    provider_id: str
    tool_id: str
    capability: str
    arguments_from_input: tuple[str, ...] = ()
    fixed_arguments: Mapping[str, object] = field(default_factory=dict)
    ids_from_previous: str | None = None
    run_id_argument: bool = False
    requires_previous_ids: bool = True
    phase_id: str | None = None
    artifact_from_previous: str | None = None
    #: **读上一轮（而非本次链内上一步）的产出**（GOAL-20261008-034 EC-01）。
    #:
    #: 为什么需要：`artifact_from_previous` 的后缀判据要求"恰好一条" —— 两轮时成立；
    #: **三轮起**同一后缀会匹配到**多份**（前几轮的产出都还在证据投影里）⇒ fail closed。
    #: 本字段把选择收窄到**上一轮**：运行时用上一轮的**任务 id**（执行期才知道 ——
    #: 与 `run_id_argument` 同层：声明的是"取值的来源"而不是值）挑出那一份。
    #: 缺省 `False` ⇒ 走既有后缀判据（单轮 / 两轮语义**逐字节不变**）。
    artifact_from_previous_round: bool = False


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
    """一次能力步的结果：证据（挂到 claim 用）/ 失败消息 / **声明式跳过**。

    `skipped`（GOAL-20261006-031 EC-03）：某一步的 `requires_previous_ids=False` 且上一步
    没给 id 列表时**带理由跳过**（不执行工具、不产出证据）。它是**可观测事实**而不是
    静默降级：理由逐字说明「哪条工具因上一步的哪个字段而没跑」，由调用方登记。
    缺省 `None` ⇒ 没有任何跳过（既有行为逐字节不变）。
    """

    evidences: tuple[Evidence, ...] = ()
    failure_message: str | None = None
    system_failure: bool = True
    skipped: tuple[str, ...] = ()
    # GOAL-20261008-034 EC-01：各步**返回内容**（`_payload` 的解析结果，按声明顺序）。
    # 多轮循环的停止判据读它（"本轮结论"的可观察事实）；缺省空 = 既有行为逐字节不变。
    outputs: tuple[Mapping[str, object], ...] = ()


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

    **本轮声明优先**（GOAL-20261008-034 EC-01）：`spec.round_calls` 非空时用它替代
    装配面那一批 —— 多轮循环因此可以让**每一轮**用不同的调用声明（其余判定逐字不变：
    仍按 phase 与 provider 过滤、仍过冻结集与策略）。
    """
    if deps is None:
        return CapabilityStepOutcome()
    declared = spec.round_calls or deps.calls
    planned = tuple(call for call in declared if _planned_in_this_phase(call, spec))
    if not planned:
        return CapabilityStepOutcome()
    try:
        return _run_planned_calls(deps, task, spec, planned)
    except (InvalidInputError, PermanentPortError, TransientPortError) as error:
        return CapabilityStepOutcome(
            failure_message=f"run-chain capability step failed: {error}",
            system_failure=isinstance(error, TransientPortError),
        )


def _run_planned_calls(
    deps: CapabilityDeps,
    task: ResearchTask,
    spec: SessionSpecContext,
    planned: tuple[RunChainCall, ...],
) -> CapabilityStepOutcome:
    """逐步执行（前一步结果带入下一步）；跳过**带理由**记下，不静默。"""
    evidences: list[Evidence] = []
    skipped: list[str] = []
    outputs: list[Mapping[str, object]] = []
    previous: Mapping[str, object] | None = None
    material = _input_material(deps, spec)
    for call in planned:
        if _should_skip(call, previous):
            skipped.append(skip_reason(call))
            continue
        previous, evidence = _execute_one(
            deps,
            task,
            spec,
            call,
            _StepInputs(
                material=material,
                previous=previous,
                run_id=task.run_id.value,
                previous_round_task_prefixes=spec.previous_round_task_prefixes,
            ),
        )
        evidences.append(evidence)
        outputs.append(previous)
    return CapabilityStepOutcome(
        evidences=tuple(evidences), skipped=tuple(skipped), outputs=tuple(outputs)
    )


def _planned_in_this_phase(call: RunChainCall, spec: SessionSpecContext) -> bool:
    """本 phase 是否该执行这条调用（判定见 `phase_capability_triggers`）。"""
    return planned_in_this_phase(call, spec)


def _should_skip(call: RunChainCall, previous: Mapping[str, object] | None) -> bool:
    """声明式触发判定（见 `phase_capability_triggers.should_skip`）。"""
    return should_skip(call, previous, lookup=_lookup)


@dataclass(frozen=True, slots=True)
class _StepInputs:
    """一步的输入材料：声明输入制品的字段 + 上一步的结果 + 本次 run 的标识。

    `run_id` 是 `run_id_argument` 的取值来源（**只在执行期存在**的标识；见
    `RunChainCall.run_id_argument`）。缺省 `None` ⇒ 该参数不注入。
    """

    material: Mapping[str, object]
    previous: Mapping[str, object] | None = None
    run_id: str | None = None
    #: **上一轮**任务的制品前缀（`artifact_from_previous_round` 的收窄条件；执行期才知道）。
    previous_round_task_prefixes: tuple[str, ...] = ()


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
        # 点名到**能力**与**工具**，不只是 provider：缺实现的可观测后果必须能指回
        # 「哪条声明没人承接」（GOAL-20261005-030 EC-01 的反证要求点名缺哪条）。
        raise InvalidInputError(
            f"run-chain provider {call.provider_id!r} has no registered instance in this "
            f"assembly (capability {call.capability!r}, tool {call.tool_id!r})"
        )
    require_frozen_tool_set(spec.frozen_tool_set, call.provider_id)
    record = _tool_call(deps, task, call, arguments_for(call, inputs))

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
            trust_label=_trust_label_for(provider_spec),
        ),
    )
    return _payload(deps, result, call), evidence


def _trust_label_for(provider_spec: ToolProviderSpec) -> TrustLabel:
    """来源性质由 **provider 的声明**决定（GOAL-011 EC-02），不由本步自称。

    声明了外部网络域（`network_domains`）⇒ 内容取自系统之外 ⇒ `RETRIEVED`
    （`execute_tool_call` 的 URL 策略正是按这份声明在触网前判的）；
    否则 `GENERATED`：本地计算/读取**不得**冒充「系统取得」。
    """
    if provider_spec.network_domains:
        return TrustLabel.RETRIEVED
    return TrustLabel.GENERATED


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
