"""GOAL-20261018-084 EC-01：**解析面**——一个 agent 的全部可能执行目标。

**它补哪一格**：`check_heterogeneity` 早已存在且语义正确（「同一模型不得同时承担 Writer
与 Reviewer」），但它比的是 `plan.resolved_models` 里的 **model id**。出厂目录里多个
ModelDefinition 可以共用同一个 `model_name` ⇒ **id 不同、底层同一个** ⇒ 旧口径判绿。

**EC-01 判什么**：解析出 `(endpoint, model_name)` 集合，**含 profile 的每一个 fallback**；
**确定性纯函数、零出网**；解析不了 ⇒ **点名**（空集被读成「无交集」就是假绿）。

判定面（EC-02）与 fallback 相交（EC-03）判在 `test_review_independence_judgment.py`。
"""

from __future__ import annotations

from dataclasses import replace

from packages.application.preflight.review_independence import (
    describe_target,
    resolve_agent_targets,
)
from packages.domain.enums import ModelBindingMode
from packages.domain.models import ModelProfile
from packages.domain.roles import AgentBinding
from tests.application.review_independence_fixtures import (
    agent,
    binding_explicit,
    binding_profile,
    catalog,
    model,
)


def test_explicit_model_resolves_to_a_single_target() -> None:
    cat = catalog(models={"m1": model("m1", model_name="alpha")}, profiles={}, agents={}, roles={})
    resolved = resolve_agent_targets("a1", agent("a1", "r", binding_explicit("m1")), cat)
    assert resolved.resolved
    assert resolved.targets == {("ep", "alpha")}


def test_profile_includes_primary_and_every_fallback() -> None:
    """**含全部 fallback**：只看 primary 会漏掉「可能回落到同一模型」。"""
    cat = catalog(
        models={
            "p": model("p", model_name="primary-name"),
            "f1": model("f1", model_name="fallback-one"),
            "f2": model("f2", model_name="fallback-two", endpoint="other"),
        },
        profiles={"prof": ModelProfile(id="prof", primary="p", fallback=["f1", "f2"])},
        agents={},
        roles={},
    )
    resolved = resolve_agent_targets("a1", agent("a1", "r", binding_profile("prof")), cat)
    assert resolved.targets == {
        ("ep", "primary-name"),
        ("ep", "fallback-one"),
        ("other", "fallback-two"),
    }


def test_same_model_name_on_different_endpoints_is_a_different_target() -> None:
    """目标 = `(endpoint, model_name)`：同名不同 endpoint **不算**同一个。"""
    cat = catalog(
        models={
            "a": model("a", model_name="same", endpoint="ep-1"),
            "b": model("b", model_name="same", endpoint="ep-2"),
        },
        profiles={
            "left": ModelProfile(id="left", primary="a"),
            "right": ModelProfile(id="right", primary="b"),
        },
        agents={},
        roles={},
    )
    left = resolve_agent_targets("l", agent("l", "r", binding_profile("left")), cat)
    right = resolve_agent_targets("r", agent("r", "r", binding_profile("right")), cat)
    assert left.targets and right.targets
    assert not (left.targets & right.targets)


def test_unresolvable_bindings_are_named_not_silently_empty() -> None:
    """**解析不了 ⇒ 点名**（空集不能被读成「独立」）。"""
    cat = catalog(models={}, profiles={}, agents={}, roles={})
    cases = (
        resolve_agent_targets("a", agent("a", "r", binding_explicit("ghost")), cat),
        resolve_agent_targets("b", agent("b", "r", binding_profile("nope")), cat),
        resolve_agent_targets(
            "c", agent("c", "r", AgentBinding(mode=ModelBindingMode.INHERIT)), cat
        ),
    )
    for resolved in cases:
        assert resolved.problems, resolved
        assert not resolved.resolved


def test_compiled_primary_covers_inherit_bindings_and_still_expands_fallbacks() -> None:
    """**编译期解析值可作 primary**：`INHERIT` 的绑定里没有模型名，只有编译期知道它落到哪；
    同时该绑定的 profile fallback **仍然**要展开（那是运行时可能落到的面）。"""
    cat = catalog(
        models={
            "p": model("p", model_name="primary-name"),
            "f": model("f", model_name="fallback-name"),
        },
        profiles={"prof": ModelProfile(id="prof", primary="p", fallback=["f"])},
        agents={},
        roles={},
    )
    inherited = replace(
        agent("a", "r", binding_profile("prof")),
        model_binding=AgentBinding(mode=ModelBindingMode.INHERIT),
    )
    # 没有编译期解析值 ⇒ 点名（INHERIT 本身不含模型名）
    unresolved = resolve_agent_targets("a", inherited, cat)
    assert not unresolved.resolved and unresolved.problems
    # 给了编译期解析值 ⇒ 解析出 primary + 该 profile 的 fallback
    resolved = resolve_agent_targets("a", inherited, cat, resolved_model_id="p")
    assert resolved.resolved
    assert resolved.targets == {("ep", "primary-name"), ("ep", "fallback-name")}


def test_resolution_is_deterministic() -> None:
    cat = catalog(
        models={"p": model("p", model_name="x"), "f": model("f", model_name="y")},
        profiles={"prof": ModelProfile(id="prof", primary="p", fallback=["f"])},
        agents={},
        roles={},
    )
    runs = {
        resolve_agent_targets("a", agent("a", "r", binding_profile("prof")), cat).targets
        for _ in range(20)
    }
    assert len(runs) == 1, runs


def test_describe_target_is_stable_and_readable() -> None:
    """判词形态稳定（`endpoint/model_name`）：finding 与判据读同一处。"""
    assert describe_target(("main", "glm-5.3")) == "main/glm-5.3"


def test_the_resolver_makes_no_outbound_calls() -> None:
    """**零出网**：解析只读 catalog（源码级钉住 —— 模块不 import 任何网络/网关面）。"""
    from pathlib import Path

    source = Path("packages/application/preflight/review_independence.py").read_text(
        encoding="utf-8"
    )
    forbidden = ("requests", "httpx", "urllib", "socket", "openai", "model_relay", "gateway")
    hits = [
        token for token in forbidden if f"import {token}" in source or f"from {token}" in source
    ]
    assert hits == [], hits
