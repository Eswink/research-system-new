"""GOAL-20261016-081 EC-04 的 **e2e 判据**：跨相输入让 `plan` 格的覆盖两维**都成立**。

**被测对象**：`examples/protocols/grounded_report_chain_v1.yaml` —— `scouting` 相用运行链
取回真检索（`europe_pmc`），`plan` 相把它的产物声明为**跨相输入**
（`inputs: [..., scouting:scouting_report]`），合约 `research_report_plan` 的两条覆盖判据
（计数维 + **性质维** `minimum_retrieved_sources: 1`）因此必须判过。

**三条读数（全部经既有读面，且成对）**：

1. **run 真的过**：终态 `SUCCEEDED`，没有失败事件；
2. **`plan` 的覆盖判词逐字读出两维**：`<n> >= <m> sources; <k> >= <j> retrieved` ——
   只判「run 成功」是间接推断，**不算**读出判词（与
   `test_two_dimensional_coverage_and_claim_relation` 同一口径）；
3. **反证臂**：把这一条跨相声明摘掉（同一份装配、其余逐字不变）⇒ `plan` 被判拒，
   判词**点名性质维**（`0 < 1 retrieved sources`）、且计数维已满足。

第 3 条是「跨相输入真的被覆盖门数进去」的机械证明：它同时排除了「run 本来就能过」
与「性质维从来没被求值」两种假绿。

**如实边界**：run-ready 夹具（装配方接执行体缝），证的是**链路与判据**，不是真实中转站
（那由 live 判据承担）；检索用离线 `OfflineEuropePmc`（同一份真实语料作答）。
"""

from __future__ import annotations

import re
from typing import Any

import pytest
from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.e2e.literature_chain_support import OfflineEuropePmc
from tests.e2e.retrieval_context_support import install_spec_recorder
from tests.e2e.test_ec03_real_runtime_offline_chain import _read_chain, mock_relay
from tests.e2e.test_research_report_arc_offline import _assembled_deps

__all__ = ["mock_relay"]

pytestmark = pytest.mark.requires_docker

_PROTOCOL = "grounded_report_chain_v1.yaml"
_PLAN_CONTRACT = "research_report_plan"
#: 判过的两维判词（域函数 `_evaluate_evidence_coverage` 的原文形态）。
_COVERAGE_PASS = re.compile(r"(\d+) >= (\d+) sources; (\d+) >= (\d+) retrieved")
#: 性质维判负的判词：**两个维度的数都在**（计数满足、性质不满足）。
_COVERAGE_NATURE = re.compile(r"(\d+) < (\d+) retrieved sources \((\d+) >= (\d+) sources\)")
#: 跨相声明原文（反证臂要摘的就是它）。
_CROSS_PHASE_INPUT = "scouting:scouting_report"


def _plan_review(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    """`plan` 格的验收结论（经既有读面 `GET /runs/{id}/reviews` 取）。"""
    matches = [
        item
        for item in reviews
        if item.get("review_type") == "acceptance_gate"
        and item.get("contract_id") == _PLAN_CONTRACT
    ]
    assert matches, (
        "读面没有 plan 格的验收结论",
        [(item.get("contract_id"), item.get("review_type")) for item in reviews],
    )
    return matches[0]


def _run(client: TestClient, deps: Any, key: str) -> dict[str, Any]:
    created = client.post(
        "/projects/example-project/runs",
        json={"protocol_path": _PROTOCOL},
        headers={"Idempotency-Key": key},
    )
    assert created.status_code == 200, created.text
    payload: dict[str, Any] = created.json()
    return payload


def _with_retrieval(deps: Any) -> None:
    """接上检索上下文装配（产品组合根同一处决策；本判据的前提不是被测对象）。"""
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.retrieval_context_support import retrieval_context_builder

    deps.runs = RunOrchestrationService(
        replace(
            deps.runs._deps,
            retrieval_context=retrieval_context_builder(
                artifacts=deps.artifacts, ledger=deps.ledger
            ),
        )
    )
    install_spec_recorder(deps)


def test_the_plan_phase_coverage_has_both_dimensions(mock_relay: str) -> None:
    """两条成对读数：run 过 + `plan` 的覆盖判词**逐字**读出两维。"""
    offline = OfflineEuropePmc(requests=[])
    deps, _recorder = _assembled_deps(mock_relay, offline)
    _with_retrieval(deps)
    with TestClient(create_app(deps)) as client:
        run = _run(client, deps, "run-goal081-ec04-cross-phase")
        reads = _read_chain(client, run)
        reviews = client.get(f"/runs/{run['id']}/reviews").json()

    assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
    assert not reads.failures, reads.failures
    review = _plan_review(reviews)
    findings = "\n".join(str(item) for item in review.get("findings", []))
    match = _COVERAGE_PASS.search(findings)
    assert match, ("plan 的覆盖判词必须逐字给出两维", review)
    count, minimum, retrieved, minimum_retrieved = (int(g) for g in match.groups())
    assert count >= minimum and retrieved >= minimum_retrieved
    assert retrieved >= 1, ("性质维必须由**真实检索**满足", review)


def _press_protocol(protocol: Any) -> Any:
    """把 `plan` 的跨相声明摘掉（其余 phase 逐字不动）——反证臂的唯一改动。"""
    from dataclasses import replace

    from packages.application.protocol_compile.cross_phase_inputs import local_inputs
    from packages.domain.protocols import ProtocolDefinition

    phases = []
    for phase in protocol.phases:
        if phase.id != "plan":
            phases.append(phase)
            continue
        kept = tuple(item for item in phase.inputs if item != _CROSS_PHASE_INPUT)
        assert kept != tuple(phase.inputs), ("plan 的 inputs 里没有那条跨相声明", phase.inputs)
        phases.append(replace(phase, inputs=list(kept)))
    assert local_inputs(protocol, protocol.phases[1])  # 声明面确实有本地输入那一类
    return ProtocolDefinition(id=protocol.id, version=protocol.version, phases=phases)


def test_press_dropping_the_cross_phase_input_rejects_the_plan(mock_relay: str) -> None:
    """**按压**：摘掉 `scouting:scouting_report` ⇒ `plan` 判拒，且判词**点名性质维**。

    同一份装配、同一份协议，只改这一条声明 ⇒ 读数必须相反。这证明：
    (i) 覆盖门真的把跨相输入数了进去；(ii) 性质维**没有**被跳过或恒真。

    走 `deps.runs.start_run(...)`（同一条产品链；API 的 `protocol_path` 只接受
    `examples/protocols/` 内的文件，而按压**不能**改仓库里的协议文件）。
    """
    import uuid

    from adapters.contracts.protocol_loaders import load_protocol
    from packages.application.run_orchestration.commands import StartRunCommand
    from packages.domain.core import ID
    from packages.domain.run_state import ResearchRunState

    protocol = _press_protocol(load_protocol(f"examples/protocols/{_PROTOCOL}"))
    offline = OfflineEuropePmc(requests=[])
    deps, _recorder = _assembled_deps(mock_relay, offline)
    _with_retrieval(deps)
    with TestClient(create_app(deps)):
        # run-ready 夹具**总是**给出 `preflight_override`（目录已指向本机 mock 端点）；
        # 走实时 preflight 会去探真实中转站（本判据不出网）。
        preflight = deps.preflight_override
        assert preflight is not None, "run-ready 夹具必须给出 preflight_override"
        catalog = preflight.catalog
        project = preflight.project
        run_id = ID.generate()
        outcome = deps.runs.start_run(
            protocol,
            catalog,
            project,
            preflight,
            StartRunCommand(
                project_id=project.project_id,
                protocol_id=protocol.id,
                run_id=run_id,
                trace_id=f"press-{uuid.uuid4()}",
            ),
        )

    assert outcome.state == ResearchRunState.State.FAILED, (outcome.state, outcome.message)
    # run 行由控制面在编排返回**之后**才落库（`run_from_execution`）⇒ 这里读不到
    # `/runs/{id}/events`；判词取编排返回的失败消息（与 `run.failed` 的 payload 同源）。
    joined = outcome.message
    match = _COVERAGE_NATURE.search(joined)
    assert match, ("判词必须点名**性质维**（且计数维仍满足）", joined)
    retrieved, minimum, count, sources_minimum = (int(g) for g in match.groups())
    assert retrieved < minimum, (retrieved, minimum)
    assert count >= sources_minimum, ("计数维应当已满足 —— 只有性质维不满足", joined)
