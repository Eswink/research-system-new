"""GOAL-20261008-036 EC-03 判据的**共享支持件**（装配 + 读面辅助）。

**为什么单独成模块**：规模门禁对 `tests/**` 同样生效（单文件 ≤ 450 行），而本 EC 的判据要
覆盖「用上 / 缺实现 / 未放行」三态。本模块**不含用例**，只放常量与装配辅助 —— 与
`tests/e2e/granted_reads_support.py` / `tests/e2e/live_run_support.py` 的拆分同一手法。

**它装配什么**：`review_consumption_v1.yaml` 的两个 phase 都由**运行链**执行
（`capability_execution: run_chain`），`consume` 的 `review.read` 一条调用由本模块声明
（`RunChainCall`，`run_id_argument=True`）—— 与 GOAL-031 EC-01(e) 的做法同一口径：
**确定性执行**，不押在「模型恰好调了工具」上。

**受控执行体的声明**（`outputs_by_contract`，按合约 id 区分两个 phase）：`produce` 交
`review_decision`（含它自己给的分数 0.95 ⇒ 验收门判过并把逐条判词落库），`consume` 交
`meta_review`。两者都是**受控执行体自己声明的交付物**，不是判据编造的值。

**如实边界**：本支持件不声称读到的评审结论**内容正确**，也不声称多评审者聚合已接通
（GOAL-035 的 `N-3` 仍未收口）。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, cast

from adapters.canonical import CanonicalReadProvider
from packages.application.ports.tool_provider import ToolProvider
from packages.application.run_orchestration.phase_capabilities import (
    CapabilityDeps,
    RunChainCall,
)

PROTOCOL = "review_consumption_v1.yaml"
PROVIDER = "m12_artifact"
#: 本轮**新承接**的能力与它 provider 侧的工具 id（逐字写死，不 import 产品常量当预言机）。
CAPABILITY = "review.read"
TOOL_ID = "review_read"
PRODUCE_PHASE = "produce"
CONSUME_PHASE = "consume"
#: 两个 phase 各自引用的合约（`outputs_by_contract` 的键）。
PRODUCE_CONTRACT = "review_scored_deliverable"
CONSUME_CONTRACT = "review_consumption_deliverable"
#: 受控执行体声明的交付物（`produce` 的分数 0.95 ≥ 阈值 0.8 ⇒ 验收门判过）。
PRODUCE_OUTPUT: dict[str, object] = {"review_decision": {"verdict": "ACCEPT", "score": 0.95}}
CONSUME_OUTPUT: dict[str, object] = {"meta_review": {"covers": "recorded-review-findings"}}
#: `produce` 落库判词的**前缀**（`ARTIFACT_EXISTS` / `REVIEW_SCORE` 两条判据各一行）。
RECORDED_PREFIXES = ("ARTIFACT_EXISTS: ", "REVIEW_SCORE: ")


def calls(omit: str | None = None) -> tuple[RunChainCall, ...]:
    """本协议声明的运行链调用（`review.read` 一条）。

    `run_id_argument=True`：读的是**本 run 自己**的落库结论 —— 执行期才有 run 标识，
    装配方无从写死（与既有 `claim.read` / `evidence.read` 的运行链步同一口径）。
    """
    declared = (
        RunChainCall(
            provider_id=PROVIDER,
            tool_id=TOOL_ID,
            capability=CAPABILITY,
            run_id_argument=True,
        ),
    )
    if omit is None:
        return declared
    return tuple(call for call in declared if call.capability != omit)


def provider(deps: Any) -> CanonicalReadProvider:
    """本轮的 canonical 读面 provider（**真实现**，读**同一个** `ReviewFindingStore` 实例）。

    `review_store` 取 `ApiDeps.review_findings` —— 与编排侧（写结论）**同一实例**
    （run-ready 装配的既有约定）；取不到 ⇒ 工具**点名**不可用（不返回空列表冒充「没有」）。
    `spill_threshold_bytes=1`：运行链证据要求内容寻址的内容在场（准入会重算 digest）。
    """
    inner = deps.runs._deps
    return CanonicalReadProvider(
        inner.artifacts,
        inner.ledger,
        review_store=deps.review_findings,
        spill_threshold_bytes=1,
    )


def assembled_deps(*, omit_provider: bool = False) -> Any:
    """run-ready 装配 + 受控执行体声明 + 运行链能力步（**同一批产品对象**）。

    `omit_provider=True` 是**反证面**：调用声明照旧（一条能力），但装配里**不给** provider
    实例 ⇒ 运行链步必须**点名失败**（不是静默跳过那条能力）。
    """
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.assembly import policy_bindings
    from tests.api.run_fixtures import make_run_ready_deps
    from tests.e2e.scenario import StructuredOutputAgentRuntime

    deps = make_run_ready_deps()
    reader = provider(deps)
    context = deps.preflight_override
    assert context is not None
    spec = context.catalog.tool_providers[PROVIDER]
    policy = policy_bindings().get("policy_evaluator")
    assert policy is not None, "policy.yaml must be loadable for the run-chain policy check"
    service = deps.runs
    assert service is not None, "run-ready 装配必须带编排服务"
    inner = service._deps
    artifacts = inner.artifacts
    ledger = inner.ledger
    assert ledger is not None, "运行链证据要落在 ledger 上 ⇒ 装配必须带 ledger"
    capabilities = CapabilityDeps(
        calls=calls(),
        providers={} if omit_provider else {str(spec.id): cast("ToolProvider", reader)},
        provider_specs={str(spec.id): spec},
        policy=policy,
        artifacts=artifacts,
        ledger=ledger,
    )
    runtime = StructuredOutputAgentRuntime(
        outputs_by_contract={
            PRODUCE_CONTRACT: PRODUCE_OUTPUT,
            CONSUME_CONTRACT: CONSUME_OUTPUT,
        }
    )
    deps.runs = RunOrchestrationService(replace(inner, runtime=runtime, capabilities=capabilities))
    return deps


def deps_without_grant() -> Any:
    """把 `review.read` 的放行规则**删掉**之后的装配（反证臂的输入）。

    裁剪发生在**内存内的目录副本**上（产品文件零改动，与
    `test_release_expansion_is_read_only.py` 的注入臂同一手法）；preflight 求值器一并换成
    以**裁剪后策略**构造的真实 `NativePolicyEvaluator` —— 夹具缺省注入的是
    `FakePolicyEvaluator`（不读 `policy.yaml`），不换就测不到「放行被删」这件事。
    """
    from packages.application.policy.native import NativePolicyEvaluator

    deps = assembled_deps()
    context = deps.preflight_override
    assert context is not None
    policy = context.catalog.policy
    assert policy is not None, "policy.yaml must be loadable"
    trimmed = replace(
        policy, allow=tuple(rule for rule in policy.allow if rule.capability != CAPABILITY)
    )
    deps.preflight_override = replace(
        context,
        catalog=replace(context.catalog, policy=trimmed),
        policy_evaluator=NativePolicyEvaluator(trimmed),
    )
    return deps


@dataclass(frozen=True, slots=True)
class ChainReads:
    """经**既有读面**取到的 canonical 事实（判据只看这一面，不读内部对象）。"""

    run: dict[str, Any]
    failures: list[str]
    evidence: list[dict[str, Any]]
    artifacts: list[dict[str, Any]]
    reviews: list[dict[str, Any]]


def read_chain(client: Any, run: dict[str, Any]) -> ChainReads:
    """把一次 run 的读面事实一次取齐（`run_failures` 取 `run.failed` / `task.failed`）。"""
    from tests.e2e.live_run_support import run_failures

    run_id = str(run["id"])
    return ChainReads(
        run=run,
        failures=run_failures(client, run_id),
        evidence=client.get(f"/runs/{run_id}/evidence").json(),
        artifacts=client.get(f"/runs/{run_id}/artifacts").json(),
        reviews=client.get(f"/runs/{run_id}/reviews").json(),
    )


def preflight_report(deps: Any) -> Any:
    """经**产品入口**（`services.api.run_execution.execution_inputs`）求一次 preflight。

    与 run 启动走同一条输入解析路径 ⇒ 这里读到的 findings 就是那次 run 判 `FAILED`
    所依据的那一份（不是判据另拼的上下文）。
    """
    from adapters.contracts.protocol_loaders import load_protocol
    from packages.application.preflight.preflight import compile_and_preflight
    from packages.domain.core import ID
    from services.api.run_execution import ExecutionRequest, execution_inputs

    inputs = execution_inputs(
        ExecutionRequest(
            deps=deps,
            protocol_path=PROTOCOL,
            run_id=ID("0d031100-0000-4000-8000-0000000000fe"),
            trace_id=None,
            draft_ref=None,
            project_id="example-project",
        )
    )
    protocol = load_protocol(f"examples/protocols/{PROTOCOL}")
    _plan, report = compile_and_preflight(
        protocol, inputs.catalog, inputs.project, inputs.preflight
    )
    return report


def phase_of_task(reads: Any) -> dict[str, str]:
    """`task_id` → phase id（由**该任务的交付物制品名**判，不靠调用顺序猜）。"""
    mapping: dict[str, str] = {}
    for artifact_id in artifact_ids(reads):
        head, _, tail = artifact_id.rpartition(":")
        if tail == "review_decision":
            mapping[head] = PRODUCE_PHASE
        elif tail == "meta_review":
            mapping[head] = CONSUME_PHASE
    return mapping


def task_of_evidence(item: dict[str, Any]) -> str:
    """证据所属任务的标识（工具证据的 `artifact_id` 带 `tool-result:{task_id}:…`）。"""
    parts = str(item.get("artifact_id") or "").split(":")
    return parts[1] if len(parts) > 2 else ""


def tool_evidence(reads: Any, *, phase: str | None = None) -> dict[str, dict[str, Any]]:
    """`tool_refs` 非空的证据，按 provider 侧 **tool id** 建索引（读面口径，非内部对象）。

    `phase` 非空时只取该 phase 任务的证据 —— 按 phase 分开取是**掩蔽防护**
    （GOAL-030 EC-01 实测过「单键索引后写覆盖前写」）。
    """
    by_task = phase_of_task(reads)
    by_tool: dict[str, dict[str, Any]] = {}
    for item in reads.evidence:
        refs = item.get("tool_refs") or []
        if len(refs) != 2 or refs[0] != PROVIDER:
            continue
        if phase is not None and by_task.get(task_of_evidence(item)) != phase:
            continue
        by_tool[str(refs[1])] = item
    return by_tool


def artifact_ids(reads: Any) -> list[str]:
    payload = reads.artifacts
    entries = payload["artifacts"] if isinstance(payload, dict) else payload
    return [str(item.get("id") or "") for item in entries]


__all__ = [
    "CAPABILITY",
    "ChainReads",
    "CONSUME_CONTRACT",
    "CONSUME_OUTPUT",
    "CONSUME_PHASE",
    "PRODUCE_CONTRACT",
    "PRODUCE_OUTPUT",
    "PRODUCE_PHASE",
    "PROTOCOL",
    "PROVIDER",
    "RECORDED_PREFIXES",
    "TOOL_ID",
    "artifact_ids",
    "assembled_deps",
    "calls",
    "deps_without_grant",
    "phase_of_task",
    "preflight_report",
    "provider",
    "read_chain",
    "task_of_evidence",
    "tool_evidence",
]
