"""GOAL-20261008-037 EC-03 判据的**共享支持件**（跨 run 知识累积实跑）。

**为什么单独成模块**：规模门禁对 `tests/**` 同样生效（单文件 ≤ 450 行）。本模块不含用例，
只放装配辅助 —— 与 `tests/e2e/review_read_support.py` 的拆分同一手法。

**它装配什么**：把「跨 run 知识读入」这一条跑链能力（`research_state_read`）接到
**真实现**（`CanonicalReadProvider`，读同一个 `RunStore` + `ReviewFindingStore` 实例），
其余走 GOAL-037 EC-02 的程序面装配（`program_advance_support.program_deps`）。

**如实边界**：本支持件不声称读到的结论**影响**了后续 run 的科学结论；它只让
「前序 run 的落库判词」在后续 run 的能力面上**可见且被读到**。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

from tests.e2e.program_advance_support import PASS_OUTPUT, deps_for_capabilities, program_deps

#: 本轮证跨 run 的协议（两 phase：`produce` 落库判词 ⇒ `consume` 读**前序 run** 的结论）。
PROTOCOL = "cross_run_knowledge_v1.yaml"
PROVIDER = "m12_artifact"
#: 本轮承接的能力与 provider 侧工具 id（逐字写死，不 import 产品常量当预言机）。
CAPABILITY = "research_state.read"
TOOL_ID = "research_state_read"
#: `consume` 的合约（与 `review_consumption_deliverable` **不同名** ⇒ 交付物可区分）。
CONSUME_CONTRACT = "cross_run_consumption_deliverable"
CONSUME_OUTPUT: dict[str, object] = {"meta_review": {"covers": "prior-run-recorded-verdicts"}}


def calls(omit: str | None = None) -> tuple[Any, ...]:
    """本协议声明的运行链调用（`research_state.read` 一条；入口 = 本 run 的标识）。

    `run_id_argument=True`：**入口是执行期才知道的本 run 标识**，由它反查程序归属 ⇒
    读到的才是「本 run 所属程序的前序轮次」（装配方无从写死）。
    """
    from packages.application.run_orchestration.phase_capabilities import RunChainCall

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


def _trim_the_grant(deps: Any) -> None:
    """把 `research_state.read` 那条 `allow` 从**内存内**目录副本里删掉（产品文件零改动）。

    策略面求值器一并换成以**裁剪后策略**构造的真实 `NativePolicyEvaluator` ——
    夹具缺省注入的是 `FakePolicyEvaluator`（不读 `policy.yaml`），不换就测不到「放行被删」。
    """
    from packages.application.policy.native import NativePolicyEvaluator

    context = deps.preflight_override
    assert context is not None
    catalog_policy = context.catalog.policy
    assert catalog_policy is not None
    trimmed = replace(
        catalog_policy,
        allow=tuple(rule for rule in catalog_policy.allow if rule.capability != CAPABILITY),
    )
    deps.preflight_override = replace(
        context,
        catalog=replace(context.catalog, policy=trimmed),
        policy_evaluator=NativePolicyEvaluator(trimmed),
    )


def cross_run_deps(
    *,
    omit_provider_capability: bool = False,
    without_grant: bool = False,
) -> Any:
    """程序面装配（EC-02 的）+ 跨 run 读链的能力步。

    两个反证臂（与 GOAL-036 EC-03 同一手法）：

    - `omit_provider_capability=True`：调用声明照旧，但**不给** provider 实例（或给一个
      **没有**该能力的实例）⇒ 该步必须**点名失败**；
    - `without_grant=True`：从**内存内的**策略副本里删掉 `research_state.read` 那条
      `allow` ⇒ 调用点必须点名 `POLICY_DENIED`（产品文件零改动）。
    """
    from adapters.canonical import CanonicalReadProvider

    deps = program_deps(
        output=PASS_OUTPUT,
        consume_contract=CONSUME_CONTRACT,
        consume_output=CONSUME_OUTPUT,
    )
    run_store = deps.runs_store
    assert run_store is not None
    inner = deps.runs._deps

    if without_grant:
        _trim_the_grant(deps)

    reader = CanonicalReadProvider(
        inner.artifacts,
        inner.ledger,
        run_store=run_store,
        review_store=deps.review_findings,
        spill_threshold_bytes=1,
    )
    return deps_for_capabilities(
        deps,
        calls=calls(),
        provider_instance=None if omit_provider_capability else cast("Any", reader),
    )


def run_ids_of(client: Any, program_id: str) -> list[str]:
    """程序内各轮 run id（按序号；经**程序读面**取，不读内部对象）。"""
    from tests.e2e.program_advance_support import read_program

    detail = read_program(client, program_id)
    return [str(row["run_id"]) for row in detail["runs"]]


def tool_evidence_of_run(client: Any, run_id: str) -> list[dict[str, Any]]:
    """该 run 的证据链里 `tool_refs` 命中本工具的那几条（经既有读面）。"""
    rows = client.get(f"/runs/{run_id}/evidence").json()
    return [
        row
        for row in rows
        if [PROVIDER, TOOL_ID] == [str(item) for item in (row.get("tool_refs") or [])]
    ]
