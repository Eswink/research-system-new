"""GOAL-20261018-086 EC-01/EC-03：**同一 phase 的评审者被聚成一个小组**，且成对可反证。

**它咬住的假绿**：GOAL-085 的 `panels` 按 `(task_id, contract_id)` 分组，而运行链给同一
phase 的**每个**评审 agent 各生成一个 `ResearchTask`（`resolve_sessions` 逐个 agent 展开，
幂等键 `{run}:{phase}:{agent}`），判词 id 又是 `finding:{task_id}:gate` ⇒ 每个任务下**至多
一条**判词 ⇒ 多评审阶段的小组**永远不存在**。既有判据用手写 `ScopedReviewFinding` 把
`task_id` 显式给成同一个，替产品做出了产品从不做的假设。

**本文件的判据全部走运行链**（`deps.runs.start_run`），不手写落库记录 —— 判据不得替产品
搭场景。协议取自 `review_scored_research_v1.yaml` 并把 `review` phase 的
`scientific_reviewer` 下限改成 2（出厂目录里 `standard` 模板同样是 2..4，且
`ai_ml_research_v0_4_0` 的 `peer_review` 逐字是 `min_instances: 2`）⇒ 两位评审者
（`reviewer_a` → `glm-5.3`、`reviewer_b` → `kimi-k2.6`）被判进**同一个 phase**。

**四条读数（成对）**：

1. 两位评审者各落一条判词，且**都带同一个 `phase_id`**（落库事实，不是读面推测）；
2. 读面 `panels` 非空、`voters == 2`、`scope == "PHASE"`、`independent is True`；
3. **按压（同模型）**：把 `reviewer_b` 指回 `reviewer_a` 的 profile ⇒ 目标集合收缩成一个，
   `independent` 翻成 `False` 并**点名**那个目标；
4. **反证（不同 phase）**：把第二位评审者挪到**另一个 phase** ⇒ 不聚合（两组各一票）。

第 3、4 条是「结论来自落库事实」的机械证明：改**装配事实**（不是改断言）⇒ 结论必须相反。

**如实边界**：本文件不声称「模型判得对」（那是评审者的事）；也不声称「两个模型不同质化」
（GOAL-084 `W-2` / GOAL-085 `W-3` / 本 GOAL `W-3` 同一条边界）。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from typing import Any

from adapters.canonical.review_read import review_read
from adapters.contracts.protocol_loaders import load_protocol
from packages.application.run_orchestration.commands import StartRunCommand
from packages.domain.core import ID
from packages.domain.enums import ModelBindingMode
from packages.domain.protocols import ProtocolDefinition
from packages.domain.roles import AgentBinding
from tests.api.run_fixtures import make_run_ready_deps
from tests.e2e.scenario import StructuredOutputAgentRuntime

_PROTOCOL = "examples/protocols/review_scored_research_v1.yaml"
_PHASE = "review"
_REVIEWER_ROLE = "scientific_reviewer"
_CONTRACT = "review_scored_deliverable"
#: 受控执行体交付的评审结论（分数 0.95 ≥ 阈值 0.8 ⇒ 验收门判过并落库判词）。
_OUTPUT: dict[str, object] = {"review_decision": {"verdict": "ACCEPT", "score": 0.95}}


@dataclass(frozen=True, slots=True)
class _Run:
    """一次实跑的读数（`records` 是**落库事实**，`payload` 是**读面载荷**）。"""

    state: str
    records: tuple[Any, ...]
    payload: dict[str, Any]

    @property
    def panels(self) -> list[dict[str, Any]]:
        value = self.payload["panels"]
        assert isinstance(value, list), value
        return [item for item in value if isinstance(item, dict)]


def _two_reviewers_on_one_phase() -> ProtocolDefinition:
    """出厂协议的 `review` phase ⇒ `scientific_reviewer` 下限提到 2（其余逐字不动）。"""
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


def _two_phases() -> ProtocolDefinition:
    """**反证臂**：第二位评审者挪到**另一个 phase**（同合约 ⇒ 只有分组键不同）。

    新 phase 与 `review` **无依赖关系**（`depends_on` 空），两者因此都能跑到；协议因此会
    带一条 `DAG_ORPHAN_PHASE` —— 那条 finding 不阻断执行（同一份协议照跑，实测状态
    `SUCCEEDED`），且它**不是**本判据的被测对象。
    """
    protocol = _two_reviewers_on_one_phase()
    single = [
        replace(item, min_instances=1, max_instances=1) if item.role == _REVIEWER_ROLE else item
        for item in protocol.phases[0].required_roles
    ]
    first = replace(protocol.phases[0], required_roles=single)
    second = replace(first, id=f"{_PHASE}_second")
    return ProtocolDefinition(id=protocol.id, version=protocol.version, phases=[first, second])


def _press_same_model(catalog: Any) -> Any:
    """**按压**：`reviewer_b` 改用 `reviewer_a` 的 profile ⇒ 解析后的目标收缩成一个。"""
    agents = dict(catalog.agents)
    agents["reviewer_b"] = replace(
        agents["reviewer_b"],
        model_binding=AgentBinding(mode=ModelBindingMode.MODEL_PROFILE, value="critic_independent"),
    )
    return replace(catalog, agents=agents)


def _run(protocol: ProtocolDefinition, *, press_same_model: bool = False) -> _Run:
    """启动一次 run 并读**落库记录** + **读面载荷**（两者都经产品路径）。"""
    deps = make_run_ready_deps()
    service = deps.runs
    assert service is not None, "run-ready 装配必须带编排服务"
    deps.runs = type(service)(
        replace(
            service._deps,
            runtime=StructuredOutputAgentRuntime(structured_output=dict(_OUTPUT)),
        )
    )
    base = deps.preflight_override
    assert base is not None, "run-ready 夹具必须给出 preflight_override"
    catalog = _press_same_model(base.catalog) if press_same_model else base.catalog
    context = replace(base, catalog=catalog)
    outcome = deps.runs.start_run(
        protocol,
        context.catalog,
        context.project,
        context,
        StartRunCommand(
            project_id=context.project.project_id,
            protocol_id=protocol.id,
            run_id=ID.generate(),
            trace_id=f"goal086-{uuid.uuid4()}",
        ),
    )
    run_id = str(outcome.run_id)
    store = deps.review_findings
    assert store is not None, "run-ready 装配必须带评审结论存储"
    records = store.for_run(run_id)
    payload = review_read(store, {"run_id": run_id})
    return _Run(state=str(outcome.state), records=records, payload=payload)


def test_two_reviewers_on_one_phase_form_one_panel() -> None:
    """① 同一 phase 的两位评审者 ⇒ 一份小组、两票、各自点名自己的模型目标。"""
    result = _run(_two_reviewers_on_one_phase())
    assert result.state == "SUCCEEDED", (result.state, result.payload)
    assert len(result.records) == 2, [(item.task_id, item.phase_id) for item in result.records]
    # 落库事实：两条判词**同 phase**、**不同任务**、**不同模型目标**
    assert {item.phase_id for item in result.records} == {_PHASE}
    assert len({item.task_id for item in result.records}) == 2
    assert {item.finding.reviewer_model for item in result.records} == {
        "main/glm-5.3",
        "main/kimi-k2.6",
    }
    panels = result.panels
    assert len(panels) == 1, panels
    panel = panels[0]
    assert panel["scope"] == "PHASE", panel
    assert panel["phase_id"] == _PHASE, panel
    assert panel["contract_id"] == _CONTRACT, panel
    assert panel["voters"] == 2, panel
    assert panel["independent"] is True, panel


def test_pressing_the_second_reviewer_to_the_first_model_flips_independence() -> None:
    """② **按压**：把 `reviewer_b` 指回 `reviewer_a` 的 profile ⇒ 目标收缩、判不独立并点名。"""
    result = _run(_two_reviewers_on_one_phase(), press_same_model=True)
    assert result.state == "SUCCEEDED", (result.state, result.payload)
    panels = result.panels
    assert len(panels) == 1, panels
    panel = panels[0]
    assert panel["targets"] == ["main/glm-5.3"], panel
    assert panel["independent"] is False, panel
    assert any("main/glm-5.3" in note for note in panel["independence_notes"]), panel


def test_reviewers_on_different_phases_do_not_share_a_panel() -> None:
    """③ **反证**：两位评审者在**不同 phase** ⇒ 各自一票，谁都不聚合成小组。"""
    result = _run(_two_phases())
    assert result.state == "SUCCEEDED", (result.state, result.payload)
    assert len(result.records) == 2, [(item.task_id, item.phase_id) for item in result.records]
    assert len({item.phase_id for item in result.records}) == 2
    assert result.panels == [], result.panels
    assert result.payload["panel_count"] == 0
