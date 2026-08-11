from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

NON_RELEASE_DIRS = frozenset(
    {
        ".git",
        ".import_linter_cache",
        ".mypy_cache",
        ".pnpm-store",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "node_modules",
    }
)
RUNTIME_KEEP = frozenset({".cursor/runtime/.gitignore", ".cursor/runtime/.gitkeep"})
GENERATED_RELEASE_ASSETS = frozenset(
    {"FRAMEWORK_MANIFEST.json", ".cursor/releases/RELEASE_EVIDENCE.json"}
)


def source_files(root: Path) -> Iterator[Path]:
    for directory, child_dirs, filenames in os.walk(root, topdown=True):
        child_dirs[:] = [name for name in child_dirs if name not in NON_RELEASE_DIRS]
        current = Path(directory)
        for filename in filenames:
            path = current / filename
            relative = path.relative_to(root).as_posix()
            if path.suffix == ".pyc":
                continue
            if relative.startswith(".cursor/runtime/") and relative not in RUNTIME_KEEP:
                continue
            yield path


def releasable_files(root: Path) -> Iterator[Path]:
    return (
        path
        for path in source_files(root)
        if path.relative_to(root).as_posix() not in GENERATED_RELEASE_ASSETS
    )


def archive_files(root: Path, output: Path) -> Iterator[Path]:
    resolved_output = output.resolve()
    return (path for path in source_files(root) if path.resolve() != resolved_output)