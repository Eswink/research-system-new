#!/usr/bin/env python3
"""Deterministic documentation consistency checks for M0-M11 records.

Covers gaps not handled by validate_bundle.py / governance validate.py:
- INDEX roadmap-section completeness (M*_COMPLETION_RECORD + unified matrix)
- milestone status consistency (MILESTONES table vs completion records /
  BACKLOG / unified completion matrix)
- completion-record plan/recheck dangling references
- backtick code references resolvable from repo root
- duplicate milestone names
- HEAD status marker regression guard

Pure stdlib; deterministic; exit code 0 on clean.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROADMAP_DIR = "docs/roadmap"
INDEX_FILE = "docs/INDEX.md"
BACKLOG_FILE = "BACKLOG.md"
MILESTONES_FILE = "docs/roadmap/MILESTONES.md"
UNIFIED_MATRIX = "docs/roadmap/COMPLETION_MATRIX_M0_M11.md"
MILESTONE_IDS = ("M8", "M9", "M10", "M11", "M12", "M13", "M14", "M15")
# COMPLETION_MATRIX_M0_M11 只覆盖 M0-M11；M12+ 的状态由各自 completion record /
# recheck 记录与 BACKLOG 承载。
MATRIX_SCOPE_IDS = ("M8", "M9", "M10", "M11")
KNOWN_PREFIXES = (
    "packages/",
    "adapters/",
    "tests/",
    "schemas/",
    "examples/",
    "tools/",
    ".cursor/",
    "docs/",
    ".github/",
    "pyproject.toml",
    "uv.lock",
    "pnpm-lock.yaml",
    "tsconfig.json",
    "tsconfig.base.json",
    "eslint.config.mjs",
    "dependency-cruiser.config.mjs",
    "UPSTREAM_COMPONENTS.yaml",
    "VERSION",
)
BACKTICK_SOURCES = (
    "docs",
    "README.md",
    "BACKLOG.md",
    "CODEX_BOOTSTRAP.md",
)
IGNORED_BACKTICK_REFS = (
    "d:\\",
    "agent/agent.py",
    "openhands",
    "utils/",
)


class Checker:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.findings: list[str] = []

    def add(self, message: str) -> None:
        if message not in self.findings:
            self.findings.append(message)

    def read(self, relative: str) -> str:
        path = self.root / relative
        if not path.is_file():
            self.add(f"[missing-file] {relative}")
            return ""
        return path.read_text(encoding="utf-8")


def check_index_roadmap_completeness(checker: Checker) -> None:
    index = checker.read(INDEX_FILE)
    roadmap_dir = checker.root / ROADMAP_DIR
    if not roadmap_dir.is_dir():
        return
    expected = sorted(
        path.name for path in roadmap_dir.iterdir() if path.name.endswith("_COMPLETION_RECORD.md")
    )
    expected.append("COMPLETION_MATRIX_M0_M11.md")
    for name in expected:
        if f"roadmap/{name}" not in index:
            checker.add(f"[index-missing] {INDEX_FILE} Roadmap 节未引用 roadmap/{name}")


def extract_status_table(text: str, table_header: str) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("| ") and re.match(r"^\| M\d+ ", line):
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if len(cells) >= 5 and cells[1].startswith(table_header):
                statuses[cells[0]] = cells[-1]
    return statuses


def check_milestone_status_consistency(checker: Checker) -> None:
    milestones = checker.read(MILESTONES_FILE)
    backlog = checker.read(BACKLOG_FILE)
    matrix = checker.read(UNIFIED_MATRIX)
    overview = _section(milestones, "## 未来 Milestone 总览", "## 依赖 DAG")
    for milestone_id in MILESTONE_IDS:
        status = _overview_status(overview, milestone_id)
        if "DONE" in status.upper():
            _check_done_milestone(checker, milestones, backlog, matrix, milestone_id)
        else:
            _check_planned_milestone(checker, matrix, milestone_id)


def _overview_status(overview: str, milestone_id: str) -> str:
    for line in overview.splitlines():
        if line.startswith(f"| {milestone_id} "):
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if len(cells) >= 5:
                return cells[-1]
    return "UNKNOWN"


def _check_done_milestone(
    checker: Checker,
    milestones: str,
    backlog: str,
    matrix: str,
    milestone_id: str,
) -> None:
    record = f"{ROADMAP_DIR}/{milestone_id}_COMPLETION_RECORD.md"
    has_record = (checker.root / record).is_file()
    recheck = _has_recheck_record(checker.root, milestone_id)
    if not (has_record or recheck):
        checker.add(f"[milestone-status] {milestone_id} DONE 但既无 {record} 也无 recheck 记录")
    if not _has_completion_note(milestones, milestone_id):
        checker.add(f"[milestone-status] {milestone_id} DONE 但 MILESTONES 节内缺完成状态段")
    if not any(f"| {milestone_id} " in line and "DONE" in line for line in backlog.splitlines()):
        checker.add(f"[milestone-status] {milestone_id} DONE 但 BACKLOG 行状态不一致")
    if milestone_id in MATRIX_SCOPE_IDS and not any(
        line.startswith(f"| {milestone_id} ") and "DONE" in line for line in matrix.splitlines()
    ):
        checker.add(f"[milestone-status] {milestone_id} DONE 但 COMPLETION_MATRIX_M0_M11 行不一致")


def _has_recheck_record(root: Path, milestone_id: str) -> bool:
    rechecks = root / ".cursor" / "plans" / "rechecks"
    if not rechecks.is_dir():
        return False
    milestone_token = milestone_id.lower().replace("m", "m")
    return any(f"-{milestone_token}-" in path.name for path in rechecks.glob("*M*.md"))


def _check_planned_milestone(checker: Checker, matrix: str, milestone_id: str) -> None:
    marked_done = any(
        line.startswith(f"| {milestone_id} ") and "DONE" in line for line in matrix.splitlines()
    )
    if marked_done:
        checker.add(f"[milestone-status] {milestone_id} 非 DONE 但统一矩阵标记 DONE")


def _has_completion_note(milestones: str, milestone_id: str) -> bool:
    section_start = f"## {milestone_id} —"
    section_end = re.compile(r"^## M(?:[0-9]+) —")
    in_section = False
    for line in milestones.splitlines():
        if line.startswith(section_start):
            in_section = True
            continue
        if in_section and section_end.match(line):
            break
        if in_section and "完成状态" in line:
            return True
    return False


def _section(text: str, start: str, end: str) -> str:
    lines = text.splitlines()
    started = False
    collected: list[str] = []
    for line in lines:
        if line.startswith(start):
            started = True
            continue
        if started and line.startswith(end):
            break
        if started:
            collected.append(line)
    return "\n".join(collected)


PLAN_REF = re.compile(
    r"(?:\.cursor/plans/(?:tasks|rechecks)/)?(PLAN-\d{8}-\d{3}[-\w]*|RECHECK-\d{8}-\d{3}[-\w]*)"
)


def check_completion_record_refs(checker: Checker) -> None:
    roadmap_dir = checker.root / ROADMAP_DIR
    if not roadmap_dir.is_dir():
        return
    for record in sorted(roadmap_dir.glob("*_COMPLETION_RECORD.md")):
        text = record.read_text(encoding="utf-8")
        for match in PLAN_REF.finditer(text):
            ref = match.group(1)
            for directory in ("tasks", "rechecks"):
                plan_dir = checker.root / ".cursor" / "plans" / directory
                if list(plan_dir.glob(f"{ref}*.md")):
                    break
            else:
                checker.add(f"[dangling-ref] {record.relative_to(checker.root)} 引用 {ref} 不存在")


def backtick_refs(text: str) -> list[str]:
    return re.findall(r"`([^`]+)`", text)


def is_resolvable_ref(ref: str) -> bool:
    if not ref or " " in ref or ":" in ref or "{" in ref or "}" in ref:
        return False
    if "*" in ref or "?" in ref or "[" in ref:
        return False
    for ignored in IGNORED_BACKTICK_REFS:
        if ref.startswith(ignored):
            return False
    return ref.startswith(KNOWN_PREFIXES)


def resolve_ref(root: Path, ref: str) -> bool:
    target = root / ref
    if target.exists():
        return True
    for suffix in (".schema.json", ".json"):
        if (root / f"{ref}{suffix}").exists():
            return True
    try:
        return bool(list(root.glob(f"{ref}*.md")))
    except ValueError:
        return False


def check_backtick_code_refs(checker: Checker) -> None:
    for source in BACKTICK_SOURCES:
        base = checker.root / source
        files = [base] if base.is_file() else sorted(base.rglob("*.md"))
        for path in files:
            if "references" in path.parts and "upstream" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            for ref in backtick_refs(text):
                if not is_resolvable_ref(ref):
                    continue
                if not resolve_ref(checker.root, ref):
                    checker.add(
                        f"[backtick-ref] {path.relative_to(checker.root)} 引用 `{ref}` 不存在"
                    )


def check_milestone_name_duplicates(checker: Checker) -> None:
    milestones = checker.read(MILESTONES_FILE)
    matrix = checker.read(UNIFIED_MATRIX)
    overview = _section(milestones, "## 未来 Milestone 总览", "## 依赖 DAG")
    for label, text in (("MILESTONES", overview), ("COMPLETION_MATRIX", matrix)):
        seen: dict[str, int] = {}
        for line in text.splitlines():
            if line.startswith("| "):
                match = re.match(r"^\| (M\d+) \|", line)
                if match:
                    seen[match.group(1)] = seen.get(match.group(1), 0) + 1
        for milestone_id, count in seen.items():
            if count > 1:
                checker.add(f"[duplicate-milestone] {label} 表出现 {count} 次 {milestone_id}")


def check_head_status_marker(checker: Checker) -> None:
    index = checker.read(INDEX_FILE)
    backlog = checker.read(BACKLOG_FILE)
    for label, text in (("docs/INDEX.md", index), ("BACKLOG.md", backlog)):
        if "M8-M11" not in text:
            checker.add(f"[head-status] {label} 缺少 M8-M11 完成状态标记")


CHECKS = (
    ("index-roadmap", check_index_roadmap_completeness),
    ("milestone-status", check_milestone_status_consistency),
    ("completion-refs", check_completion_record_refs),
    ("backtick-refs", check_backtick_code_refs),
    ("milestone-duplicates", check_milestone_name_duplicates),
    ("head-status", check_head_status_marker),
)


def run_checks(root: Path) -> list[str]:
    checker = Checker(root)
    for _name, check in CHECKS:
        check(checker)
    return checker.findings


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Research OS docs consistency checks")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(arguments)
    findings = run_checks(args.root)
    for finding in findings:
        print(f"DOCS-FINDING: {finding}", flush=True)
    if findings:
        print(f"DOCS-CHECK FAILED: {len(findings)} finding(s)", flush=True)
        return 1
    print(f"DOCS-CHECK PASS: {len(CHECKS)} deterministic checks", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
