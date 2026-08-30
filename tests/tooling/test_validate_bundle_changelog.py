"""validate_bundle CHANGELOG 版本一致性检查回归测试（M15 remediation WP7）。"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

_VALIDATOR_PATH = (
    Path(__file__).resolve().parents[2]
    / ".cursor/skills/system-spec-check/scripts/validate_bundle.py"
)


@pytest.fixture()
def validator() -> Any:
    spec = importlib.util.spec_from_file_location("validate_bundle", _VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _version_section(version: str = "0.4.0") -> list[str]:
    return [
        "## Unreleased",
        "",
        "- M15 changes (unreleased)",
        "",
        f"## v{version} — 2026-08-15（M11 Evaluation Plane）",
        "",
        "- Released history.",
    ]


def test_changelog_ahead_of_version_is_rejected(validator: Any, tmp_path: Path) -> None:
    """CHANGELOG 中任何超前于 VERSION 的已发布标题都必须失败。"""
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("\n".join(_version_section("9.9.9")), encoding="utf-8")
    errors: list[str] = []
    validator._check_changelog_version_consistency(changelog, "0.4.0", errors)
    assert any("超前" in error for error in errors)


def test_changelog_current_and_unreleased_pass(validator: Any, tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("\n".join(_version_section("0.4.0")), encoding="utf-8")
    errors: list[str] = []
    validator._check_changelog_version_consistency(changelog, "0.4.0", errors)
    assert errors == []
