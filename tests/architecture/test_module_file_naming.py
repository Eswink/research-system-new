from __future__ import annotations

from pathlib import Path, PurePosixPath

import pytest

from tests.architecture.module_file_naming import (
    LEGACY_PATH_EXCEPTIONS,
    classify_path,
    collect_violations,
    stale_legacy_exceptions,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "relative",
    (
        "packages/domain/run_state.py",
        "packages/domain/__init__.py",
        "tests/domain/test_run_state.py",
        "apps/web/src/features/runs/RunPanel.tsx",
        "apps/web/src/features/runs/useRunPanel.ts",
        "apps/web/src/features/setup/wizardApi.ts",
        "apps/web/tests/unit/run-api.test.ts",
        "tests/architecture/typescript/fixtures/valid/packages/domain/src/research-question.ts",
        "adapters/postgres/migrations/013_usage_replay.sql",
    ),
)
def test_valid_product_paths_are_accepted(relative: str) -> None:
    assert classify_path(PurePosixPath(relative)) == ()


@pytest.mark.parametrize(
    ("relative", "reason_fragment"),
    (
        ("packages/domain/RunState.py", "snake_case"),
        ("packages/domain/run state.py", "whitespace"),
        ("packages/domain/运行状态.py", "ASCII"),
        ("packages/run-domain/model.py", "package directory"),
        ("apps/web/src/features/runs/run_panel.tsx", "TypeScript source"),
        ("apps/web/src/features/runs/use_run_panel.ts", "TypeScript source"),
        ("apps/web/src/features/run_history/runPanel.ts", "source directory"),
        ("apps/web/tests/unit/run_api.test.ts", "test or fixture"),
        (
            "tests/architecture/typescript/fixtures/valid/packages/domain/src/badFixture.ts",
            "test or fixture",
        ),
        ("adapters/postgres/migrations/013_UsageReplay.sql", "migration"),
        ("packages/domain/run_state_v2.py", "version suffix"),
        ("packages/domain/final.py", "lifecycle label"),
    ),
)
def test_invalid_product_paths_are_rejected(relative: str, reason_fragment: str) -> None:
    reasons = classify_path(PurePosixPath(relative))
    assert any(reason_fragment in reason for reason in reasons), reasons


def test_pascal_case_component_must_match_its_only_export(tmp_path: Path) -> None:
    source = tmp_path / "apps" / "web" / "src" / "features" / "runs" / "RunPanel.tsx"
    source.parent.mkdir(parents=True)
    source.write_text("export function OtherPanel() { return null; }\n", encoding="utf-8")

    violations = collect_violations(tmp_path)

    assert any(
        violation.path == "apps/web/src/features/runs/RunPanel.tsx"
        and "component export" in violation.reason
        for violation in violations
    )


def test_hook_filename_must_match_export(tmp_path: Path) -> None:
    source = tmp_path / "apps" / "web" / "src" / "features" / "runs" / "useRunPanel.ts"
    source.parent.mkdir(parents=True)
    source.write_text("export function useOtherPanel() { return {}; }\n", encoding="utf-8")

    violations = collect_violations(tmp_path)

    assert any(
        violation.path == "apps/web/src/features/runs/useRunPanel.ts"
        and "hook export" in violation.reason
        for violation in violations
    )


def test_primary_component_requires_pascal_case_filename(tmp_path: Path) -> None:
    source = tmp_path / "apps" / "web" / "src" / "features" / "runs" / "runPanel.tsx"
    source.parent.mkdir(parents=True)
    source.write_text("export function RunPanel() { return null; }\n", encoding="utf-8")

    violations = collect_violations(tmp_path)

    assert any(
        violation.path == "apps/web/src/features/runs/runPanel.tsx"
        and "component export" in violation.reason
        for violation in violations
    )


def test_exported_hook_requires_matching_use_filename(tmp_path: Path) -> None:
    source = tmp_path / "apps" / "web" / "src" / "features" / "runs" / "runPanel.ts"
    source.parent.mkdir(parents=True)
    source.write_text("export function useRunPanel() { return {}; }\n", encoding="utf-8")

    violations = collect_violations(tmp_path)

    assert any(
        violation.path == "apps/web/src/features/runs/runPanel.ts"
        and "hook export" in violation.reason
        for violation in violations
    )


def test_non_source_product_files_still_require_ascii_paths(tmp_path: Path) -> None:
    target = tmp_path / "apps" / "web" / "public" / "用户配置.json"
    target.parent.mkdir(parents=True)
    target.write_text("{}\n", encoding="utf-8")

    violations = collect_violations(tmp_path)

    assert any(
        violation.path == "apps/web/public/用户配置.json" and "ASCII" in violation.reason
        for violation in violations
    )


def test_python_module_containing_tests_requires_test_prefix(tmp_path: Path) -> None:
    source = tmp_path / "tests" / "domain" / "run_checks.py"
    source.parent.mkdir(parents=True)
    source.write_text("def test_run_state():\n    pass\n", encoding="utf-8")

    violations = collect_violations(tmp_path)

    assert any(
        violation.path == "tests/domain/run_checks.py" and "Python test module" in violation.reason
        for violation in violations
    )


def test_legacy_baseline_is_exact_and_not_stale() -> None:
    assert len(LEGACY_PATH_EXCEPTIONS) == 26
    assert not any(set(path) & {"*", "?", "[", "]"} for path in LEGACY_PATH_EXCEPTIONS)
    assert stale_legacy_exceptions(ROOT) == ()


def test_generated_playwright_artifacts_are_not_policed(tmp_path: Path) -> None:
    """test-results 的目录名取自用例标题（可含中文），不属于仓库路径规则。"""

    artifact = tmp_path / "apps" / "web" / "test-results"
    shot = artifact / "用例标题（dark-normal-zh）" / "shot.png"
    shot.parent.mkdir(parents=True)
    shot.write_bytes(b"")

    assert collect_violations(tmp_path) == ()


def test_current_repository_has_no_unapproved_naming_violations() -> None:
    violations = collect_violations(ROOT)
    rendered = "\n".join(f"{item.path}: {item.reason}" for item in violations)
    assert violations == (), rendered
