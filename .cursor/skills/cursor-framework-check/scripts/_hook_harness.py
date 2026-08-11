from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


class HookHarness:
    """Fast in-process harness for project command hooks.

    Real subprocess/stdin/stdout contract smoke tests still live in the public eval script.
    This harness is for the larger behavioral matrix so release validation does not pay a
    Python cold-start cost for every single hook case.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.hooks_dir = self.root / ".cursor" / "hooks"
        os.environ["CURSOR_FRAMEWORK_ROOT"] = str(self.root)
        hook_path = str(self.hooks_dir)
        if hook_path not in sys.path:
            sys.path.insert(0, hook_path)
        self._modules: dict[str, ModuleType] = {}

    def _module(self, filename: str) -> ModuleType:
        if filename in self._modules:
            return self._modules[filename]
        path = self.hooks_dir / filename
        name = f"cursor_eval_hook_{path.stem}"
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Cannot load hook: {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(name, None)
            raise
        self._modules[filename] = module
        return module

    def call(self, filename: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any], str]:
        module = self._module(filename)
        old_stdin = sys.stdin
        stdin = io.StringIO(json.dumps(payload, ensure_ascii=False))
        stdout = io.StringIO()
        stderr = io.StringIO()
        try:
            sys.stdin = stdin
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                rc = int(module.main())
        finally:
            sys.stdin = old_stdin
        raw = stdout.getvalue().strip()
        try:
            parsed = json.loads(raw or "{}")
            if not isinstance(parsed, dict):
                parsed = {"_raw": raw}
        except Exception:
            parsed = {"_raw": raw}
        return rc, parsed, stderr.getvalue()
