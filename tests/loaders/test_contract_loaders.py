"""契约加载器测试：基于真实 examples 的加载/校验/映射。"""

from __future__ import annotations

import pytest

from adapters.contracts import (
    ContractLoadError,
    load_agents,
    load_budget_policies,
    load_collection,
    load_handoff_bundles,
    load_llm_endpoints,
    load_model_profiles,
    load_models,
    load_policy,
    load_protocol,
    load_roles,
    load_skills,
    load_task_contracts,
    load_team_templates,
    load_tool_providers,
    load_yaml,
)
from packages.domain.enums import (
    ActivationPolicy,
    ModelBindingMode,
    ModelCapability,
    ReviewPanelRole,
    RoleCategory,
    SelectionStrategy,
    WorkspacePolicy,
)


def test_load_yaml_reads_utf8() -> None:
    data = load_yaml("examples/config/model_profiles.yaml")
    assert isinstance(data, dict)
    assert "model_profiles" in data


def test_load_yaml_missing_file_raises() -> None:
    with pytest.raises(ContractLoadError):
        load_yaml("examples/config/does_not_exist.yaml")


def test_load_roles_from_fixture() -> None:
    roles = load_roles("examples/config/roles.yaml")
    assert len(roles) == 26
    director = roles["research_director"]
    assert director.category is RoleCategory.MANAGEMENT
    assert director.activation_default is ActivationPolicy.REQUIRED_BY_PROTOCOL
    assert director.workspace_policy is WorkspacePolicy.READ_ONLY
    assert director.hard_model_capabilities.all_of == ["CHAT"]


def test_load_agents_binding_modes() -> None:
    agents = load_agents("examples/config/agents.yaml")
    assert agents["director"].model_binding.mode is ModelBindingMode.MODEL_PROFILE
    assert agents["director"].model_binding.value == "research_strong"
    assert agents["scout_a"].model_binding.mode is ModelBindingMode.EXPLICIT_MODEL
    assert agents["reviewer_a"].workspace_policy is WorkspacePolicy.READ_ONLY


def test_load_agents_extended_config_surface() -> None:
    agents = load_agents("examples/config/agents.yaml")
    director = agents["director"]
    assert director.context is not None
    assert director.context.max_context_tokens == 16000
    assert director.context.max_iterations == 40
    assert director.runtime_kind is not None
    assert director.runtime_kind.value == "OPENHANDS_NATIVE"
    assert director.budget_policy_ref == "low_cost"
    engineer = agents["engineer"]
    assert engineer.skill_refs == ["experiment_engineering"]
    assert engineer.capability_refs == ["code.execute"]
    assert engineer.context is not None
    assert engineer.context.max_iterations == 80
    reviewer = agents["reviewer_a"]
    assert reviewer.skill_refs == ["scientific_review"]
    assert reviewer.runtime_kind is None
    assert reviewer.budget_policy_ref is None


def test_load_roles_extended_fields() -> None:
    roles = load_roles("examples/config/roles.yaml")
    reviewer = roles["scientific_reviewer"]
    assert reviewer.default_skills == ["scientific_review"]
    assert "evidence.write" in reviewer.forbidden_capabilities
    writer = roles["research_writer"]
    assert "evidence.write" in writer.forbidden_capabilities
    assert "experiment.execute" in writer.forbidden_capabilities
    assert "deliverable.write" in writer.requested_capabilities
    scout = roles["literature_scout"]
    assert scout.default_skills == ["literature_scouting"]
    assert roles["scientific_reviewer"].review_panel_role is ReviewPanelRole.REVIEWER
    assert roles["research_writer"].review_panel_role is ReviewPanelRole.WRITER
    assert roles["literature_scout"].review_panel_role is ReviewPanelRole.NONE


def test_load_skills_from_fixture() -> None:
    skills = load_skills("examples/config/skills.yaml")
    assert len(skills) == 6
    review = skills["scientific_review"]
    assert review.version.text == "1.0.0"
    assert review.capabilities == [
        "research_state.read",
        "evidence.read",
        "experiment.read",
        "review.write",
    ]


def test_load_team_templates_from_fixture() -> None:
    teams = load_team_templates("examples/config/team_templates.yaml")
    assert {"lean", "standard", "rigorous"} <= set(teams)
    lean = teams["lean"]
    pool = lean.roles["domain_researcher"]
    assert pool.min_instances == 1
    assert pool.max_instances == 1
    assert pool.selection_strategy is SelectionStrategy.FIXED


def test_load_llm_endpoints_from_fixture() -> None:
    endpoints = load_llm_endpoints("examples/config/llm_endpoints.yaml")
    endpoint = endpoints["main"]
    assert endpoint.protocol == "OPENAI_COMPATIBLE"
    assert endpoint.credential_ref == "LLM_MAIN_KEY"
    assert endpoint.request_timeout_seconds == 120
    assert endpoint.discovery is not None
    assert endpoint.discovery.enabled is True
    assert endpoint.discovery.allow_models == (
        "deepseek-v4-flash",
        "muse-spark-1.2-contributor",
    )
    assert endpoint.circuit_breaker is not None
    assert endpoint.circuit_breaker.failure_threshold == 5


def test_load_models_from_fixture() -> None:
    models = load_models("examples/config/models.yaml")
    model = models["research_alpha"]
    assert model.endpoint_id == "main"
    assert model.model_name == "deepseek-v4-flash"
    assert ModelCapability.TOOL_CALLING_NATIVE in model.capabilities


def test_load_model_profiles_from_fixture() -> None:
    profiles = load_model_profiles("examples/config/model_profiles.yaml")
    strong = profiles["research_strong"]
    assert strong.primary == "research_alpha"
    assert strong.fallback == ["reviewer_gamma"]
    coding = profiles["coding_strong"]
    assert coding.hard_capabilities == [
        ModelCapability.CHAT,
        ModelCapability.TOOL_CALLING_NATIVE,
    ]


def test_load_task_contracts_from_fixture() -> None:
    contracts = load_task_contracts("examples/contracts/task_contracts.yaml")
    contract = contracts["domain_discovery"]
    assert contract.version == "1.0.0"
    assert len(contract.acceptance_criteria) == 3
    assert contract.retry_policy is not None
    assert contract.retry_policy.max_attempts == 3
    assert contract.idempotency_scope == "task"


def test_load_task_contracts_carries_extended_fields() -> None:
    contracts = load_task_contracts("examples/contracts/task_contracts.yaml")
    discovery = contracts["domain_discovery"]
    assert discovery.input_schema == "domain_discovery_input_v1"
    assert discovery.budget["model_cost_usd"] is not None
    assert discovery.budget["tool_requests"] is None
    assert discovery.failure_policy["on_validation_failure"] == "DEAD_LETTER"
    execution = contracts["experiment_execution"]
    assert execution.input_schema == "experiment_run_input_v1"
    assert execution.output_schema == "experiment_run_output_v1"


def test_load_acceptance_criteria_structured_parameters() -> None:
    contracts = load_task_contracts("examples/contracts/task_contracts.yaml")
    criteria = contracts["domain_discovery"].acceptance_criteria
    coverage = next(item for item in criteria if item.type.value == "EVIDENCE_COVERAGE")
    assert coverage.minimum_sources == 10
    artifact = next(item for item in criteria if item.type.value == "ARTIFACT_EXISTS")
    assert artifact.artifact == "source_set"


def test_load_handoff_bundle_from_fixture() -> None:
    bundle = load_handoff_bundles("examples/contracts/handoff_bundle.yaml")
    assert bundle.producer == "agent-domain-a"
    assert bundle.producer_agent_id == "agent-domain-a"
    assert bundle.producer_role_id == "domain_researcher"
    assert bundle.task_id.value == "0e4a3f2e-9b1c-4d6a-8f2b-1c3d5e7f9a0b"
    assert bundle.digest.hex_value == (
        "0c8d4e6f2a1b3c5d7e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d"
    )
    assert bundle.artifact_refs == ["artifact-domain-map-001"]
    assert bundle.structured_output == {"domain": "agentic research systems"}


def test_handoff_schema_rejects_invalid_digest() -> None:
    from adapters.contracts.base import ContractLoadError, load_json_schema, validate_instance

    payload = load_yaml("examples/contracts/handoff_bundle.yaml")
    payload["digest"] = "sha256:not-a-digest"
    with pytest.raises(ContractLoadError):
        validate_instance(load_json_schema("handoff-bundle.schema.json"), payload, "inline")


def test_load_collection_generic_dispatch() -> None:
    roles = load_collection("roles", "examples/config/roles.yaml")
    assert len(roles) == 26
    with pytest.raises(ContractLoadError):
        load_collection("unknown_kind", "examples/config/roles.yaml")


def test_loader_rejects_unknown_schema_field() -> None:
    from adapters.contracts.base import validate_instance

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "properties": {"id": {"type": "string"}},
    }
    with pytest.raises(ContractLoadError):
        validate_instance(schema, {"id": "x", "unknown": 1}, "inline")


def test_model_profile_schema_validates_fixture() -> None:
    # model-profile.schema.json 必须能放行 examples 中的全部 profile
    import json
    from pathlib import Path

    import jsonschema  # type: ignore[import-untyped]

    schema = json.loads(
        (Path(__file__).resolve().parents[2] / "schemas/model-profile.schema.json").read_text(
            encoding="utf-8"
        )
    )
    profiles = load_yaml("examples/config/model_profiles.yaml")["model_profiles"]
    validator = jsonschema.Draft202012Validator(schema)
    for profile_id, body in profiles.items():
        errors = list(validator.iter_errors({"id": profile_id, **body}))
        assert not errors, (profile_id, [e.message for e in errors])


def test_load_protocol_example() -> None:
    protocol = load_protocol("examples/protocols/ai_ml_research_v0_4_0.yaml")
    assert protocol.id == "ai_ml_research_v0_4_0"
    assert len(protocol.phases) == 11
    assert protocol.phases[1].task_contracts == ["domain_discovery"]
    assert protocol.phases[5].stop_conditions is not None


def test_load_budget_policy_and_resource_contracts() -> None:
    budget = load_budget_policies("examples/config/budgets.yaml")["low_cost"]
    assert budget.hard_limits["tool_requests"] == 1000
    policy = load_policy("examples/config/policy.yaml")
    assert policy.default_effect.value == "DENY"
    providers = load_tool_providers("examples/config/tool_providers.yaml")
    assert providers["ncbi_eutils"].capabilities == [
        "literature.search",
        "literature.read",
        "citation.inspect",
    ]
