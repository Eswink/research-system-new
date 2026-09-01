"""validate_bundle NPM 来源 ADOPTED 校验（cursor_sdk）的回归测试。"""

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


_DIGEST = {
    "algorithm": "sha256",
    "artifact": "tarball",
    "value": "b" * 64,
}
_LICENSE = {
    "spdx": "LicenseRef-Anysphere-Proprietary",
    "evidence": "https://cursor.com/terms-of-service",
}
_GATE = {"explicit_approval": True, "required_checks": ["orchestration_contract_tests"]}


def _source(package: str | None = "@cursor/sdk") -> dict[str, object]:
    return {"kind": "NPM", "package": package}


def _resolution(version: str | None = "1.0.30") -> dict[str, object]:
    return {"version": version}


def _dev(spec: str | None = "1.0.30") -> dict[str, object]:
    return {"@cursor/sdk": spec}


def _lock_keys(entry: str | None = "@cursor/sdk@1.0.30") -> set[str]:
    return {entry} if entry else set()


class TestNpmAdopted:
    def test_valid_npm_component_passes(
        self, validator: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        validator._check_npm_adopted(
            "cursor_sdk",
            _source(),
            _resolution(),
            _DIGEST,
            _LICENSE,
            _GATE,
            "cursor_sdk in matrix",
            _dev(),
            _lock_keys(),
        )
        assert validator.ERRORS == []

    def test_caret_spec_rejected(self, validator: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        validator._check_npm_adopted(
            "cursor_sdk",
            _source(),
            _resolution(),
            _DIGEST,
            _LICENSE,
            _GATE,
            "cursor_sdk in matrix",
            _dev("^1.0.30"),
            _lock_keys(),
        )
        assert any("精确锁定" in error for error in validator.ERRORS)

    def test_missing_lockfile_entry_rejected(
        self, validator: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        validator._check_npm_adopted(
            "cursor_sdk",
            _source(),
            _resolution(),
            _DIGEST,
            _LICENSE,
            _GATE,
            "cursor_sdk in matrix",
            _dev(),
            _lock_keys(None),
        )
        assert any("未进入 pnpm-lock" in error for error in validator.ERRORS)

    def test_sdist_style_digest_rejected(
        self, validator: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        bad_digest = {"algorithm": "sha256", "artifact": "sdist", "value": "b" * 64}
        validator._check_npm_adopted(
            "cursor_sdk",
            _source(),
            _resolution(),
            bad_digest,
            _LICENSE,
            _GATE,
            "cursor_sdk in matrix",
            _dev(),
            _lock_keys(),
        )
        assert any("tarball sha256 digest 无效" in error for error in validator.ERRORS)

    def test_short_digest_rejected(self, validator: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        bad_digest = {"algorithm": "sha256", "artifact": "tarball", "value": "abc"}
        validator._check_npm_adopted(
            "cursor_sdk",
            _source(),
            _resolution(),
            bad_digest,
            _LICENSE,
            _GATE,
            "cursor_sdk in matrix",
            _dev(),
            _lock_keys(),
        )
        assert any("tarball sha256 digest 无效" in error for error in validator.ERRORS)

    def test_non_https_license_evidence_rejected(
        self, validator: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        validator._check_npm_adopted(
            "cursor_sdk",
            _source(),
            _resolution(),
            _DIGEST,
            {"spdx": "MIT", "evidence": "file:///LICENSE"},
            _GATE,
            "cursor_sdk in matrix",
            _dev(),
            _lock_keys(),
        )
        assert any("SPDX/license evidence" in error for error in validator.ERRORS)

    def test_missing_upgrade_gate_rejected(
        self, validator: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        validator._check_npm_adopted(
            "cursor_sdk",
            _source(),
            _resolution(),
            _DIGEST,
            _LICENSE,
            {"explicit_approval": False, "required_checks": []},
            "cursor_sdk in matrix",
            _dev(),
            _lock_keys(),
        )
        assert any("升级门禁" in error for error in validator.ERRORS)

    def test_missing_license_matrix_entry_rejected(
        self, validator: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        validator._check_npm_adopted(
            "cursor_sdk",
            _source(),
            _resolution(),
            _DIGEST,
            _LICENSE,
            _GATE,
            "some other matrix",
            _dev(),
            _lock_keys(),
        )
        assert any("LICENSE_MATRIX 缺少" in error for error in validator.ERRORS)
