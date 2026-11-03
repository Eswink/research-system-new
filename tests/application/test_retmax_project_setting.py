"""`retmax` 的四级回落（GOAL-20261101-103 EC-05）。

**它补哪一格**：`retmax`（每次检索取几条）此前只到**进程级环境变量**
（`RESEARCHOS_RETMAX`，GOAL-20261029-100 EC-04）⇒ 同一控制面上的两个项目无法有不同的
检索深度。本轮把「项目声明」插进这条路，并钉住三件事：

1. **四级顺序**：显式参数 > 项目声明 > 环境变量 > 默认 3（逐级按压，每级都有一条）；
2. **不声明 ⇒ 逐字段不变**：`project_retmax is None` 时生成的调用表必须与改动前**逐字段**
   相同（这是"插一级不改变既有行为"的机械证据，不是一句声明）；
3. **非法值仍点名拒绝**（项目面与 env 面同一条范围规则）—— 不给项目面开后门。

**射程边界（如实登记）**：本文件判的是 `retrieval_wiring` 这一层的回落与校验；
「组合根把 `ProjectSettings.retmax` 真的传进来」由 `catalog.ProjectSettings` 的字段
判据（`test_project_settings_round_trips_retmax`）与本文件最后一节共同钉住。
"""

from __future__ import annotations

import pytest

from packages.application.ports.resource_catalog import ProjectSettings
from services.api.retrieval_wiring import (
    DEFAULT_RETMAX,
    MAX_RETMAX,
    RETMAX_ENV,
    configured_retmax,
    retrieval_calls,
)


def _hits(calls: tuple[object, ...]) -> object:
    """两步链里**第一步**的 `retmax` 固定参数（第二步没有它）。"""
    return getattr(calls[0], "fixed_arguments")["retmax"]


# ------------------------------------------------------------------------------- 四级回落


def test_the_default_is_three_when_nothing_is_declared() -> None:
    """四级全空 ⇒ 3（与改动前的字面量 `{"retmax": 3}` 逐字段相同）。"""
    assert configured_retmax({}) == DEFAULT_RETMAX == 3


def test_the_project_declaration_beats_the_environment() -> None:
    """**项目声明 > 环境变量**（本轮新增的那一级）。"""
    assert configured_retmax({RETMAX_ENV: "9"}, project_retmax=5) == 5


def test_the_environment_still_applies_when_the_project_declares_nothing() -> None:
    """未声明项目设置 ⇒ 回落 env（**不声明时行为逐字不变**）。"""
    assert configured_retmax({RETMAX_ENV: "9"}, project_retmax=None) == 9


def test_the_explicit_argument_beats_everything() -> None:
    """显式参数最高（运维/判据通道不因项目声明而失效）。"""
    calls = retrieval_calls(7, project_retmax=5)
    assert _hits(calls) == 7


def test_the_project_declaration_reaches_the_generated_calls() -> None:
    """项目声明**真的进了调用表**（不是只进了函数签名）。"""
    calls = retrieval_calls(project_retmax=11)
    assert _hits(calls) == 11


def test_without_a_project_declaration_the_call_table_is_unchanged() -> None:
    """**零回归**：不传 `project_retmax` 时，调用表与"只有 env 那一级"时逐字段相同。"""
    baseline = retrieval_calls()
    same = retrieval_calls(project_retmax=None)
    assert [_fields(call) for call in baseline] == [_fields(call) for call in same]
    assert _hits(baseline) == DEFAULT_RETMAX


def _fields(call: object) -> tuple[object, ...]:
    """调用声明的**全部字段**（用来做逐字段相等，不只看 retmax）。"""
    return (
        getattr(call, "provider_id"),
        getattr(call, "tool_id"),
        getattr(call, "capability"),
        getattr(call, "arguments_from_input"),
        tuple(sorted(getattr(call, "fixed_arguments").items())),
        getattr(call, "phase_id"),
    )


# --------------------------------------------------------------------------- 非法值仍拒绝


@pytest.mark.parametrize("bad", [0, -1, MAX_RETMAX + 1, 10_000])
def test_an_out_of_range_project_declaration_is_named(bad: int) -> None:
    """项目声明越界 ⇒ **点名**拒绝（不静默夹到边界、不回落默认）。"""
    with pytest.raises(ValueError, match="project retmax must be between"):
        configured_retmax({}, project_retmax=bad)


def test_a_non_integer_project_declaration_is_named() -> None:
    """`retmax: "three"` 是**拼错**，不是"用默认值" —— 静默回落会让两者不可区分。"""
    with pytest.raises(ValueError, match="must be an integer"):
        ProjectSettings.from_mapping(
            "p1",
            {
                "team_template": "t",
                "budget": "b",
                "workspace_backend": "w",
                "retmax": "three",
            },
        )


def test_an_out_of_range_environment_value_is_still_named() -> None:
    """env 面的既有拒绝语义逐字不变（这一级没有因为新增项目面而放松）。"""
    with pytest.raises(ValueError, match=RETMAX_ENV):
        configured_retmax({RETMAX_ENV: str(MAX_RETMAX + 1)})


def test_a_boolean_project_declaration_is_named() -> None:
    """`True` 是 `int` 的子类 —— 必须显式拒绝，否则 `retmax: true` 会变成 1。"""
    with pytest.raises(ValueError, match="must be an integer"):
        ProjectSettings.from_mapping(
            "p1",
            {"team_template": "t", "budget": "b", "workspace_backend": "w", "retmax": True},
        )


# ----------------------------------------------------------------- ProjectSettings 的字段面


def test_project_settings_default_retmax_is_undeclared() -> None:
    """**`None` = 未声明**（GOAL-20261103-105 EC-03 改写了这一条）。

    这条判据此前断言「缺省 3」—— 它钉住的正是本轮修掉的缺陷。缺省 `3` 让「未声明」与
    「声明 3」不可区分，于是施加点把字段缺省当成一次声明 ⇒ 项目未声明时运行期恒被压成 3。
    现在缺省必须是 `None`，且**既有构造点不用改**（`ProjectSettings(...)` 的十几处调用现场
    零改动 —— 它们不传这个字段，语义从「声明 3」变成「未声明」）。
    """
    settings = ProjectSettings(
        project_id="p1",
        team_template_id="t",
        default_model_profile_id=None,
        budget_policy_id="b",
        workspace_backend="w",
    )
    assert settings.retmax is None, "缺省必须是 None（未声明）；缺省 3 会把「未声明」抹平成一次声明"
    assert settings.retmax != DEFAULT_RETMAX, "未声明与「声明 3」必须是两个不同的事实"


def test_an_absent_mapping_key_reads_back_as_undeclared() -> None:
    """`from_mapping` 缺键 ⇒ `None`（不是 3）：持久化面同样保留「未声明」。"""
    settings = ProjectSettings.from_mapping(
        "p1", {"team_template": "t", "budget": "b", "workspace_backend": "w"}
    )
    assert settings.retmax is None


def test_an_explicit_three_is_distinguishable_from_no_declaration() -> None:
    """**声明 3** 与 **未声明** 必须可区分 —— 这正是缺陷的判据面。

    声明 3 ⇒ 压过 env；未声明 ⇒ 不施加。两者若折成同一个值，下面两条断言里必有一条红。
    """
    declared = ProjectSettings.from_mapping(
        "p1", {"team_template": "t", "budget": "b", "workspace_backend": "w", "retmax": 3}
    )
    undeclared = ProjectSettings.from_mapping(
        "p1", {"team_template": "t", "budget": "b", "workspace_backend": "w"}
    )
    assert declared.retmax == 3 and undeclared.retmax is None
    assert configured_retmax({RETMAX_ENV: "9"}, project_retmax=declared.retmax) == 3
    assert configured_retmax({RETMAX_ENV: "9"}, project_retmax=undeclared.retmax) == 9


def test_project_settings_round_trips_retmax() -> None:
    """`from_mapping` 能把声明读进字段（组合根从这里取，见下一节）。"""
    settings = ProjectSettings.from_mapping(
        "p1",
        {"team_template": "t", "budget": "b", "workspace_backend": "w", "retmax": 42},
    )
    assert settings.retmax == 42


def test_the_run_wiring_passes_the_project_declaration() -> None:
    """**接线真的接了**：`runner_wiring` 把本 run 项目的 `retmax` 补进能力装配。

    只断言字段存在是不够的 —— 一个字段可以在 `ProjectSettings` 里、而运行时从不读它
    （本仓反复修掉的"声明了但从未构造"）。取值点**必须**在 `RunContext` 已知之后：
    进程级装配面（`deps.capabilities`）只造一次，在那里取值会把第一个项目的设置施加给
    之后所有项目。所以判据钉的是 `runner_wiring` 的调用点，不是 `composition.py`。
    """
    from pathlib import Path

    source = (
        Path("packages/application/run_orchestration/runner_wiring.py").read_bytes().decode("utf-8")
    )
    assert "_with_project_retmax(" in source, (
        "runner_wiring 必须把项目声明的 retmax 补进 capabilities（否则字段只到目录、到不了调用表）"
    )
    assert "context" in source, "取值必须来自本 run 的 RunContext（项目级声明的唯一正确来源）"
    # 施加点：真正把声明落到调用参数上的那个函数（`phase_call_arguments.apply_retmax`）。
    # GOAL-20261103-105 EC-03 起，施加的**取值**由 `_retmax_for_phase` 决定（协议相级优先，
    # `deps.retmax` 只承载项目那一级）—— 所以这里判的是「施加点用的是那个取值函数」，
    # 而不是某个已经被重构掉的字面调用式。行为由 `test_the_capability_step_really_applies_
    # the_declaration` 与 `test_retmax_undeclared_is_a_fact.py` 钉住。
    capabilities = (
        Path("packages/application/run_orchestration/phase_capabilities.py")
        .read_bytes()
        .decode("utf-8")
    )
    assert "apply_retmax(declared, retmax_for_phase(spec, deps))" in capabilities, (
        "能力步必须真的施加 retmax（否则 `CapabilityDeps.retmax` 是一个死字段）"
    )
    # 取值函数必须真的读 `deps.retmax`（项目声明那一级不许被协议相级整条替掉）。
    arguments = (
        Path("packages/application/run_orchestration/phase_call_arguments.py")
        .read_bytes()
        .decode("utf-8")
    )
    assert 'getattr(deps, "retmax", None)' in arguments, (
        "`retmax_for_phase` 必须回落到 `deps.retmax`（项目声明那一级）"
    )


def test_the_capability_step_really_applies_the_declaration() -> None:
    """**行为**判据：`execute_run_chain_capabilities` 收到的调用里 `retmax` 真的变了。

    与上面几条源码判据成对：源码判据钉「代码在」，这一条钉「行为真的变了」。
    没有它，`apply_retmax` 可以被调用而返回值被丢弃 —— 那是假绿。
    """
    from packages.application.run_orchestration import phase_call_arguments as pca
    from packages.application.run_orchestration.phase_capabilities import RunChainCall

    base = RunChainCall(
        provider_id="europe_pmc",
        tool_id="literature_search",
        capability="literature.search",
        arguments_from_input=("research_question.query",),
        fixed_arguments={"retmax": 3},
        phase_id="retrieval",
    )
    calls = (base,)

    unchanged = pca.apply_retmax(calls, None)
    assert unchanged is calls, "未声明项目设置 ⇒ 必须原样返回（连对象都不新造）"

    applied = pca.apply_retmax(calls, 17)
    assert applied[0].fixed_arguments["retmax"] == 17
    assert calls[0].fixed_arguments["retmax"] == 3, "原对象不得被改写"


def test_a_call_without_retmax_is_not_touched() -> None:
    """**射程边界**：没有 `retmax` 键的调用（读取步）不被塞参数 —— 那是伪造调用。"""
    from packages.application.run_orchestration import phase_call_arguments as pca
    from packages.application.run_orchestration.phase_capabilities import RunChainCall

    read_call = RunChainCall(
        provider_id="europe_pmc",
        tool_id="literature_read",
        capability="literature.read",
        ids_from_previous="ids",
        fixed_arguments={},
        phase_id="retrieval",
    )
    applied = pca.apply_retmax((read_call,), 17)
    assert applied[0].fixed_arguments == {}, "读取步不认识 retmax ⇒ 不得被塞参数"
