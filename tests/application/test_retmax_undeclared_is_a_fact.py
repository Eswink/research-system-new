"""`retmax` 的**缺省抹平**缺陷（GOAL-20261103-105 EC-03）。

**它补哪一格**：文档口径写的是四级回落（显式 > 项目 > env > 默认 3），而产品路径实测
**只有一级** —— `ProjectSettings.retmax` 的缺省是 `3`（不是 `None`），于是

    RESEARCHOS_RETMAX=9  → 构造期 retrieval_calls() 给 {"retmax": 9}
    _with_project_retmax → CapabilityDeps.retmax = 3   （产品路径上该值本是 None）
    apply_retmax(calls, 3) → {"retmax": 3}            ← env 被抹平

同一形态在**显式参数**上更严重：`retrieval_calls(7)` 构造期 7、运行期 3。根因是一句话：
**字段的缺省值被当成了一次声明**。

**本文件判什么**（三条，每条都走**产品路径**：`_with_project_retmax` → `apply_retmax`，
不是直接调 `apply_retmax` 自证）：

1. `RESEARCHOS_RETMAX=9` + 项目未声明 ⇒ 运行期调用表仍是 9；
2. `retrieval_calls(7)` + 项目未声明 ⇒ 运行期仍是 7；
3. 项目**显式**声明 5 ⇒ 压过 env（已成立的语义不许回归）。

**修法不许是「再叠一层覆盖」**（C-6）：判据 (iii) 与 (i) 成对存在 —— 若把项目缺省改成
「后写覆盖」的兜底值，(i) 会在未声明时仍被某个非 `None` 值压住；(iii) 会在声明时正常。
两条同时绿只有一种解释：**「未声明」是一等事实**（`None`），施加点据此跳过。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, cast

import pytest

from packages.application.ports.resource_catalog import ProjectSettings
from packages.application.run_orchestration.phase_call_arguments import apply_retmax
from packages.application.run_orchestration.runner_wiring import _with_project_retmax
from services.api.retrieval_wiring import DEFAULT_RETMAX, RETMAX_ENV, retrieval_calls


def _hits(calls: tuple[object, ...]) -> object:
    """两步链里**第一步**的 `retmax` 固定参数（第二步没有它）。"""
    return getattr(calls[0], "fixed_arguments")["retmax"]


def _undeclared() -> ProjectSettings:
    """一个**没有声明** `retmax` 的项目（这是产品的默认形态：模板里没有这一项）。"""
    return ProjectSettings.from_mapping(
        "p1", {"team_template": "t", "budget": "b", "workspace_backend": "w"}
    )


def _context(project: ProjectSettings) -> object:
    """`_with_project_retmax` 只读 `context.project` —— 最小替身，不造整个 RunContext。"""
    return _MinimalContext(project=project)


@dataclass(frozen=True, slots=True)
class _MinimalContext:
    """`context.project` 之外的字段在这一条判据里不参与（只读那一个字段）。"""

    project: ProjectSettings | None = None


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """每条判据自带 env 面：不依赖外部环境，也不把值漏给别人。"""
    monkeypatch.delenv(RETMAX_ENV, raising=False)


def test_the_environment_survives_an_undeclared_project_at_runtime() -> None:
    """**(i)** `RESEARCHOS_RETMAX=9` + 项目未声明 ⇒ 运行期调用表仍是 `[9]`。

    修复前实测是 `[3]`。判的是**施加之后**的调用表（走产品装配
    `_with_project_retmax`），因为缺陷就发生在「项目字段 → `CapabilityDeps.retmax`」这一步。
    """
    import os

    os.environ[RETMAX_ENV] = "9"
    try:
        declared = retrieval_calls()
        assert _hits(declared) == 9, "前提：构造期 env 那一级必须生效"
        capabilities = replace(_capabilities(declared), retmax=None)
        wired = _with_project_retmax(capabilities, _context(_undeclared()))
    finally:
        os.environ.pop(RETMAX_ENV, None)
    applied = apply_retmax(wired.calls, wired.retmax)
    assert _hits(applied) == 9, (
        "项目未声明时运行期不得把 retmax 压回缺省值：env 的 9 必须生存（修复前为 3）"
    )


def test_an_explicit_argument_survives_an_undeclared_project_at_runtime() -> None:
    """**(ii)** `retrieval_calls(7)` + 项目未声明 ⇒ 运行期仍是 `[7]`（修复前为 `[3]`）。"""
    declared = retrieval_calls(7)
    assert _hits(declared) == 7, "前提：显式参数在构造期生效"
    capabilities = replace(_capabilities(declared), retmax=None)
    wired = _with_project_retmax(capabilities, _context(_undeclared()))
    applied = apply_retmax(wired.calls, wired.retmax)
    assert _hits(applied) == 7, "项目未声明时运行期不得抹平显式参数（修复前为 3）"


def test_a_declared_project_still_beats_the_environment_at_runtime() -> None:
    """**(iii)** 项目**显式**声明 5 ⇒ 压过 env（已成立的语义不许回归）。"""
    import os

    os.environ[RETMAX_ENV] = "9"
    try:
        calls = retrieval_calls()
        assert _hits(calls) == 9, "前提：构造期 env 生效"
        project = ProjectSettings.from_mapping(
            "p1", {"team_template": "t", "budget": "b", "workspace_backend": "w", "retmax": 5}
        )
        capabilities = replace(_capabilities(calls), retmax=None)
        wired = _with_project_retmax(capabilities, _context(project))
    finally:
        os.environ.pop(RETMAX_ENV, None)
    applied = apply_retmax(wired.calls, wired.retmax)
    assert _hits(applied) == 5, "项目显式声明必须压过 env"


def test_no_declaration_anywhere_still_lands_on_the_default() -> None:
    """全都不声明 ⇒ 默认 3（**这条不能因为修缺陷而变**）。"""
    calls = retrieval_calls()
    capabilities = replace(_capabilities(calls), retmax=None)
    wired = _with_project_retmax(capabilities, _context(_undeclared()))
    assert _hits(apply_retmax(wired.calls, wired.retmax)) == DEFAULT_RETMAX == 3


def test_the_undeclared_path_does_not_even_allocate_a_new_deps() -> None:
    """未声明 ⇒ `_with_project_retmax` **原样返回**（连对象都不新造）。

    这是「未声明是一等事实」最直接的形体：它不进施加面，而不是进了之后被覆盖成同一个值。
    """
    calls = retrieval_calls()
    capabilities = _capabilities(calls)
    wired = _with_project_retmax(capabilities, _context(_undeclared()))
    assert wired is capabilities, "未声明（None）时必须原样返回，不得 replace 出一个新对象"


def _capabilities(calls: tuple[object, ...]) -> Any:
    """能力装配面：本文件只用到 `calls` / `retmax` 两个字段，故用**既有 Fake**（不跑工具）。

    用仓内既有的 `Fake*` 而不是自造哑对象：自造的 `__getattr__` 替身在 strict mypy 下
    与 `ArtifactStore` / `EvidenceLedger` 的协议不一致（全量 m0 的 typecheck 会判红，
    定向套件看不见 —— 这正是「新判据文件自身的缺陷只有全量 m0 抓到」那条）。
    """
    from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger, FakePolicyEvaluator
    from packages.application.run_orchestration.phase_capabilities import CapabilityDeps

    return CapabilityDeps(
        calls=cast(Any, calls),
        providers={},
        provider_specs={},
        policy=FakePolicyEvaluator(),
        artifacts=FakeArtifactStore(),
        ledger=FakeEvidenceLedger(),
    )
