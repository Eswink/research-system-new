"""validate_bundle 校验器新增逻辑的回归测试（M9）。

覆盖 DOCKERFILE 来源形态（source.kind=DOCKERFILE）的 ADOPTED 校验：
镜像不是 PyPI 包，不走 uv.lock 校验，但必须提供仓库内 Dockerfile、
sha256 base pin、https license evidence、upgrade gate 与 LICENSE_MATRIX
登记。这是对镜像供应链 pin（M9 DoD）的机器检查。
"""

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


def _dockerfile_source(
    path: str | None = "adapters/execution/sandbox/Dockerfile",
) -> dict[str, object]:
    return {"kind": "DOCKERFILE", "path": path}


def _resolution(digest: str | None = "sha256:" + "ab" * 32) -> dict[str, object]:
    return {"base_index_digest": digest, "version": "m9-sandbox-v1"}


def _license(
    spdx: str | None = "PSF-2.0",
    evidence: str | None = "https://example.com/LICENSE",
) -> dict[str, object]:
    return {"spdx": spdx, "evidence": evidence}


def _gate() -> dict[str, object]:
    return {"explicit_approval": True, "required_checks": ["image_rebuild", "container_e2e"]}


class TestDockerfileAdopted:
    def test_valid_dockerfile_component_passes(
        self, validator: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        monkeypatch.setattr(validator, "ROOT", tmp_path)
        (tmp_path / "adapters/execution/sandbox").mkdir(parents=True)
        (tmp_path / "adapters/execution/sandbox/Dockerfile").write_text(
            "FROM python:3.12-slim\n", encoding="utf-8"
        )
        validator._check_dockerfile_adopted(
            "sandbox_image",
            _dockerfile_source(),
            _resolution(),
            _license(),
            _gate(),
            "sandbox_image in matrix",
        )
        assert validator.ERRORS == []

    def test_missing_dockerfile_path_rejected(
        self, validator: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        monkeypatch.setattr(validator, "ROOT", tmp_path)
        validator._check_dockerfile_adopted(
            "sandbox_image",
            _dockerfile_source(path="missing/Dockerfile"),
            _resolution(),
            _license(),
            _gate(),
            "sandbox_image in matrix",
        )
        assert any("source.path 不存在" in error for error in validator.ERRORS)

    def test_non_sha256_base_pin_rejected(
        self, validator: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        monkeypatch.setattr(validator, "ROOT", tmp_path)
        (tmp_path / "adapters/execution/sandbox").mkdir(parents=True)
        (tmp_path / "adapters/execution/sandbox/Dockerfile").write_text("x", encoding="utf-8")
        validator._check_dockerfile_adopted(
            "sandbox_image",
            _dockerfile_source(),
            _resolution(digest="latest"),
            _license(),
            _gate(),
            "sandbox_image in matrix",
        )
        assert any("base_index_digest" in error for error in validator.ERRORS)

    def test_missing_license_evidence_rejected(
        self, validator: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        monkeypatch.setattr(validator, "ROOT", tmp_path)
        (tmp_path / "adapters/execution/sandbox").mkdir(parents=True)
        (tmp_path / "adapters/execution/sandbox/Dockerfile").write_text("x", encoding="utf-8")
        validator._check_dockerfile_adopted(
            "sandbox_image",
            _dockerfile_source(),
            _resolution(),
            _license(spdx=None, evidence="file://local"),
            _gate(),
            "sandbox_image in matrix",
        )
        assert any("SPDX/license evidence" in error for error in validator.ERRORS)

    def test_missing_upgrade_gate_rejected(
        self, validator: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        monkeypatch.setattr(validator, "ROOT", tmp_path)
        (tmp_path / "adapters/execution/sandbox").mkdir(parents=True)
        (tmp_path / "adapters/execution/sandbox/Dockerfile").write_text("x", encoding="utf-8")
        validator._check_dockerfile_adopted(
            "sandbox_image",
            _dockerfile_source(),
            _resolution(),
            _license(),
            {},
            "sandbox_image in matrix",
        )
        assert any("升级门禁" in error for error in validator.ERRORS)

    def test_missing_license_matrix_entry_rejected(
        self, validator: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "ERRORS", [])
        monkeypatch.setattr(validator, "ROOT", tmp_path)
        (tmp_path / "adapters/execution/sandbox").mkdir(parents=True)
        (tmp_path / "adapters/execution/sandbox/Dockerfile").write_text("x", encoding="utf-8")
        validator._check_dockerfile_adopted(
            "sandbox_image",
            _dockerfile_source(),
            _resolution(),
            _license(),
            _gate(),
            "no such entry",
        )
        assert any("LICENSE_MATRIX 缺少" in error for error in validator.ERRORS)
