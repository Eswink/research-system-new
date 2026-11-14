"""GOAL-20261114-113 EC-06/EC-07 判据：condenser **护栏**与**只读读数**。

- EC-06①（装配真的在）：两个 `PolicyEnforcingAgent` 构造点装出的 agent 都带
  `LLMSummarizingCondenser(max_size=80, keep_first=4)`，且**复用 agent 的同一个
  `llm`**（`usage_id` 共享 ⇒ 指纹面仍单值 —— C-4 的机械形态）；`max_tokens` 为
  `None`（不触发 HARD 路径）。
- EC-06②（不触发）：当前 shape（≈12 个 view event）在护栏下**零**触发理由。
- EC-06③（真的会压）：合成 >80 view event ⇒ 触发理由出现、求值要求为 SOFT
  （事件数压力是软要求）、被摘要的事件**不含首 4 条**（keep_first 承重）。
- EC-07（只读读数）：sink 注入 ⇒ 终态采样 `view_events` / `prompt_tokens_total`
  两个 metric；sink 缺省 None ⇒ 零采样（既有语义逐字不变）。

全程零出网：condensation 判定走 `get_condensation_reasons` /
`_get_forgotten_events`（纯函数，不调 `llm.completion`）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openhands.sdk.context.condenser.base import CondensationRequirement
from openhands.sdk.context.condenser.llm_summarizing_condenser import Reason
from openhands.sdk.context.view import View
from openhands.sdk.event.llm_convertible import MessageEvent
from openhands.sdk.llm import Message, TextContent
from openhands.sdk.testing import TestLLM
from openhands.sdk.workspace.local import LocalWorkspace

from adapters.fakes import FakeCredentialResolver, FakePolicyEvaluator
from adapters.openhands.runtime_adapter import OpenHandsRuntimeAdapter
from adapters.openhands.session_builder import _context_guardrail
from adapters.openhands.session_types import AdapterDependencies
from packages.application.observability.attributes import MetricKind, MetricName, MetricSample
from packages.application.ports.agent_runtime import AgentSessionSpec
from packages.domain.enums import PolicyDecision
from packages.domain.session_state import AgentSessionState
from tests.contracts.fixtures import agent_spec, research_task, role_definition, task_contract

_CURRENT_SHAPE_EVENTS = 12


def _spec() -> AgentSessionSpec:
    return AgentSessionSpec(
        task_id=research_task().id,
        task_contract=task_contract(),
        role=role_definition(),
        agent=agent_spec(),
    )


class _RecordingSink:
    """TelemetrySink Protocol 的**只记录**测试实现（fail-open 不是本判据的对象）。"""

    def __init__(self) -> None:
        self.samples: list[MetricSample] = []

    def begin_operation(self, begin: object) -> None:
        return None

    def end_operation(self, end: object) -> None:
        return None

    def record_metric(self, sample: MetricSample) -> None:
        self.samples.append(sample)


def _make_adapter(
    tmp_path: Path,
    *,
    telemetry: object | None = None,
) -> OpenHandsRuntimeAdapter:
    llm = TestLLM.from_messages([Message(role="assistant", content=[TextContent(text="Done.")])])
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir(exist_ok=True)
    deps = AdapterDependencies(
        credential_resolver=FakeCredentialResolver({"LLM_KEY": "sk-test"}),
        policy_evaluator=FakePolicyEvaluator(default=PolicyDecision.ALLOW),
        build_llm=lambda spec: llm,
        build_workspace=lambda lease, session_id: LocalWorkspace(working_dir=str(workspace_root)),
        persistence_dir=str(tmp_path / "persist"),
        telemetry=telemetry,
    )
    return OpenHandsRuntimeAdapter(deps)


def _session_agent(runtime: OpenHandsRuntimeAdapter, session_id: str) -> object:
    """经 adapter 自己的装配（`SessionBuilder.build_session`）取出**真在跑**的 agent。"""
    entry = runtime._sessions[session_id]
    return entry.conversation.agent


def _view_with(events: int) -> View:
    return View.from_events([
        MessageEvent(
            source="user",
            llm_message=Message(role="user", content=[TextContent(text=f"event-{i}")]),
        )
        for i in range(events)
    ])


class TestTheGuardrailIsInstalled:
    def test_the_default_agent_carries_the_condenser_reusing_the_same_llm(
        self, tmp_path: Path
    ) -> None:
        runtime = _make_adapter(tmp_path)
        handle = runtime.create_session(_spec())
        agent: Any = _session_agent(runtime, handle.session_id)
        condenser = getattr(agent, "condenser", None)
        assert condenser is not None, "护栏必须真的装上（两处构造点共用同一 helper）"
        assert condenser.max_size == 80, condenser
        assert condenser.keep_first == 4, ("keep_first 是承重的（首 4 条不摘要）", condenser)
        assert condenser.max_tokens is None, ("不设 token 阈值 ⇒ 不触发 HARD 路径", condenser)
        assert condenser.llm.usage_id == agent.llm.usage_id, (
            "摘要必须复用 agent 的同一 llm（usage_id/Metrics 共享 ⇒ 指纹仍单值）"
        )


class TestTheGuardrailDoesNotFireOnTheCurrentShape:
    def test_a_view_within_the_measured_shape_has_no_condensation_reasons(self) -> None:
        runtime_deps_llm = TestLLM.from_messages([])
        condenser = _context_guardrail(runtime_deps_llm)
        reasons = condenser.get_condensation_reasons(_view_with(_CURRENT_SHAPE_EVENTS))
        assert reasons == set(), (
            "实测 message_count 2×9/1×2 的 shape 在护栏下不触发",
            reasons,
        )


class TestTheGuardrailCondensesWhenPressed:
    def test_a_view_over_max_size_is_condensed_and_the_first_four_events_survive(self) -> None:
        llm = TestLLM.from_messages([])
        condenser = _context_guardrail(llm)
        view = _view_with(81)
        reasons = condenser.get_condensation_reasons(view)
        assert Reason.EVENTS in reasons, ("合成 >80 view event ⇒ 触发理由出现", reasons)
        assert condenser.condensation_requirement(view) is CondensationRequirement.SOFT, (
            "事件数压力按 SDK 语义是软要求（agent 会压缩）",
        )
        forgotten, summary_offset = condenser._get_forgotten_events(view)  # noqa: SLF001
        assert forgotten, ("真的有事件进入摘要", len(forgotten))
        assert summary_offset >= condenser.keep_first, (
            "首 4 条事件不被摘要（keep_first 承重）",
            summary_offset,
        )
        forgotten_ids = {event.id for event in forgotten}
        for kept in view.events[: condenser.keep_first]:
            assert kept.id not in forgotten_ids, (
                "keep_first 挡住的条目逐个点名",
                kept.id,
            )


class TestContextReadingsAreSampled:
    def test_terminal_readings_reach_the_injected_sink(self, tmp_path: Path) -> None:
        sink = _RecordingSink()
        runtime = _make_adapter(tmp_path, telemetry=sink)
        handle = runtime.create_session(_spec())
        runtime.run(handle.session_id)
        names = [sample.name for sample in sink.samples]
        assert MetricName.SESSION_VIEW_EVENTS in names, names
        assert MetricName.SESSION_PROMPT_TOKENS_TOTAL in names, names
        view_events = next(s for s in sink.samples if s.name is MetricName.SESSION_VIEW_EVENTS)
        assert view_events.kind is MetricKind.COUNTER and view_events.value > 0, view_events
        assert isinstance(view_events.value, int), ("COUNTER 必须是 int", view_events)

    def test_without_a_sink_nothing_is_sampled(self, tmp_path: Path) -> None:
        runtime = _make_adapter(tmp_path, telemetry=None)
        handle = runtime.create_session(_spec())
        result = runtime.run(handle.session_id)
        assert result.status == AgentSessionState.State.SUCCEEDED, result.status
        assert runtime._builder._telemetry is None  # noqa: SLF001
