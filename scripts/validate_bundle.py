#!/usr/bin/env python3
"""验证 Research OS Bootstrap v0.2.2 的文档、Schema 和示例引用。"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("缺少 PyYAML，请运行: pip install -r requirements-bootstrap.txt") from exc

try:
    import jsonschema
except ImportError as exc:  # pragma: no cover
    raise SystemExit("缺少 jsonschema，请运行: pip install -r requirements-bootstrap.txt") from exc

ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []
WARNINGS: list[str] = []


def load_yaml(rel: str) -> Any:
    try:
        return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        ERRORS.append(f"YAML 无法解析: {rel}: {exc}")
        return {}


def load_json(rel: str) -> Any:
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        ERRORS.append(f"JSON 无法解析: {rel}: {exc}")
        return {}


def required_files() -> list[str]:
    return [
        "README.md", "AGENTS.md", "CODEX_BOOTSTRAP.md", "BACKLOG.md", "CHANGELOG.md",
        "docs/INDEX.md", "docs/PRODUCT.md",
        "docs/product/END_TO_END_USER_JOURNEY.md", "docs/product/CONSOLE_INFORMATION_ARCHITECTURE.md",
        "docs/architecture/SYSTEM_ARCHITECTURE.md", "docs/architecture/DOMAIN_MODEL.md",
        "docs/architecture/ROLE_MODEL.md", "docs/architecture/TASK_HANDOFF.md",
        "docs/architecture/MODEL_COMPATIBILITY.md", "docs/architecture/TOOL_RUNTIME.md",
        "docs/architecture/WORKSPACE_RUNTIME.md", "docs/architecture/CONTEXT_ENGINE.md",
        "docs/architecture/CAPABILITY_SECURITY.md", "docs/architecture/WORKFLOW_RELIABILITY.md",
        "docs/architecture/BUDGET_QUOTA.md", "docs/architecture/DATA_LIFECYCLE.md",
        "docs/architecture/OBSERVABILITY.md", "docs/architecture/DEPLOYMENT_PROFILES.md",
        "docs/security/THREAT_MODEL.md", "docs/security/PLUGIN_TOOL_SUPPLY_CHAIN.md",
        "docs/security/SECRET_MANAGEMENT.md", "docs/security/IDENTITY_AND_ACCESS.md",
        "docs/governance/DATA_GOVERNANCE.md", "docs/governance/RESEARCH_INTEGRITY.md",
        "docs/operations/OPERATIONS_RUNBOOK.md", "docs/operations/BACKUP_RECOVERY.md",
        "docs/operations/SLO_AND_CAPACITY.md",
        "docs/reliability/RUN_STATE_MACHINE.md", "docs/reliability/FAILURE_MODEL.md",
        "docs/catalog/SYSTEM_ROLES.md", "docs/configuration/TEAM_TEMPLATES.md",
        "docs/configuration/AUTONOMY_AND_GATES.md",
        "docs/integration/LLM_ENDPOINTS.md", "docs/integration/MODEL_GATEWAY.md",
        "docs/integration/OPENHANDS_ADAPTER.md", "docs/integration/MCP_TOOL_PROVIDERS.md",
        "docs/integration/POLICY_ENGINE.md", "docs/integration/WORKFLOW_ENGINE.md",
        "docs/evaluation/EVAL_HARNESS.md", "docs/evaluation/QUALITY_GATES.md",
        "docs/api/CONTROL_PLANE_API.md", "docs/api/EVENT_STREAM_API.md",
        "docs/storage/DATABASE_SCHEMA.md", "docs/storage/ARTIFACT_STORE.md",
        "docs/references/OPEN_SOURCE_REUSE_AUDIT.md", "docs/references/UPSTREAM_FINDINGS_V0_2_2.md",
        "docs/roadmap/VERTICAL_SLICE_V0_2_2.md", "docs/migrations/V0_2_1_TO_V0_2_2.md",
        "docs/reviews/REVIEW_RUBRIC.md", "docs/reviews/REVIEW_ROUND_1.md",
        "docs/reviews/REVIEW_ROUND_2.md", "docs/reviews/REVIEW_ROUND_3.md",
        "docs/reviews/REVIEW_ROUND_4.md", "docs/reviews/RELEASE_QUALITY_REPORT.md",
        "examples/protocols/ai_ml_research_v0_2_2.yaml", "scripts/validate_bundle.py",
    ]


def check_required_files() -> None:
    for rel in required_files():
        path = ROOT / rel
        if not path.exists() or path.stat().st_size == 0:
            ERRORS.append(f"缺失或空文件: {rel}")


def check_index_links() -> None:
    path = ROOT / "docs/INDEX.md"
    text = path.read_text(encoding="utf-8")
    for target in re.findall(r"`([^`]+\.(?:md|yaml|json))`", text):
        resolved = (path.parent / target).resolve()
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError:
            ERRORS.append(f"INDEX 链接越出包目录: {target}")
            continue
        if not resolved.exists():
            ERRORS.append(f"INDEX 引用不存在: {target}")


def check_versions() -> None:
    for rel in ["README.md", "AGENTS.md", "CODEX_BOOTSTRAP.md", "docs/PRODUCT.md", "CHANGELOG.md"]:
        if "v0.2.2" not in (ROOT / rel).read_text(encoding="utf-8"):
            ERRORS.append(f"主文档缺少 v0.2.2: {rel}")
    if (ROOT / "docs/roadmap/VERTICAL_SLICE_V0_2_1.md").exists():
        ERRORS.append("旧 Vertical Slice 仍在活动目录")


def validate_instance(schema_name: str, instance: Any, label: str) -> None:
    schema = load_json(f"schemas/{schema_name}")
    if not schema:
        return
    try:
        jsonschema.Draft202012Validator(schema).validate(instance)
    except Exception as exc:  # noqa: BLE001
        ERRORS.append(f"Schema instance 无效: {label}: {exc}")


def check_yaml_and_references() -> None:
    roles = (load_yaml("examples/config/roles.yaml") or {}).get("roles", {})
    agents = (load_yaml("examples/config/agents.yaml") or {}).get("agents", {})
    endpoints = (load_yaml("examples/config/llm_endpoints.yaml") or {}).get("llm_endpoints", {})
    models = (load_yaml("examples/config/models.yaml") or {}).get("models", {})
    profiles = (load_yaml("examples/config/model_profiles.yaml") or {}).get("model_profiles", {})
    teams = (load_yaml("examples/config/team_templates.yaml") or {}).get("team_templates", {})
    capabilities = set((load_yaml("examples/config/capabilities.yaml") or {}).get("capabilities", []))
    tools = (load_yaml("examples/config/tool_providers.yaml") or {}).get("tool_providers", {})
    contracts = (load_yaml("examples/contracts/task_contracts.yaml") or {}).get("task_contracts", {})
    protocol = load_yaml("examples/protocols/ai_ml_research_v0_2_2.yaml") or {}
    project = (load_yaml("examples/config/project.yaml") or {}).get("project", {})
    autonomies = (load_yaml("examples/config/autonomy_levels.yaml") or {}).get("autonomy_levels", {})
    budgets = (load_yaml("examples/config/budgets.yaml") or {}).get("budgets", {})
    backends = load_yaml("examples/config/backends.yaml") or {}
    deployments = (load_yaml("examples/config/deployment_profiles.yaml") or {}).get("deployment_profiles", {})

    # Catalog parity.
    catalog = (ROOT / "docs/catalog/SYSTEM_ROLES.md").read_text(encoding="utf-8")
    catalog_types = set(re.findall(r"^###\s+\d+\.\s+([A-Za-z0-9_]+)", catalog, re.MULTILINE))
    fixture_types = {x.get("role_type") for x in roles.values()}
    if catalog_types != fixture_types:
        ERRORS.append(f"Role Catalog/fixture 不一致: {sorted(catalog_types ^ fixture_types)}")
    if len(fixture_types) != 26:
        ERRORS.append(f"系统 Role 数量应为 26，实际 {len(fixture_types)}")

    # Schema instances and endpoint/model refs.
    for eid, endpoint in endpoints.items():
        validate_instance("llm-endpoint.schema.json", {"id": eid, **endpoint}, f"LLMEndpoint/{eid}")
    for mid, model in models.items():
        validate_instance(
            "model-definition.schema.json",
            {"id": mid, "endpoint_id": model.get("endpoint"), **{k: v for k, v in model.items() if k != "endpoint"}},
            f"ModelDefinition/{mid}",
        )
        if model.get("endpoint") not in endpoints:
            ERRORS.append(f"Model {mid} 引用不存在 Endpoint")

    model_caps = {mid: set((model.get("capabilities") or {}).keys()) for mid, model in models.items()}
    known_model_caps = {
        "CHAT", "STREAMING", "TOOL_CALLING_NATIVE", "TOOL_CALLING_EMULATED",
        "STRUCTURED_OUTPUT_NATIVE", "STRUCTURED_OUTPUT_PROMPTED", "VISION", "REASONING",
        "EMBEDDING", "SEED", "USAGE_REPORTING", "SYSTEM_FINGERPRINT",
    }
    for mid, caps in model_caps.items():
        unknown = caps - known_model_caps
        if unknown:
            ERRORS.append(f"Model {mid} 存在未知 Capability: {sorted(unknown)}")

    # Profiles.
    for pid, profile in profiles.items():
        refs = [profile.get("primary"), *(profile.get("fallback") or [])]
        for ref in refs:
            if ref and ref not in models:
                ERRORS.append(f"ModelProfile {pid} 引用不存在 Model: {ref}")

    # Roles and capability/model eligibility.
    for rid, role in roles.items():
        validate_instance("role-definition.schema.json", {"id": rid, **role}, f"RoleDefinition/{rid}")
        profile_id = role.get("default_model_profile")
        if profile_id not in profiles:
            ERRORS.append(f"Role {rid} 引用不存在 ModelProfile: {profile_id}")
            continue
        for capability in role.get("requested_capabilities", []):
            if capability not in capabilities:
                ERRORS.append(f"Role {rid} 引用未注册 Capability: {capability}")
        required_model_caps = set((role.get("hard_model_capabilities") or {}).get("all_of", []))
        unknown = required_model_caps - known_model_caps
        if unknown:
            ERRORS.append(f"Role {rid} 使用未知 Model Capability: {sorted(unknown)}")
        profile = profiles[profile_id]
        for mid in [profile.get("primary"), *(profile.get("fallback") or [])]:
            if mid and required_model_caps - model_caps.get(mid, set()):
                ERRORS.append(f"Role {rid} 默认模型 {mid} 不满足: {sorted(required_model_caps - model_caps.get(mid, set()))}")

    # Agents.
    reviewer_models: set[str] = set()
    for aid, agent in agents.items():
        validate_instance("agent-spec.schema.json", {"id": aid, **agent}, f"AgentSpec/{aid}")
        role_id = agent.get("role")
        if role_id not in roles:
            ERRORS.append(f"Agent {aid} 引用不存在 Role: {role_id}")
            continue
        binding = agent.get("model_binding", {})
        mids: list[str] = []
        if binding.get("type") == "EXPLICIT_MODEL":
            if binding.get("value") not in models:
                ERRORS.append(f"Agent {aid} 引用不存在 Model: {binding.get('value')}")
            else:
                mids = [binding["value"]]
        elif binding.get("type") == "MODEL_PROFILE":
            if binding.get("value") not in profiles:
                ERRORS.append(f"Agent {aid} 引用不存在 Profile: {binding.get('value')}")
            else:
                profile = profiles[binding["value"]]
                mids = [profile.get("primary"), *(profile.get("fallback") or [])]
        required = set((roles[role_id].get("hard_model_capabilities") or {}).get("all_of", []))
        for mid in filter(None, mids):
            missing = required - model_caps.get(mid, set())
            if missing:
                ERRORS.append(f"Agent {aid} / Model {mid} 不满足 Role 能力: {sorted(missing)}")
        if role_id == "scientific_reviewer" and mids:
            reviewer_models.add(mids[0])
    if len(reviewer_models) < 2:
        WARNINGS.append("示例 ScientificReviewer 未形成两个不同主模型")

    # Team templates and inheritance cycles.
    for tid, team in teams.items():
        validate_instance("team-template.schema.json", {"id": tid, **team}, f"TeamTemplate/{tid}")
        if team.get("extends") and team["extends"] not in teams:
            ERRORS.append(f"TeamTemplate {tid} extends 不存在")
        for rid, bounds in (team.get("roles") or {}).items():
            if rid not in roles:
                ERRORS.append(f"TeamTemplate {tid} 引用不存在 Role: {rid}")
            if int(bounds.get("min_instances", 0)) > int(bounds.get("max_instances", 0)):
                ERRORS.append(f"TeamTemplate {tid}/{rid} min > max")
    for start in teams:
        seen: set[str] = set()
        cur = start
        while cur and teams.get(cur, {}).get("extends"):
            if cur in seen:
                ERRORS.append(f"TeamTemplate inheritance cycle: {start}")
                break
            seen.add(cur)
            cur = teams[cur]["extends"]

    # Tools / contracts.
    for provider_id, provider in tools.items():
        validate_instance("tool-provider.schema.json", {"id": provider_id, **provider}, f"ToolProvider/{provider_id}")
        for capability in provider.get("capabilities", []):
            if capability not in capabilities:
                ERRORS.append(f"ToolProvider {provider_id} 引用未注册 Capability: {capability}")
    for cid, contract in contracts.items():
        validate_instance("task-contract.schema.json", {"id": cid, **contract}, f"TaskContract/{cid}")
        for capability in contract.get("required_capabilities", []):
            if capability not in capabilities:
                ERRORS.append(f"TaskContract {cid} 引用未注册 Capability: {capability}")
        output_schema = contract.get("output_schema")
        if not output_schema or not (ROOT / "schemas" / f"{output_schema}.schema.json").exists():
            ERRORS.append(f"TaskContract {cid} 输出 Schema 不存在: {output_schema}")

    # Protocol DAG and refs.
    validate_instance("protocol.schema.json", protocol, "Protocol")
    defined: set[str] = set()
    for phase in protocol.get("phases", []):
        pid = phase.get("id")
        if pid in defined:
            ERRORS.append(f"Protocol Phase 重复: {pid}")
        for dep in phase.get("depends_on", []) or []:
            if dep not in defined:
                ERRORS.append(f"Phase {pid} 依赖不存在/顺序错误: {dep}")
        if phase.get("task_contract") and phase["task_contract"] not in contracts:
            ERRORS.append(f"Phase {pid} TaskContract 不存在")
        for req in phase.get("required_roles", []) or []:
            if req.get("role") not in roles:
                ERRORS.append(f"Phase {pid} Role 不存在: {req.get('role')}")
        defined.add(pid)

    # Project and deployment refs.
    if project.get("protocol") != protocol.get("id"):
        ERRORS.append("project.yaml protocol 引用不一致")
    if project.get("team_template") not in teams:
        ERRORS.append("project.yaml TeamTemplate 不存在")
    if project.get("default_model_profile") not in profiles:
        ERRORS.append("project.yaml ModelProfile 不存在")
    if project.get("autonomy") not in autonomies:
        ERRORS.append("project.yaml Autonomy 不存在")
    if project.get("budget") not in budgets:
        ERRORS.append("project.yaml Budget 不存在")

    workflows = backends.get("workflow_engines", {})
    workspaces = backends.get("workspace_backends", {})
    for did, deployment in deployments.items():
        if deployment.get("workflow_engine") not in workflows:
            ERRORS.append(f"Deployment {did} WorkflowEngine 不存在")
        if deployment.get("workspace_backend") not in workspaces:
            ERRORS.append(f"Deployment {did} WorkspaceBackend 不存在")


def check_json_schemas() -> None:
    schemas = list((ROOT / "schemas").glob("*.json"))
    if len(schemas) < 10:
        ERRORS.append(f"JSON Schema 数量不足: {len(schemas)}")
    for path in schemas:
        schema = load_json(str(path.relative_to(ROOT)))
        if schema:
            try:
                jsonschema.Draft202012Validator.check_schema(schema)
            except Exception as exc:  # noqa: BLE001
                ERRORS.append(f"JSON Schema 无效: {path.name}: {exc}")


def check_runtime_and_security_boundary() -> None:
    active = [
        "examples/config/backends.yaml", "examples/config/agents.yaml",
        "examples/protocols/ai_ml_research_v0_2_2.yaml", "CODEX_BOOTSTRAP.md",
    ]
    forbidden = ["codex_acp", "openhands_acp", "claude_code", "preferred_backend: acp"]
    for rel in active:
        text = (ROOT / rel).read_text(encoding="utf-8").lower()
        for token in forbidden:
            if token in text:
                ERRORS.append(f"MVP 主路径出现外部 Agent Backend: {rel}: {token}")

    must_have = {
        "AGENTS.md": ["execute_tool()", "transactional outbox", "mcp roots", "modelruntimefingerprint"],
        "docs/security/THREAT_MODEL.md": ["prompt injection", "ssrf", "supply chain", "data exfiltration"],
        "docs/security/IDENTITY_AND_ACCESS.md": ["agentprincipal", "不继承"],
        "docs/governance/DATA_GOVERNANCE.md": ["relay", "restricted", "retention"],
        "docs/architecture/MODEL_COMPATIBILITY.md": ["runtime fingerprint", "tool calling", "circuit breaker"],
        "docs/architecture/WORKFLOW_RELIABILITY.md": ["at-least-once", "idempotency", "outbox"],
    }
    for rel, terms in must_have.items():
        text = (ROOT / rel).read_text(encoding="utf-8").lower()
        for term in terms:
            if term.lower() not in text:
                ERRORS.append(f"关键约束缺失: {rel}: {term}")


def check_manifest_if_present() -> None:
    path = ROOT / "BOOTSTRAP_MANIFEST.json"
    if not path.exists():
        WARNINGS.append("BOOTSTRAP_MANIFEST.json 尚未生成（发布阶段生成）")
        return
    manifest = load_json("BOOTSTRAP_MANIFEST.json")
    for item in manifest.get("files", []):
        target = ROOT / item["path"]
        if not target.exists():
            ERRORS.append(f"Manifest 文件缺失: {item['path']}")
            continue
        if hashlib.sha256(target.read_bytes()).hexdigest() != item["sha256"]:
            ERRORS.append(f"Manifest hash mismatch: {item['path']}")


def main() -> int:
    check_required_files()
    check_index_links()
    check_versions()
    check_yaml_and_references()
    check_json_schemas()
    check_runtime_and_security_boundary()
    check_manifest_if_present()

    for warning in WARNINGS:
        print(f"警告: {warning}")
    if ERRORS:
        print("验证失败:")
        for error in ERRORS:
            print(f"- {error}")
        return 1
    print("验证通过")
    print("- Required docs / INDEX links 完整")
    print("- YAML / JSON Schema / instances 可解析")
    print("- Role / Agent / Model / Team / Task / Protocol 引用一致")
    print("- Model eligibility 与 Deployment refs 一致")
    print("- MVP Runtime、Security、Governance 边界存在")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
