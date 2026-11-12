"""GOAL-20261111-112 EC-01/EC-05：**同一张约束表**在**三个执行面**上同判。

**判什么**：

1. **表自洽**（EC-01）：四个键的闭集、类型表、`ENFORCED_KEYS` 关系；
   `bool` 不冒充 `int`（`max_seconds: true` 是声明错误）；
2. **对抗性反证 4 条 × 三面**（EC-05）：无沙箱 / 越界路径 / 超时 / digest 不匹配，
   在
   - **实验执行边界**（`script_authority.check_constraints`）、
   - **工具面**（`tool_plane.resolver` 的形状 findings）、
   - **preflight**（`preflight.policy_check` 的 `POLICY_CONSTRAINTS_INVALID` finding）
   各验一次 —— **同一张表，三面同判**；
3. **三处都调同一张表**（EC-01 的源码面）：三份消费文件的源码都出现对
   `constraint_table` 的引用（判据按源码断言，不按运行时导入 —— 那三个面在不同进程里）。
4. **第四键的射程**：`requires_workspace_lease` **能过形状**（它是出厂策略文件里写着的）
   但**不在** `ENFORCED_KEYS` 里（本轮不假装执行它）。
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest

from packages.application.experiments import constraint_table
from packages.application.experiments.script_authority import (
    AuthorityError,
    ExecutionRequest,
    check_constraints,
    shipped_scripts,
)
from packages.application.ports import PreflightContext
from packages.application.tool_plane.catalog import ToolCatalog
from packages.application.tool_plane.resolver import CapabilityResolution
from packages.domain.enums import PolicyDecision
from packages.domain.protocols import ToolRequirement

ROOT = Path(__file__).resolve().parents[3]
_SHIPPED = shipped_scripts()[0]


class TestTheTableItself:
    """EC-01：表自洽。"""

    def test_the_closed_set_has_four_keys_and_three_enforced(self) -> None:
        assert constraint_table.CONSTRAINT_KEYS == (
            "sandbox_required",
            "path_prefix",
            "max_seconds",
            "requires_workspace_lease",
        )
        assert constraint_table.ENFORCED_KEYS == (
            "sandbox_required",
            "path_prefix",
            "max_seconds",
        )
        assert set(constraint_table.ENFORCED_KEYS) < set(constraint_table.CONSTRAINT_KEYS)

    def test_every_key_has_a_declared_type(self) -> None:
        assert set(constraint_table.EXPECTED_TYPES) == set(constraint_table.CONSTRAINT_KEYS)

    @pytest.mark.parametrize(
        ("declaration", "reason_fragment"),
        [
            ({"unknown": 1}, "unknown constraint key"),
            ({"sandbox_required": "yes"}, "expected bool"),
            ({"path_prefix": 3}, "expected str"),
            ({"max_seconds": True}, "expected int|float, got bool"),
            ({"requires_workspace_lease": "true"}, "expected bool"),
        ],
    )
    def test_shape_violations_are_named(
        self, declaration: dict[str, object], reason_fragment: str
    ) -> None:
        problems = constraint_table.shape_violations(declaration)
        assert problems, f"{declaration} 应被点名为不合法"
        assert any(reason_fragment in item.reason for item in problems), problems

    def test_the_fourth_key_passes_shape_but_is_not_enforced(self) -> None:
        """**第四键的射程**：形状合法（不判红），但**不在** `ENFORCED_KEYS`（不假装执行）。"""
        assert constraint_table.shape_violations({"requires_workspace_lease": True}) == ()
        assert "requires_workspace_lease" not in constraint_table.ENFORCED_KEYS

    def test_an_empty_declaration_is_valid(self) -> None:
        assert constraint_table.shape_violations({}) == ()
        assert constraint_table.shape_violations(None) == ()


class TestTheExperimentBoundary:
    """EC-05 面 ①：实验执行边界（既有面，本轮改为调表）。"""

    def test_no_sandbox_is_refused(self) -> None:
        with pytest.raises(AuthorityError, match="sandbox_required"):
            check_constraints(
                ExecutionRequest(
                    script_path=_SHIPPED,
                    digest="sha256:" + "a" * 64,
                    constraints={"sandbox_required": True},
                    sandboxed=False,
                )
            )

    def test_an_escaping_path_is_refused(self) -> None:
        with pytest.raises(AuthorityError, match="escapes upward"):
            check_constraints(
                ExecutionRequest(
                    script_path=_SHIPPED,
                    digest="sha256:" + "a" * 64,
                    constraints={"path_prefix": "work/"},
                    write_path="../etc/passwd",
                )
            )

    def test_a_timeout_is_refused(self) -> None:
        with pytest.raises(AuthorityError, match="exceeds the policy limit"):
            check_constraints(
                ExecutionRequest(
                    script_path=_SHIPPED,
                    digest="sha256:" + "a" * 64,
                    constraints={"max_seconds": 60},
                    requested_seconds=120,
                )
            )

    def test_a_missing_digest_is_refused(self) -> None:
        """digest pin：出厂脚本无摘要 ⇒ 拒（「跑的不是被审过的字节」）。"""
        with pytest.raises(AuthorityError, match="carries no digest"):
            check_constraints(ExecutionRequest(script_path=_SHIPPED, digest="", authored=False))

    def test_a_compliant_request_passes(self) -> None:
        authority = check_constraints(
            ExecutionRequest(
                script_path=_SHIPPED,
                digest="sha256:" + "a" * 64,
                constraints={"sandbox_required": True, "path_prefix": "work/", "max_seconds": 60},
                sandboxed=True,
                write_path="work/out.txt",
                requested_seconds=30,
            )
        )
        assert str(authority) == "SHIPPED"


class TestTheToolPlane:
    """EC-05 面 ②：工具面（本轮新接）。"""

    def _resolve(
        self, capability_constraints: dict[str, Mapping[str, object]]
    ) -> CapabilityResolution:
        from packages.application.tool_plane.resolver import ResolutionInput, resolve_capability

        catalog = _catalog()
        return resolve_capability(
            catalog,
            "literature.search",
            ResolutionInput(
                policy_decisions=_allow_with_constraints("literature.search"),
                capability_constraints=capability_constraints,
            ),
        )

    def test_the_resolution_carries_the_constraints(self) -> None:
        resolution = self._resolve({"literature.search": {"sandbox_required": True}})
        assert resolution.constraints == {"sandbox_required": True}
        assert resolution.constraint_keys == ("sandbox_required",)

    def test_no_constraints_yields_an_empty_mapping(self) -> None:
        resolution = self._resolve({})
        assert resolution.constraints == {}
        assert resolution.constraint_keys == ()

    def test_a_malformed_declaration_is_named_in_findings(self) -> None:
        """**对抗面**：未知键在**工具面**也被点名（不再等价放行）。"""
        resolution = self._resolve({"literature.search": {"unknown_key": 1}})
        assert any("unknown constraint key" in item for item in resolution.findings)


class TestPreflight:
    """EC-05 面 ③：preflight（本轮新接）。"""

    def test_a_malformed_constraint_yields_the_named_finding(self) -> None:
        """**对抗面**：类型错的约束在 preflight **点名**（此前只被复述）。"""
        from packages.application.preflight.policy_check import _evaluate_requirement

        context = _context_with_constraints({"max_seconds": True})
        evaluator = context.policy_evaluator
        assert evaluator is not None
        finding, note = _evaluate_requirement(
            _requirement("literature.search", "retrieval"), evaluator, context
        )
        assert finding is not None, "类型错的约束必须产出 finding"
        assert finding.code == "POLICY_CONSTRAINTS_INVALID", finding
        assert "expected int|float" in str(note)

    def test_valid_constraints_produce_no_finding(self) -> None:
        from packages.application.preflight.policy_check import _evaluate_requirement

        context = _context_with_constraints({"max_seconds": 60, "path_prefix": "/work"})
        evaluator = context.policy_evaluator
        assert evaluator is not None
        finding, note = _evaluate_requirement(
            _requirement("literature.search", "retrieval"), evaluator, context
        )
        assert finding is None
        assert "policy constraints" in str(note)


class TestAllThreeFacesShareOneTable:
    """EC-01：三处消费点都引用**同一张表**（源码面断言）。"""

    @pytest.mark.parametrize(
        "relative",
        [
            "packages/application/experiments/script_authority.py",
            "packages/application/tool_plane/resolver.py",
            "packages/application/preflight/policy_check.py",
        ],
    )
    def test_the_consumer_references_the_table(self, relative: str) -> None:
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "constraint_table" in source, f"{relative} 没有引用唯一那张约束表"

    def test_the_table_is_the_only_place_the_keys_are_declared(self) -> None:
        """三键的**判定**只在表里：消费点不得自己 `isinstance` 判 `max_seconds` 之类的形状。"""
        for relative in (
            "packages/application/tool_plane/resolver.py",
            "packages/application/preflight/policy_check.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            assert "expected int|float" not in source, f"{relative} 自己写了一份形状判词"


# --- helpers -------------------------------------------------------------


def _catalog() -> ToolCatalog:
    """用**既有共享构造器**造 catalog（`tool_plane_support` 是 M8 的 fixture 单一来源）。"""
    from packages.application.tool_plane import build_tool_catalog
    from tests.application.tool_plane_support import make_manifest, make_provider, make_tool

    provider = make_provider("europe-pmc", capabilities=("literature.search",))
    tool = make_tool("literature_search", capabilities=("literature.search",))
    manifest = make_manifest(tools=(tool,), capabilities=("literature.search",), pack_id="lit-pack")
    catalog, errors = build_tool_catalog({provider.id: provider}, {manifest.id: manifest})
    assert not errors, errors
    return catalog


def _allow_with_constraints(capability: str) -> dict[str, PolicyDecision]:
    return {capability: PolicyDecision.ALLOW_WITH_CONSTRAINTS}


def _requirement(capability: str, phase_id: str) -> ToolRequirement:
    return ToolRequirement(capability=capability, phase_id=phase_id)


def _context_with_constraints(constraints: dict[str, object]) -> PreflightContext:
    """最小 `PreflightContext`：只填 `_evaluate_requirement` 真正读的两样。

    `project` 必须是真对象（`PolicyRequest.actor` 读 `project.project_id`）；
    `credentials` 与 health 面本判据不触及，留空。
    """
    from packages.application.ports import PreflightContext
    from packages.application.ports.resource_catalog import ProjectSettings

    return PreflightContext(
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


class _Evaluator:
    """最小策略求值器：对任何请求都回 `ALLOW_WITH_CONSTRAINTS` + 给定约束。"""

    def __init__(self, constraints: dict[str, object]) -> None:
        self._constraints = constraints

    def evaluate(self, request: object) -> object:
        from packages.application.ports.policy_evaluator import PolicyEvaluation
        from packages.domain.enums import PolicyDecision

        return PolicyEvaluation(
            decision=PolicyDecision.ALLOW_WITH_CONSTRAINTS,
            reason="criterion fixture",
            constraints=dict(self._constraints),
        )
