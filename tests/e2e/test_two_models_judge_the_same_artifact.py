"""GOAL-20261020-091 EC-03：**两个不同的模型对同一件上游产物各判一次**，分歧可读。

**它补哪一格**：阶梯「复检」域的 `下一级` 是「评审真的用不同模型判出负」。GOAL-084…087 已把
三件事补齐（配置不相交 / 判词可归因且可聚合 / 同 phase 成组且一位判负不取消同批），但
**结构上仍做不到**「判出不同结论」—— 本轮建档实测出两处阻断，本文件判它们被修掉：

1. 真实会话的交付物是**信封**（正文在 `content` 里），`REVIEW_SCORE` 只按顶层点分路径取值
   ⇒ 判词恒 `review score unknown` ⇒ 恒判负。**两个模型无论各自判什么，判定面看到的都是
   同一个「不知道」**（EC-01 修掉；本文件在**运行链**上取证，不只看纯函数）；
2. 上游产物只以**证据**身份落库、不进评审者的提示词 ⇒ 两位评的**不是同一件东西**
   （EC-02 修掉；本文件取证「两位评审者的提示词里是**同一份**被评对象」）。

**四条读数（成对，全部走 `deps.runs.start_run`）**：

1. **不同目标 + 同一被评对象**：两位评审者各落一条判词，`reviewer_model` 互不相同；两条
   判词的 `phase_id` 相同（同一被评对象那一格）、`task_id` 不同；两份**提示词**里的
   `UNDER REVIEW` 段**逐字相同**（同一份产物、同一摘录）；
2. **构造的分歧**：同一份被评对象上，一位给 0.95（判过）、另一位给 0.4（判负）⇒ 两条
   verdict **相异**、`panels[0].dissent` **非空**且逐条点名；
3. **反证（独立性失效）**：把 `reviewer_b` 指回 `reviewer_a` 的模型 ⇒ `independent` 判否
   并点名那个目标（改的是**装配事实**，不是断言）；
4. **反证（单评审不聚合）**：只声明一位评审 ⇒ `panels == []`（既有读面形态不变）。

**如实边界**：本文件用**受控执行体**证明「分歧可表达、可归因、可读、且两位读的是同一件
东西」；真实中转站上两位模型**是否真的**给出不同结论属 live 观察（`EC-04`），不在本文件。
本文件**不**声称评审判得对。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from typing import Any

from adapters.canonical.review_read import review_read
from adapters.contracts.protocol_loaders import load_protocol
from packages.application.run_orchestration.commands import StartRunCommand
from packages.application.run_orchestration.retrieval_prompt import (
    REVIEW_MATERIAL_SECTION_TITLE,
)
from packages.application.run_orchestration.review_material import build_review_material
from packages.domain.core import ID
from packages.domain.enums import ModelBindingMode
from packages.domain.protocols import ProtocolDefinition
from packages.domain.roles import AgentBinding
from tests.api.run_fixtures import make_run_ready_deps
from tests.e2e.scenario import StructuredOutputAgentRuntime

_PROTOCOL = "examples/protocols/dual_model_review_v1.yaml"
_PHASE = "review"
_AUTHOR_PHASE = "author"
_REVIEWER_ROLE = "scientific_reviewer"
_CONTRACT = "dual_model_review_deliverable"
_PLAN_CONTRACT = "dual_model_review_plan"
#: 被评对象（作者写的产物）——两位评审者读到的必须是**这一份**。
_PLAN: dict[str, object] = {
    "research_plan": {
        "question": "does exact-match indexing reduce duplicate storage at equal recall?",
        "hypothesis": "an exact-match index cuts duplicate pairs without lowering recall",
        "refutation_test": "recall drops below 0.9 at equal duplicate-pair settings",
    }
}
#: 两位评审者的**判分**（受控执行体声明；分数跨过阈值 0.8 ⇒ 一位判过、一位判负）。
_PASS: dict[str, object] = {
    "review_decision": {
        "verdict": "ACCEPT",
        "score": 0.95,
        "weakest_link": "the refutation test does not name a sample size",
    }
}
_FAIL: dict[str, object] = {
    "review_decision": {
        "verdict": "REJECT",
        "score": 0.4,
        "weakest_link": "the hypothesis is not falsifiable as written",
    }
}


@dataclass(frozen=True, slots=True)
class _Run:
    state: str
    message: str
    records: tuple[Any, ...]
    payload: dict[str, Any]
    prompts: dict[str, str]

    @property
    def review_records(self) -> tuple[Any, ...]:
        """**评审格**的判词（按合约筛）。

        落库面同时记**每一位**任务的门结论（作者那一格也有一条 —— 那是产品既有语义：
        「门判过」与「门根本没跑」必须可区分）。本文件的被测对象是**评审格的两位**，
        按合约筛选而不是按条数假设（作者格有没有判词不该影响本文件）。
        """
        return tuple(item for item in self.records if item.contract_id == _CONTRACT)

    @property
    def panels(self) -> list[dict[str, Any]]:
        value = self.payload["panels"]
        assert isinstance(value, list), value
        return [item for item in value if isinstance(item, dict)]

    def by_model(self) -> dict[str, Any]:
        return {str(item.finding.reviewer_model): item for item in self.review_records}


def _protocol(*, reviewers: int = 2) -> ProtocolDefinition:
    """出厂协议的 `review` phase ⇒ 评审者数量（其余逐字不动）。"""
    protocol = load_protocol(_PROTOCOL)
    phases = []
    for phase in protocol.phases:
        if phase.id != _PHASE:
            phases.append(phase)
            continue
        roles = [
            replace(item, min_instances=reviewers, max_instances=reviewers)
            if item.role == _REVIEWER_ROLE
            else item
            for item in phase.required_roles
        ]
        phases.append(replace(phase, required_roles=roles))
    return ProtocolDefinition(id=protocol.id, version=protocol.version, phases=phases)


def _press_same_model(catalog: Any) -> Any:
    """**反证**：`reviewer_b` 改用 `reviewer_a` 的 profile ⇒ 解析后的目标收缩成一个。"""
    agents = dict(catalog.agents)
    agents["reviewer_b"] = replace(
        agents["reviewer_b"],
        model_binding=AgentBinding(mode=ModelBindingMode.MODEL_PROFILE, value="critic_independent"),
    )
    return replace(catalog, agents=agents)


def _prompt_recorder(runtime: Any) -> Any:
    """包一层 execution 体：记下**每个会话收到的提示词**（观察、不改行为）。"""
    return _PromptRecordingRuntime(runtime)


class _PromptRecordingRuntime(StructuredOutputAgentRuntime):
    """按 agent id 给出交付物，并记下 spec 上的 `review_material_prompt`。"""

    def __init__(self, by_agent: dict[str, dict[str, object]]) -> None:
        super().__init__()
        self._by_agent: dict[str, dict[str, object]] = {
            key: dict(value) for key, value in by_agent.items()
        }
        self.prompts: dict[str, str] = {}

    def create_session(self, spec: Any) -> Any:
        agent_id = spec.agent.id
        if spec.review_material_prompt is not None:
            self.prompts[agent_id] = spec.review_material_prompt
        return super().create_session(spec)

    def _output_for(self, session_id: str) -> dict[str, object]:
        spec = self._specs.get(session_id)
        if spec is not None and spec.agent.id in self._by_agent:
            return dict(self._by_agent[spec.agent.id])
        return super()._output_for(session_id)


def build_review_material_for(task: Any, declared: Any) -> Any:
    """装配器（与产品闭包 `review_material_builder` 同签名；workflow 由本次 run 提供）。

    这里刻意**不**用夹具的 workflow：`build_review_material` 需要它解析产出方的真实任务
    身份，而 run-ready 装配的 `deps.workflow` 就是那一个。
    """

    workflow = _ACTIVE_WORKFLOW.get("current")
    assert workflow is not None, "装配器必须在 run 进行中被调用"
    artifacts = _ACTIVE_WORKFLOW["artifacts"]
    return build_review_material(workflow, artifacts, task, declared)


_ACTIVE_WORKFLOW: dict[str, Any] = {}


def test_the_two_reviewers_run_on_different_targets_and_read_the_same_artifact() -> None:
    """① 不同目标 + 同一被评对象（落库事实 + 提示词逐字比对）。"""
    result = _run_with_workflow()
    assert result.state == "FAILED", (result.state, result.message)
    reviews = result.review_records
    assert len(reviews) == 2, [(item.task_id, item.finding.reviewed_by) for item in reviews]
    models = {str(item.finding.reviewer_model) for item in reviews}
    assert models == {"main/glm-5.3", "main/kimi-k2.6"}, models
    # 同一被评对象那一格：同 phase、不同任务。
    assert {item.phase_id for item in reviews} == {_PHASE}
    assert len({item.task_id for item in reviews}) == 2
    # 两份提示词里的**被评对象段**逐字相同（同一份产物、同一摘录 ⇒ 同一道题）。
    assert set(result.prompts) == {"reviewer_a", "reviewer_b"}, result.prompts
    sections = {_section(text) for text in result.prompts.values()}
    assert len(sections) == 1, sections
    assert REVIEW_MATERIAL_SECTION_TITLE in sections.pop()


def test_a_constructed_split_produces_two_verdicts_and_a_readable_dissent() -> None:
    """② 构造的分歧：同一被评对象、0.95 vs 0.4 ⇒ verdict 相异、`dissent` 非空且点名。"""
    result = _run_with_workflow()
    by_model = result.by_model()
    assert by_model["main/glm-5.3"].finding.verdict == "PASS", by_model["main/glm-5.3"].finding
    assert by_model["main/kimi-k2.6"].finding.verdict == "REJECT", by_model[
        "main/kimi-k2.6"
    ].finding
    panels = result.panels
    assert len(panels) == 1, panels
    panel = panels[0]
    assert panel["votes"] == {"PASS": 1, "REJECT": 1}, panel
    assert panel["independent"] is True, panel
    dissent = panel["dissent"]
    assert dissent, panel
    assert any("REJECT" in item for item in dissent), dissent
    # 判负那位在失败消息里被**逐条点名**（不只说「评审拒了」）。
    assert "main/kimi-k2.6=REJECT" in result.message, result.message


def test_pressing_both_reviewers_to_one_model_flips_independence() -> None:
    """③ 反证：同目标 ⇒ 独立性判否并点名（结论来自落库事实，不是读面编造）。"""
    result = _run_with_workflow(press_same_model=True)
    panels = result.panels
    assert len(panels) == 1, panels
    panel = panels[0]
    assert panel["targets"] == ["main/glm-5.3"], panel
    assert panel["independent"] is False, panel
    assert any("main/glm-5.3" in note for note in panel["independence_notes"]), panel


def test_a_single_reviewer_produces_no_panel() -> None:
    """④ 反证：单评审 ⇒ `panels == []`（既有读面形态不变，单评审不聚合）。"""
    result = _run_with_workflow(reviewers=1)
    reviews = result.review_records
    assert len(reviews) == 1, [item.task_id for item in reviews]
    assert result.panels == [], result.panels
    assert result.payload["panel_count"] == 0


def _section(prompt: str) -> str:
    """提示词里的**被评对象段**（从标题到文末；用于两位评审者的逐字比对）。"""
    index = prompt.find(REVIEW_MATERIAL_SECTION_TITLE)
    assert index != -1, prompt
    return prompt[index:]


def _run_with_workflow(**kwargs: Any) -> _Run:
    """把本次装配的 workflow/artifacts 暴露给装配器（`build_review_material` 需要）。"""
    deps = make_run_ready_deps()
    base = deps.preflight_override
    assert base is not None
    catalog = _press_same_model(base.catalog) if kwargs.get("press_same_model") else base.catalog
    context = replace(base, catalog=catalog)
    service = deps.runs
    assert service is not None
    runtime = _PromptRecordingRuntime({"director": _PLAN, "reviewer_a": _PASS, "reviewer_b": _FAIL})
    inner = service._deps
    _ACTIVE_WORKFLOW.clear()
    _ACTIVE_WORKFLOW.update({"current": inner.workflow, "artifacts": inner.artifacts})
    try:
        deps.runs = type(service)(
            replace(inner, runtime=runtime, review_material=build_review_material_for)
        )
        protocol = _protocol(reviewers=int(kwargs.get("reviewers", 2)))
        outcome = deps.runs.start_run(
            protocol,
            context.catalog,
            context.project,
            context,
            StartRunCommand(
                project_id=context.project.project_id,
                protocol_id=protocol.id,
                run_id=ID.generate(),
                trace_id=f"goal091-{uuid.uuid4()}",
            ),
        )
    finally:
        _ACTIVE_WORKFLOW.clear()
    run_id = str(outcome.run_id)
    store = deps.review_findings
    assert store is not None
    return _Run(
        state=str(outcome.state),
        message=str(outcome.message),
        records=store.for_run(run_id),
        payload=review_read(store, {"run_id": run_id}),
        prompts=dict(runtime.prompts),
    )
