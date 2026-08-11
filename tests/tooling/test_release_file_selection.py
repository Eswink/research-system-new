from __future__ import annotations

import runpy
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import cast

ReleaseSelector = Callable[[Path], Iterator[Path]]
ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / ".cursor/skills/framework-release/scripts/_release_files.py"


def load_selector(name: str) -> ReleaseSelector:
    namespace = runpy.run_path(str(HELPER))
    return cast(ReleaseSelector, namespace[name])


def touch(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(relative, encoding="utf-8")


def relative_paths(root: Path, selector: ReleaseSelector) -> set[str]:
    return {path.relative_to(root).as_posix() for path in selector(root)}


def test_release_source_selector_prunes_local_dependency_state(tmp_path: Path) -> None:
    for relative in (
        "README.md",
        ".cursor/runtime/.gitignore",
        ".cursor/runtime/session.json",
        ".venv/package.py",
        "node_modules/package/index.js",
        ".pytest_cache/state",
    ):
        touch(tmp_path, relative)

    observed = relative_paths(tmp_path, load_selector("source_files"))
    assert observed == {"README.md", ".cursor/runtime/.gitignore"}


def test_releasable_selector_excludes_generated_evidence(tmp_path: Path) -> None:
    for relative in (
        "VERSION",
        "FRAMEWORK_MANIFEST.json",
        ".cursor/releases/RELEASE_EVIDENCE.json",
    ):
        touch(tmp_path, relative)

    observed = relative_paths(tmp_path, load_selector("releasable_files"))
    assert observed == {"VERSION"}
