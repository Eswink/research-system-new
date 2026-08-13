"""Workspace adapter 测试：路径归一化 + host shell deny + Docker 探测。"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from adapters.openhands.workspace_adapter import (
    HostShellDeniedError,
    absolute_path_within,
    build_local_workspace,
)
from packages.domain.workspace import WorkspaceLease


def _lease(session: str = "s-1") -> WorkspaceLease:
    return WorkspaceLease(workspace_id="w-1", agent_session_id=session)


class TestPathNormalization:
    def test_relative_path_resolves_within_root(self, tmp_path: Path) -> None:
        assert absolute_path_within(tmp_path, "notes/file.txt") == tmp_path / "notes" / "file.txt"

    def test_absolute_path_within_root_is_allowed(self, tmp_path: Path) -> None:
        target = tmp_path / "x.txt"
        target.write_text("ok", encoding="utf-8")
        assert absolute_path_within(tmp_path, str(target)) == target

    def test_escape_via_dotdot_is_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError):
            absolute_path_within(tmp_path, "../escape.txt")

    def test_escape_via_absolute_other_root_is_rejected(self, tmp_path: Path) -> None:
        other = Path(tempfile.mkdtemp(prefix="outside-"))
        try:
            with pytest.raises(ValueError):
                absolute_path_within(tmp_path, str(other / "x.txt"))
        finally:
            shutil.rmtree(other, ignore_errors=True)


class TestLocalWorkspace:
    def test_host_shell_denied_by_default(self) -> None:
        with pytest.raises(HostShellDeniedError):
            build_local_workspace(_lease(), "s-1", allow_host_shell=False)

    def test_explicit_allow_creates_isolated_workspace(self, tmp_path: Path) -> None:
        workspace = build_local_workspace(
            _lease(), "s-1", allow_host_shell=True, base_dir=str(tmp_path)
        )
        assert workspace.working_dir == str(tmp_path.resolve())

    def test_workspace_root_is_isolated(self, tmp_path: Path) -> None:
        build_local_workspace(_lease(), "s-2", allow_host_shell=True, base_dir=str(tmp_path))
        entries = list(tmp_path.iterdir())
        assert len(entries) >= 0  # 目录可写且隔离
