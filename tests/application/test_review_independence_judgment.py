"""GOAL-20261018-084 EC-02 / EC-03：**判定面按解析后的目标**（含 fallback 相交）。

**EC-02**：判定比较的是**解析后的目标**，不是绑定 id —— 出厂目录下评审者与生产者
**必须判绿**（本轮接入了第三方模型），把评审者指回生产者的模型 ⇒ **必须判红**。
**EC-03**：profile 的 fallback 是「可能落到」的面 ⇒ 相交即判出并点名相交目标；
清空 fallback ⇒ 相交消失。

解析面本身的判据在 `test_review_independence.py`。
"""

from __future__ import annotations

from dataclasses import replace

from adapters.contracts.models_loaders import load_model_profiles, load_models
from adapters.contracts.roles_loaders import load_agents
from packages.application.ports import CatalogSnapshot
from packages.application.preflight.review_independence import resolve_agent_targets
from packages.application.preflight.role_checks import check_heterogeneity
from packages.domain.enums import ReviewPanelRole
from packages.domain.models import ModelProfile
from tests.application.review_independence_fixtures import (
    FACTORY_ENDPOINT,
    PRODUCER_MODEL_NAME,
    REVIEWER_MODEL_NAME,
    REVIEWER_ROLE,
    SECOND_REVIEWER_MODEL_NAME,
    WRITER_ROLE,
    agent,
    binding_explicit,
    binding_profile,
    catalog,
    compile_plan,
    context,
    model,
    panel_catalog,
    panel_role,
    with_model_names,
)

VIOLATION = "HETEROGENEITY_VIOLATION"


# --------------------------------------------- EC-02 出厂目录的真实读数


def test_the_factory_reviewer_and_producer_sit_on_different_underlying_models() -> None:
    """**本轮落地后的真实读数**：评审者的 `(endpoint, model_name)` 与生产者**不同**。"""
    models = load_models("examples/config/models.yaml")
    profiles = load_model_profiles("examples/config/model_profiles.yaml")
    agents = load_agents("examples/config/agents.yaml")
    snapshot = CatalogSnapshot(models=models, model_profiles=profiles, agents=agents, roles={})
    producer = resolve_agent_targets("writer", agents["writer"], snapshot)
    reviewer_a = resolve_agent_targets("reviewer_a", agents["reviewer_a"], snapshot)
    reviewer_b = resolve_agent_targets("reviewer_b", agents["reviewer_b"], snapshot)
    assert producer.resolved and reviewer_a.resolved and reviewer_b.resolved
    assert producer.targets == {(FACTORY_ENDPOINT, PRODUCER_MODEL_NAME)}, producer.targets
    assert reviewer_a.targets == {(FACTORY_ENDPOINT, REVIEWER_MODEL_NAME)}, reviewer_a.targets
    assert reviewer_b.targets == {(FACTORY_ENDPOINT, SECOND_REVIEWER_MODEL_NAME)}, (
        reviewer_b.targets
    )
    # 受判面非空 + **逐对**比较（不是并集掩蔽）
    assert producer.targets and reviewer_a.targets and reviewer_b.targets
    assert not (producer.targets & reviewer_a.targets)
    assert not (producer.targets & reviewer_b.targets)
    assert not (reviewer_a.targets & reviewer_b.targets)


def test_the_critic_profile_no_longer_falls_back_to_the_producers_model() -> None:
    """`critic_independent` 原先 fallback 到 `research_alpha`（生产者模型）⇒ 已移除。"""
    profiles = load_model_profiles("examples/config/model_profiles.yaml")
    models = load_models("examples/config/models.yaml")
    critic = profiles["critic_independent"]
    assert critic.primary == "reviewer_independent"
    assert critic.fallback == [], critic.fallback
    producer_names = {models[profiles["research_strong"].primary].model_name} | {
        models[item].model_name for item in profiles["research_strong"].fallback
    }
    critic_names = {models[critic.primary].model_name} | {
        models[item].model_name for item in critic.fallback
    }
    assert not (producer_names & critic_names)


def test_the_gate_passes_for_distinct_underlying_models() -> None:
    """**正向**：底层模型不同 ⇒ 无 finding（受判面非空：两个 agent 都被解析到）。"""
    snapshot = panel_catalog(producer="prod", reviewer="rev", profiles={})
    snapshot = with_model_names(snapshot, prod=PRODUCER_MODEL_NAME, rev=REVIEWER_MODEL_NAME)
    plan = compile_plan(snapshot)
    assert set(plan.resolved_models.values()) == {"prod", "rev"}, plan.resolved_models
    assert check_heterogeneity(plan, context(snapshot)) == []


def test_the_gate_fails_when_two_ids_share_one_underlying_model_name() -> None:
    """**反向**：id 不同、`model_name` 相同 ⇒ **判红并点名该目标**。"""
    snapshot = panel_catalog(producer="prod", reviewer="rev", profiles={})
    snapshot = with_model_names(snapshot, prod=PRODUCER_MODEL_NAME, rev=PRODUCER_MODEL_NAME)
    plan = compile_plan(snapshot)
    findings = check_heterogeneity(plan, context(snapshot))
    assert [item.code for item in findings] == [VIOLATION], findings
    assert f"ep/{PRODUCER_MODEL_NAME}" in findings[0].message, findings[0].message
    assert WRITER_ROLE in findings[0].message and REVIEWER_ROLE in findings[0].message


def test_binding_ids_alone_do_not_decide_independence() -> None:
    """**判据面差异的机械证明**：绑定 id 完全相同，只改 `model_name` ⇒ 结论翻转。"""
    same = with_model_names(
        panel_catalog(producer="prod", reviewer="rev", profiles={}),
        prod="same-underlying",
        rev="same-underlying",
    )
    distinct = with_model_names(
        panel_catalog(producer="prod", reviewer="rev", profiles={}),
        prod="producer-underlying",
        rev="reviewer-underlying",
    )
    same_plan, distinct_plan = compile_plan(same), compile_plan(distinct)
    assert same_plan.resolved_models == distinct_plan.resolved_models, (
        same_plan.resolved_models,
        distinct_plan.resolved_models,
    )
    assert check_heterogeneity(same_plan, context(same)), "同 model_name 必须判红"
    assert check_heterogeneity(distinct_plan, context(distinct)) == [], "异 model_name 必须判绿"


# -------------------------------------------------- EC-03 fallback 路径


def _fallback_pair(*, with_fallback: bool) -> CatalogSnapshot:
    models = {
        "prod": model("prod", model_name="producer-underlying"),
        "rev": model("rev", model_name="reviewer-underlying"),
    }
    writer_profile = (
        ModelProfile(id="writer_profile", primary="prod", fallback=["rev"])
        if with_fallback
        else ModelProfile(id="writer_profile", primary="prod")
    )
    return catalog(
        models=models,
        profiles={
            "writer_profile": writer_profile,
            "reviewer_profile": ModelProfile(id="reviewer_profile", primary="rev"),
        },
        agents={
            "w": agent("w", WRITER_ROLE, binding_profile("writer_profile")),
            "r": agent("r", REVIEWER_ROLE, binding_profile("reviewer_profile")),
        },
        roles={
            WRITER_ROLE: panel_role(WRITER_ROLE, ReviewPanelRole.WRITER),
            REVIEWER_ROLE: panel_role(REVIEWER_ROLE, ReviewPanelRole.REVIEWER),
        },
    )


def test_a_fallback_creates_the_overlap_even_when_primaries_differ() -> None:
    """primary 不同，但生产者侧的 fallback 落到评审者的模型 ⇒ **相交**。"""
    snapshot = _fallback_pair(with_fallback=True)
    plan = compile_plan(snapshot)
    # 受判面非空：primary 确实不同（否则本条测不到 fallback）
    assert plan.resolved_models == {"w": "prod", "r": "rev"}, plan.resolved_models
    findings = check_heterogeneity(plan, context(snapshot))
    assert [item.code for item in findings] == [VIOLATION], findings
    assert "ep/reviewer-underlying" in findings[0].message, findings[0].message


def test_clearing_the_fallback_removes_the_overlap() -> None:
    """**反证**：把 fallback 清空 ⇒ 相交消失（证明相交真的来自 fallback）。"""
    with_fallback = _fallback_pair(with_fallback=True)
    without_fallback = _fallback_pair(with_fallback=False)
    assert check_heterogeneity(compile_plan(with_fallback), context(with_fallback)), (
        "有 fallback ⇒ 必须判红（否则本条测不到 fallback）"
    )
    assert check_heterogeneity(compile_plan(without_fallback), context(without_fallback)) == [], (
        "清空 fallback ⇒ 必须判绿"
    )


def test_an_unresolvable_role_is_named_instead_of_silently_passing() -> None:
    """**解析失败要点名**：reviewer 的绑定指向未注册模型 ⇒ `MODEL_MISSING`
    （而不是「没有交集 ⇒ 判绿」）。

    这条钉的是**假绿形态**：解析失败的 agent 不在 `plan.resolved_models` 里，
    若判定面直接跳过它，writer/reviewer 两边就「没有交集」⇒ 静默判绿。
    """
    snapshot = catalog(
        models={"prod": model("prod", model_name="producer-underlying")},
        profiles={},
        agents={
            "w": agent("w", WRITER_ROLE, binding_explicit("prod")),
            "r": agent("r", REVIEWER_ROLE, binding_explicit("ghost")),
        },
        roles={
            WRITER_ROLE: panel_role(WRITER_ROLE, ReviewPanelRole.WRITER),
            REVIEWER_ROLE: panel_role(REVIEWER_ROLE, ReviewPanelRole.REVIEWER),
        },
    )
    plan = compile_plan(snapshot)
    assert plan.resolved_models == {"w": "prod"}, plan.resolved_models
    findings = check_heterogeneity(plan, context(snapshot))
    assert [item.code for item in findings] == ["MODEL_MISSING"], findings
    assert "ghost" in findings[0].message, findings[0].message
    assert findings[0].subject_ref == f"role:{REVIEWER_ROLE}", findings[0].subject_ref


def test_a_fallback_to_a_producer_model_is_caught_through_a_profile() -> None:
    """**生产者的 fallback 落到评审者模型** 与 **评审者的 fallback 落到生产者模型**
    是两个方向，都要判出（`replace` 只换 fallback，其余逐字不变）。"""
    snapshot = _fallback_pair(with_fallback=False)
    reviewer_side = replace(
        snapshot,
        model_profiles={
            **snapshot.model_profiles,
            "reviewer_profile": ModelProfile(
                id="reviewer_profile", primary="rev", fallback=["prod"]
            ),
        },
    )
    plan = compile_plan(reviewer_side)
    assert plan.resolved_models == {"w": "prod", "r": "rev"}, plan.resolved_models
    findings = check_heterogeneity(plan, context(reviewer_side))
    assert [item.code for item in findings] == [VIOLATION], findings
    assert "ep/producer-underlying" in findings[0].message, findings[0].message
