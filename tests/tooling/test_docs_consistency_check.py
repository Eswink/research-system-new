from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "tools" / "docs_consistency_check.py"


def load_runner() -> Any:
    namespace = runpy.run_path(str(HELPER))
    return namespace["run_checks"]


def write(root: Path, relative: str, content: str = "") -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_consistent_fixture(root: Path) -> None:
    write(root, "CODEX_BOOTSTRAP.md")
    write(root, "README.md")
    write(
        root,
        "BACKLOG.md",
        "M8-M11 完成\n| 能力 | M8 Capability Plane | DONE |\n"
        "| 能力 | M9 Runtime | DONE |\n"
        "| 能力 | M10 Memory | DONE |\n"
        "| 能力 | M11 Eval | DONE |\n",
    )
    write(
        root,
        "docs/INDEX.md",
        "M8-M11 完成\nroadmap/COMPLETION_MATRIX_M0_M11.md\n"
        "roadmap/M8_COMPLETION_RECORD.md\nroadmap/M9_COMPLETION_RECORD.md\n"
        "roadmap/M10_COMPLETION_RECORD.md\nroadmap/M11_COMPLETION_RECORD.md\n",
    )
    milestones = (
        "## 未来 Milestone 总览\n\n"
        "| Stage | 名称 | 分层 | Hard Deps | 状态 |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| M8 | Capability Plane | MVP | M7 | DONE |\n"
        "| M9 | Runtime | MVP | M7 | DONE |\n"
        "| M10 | Memory | MVP | M7 | DONE |\n"
        "| M11 | Eval | MVP | M7 | DONE |\n\n"
        "## 依赖 DAG\n\ntext\n\n"
        "## M8 — Capability Plane\n\n完成状态\n\n"
        "## M9 — Runtime\n\n完成状态\n\n"
        "## M10 — Memory\n\n完成状态\n\n"
        "## M11 — Eval\n\n完成状态\n"
    )
    write(root, "docs/roadmap/MILESTONES.md", milestones)
    matrix = (
        "| Stage | Scope | Status |\n"
        "| --- | --- | --- |\n"
        "| M8 | Capability Plane | DONE |\n"
        "| M9 | Runtime | DONE |\n"
        "| M10 | Memory | DONE |\n"
        "| M11 | Eval | DONE |\n"
    )
    write(root, "docs/roadmap/COMPLETION_MATRIX_M0_M11.md", matrix)
    for milestone_id in ("M8", "M9", "M10", "M11"):
        write(root, f"docs/roadmap/{milestone_id}_COMPLETION_RECORD.md", f"# {milestone_id}\n")


def test_consistent_fixture_passes(tmp_path: Path) -> None:
    build_consistent_fixture(tmp_path)
    assert load_runner()(tmp_path) == []


def test_index_missing_completion_record_reported(tmp_path: Path) -> None:
    build_consistent_fixture(tmp_path)
    write(tmp_path, "docs/INDEX.md", "M8-M11 完成\nroadmap/COMPLETION_MATRIX_M0_M11.md\n")
    findings = load_runner()(tmp_path)
    assert any("index-missing" in finding for finding in findings)


def test_done_milestone_without_record_reported(tmp_path: Path) -> None:
    build_consistent_fixture(tmp_path)
    (tmp_path / "docs/roadmap/M11_COMPLETION_RECORD.md").unlink()
    findings = load_runner()(tmp_path)
    assert any("M11 DONE 但" in finding for finding in findings)


def test_backlog_status_conflict_reported(tmp_path: Path) -> None:
    build_consistent_fixture(tmp_path)
    write(tmp_path, "BACKLOG.md", "M8-M11 完成\n| 能力 | M8 Capability Plane | PLANNED |\n")
    findings = load_runner()(tmp_path)
    assert any("BACKLOG 行状态不一致" in finding for finding in findings)


def test_dangling_plan_ref_reported(tmp_path: Path) -> None:
    build_consistent_fixture(tmp_path)
    write(
        tmp_path,
        "docs/roadmap/M8_COMPLETION_RECORD.md",
        "Plan: `PLAN-20260899-999`\n",
    )
    findings = load_runner()(tmp_path)
    assert any("dangling-ref" in finding and "PLAN-20260899-999" in finding for finding in findings)


def test_broken_backtick_ref_reported(tmp_path: Path) -> None:
    build_consistent_fixture(tmp_path)
    write(tmp_path, "docs/INDEX.md", "M8-M11 完成\n引用 `packages/nope.py`\n")
    findings = load_runner()(tmp_path)
    assert any("backtick-ref" in finding and "packages/nope.py" in finding for finding in findings)


def test_duplicate_milestone_reported(tmp_path: Path) -> None:
    build_consistent_fixture(tmp_path)
    milestones = (tmp_path / "docs/roadmap/MILESTONES.md").read_text(encoding="utf-8")
    duplicate = milestones.replace(
        "| M8 | Capability Plane | MVP | M7 | DONE |",
        "| M8 | Capability Plane | MVP | M7 | DONE |\n| M8 | Duplicate | MVP | M7 | PLANNED |",
    )
    write(tmp_path, "docs/roadmap/MILESTONES.md", duplicate)
    findings = load_runner()(tmp_path)
    assert any("duplicate-milestone" in finding for finding in findings)


def test_real_repo_is_clean() -> None:
    assert load_runner()(ROOT) == []
