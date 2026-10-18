"""GOAL-20261018-084 EC-04 判据：独立性判据**接进产品路径**且默认零回归。

三条成对读数：

1. **命中 ⇒ 点名拒绝**：构造一个「writer 与 reviewer 落到同一目标」的目录 ⇒
   `check_heterogeneity` 给出 `HETEROGENEITY_VIOLATION`，判词**点名**那个目标
   （`endpoint/model_name`）与两侧角色；
2. **不相交 ⇒ 不判**：把 reviewer 换成不同 `model_name` ⇒ 零 finding；
3. **按压**：把判据的解析回落关掉（模拟「只比 id」的旧口径）⇒ 同一份目录**变绿**
   —— 证明拒绝来自**目标比较**，不是别处顺手拒的。

**为什么这算「接进产品路径」**：`check_heterogeneity` 由 `packages/application/preflight`
的 `check_team` 调用，`check_team` 由 `run_preflight` 调用 —— 那是 `compile_and_preflight`
→ `freeze_manifest` 的必经之路（AGENTS.md §3：Preflight 未通过不得进入 RUNNING）。
本判据不新造入口，钉的是那条既有链。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from packages.application.preflight import role_checks
from packages.application.preflight.role_checks import check_heterogeneity
from packages.domain.enums import ModelBindingMode, ReviewPanelRole
from packages.domain.models import ModelDefinition
from packages.domain.roles import AgentSpec, RoleDefinition
from tests.application import protocol_fixtures as fixtures_mod
from tests.application import test_m4_heterogeneity as _m4

_WRITER = "writer-role"
_REVIEWER = "reviewer-role"


def _role(role_id: str, *, capabilities: list[str]) -> RoleDefinition:
    return _m4._role(role_id, capabilities=capabilities)  # noqa: SLF001


def _panel_role(role: RoleDefinition, panel: ReviewPanelRole) -> RoleDefinition:
    return replace(role, review_panel_role=panel)


def _agent(agent_id: str, role_id: str, model_id: str) -> AgentSpec:
    from packages.domain.roles import AgentBinding

    return AgentSpec(
        id=agent_id,
        role=role_id,
        model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value=model_id),
    )


def _catalog_with(*, reviewer_model_name: str) -> Any:
    """writer 用 `model-a`（name=`shared-name`），reviewer 的 `model_name` 由参数决定。"""
    base = _m4._catalog(  # noqa: SLF001
        roles={
            _WRITER: _panel_role(
                _role(_WRITER, capabilities=["deliverable.write"]), ReviewPanelRole.WRITER
            ),
            _REVIEWER: _panel_role(
                _role(_REVIEWER, capabilities=["review.write"]), ReviewPanelRole.REVIEWER
            ),
        },
        agents={
            "writer": _agent("writer", _WRITER, "model-a"),
            "reviewer": _agent("reviewer", _REVIEWER, "model-b"),
        },
    )
    return replace(
        base,
        models={
            **base.models,
            "model-a": ModelDefinition(id="model-a", endpoint_id="ep", model_name="shared-name"),
            "model-b": ModelDefinition(
                id="model-b", endpoint_id="ep", model_name=reviewer_model_name
            ),
        },
        model_profiles=dict(base.model_profiles),
    )


def _plan_for(catalog: Any) -> Any:
    from packages.domain.protocols import RoleRequirement

    return _m4._compile(  # noqa: SLF001
        catalog,
        _m4._protocol([  # noqa: SLF001
            RoleRequirement(_WRITER, 1, 1),
            RoleRequirement(_REVIEWER, 1, 1),
        ]),
    )


def test_the_gate_rejects_a_shared_underlying_model_and_names_the_target() -> None:
    """**命中 ⇒ 点名拒绝**：判词含目标（`ep/shared-name`）与两侧角色 id。"""
    catalog = _catalog_with(reviewer_model_name="shared-name")
    findings = check_heterogeneity(_plan_for(catalog), fixtures_mod.context(catalog))

    codes = [item.code for item in findings]
    assert "HETEROGENEITY_VIOLATION" in codes, codes
    joined = " ".join(item.message for item in findings)
    assert "ep/shared-name" in joined, ("判词必须点名**解析后的目标**", joined)
    assert _WRITER in joined and _REVIEWER in joined, joined


def test_the_gate_passes_when_the_underlying_models_differ() -> None:
    """**不相交 ⇒ 不判**（不同 `model_name`）。"""
    catalog = _catalog_with(reviewer_model_name="reviewer-name")
    findings = check_heterogeneity(_plan_for(catalog), fixtures_mod.context(catalog))
    assert findings == []


def test_press_comparing_ids_only_would_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    """**按压**：把「解析后的目标」这条路径关掉（回落成 model id 比较）⇒ 同一目录**变绿**。

    与第一条成对：同一份目录、只改「判据比什么」⇒ 读数相反。证明拒绝来自**目标比较**。
    """
    catalog = _catalog_with(reviewer_model_name="shared-name")
    plan = _plan_for(catalog)
    context = fixtures_mod.context(catalog)
    assert check_heterogeneity(plan, context), "前置：正常情况下应判违规"

    monkeypatch.setattr(role_checks, "resolve_targets_by_role", lambda *args, **kwargs: ({}, {}))
    assert check_heterogeneity(plan, context) == [], (
        "关掉目标解析后应回落到 model id 口径 ⇒ id 不同 ⇒ 判绿"
    )


def test_the_gate_reads_the_same_resolution_helper() -> None:
    """**同源**：门链用的就是 `review_independence` 那个解析器（不是第二套实现）。"""
    assert role_checks.resolve_targets_by_role is not None
    import packages.application.preflight.review_independence as module

    assert role_checks.describe_target is module.describe_target


def test_profiles_and_models_are_not_hardcoded_in_the_check() -> None:
    """判据不写死 agent/model 名：源码里不出现出厂目录的具体标识。"""
    import inspect

    body = inspect.getsource(role_checks._panel_role_map)  # noqa: SLF001
    for literal in ("research_strong", "reviewer_gamma", "research_alpha"):
        assert literal not in body, literal

