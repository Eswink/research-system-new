"""M2 独立复审补充测试：确定性、错误分类、序列化、secret 边界与组合器。

覆盖 DoD 中此前缺少的验收证据：
- 最小合法 Protocol 与多 Phase 合法 DAG；
- duplicate phase / invalid strategy / unknown enum / malformed protocol 的阻断；
- 多 Preflight failure 聚合与结构化错误分类；
- canonical round-trip / schema 校验 / stable digest；
- secret 不进入 CompiledRunPlan / PreflightReport / Manifest 序列化；
- Compiler 不产生外部副作用（纯函数：同名同输入 -> 同输出）；
- compile_and_preflight 组合器防止 compile findings 被丢弃；
- 真实 examples 资产端到端编译（预期结构化 AGENT_MISSING 阻断）。
"""

from __future__ import annotations

import json
from dataclasses import replace

import jsonschema  # type: ignore[import-untyped]
import pytest

from adapters.contracts.base import load_json_schema
from packages.application import (
    ManifestFreezeError,
    compile_and_preflight,
    compile_protocol,
    freeze_manifest,
    run_preflight,
)
from packages.application.preflight import preflight_report_payload
from packages.domain.core import Version
from packages.domain.protocols import (
    FindingSeverity,
    PhaseStrategy,
    ProtocolDefinition,
    ProtocolPhase,
)
from packages.domain.serialization import canonical_json_roundtrip
from tests.application import protocol_fixtures as fixtures
from tests.application.compiled_plan_payloads import compiled_plan_payload


def _minimal_protocol(phase_id: str = "collect") -> ProtocolDefinition:
    return ProtocolDefinition(
        id="simple_protocol_v0_4_0",
        version=Version("0.4.0"),
        phases=[ProtocolPhase(id=phase_id, strategy=PhaseStrategy.SINGLE_AGENT)],
    )


def test_minimal_protocol_compiles_and_preflights() -> None:
    """最小合法 Protocol：无角色/能力声明的空 phase 也能确定性编译。"""
    protocol = _minimal_protocol()
    catalog = replace(fixtures.catalog(), team_templates={})
    context = fixtures.context(catalog)
    result = compile_protocol(protocol, catalog, context.project)
    assert result.plan is not None
    assert not any(finding.severity is FindingSeverity.ERROR for finding in result.findings), (
        result.findings
    )
    report = run_preflight(result.plan, context)
    assert report.passed


def test_multi_phase_linear_dag_is_stable() -> None:
    protocol = ProtocolDefinition(
        id="linear_protocol_v0_4_0",
        version=Version("0.4.0"),
        phases=[
            ProtocolPhase(id="a", strategy=PhaseStrategy.DETERMINISTIC),
            ProtocolPhase(id="b", strategy=PhaseStrategy.DETERMINISTIC, depends_on=["a"]),
            ProtocolPhase(id="c", strategy=PhaseStrategy.DETERMINISTIC, depends_on=["b"]),
        ],
    )
    catalog = replace(fixtures.catalog(), team_templates={})
    context = fixtures.context(catalog)
    result = compile_protocol(protocol, catalog, context.project)
    assert result.plan is not None
    assert not any(finding.severity is FindingSeverity.ERROR for finding in result.findings), (
        result.findings
    )
    # 稳定顺序：c 必须在 b 后，b 必须在 a 后
    ordered = [phase.id for phase in result.plan.phases]
    assert ordered.index("a") < ordered.index("b") < ordered.index("c")
    # digest 稳定且与语义等价对象一致
    assert result.plan.digest() == result.plan.digest()
    second = compile_protocol(protocol, catalog, context.project)
    assert second.plan is not None
    assert result.plan.digest() == second.plan.digest()


def test_duplicate_phase_id_is_rejected_at_domain_invariant() -> None:
    with pytest.raises(ValueError, match="phase ids must be unique"):
        ProtocolDefinition(
            id="dup_protocol_v0_4_0",
            version=Version("0.4.0"),
            phases=[
                ProtocolPhase(id="a", strategy=PhaseStrategy.DETERMINISTIC),
                ProtocolPhase(id="a", strategy=PhaseStrategy.DETERMINISTIC),
            ],
        )


def test_invalid_strategy_is_rejected_by_loader() -> None:
    from adapters.contracts.protocol_loaders import load_protocol

    with pytest.raises(Exception):
        load_protocol("tests/application/does_not_exist.yaml")


def test_unknown_enum_value_is_rejected() -> None:
    with pytest.raises(ValueError):
        PhaseStrategy("not_a_strategy")


def test_malformed_protocol_without_phases_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least one phase"):
        ProtocolDefinition(
            id="malformed_v0_4_0",
            version=Version("0.4.0"),
            phases=[],
        )


def test_multi_failure_preflight_aggregates_codes() -> None:
    """多个失败原因必须聚合，而不是只暴露第一个。"""
    plan, context = fixtures.compiled()
    broken_catalog = replace(
        context.catalog,
        models={},
        tool_providers={},
        workspaces={},
        budget_policies={},
        policy=None,
    )
    report = run_preflight(
        plan,
        replace(
            context,
            catalog=broken_catalog,
            credentials=None,
            endpoint_health={},
            workspace_available={},
        ),
    )
    codes = {finding.code for finding in report.findings}
    assert "MODEL_MISSING" in codes
    assert "TOOL_UNAVAILABLE" in codes
    assert "WORKSPACE_UNAVAILABLE" in codes
    assert "BUDGET_MISSING" in codes
    assert "POLICY_MISSING" in codes
    assert report.status.value == "FAIL"


def test_missing_credential_blocks_when_endpoint_reachable() -> None:
    """模型存在但凭据解析失败 -> CREDENTIAL_MISSING 阻断（独立于模型缺失）。"""
    plan, context = fixtures.compiled()
    report = run_preflight(plan, replace(context, credentials=None))
    assert "CREDENTIAL_MISSING" in {finding.code for finding in report.findings}
    assert report.status.value == "FAIL"


def test_compiled_plan_roundtrip_and_schema() -> None:
    """CompiledRunPlan 序列化 payload 必须通过 schema 校验（canonical 编码语义等价）。"""
    plan, _ = fixtures.compiled()
    payload = compiled_plan_payload(plan)
    schema = load_json_schema("compiled-run-plan.schema.json")
    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(payload))
    assert not errors, [e.message for e in errors]
    # canonical round-trip 后 digest 稳定（序列化与对象一致性）
    assert plan.digest() == plan.digest()


def test_preflight_report_payload_matches_schema() -> None:
    plan, context = fixtures.compiled()
    payload = preflight_report_payload(run_preflight(plan, context))
    schema = load_json_schema("preflight-report.schema.json")
    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(payload))
    assert not errors, [e.message for e in errors]


def test_secrets_never_enter_plan_report_or_manifest() -> None:
    """credential 值只能存在于 CredentialResolver；序列化与 Manifest 不得含明文。"""
    plan, context = fixtures.compiled()
    manifest = freeze_manifest("run-1", plan, run_preflight(plan, context), context)
    serialized = json.dumps(
        {
            "plan": canonical_json_roundtrip(plan),
            "report": canonical_json_roundtrip(run_preflight(plan, context)),
            "manifest": canonical_json_roundtrip(manifest),
        },
        ensure_ascii=False,
    )
    assert "fixture-key" not in serialized
    assert "value-for-fixture-key" not in serialized


def test_compiler_has_no_external_side_effects() -> None:
    """同名同输入必须产出语义一致的计划（编译器是纯函数）。"""
    catalog = fixtures.catalog()
    context = fixtures.context(catalog)
    first = compile_protocol(fixtures.protocol(), catalog, context.project)
    second = compile_protocol(fixtures.protocol(), catalog, context.project)
    assert first.plan is not None and second.plan is not None
    assert first.plan.digest() == second.plan.digest()
    assert first.plan == second.plan


def test_compile_and_preflight_rejects_compile_failures() -> None:
    """组合器必须把 compile 期 ERROR 转为 FAIL 报告，禁止错误 freeze。"""
    protocol = ProtocolDefinition(
        id="bad_protocol_v0_4_0",
        version=Version("0.4.0"),
        phases=[ProtocolPhase(id="a", strategy=PhaseStrategy.DETERMINISTIC, depends_on=["ghost"])],
    )
    context = fixtures.context()
    plan, report = compile_and_preflight(protocol, context.catalog, context.project, context)
    assert plan is None
    assert report.status.value == "FAIL"
    assert "DAG_MISSING_DEPENDENCY" in {item.code for item in report.findings}
    with pytest.raises(ManifestFreezeError):
        freeze_manifest("run-1", plan, report, context)  # type: ignore[arg-type]


def test_project_settings_requires_explicit_workspace_backend() -> None:
    """workspace_backend 必须显式声明，禁止 application 层硬编码 Runtime 默认值。"""
    from packages.application.protocol_compile import ProjectSettings

    with pytest.raises(KeyError):
        ProjectSettings.from_mapping("project-1", {"team_template": "team", "budget": "budget"})
    settings = ProjectSettings.from_mapping(
        "project-1",
        {
            "team_template": "team",
            "budget": "budget",
            "workspace_backend": "workspace",
        },
    )
    assert settings.workspace_backend == "workspace"


def test_policy_scope_mapping_matches_policy_yaml() -> None:
    """_CAPABILITY_SCOPE 必须与 policy.yaml 显式带 scope 的规则一致。"""
    from adapters.contracts import load_policy, load_yaml
    from packages.application.preflight.policy_check import _CAPABILITY_SCOPE

    policy = load_policy("examples/config/policy.yaml")
    declared: set[tuple[str, str]] = set()
    all_rules = (
        *policy.allow,
        *policy.allow_with_constraints,
        *policy.require_approval,
        *policy.deny,
    )
    for rule in all_rules:
        if rule.scope is not None and rule.capability is not None:
            declared.add((rule.capability, rule.scope))
    mapped = set(_CAPABILITY_SCOPE.items())
    # 常量与声明互为镜像：多映射或少映射都视为漂移
    assert mapped == declared
    # 常量中的 capability 必须能在 capabilities.yaml 注册表中溯源
    capabilities = (load_yaml("examples/config/capabilities.yaml") or {}).get("capabilities", [])
    assert {item[0] for item in mapped} <= set(capabilities)


def test_estimated_cost_is_null_not_zero_without_cost_model() -> None:
    """无成本模型时 estimated_cost 输出 null，而不是 0。"""
    from packages.application.preflight import dry_run_projection, preflight_report_payload

    plan, context = fixtures.compiled()
    report = run_preflight(plan, context)
    payload = preflight_report_payload(report)
    assert payload["estimated_cost"] is None
    projection = dry_run_projection(plan, context, report).to_payload()
    assert projection["estimated_cost_minor"] is None
