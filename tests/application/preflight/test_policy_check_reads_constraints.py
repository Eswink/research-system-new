"""GOAL-20261111-112 EC-03：preflight **核验约束形状**（独立取证）。

与 `test_constraint_table.py` 的 `TestPreflight` 分工：那份在对抗矩阵里跑一条（`max_seconds`
类型错）；本文件把**四种形状错误各判一次**，并判「合法声明不产 finding」这条零回归线。

**为什么值得单列**：`preflight` 是**冻结前**唯一的批量判定面——它放过的形状错误会一直走到
实验执行边界才被拒（或更糟：根本没人拒）。这条线因此不能只靠一条臂。
"""

from __future__ import annotations

import pytest

from packages.application.experiments import constraint_table
from packages.application.ports.policy_evaluator import PolicyEvaluation
from packages.application.ports.resource_catalog import ProjectSettings
from packages.application.preflight.policy_check import _evaluate_requirement
from packages.application.tool_plane import build_tool_catalog
from packages.domain.enums import PolicyDecision
from tests.application.tool_plane_support import make_manifest, make_provider, make_tool


def _catalog() -> object:
    provider = make_provider("europe-pmc", capabilities=("literature.search",))
    tool = make_tool("literature_search", capabilities=("literature.search",))
    manifest = make_manifest(tools=(tool,), capabilities=("literature.search",), pack_id="lit-pack")
    catalog, errors = build_tool_catalog({provider.id: provider}, {manifest.id: manifest})
    assert not errors, errors
    return catalog


class _Evaluator:
    """对任何请求都回 `ALLOW_WITH_CONSTRAINTS` + 给定约束。"""

    def __init__(self, constraints: dict[str, object]) -> None:
        self._constraints = constraints

    def evaluate(self, request: object) -> object:
        return PolicyEvaluation(
            decision=PolicyDecision.ALLOW_WITH_CONSTRAINTS,
            reason="criterion fixture",
            constraints=dict(self._constraints),
        )


def _evaluate(constraints: dict[str, object]) -> tuple[object, object]:
    from packages.application.ports import PreflightContext
    from packages.domain.protocols import ToolRequirement

    context = PreflightContext(
        catalog=_catalog(),  # type: ignore[arg-type]
        project=ProjectSettings(
            project_id="project-1",
            team_template_id="team",
            default_model_profile_id=None,
            budget_policy_id="budget",
            workspace_backend="workspace",
        ),
        credentials=None,
        policy_evaluator=_Evaluator(constraints),  # type: ignore[arg-type]
        endpoint_health={},
        provider_health={},
    )
    evaluator = context.policy_evaluator
    assert evaluator is not None
    return _evaluate_requirement(
        ToolRequirement(capability="literature.search", phase_id="retrieval"),
        evaluator,
        context,
    )


@pytest.mark.parametrize(
    ("declaration", "fragment"),
    [
        ({"unknown": 1}, "unknown constraint key"),
        ({"sandbox_required": "yes"}, "expected bool"),
        ({"path_prefix": 7}, "expected str"),
        ({"max_seconds": True}, "expected int|float"),
    ],
)
def test_each_shape_error_is_named_by_preflight(
    declaration: dict[str, object], fragment: str
) -> None:
    """四种形状错误各判一次：finding code + 点名词。"""
    finding, note = _evaluate(declaration)
    assert finding is not None, declaration
    assert finding.code == "POLICY_CONSTRAINTS_INVALID"  # type: ignore[attr-defined]
    assert fragment in str(note), note


def test_valid_constraints_stay_a_note_not_a_finding() -> None:
    """零回归：合法约束**不**产 finding（仍是一条 note，措辞与改动前同形）。"""
    finding, note = _evaluate({"sandbox_required": True, "max_seconds": 1800})
    assert finding is None
    assert "policy constraints for literature.search" in str(note)


def test_an_empty_declaration_is_not_a_finding() -> None:
    """空声明合法（约束缺席 = 不检查那一条）。"""
    finding, note = _evaluate({})
    assert finding is None
    assert "policy constraints for literature.search" in str(note)


def test_the_preflight_branch_uses_the_shared_table() -> None:
    """源码面：preflight 的形状判词来自表，不是自己写的 isinstance 链。"""
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    source = (root / "packages/application/preflight/policy_check.py").read_text(encoding="utf-8")
    assert "shape_violations" in source
    assert "expected int|float" not in source
    # 且表确实是同一条闭集（未在 preflight 里另列一份）。
    assert constraint_table.CONSTRAINT_KEYS == (
        "sandbox_required",
        "path_prefix",
        "max_seconds",
        "requires_workspace_lease",
    )
