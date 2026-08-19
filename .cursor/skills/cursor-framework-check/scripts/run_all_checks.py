#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

FRAMEWORK_SCRIPTS = (
    ".cursor/skills/system-spec-check/scripts/validate_bundle.py",
    ".cursor/skills/governance-check/scripts/validate.py",
    ".cursor/skills/cursor-framework-check/scripts/validate_cursor_framework.py",
    ".cursor/skills/learning-check/scripts/validate_cursor_learning.py",
    ".cursor/skills/cursor-framework-check/scripts/run_cursor_hook_evals.py",
    ".cursor/skills/cursor-framework-check/scripts/run_cursor_framework_evals.py",
    ".cursor/skills/learning-check/scripts/run_cursor_learning_evals.py",
    "tools/docs_consistency_check.py",
)
PRODUCT_ROOTS = ("apps", "services", "packages", "adapters", "tests")
STRICT_PYTHON_FILES = (
    ".cursor/hooks/common.py",
    ".cursor/hooks/secret_guard.py",
    ".cursor/hooks/shell_guard.py",
    ".cursor/hooks/mcp_guard.py",
    ".cursor/hooks/subagent_guard.py",
    ".cursor/hooks/subagent_pretool_guard.py",
    ".cursor/skills/cursor-framework-check/scripts/run_all_checks.py",
)
RELEASE_ASSETS = (
    "FRAMEWORK_MANIFEST.json",
    ".cursor/releases/RELEASE_EVIDENCE.json",
)
PROFILE_NAMES = ("framework", "python", "typescript", "m0")


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    command: tuple[str, ...]


def discover_root() -> Path:
    explicit = os.environ.get("CURSOR_FRAMEWORK_ROOT")
    if explicit:
        return Path(explicit).resolve()
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "VERSION").is_file() and (
            candidate / ".cursor" / "framework.json"
        ).is_file():
            return candidate
    raise RuntimeError("Cannot locate repository root (VERSION + .cursor/framework.json)")


def python_command(*arguments: str) -> tuple[str, ...]:
    return (sys.executable, *arguments)


def pnpm_command(*arguments: str) -> tuple[str, ...]:
    executable = shutil.which("pnpm")
    if executable is None:
        return ("pnpm", *arguments)
    if os.name == "nt":
        return ("cmd.exe", "/d", "/s", "/c", executable, *arguments)
    return (executable, *arguments)


def framework_checks() -> tuple[Check, ...]:
    return tuple(
        Check(name=f"framework/{Path(script).stem}", command=python_command("-B", script))
        for script in FRAMEWORK_SCRIPTS
    )


def existing_product_roots(root: Path) -> tuple[str, ...]:
    return tuple(directory for directory in PRODUCT_ROOTS if (root / directory).is_dir())


def python_checks(root: Path) -> tuple[Check, ...]:
    product_roots = existing_product_roots(root)
    format_targets = (*STRICT_PYTHON_FILES, *product_roots)
    boundary_test = "tests/architecture/python/test_dependency_boundaries.py"
    return (
        Check(
            name="python/engineering-lint",
            command=python_command(
                "-m",
                "ruff",
                "check",
                ".cursor/hooks",
                ".cursor/skills",
                "--select",
                "F,I",
            ),
        ),
        Check(
            name="python/product-lint",
            command=python_command("-m", "ruff", "check", *product_roots),
        ),
        Check(
            name="python/format-check",
            command=python_command("-m", "ruff", "format", "--check", *format_targets),
        ),
        Check(name="python/typecheck", command=python_command("-m", "mypy")),
        Check(
            name="python/dependency-boundaries",
            command=python_command("-m", "pytest", boundary_test),
        ),
        Check(
            name="python/tests",
            command=python_command("-m", "pytest", f"--ignore={boundary_test}"),
        ),
    )


def typescript_checks() -> tuple[Check, ...]:
    return tuple(
        Check(name=f"typescript/{script}", command=pnpm_command("run", script))
        for script in ("format:check", "lint", "typecheck", "boundaries", "test")
    )


def checks_for(profile: str, root: Path) -> tuple[Check, ...]:
    groups = {
        "framework": framework_checks(),
        "python": python_checks(root),
        "typescript": typescript_checks(),
    }
    if profile == "m0":
        return groups["python"] + groups["typescript"] + groups["framework"]
    return groups[profile]


def asset_state(root: Path) -> dict[str, str | None]:
    return {
        relative: hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        for relative in RELEASE_ASSETS
        if (path := root / relative)
    }


def display_command(command: Sequence[str]) -> str:
    return subprocess.list2cmdline(command)


def run_check(check: Check, root: Path, env: dict[str, str]) -> int:
    print(f"RUN [{check.name}]: {display_command(check.command)}", flush=True)
    try:
        completed = subprocess.run(
            check.command,
            cwd=root,
            env=env,
            check=False,
        )
    except OSError as exc:
        print(f"FAILED [{check.name}]: command unavailable: {exc}", flush=True)
        return 127
    if completed.returncode == 0:
        print(f"PASS [{check.name}]", flush=True)
    else:
        print(f"FAILED [{check.name}]: exit {completed.returncode}", flush=True)
    return completed.returncode


def parse_args(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic Research System quality gates")
    parser.add_argument("--profile", choices=PROFILE_NAMES, default="m0")
    parser.add_argument(
        "--keep-going",
        action="store_true",
        help="run every selected check before returning failure",
    )
    return parser.parse_args(arguments)


def main(arguments: Sequence[str] | None = None) -> int:
    args = parse_args(arguments)
    root = discover_root()
    before_assets = asset_state(root)
    env = {
        **os.environ,
        "CURSOR_FRAMEWORK_ROOT": str(root),
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
        "NO_COLOR": "1",
    }
    failures: list[tuple[str, int]] = []
    selected = checks_for(str(args.profile), root)
    for check in selected:
        returncode = run_check(check, root, env)
        if returncode != 0:
            failures.append((check.name, returncode))
            if not args.keep_going:
                break

    after_assets = asset_state(root)
    if after_assets != before_assets:
        failures.append(("release-assets-immutable", 1))
        print(
            "FAILED [release-assets-immutable]: ordinary checks modified release evidence",
            flush=True,
        )
    else:
        print("PASS [release-assets-immutable]", flush=True)

    if failures:
        rendered = ", ".join(f"{name}={code}" for name, code in failures)
        print(f"FAILED: {len(failures)} check(s): {rendered}", flush=True)
        return failures[0][1] or 1
    print(f"PASS: profile={args.profile}; {len(selected)} deterministic checks", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
