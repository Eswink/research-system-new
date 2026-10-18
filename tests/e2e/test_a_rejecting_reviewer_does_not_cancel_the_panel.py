"""GOAL-20261018-087 EC-01/EC-02/EC-03：**判负不取消同批评审**，分歧因此真的能出现。

**它咬住的缺口**：`phase_runner._run_group_task` 在 `step.failure` 非空时**立即**返回失败
`RunOutcome` ⇒ 同一 phase 的后续任务不执行。对一批评审者，这意味着**第一位判负就把 run
打死**，第二位连跑都不跑 ⇒ 阶梯「复检」的 `下一级`（两个模型在同一上游产物上给出**不同
判词**）在**结构上不可达**。建档实测：两位都判负 ⇒ `state: FAILED, records: 1, panels: []`。

**三条读数（成对）**：

1. **声明了 `review_panel: COMPLETE_THEN_JUDGE`** ⇒ 两位评审者都跑、两条判词都落库、
   `panels` 一条且 `voters == 2`；run 终态**仍是 `FAILED`**（判负没被吞掉），
   失败消息**逐条点名**每位评审者的目标与 verdict。
2. **未声明** ⇒ 逐字回到既有 fail-fast：`records == 1`、`panels == []`、消息是既有的
   `rejected by acceptance gate` 形态。
3. **按压（一负一过）** ⇒ `panels` 的 `advisory == "REJECT"`、`dissent` 点名判过的那位；
   把第二位也改成判负 ⇒ `dissent == []`、`advisory == "REJECT"`（事实变 ⇒ 读数变）。

**如实边界**：本文件用**受控执行体**证明「分歧可表达、可读、可点名」；
**真实中转站上两位评审者是否会真的分歧**属 live 观察，不在本文件（GOAL 的 `W-4`）。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from typing import Any

from adapters.canonical.review_read import review_read
from adapters.contracts.protocol_loaders import load_protocol
from packages.application.run_orchestration.commands import StartRunCommand
from packages.domain.core import ID
from packages.domain.protocols import ProtocolDefinition
from tests.api.run_fixtures import make_run_ready_deps
from tests.e2e.scenario import StructuredOutputAgentRuntime

_PROTOCOL = "examples/protocols/review_scored_research_v1.yaml"
_PHASE = "review"
_REVIEWER_ROLE = "scientific_reviewer"
_CONTRACT = "review_scored_deliverable"
#: 评审面板声明（与 `packages/domain/failure_policy.ReviewPanelFailure` 同一个取值）。
PANEL_KEY = "review_panel"
PANEL_VALUE = "COMPLETE_THEN_JUDGE"
#: 阈值 0.8：0.95 判过、0.5 判负。
_PASS: dict[str, object] = {"review_decision": {"verdict": "ACCEPT", "score": 0.95}}
_FAIL: dict[str, object] = {"review_decision": {"verdict": "REJECT", "score": 0.5}}


@dataclass(frozen=True, slots=True)
class _Run:
    state: str
    message: str
    records: tuple[Any, ...]
    payload: dict[str, Any]

    @property
    def panels(self) -> list[dict[str, Any]]:
        value = self.payload["panels"]
        assert isinstance(value, list), value
        return [item for item in value if isinstance(item, dict)]


def _two_reviewers() -> ProtocolDefinition:
    """出厂协议的 `review` phase ⇒ 两位评审者（其余逐字不动）。"""
    protocol = load_protocol(_PROTOCOL)
    phases = []
    for phase in protocol.phases:
        if phase.id != _PHASE:
            phases.append(phase)
            continue
        roles = [
            replace(item, min_instances=2, max_instances=2) if item.role == _REVIEWER_ROLE else item
            for item in phase.required_roles
        ]
        phases.append(replace(phase, required_roles=roles))
    return ProtocolDefinition(id=protocol.id, version=protocol.version, phases=phases)


def _run(per_reviewer: tuple[dict[str, object], ...], *, declare: bool) -> _Run:
    """跑一次：`per_reviewer` 按**评审者 id 排序**给出各自的交付物（`reviewer_a` 在前）。

    `declare=False` 是**反证臂**：同一份协议、同一批交付物，只去掉面板声明 ⇒
    读数必须退回 fail-fast。
    """
    deps = make_run_ready_deps()
    base = deps.preflight_override
    assert base is not None, "run-ready 夹具必须给出 preflight_override"
    contracts = dict(base.catalog.task_contracts)
    contract = contracts[_CONTRACT]
    if declare:
        contracts[_CONTRACT] = replace(
            contract,
            failure_policy={**(contract.failure_policy or {}), PANEL_KEY: PANEL_VALUE},
        )
    context = replace(base, catalog=replace(base.catalog, task_contracts=contracts))
    runtime = _PerReviewerRuntime(
        dict(zip(("reviewer_a", "reviewer_b"), per_reviewer, strict=True))
    )
    service = deps.runs
    assert service is not None, "run-ready 装配必须带编排服务"
    deps.runs = type(service)(replace(service._deps, runtime=runtime))
    outcome = deps.runs.start_run(
        _two_reviewers(),
        context.catalog,
        context.project,
        context,
        StartRunCommand(
            project_id=context.project.project_id,
            protocol_id=_two_reviewers().id,
            run_id=ID.generate(),
            trace_id=f"goal087-{uuid.uuid4()}",
        ),
    )
    run_id = str(outcome.run_id)
    store = deps.review_findings
    assert store is not None, "run-ready 装配必须带评审结论存储"
    return _Run(
        state=str(outcome.state),
        message=str(outcome.message),
        records=store.for_run(run_id),
        payload=review_read(store, {"run_id": run_id}),
    )


class _PerReviewerRuntime(StructuredOutputAgentRuntime):
    """按**评审者 id** 给出不同交付物（`outputs_by_contract` 只按合约分，不够用）。

    为什么需要它：本 GOAL 的靶子是「两位评审者**给出不同判词**」，而既有夹具的
    `outputs_by_contract` 让同一合约的所有会话拿同一份输出 ⇒ 分歧在那个夹具里**不可表达**。
    本类只多一层「按 agent 分派」，其余行为逐字沿用父类。
    """

    def __init__(self, by_agent: dict[str, dict[str, object]]) -> None:
        super().__init__()
        self._by_agent = by_agent

    def _output_for(self, session_id: str) -> dict[str, object]:
        spec = self._specs.get(session_id)
        if spec is not None and spec.agent.id in self._by_agent:
            return dict(self._by_agent[spec.agent.id])
        return super()._output_for(session_id)


def test_a_rejecting_reviewer_does_not_cancel_the_panel() -> None:
    """① 两位都判负 ⇒ **两条判词都在**、面板两票、run 仍 `FAILED` 且消息点名全体。"""
    result = _run((_FAIL, _FAIL), declare=True)
    assert result.state == "FAILED", (result.state, result.message)
    assert len(result.records) == 2, [
        (item.task_id, item.finding.reviewed_by) for item in result.records
    ]
    assert {item.finding.verdict for item in result.records} == {"REJECT"}
    panels = result.panels
    assert len(panels) == 1, panels
    assert panels[0]["voters"] == 2, panels[0]
    assert panels[0]["votes"] == {"REJECT": 2}, panels[0]
    # 失败消息逐条点名两位评审者的**目标**（不是笼统「gate rejected」）
    assert "main/glm-5.3=REJECT" in result.message, result.message
    assert "main/kimi-k2.6=REJECT" in result.message, result.message


def test_without_the_declaration_the_first_rejection_stops_the_group() -> None:
    """② **反证臂**：去掉面板声明 ⇒ 退回既有 fail-fast（只一条判词、无面板）。"""
    result = _run((_FAIL, _FAIL), declare=False)
    assert result.state == "FAILED", (result.state, result.message)
    assert len(result.records) == 1, [item.finding.reviewed_by for item in result.records]
    assert result.panels == [], result.panels
    assert "rejected by acceptance gate" in result.message, result.message
    assert "review panel rejected" not in result.message, result.message


def test_a_split_panel_names_the_dissent_and_presses_to_unanimity() -> None:
    """③ **分歧可读**：一负一过 ⇒ 少数意见被点名；都改判负 ⇒ 分歧消失（读数随之变）。"""
    split = _run((_FAIL, _PASS), declare=True)
    assert split.state == "FAILED", (split.state, split.message)
    panel = split.panels[0]
    assert panel["voters"] == 2, panel
    assert panel["votes"] == {"PASS": 1, "REJECT": 1}, panel
    # 平票 ⇒ advisory 为 None（GOAL-085 语义），但**分歧逐条可读**：
    # 没有多数可相对 ⇒ **每票都列**（原实现在平票时 list 为空，正是本 GOAL 抓到并修掉的
    # 缺口：分歧最大的那一刻反而读不到分歧）。
    assert panel["advisory"] is None, panel
    assert panel["dissent"] == [
        "gate:reviewer_a:REJECT",
        "gate:reviewer_b:PASS",
    ], panel

    unanimous = _run((_FAIL, _FAIL), declare=True)
    same = unanimous.panels[0]
    assert same["advisory"] == "REJECT", same
    assert same["dissent"] == [], same
