#!/usr/bin/env python3
"""验证 Research OS Cursor Engineering Framework v0.4.0 的文档、Schema 和示例引用。"""

from __future__ import annotations

import json
import os
import re
import tomllib
from collections.abc import Iterator
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("缺少 PyYAML，请运行: uv sync --frozen") from exc

try:
    import jsonschema
except ImportError as exc:  # pragma: no cover
    raise SystemExit("缺少 jsonschema，请运行: uv sync --frozen") from exc


def _discover_root() -> Path:
    explicit = os.environ.get("CURSOR_FRAMEWORK_ROOT")
    if explicit:
        return Path(explicit).resolve()
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "VERSION").is_file() and (
            candidate / ".cursor" / "framework.json"
        ).is_file():
            return candidate
    raise RuntimeError("Cannot locate repository root (VERSION + .cursor/framework.json)")


ROOT = _discover_root()
ERRORS: list[str] = []
WARNINGS: list[str] = []
DEPENDENCY_LOCKFILES = frozenset({"pnpm-lock.yaml", "uv.lock"})
NON_SOURCE_DIRS = frozenset({
    ".git",
    ".import_linter_cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
})


def repository_files() -> Iterator[Path]:
    for directory, child_dirs, filenames in os.walk(ROOT, topdown=True):
        child_dirs[:] = [name for name in child_dirs if name not in NON_SOURCE_DIRS]
        current = Path(directory)
        yield from (current / filename for filename in filenames)


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


def canonical_text_values(rel: str, heading: str) -> set[str]:
    text = (ROOT / rel).read_text(encoding="utf-8")
    start = text.find(heading)
    if start < 0:
        ERRORS.append(f"Canonical 文档缺少章节: {rel}: {heading}")
        return set()
    match = re.search(r"```text\s*(.*?)```", text[start:], re.DOTALL)
    if match is None:
        ERRORS.append(f"Canonical 文档章节缺少 text code block: {rel}: {heading}")
        return set()
    return {
        line.strip()
        for line in match.group(1).splitlines()
        if re.fullmatch(r"[A-Z][A-Z0-9_]*", line.strip())
    }


def assert_rejects_extra(schema_name: str, instance: Any, label: str) -> None:
    if not isinstance(instance, dict):
        ERRORS.append(f"无法执行额外字段负测，fixture 非对象: {label}")
        return
    schema = load_json(f"schemas/{schema_name}")
    if not schema:
        return
    mutated = {**instance, "__unexpected_contract_field__": True}
    if jsonschema.Draft202012Validator(schema).is_valid(mutated):
        ERRORS.append(f"Schema 未拒绝额外顶层字段: {label}")


def required_files() -> list[str]:
    return [
        "VERSION",
        "README.md",
        "AGENTS.md",
        "CODEX_BOOTSTRAP.md",
        "BACKLOG.md",
        "CHANGELOG.md",
        "pyproject.toml",
        ".python-version",
        "uv.lock",
        "UPSTREAM_COMPONENTS.yaml",
        "package.json",
        ".node-version",
        "pnpm-workspace.yaml",
        "pnpm-lock.yaml",
        "tsconfig.base.json",
        "tsconfig.json",
        "eslint.config.mjs",
        "dependency-cruiser.config.mjs",
        ".importlinter",
        ".github/workflows/m0-quality.yml",
        "docs/references/LICENSE_MATRIX.md",
        "docs/adr/ADR-0026-otel-adapter-boundary.md",
        "docs/references/upstream/M15_OTEL_QUALIFICATION.md",
        "docs/roadmap/M15_COMPLETION_RECORD.md",
        ".cursor/framework.json",
        "docs/INDEX.md",
        "docs/PRODUCT.md",
        "docs/product/END_TO_END_USER_JOURNEY.md",
        "docs/product/CONSOLE_INFORMATION_ARCHITECTURE.md",
        "docs/architecture/SYSTEM_ARCHITECTURE.md",
        "docs/architecture/PORTS.md",
        "docs/architecture/DOMAIN_MODEL.md",
        "docs/architecture/ROLE_MODEL.md",
        "docs/architecture/TASK_HANDOFF.md",
        "docs/architecture/MODEL_COMPATIBILITY.md",
        "docs/architecture/TOOL_RUNTIME.md",
        "docs/architecture/WORKSPACE_RUNTIME.md",
        "docs/architecture/CONTEXT_ENGINE.md",
        "docs/architecture/CAPABILITY_SECURITY.md",
        "docs/architecture/WORKFLOW_RELIABILITY.md",
        "docs/architecture/BUDGET_QUOTA.md",
        "docs/architecture/DATA_LIFECYCLE.md",
        "docs/architecture/OBSERVABILITY.md",
        "docs/architecture/DEPLOYMENT_PROFILES.md",
        "docs/security/THREAT_MODEL.md",
        "docs/security/PLUGIN_TOOL_SUPPLY_CHAIN.md",
        "docs/security/SECRET_MANAGEMENT.md",
        "docs/security/IDENTITY_AND_ACCESS.md",
        "docs/governance/DATA_GOVERNANCE.md",
        "docs/governance/RESEARCH_INTEGRITY.md",
        "docs/operations/OPERATIONS_RUNBOOK.md",
        "docs/operations/BACKUP_RECOVERY.md",
        "docs/operations/SLO_AND_CAPACITY.md",
        "docs/reliability/RUN_STATE_MACHINE.md",
        "docs/reliability/FAILURE_MODEL.md",
        "docs/catalog/SYSTEM_ROLES.md",
        "docs/configuration/TEAM_TEMPLATES.md",
        "docs/configuration/AUTONOMY_AND_GATES.md",
        "docs/integration/LLM_ENDPOINTS.md",
        "docs/integration/MODEL_GATEWAY.md",
        "docs/integration/OPENHANDS_ADAPTER.md",
        "docs/integration/MCP_TOOL_PROVIDERS.md",
        "docs/integration/POLICY_ENGINE.md",
        "docs/integration/WORKFLOW_ENGINE.md",
        "docs/evaluation/EVAL_HARNESS.md",
        "docs/evaluation/QUALITY_GATES.md",
        "docs/api/CONTROL_PLANE_API.md",
        "docs/api/EVENT_STREAM_API.md",
        "docs/storage/DATABASE_SCHEMA.md",
        "docs/storage/ARTIFACT_STORE.md",
        "docs/references/OPEN_SOURCE_REUSE_AUDIT.md",
        "docs/references/UPSTREAM_FINDINGS_V0_4_0.md",
        "docs/roadmap/VERTICAL_SLICE_V0_4_0.md",
        "docs/versioning/VERSION_POLICY.md",
        "examples/protocols/ai_ml_research_v0_4_0.yaml",
        ".cursor/skills/system-spec-check/scripts/validate_bundle.py",
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


def _check_changelog_version_consistency(
    changelog_path: Path,
    version: str,
    errors: list[str],
) -> None:
    """CHANGELOG 不得出现超前于 VERSION 的已发布标题。

    `## vX.Y.Z` 表示一次已发布版本；未发布内容必须置于 `## Unreleased`
    （当前 VERSION 是唯一项目版本源，M15 复审发现 v0.5.0/v0.5.1 超前标题）。
    """
    text = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else ""
    published = {
        match.group(1)
        for match in re.finditer(r"^## v([0-9]+\.[0-9]+\.[0-9]+)", text, flags=re.MULTILINE)
    }
    for published_version in sorted(published):
        if _version_tuple(published_version) > _version_tuple(version):
            errors.append(
                f"CHANGELOG 出现超前于 VERSION 的已发布标题: v{published_version} > v{version}"
            )


def _version_tuple(version: str) -> tuple[int, int, int]:
    parts = version.split(".")
    return tuple(int(part) for part in parts)


def check_versions() -> None:
    version_path = ROOT / "VERSION"
    version = version_path.read_text(encoding="utf-8").strip() if version_path.exists() else ""
    if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) is None:
        ERRORS.append(f"VERSION 必须为 SemVer: {version!r}")

    version_token = version.replace(".", "_")
    protocol_path = ROOT / "examples" / "protocols" / f"ai_ml_research_v{version_token}.yaml"
    protocol = load_yaml(str(protocol_path.relative_to(ROOT))) if protocol_path.exists() else {}
    expected_protocol_id = f"ai_ml_research_v{version_token}"
    if not protocol_path.exists():
        ERRORS.append(f"缺少当前版本 Protocol: {protocol_path.relative_to(ROOT)}")
    else:
        if protocol_path.stem != protocol.get("id"):
            ERRORS.append(
                f"Protocol 文件名/id 不一致: {protocol_path.stem!r} != {protocol.get('id')!r}"
            )
        if protocol.get("id") != expected_protocol_id:
            ERRORS.append(
                f"Protocol id/version token 不一致: {protocol.get('id')!r} != {expected_protocol_id!r}"
            )
        if protocol.get("version") != version:
            ERRORS.append(
                f"Protocol version 与 VERSION 不一致: {protocol.get('version')!r} != {version!r}"
            )

    framework = load_json(".cursor/framework.json") or {}
    if framework.get("framework_version") != version:
        ERRORS.append("framework_version 与 VERSION 不一致")
    if framework.get("version_source") != "VERSION":
        ERRORS.append("framework version_source 必须指向 VERSION")
    if "research_os_baseline" in framework:
        ERRORS.append("不得维护独立 research_os_baseline 版本")

    for rel in ["README.md", "AGENTS.md", "CODEX_BOOTSTRAP.md", "docs/PRODUCT.md", "CHANGELOG.md"]:
        if f"v{version}" not in (ROOT / rel).read_text(encoding="utf-8"):
            ERRORS.append(f"主文档缺少 v{version}: {rel}")

    _check_changelog_version_consistency(ROOT / "CHANGELOG.md", version, ERRORS)

    old_version = re.compile(r"(?<![0-9])v?(?:0\.2\.[0-9]+|0\.3\.0)(?![0-9])", re.IGNORECASE)
    scan_suffixes = {".md", ".mdc", ".yaml", ".yml", ".json", ".py", ".txt"}
    for path in repository_files():
        if path.suffix.lower() not in scan_suffixes:
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative in DEPENDENCY_LOCKFILES:
            continue
        if "runtime" in path.relative_to(ROOT).parts:
            continue
        if relative.startswith(".cursor/plans/archive/"):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if relative.startswith(".cursor/memory/entries/") and re.search(
            r"(?m)^status:\s*(?:SUPERSEDED|RETIRED)\s*$", text
        ):
            continue
        if old_version.search(text):
            ERRORS.append(f"发现旧项目版本引用: {path.relative_to(ROOT)}")

    for path in repository_files():
        if re.search(r"(?:V0_2|V0_3|v0_2|v0_3)", path.name):
            ERRORS.append(f"发现旧版本命名文件: {path.relative_to(ROOT)}")


def validate_instance(schema_name: str, instance: Any, label: str) -> None:
    schema = load_json(f"schemas/{schema_name}")
    if not schema:
        return
    try:
        jsonschema.Draft202012Validator(schema).validate(instance)
    except Exception as exc:  # noqa: BLE001
        ERRORS.append(f"Schema instance 无效: {label}: {exc}")


def validate_strict_instance(schema_name: str, instance: Any, label: str) -> None:
    validate_instance(schema_name, instance, label)
    assert_rejects_extra(schema_name, instance, label)


def check_yaml_and_references() -> None:
    roles = (load_yaml("examples/config/roles.yaml") or {}).get("roles", {})
    agents = (load_yaml("examples/config/agents.yaml") or {}).get("agents", {})
    skills = (load_yaml("examples/config/skills.yaml") or {}).get("skills", {})
    endpoints = (load_yaml("examples/config/llm_endpoints.yaml") or {}).get("llm_endpoints", {})
    models = (load_yaml("examples/config/models.yaml") or {}).get("models", {})
    profiles = (load_yaml("examples/config/model_profiles.yaml") or {}).get("model_profiles", {})
    teams = (load_yaml("examples/config/team_templates.yaml") or {}).get("team_templates", {})
    capability_values = (load_yaml("examples/config/capabilities.yaml") or {}).get(
        "capabilities", []
    )
    if not isinstance(capability_values, list):
        ERRORS.append("Capability registry 必须为列表")
        capability_values = []
    if len(capability_values) != len(set(capability_values)):
        ERRORS.append("Capability registry 存在重复项")
    capabilities = set(capability_values)
    tools = (load_yaml("examples/config/tool_providers.yaml") or {}).get("tool_providers", {})
    contracts = (load_yaml("examples/contracts/task_contracts.yaml") or {}).get(
        "task_contracts", {}
    )
    version_token = (ROOT / "VERSION").read_text(encoding="utf-8").strip().replace(".", "_")
    protocol = load_yaml(f"examples/protocols/ai_ml_research_v{version_token}.yaml") or {}
    project = (load_yaml("examples/config/project.yaml") or {}).get("project", {})
    autonomies = (load_yaml("examples/config/autonomy_levels.yaml") or {}).get(
        "autonomy_levels", {}
    )
    budgets = (load_yaml("examples/config/budgets.yaml") or {}).get("budgets", {})
    backends = load_yaml("examples/config/backends.yaml") or {}
    deployments = (load_yaml("examples/config/deployment_profiles.yaml") or {}).get(
        "deployment_profiles", {}
    )
    memory_policy = (load_yaml("examples/config/memory_policy.yaml") or {}).get("memory_policy", {})
    policy = (load_yaml("examples/config/policy.yaml") or {}).get("policy", {})
    handoff_fixture = load_yaml("examples/contracts/handoff_bundle.yaml") or {}
    preflight_fixture = load_yaml("examples/contracts/preflight_report.yaml") or {}
    compiled_plan_fixture = load_yaml("examples/contracts/compiled_run_plan.yaml") or {}
    toolpack_fixture = load_yaml("examples/contracts/toolpack_manifest.yaml") or {}
    probe_fixture = load_yaml("examples/contracts/probe_result.yaml") or {}
    health_fixture = load_yaml("examples/contracts/endpoint_health.yaml") or {}
    fingerprint_fixture = load_yaml("examples/contracts/model_runtime_fingerprint.yaml") or {}
    fallback_fixture = load_yaml("examples/contracts/fallback_audit_record.yaml") or {}

    memory_types = canonical_text_values(
        "docs/architecture/CONTEXT_ENGINE.md", "## 5. Memory Types"
    )
    session_states = canonical_text_values(
        "docs/reliability/RUN_STATE_MACHINE.md", "## AgentSession"
    )
    runtime_session_states = canonical_text_values(
        "docs/architecture/AGENT_RUNTIME.md", "## 5. Status Mapping"
    )
    failure_categories = canonical_text_values("docs/reliability/FAILURE_MODEL.md", "## Categories")
    if session_states != runtime_session_states:
        ERRORS.append(
            f"AgentSession canonical 状态漂移: {sorted(session_states ^ runtime_session_states)}"
        )

    for schema_name, fixture, label in (
        ("handoff-bundle.schema.json", handoff_fixture, "HandoffBundle fixture"),
        ("preflight-report.schema.json", preflight_fixture, "PreflightReport fixture"),
        ("compiled-run-plan.schema.json", compiled_plan_fixture, "CompiledRunPlan fixture"),
        ("toolpack-manifest.schema.json", toolpack_fixture, "ToolPackManifest fixture"),
        ("probe-result.schema.json", probe_fixture, "ModelProbeResult fixture"),
        ("endpoint-health.schema.json", health_fixture, "EndpointHealthRecord fixture"),
        (
            "model-runtime-fingerprint.schema.json",
            fingerprint_fixture,
            "ModelRuntimeFingerprint fixture",
        ),
        ("fallback-audit-record.schema.json", fallback_fixture, "FallbackAuditRecord fixture"),
    ):
        validate_strict_instance(schema_name, fixture, label)
    unknown_toolpack_caps = set(toolpack_fixture.get("requested_capabilities") or []) - capabilities
    if unknown_toolpack_caps:
        ERRORS.append(f"ToolPackManifest 引用未注册 Capability: {sorted(unknown_toolpack_caps)}")
    if (toolpack_fixture.get("compatibility") or {}).get("research_os") != (
        ROOT / "VERSION"
    ).read_text(encoding="utf-8").strip():
        ERRORS.append("ToolPackManifest compatibility.research_os 与 VERSION 不一致")

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
        validate_strict_instance(
            "llm-endpoint.schema.json", {"id": eid, **endpoint}, f"LLMEndpoint/{eid}"
        )
    for mid, model in models.items():
        validate_strict_instance(
            "model-definition.schema.json",
            {
                "id": mid,
                "endpoint_id": model.get("endpoint"),
                **{k: v for k, v in model.items() if k != "endpoint"},
            },
            f"ModelDefinition/{mid}",
        )
        if model.get("endpoint") not in endpoints:
            ERRORS.append(f"Model {mid} 引用不存在 Endpoint")

    model_caps = {
        mid: set((model.get("capabilities") or {}).keys()) for mid, model in models.items()
    }
    known_model_caps = {
        "CHAT",
        "STREAMING",
        "TOOL_CALLING_NATIVE",
        "TOOL_CALLING_EMULATED",
        "STRUCTURED_OUTPUT_NATIVE",
        "STRUCTURED_OUTPUT_PROMPTED",
        "VISION",
        "REASONING",
        "EMBEDDING",
        "SEED",
        "USAGE_REPORTING",
        "SYSTEM_FINGERPRINT",
    }
    for mid, caps in model_caps.items():
        unknown = caps - known_model_caps
        if unknown:
            ERRORS.append(f"Model {mid} 存在未知 Capability: {sorted(unknown)}")

    # Profiles.
    for pid, profile in profiles.items():
        validate_strict_instance(
            "model-profile.schema.json", {"id": pid, **profile}, f"ModelProfile/{pid}"
        )
        refs = [profile.get("primary"), *(profile.get("fallback") or [])]
        for ref in refs:
            if ref and ref not in models:
                ERRORS.append(f"ModelProfile {pid} 引用不存在 Model: {ref}")

    # Roles and capability/model eligibility.
    for rid, role in roles.items():
        validate_strict_instance(
            "role-definition.schema.json", {"id": rid, **role}, f"RoleDefinition/{rid}"
        )
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
                ERRORS.append(
                    f"Role {rid} 默认模型 {mid} 不满足: {sorted(required_model_caps - model_caps.get(mid, set()))}"
                )
        for skill_ref in role.get("default_skills", []):
            if skill_ref not in skills:
                ERRORS.append(f"Role {rid} 引用不存在 Skill: {skill_ref}")
        for capability in role.get("forbidden_capabilities", []):
            if capability not in capabilities:
                ERRORS.append(f"Role {rid} 禁止未注册 Capability: {capability}")
        denied = set(role.get("requested_capabilities", [])) & set(
            role.get("forbidden_capabilities", [])
        )
        if denied:
            ERRORS.append(f"Role {rid} 同时请求与禁止 Capability: {sorted(denied)}")

    # Skills.
    for sid, skill in skills.items():
        validate_strict_instance("skill.schema.json", {"id": sid, **skill}, f"SkillSpec/{sid}")
        for capability in skill.get("capabilities", []):
            if capability not in capabilities:
                ERRORS.append(f"Skill {sid} 引用未注册 Capability: {capability}")

    # Agents.
    writer_models: set[str] = set()
    reviewer_models: set[str] = set()
    for aid, agent in agents.items():
        validate_strict_instance("agent-spec.schema.json", {"id": aid, **agent}, f"AgentSpec/{aid}")
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
        panel_role = (roles[role_id] or {}).get("review_panel_role", "NONE")
        if panel_role == "REVIEWER" and mids:
            reviewer_models.add(mids[0])
        if panel_role == "WRITER" and mids:
            writer_models.add(mids[0])
        for skill_ref in agent.get("skill_refs", []):
            if skill_ref not in skills:
                ERRORS.append(f"Agent {aid} 引用不存在 Skill: {skill_ref}")
        for capability in agent.get("capability_refs", []):
            if capability not in capabilities:
                ERRORS.append(f"Agent {aid} 引用未注册 Capability: {capability}")
        for capability in agent.get("capability_refs", []):
            if capability in set((roles.get(role_id) or {}).get("forbidden_capabilities", [])):
                ERRORS.append(f"Agent {aid} 请求 Role {role_id} 禁止的 Capability: {capability}")
        budget_ref = agent.get("budget_policy_ref")
        if budget_ref and budget_ref not in budgets:
            ERRORS.append(f"Agent {aid} 引用不存在 BudgetPolicy: {budget_ref}")
    if not reviewer_models:
        ERRORS.append("示例缺少 review_panel_role=REVIEWER 的 Agent")
    if not writer_models:
        ERRORS.append("示例缺少 review_panel_role=WRITER 的 Agent")
    if reviewer_models & writer_models:
        ERRORS.append(f"示例 Writer/Reviewer 共享模型: {sorted(reviewer_models & writer_models)}")

    # Team templates and inheritance cycles.
    for tid, team in teams.items():
        validate_strict_instance(
            "team-template.schema.json", {"id": tid, **team}, f"TeamTemplate/{tid}"
        )
        if team.get("extends") and team["extends"] not in teams:
            ERRORS.append(f"TeamTemplate {tid} extends 不存在")
        for rid, bounds in (team.get("roles") or {}).items():
            if rid not in roles:
                ERRORS.append(f"TeamTemplate {tid} 引用不存在 Role: {rid}")
            if int(bounds.get("min_instances", 0)) > int(bounds.get("max_instances", 0)):
                ERRORS.append(f"TeamTemplate {tid}/{rid} min > max")
    resolved_teams: dict[str, dict[str, Any]] = {}
    for start in teams:
        seen: set[str] = set()
        chain: list[dict[str, Any]] = []
        cur: str | None = start
        while cur:
            if cur in seen:
                ERRORS.append(f"TeamTemplate inheritance cycle: {start}")
                chain = []
                break
            seen.add(cur)
            team = teams.get(cur)
            if not isinstance(team, dict):
                chain = []
                break
            chain.append(team)
            parent = team.get("extends")
            cur = str(parent) if parent else None
        merged_roles: dict[str, Any] = {}
        for team in reversed(chain):
            merged_roles.update(team.get("roles") or {})
        resolved_teams[start] = merged_roles

    configured_memory_types = set((memory_policy.get("run") or {}).get("auto_write_types") or [])
    configured_memory_types.update(
        (memory_policy.get("project") or {}).get("require_gate_for_types") or []
    )
    unknown_memory_types = configured_memory_types - memory_types
    if unknown_memory_types:
        ERRORS.append(f"Memory policy 使用未知 Memory Type: {sorted(unknown_memory_types)}")

    for section in ("allow", "allow_with_constraints", "require_approval", "deny"):
        for rule in policy.get(section) or []:
            capability = rule.get("capability") if isinstance(rule, dict) else None
            if capability and capability not in capabilities:
                ERRORS.append(f"Policy {section} 引用未注册 Capability: {capability}")

    for budget_id, budget in budgets.items():
        validate_strict_instance(
            "budget-policy.schema.json",
            {"id": budget_id, **budget},
            f"BudgetPolicy/{budget_id}",
        )
    policy_instance = {
        "id": policy.get("id", "project-policy"),
        "version": policy.get("version", (ROOT / "VERSION").read_text(encoding="utf-8").strip()),
        **policy,
    }
    validate_strict_instance("policy.schema.json", policy_instance, "PolicyDefinition/project")
    for workspace_id, workspace in (backends.get("workspace_backends") or {}).items():
        validate_strict_instance(
            "workspace.schema.json",
            {"id": workspace_id, **workspace},
            f"WorkspaceBackend/{workspace_id}",
        )

    # Tools / contracts.
    for provider_id, provider in tools.items():
        validate_strict_instance(
            "tool-provider.schema.json",
            {"id": provider_id, **provider},
            f"ToolProvider/{provider_id}",
        )
        for capability in provider.get("capabilities", []):
            if capability not in capabilities:
                ERRORS.append(f"ToolProvider {provider_id} 引用未注册 Capability: {capability}")
    for cid, contract in contracts.items():
        validate_strict_instance(
            "task-contract.schema.json", {"id": cid, **contract}, f"TaskContract/{cid}"
        )
        for capability in contract.get("required_capabilities", []):
            if capability not in capabilities:
                ERRORS.append(f"TaskContract {cid} 引用未注册 Capability: {capability}")
        output_schema = contract.get("output_schema")
        if not output_schema or not (ROOT / "schemas" / f"{output_schema}.schema.json").exists():
            ERRORS.append(f"TaskContract {cid} 输出 Schema 不存在: {output_schema}")
        version_match = re.fullmatch(
            r"([0-9]+)\.[0-9]+\.[0-9]+", str(contract.get("version") or "")
        )
        schema_version_match = re.search(r"_v([0-9]+)$", str(output_schema or ""))
        if (
            version_match is None
            or schema_version_match is None
            or version_match.group(1) != schema_version_match.group(1)
        ):
            ERRORS.append(f"TaskContract {cid} version/output_schema 主版本不一致")
        retry_categories = set(
            (contract.get("retry_policy") or {}).get("retryable_categories") or []
        )
        unknown_failure_categories = retry_categories - failure_categories
        if unknown_failure_categories:
            ERRORS.append(
                f"TaskContract {cid} 使用未知 Failure Category: {sorted(unknown_failure_categories)}"
            )

    # Protocol DAG and refs.
    validate_strict_instance("protocol.schema.json", protocol, "Protocol")
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
            if int(req.get("min_instances", 0)) > int(req.get("max_instances", 0)):
                ERRORS.append(f"Phase {pid}/{req.get('role')} min > max")
        for capability in phase.get("required_capabilities", []) or []:
            if capability not in capabilities:
                ERRORS.append(f"Phase {pid} 引用未注册 Capability: {capability}")
        defined.add(pid)

    # Project and deployment refs.
    if project.get("protocol") != protocol.get("id"):
        ERRORS.append("project.yaml protocol 引用不一致")
    selected_team_id = project.get("team_template")
    if selected_team_id not in teams:
        ERRORS.append("project.yaml TeamTemplate 不存在")
    else:
        selected_roles = resolved_teams.get(str(selected_team_id), {})
        for phase in protocol.get("phases", []):
            for requirement in phase.get("required_roles", []) or []:
                role_id = requirement.get("role")
                bounds = selected_roles.get(role_id)
                if not isinstance(bounds, dict):
                    ERRORS.append(
                        f"Project TeamTemplate {selected_team_id} 无法满足 Phase {phase.get('id')} Role: {role_id}"
                    )
                    continue
                if int(bounds.get("max_instances", 0)) < int(requirement.get("min_instances", 0)):
                    ERRORS.append(
                        f"Project TeamTemplate {selected_team_id}/{role_id} 容量不足以满足 Phase {phase.get('id')}"
                    )
    if project.get("default_model_profile") not in profiles:
        ERRORS.append("project.yaml ModelProfile 不存在")
    if project.get("autonomy") not in autonomies:
        ERRORS.append("project.yaml Autonomy 不存在")
    if project.get("budget") not in budgets:
        ERRORS.append("project.yaml Budget 不存在")
    if project.get("workspace_backend") not in (backends.get("workspace_backends") or {}):
        ERRORS.append("project.yaml workspace_backend 未在 backends.yaml 注册")

    workflows = backends.get("workflow_engines", {})
    workspaces = backends.get("workspace_backends", {})
    for did, deployment in deployments.items():
        if deployment.get("workflow_engine") not in workflows:
            ERRORS.append(f"Deployment {did} WorkflowEngine 不存在")
        if deployment.get("workspace_backend") not in workspaces:
            ERRORS.append(f"Deployment {did} WorkspaceBackend 不存在")


def check_json_schemas() -> None:
    expected_schema_files = {
        "agent-spec.schema.json",
        "budget-policy.schema.json",
        "capability.schema.json",
        "compiled-run-plan.schema.json",
        "domain_discovery_input_v1.schema.json",
        "domain_discovery_output_v1.schema.json",
        "endpoint-health.schema.json",
        "eval-dataset.schema.json",
        "eval-score.schema.json",
        "experiment_run_input_v1.schema.json",
        "experiment_run_output_v1.schema.json",
        "export_bundle_v1.schema.json",
        "fallback-audit-record.schema.json",
        "handoff-bundle.schema.json",
        "llm-endpoint.schema.json",
        "model-definition.schema.json",
        "model-profile.schema.json",
        "model-runtime-fingerprint.schema.json",
        "preflight-report.schema.json",
        "pricing-table.schema.json",
        "probe-result.schema.json",
        "policy.schema.json",
        "protocol.schema.json",
        "real_research_deliverable_v1.schema.json",
        "reproducibility_audit_v1.schema.json",
        "role-definition.schema.json",
        "skill.schema.json",
        "task-contract.schema.json",
        "team-template.schema.json",
        "tool-provider.schema.json",
        "tool-spec.schema.json",
        "toolpack-manifest.schema.json",
        "workspace.schema.json",
    }
    schemas = list((ROOT / "schemas").glob("*.json"))
    actual_schema_files = {path.name for path in schemas}
    if actual_schema_files != expected_schema_files:
        ERRORS.append(
            f"JSON Schema 注册表不一致: {sorted(actual_schema_files ^ expected_schema_files)}"
        )

    def check_object_boundaries(node: Any, path: str) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object":
                if "additionalProperties" not in node:
                    ERRORS.append(f"JSON Schema object 未显式声明 additionalProperties: {path}")
                elif node.get("additionalProperties") is True:
                    ERRORS.append(f"JSON Schema object 禁止 additionalProperties=true: {path}")
            for key, value in node.items():
                check_object_boundaries(value, f"{path}/{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                check_object_boundaries(value, f"{path}/{index}")

    for path in schemas:
        schema = load_json(str(path.relative_to(ROOT)))
        if schema:
            expected_id = f"https://research-os.local/schemas/{path.name}"
            if schema.get("$id") != expected_id:
                ERRORS.append(f"JSON Schema $id/文件名不一致: {path.name}: {schema.get('$id')!r}")
            try:
                jsonschema.Draft202012Validator.check_schema(schema)
            except Exception as exc:  # noqa: BLE001
                ERRORS.append(f"JSON Schema 无效: {path.name}: {exc}")
            check_object_boundaries(schema, path.name)

    task_schema = load_json("schemas/task-contract.schema.json") or {}
    schema_failure_categories = set(
        (((task_schema.get("$defs") or {}).get("retryPolicy") or {}).get("properties") or {})
        .get("retryable_categories", {})
        .get("items", {})
        .get("enum", [])
    )
    canonical_failure_categories = canonical_text_values(
        "docs/reliability/FAILURE_MODEL.md", "## Categories"
    )
    if schema_failure_categories != canonical_failure_categories:
        ERRORS.append(
            f"Failure Category 文档/Schema 不一致: {sorted(schema_failure_categories ^ canonical_failure_categories)}"
        )


def check_runtime_and_security_boundary() -> None:
    active = [
        "examples/config/backends.yaml",
        "examples/config/agents.yaml",
        "examples/protocols/ai_ml_research_v0_4_0.yaml",
        "CODEX_BOOTSTRAP.md",
    ]
    forbidden = ["codex_acp", "openhands_acp", "claude_code", "preferred_backend: acp"]
    for rel in active:
        text = (ROOT / rel).read_text(encoding="utf-8").lower()
        for token in forbidden:
            if token in text:
                ERRORS.append(f"MVP 主路径出现外部 Agent Backend: {rel}: {token}")

    must_have = {
        "AGENTS.md": [
            "execute_tool()",
            "transactional outbox",
            "mcp roots",
            "modelruntimefingerprint",
        ],
        "docs/security/THREAT_MODEL.md": [
            "prompt injection",
            "ssrf",
            "supply chain",
            "data exfiltration",
        ],
        "docs/security/IDENTITY_AND_ACCESS.md": ["agentprincipal", "不继承"],
        "docs/governance/DATA_GOVERNANCE.md": ["relay", "restricted", "retention"],
        "docs/architecture/MODEL_COMPATIBILITY.md": [
            "runtime fingerprint",
            "tool calling",
            "circuit breaker",
        ],
        "docs/architecture/WORKFLOW_RELIABILITY.md": ["at-least-once", "idempotency", "outbox"],
    }
    for rel, terms in must_have.items():
        text = (ROOT / rel).read_text(encoding="utf-8").lower()
        for term in terms:
            if term.lower() not in text:
                ERRORS.append(f"关键约束缺失: {rel}: {term}")


def check_supply_chain() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    try:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        ERRORS.append(f"Python dependency metadata 无法解析: {exc}")
        return

    project = pyproject.get("project") or {}
    if project.get("version") != version:
        ERRORS.append("pyproject.toml project.version 与 VERSION 不一致")
    if project.get("requires-python") != ">=3.12,<3.13":
        ERRORS.append("pyproject.toml 必须固定 Python 3.12 compatibility window")
    if (ROOT / ".python-version").read_text(encoding="utf-8").strip() != "3.12":
        ERRORS.append(".python-version 必须固定为 3.12")
    if lock.get("requires-python") != "==3.12.*":
        ERRORS.append("uv.lock requires-python 必须固定为 ==3.12.*")

    dev_requirements = (pyproject.get("dependency-groups") or {}).get("dev") or []
    direct_packages = {
        re.split(r"[<>=!~\[; ]", requirement, maxsplit=1)[0].casefold()
        for requirement in dev_requirements
        if isinstance(requirement, str)
    }
    lock_packages = {
        str(package.get("name") or "").casefold(): package
        for package in lock.get("package") or []
        if isinstance(package, dict)
    }
    missing_locked = direct_packages - set(lock_packages)
    if missing_locked:
        ERRORS.append(f"pyproject dev dependency 未进入 uv.lock: {sorted(missing_locked)}")

    try:
        node_package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        pnpm_lock = load_yaml("pnpm-lock.yaml") or {}
    except Exception as exc:  # noqa: BLE001
        ERRORS.append(f"Node dependency metadata 无法解析: {exc}")
        node_package = {}
        pnpm_lock = {}
    if node_package.get("private") is not True:
        ERRORS.append("根 package.json 必须是 private 工具包")
    if "version" in node_package:
        ERRORS.append("根 package.json 不得维护第二个项目版本；VERSION 是唯一版本源")
    if node_package.get("packageManager") != "pnpm@9.15.1":
        ERRORS.append("package.json packageManager 必须精确固定 pnpm@9.15.1")
    if (node_package.get("engines") or {}).get("node") != ">=22.18.0 <23":
        ERRORS.append("package.json 必须固定 Node 22 compatibility window")
    if (ROOT / ".node-version").read_text(encoding="utf-8").strip() != "22.18.0":
        ERRORS.append(".node-version 必须固定为 22.18.0")
    node_dev = node_package.get("devDependencies") or {}
    required_node_tools = {
        "@eslint/js",
        "dependency-cruiser",
        "eslint",
        "prettier",
        "typescript",
        "typescript-eslint",
    }
    missing_node_tools = required_node_tools - set(node_dev)
    if missing_node_tools:
        ERRORS.append(f"package.json 缺少 M0 TypeScript 工具: {sorted(missing_node_tools)}")
    pnpm_importer = (((pnpm_lock.get("importers") or {}).get(".")) or {}).get(
        "devDependencies"
    ) or {}
    pnpm_packages = pnpm_lock.get("packages") or {}
    for package_name, declared_version in node_dev.items():
        if (
            re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?", str(declared_version))
            is None
        ):
            ERRORS.append(f"Node 直接依赖必须精确固定版本: {package_name}: {declared_version!r}")
            continue
        locked_direct = pnpm_importer.get(package_name) or {}
        locked_version = str(locked_direct.get("version") or "")
        if locked_direct.get("specifier") != declared_version or not (
            locked_version == declared_version or locked_version.startswith(f"{declared_version}(")
        ):
            ERRORS.append(f"package.json/pnpm-lock 直接依赖不一致: {package_name}")
        locked_package = pnpm_packages.get(f"{package_name}@{declared_version}") or {}
        integrity = str((locked_package.get("resolution") or {}).get("integrity") or "")
        if not integrity.startswith("sha512-"):
            ERRORS.append(f"pnpm-lock 缺少直接依赖 sha512 integrity: {package_name}")

    registry = load_yaml("UPSTREAM_COMPONENTS.yaml") or {}
    if registry.get("schema_version") != 2 or registry.get("project_version_source") != "VERSION":
        ERRORS.append("UPSTREAM_COMPONENTS 必须使用 schema v2 和 VERSION 单一版本源")
    components = registry.get("components") or []
    if not isinstance(components, list):
        ERRORS.append("UPSTREAM_COMPONENTS components 必须为列表")
        return
    seen: set[str] = set()
    adopted: set[str] = set()
    license_matrix = (ROOT / "docs/references/LICENSE_MATRIX.md").read_text(encoding="utf-8")
    for component in components:
        if not isinstance(component, dict):
            ERRORS.append("UPSTREAM_COMPONENTS 条目必须为对象")
            continue
        component_id = component.get("id")
        if not isinstance(component_id, str) or not component_id:
            ERRORS.append("UPSTREAM_COMPONENTS 条目缺少 id")
            continue
        if component_id in seen:
            ERRORS.append(f"UPSTREAM_COMPONENTS id 重复: {component_id}")
        seen.add(component_id)
        status = component.get("adoption_status")
        if status not in {"ADOPTED", "PLANNED"}:
            ERRORS.append(f"UPSTREAM_COMPONENTS adoption_status 无效: {component_id}: {status!r}")
            continue
        if status == "PLANNED":
            forbidden_claims = {"resolution", "license", "upgrade_gate"} & set(component)
            if forbidden_claims:
                ERRORS.append(
                    f"PLANNED upstream 不得伪造采用证据: {component_id}: {sorted(forbidden_claims)}"
                )
            continue

        adopted.add(component_id.casefold())
        source = component.get("source") or {}
        resolution = component.get("resolution") or {}
        digest = resolution.get("digest") or {}
        license_record = component.get("license") or {}
        upgrade_gate = component.get("upgrade_gate") or {}
        package_name = str(source.get("package") or "").casefold()
        locked = lock_packages.get(package_name)
        if source.get("kind") == "DOCKERFILE":
            _check_dockerfile_adopted(
                component_id, source, resolution, license_record, upgrade_gate, license_matrix
            )
            continue
        if source.get("kind") == "NPM":
            _check_npm_adopted(
                component_id,
                source,
                resolution,
                digest,
                license_record,
                upgrade_gate,
                license_matrix,
                node_dev,
                set((pnpm_lock.get("packages") or {}).keys()),
            )
            continue
        if source.get("kind") == "HTTP_API":
            _check_http_api_adopted(
                component_id, source, resolution, license_record, upgrade_gate, license_matrix
            )
            continue
        if package_name not in direct_packages or locked is None:
            ERRORS.append(f"ADOPTED upstream 未作为直接锁定依赖: {component_id}")
            continue
        if resolution.get("lockfile") != "uv.lock" or resolution.get("version") != locked.get(
            "version"
        ):
            ERRORS.append(f"ADOPTED upstream version/lockfile 与 uv.lock 不一致: {component_id}")
        locked_sdist_hash = str((locked.get("sdist") or {}).get("hash") or "").removeprefix(
            "sha256:"
        )
        if (
            digest.get("algorithm") != "sha256"
            or digest.get("artifact") != "sdist"
            or digest.get("value") != locked_sdist_hash
            or re.fullmatch(r"[0-9a-f]{64}", str(digest.get("value") or "")) is None
        ):
            ERRORS.append(f"ADOPTED upstream sdist digest 与 uv.lock 不一致: {component_id}")
        if not license_record.get("spdx") or not str(
            license_record.get("evidence") or ""
        ).startswith("https://"):
            ERRORS.append(f"ADOPTED upstream 缺少 SPDX/license evidence: {component_id}")
        if upgrade_gate.get("explicit_approval") is not True or not upgrade_gate.get(
            "required_checks"
        ):
            ERRORS.append(f"ADOPTED upstream 缺少升级门禁: {component_id}")
        if component_id.casefold() not in license_matrix.casefold():
            ERRORS.append(f"LICENSE_MATRIX 缺少 ADOPTED upstream: {component_id}")

    if not {"pyyaml", "jsonschema"} <= adopted:
        ERRORS.append("UPSTREAM_COMPONENTS 必须登记实际采用的 PyYAML/jsonschema")
    if (ROOT / "requirements-bootstrap.txt").exists():
        ERRORS.append("requirements-bootstrap.txt 已被 uv.lock 取代，禁止维护第二套浮动依赖源")


def _check_dockerfile_adopted(
    component_id: str,
    source: dict,
    resolution: dict,
    license_record: dict,
    upgrade_gate: dict,
    license_matrix: str,
) -> None:
    """容器镜像来源（source.kind=DOCKERFILE）的 ADOPTED 校验。

    镜像不是 PyPI 包，不参与 uv.lock 校验；但必须：
    - source.path 指向仓库内 Dockerfile 且文件存在（可审计、可重建）；
    - resolution.base_index_digest 为 sha256 格式 pin（镜像供应链）；
    - license evidence 为 https 链接；
    - upgrade_gate 与 LICENSE_MATRIX 与其他 ADOPTED 组件同等要求。
    """
    dockerfile_path = str(source.get("path") or "")
    if not dockerfile_path or not (ROOT / dockerfile_path).is_file():
        ERRORS.append(
            f"DOCKERFILE upstream source.path 不存在: {component_id}: {dockerfile_path!r}"
        )
    base_digest = str(resolution.get("base_index_digest") or "")
    digest_hex = base_digest.removeprefix("sha256:")
    if base_digest and re.fullmatch(r"[0-9a-f]{64}", digest_hex) is None:
        ERRORS.append(f"DOCKERFILE upstream base_index_digest 不是 sha256 pin: {component_id}")
    if not license_record.get("spdx") or not str(license_record.get("evidence") or "").startswith(
        "https://"
    ):
        ERRORS.append(f"ADOPTED upstream 缺少 SPDX/license evidence: {component_id}")
    if upgrade_gate.get("explicit_approval") is not True or not upgrade_gate.get("required_checks"):
        ERRORS.append(f"ADOPTED upstream 缺少升级门禁: {component_id}")
    if component_id.casefold() not in license_matrix.casefold():
        ERRORS.append(f"LICENSE_MATRIX 缺少 ADOPTED upstream: {component_id}")


def _check_http_api_adopted(
    component_id: str,
    source: dict,
    resolution: dict,
    license_record: dict,
    upgrade_gate: dict,
    license_matrix: str,
) -> None:
    """外部 HTTP API 来源（source.kind=HTTP_API）的 ADOPTED 校验（M12）。

    API 服务不是 PyPI 包，不参与 uv.lock 校验；但必须：
    - source.url 为 https 官方端点（可审计来源）；
    - resolution.version 为显式 revision/版本引用（API 变更门禁）；
    - license evidence 为 https 链接；
    - upgrade_gate 与 LICENSE_MATRIX 与其他 ADOPTED 组件同等要求。
    """
    source_url = str(source.get("url") or "")
    if not source_url.startswith("https://"):
        ERRORS.append(f"HTTP_API upstream source.url 必须是 https: {component_id}: {source_url!r}")
    if not str(resolution.get("version") or "").strip():
        ERRORS.append(f"HTTP_API upstream 缺少 resolution.version: {component_id}")
    if not license_record.get("spdx") or not str(license_record.get("evidence") or "").startswith(
        "https://"
    ):
        ERRORS.append(f"ADOPTED upstream 缺少 SPDX/license evidence: {component_id}")
    if upgrade_gate.get("explicit_approval") is not True or not upgrade_gate.get("required_checks"):
        ERRORS.append(f"ADOPTED upstream 缺少升级门禁: {component_id}")
    if component_id.casefold() not in license_matrix.casefold():
        ERRORS.append(f"LICENSE_MATRIX 缺少 ADOPTED upstream: {component_id}")


def _check_npm_adopted(
    component_id: str,
    source: dict,
    resolution: dict,
    digest: dict,
    license_record: dict,
    upgrade_gate: dict,
    license_matrix: str,
    node_dev: dict,
    lockfile_package_keys: set[str],
) -> None:
    """npm 来源（source.kind=NPM）的 ADOPTED 校验。

    npm 包不在 uv.lock；与 PyPI 分支同等强度的要求是：
    - package.json devDependencies 以 exact 版本（无 ^/~ 前缀）声明；
    - pnpm-lock.yaml 的 packages 段包含 `包@版本` 条目（immutable resolution）；
    - digest 为 tarball 的 sha256（64 hex，与 UPSTREAM 登记一致）；
    - license spdx/evidence、upgrade_gate、LICENSE_MATRIX 与其他 ADOPTED 组件同等。
    """
    package_name = str(source.get("package") or "")
    version = str(resolution.get("version") or "")
    spec = str((node_dev or {}).get(package_name) or "")
    if not version or spec != version or re.match(r"^[~^]", spec) is not None:
        ERRORS.append(
            f"NPM upstream devDependencies 必须精确锁定 {version!r}: {component_id}: {spec!r}"
        )
    if f"{package_name}@{version}" not in lockfile_package_keys:
        ERRORS.append(f"NPM upstream 未进入 pnpm-lock: {component_id}: {package_name}@{version}")
    if (
        digest.get("algorithm") != "sha256"
        or digest.get("artifact") != "tarball"
        or re.fullmatch(r"[0-9a-f]{64}", str(digest.get("value") or "")) is None
    ):
        ERRORS.append(f"ADOPTED upstream tarball sha256 digest 无效: {component_id}")
    if not license_record.get("spdx") or not str(license_record.get("evidence") or "").startswith(
        "https://"
    ):
        ERRORS.append(f"ADOPTED upstream 缺少 SPDX/license evidence: {component_id}")
    if upgrade_gate.get("explicit_approval") is not True or not upgrade_gate.get("required_checks"):
        ERRORS.append(f"ADOPTED upstream 缺少升级门禁: {component_id}")
    if component_id.casefold() not in license_matrix.casefold():
        ERRORS.append(f"LICENSE_MATRIX 缺少 ADOPTED upstream: {component_id}")


def check_manifest_if_present() -> None:
    path = ROOT / "FRAMEWORK_MANIFEST.json"
    if path.exists():
        WARNINGS.append(
            "FRAMEWORK_MANIFEST.json 由 .cursor/skills/framework-release/scripts/verify_cursor_framework_release.py 专门验证；普通 bundle validation 不阻塞后续合法修改"
        )
    else:
        WARNINGS.append("FRAMEWORK_MANIFEST.json 尚未生成（显式发布阶段生成）")


def validate_local_markdown_links() -> None:
    link_re = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
    for doc in repository_files():
        if doc.suffix.lower() != ".md":
            continue
        text = doc.read_text(encoding="utf-8")
        for raw_target in link_re.findall(text):
            target = raw_target.split("#", 1)[0].strip()
            if not target or "://" in target or target.startswith(("mailto:", "#")):
                continue
            resolved = (doc.parent / target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                continue
            if not resolved.exists():
                ERRORS.append(f"Markdown 本地链接不存在: {doc.relative_to(ROOT)} -> {raw_target}")


def main() -> int:
    validate_local_markdown_links()
    check_required_files()
    check_index_links()
    check_versions()
    check_yaml_and_references()
    check_json_schemas()
    check_runtime_and_security_boundary()
    check_supply_chain()
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
