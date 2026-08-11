#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml
from _hook_harness import HookHarness


def _discover_root() -> Path:
    explicit = os.environ.get("CURSOR_FRAMEWORK_ROOT")
    if explicit:
        return Path(explicit).resolve()
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "VERSION").is_file() and (candidate / ".cursor" / "framework.json").is_file():
            return candidate
    raise RuntimeError("Cannot locate repository root (VERSION + .cursor/framework.json)")


ROOT = _discover_root()
PY = sys.executable
os.environ["CURSOR_FRAMEWORK_ROOT"] = str(ROOT)
HARNESS = HookHarness(ROOT)
FAIL: list[str] = []


def hook(name: str, payload: dict) -> dict:
    _, out, _ = HARNESS.call(name, payload)
    return out


def check(condition: bool, message: str) -> None:
    if not condition:
        FAIL.append(message)


for path in (ROOT / ".cursor/evals/cases").glob("*.yaml"):
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for case in data.get("cases") or []:
        if "hook" in case:
            payload = dict(case.get("input") or {})
            file_path = payload.get("file_path")
            if file_path and not Path(file_path).is_absolute():
                payload["file_path"] = str(ROOT / file_path)
            out = hook(case["hook"], payload)
            for key, expected in (case.get("expect") or {}).items():
                check(out.get(key) == expected, f"{case['id']}: {key} mismatch")
        elif "state" in case:
            state_path = ROOT / ".cursor/runtime/evolution_state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(case["state"]), encoding="utf-8")
            out = hook("evolution_gate.py", case.get("stop") or {})
            check(bool(out.get("followup_message")) == case["expect_followup"], f"{case['id']}: followup mismatch")
            if str((case.get("stop") or {}).get("status") or "").lower() in {"error", "aborted"}:
                check(json.loads(state_path.read_text(encoding="utf-8")).get("recovery_required") is True, f"{case['id']}: recovery_required")

obs = ROOT / ".cursor/runtime/observations"
if obs.exists():
    for path in obs.glob("*.jsonl"):
        path.unlink()
hook(
    "failure_observer.py",
    {
        "conversation_id": "eval-private",
        "tool_name": "Shell",
        "error_message": "api_key=TOPSECRET path=/home/alice/private.py syntax error",
        "failure_type": "error",
        "duration": 12,
        "is_interrupt": False,
    },
)
files = list(obs.glob("*.jsonl")) if obs.exists() else []
check(len(files) == 1, "failure observer file count")
if files:
    text = files[0].read_text(encoding="utf-8")
    check("TOPSECRET" not in text and "/home/alice" not in text and "syntax error" not in text, "failure observer persisted raw data")
    rec = json.loads(text.splitlines()[-1])
    check(set(rec) == {"at", "tool_name", "duration_ms", "is_interrupt", "error_class", "error_signature"}, "failure observer schema")
    check(rec.get("error_class") == "CURSOR_ERROR", "failure observer official failure_type mapping")

state = ROOT / ".cursor/runtime/evolution_state.json"
state.unlink(missing_ok=True)


def evo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PY, "-B", str(ROOT / ".cursor/skills/evolve-framework/scripts/framework_evolution.py"), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=8,
        env={
            **os.environ,
            "CURSOR_FRAMEWORK_ROOT": str(ROOT),
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
        },
        cwd=ROOT,
    )


check(evo("start", "--target", "9.9.9", "--goal", "eval").returncode == 0, "evolution start")
check(evo("stage", "RELEASE", "--next-action", "gate").returncode == 0, "stage release")
check(evo("finish").returncode != 0, "evolution passed without deterministic validation")
check(evo("validate", "--status", "PASS", "--evidence-ref", "eval://validators-pass").returncode == 0, "validation record")
check(evo("stage", "RELEASE", "--next-action", "finish").returncode == 0, "restage release")
check(evo("finish").returncode == 0, "evolution failed after validation")
final = json.loads(state.read_text(encoding="utf-8"))
check(final.get("release_gate") == "PASS" and final.get("active") is False, "evolution final state")
state.unlink(missing_ok=True)
for path in obs.glob("*.jsonl") if obs.exists() else []:
    path.unlink()

if FAIL:
    print("FRAMEWORK EVAL FAILED")
    for item in FAIL:
        print("-", item)
    raise SystemExit(1)
print("FRAMEWORK EVAL PASS")
