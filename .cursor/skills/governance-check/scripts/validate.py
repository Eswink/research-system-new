#!/usr/bin/env python3
"""离线验证 Research OS 的 Cursor 工程治理资产。"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parents[4]
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
    "30-ui-skill-routing.mdc",
    "40-python.mdc",
    "41-typescript.mdc",
    "50-contract-assets.mdc",
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


def check_required_structure() -> None:
    required_files = {
        ".cursor/README.md",
        ".cursor/skills.lock.yaml",
        ".cursor/plans/ALL_PLAN.md",
        ".cursor/memory/INDEX.md",
    }
    for relative in required_files:
        path = ROOT / relative
        if not path.exists() or path.stat().st_size == 0:
            add_error(f"缺失或空治理文件: {relative}")

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
            add_error(f"子代理数值预算只能由 10-agent-delegation.mdc 定义: {path.relative_to(ROOT)}")


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

    explicit_skills = {"all-plan", "recheck"}
    for name in explicit_skills:
        path = skill_root / name / "SKILL.md"
        metadata, _ = parse_frontmatter(path)
        if metadata.get("disable-model-invocation") is not True:
            add_error(f"{name} 必须只允许显式调用")


def check_external_skill_lock() -> None:
    path = CURSOR_ROOT / "skills.lock.yaml"
    lock = load_yaml(path)
    if not isinstance(lock, dict):
        add_error("skills.lock.yaml 顶层必须是对象")
        return
    if lock.get("schema_version") != 1:
        add_error("skills.lock.yaml schema_version 必须为 1")
    if lock.get("digest_algorithm") != "sha256-path-content-lf-v1":
        add_error("skills.lock.yaml digest_algorithm 不受支持")

    skills = lock.get("skills")
    if not isinstance(skills, list):
        add_error("skills.lock.yaml skills 必须是数组")
        return
    locked_names = {item.get("name") for item in skills if isinstance(item, dict)}
    for required in {"impeccable", "shadcn"}:
        if required not in locked_names:
            add_error(f"外部技能锁缺少: {required}")

    for item in skills:
        if not isinstance(item, dict):
            add_error("skills.lock.yaml skill 条目必须是对象")
            continue
        name = item.get("name", "<unknown>")
        source = item.get("source") or {}
        policy = item.get("installation_policy") or {}
        installations = item.get("installations")
        revision = source.get("revision")
        if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
            add_error(f"外部 Skill revision 必须是完整 commit: {name}")
        if not source.get("repository") or not source.get("license"):
            add_error(f"外部 Skill 缺少 repository/license: {name}")
        if policy.get("mode") != "ALL_LISTED_INSTALLATIONS_MUST_MATCH":
            add_error(f"外部 Skill installation_policy 不受支持: {name}")
        if not isinstance(installations, list) or not installations:
            add_error(f"外部 Skill 必须声明至少一个安装树: {name}")
            continue

        listed_paths: set[Path] = set()
        for installation in installations:
            if not isinstance(installation, dict):
                add_error(f"外部 Skill installation 必须是对象: {name}")
                continue
            raw_path = installation.get("path")
            provider = installation.get("provider")
            if not isinstance(raw_path, str) or not provider:
                add_error(f"外部 Skill installation 缺少 path/provider: {name}")
                continue
            installed_path = Path(raw_path).expanduser()
            resolved_path = installed_path.resolve()
            if resolved_path in listed_paths:
                add_error(f"外部 Skill 重复声明安装路径: {name}: {raw_path}")
                continue
            listed_paths.add(resolved_path)
            if not installed_path.exists():
                add_error(f"已锁定的全局 Skill 安装不存在: {name}/{provider}: {raw_path}")
                continue

            expected_count = installation.get("expected_file_count")
            expected_digest = installation.get("tree_digest")
            actual_count, actual_digest = tree_digest(installed_path)
            if actual_count != expected_count:
                add_error(
                    f"全局 Skill 文件数漂移: {name}/{provider}: "
                    f"{actual_count} != {expected_count}"
                )
            if actual_digest != expected_digest:
                add_error(
                    f"全局 Skill digest 漂移: {name}/{provider}: "
                    f"{actual_digest} != {expected_digest}"
                )

            declared_version = installation.get("declared_version")
            if declared_version:
                metadata, _ = parse_frontmatter(installed_path / "SKILL.md")
                if str(metadata.get("version")) != str(declared_version):
                    add_error(
                        f"全局 Skill 声明版本漂移: {name}/{provider}: "
                        f"{metadata.get('version')!r} != {declared_version!r}"
                    )

        discoverable_roots = (
            Path("~/.agents/skills").expanduser(),
            Path("~/.cursor/skills").expanduser(),
            Path("~/.claude/skills").expanduser(),
            Path("~/.codex/skills").expanduser(),
        )
        unlisted = {
            (root / str(name)).resolve()
            for root in discoverable_roots
            if (root / str(name)).exists() and (root / str(name)).resolve() not in listed_paths
        }
        if unlisted:
            add_error(f"发现未锁定的同名全局 Skill: {name}: {sorted(map(str, unlisted))}")


def check_bootstrap_manifest() -> None:
    path = ROOT / "BOOTSTRAP_MANIFEST.json"
    try:
        manifest = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        add_error(f"BOOTSTRAP_MANIFEST.json 无法解析: {exc}")
        return
    for item in manifest.get("files", []):
        relative = item.get("path")
        expected = item.get("sha256")
        target = ROOT / str(relative)
        if not target.exists():
            add_error(f"冻结 Bootstrap 文件缺失: {relative}")
            continue
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != expected:
            add_error(f"冻结 Bootstrap digest 漂移: {relative}")


def load_task_plans() -> dict[str, tuple[Path, dict[str, Any], str]]:
    result: dict[str, tuple[Path, dict[str, Any], str]] = {}
    for path in sorted((CURSOR_ROOT / "plans" / "tasks").glob("PLAN-*.md")):
        metadata, body = parse_frontmatter(path)
        plan_id = metadata.get("id")
        if not isinstance(plan_id, str) or re.fullmatch(r"PLAN-\d{8}-\d{3}", plan_id) is None:
            add_error(f"任务计划 ID 无效: {path.relative_to(ROOT)}: {plan_id!r}")
            continue
        if not path.name.startswith(plan_id + "-"):
            add_error(f"任务计划文件名必须以 ID 开头: {path.relative_to(ROOT)}")
        if plan_id in result:
            add_error(f"任务计划 ID 重复: {plan_id}")
        result[plan_id] = (path, metadata, body)
    return result


def load_rechecks() -> dict[str, tuple[Path, dict[str, Any], str]]:
    result: dict[str, tuple[Path, dict[str, Any], str]] = {}
    for path in sorted((CURSOR_ROOT / "plans" / "rechecks").glob("RECHECK-*.md")):
        metadata, body = parse_frontmatter(path)
        recheck_id = metadata.get("id")
        if not isinstance(recheck_id, str) or re.fullmatch(r"RECHECK-\d{8}-\d{3}", recheck_id) is None:
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
        budget = metadata.get("subagent_budget")
        used = metadata.get("subagents_used")
        if not isinstance(budget, int) or not 0 <= budget <= 3:
            add_error(f"subagent_budget 必须在 0–3: {plan_id}: {budget!r}")
        if not isinstance(used, int) or used < 0 or isinstance(budget, bool) or (isinstance(budget, int) and used > budget):
            add_error(f"subagents_used 无效或超过预算: {plan_id}: {used!r}/{budget!r}")
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
                add_error(f"DONE 任务缺少工程记忆引用: {plan_id}")
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
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
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
        for heading in ("## 做了什么", "## 为什么这样做", "## 怎么做与复现", "## 适用边界", "## 来源"):
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


def iter_cursor_text_files() -> Iterable[Path]:
    for path in CURSOR_ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".mdc", ".yaml", ".yml", ".py"}:
            yield path


def check_links_and_secrets() -> None:
    for path in sorted(iter_cursor_text_files()):
        text = read_text(path)
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


def main() -> int:
    checks = (
        check_required_structure,
        check_rules,
        check_skills,
        check_external_skill_lock,
        check_bootstrap_manifest,
        check_plans_and_rechecks,
        check_memory,
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
    print("- 子代理预算少于 4 且禁止嵌套")
    print("- ALL_PLAN / Task Plan / Recheck / Memory 交叉引用一致")
    print("- Impeccable / shadcn 安装树与技能锁一致")
    print("- v0.2.2 Bootstrap 冻结文件摘要未漂移")
    print("- 未发现明显凭据材料")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())