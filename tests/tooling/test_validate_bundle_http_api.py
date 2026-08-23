"""validate_bundle 校验器新增逻辑的回归测试（M12）。"""

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


def _http_source(url: str | None = "https://eutils.ncbi.nlm.nih.gov/") -> dict[str, object]:
    return {"kind": "HTTP_API", "url": url}


def _resolution(version: str | None = "2026-08-22") -> dict[str, object]:
    return {"version": version}


def _license(
    spdx: str | None = "NLM-TOU",
    evidence: str | None = "https://www.ncbi.nlm.nih.gov/books/NBK25497/",
) -> dict[str, object]:
    return {"spdx": spdx, "evidence": evidence}


def _gate() -> dict[str, object]:
    return {"explicit_approval": True, "required_checks": ["provider_contract_suite"]}


class TestHttpApiAdopted:
    def test_valid_http_api_component_passes(
        self, validator: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        validator._check_http_api_adopted(
            "ncbi_eutils",
            _http_source(),
            _resolution(),
            _license(),
            _gate(),
            "ncbi_eutils in matrix",
        )
        assert validator.ERRORS == []

    def test_non_https_source_rejected(
        self, validator: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        validator._check_http_api_adopted(
            "ncbi_eutils",
            _http_source(url="http://eutils.ncbi.nlm.nih.gov/"),
            _resolution(),
            _license(),
            _gate(),
            "ncbi_eutils in matrix",
        )
        assert any("source.url 必须是 https" in error for error in validator.ERRORS)

    def test_missing_resolution_version_rejected(
        self, validator: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        validator._check_http_api_adopted(
            "ncbi_eutils",
            _http_source(),
            _resolution(version=None),
            _license(),
            _gate(),
            "ncbi_eutils in matrix",
        )
        assert any("resolution.version" in error for error in validator.ERRORS)

    def test_missing_license_evidence_rejected(
        self, validator: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        validator._check_http_api_adopted(
            "ncbi_eutils",
            _http_source(),
            _resolution(),
            _license(evidence="file://local"),
            _gate(),
            "ncbi_eutils in matrix",
        )
        assert any("SPDX/license evidence" in error for error in validator.ERRORS)

    def test_missing_upgrade_gate_rejected(
        self, validator: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        validator._check_http_api_adopted(
            "ncbi_eutils",
            _http_source(),
            _resolution(),
            _license(),
            {},
            "ncbi_eutils in matrix",
        )
        assert any("升级门禁" in error for error in validator.ERRORS)

    def test_missing_license_matrix_entry_rejected(
        self, validator: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        validator._check_http_api_adopted(
            "ncbi_eutils",
            _http_source(),
            _resolution(),
            _license(),
            _gate(),
            "no such entry",
        )
        assert any("LICENSE_MATRIX 缺少" in error for error in validator.ERRORS)
