#!/usr/bin/env python3
from __future__ import annotations

import hashlib
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
        if (candidate / "VERSION").is_file() and (
            candidate / ".cursor" / "framework.json"
        ).is_file():
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


def safe_id(value: object) -> str:
    return hashlib.sha256(str(value or "unknown").encode("utf-8")).hexdigest()[:20]


def seed_hook_case(case: dict) -> dict:
    """Seed observations/distillation state for a hook eval case; returns cleanup callable."""
    payload = dict(case.get("input") or {})
    seed = case.get("seed") or {}
    obs_dir = ROOT / ".cursor/runtime/observations"
    dist_dir = ROOT / ".cursor/runtime/distillation"
    cid = safe_id(payload.get("conversation_id"))
    current = obs_dir / f"{cid}.jsonl"
    marker = dist_dir / f"{cid}.prompted"
    current.unlink(missing_ok=True)
    marker.unlink(missing_ok=True)
    for item in seed.get("observations") or []:
        obs_dir.mkdir(parents=True, exist_ok=True)
        with current.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    for idx, item in enumerate(seed.get("history") or []):
        hist = obs_dir / f"{safe_id(payload.get('conversation_id') + '-h' + str(idx))}.jsonl"
        hist.unlink(missing_ok=True)
        obs_dir.mkdir(parents=True, exist_ok=True)
        with hist.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    if seed.get("prompted"):
        dist_dir.mkdir(parents=True, exist_ok=True)
        marker.write_text("{}", encoding="utf-8")
    return {"current": current, "marker": marker, "history_count": len(seed.get("history") or [])}


def cleanup_hook_case(payload: dict, seeded: dict) -> None:
    seeded["current"].unlink(missing_ok=True)
    seeded["marker"].unlink(missing_ok=True)
    for idx in range(seeded["history_count"]):
        hist = (
            ROOT
            / ".cursor/runtime/observations"
            / f"{safe_id(payload.get('conversation_id') + '-h' + str(idx))}.jsonl"
        )
        hist.unlink(missing_ok=True)


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
            seeded = seed_hook_case(case)
            try:
                out = hook(case["hook"], payload)
            finally:
                cleanup_hook_case(payload, seeded)
            if "expect_followup" in case:
                check(
                    bool(out.get("followup_message")) == case["expect_followup"],
                    f"{case['id']}: followup mismatch",
                )
            for key, expected in (case.get("expect") or {}).items():
                check(out.get(key) == expected, f"{case['id']}: {key} mismatch")
        elif "state" in case:
            state_path = ROOT / ".cursor/runtime/evolution_state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(case["state"]), encoding="utf-8")
            out = hook("evolution_gate.py", case.get("stop") or {})
            check(
                bool(out.get("followup_message")) == case["expect_followup"],
                f"{case['id']}: followup mismatch",
            )
            if str((case.get("stop") or {}).get("status") or "").lower() in {"error", "aborted"}:
                check(
                    json.loads(state_path.read_text(encoding="utf-8")).get("recovery_required")
                    is True,
                    f"{case['id']}: recovery_required",
                )

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
    check(
        "TOPSECRET" not in text and "/home/alice" not in text and "syntax error" not in text,
        "failure observer persisted raw data",
    )
    rec = json.loads(text.splitlines()[-1])
    check(
        set(rec)
        == {"at", "tool_name", "duration_ms", "is_interrupt", "error_class", "error_signature"},
        "failure observer schema",
    )
    check(
        rec.get("error_class") == "CURSOR_ERROR", "failure observer official failure_type mapping"
    )

state = ROOT / ".cursor/runtime/evolution_state.json"
state.unlink(missing_ok=True)


def evo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            PY,
            "-B",
            str(ROOT / ".cursor/skills/evolve-framework/scripts/framework_evolution.py"),
            *args,
        ],
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
check(
    evo("validate", "--status", "PASS", "--evidence-ref", "eval://validators-pass").returncode == 0,
    "validation record",
)
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
