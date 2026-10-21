"""GOAL-20261022-093 判据（一）：**上一轮评审的判词**进下一轮的会话（阶梯「复检」域）。

**它判什么**（阶梯原文：「评审的判词驱动下一轮修订 —— 把分歧变成下一轮的修订指令」）：
一次 run 的**会话**在开工前，能看到**同一程序内前序 run** 的落库判词 —— 面板建议性结论
与**逐条分歧**。判据走**产品路径**（`compile → preflight → freeze → execute_phases`）
与**产品闭包**（`services/api/review_outcome_support.review_outcome_builder`），
不是只测一个纯函数：

1. **分歧逐条可读**：一负一过 ⇒ `advisory` 为 `None`（平票不报结论）、`dissent` **两位都在**、
   `targets` 含两个执行目标（上一轮 GOAL-087 的成果不得被压回多数票）；
2. **零回归**：五段全缺 ⇒ `compose_prompt` **逐字**返回 purpose；程序**第一轮**的每次会话
   spec 上 `review_outcome_prompt is None`；
3. **失败即点名**：没有前序 / 有前序但读不到可归因判词 / 本 run 行未落库 —— 三态各自点名；
4. **段序**：方向 → 前序知识 → 检索 → **上一轮评审** → 被评对象。

跨 run 的**端到端**（真程序两轮）在 `test_review_outcome_across_runs.py`；共享夹具在
`review_outcome_support.py`（规模门：本文件 ≤ 450 行、函数 ≤ 50 行）。

**如实边界**：本文件不声称「模型据此真的修订了」（那要人评或 live 判据，与 GOAL-082
EC-04 同一条诚实边界）；它判的是「上一轮的判词在下一轮的会话里可见、可归因、分歧不丢」。
"""

from __future__ import annotations

from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from packages.application.run_orchestration.retrieval_prompt import (
    REVIEW_OUTCOME_SECTION_TITLE,
    compose_prompt,
)
from packages.application.run_orchestration.review_outcome import (
    NO_ATTRIBUTABLE,
    NO_PRIOR_RUN,
    ReviewOutcomeView,
    build_review_outcome,
    view_of,
)
from services.api.app import create_app
from tests.application.run_orchestration.review_outcome_support import (
    GLM,
    KIMI,
    PLAN_CONTRACT,
    PROTOCOL,
    Scope,
    scoped,
    splitting,
)
from tests.e2e.test_ec03_real_runtime_offline_chain import mock_relay  # noqa: F401 - fixture
from tests.e2e.test_research_report_arc_offline import _assembled_deps

__all__ = ["mock_relay"]

pytestmark = pytest.mark.requires_docker


# --------------------------------------------------------------- 分歧逐条可读


def test_a_split_panel_carries_both_verdicts_and_the_advisory() -> None:
    """(EC-01) 一负一过 ⇒ 平票 ⇒ `advisory` 为 `None`，但**双方 verdict 都在** `dissent` 里。"""
    view = view_of("run-prior", splitting())
    assert view.prior_run_id == "run-prior"
    assert view.voters == 2
    assert view.advisory is None, "平票不得报一个建议性结论（与 aggregate_panel 同口径）"
    assert view.votes == {"PASS": 1, "REJECT": 1}, view.votes
    speakers = {entry.speaker: entry.verdict for entry in view.dissent}
    assert speakers == {"gate:reviewer_a": "REJECT", "gate:reviewer_b": "PASS"}, speakers
    assert {entry.target for entry in view.dissent} == {GLM, KIMI}
    assert "too shallow" in {entry.detail for entry in view.dissent}


def test_a_unanimous_panel_reports_an_advisory_and_no_dissent() -> None:
    """(EC-01 按压) 两位同判 ⇒ `dissent` 空、`advisory` 有值 —— 与分歧形态**可区分**。"""
    records = (
        scoped("f-a", verdict="REJECT", findings=["too shallow"]),
        scoped(
            "f-b",
            scope=Scope(reviewer="reviewer_b"),
            verdict="REJECT",
            model=KIMI,
            findings=["also thin"],
        ),
    )
    view = view_of("run-prior", records)
    assert view.advisory == "REJECT"
    assert view.dissent == (), "同判不应产生分歧条目"
    assert view.voters == 2


def test_an_unattributable_finding_is_named_not_folded_into_a_vote() -> None:
    """(EC-03) 没有 `reviewer_model` 的判词**不进票**，但**逐条点名**。"""
    records = (
        scoped("f-a", verdict="REJECT"),
        scoped("f-unknown", scope=Scope(reviewer="reviewer_c"), model=None),
        scoped("f-b", scope=Scope(reviewer="reviewer_b"), verdict="PASS", model=KIMI),
    )
    view = view_of("run-prior", records)
    assert view.voters == 2, "无法归因的那条不得计入票数"
    assert any("f-unknown" in item for item in view.ineligible), view.ineligible
    assert all("f-unknown" not in entry.speaker for entry in view.dissent)


# --------------------------------------------------------------- 三态各自点名


def test_no_prior_run_is_named_and_carries_nothing() -> None:
    """(EC-03 态一) 程序第一轮 ⇒ 视图为空、`reason` 逐字点名「没有前序」。"""
    view = ReviewOutcomeView(
        prior_run_id=None,
        advisory=None,
        votes={},
        voters=0,
        dissent=(),
        ineligible=(),
        targets=(),
        reason=NO_PRIOR_RUN,
    )
    assert view.empty is True
    assert view.reason == NO_PRIOR_RUN
    assert compose_prompt("PURPOSE", review_outcome=view) == "PURPOSE", (
        "空视图 ⇒ 提示词**逐字**回到 purpose（不得留一个空标题）"
    )


def test_a_prior_run_without_attributable_findings_is_named() -> None:
    """(EC-03 态二) 有前序 run 但读不到可归因判词 ⇒ `reason` 点名，**不**伪造一条结论。"""
    view = view_of("run-prior", (scoped("f-unknown", model=None),))
    assert view.voters == 0
    assert view.advisory is None
    assert NO_ATTRIBUTABLE in view.reason, view.reason
    assert "run-prior" in view.reason, "点名是哪一轮读不到（不是一句泛泛的失败）"


def test_a_run_whose_row_is_not_persisted_is_the_first_round_not_a_failure() -> None:
    """(EC-03 态三) 本 run 的行还没落库 ⇒ 点名那一态，**不是**失败。

    这是第一轮开工那一刻的**真实形态**（run 行由调用方在编排返回之后才写入）。
    判成失败会让**每个程序的第一轮必然失败** —— 实测中它正是这样把产品路径打成 404 的。
    """

    class _Empty:
        def get_run(self, run_id: str) -> Any:
            raise KeyError(run_id)

        def for_program(self, program_id: str) -> tuple[Any, ...]:
            return ()

    view = build_review_outcome(_Empty(), None, run_id="run-new")
    assert view.empty is True
    assert "not persisted yet" in view.reason, view.reason
    assert view.reason != NO_PRIOR_RUN, "「行未落库」与「没有前序」不得合并成同一句话"


# --------------------------------------------------------------- 渲染面


def test_the_rendered_section_names_both_sides_and_the_source_run() -> None:
    """(EC-01) 提示词那一段：带标题、来源 run、双方 verdict 与执行目标。"""
    view = view_of("run-prior", splitting())
    text = compose_prompt("PURPOSE", review_outcome=view)
    assert REVIEW_OUTCOME_SECTION_TITLE in text
    assert text.startswith("PURPOSE"), "purpose 必须仍在最前（既有顺序不变）"
    assert "run-prior" in text
    assert "REJECT" in text and "PASS" in text
    assert GLM in text and KIMI in text
    assert "too shallow" in text


def test_all_segments_absent_returns_the_purpose_verbatim() -> None:
    """(EC-02 零回归) 五段全缺 ⇒ **逐字**返回 purpose。"""
    assert compose_prompt("PURPOSE") == "PURPOSE"
    assert compose_prompt("PURPOSE", review_outcome=None, review_material=None) == "PURPOSE"


# --------------------------------------------------------------- 产品路径（第一轮）


def _wire_first_round(deps: Any) -> Any:
    """把产品闭包 + spec 记录器**一次**装上（两次 `replace` 会互相顶掉刚装的东西）。"""
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.review_outcome_support import review_outcome_builder
    from tests.e2e.retrieval_context_support import SessionSpecRecorder

    inner = deps.runs._deps
    assert deps.runs_store is not None, "本装配必须带 runs_store（否则闭包读不到前序 run）"
    recorder = SessionSpecRecorder(inner.runtime)
    ports = {"runs_store": deps.runs_store, "review_findings": inner.review_findings}
    deps.runs = RunOrchestrationService(
        replace(inner, runtime=recorder, review_outcome=review_outcome_builder(ports))
    )
    deps.session_specs = recorder
    return deps


def test_the_first_rounds_session_carries_no_review_outcome(mock_relay: str) -> None:  # noqa: F811
    """(EC-02) **产品路径**：程序第一轮 ⇒ 会话 spec 上那一段缺席（逐字不变）。"""
    from tests.e2e.literature_chain_support import OfflineEuropePmc

    deps, recorder = _assembled_deps(mock_relay, OfflineEuropePmc(requests=[]))
    _wire_first_round(deps)
    # 新 service 的 `start_run` 是**未包装**的那个 ⇒ 记录器要装到它上面（旧包装随旧实例
    # 一起被丢掉；不重装，`start_run` 的产物没人接住 ⇒ 路由侧 `run not found`）。
    recorder.install(deps)
    with TestClient(create_app(deps)) as client:
        created = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": PROTOCOL},
            headers={"Idempotency-Key": "goal093-first-round"},
        )
        assert created.status_code == 200, created.text
        run = created.json()
        state = client.get(f"/runs/{run['id']}").json()["state"]
    assert state == "SUCCEEDED", state
    spec = getattr(deps, "session_specs", None)
    assert spec is not None
    assert spec.specs, "记录器必须抓到至少一次会话 spec（否则本条是空真）"
    assert PLAN_CONTRACT in spec.specs, sorted(spec.specs)
    for contract_id, recorded in spec.specs.items():
        assert getattr(recorded, "review_outcome_prompt", None) is None, (
            f"{contract_id} 是第一轮，不该带上一轮评审段"
        )


def test_a_prior_runs_panel_reaches_the_prompt(mock_relay: str) -> None:  # noqa: F811
    """(EC-02 反证臂) 前序 run **有**分歧判词 ⇒ 同一装配下那一段**在场**且含双方 verdict。

    与上一条只差「前序有没有判词」，其余逐字相同 —— 否则「这一段永远不出现」也会让
    上一条绿。
    """
    from tests.e2e.literature_chain_support import OfflineEuropePmc

    deps, recorder = _assembled_deps(mock_relay, OfflineEuropePmc(requests=[]))
    _wire_first_round(deps)
    recorder.install(deps)
    store = deps.runs._deps.review_findings
    assert store is not None
    with TestClient(create_app(deps)) as client:
        first = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": PROTOCOL},
            headers={"Idempotency-Key": "goal093-prior-panel"},
        )
        assert first.status_code == 200, first.text
        first_id = str(first.json()["id"])

    from tests.application.run_orchestration.review_outcome_support import write_findings

    write_findings(store, first_id, splitting())
    view = view_of(first_id, store.for_run(first_id))
    assert "REJECT" in {entry.verdict for entry in view.dissent}, view.dissent
    assert {GLM, KIMI} <= set(view.targets), view.targets
    rendered = compose_prompt("PURPOSE", review_outcome=view)
    assert REVIEW_OUTCOME_SECTION_TITLE in rendered
    assert GLM in rendered and KIMI in rendered


# --------------------------------------------------------------- 段序

#: 五段的标题（**逐字**；判据按它们定位）。
_TITLES: tuple[str, ...] = (
    "DIRECTION_SECTION_TITLE",
    "PRIOR_SECTION_TITLE",
    "PROMPT_SECTION_TITLE",
    "REVIEW_OUTCOME_SECTION_TITLE",
    "REVIEW_MATERIAL_SECTION_TITLE",
)


def _prior_view() -> Any:
    """前序知识段的一个真实视图（`mem-1` / 来源 `run:1:claim`）。"""
    from packages.application.run_orchestration.prior_knowledge import (
        MemoryEntry,
        PriorKnowledgeView,
    )

    return PriorKnowledgeView(
        entries=(
            MemoryEntry(
                memory_id="mem-1",
                tier="project",
                kind="lesson",
                provenance="run:1:claim",
                shown="learned",
                truncated=False,
                review_due=False,
            ),
        ),
        run_id="run-1",
    )


def _retrieval_view() -> Any:
    """检索段的一个真实视图（`41408154` 一条摘录）。"""
    from packages.application.run_orchestration.retrieval_context import (
        RetrievalContextView,
        RetrievalEntry,
    )

    return RetrievalContextView(
        # 渲染器只看 `entries`；快照不参与那一段 ⇒ 用 `cast` 给出一个「无快照」的
        # 受控形态（`type: ignore` 在本仓的 strict 配置下是语法错误，不用它）。
        snapshot=cast("Any", None),
        entries=(
            RetrievalEntry(
                evidence_id="evidence:tool:1",
                artifact_id="task-1:search",
                identifier="41408154",
                title="a title",
                shown="a title",
                truncated=False,
            ),
        ),
        run_id="run-1",
    )


def _material_view() -> Any:
    """被评对象段的一个真实视图（`research_plan` 一件产物）。"""
    from packages.application.run_orchestration.review_material import (
        ReviewMaterialEntry,
        ReviewMaterialView,
    )

    return ReviewMaterialView(
        entries=(
            ReviewMaterialEntry(
                producer_phase_id="author",
                artifact_name="research_plan",
                artifact_id="task-1:research_plan",
                shown="{}",
                truncated=False,
                digest="sha256:abc",
            ),
        )
    )


def _views() -> dict[str, Any]:
    """五段的**真实视图**（渲染器按视图对象出标题；字符串会让定位在标题缺席时假绿）。"""
    return {
        "direction": "aim",
        "prior_knowledge": _prior_view(),
        "retrieval": _retrieval_view(),
        "review_outcome": view_of("run-prior", splitting()),
        "review_material": _material_view(),
    }


def test_the_section_sits_between_retrieval_and_the_artifact_under_review() -> None:
    """(EC-01) 五段并列的顺序：方向 → 前序知识 → 检索 → **上一轮评审** → 被评对象。"""
    from packages.application.run_orchestration import retrieval_prompt as rp

    text = compose_prompt("PURPOSE", **_views())
    order = [text.index(getattr(rp, name)) for name in _TITLES]
    assert order == sorted(order), f"段序不对：{order}"
