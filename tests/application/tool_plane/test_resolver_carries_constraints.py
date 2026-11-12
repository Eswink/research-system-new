"""GOAL-20261111-112 EC-02/EC-03：**工具面与 preflight 各自读约束**（独立取证）。

与 `test_constraint_table.py` 的分工：那份证明**同一张表**在三面同判（含对抗性 4 条）；
本文件只证明**两个新接入面各自的读法**——解析结果携带约束、preflight 核验形状——
用**更贴近产品调用**的入口（而不是判据自造的求值器）。

**射程**：本文件不重复 12 臂对抗矩阵（在表判据里），只判「接上了、读得出、点名」。
"""

from __future__ import annotations

from collections.abc import Mapping

from packages.application.tool_plane.catalog import ToolCatalog
from packages.application.tool_plane.resolver import (
    CapabilityResolution,
    ResolutionInput,
    resolve_capability,
)
from packages.domain.enums import PolicyDecision
from tests.application.tool_plane_support import make_manifest, make_provider, make_tool


def _catalog() -> ToolCatalog:
    from packages.application.tool_plane import build_tool_catalog

    provider = make_provider("europe-pmc", capabilities=("literature.search",))
    tool = make_tool("literature_search", capabilities=("literature.search",))
    manifest = make_manifest(tools=(tool,), capabilities=("literature.search",), pack_id="lit-pack")
    catalog, errors = build_tool_catalog({provider.id: provider}, {manifest.id: manifest})
    assert not errors, errors
    return catalog


def _resolve(constraints: dict[str, Mapping[str, object]]) -> CapabilityResolution:
    return resolve_capability(
        _catalog(),
        "literature.search",
        ResolutionInput(
            policy_decisions={"literature.search": PolicyDecision.ALLOW_WITH_CONSTRAINTS},
            capability_constraints=constraints,
        ),
    )


class TestTheResolverCarriesConstraints:
    """EC-02：解析结果**携带**约束（不再「解析面等价放行、约束丢弃」）。"""

    def test_the_declared_constraints_are_readable_from_the_resolution(self) -> None:
        declared: dict[str, object] = {"sandbox_required": True, "max_seconds": 1800}
        resolution = _resolve({"literature.search": declared})
        assert resolution.constraints == declared
        assert resolution.constraint_keys == ("max_seconds", "sandbox_required")

    def test_absent_constraints_yield_an_empty_mapping(self) -> None:
        """**两种空分得开**：没有声明 ⇒ 空映射；有声明但是空表 ⇒ 也是空映射，
        但**前者**不产生 findings、**后者**同样不产生（空声明合法）——由 `shape_violations` 判。"""
        resolution = _resolve({})
        assert resolution.constraints == {}
        empty_declared = _resolve({"literature.search": {}})
        assert empty_declared.constraints == {}
        assert empty_declared.findings == ()

    def test_a_malformed_declaration_is_named_in_findings(self) -> None:
        """未知键 / 类型错 ⇒ findings 点名，且**原始声明仍可读**（不替调用方挑子集）。"""
        resolution = _resolve({"literature.search": {"nope": 1}})
        assert any("unknown constraint key" in item for item in resolution.findings)
        assert resolution.constraints == {"nope": 1}

    def test_a_valid_declaration_produces_no_constraint_finding(self) -> None:
        resolution = _resolve({"literature.search": {"sandbox_required": True}})
        assert not any("constraint" in item for item in resolution.findings)
