"""GOAL-20261018-084 EC-01 / EC-02 / EC-03 判据：**评审独立性的解析面与判定面**。

**它判什么**：`check_heterogeneity` 早已存在且语义正确，但它比的是 `plan.resolved_models`
里的 **model id**。建档实测：出厂目录里**四个** ModelDefinition
（`agnes_flash` / `research_alpha` / `coding_beta` / `reviewer_gamma`）
**全部** `model_name: deepseek-v4-flash-vision` + `endpoint: main` ⇒ **id 不同、底层同一个**
⇒ 既有的门**判绿**。本文件判新增的**解析面**：

- **EC-01**：一个 agent 的**全部可能执行目标**（primary + **每个** fallback）解析成
  `(endpoint, model_name)` 集合；解析不了 ⇒ **点名**（不静默空集）。
- **EC-02**：判定比较的是**解析后的目标**，不是绑定 id。
- **EC-03**：fallback 路径一并覆盖（`research_strong.fallback` 含 `reviewer_gamma`）。

判据分四组：解析面（EC-01）/ 出厂目录的**真实读数**（EC-02）/ fallback 相交（EC-03）/
**按压**（改 catalog 制造差异 ⇒ 结论翻转）。
"""

from __future__ import annotations

from adapters.contracts.models_loaders import load_model_profiles, load_models
from packages.application.ports import CatalogSnapshot
from packages.application.preflight.review_independence import (
    describe_target,
    resolve_agent_targets,
)
from packages.domain.enums import ModelBindingMode
from packages.domain.models import ModelDefinition, ModelProfile
from packages.domain.roles import AgentBinding, AgentSpec

#: 出厂目录里的真实模型名（**判据里写死**：不 import 产品常量当预言机）。
_FACTORY_MODEL_NAME = "deepseek-v4-flash-vision"
_FACTORY_ENDPOINT = "main"


def _catalog(
    models: dict[str, ModelDefinition],
    profiles: dict[str, ModelProfile],
    agents: dict[str, AgentSpec],
) -> CatalogSnapshot:
    return CatalogSnapshot(models=models, model_profiles=profiles, agents=agents)


def _model(model_id: str, *, model_name: str = "m", endpoint: str = "ep") -> ModelDefinition:
    return ModelDefinition(id=model_id, endpoint_id=endpoint, model_name=model_name)


def _agent(agent_id: str, binding: AgentBinding) -> AgentSpec:
    return AgentSpec(id=agent_id, role="r", model_binding=binding)


def _explicit(model_id: str) -> AgentBinding:
    return AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value=model_id)


def _profile(profile_id: str) -> AgentBinding:
    return AgentBinding(mode=ModelBindingMode.MODEL_PROFILE, value=profile_id)


# ------------------------------------------------------------ EC-01 解析面


def test_explicit_model_resolves_to_one_target() -> None:
    cat = _catalog({"m1": _model("m1", model_name="alpha", endpoint="ep")}, {}, {})
    resolved = resolve_agent_targets("a1", _agent("a1", _explicit("m1")), cat)
    assert resolved.resolved
    assert resolved.targets == {("ep", "alpha")}


def test_profile_includes_primary_and_every_fallback() -> None:
    """**含全部 fallback**（只看 primary 会漏掉「可能回落到同一模型」）。"""
    cat = _catalog(
        {
            "p": _model("p", model_name="primary-name", endpoint="ep"),
            "f1": _model("f1", model_name="fallback-one", endpoint="ep"),
            "f2": _model("f2", model_name="fallback-two", endpoint="other"),
        },
        {"prof": ModelProfile(id="prof", primary="p", fallback=["f1", "f2"])},
        {},
    )
    resolved = resolve_agent_targets("a1", _agent("a1", _profile("prof")), cat)
    assert resolved.targets == {
        ("ep", "primary-name"),
        ("ep", "fallback-one"),
        ("other", "fallback-two"),
    }


def test_same_model_name_on_different_endpoints_is_not_the_same_target() -> None:
    """目标 = `(endpoint, model_name)` 两元组：同名不同 endpoint **不算**同一个。"""
    cat = _catalog(
        {
            "a": _model("a", model_name="same", endpoint="ep-1"),
            "b": _model("b", model_name="same", endpoint="ep-2"),
        },
        {
            "left": ModelProfile(id="left", primary="a"),
            "right": ModelProfile(id="right", primary="b"),
        },
        {},
    )
    left = resolve_agent_targets("l", _agent("l", _profile("left")), cat)
    right = resolve_agent_targets("r", _agent("r", _profile("right")), cat)
    assert left.targets != right.targets
    assert not (left.targets & right.targets)


def test_unresolvable_bindings_are_named_not_silently_empty() -> None:
    """**解析不了 ⇒ 点名**（空集不能被读成「独立」）。"""
    cat = _catalog({}, {}, {})
    missing_model = resolve_agent_targets("a", _agent("a", _explicit("ghost")), cat)
    missing_profile = resolve_agent_targets("b", _agent("b", _profile("nope")), cat)
    inherit = resolve_agent_targets(
        "c", _agent("c", AgentBinding(mode=ModelBindingMode.INHERIT)), cat
    )
    for resolved in (missing_model, missing_profile, inherit):
        assert resolved.problems, resolved
        assert not resolved.resolved


def test_resolution_is_deterministic() -> None:
    """同输入同输出（集合相等；顺序无关）。"""
    cat = _catalog(
        {
            "p": _model("p", model_name="x", endpoint="ep"),
            "f": _model("f", model_name="y", endpoint="ep"),
        },
        {"prof": ModelProfile(id="prof", primary="p", fallback=["f"])},
        {},
    )
    runs = {
        resolve_agent_targets("a", _agent("a", _profile("prof")), cat).targets for _ in range(20)
    }
    assert len(runs) == 1, runs


# ------------------------------------------- EC-02 出厂目录的真实读数


def test_the_factory_catalog_has_the_same_model_name_everywhere() -> None:
    """**建档事实**：出厂目录四个 ModelDefinition 的 `model_name` + `endpoint` 全相同。

    这条断言**钉住事实**（而不是钉住「应该如此」）：它是本 GOAL 存在的理由。
    若将来接入第二个真实模型，**这条会红** —— 那时应当更新本判据与 GOAL 的残余，
    而不是让它默默变绿。
    """
    models = load_models("examples/config/models.yaml")
    targets = {(model.endpoint_id, model.model_name) for model in models.values()}
    assert len(models) >= 4, sorted(models)
    assert targets == {(_FACTORY_ENDPOINT, _FACTORY_MODEL_NAME)}, sorted(targets)


def test_the_reviewer_and_the_producer_resolve_to_the_same_target_in_the_factory() -> None:
    """**EC-02 核心读数**：`research_strong`（生产者）与 `reviewer_gamma`（评审者）
    在出厂目录下**解析到同一个目标** —— 尽管绑定 id / profile 名**不同**。"""
    from services.api.catalog import load_catalog_snapshot

    catalog = load_catalog_snapshot()
    producer = catalog.agents.get("director") or next(
        (
            agent
            for agent in catalog.agents.values()
            if getattr(getattr(agent, "model_binding", None), "value", None) == "research_strong"
        ),
        None,
    )
    reviewer = next(
        (
            agent
            for agent in catalog.agents.values()
            if getattr(getattr(agent, "model_binding", None), "value", None) == "reviewer_gamma"
        ),
        None,
    )
    assert producer is not None and reviewer is not None, sorted(catalog.agents)
    producer_targets = resolve_agent_targets(producer.id, producer, catalog)
    reviewer_targets = resolve_agent_targets(reviewer.id, reviewer, catalog)
    assert producer_targets.resolved and reviewer_targets.resolved
    assert producer_targets.targets & reviewer_targets.targets, (
        "出厂目录下两者必须相交（否则本 GOAL 的建档依据不成立）",
        sorted(producer_targets.targets),
        sorted(reviewer_targets.targets),
    )


def test_comparing_binding_ids_would_have_passed_but_targets_do_not() -> None:
    """**判据面差异的机械证明**：绑定 id 不同、但目标相同。"""
    profile_name, reviewer_model = "research_strong", "reviewer_gamma"
    assert profile_name != reviewer_model  # 名字不同
    producer_model = "research_alpha"
    assert producer_model != reviewer_model  # model id 也不同
    # 但底层目标相同（由下一条断言证明，不在这里重复推理）。
    models = load_models("examples/config/models.yaml")
    assert models["research_alpha"].model_name == models["reviewer_gamma"].model_name
    assert models["research_alpha"].endpoint_id == models["reviewer_gamma"].endpoint_id


# --------------------------------------------------- EC-03 fallback 路径


def test_fallback_creates_a_shared_target_even_when_primary_differs() -> None:
    """**fallback 让 primary 的差异失效**：`left.primary` ≠ `right.primary`，
    但 `left.fallback` 落到 `right.primary` 的同一个目标 ⇒ **相交**。"""
    cat = _catalog(
        {
            "producer": _model("producer", model_name="prod", endpoint="ep"),
            "reviewer": _model("reviewer", model_name="rev", endpoint="ep"),
        },
        {
            "left": ModelProfile(id="left", primary="producer", fallback=["reviewer"]),
            "right": ModelProfile(id="right", primary="reviewer"),
        },
        {},
    )
    left = resolve_agent_targets("l", _agent("l", _profile("left")), cat)
    right = resolve_agent_targets("r", _agent("r", _profile("right")), cat)
    assert left.targets != right.targets, "primary 不同（否则这条用例测不到 fallback）"
    assert left.targets & right.targets == {("ep", "rev")}


def test_clearing_the_fallback_removes_the_overlap() -> None:
    """**反证**：把 fallback 清空 ⇒ 相交消失（证明相交真的来自 fallback）。"""
    models = {
        "producer": _model("producer", model_name="prod", endpoint="ep"),
        "reviewer": _model("reviewer", model_name="rev", endpoint="ep"),
    }
    with_fb = _catalog(
        models,
        {
            "left": ModelProfile(id="left", primary="producer", fallback=["reviewer"]),
            "right": ModelProfile(id="right", primary="reviewer"),
        },
        {},
    )
    without_fb = _catalog(
        models,
        {
            "left": ModelProfile(id="left", primary="producer"),
            "right": ModelProfile(id="right", primary="reviewer"),
        },
        {},
    )
    left_with = resolve_agent_targets("l", _agent("l", _profile("left")), with_fb)
    right = resolve_agent_targets("r", _agent("r", _profile("right")), with_fb)
    assert left_with.targets & right.targets
    left_without = resolve_agent_targets("l", _agent("l", _profile("left")), without_fb)
    assert not (left_without.targets & right.targets)


def test_the_factory_critic_independent_profile_can_fall_back_to_the_producers_model() -> None:
    """**出厂目录的真实读数**：`critic_independent` 的 fallback 含 `research_alpha`
    （生产者用的模型）—— 一个名字就叫「独立评审者」的 profile 可以回落到生产者模型。"""
    profiles = load_model_profiles("examples/config/model_profiles.yaml")
    critic = profiles.get("critic_independent")
    assert critic is not None, sorted(profiles)
    assert "research_alpha" in critic.fallback, critic.fallback
    producer_side = profiles.get("research_strong")
    assert producer_side is not None
    assert producer_side.fallback and "reviewer_gamma" in producer_side.fallback


# --------------------------------------------------------------- 按压


def test_press_a_distinct_model_name_is_judged_independent() -> None:
    """**按压**：把评审者的 model 换成一个**不同 `model_name`** 的定义 ⇒ 目标不相交。

    与前面的相交读数成对：只改「底层模型是否同一个」，其余不变。
    """
    same = _catalog(
        {
            "a": _model("a", model_name="same", endpoint="ep"),
            "b": _model("b", model_name="same", endpoint="ep"),
        },
        {
            "left": ModelProfile(id="left", primary="a"),
            "right": ModelProfile(id="right", primary="b"),
        },
        {},
    )
    distinct = _catalog(
        {
            "a": _model("a", model_name="same", endpoint="ep"),
            "b": _model("b", model_name="other", endpoint="ep"),
        },
        {
            "left": ModelProfile(id="left", primary="a"),
            "right": ModelProfile(id="right", primary="b"),
        },
        {},
    )
    left = resolve_agent_targets("l", _agent("l", _profile("left")), same)
    right = resolve_agent_targets("r", _agent("r", _profile("right")), same)
    assert left.targets & right.targets, "同 model_name ⇒ 必须相交"

    left2 = resolve_agent_targets("l", _agent("l", _profile("left")), distinct)
    right2 = resolve_agent_targets("r", _agent("r", _profile("right")), distinct)
    assert not (left2.targets & right2.targets), "不同 model_name ⇒ 不应相交"


def test_describe_target_is_stable_and_readable() -> None:
    """判词形态稳定（`endpoint/model_name`）：finding 与判据读同一处。"""
    assert describe_target(("main", "deepseek-v4-flash-vision")) == "main/deepseek-v4-flash-vision"
