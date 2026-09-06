#!/usr/bin/env python3
"""离线验证 Research OS 的 Cursor 工程治理资产。"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable

import yaml


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
CURSOR_ROOT = ROOT / ".cursor"
ERRORS: list[str] = []
WARNINGS: list[str] = []

PLAN_STATUSES = {
    "DRAFT",
    "APPROVED",
    "IN_PROGRESS",
    "VERIFYING",
    "BLOCKED",
    "DONE",
    "CANCELLED",
    "REOPENED",
}
RECHECK_RESULTS = {"PASS", "PASS_WITH_WARNINGS", "REVISE", "BLOCK"}
RECHECK_STATUSES = {"VERIFYING", "COMPLETED"}
MEMORY_STATUSES = {"ACTIVE", "SUPERSEDED", "RETIRED"}
EXPECTED_RULES = {
    "00-repository-contract.mdc",
    "10-agent-delegation.mdc",
    "20-plan-memory-recheck.mdc",
    "21-cursor-framework-governance.mdc",
    "22-learning-promotion.mdc",
    "30-ui-skill-routing.mdc",
    "40-python.mdc",
    "41-typescript.mdc",
    "42-command-encoding.mdc",
    "43-git-commit-policy.mdc",
    "44-code-architecture.mdc",
    "45-module-file-naming.mdc",
    "50-contract-assets.mdc",
}
EXPECTED_RULE_METADATA = {
    "21-cursor-framework-governance.mdc": {"always_apply": True, "has_globs": False},
    "22-learning-promotion.mdc": {"always_apply": True, "has_globs": False},
    "30-ui-skill-routing.mdc": {"always_apply": False, "has_globs": True},
    "40-python.mdc": {"always_apply": False, "has_globs": True},
    "41-typescript.mdc": {"always_apply": False, "has_globs": True},
    "42-command-encoding.mdc": {"always_apply": True, "has_globs": False},
    "43-git-commit-policy.mdc": {"always_apply": True, "has_globs": False},
    "44-code-architecture.mdc": {"always_apply": False, "has_globs": True},
    "45-module-file-naming.mdc": {"always_apply": False, "has_globs": True},
    "50-contract-assets.mdc": {"always_apply": False, "has_globs": True},
}
EXPECTED_SKILLS = {
    "repository-orientation",
    "all-plan",
    "engineering-memory",
    "recheck",
    "governance-check",
}
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
PLAN_INDEX_ROW_RE = re.compile(
    r"\|\s*\[([ xX])\]\s*\|\s*\[(PLAN-\d{8}-\d{3})\]\(([^)]+)\)\s*\|\s*([A-Z_]+)\s*\|"
)
SECRET_PATTERNS = {
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "Google-style key": re.compile(r"\bAIza[A-Za-z0-9_-]{20,}\b"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "assigned secret": re.compile(
        r"(?im)^\s*(?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*[\"']?(?!null\b|none\b|redacted\b|<)[^\s#\"']{8,}"
    ),
}


def add_error(message: str) -> None:
    ERRORS.append(message)


def add_warning(message: str) -> None:
    WARNINGS.append(message)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        add_error(f"无法读取 UTF-8 文件: {path.relative_to(ROOT)}: {exc}")
        return ""


def load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(read_text(path))
    except Exception as exc:  # noqa: BLE001
        add_error(f"YAML 无法解析: {path.relative_to(ROOT)}: {exc}")
        return None


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = read_text(path)
    match = FRONTMATTER_RE.match(text)
    if match is None:
        add_error(f"缺少 YAML frontmatter: {path.relative_to(ROOT)}")
        return {}, text
    try:
        metadata = yaml.safe_load(match.group(1)) or {}
    except Exception as exc:  # noqa: BLE001
        add_error(f"frontmatter 无法解析: {path.relative_to(ROOT)}: {exc}")
        return {}, text
    if not isinstance(metadata, dict):
        add_error(f"frontmatter 必须是对象: {path.relative_to(ROOT)}")
        return {}, text
    return metadata, text[match.end() :]


def resolve_repository_path(value: str, owner: Path) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    if value.startswith(".cursor/") or value.startswith("docs/") or value.startswith("schemas/"):
        return ROOT / candidate
    return owner.parent / candidate


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def as_date(value: Any, label: str) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value)
        except ValueError:
            pass
    add_error(f"日期格式无效: {label}: {value!r}")
    return None


def normalized_content(data: bytes) -> bytes:
    return data if b"\0" in data else data.replace(b"\r\n", b"\n")


def tree_digest(root: Path) -> tuple[int, str]:
    records: list[tuple[str, str]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        digest = hashlib.sha256(normalized_content(path.read_bytes())).hexdigest()
        records.append((relative, digest))
    hasher = hashlib.sha256()
    for relative, digest in sorted(records):
        hasher.update(f"{relative}\0{digest}\n".encode("utf-8"))
    return len(records), hasher.hexdigest()


def check_hooks() -> None:
    """校验 Cursor hooks 配置与本项目依赖的关键事件。"""
    hooks_json = ROOT / ".cursor" / "hooks.json"
    if not hooks_json.exists():
        add_error("缺失 .cursor/hooks.json")
        return
    hooks = load_yaml(hooks_json)
    if not isinstance(hooks, dict) or hooks.get("version") != 1:
        add_error(".cursor/hooks.json version 必须为 1")
        return
    hook_defs = hooks.get("hooks") or {}
    if not isinstance(hook_defs, dict):
        add_error(".cursor/hooks.json hooks 必须为对象")
        return
    required = {
        "sessionStart",
        "beforeShellExecution",
        "beforeMCPExecution",
        "preToolUse",
        "subagentStart",
        "subagentStop",
        "stop",
    }
    missing = required - set(hook_defs)
    if missing:
        add_error(f".cursor/hooks.json 缺少事件: {sorted(missing)}")
    for event_name, entries in hook_defs.items():
        if not isinstance(entries, list):
            add_error(f"Hook entries 必须为列表: {event_name}")
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                add_error(f"Hook 条目必须为对象: {event_name}")
                continue
            if entry.get("type") != "command":
                add_error(f"Hook type 必须为 command: {event_name}")
            timeout = entry.get("timeout")
            if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 30:
                add_error(f"Hook timeout 必须显式设置且 <=30s: {event_name}")
            command = entry.get("command")
            if not isinstance(command, str) or not command:
                add_error(f"Hook 缺少 command: {event_name}")
                continue
            script = next(
                (
                    token
                    for token in reversed(command.split())
                    if token.endswith((".py", ".sh", ".ts", ".js"))
                ),
                "",
            )
            if not script or not (ROOT / script).exists():
                add_error(f"Hook 脚本不存在: {event_name}: {script or command}")
                continue
            if (
                event_name
                in {
                    "beforeReadFile",
                    "beforeShellExecution",
                    "beforeMCPExecution",
                    "preToolUse",
                    "subagentStart",
                }
                and entry.get("failClosed") is not True
            ):
                add_error(f"Guard Hook 必须 failClosed: {event_name}")
            if (
                event_name == "preToolUse"
                and command.endswith("subagent_pretool_guard.py")
                and entry.get("matcher") != "Task"
            ):
                add_error("Subagent preToolUse guard 必须 matcher=Task")
            if (
                event_name == "preToolUse"
                and command.endswith("secret_guard.py")
                and entry.get("matcher") != "Read"
            ):
                add_error("Secret preToolUse guard 必须 matcher=Read")
            if event_name == "stop":
                script_text = read_text(ROOT / script)
                code_only = re.sub(
                    r'"""(?:.|\n)*?"""|\'\'\'(?:.|\n)*?\'\'\'|#[^\n]*', "", script_text
                )
                if re.search(r"git\s+(?:commit|push)\b", code_only):
                    add_error(f".cursor/hooks stop 脚本不得执行 git commit/push: {script}")
    read_guards = [
        entry
        for entry in hook_defs.get("preToolUse") or []
        if isinstance(entry, dict) and str(entry.get("command") or "").endswith("secret_guard.py")
    ]
    if (
        len(read_guards) != 1
        or read_guards[0].get("matcher") != "Read"
        or read_guards[0].get("failClosed") is not True
    ):
        add_error("Read secret guard 必须唯一绑定为 fail-closed preToolUse matcher=Read")


def check_required_structure() -> None:
    required_files = {
        ".cursor/README.md",
        ".cursorignore",
        "VERSION",
        ".cursor/framework.json",
        ".cursor/compatibility/CURSOR_COMPATIBILITY.yaml",
        ".cursor/skills.lock.yaml",
        ".cursor/plans/ALL_PLAN.md",
        ".cursor/plans/archive/README.md",
        ".cursor/memory/INDEX.md",
    }
    for relative in required_files:
        path = ROOT / relative
        if not path.exists() or path.stat().st_size == 0:
            add_error(f"缺失或空治理文件: {relative}")

    check_hooks()

    rule_root = CURSOR_ROOT / "rules"
    actual_rules = {path.name for path in rule_root.glob("*.mdc")}
    missing_rules = EXPECTED_RULES - actual_rules
    extra_markdown_rules = sorted(path.name for path in rule_root.glob("*.md"))
    if missing_rules:
        add_error(f"缺少项目 Rule: {sorted(missing_rules)}")
    if extra_markdown_rules:
        add_error(f"Rules 目录存在不会被 Cursor 识别的 .md: {extra_markdown_rules}")

    skill_root = CURSOR_ROOT / "skills"
    actual_skills = {path.parent.name for path in skill_root.rglob("SKILL.md")}
    missing_skills = EXPECTED_SKILLS - actual_skills
    if missing_skills:
        add_error(f"缺少项目 Skill: {sorted(missing_skills)}")


def check_rules() -> None:
    rule_root = CURSOR_ROOT / "rules"
    for path in sorted(rule_root.glob("*.mdc")):
        metadata, _ = parse_frontmatter(path)
        always_apply = metadata.get("alwaysApply")
        if not isinstance(always_apply, bool):
            add_error(f"Rule alwaysApply 必须为 bool: {path.relative_to(ROOT)}")
        if always_apply is False and not metadata.get("description") and not metadata.get("globs"):
            add_error(f"非 always Rule 必须设置 description 或 globs: {path.relative_to(ROOT)}")
        expected = EXPECTED_RULE_METADATA.get(path.name)
        if expected is not None:
            if always_apply is not expected["always_apply"]:
                add_error(
                    f"Rule alwaysApply 与期望不符: {path.name}: {always_apply!r} != {expected['always_apply']}"
                )
            if expected["has_globs"] and not metadata.get("globs"):
                add_error(f"Rule 缺少 globs: {path.name}")
            if not expected["has_globs"] and metadata.get("globs"):
                add_error(f"Rule 不应设置 globs（应为 alwaysApply）: {path.name}")

    delegation_path = rule_root / "10-agent-delegation.mdc"
    delegation_text = read_text(delegation_path)
    required_patterns = {
        "少于 4 个": r"少于\s*4\s*个",
        "最多 3 个": r"最多\s*3\s*个",
        "禁止嵌套": r"禁止.{0,12}(?:嵌套|创建|委派).{0,12}子代理|子代理.{0,12}禁止.{0,12}(?:子代理|委派)",
        "根代理所有权": r"只有.{0,12}根代理.{0,12}(?:创建|委派)",
    }
    for label, pattern in required_patterns.items():
        if re.search(pattern, delegation_text) is None:
            add_error(f"子代理规则缺少约束“{label}”")

    for path in sorted(rule_root.glob("*.mdc")):
        if path == delegation_path:
            continue
        text = read_text(path)
        if "子代理" in text and re.search(r"(?:最多|上限|少于)\s*\d+", text):
            add_error(
                f"子代理数值预算只能由 10-agent-delegation.mdc 定义: {path.relative_to(ROOT)}"
            )

    git_text = read_text(rule_root / "43-git-commit-policy.mdc")
    if "每个任务默认一个本地语义提交" in git_text:
        add_error("Git Rule 不得为每个任务默认创建 commit")
    if re.search(r"提交必须.*最新 recheck|必须发生在.*recheck", git_text, re.I):
        add_error("Git Rule 不得把 recheck 变成所有提交的无条件前置")

    arch_meta, arch_body = parse_frontmatter(rule_root / "44-code-architecture.mdc")
    if arch_meta.get("alwaysApply") is not False or not arch_meta.get("globs"):
        add_error("Architecture Rule 必须限定到产品代码 globs，不得 Always Apply")
    if "调用/数据流方向为 `domain → application → adapter/infra`" in arch_body:
        add_error("Architecture Rule 混淆 runtime control flow 与 dependency direction")
    for required_flow in (
        "entry adapter → application use case → domain",
        "application → inward-owned Port → adapter / infrastructure",
    ):
        if required_flow not in arch_body:
            add_error(f"Architecture Rule 缺少明确控制流: {required_flow}")


def check_skills() -> None:
    skill_root = CURSOR_ROOT / "skills"
    for path in sorted(skill_root.rglob("SKILL.md")):
        metadata, _ = parse_frontmatter(path)
        expected_name = path.parent.name
        if metadata.get("name") != expected_name:
            add_error(
                f"Skill name 必须匹配目录: {path.relative_to(ROOT)}: "
                f"{metadata.get('name')!r} != {expected_name!r}"
            )
        description = metadata.get("description")
        if not isinstance(description, str) or not description.strip():
            add_error(f"Skill 缺少 description: {path.relative_to(ROOT)}")
        disable = metadata.get("disable-model-invocation")
        if disable is not None and not isinstance(disable, bool):
            add_error(f"disable-model-invocation 必须为 bool: {path.relative_to(ROOT)}")

    explicit_skills = {"all-plan", "recheck", "engineering-memory"}
    for name in explicit_skills:
        path = skill_root / name / "SKILL.md"
        metadata, _ = parse_frontmatter(path)
        if metadata.get("disable-model-invocation") is not True:
            add_error(f"{name} 必须只允许显式调用")


def check_external_skill_lock() -> None:
    path = CURSOR_ROOT / "skills.lock.yaml"
    if not path.exists():
        add_error("缺少 .cursor/skills.lock.yaml")
        return
    try:
        payload = yaml.safe_load(read_text(path)) or {}
    except Exception as exc:  # noqa: BLE001
        add_error(f"外部 Skill lock 无法解析: {exc}")
        return

    if payload.get("schema_version") != 3:
        add_error("skills.lock.yaml schema_version 必须为 3")
    policy = payload.get("policy") or {}
    if policy.get("mode") != "SOURCE_PIN_ONLY":
        add_error("skills.lock.yaml 必须使用 SOURCE_PIN_ONLY 便携策略")
    if policy.get("digest_scheme") != "PATH_AND_CONTENT_SHA256_V1":
        add_error("skills.lock.yaml 必须声明 PATH_AND_CONTENT_SHA256_V1")
    policy_gate = policy.get("upgrade_gate") or {}
    required_upgrade_checks = {
        "immutable_revision_resolution",
        "content_digest_verification",
        "license_review",
        "content_diff_review",
        "capability_permission_network_credential_diff",
        "cursor_compatibility_validation",
    }
    if policy_gate.get("explicit_user_approval") is not True:
        add_error("外部 Skill 升级必须要求显式用户批准")
    if set(policy_gate.get("required_checks") or []) != required_upgrade_checks:
        add_error("外部 Skill 全局升级检查集合不完整")

    skills = payload.get("skills") or []
    if not isinstance(skills, list):
        add_error("skills.lock.yaml skills 必须为列表")
        return
    seen: set[str] = set()
    for entry in skills:
        if not isinstance(entry, dict):
            add_error("外部 Skill 条目必须是对象")
            continue
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            add_error("外部 Skill 缺少 name")
            continue
        if name in seen:
            add_error(f"外部 Skill 重复: {name}")
        seen.add(name)
        if entry.get("availability") != "OPTIONAL":
            add_error(f"外部 user-level Skill 必须显式标记 OPTIONAL: {name}")
        source = entry.get("source") or {}
        revision = source.get("revision")
        source_path = source.get("path")
        if (
            not source.get("repository")
            or not source.get("license")
            or not source.get("license_evidence")
        ):
            add_error(f"外部 Skill 缺少 repository/license/license_evidence: {name}")
        if (
            not isinstance(source_path, str)
            or not source_path
            or source_path.startswith(("/", "\\"))
            or ".." in Path(source_path).parts
        ):
            add_error(f"外部 Skill source.path 必须是安全相对路径: {name}")
        if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
            add_error(f"外部 Skill revision 必须是完整 commit: {name}")
        license_evidence = str(source.get("license_evidence") or "")
        if revision and revision not in license_evidence:
            add_error(f"外部 Skill license evidence 必须绑定锁定 revision: {name}")

        content = entry.get("content") or {}
        digest = content.get("digest")
        if (
            content.get("digest_algorithm") != "sha256"
            or content.get("digest_scheme") != "PATH_AND_CONTENT_SHA256_V1"
        ):
            add_error(f"外部 Skill content digest 算法/方案无效: {name}")
        if (
            not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or digest == "0" * 64
        ):
            add_error(f"外部 Skill content digest 必须是非占位 SHA-256: {name}")
        if (
            not isinstance(content.get("file_count"), int)
            or isinstance(content.get("file_count"), bool)
            or content.get("file_count", 0) <= 0
        ):
            add_error(f"外部 Skill content file_count 必须为正整数: {name}")
        as_date(content.get("verified_at"), f"skills.lock.{name}.content.verified_at")

        item_gate = entry.get("upgrade_gate") or {}
        if (
            item_gate.get("explicit_user_approval") is not True
            or item_gate.get("required_checks") != "inherit_policy"
        ):
            add_error(f"外部 Skill 条目必须继承显式升级门禁: {name}")
        if "installations" in entry:
            add_error(f"便携主包不得锁定用户 home 目录 installation: {name}")


def check_version_source() -> None:
    version_path = ROOT / "VERSION"
    if not version_path.exists():
        add_error("缺少 VERSION")
        return
    version = read_text(version_path).strip()
    try:
        framework = json.loads(read_text(CURSOR_ROOT / "framework.json"))
    except json.JSONDecodeError as exc:
        add_error(f".cursor/framework.json 无法解析: {exc}")
        return
    if framework.get("framework_version") != version:
        add_error("framework_version 与 VERSION 不一致")
    if framework.get("version_source") != "VERSION":
        add_error("framework version_source 必须为 VERSION")
    if "research_os_baseline" in framework:
        add_error("不得维护独立 research_os_baseline")


def load_task_plans() -> dict[str, tuple[Path, dict[str, Any], str]]:
    result: dict[str, tuple[Path, dict[str, Any], str]] = {}
    plan_roots = (
        CURSOR_ROOT / "plans" / "tasks",
        CURSOR_ROOT / "plans" / "archive",
    )
    for plan_root in plan_roots:
        for path in sorted(plan_root.glob("PLAN-*.md")):
            metadata, body = parse_frontmatter(path)
            plan_id = metadata.get("id")
            if not isinstance(plan_id, str) or re.fullmatch(r"PLAN-\d{8}-\d{3}", plan_id) is None:
                add_error(f"任务计划 ID 无效: {path.relative_to(ROOT)}: {plan_id!r}")
                continue
            if not path.name.startswith(plan_id + "-"):
                add_error(f"任务计划文件名必须以 ID 开头: {path.relative_to(ROOT)}")
            if plan_id in result:
                add_error(f"任务计划 ID 重复: {plan_id}")
            if plan_root.name == "archive" and metadata.get("status") not in {"DONE", "CANCELLED"}:
                add_error(f"归档任务必须为 DONE/CANCELLED: {plan_id}: {metadata.get('status')!r}")
            result[plan_id] = (path, metadata, body)
    return result


def load_rechecks() -> dict[str, tuple[Path, dict[str, Any], str]]:
    result: dict[str, tuple[Path, dict[str, Any], str]] = {}
    recheck_roots = (
        CURSOR_ROOT / "plans" / "rechecks",
        CURSOR_ROOT / "plans" / "archive",
    )
    for recheck_root in recheck_roots:
        for path in sorted(recheck_root.glob("RECHECK-*.md")):
            metadata, body = parse_frontmatter(path)
            recheck_id = metadata.get("id")
            if (
                not isinstance(recheck_id, str)
                or re.fullmatch(r"RECHECK-\d{8}-\d{3}", recheck_id) is None
            ):
                add_error(f"复检 ID 无效: {path.relative_to(ROOT)}: {recheck_id!r}")
                continue
            if not path.name.startswith(recheck_id + "-"):
                add_error(f"复检文件名必须以 ID 开头: {path.relative_to(ROOT)}")
            if recheck_id in result:
                add_error(f"复检 ID 重复: {recheck_id}")
            result[recheck_id] = (path, metadata, body)
    return result


def check_plans_and_rechecks() -> None:
    plans = load_task_plans()
    rechecks = load_rechecks()
    all_plan_path = CURSOR_ROOT / "plans" / "ALL_PLAN.md"
    all_plan_text = read_text(all_plan_path)
    indexed: dict[str, tuple[bool, str, str]] = {}
    for checked, plan_id, target, projected_status in PLAN_INDEX_ROW_RE.findall(all_plan_text):
        if plan_id in indexed:
            add_error(f"ALL_PLAN 重复索引任务: {plan_id}")
        indexed[plan_id] = (checked.lower() == "x", target, projected_status)

    for plan_id, (path, metadata, body) in plans.items():
        status = metadata.get("status")
        if status not in PLAN_STATUSES:
            add_error(f"任务状态无效: {plan_id}: {status!r}")
        parallel_limit = metadata.get("subagent_parallel_limit")
        if parallel_limit != 3:
            add_error(f"subagent_parallel_limit 必须为 3: {plan_id}: {parallel_limit!r}")
        if "subagent_budget" in metadata or "subagents_used" in metadata:
            add_error(f"任务计划不得使用累计 subagent budget 字段: {plan_id}")
        for field in ("created_at", "updated_at"):
            as_date(metadata.get(field), f"{plan_id}.{field}")
        for heading in ("## 验收条件", "## 实施清单", "## 证据", "## 状态历史", "## 影响报告"):
            if heading not in body:
                add_error(f"任务计划缺少章节 {heading}: {plan_id}")

        if plan_id not in indexed:
            add_error(f"任务计划未加入 ALL_PLAN: {plan_id}")
            continue
        checked, target, projected_status = indexed[plan_id]
        resolved_target = resolve_repository_path(target, all_plan_path).resolve()
        if resolved_target != path.resolve():
            add_error(f"ALL_PLAN 任务链接错误: {plan_id}: {target}")
        if projected_status != status:
            add_error(f"ALL_PLAN 状态投影不一致: {plan_id}: {projected_status} != {status}")
        if checked != (status == "DONE"):
            add_error(f"ALL_PLAN 勾选与 DONE 状态不一致: {plan_id}")

        latest_recheck = metadata.get("latest_recheck")
        memory_entries = as_list(metadata.get("memory_entries"))
        if status == "DONE":
            if "[ ]" in body:
                add_error(f"DONE 任务仍有未勾选项: {plan_id}")
            if not latest_recheck:
                add_error(f"DONE 任务缺少 latest_recheck: {plan_id}")
            else:
                recheck_path = resolve_repository_path(str(latest_recheck), path)
                if not recheck_path.exists():
                    add_error(f"DONE 任务复检不存在: {plan_id}: {latest_recheck}")
                else:
                    recheck_meta, _ = parse_frontmatter(recheck_path)
                    if recheck_meta.get("result") not in {"PASS", "PASS_WITH_WARNINGS"}:
                        add_error(f"DONE 任务复检未通过: {plan_id}: {recheck_meta.get('result')!r}")
            if not memory_entries:
                if "无可复用事实" not in body and "无可复用事实" not in (
                    latest_recheck
                    and read_text(resolve_repository_path(str(latest_recheck), path))
                    or ""
                ):
                    add_error(f"DONE 任务既无工程记忆引用，也未声明无可复用事实: {plan_id}")
            if "待填写" in body or "PENDING" in body:
                add_error(f"DONE 任务仍包含占位内容: {plan_id}")

    for plan_id in indexed.keys() - plans.keys():
        add_error(f"ALL_PLAN 引用了不存在的任务: {plan_id}")

    for recheck_id, (path, metadata, body) in rechecks.items():
        plan_id = metadata.get("plan_id")
        if plan_id not in plans:
            add_error(f"复检引用不存在的任务: {recheck_id}: {plan_id!r}")
        status = metadata.get("status")
        result = metadata.get("result")
        if status not in RECHECK_STATUSES:
            add_error(f"复检状态无效: {recheck_id}: {status!r}")
        if result is not None and result not in RECHECK_RESULTS:
            add_error(f"复检结果无效: {recheck_id}: {result!r}")
        if status == "COMPLETED" and result is None:
            add_error(f"已完成复检缺少 result: {recheck_id}")
        if result in {"PASS", "PASS_WITH_WARNINGS"} and "PENDING" in body:
            add_error(f"通过的复检仍有 PENDING gate: {recheck_id}")
        if result in {"PASS", "PASS_WITH_WARNINGS"} and "待填写" in body:
            add_error(f"通过的复检仍有占位内容: {recheck_id}")
        as_date(metadata.get("created_at"), f"{recheck_id}.created_at")
        if metadata.get("completed_at") is not None:
            as_date(metadata.get("completed_at"), f"{recheck_id}.completed_at")
        if "## 检查结果" not in body or "## 结论" not in body:
            add_error(f"复检缺少检查结果或结论: {recheck_id}")


def check_memory() -> None:
    entry_root = CURSOR_ROOT / "memory" / "entries"
    entries: dict[str, Path] = {}
    for path in sorted(entry_root.glob("MEM-*.md")):
        metadata, body = parse_frontmatter(path)
        memory_id = metadata.get("id")
        if not isinstance(memory_id, str) or re.fullmatch(r"MEM-\d{8}-\d{3}", memory_id) is None:
            add_error(f"工程记忆 ID 无效: {path.relative_to(ROOT)}: {memory_id!r}")
            continue
        if not path.name.startswith(memory_id + "-"):
            add_error(f"工程记忆文件名必须以 ID 开头: {path.relative_to(ROOT)}")
        if memory_id in entries:
            add_error(f"工程记忆 ID 重复: {memory_id}")
        entries[memory_id] = path

        if metadata.get("status") not in MEMORY_STATUSES:
            add_error(f"工程记忆状态无效: {memory_id}: {metadata.get('status')!r}")
        confidence = metadata.get("confidence")
        if (
            not isinstance(confidence, (int, float))
            or isinstance(confidence, bool)
            or not 0 <= confidence <= 1
        ):
            add_error(f"工程记忆 confidence 必须在 0–1: {memory_id}: {confidence!r}")
        created_at = as_date(metadata.get("created_at"), f"{memory_id}.created_at")
        review_after = as_date(metadata.get("review_after"), f"{memory_id}.review_after")
        if created_at and review_after and review_after < created_at:
            add_error(f"工程记忆 review_after 早于 created_at: {memory_id}")
        source_plans = as_list(metadata.get("source_plans"))
        source_rechecks = as_list(metadata.get("source_rechecks"))
        if not source_plans or not source_rechecks:
            add_error(f"工程记忆必须同时引用计划和复检: {memory_id}")
        for source in [*source_plans, *source_rechecks]:
            if not isinstance(source, str):
                add_error(f"工程记忆来源必须是路径: {memory_id}: {source!r}")
                continue
            if not resolve_repository_path(source, path).exists():
                add_error(f"工程记忆来源不存在: {memory_id}: {source}")
        for heading in (
            "## 做了什么",
            "## 为什么这样做",
            "## 怎么做与复现",
            "## 适用边界",
            "## 来源",
        ):
            if heading not in body:
                add_error(f"工程记忆缺少章节 {heading}: {memory_id}")
        if "待填写" in body:
            add_error(f"工程记忆仍包含占位内容: {memory_id}")

    index_path = CURSOR_ROOT / "memory" / "INDEX.md"
    index_text = read_text(index_path)
    linked_ids = re.findall(r"\[(MEM-\d{8}-\d{3})\]\(([^)]+)\)", index_text)
    seen: set[str] = set()
    for memory_id, target in linked_ids:
        if memory_id in seen:
            add_error(f"工程记忆 INDEX 重复: {memory_id}")
        seen.add(memory_id)
        if memory_id not in entries:
            add_error(f"工程记忆 INDEX 引用不存在: {memory_id}")
            continue
        if resolve_repository_path(target, index_path).resolve() != entries[memory_id].resolve():
            add_error(f"工程记忆 INDEX 链接错误: {memory_id}: {target}")
    for memory_id in entries.keys() - seen:
        add_error(f"工程记忆未加入 INDEX: {memory_id}")


def check_git_history_preservation() -> None:
    git_marker = ROOT / ".git"
    if not git_marker.exists():
        add_warning("当前包不含本地 Git 元数据，跳过历史身份删除保护")
        return

    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    completed = subprocess.run(
        [
            "git",
            "log",
            "--all",
            "--format=",
            "--name-only",
            "--",
            ".cursor/plans",
            ".cursor/memory/entries",
        ],
        cwd=ROOT,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        add_error(f"无法读取本地 Git 治理历史: {completed.stderr.strip()}")
        return

    identity_re = re.compile(r"(?:PLAN|RECHECK|MEM)-\d{8}-\d{3}")
    historical_ids = set(identity_re.findall(completed.stdout))
    current_ids = {
        match.group(0)
        for root in (
            CURSOR_ROOT / "plans" / "tasks",
            CURSOR_ROOT / "plans" / "rechecks",
            CURSOR_ROOT / "plans" / "archive",
            CURSOR_ROOT / "memory" / "entries",
        )
        for path in root.glob("*.md")
        if (match := identity_re.search(path.name)) is not None
    }
    missing = historical_ids - current_ids
    if missing:
        add_error(f"治理历史身份从工作树消失，必须归档而非删除: {sorted(missing)}")


def iter_cursor_text_files() -> Iterable[Path]:
    for path in CURSOR_ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".mdc", ".yaml", ".yml", ".py"}:
            yield path


def check_links_and_secrets() -> None:
    for path in sorted(iter_cursor_text_files()):
        text = read_text(path)
        if path.suffix.lower() in {".md", ".mdc"}:
            for target in MARKDOWN_LINK_RE.findall(text):
                clean_target = target.split("#", 1)[0].strip()
                if not clean_target or clean_target.startswith(("http://", "https://", "mailto:")):
                    continue
                if any(token in clean_target for token in ("...", "YYYY", "{", "}")):
                    continue
                resolved = resolve_repository_path(clean_target, path)
                if not resolved.exists():
                    add_error(f"Markdown 链接失效: {path.relative_to(ROOT)} -> {target}")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                add_error(f"Cursor 治理资产疑似包含 {label}: {path.relative_to(ROOT)}")


def check_runtime_config() -> None:
    config_path = CURSOR_ROOT / "runtime_config.json"
    if not config_path.exists():
        add_error("缺少 .cursor/runtime_config.json（runtime 行为配置必须显式登记）")
        return
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        add_error(f".cursor/runtime_config.json 无法解析: {exc}")
        return
    if not isinstance(payload, dict):
        add_error(".cursor/runtime_config.json 顶层必须是 JSON 对象")
        return
    allowed_keys = {"schema_version", "observation_retention_days"}
    unknown = set(payload) - allowed_keys
    if unknown:
        add_error(f".cursor/runtime_config.json 存在未登记键: {sorted(unknown)}")
    if payload.get("schema_version") != 1:
        add_error(
            f".cursor/runtime_config.json schema_version 必须为 1: {payload.get('schema_version')!r}"
        )
    retention = payload.get("observation_retention_days")
    if isinstance(retention, bool) or not isinstance(retention, int) or retention <= 0:
        add_error(
            f".cursor/runtime_config.json observation_retention_days 必须为正整数: {retention!r}"
        )
    hooks_ref = read_text(CURSOR_ROOT / "knowledge" / "HOOKS_REFERENCE.md")
    if "runtime_config.json" not in hooks_ref:
        add_error(
            ".cursor/knowledge/HOOKS_REFERENCE.md 必须引用 runtime_config.json（文档与配置漂移防护）"
        )


def main() -> int:
    checks = (
        check_required_structure,
        check_rules,
        check_skills,
        check_external_skill_lock,
        check_version_source,
        check_plans_and_rechecks,
        check_memory,
        check_git_history_preservation,
        check_runtime_config,
        check_links_and_secrets,
    )
    for check in checks:
        check()

    for warning in WARNINGS:
        print(f"警告: {warning}")
    if ERRORS:
        print("Cursor 治理验证失败:")
        for error in ERRORS:
            print(f"- {error}")
        return 1

    print("Cursor 治理验证通过")
    print("- Rules / Skills frontmatter 与作用域有效")
    print("- 子代理按 wave 最多 3；无全任务累计上限；禁止嵌套")
    print("- ALL_PLAN / Task Plan / Recheck / Memory 交叉引用一致")
    print(
        "- 外部 Skill 使用 immutable revision + content digest + upgrade gate；主包不依赖开发者 home 目录安装"
    )
    print("- VERSION 与 Cursor framework metadata 单一版本源一致")
    print("- 未发现明显凭据材料")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
