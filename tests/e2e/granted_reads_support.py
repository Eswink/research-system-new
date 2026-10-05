"""GOAL-20261006-031 EC-01(e) 判据的**共享支持件**（运行链装配 + 读面快照辅助）。

**为什么单独成模块**：规模门禁对 `tests/**` 同样生效（单文件 ≤ 450 行），而本 EC 的判据要
覆盖两个 phase、四条读能力与两类反证。本模块**不含用例**，只放常量与装配辅助 —— 与
`tests/e2e/literature_chain_support.py` 的拆分同一手法。

**它装配什么**：`probe`（`run.read` / `budget.read`）与 `review`（`claim.read` /
`evidence.read`）四条运行链调用，共用 `CapabilityDeps` / `execute_run_chain_capabilities`
这批**产品代码**；跑的是 run-ready 夹具（与 GOAL-011/027/029/030 全部离线判据同一条路径）。

**建档实测的两条结构事实**（支持件按它们设计，不是绕过它们）：

1. **`run.read` 读不到本 run 自己**：canonical 的 run 行在编排（含执行）**返回之后**才由
   控制面写入（`run_from_execution` → `save_run`）⇒ 运行链执行期 `RunStore.get_run(本 run)`
   必 `KeyError`（**实测**：`run not found: '…'` 直穿到 HTTP 404）。本支持件因此**先种一条
   既存 run 行**，`run.read` 读它 —— 这正是「读 canonical run 事实」的真实用法。
2. **预算预留的 `scope` 是 `phase:<id>`、不含 run 标识**（`protocol_compile/requirements.py`）⇒
   `budget.read` **不带** `run_id` 过滤时读到本 run 的 phase 预留；带过滤只会把预留滤空
   （工具 docstring 已如实写明该归属口径）。
"""

from __future__ import annotations

import json
from typing import Any, cast

from adapters.canonical import CanonicalReadProvider
from packages.application.ports.tool_provider import ToolProvider
from packages.application.run_orchestration.phase_capabilities import (
    CapabilityDeps,
    RunChainCall,
)
from tests.e2e.live_run_support import run_chain_store_ledger as _store_ledger

PROTOCOL = "granted_reads_used_in_a_run_v1.yaml"
#: `probe` 声明的两条**本轮新放行**能力（逐字写死，不 import 产品常量当预言机）。
PROBE_RELEASED = ("run.read", "budget.read")
#: `review` 声明的**下游消费**面里**本轮新放行**的那一条。
REVIEW_RELEASED = ("claim.read",)
EVIDENCE_READ = "evidence.read"
#: 能力 → provider 侧 **tool id**（`RunChainCall.tool_id` 用这一侧的名字：
#: `read_provider.execute` 按它分派；能力名只在 `capability` 字段上）。
TOOL_IDS = {
    "run.read": "run_read",
    "budget.read": "budget_read",
    "claim.read": "claim_read",
    EVIDENCE_READ: "evidence_read",
}
PROVIDER = "m12_artifact"
PROBE_PHASE = "probe"
REVIEW_PHASE = "review"
#: 既存 canonical run 行的标识。`ID` 是 UUID 值对象（`packages/domain/core.py`）⇒ 必须是
#: 合法 UUID（**只用于读取**，不参与本 run 的生命周期）。
SEEDED_RUN_ID = "0d031100-0000-4000-8000-000000000031"


def seed_run_row(deps: Any) -> Any:
    """种一条**既存** canonical run 行（`run.read` 的读取对象）。

    用产品的 `RunStore.save_run` 写一条 `ResearchRun`（`SUCCEEDED` + 两个 digest 在场）
    ⇒ `run.read` 读到的是一条真实存在的 canonical run，而不是支持件编造的返回值。
    """
    from packages.domain.core import ID, Digest
    from packages.domain.run import ResearchRun

    run = ResearchRun(
        id=ID(SEEDED_RUN_ID),
        project_id="example-project",
        protocol_id="granted_reads_used_in_a_run_v1_0_0",
        state="SUCCEEDED",
        manifest_digest=Digest.of_bytes(b"goal031-seeded-manifest"),
        manifest_semantic_digest=Digest.of_bytes(b"goal031-seeded-semantic"),
    )
    deps.runs_store.save_run(run)
    return run


def provider(deps: Any) -> tuple[CanonicalReadProvider, Any, Any]:
    """本轮装配的 canonical 读面 provider（**真实现**，不是替身）。

    `spill_threshold_bytes=1` 是**消费者要求**（证据准入会重算 digest，默认 32 KiB 阈值会
    让小读结果不落盘 ⇒ 准入 fail closed、链拿不到内容）。
    """
    store, ledger = _store_ledger(deps)
    inner = deps.runs._deps
    return (
        CanonicalReadProvider(
            store,
            ledger,
            budget_ledger=inner.budget,
            run_store=deps.runs_store,
            spill_threshold_bytes=1,
        ),
        store,
        ledger,
    )


def calls(*, omit: str | None = None) -> tuple[RunChainCall, ...]:
    """本协议的运行链调用声明（`probe` 两条 + `review` 两条）。

    `run.read` 用 `fixed_arguments={"run_id": SEEDED_RUN_ID}`：它读的是一条**既存**
    canonical run 行（执行期本 run 的行还不存在 —— 见模块 docstring 的结构事实 1）。

    `budget.read` **不带** `run_id` 过滤：预算预留的 scope 是 `phase:<id>`（不含 run 标识）
    ⇒ 不带过滤读到的正是本 run 的 phase 预留（结构事实 2）。

    `claim.read` / `evidence.read` 用 `run_id_argument=True`：它们以**本次 run 的标识**为
    查询键（执行期才存在，协议/装配方无从写死），读的是本 run 自己的投影。
    """
    declared = [
        RunChainCall(
            provider_id=PROVIDER,
            tool_id=TOOL_IDS["run.read"],
            capability="run.read",
            fixed_arguments={"run_id": SEEDED_RUN_ID},
        ),
        RunChainCall(
            provider_id=PROVIDER,
            tool_id=TOOL_IDS["budget.read"],
            capability="budget.read",
        ),
        RunChainCall(
            provider_id=PROVIDER,
            tool_id=TOOL_IDS["claim.read"],
            capability="claim.read",
            run_id_argument=True,
        ),
        RunChainCall(
            provider_id=PROVIDER,
            tool_id=TOOL_IDS[EVIDENCE_READ],
            capability=EVIDENCE_READ,
            run_id_argument=True,
        ),
    ]
    if omit is None:
        return tuple(declared)
    return tuple(call for call in declared if call.capability != omit)


def assembled_deps(mock_relay_url: str, *, omit_provider: bool = False) -> Any:
    """run-ready 装配 + 装配方声明的运行链能力步（**同一批产品对象**）。

    `omit_provider=True` 是**反证面**：声明照旧（四条都在），但装配里**不给** provider
    实例 ⇒ 运行链步必须**点名失败**（不是静默跳过那条能力）。
    """
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.assembly import policy_bindings
    from tests.e2e.live_run_support import openhands_deps as _openhands_deps

    deps = _openhands_deps(mock_relay_url, map_tools=False)
    seed_run_row(deps)
    canonical, store, ledger = provider(deps)
    context = deps.preflight_override
    assert context is not None
    spec = context.catalog.tool_providers[PROVIDER]
    policy = policy_bindings().get("policy_evaluator")
    assert policy is not None, "policy.yaml must be loadable for the run-chain policy check"
    inner = deps.runs._deps
    capabilities = CapabilityDeps(
        calls=calls(),
        providers={} if omit_provider else {str(spec.id): cast("ToolProvider", canonical)},
        provider_specs={str(spec.id): spec},
        policy=policy,
        artifacts=store,
        ledger=ledger,
    )
    old = deps.runs
    assert old is not None
    deps.runs = RunOrchestrationService(
        replace(inner, runtime=inner.runtime, capabilities=capabilities)
    )
    return deps


def deps_without_grant(mock_relay_url: str, capability: str) -> Any:
    """把一条放行规则**删掉**之后的装配（EC-01(d)① 反证臂的输入）。

    裁剪发生在**内存内的目录副本**上（产品文件零改动，与
    `test_release_expansion_is_read_only.py` 的注入臂同一手法）。preflight 求值器一并换成
    以**裁剪后策略**构造的真实 `NativePolicyEvaluator` —— 夹具缺省注入的是
    `FakePolicyEvaluator`（不读 `policy.yaml`），不换就测不到「放行被删」这件事。
    """
    from dataclasses import replace

    from packages.application.policy.native import NativePolicyEvaluator

    deps = assembled_deps(mock_relay_url)
    context = deps.preflight_override
    assert context is not None
    policy = context.catalog.policy
    assert policy is not None, "policy.yaml must be loadable"
    trimmed = replace(
        policy, allow=tuple(rule for rule in policy.allow if rule.capability != capability)
    )
    deps.preflight_override = replace(
        context,
        catalog=replace(context.catalog, policy=trimmed),
        policy_evaluator=NativePolicyEvaluator(trimmed),
    )
    return deps


def preflight_report(deps: Any) -> Any:
    """经**产品入口**（`services.api.run_execution.execution_inputs`）求一次 preflight。

    与 run 启动走同一条输入解析路径（`preflight_override` 在场即用它），因此这里读到的
    findings 就是那次 run 判 `FAILED` 所依据的那一份 —— 不是判据另拼的上下文。
    """
    from adapters.contracts.protocol_loaders import load_protocol
    from packages.application.preflight.preflight import compile_and_preflight
    from packages.domain.core import ID
    from services.api.run_execution import ExecutionRequest, execution_inputs

    inputs = execution_inputs(
        ExecutionRequest(
            deps=deps,
            protocol_path=PROTOCOL,
            run_id=ID("0d031100-0000-4000-8000-0000000000ff"),
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
        if tail == "probe_report":
            mapping[head] = PROBE_PHASE
        elif tail == "review_decision":
            mapping[head] = REVIEW_PHASE
    return mapping


def tool_evidence(reads: Any, *, phase: str | None = None) -> dict[str, dict[str, Any]]:
    """`tool_refs` 非空的证据，按 provider 侧 **tool id** 建索引（读面口径，非内部对象）。

    `phase` 非空时只取该 phase 任务的证据 —— 两个 phase 可能调**同名**工具 ⇒ 单键索引
    会**后写覆盖前写**（GOAL-030 EC-01 实测过这个掩蔽形态），因此必须能按 phase 分开取。
    """
    by_task = phase_of_task(reads)
    by_tool: dict[str, dict[str, Any]] = {}
    for item in reads.evidence:
        refs = item.get("tool_refs") or []
        if len(refs) != 2 or refs[0] != PROVIDER:
            continue
        task_id = task_of_evidence(item)
        if phase is not None and by_task.get(task_id) != phase:
            continue
        by_tool[str(refs[1])] = item
    return by_tool


def task_of_evidence(item: dict[str, Any]) -> str:
    """证据所属任务的标识（工具证据的 `artifact_id` 带 `tool-result:{task_id}:…`）。"""
    parts = str(item.get("artifact_id") or "").split(":")
    return parts[1] if len(parts) > 2 else ""


def upstream_evidence_ids(reads: Any) -> set[str]:
    """`probe` 两条工具证据的 id（下游消费判据的上游面；空集即判据在空转）。"""
    upstream = tool_evidence(reads, phase=PROBE_PHASE)
    ids = {str(upstream[TOOL_IDS[capability]]["id"]) for capability in PROBE_RELEASED}
    assert ids, "上游必须留下证据（否则下游消费判据在空集上恒真）"
    return ids


def content_of(client: Any, artifact_id: str) -> dict[str, Any]:
    """按 artifact id 取**内容**并解析成 JSON 对象（经既有读面，不经内部对象）。"""
    response = client.get(f"/artifacts/{artifact_id}/content")
    assert response.status_code == 200, (artifact_id, response.status_code, response.text[:200])
    parsed = json.loads(response.content.decode("utf-8"))
    assert isinstance(parsed, dict), ("工具结果内容必须是 JSON 对象", artifact_id, type(parsed))
    return parsed


def artifact_ids(reads: Any) -> list[str]:
    payload = reads.artifacts
    entries = payload["artifacts"] if isinstance(payload, dict) else payload
    return [str(item.get("id") or "") for item in entries]


def app(deps: Any) -> Any:
    from services.api.app import create_app

    return create_app(deps)


__all__ = [
    "EVIDENCE_READ",
    "PROBE_PHASE",
    "PROBE_RELEASED",
    "PROTOCOL",
    "PROVIDER",
    "REVIEW_PHASE",
    "REVIEW_RELEASED",
    "SEEDED_RUN_ID",
    "TOOL_IDS",
    "app",
    "artifact_ids",
    "assembled_deps",
    "calls",
    "content_of",
    "deps_without_grant",
    "phase_of_task",
    "preflight_report",
    "provider",
    "seed_run_row",
    "task_of_evidence",
    "tool_evidence",
    "upstream_evidence_ids",
]
