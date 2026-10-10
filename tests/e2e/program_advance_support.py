"""GOAL-20261008-037 EC-02 判据的**共享支持件**（双 run 程序实跑）。

**为什么单独成模块**：规模门禁对 `tests/**` 同样生效（单文件 ≤ 450 行）。本模块不含用例，
只放装配辅助 —— 与 `tests/e2e/review_read_support.py` 的拆分同一手法。

**它装配什么**：run-ready 装配（含程序面 store）+ **受控执行体**（按合约声明交付物）
+ 运行链能力步（GOAL-036 的同一批对象）；程序面（建程序 / 推进 / 读面）经**既有 HTTP 面**驱动。

**如实边界**：受控执行体声明的分数决定验收门判词（`PASS` / `REJECT`）—— 本支持件用它
制造「结论面判续 / 判停」两臂；它**不**声称模型真的会这么评审。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

#: 本轮实跑用的协议（与 GOAL-036 EC-03 同一份；两个 phase 都由运行链执行，
#: `produce` 落库逐条判词 ⇒ 程序的结论面有**落库事实**可依）。
PROTOCOL = "review_consumption_v1.yaml"
#: 协议内两个 phase 引用的合约（`outputs_by_contract` 的键）。
PRODUCE_CONTRACT = "review_scored_deliverable"
CONSUME_CONTRACT = "review_consumption_deliverable"
#: 分数 0.95 ≥ 阈值 0.8 ⇒ 验收门 `PASS`（判词逐字可复核）。
PASS_OUTPUT: dict[str, object] = {"review_decision": {"verdict": "PASS", "score": 0.95}}
#: 分数 0.5 < 阈值 ⇒ 验收门 `REJECT`（结论面判停的那一臂）。
REJECT_OUTPUT: dict[str, object] = {"review_decision": {"verdict": "REJECT", "score": 0.5}}
CONSUME_OUTPUT: dict[str, object] = {"meta_review": {"covers": "recorded-review-findings"}}

PROJECT = "example-project"


def program_deps(
    *,
    output: dict[str, object] | None = None,
    consume_contract: str = CONSUME_CONTRACT,
    consume_output: dict[str, object] | None = None,
) -> Any:
    """run-ready 装配 + 受控执行体 + 运行链能力步（程序面实跑的全部依赖）。

    执行体输出的**分数**决定验收门判词 ⇒ 程序推进的结论面读到的就是它。
    capabilities 步取 GOAL-036 的 `calls()` / `provider()`：两个 phase 都由运行链执行，
    缺了能力步那条 run 起不来（这与「程序推进」是两件事，各自只做自己的部分）。
    """
    from packages.application.ports.tool_provider import ToolProvider
    from packages.application.run_orchestration.phase_capabilities import CapabilityDeps
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.assembly import policy_bindings
    from tests.api.run_fixtures import make_run_ready_deps
    from tests.e2e.review_read_support import calls, provider
    from tests.e2e.scenario import StructuredOutputAgentRuntime

    deps = make_run_ready_deps()
    old = deps.runs
    assert old is not None
    runtime = StructuredOutputAgentRuntime(
        outputs_by_contract={
            PRODUCE_CONTRACT: output if output is not None else PASS_OUTPUT,
            consume_contract: consume_output if consume_output is not None else CONSUME_OUTPUT,
        }
    )
    context = deps.preflight_override
    assert context is not None
    spec = context.catalog.tool_providers["m12_artifact"]
    policy = policy_bindings().get("policy_evaluator")
    assert policy is not None
    inner = old._deps
    ledger = inner.ledger
    assert ledger is not None, "运行链要落证据 ⇒ 装配必须带 ledger"
    capabilities = CapabilityDeps(
        calls=calls(),
        providers={str(spec.id): cast("ToolProvider", provider(deps))},
        provider_specs={str(spec.id): spec},
        policy=policy,
        artifacts=inner.artifacts,
        ledger=ledger,
    )
    deps.runs = RunOrchestrationService(replace(inner, runtime=runtime, capabilities=capabilities))
    return deps


def deps_for_capabilities(
    deps: Any, *, calls: tuple[Any, ...], provider_instance: Any | None
) -> Any:
    """把**任意**运行链调用集 + provider 实例接进一个新编排服务（EC-03 的跨 run 装配用）。

    与 `program_deps` 的区别只有一处：能力步的声明与 provider 实例由调用方给
    （EC-03 的技能名/工具 id 与 GOAL-036 那份不同），其余（受控执行体 / 策略面 /
    artifacts / ledger）沿用同一批产品对象。
    """
    from packages.application.run_orchestration.phase_capabilities import CapabilityDeps
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.assembly import policy_bindings

    inner = deps.runs._deps
    ledger = inner.ledger
    assert ledger is not None, "运行链要落证据 ⇒ 装配必须带 ledger"
    context = deps.preflight_override
    assert context is not None
    spec = context.catalog.tool_providers["m12_artifact"]
    policy = policy_bindings().get("policy_evaluator")
    assert policy is not None
    deps.runs = RunOrchestrationService(
        replace(
            inner,
            capabilities=CapabilityDeps(
                calls=calls,
                providers={} if provider_instance is None else {str(spec.id): provider_instance},
                provider_specs={str(spec.id): spec},
                policy=policy,
                artifacts=inner.artifacts,
                ledger=ledger,
            ),
        )
    )
    return deps


def create_program(  # noqa: PLR0913 - 建程序声明面即字段；参数对象会降低可读性
    client: Any,
    *,
    max_runs: int,
    continue_on: list[str] | None = None,
    protocol: str | None = None,
    max_attempts_per_index: int = 1,
    human_gate_at_index: int | None = None,
    human_gate_on_verdicts: list[str] | None = None,
) -> dict[str, Any]:
    """建程序（经既有 HTTP 面；协议按启动 run 的同一校验解析）。

    `protocol` 缺省 = 本文件的 `PROTOCOL`；EC-03 的跨 run 判据传它自己那份协议
    （**同一入口、不同声明** —— 不复制第二个建程序路径）。
    `human_gate_at_index`（GOAL-20261010-046 EC-04）/ `human_gate_on_verdicts`
    （GOAL-20261010-048 EC-02）只在显式传值时进载荷 ——
    缺省**不发键**，这样「未声明」那一臂走的是与既有调用**逐字相同**的请求体。
    """
    import uuid

    payload: dict[str, object] = {
        "protocol_path": protocol if protocol is not None else PROTOCOL,
        "max_runs": max_runs,
        "continue_on_verdicts": continue_on if continue_on is not None else ["PASS"],
        "max_attempts_per_index": max_attempts_per_index,
    }
    if human_gate_at_index is not None:
        payload["human_gate_at_index"] = human_gate_at_index
    if human_gate_on_verdicts is not None:
        payload["human_gate_on_verdicts"] = human_gate_on_verdicts
    response = client.post(
        f"/projects/{PROJECT}/programs",
        json=payload,
        headers={"Idempotency-Key": f"prog-{uuid.uuid4()}"},
    )
    assert response.status_code == 201, response.text
    return dict(response.json())


def advance(client: Any, program_id: str) -> dict[str, Any]:
    """推进一次（经既有 HTTP 面）。"""
    import uuid

    response = client.post(
        f"/programs/{program_id}/advance",
        headers={"Idempotency-Key": f"advance-{uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    return dict(response.json())


def read_program(client: Any, program_id: str) -> dict[str, Any]:
    """程序读面（声明 + 各轮 run + 逐条决策）。"""
    response = client.get(f"/programs/{program_id}")
    assert response.status_code == 200, response.text
    return dict(response.json())
