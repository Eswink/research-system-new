#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

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
failures: list[str] = []


def run(script: str, payload: dict):
    return HARNESS.call(Path(script).name, payload)


def run_subprocess_raw(script: str, raw_input: bytes) -> tuple[int, dict, str, bytes]:
    env = os.environ.copy()
    env["CURSOR_FRAMEWORK_ROOT"] = str(ROOT)
    cp = subprocess.run(
        [PY, "-B", str(ROOT / script)],
        input=raw_input,
        capture_output=True,
        env=env,
        timeout=8,
        cwd=ROOT,
    )
    stderr = cp.stderr.decode("utf-8", errors="replace")
    try:
        stdout = cp.stdout.decode("utf-8")
        out = json.loads(stdout.strip() or "{}")
        if not isinstance(out, dict):
            out = {"_raw": stdout}
    except (UnicodeDecodeError, json.JSONDecodeError):
        out = {"_raw_hex": cp.stdout.hex()}
    return cp.returncode, out, stderr, cp.stdout


def run_subprocess(script: str, payload: dict, *, with_bom: bool = False) -> tuple[int, dict, str, bytes]:
    serialized = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    raw_input = (b"\xef\xbb\xbf" + serialized) if with_bom else serialized
    return run_subprocess_raw(script, raw_input)


def expect(label: str, cond: bool, detail="") -> None:
    if not cond:
        failures.append(f"{label}: {detail}")


# Every fail-closed guard must reject malformed transport input with valid UTF-8 JSON.
for script in (
    ".cursor/hooks/secret_guard.py",
    ".cursor/hooks/shell_guard.py",
    ".cursor/hooks/mcp_guard.py",
    ".cursor/hooks/subagent_guard.py",
    ".cursor/hooks/subagent_pretool_guard.py",
):
    for label, raw_input in (
        ("empty", b""),
        ("malformed", b'{"incomplete":'),
        ("non-object", b"[]"),
        ("invalid-utf8", b"\xff"),
    ):
        rc, out, stderr, raw_stdout = run_subprocess_raw(script, raw_input)
        case = f"{Path(script).name} {label}"
        expect(case + " rc", rc == 0, stderr)
        expect(case + " denied", out.get("permission") == "deny", {"out": out, "stdout_hex": raw_stdout.hex()})

# Cursor 3.14.7 on Windows prefixes hook stdin with an UTF-8 BOM. The protocol
# layer must consume it and always emit strict UTF-8, independent of system GBK.
for label, script, payload, expected in (
    (
        "BOM secret path",
        ".cursor/hooks/secret_guard.py",
        {"tool_name": "Read", "tool_input": {"path": r"C:\workspace\credentials.json"}},
        "deny",
    ),
    ("BOM safe shell", ".cursor/hooks/shell_guard.py", {"command": "git status --short"}, "allow"),
    (
        "BOM PowerShell root delete",
        ".cursor/hooks/shell_guard.py",
        {"command": r"Remove-Item -LiteralPath C:\ -Recurse -Force"},
        "deny",
    ),
    (
        "BOM MCP approval",
        ".cursor/hooks/mcp_guard.py",
        {"tool_name": "papers.search", "tool_input": {"query": "智能体系统"}},
        "ask",
    ),
):
    rc, out, stderr, raw_stdout = run_subprocess(script, payload, with_bom=True)
    expect(label + " rc", rc == 0, stderr)
    expect(label + " output", out.get("permission") == expected, {"out": out, "stdout_hex": raw_stdout.hex()})
    try:
        raw_stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        failures.append(f"{label} stdout is not UTF-8: {exc}")


# Secret read.
_, out, _ = run(".cursor/hooks/secret_guard.py", {"file_path": str(ROOT / ".env.local")})
expect("secret .env denied", out.get("permission") == "deny", out)
_, out, _ = run(".cursor/hooks/secret_guard.py", {"file_path": str(ROOT / ".env.example")})
expect(".env.example allowed", out.get("permission") == "allow", out)

# Shell guard.
for label, command, expected in [
    ("git push asks", "git push origin main", "ask"),
    ("git add -A denied", "git add -A", "deny"),
    ("hard reset denied", "git reset --hard HEAD~1", "deny"),
    ("secret via python denied", "python -c \"open('.env.local').read()\"", "deny"),
    ("env example allowed", "python tools/check.py .env.example", "allow"),
    ("safe status allowed", "git status --short", "allow"),
]:
    _, out, _ = run(".cursor/hooks/shell_guard.py", {"command": command})
    expect(label, out.get("permission") == expected, out)

# Session context.
_, out, _ = run(".cursor/hooks/session_context.py", {"hook_event_name": "sessionStart", "session_id": "test"})
expected_version = json.loads((ROOT / ".cursor/framework.json").read_text(encoding="utf-8"))["framework_version"]
expect("session version context", expected_version in str(out.get("additional_context", "")), out)
expect(
    "session no baseline residue",
    "基线 unknown" not in str(out.get("additional_context", "")) and "RESEARCH_OS_BASELINE" not in str(out.get("env", {})),
    out,
)
expect("session unified version env", (out.get("env") or {}).get("RESEARCH_OS_PROJECT_VERSION") == expected_version, out)

# Subagent per-wave active limit; no cumulative task cap.
bucket = ROOT / ".cursor/runtime/subagents"
if bucket.exists():
    shutil.rmtree(bucket)
for i in range(1, 4):
    _, out, _ = run(
        ".cursor/hooks/subagent_guard.py",
        {
            "conversation_id": "eval-parent",
            "parent_conversation_id": "eval-parent",
            "subagent_id": f"sub-{i}",
            "subagent_type": "generalPurpose",
            "task": f"task-{i}",
        },
    )
    expect(f"subagent {i} allow", out.get("permission") == "allow", out)
_, out, _ = run(
    ".cursor/hooks/subagent_guard.py",
    {
        "conversation_id": "eval-parent",
        "parent_conversation_id": "eval-parent",
        "subagent_id": "sub-4",
        "subagent_type": "generalPurpose",
        "task": "task-4",
    },
)
expect("fourth concurrent subagent denied", out.get("permission") == "deny", out)
_, out, _ = run(".cursor/hooks/subagent_pretool_guard.py", {"conversation_id": "eval-parent", "tool_name": "Task", "tool_input": {}})
expect("preToolUse fourth concurrent Task denied", out.get("permission") == "deny", out)
_, out, _ = run(
    ".cursor/hooks/subagent_stop.py",
    {
        "conversation_id": "eval-parent",
        "subagent_type": "generalPurpose",
        "status": "completed",
        "task": "task-1",
        "description": "eval",
        "summary": "done",
        "duration_ms": 10,
        "message_count": 1,
        "tool_call_count": 0,
        "loop_count": 0,
        "modified_files": [],
        "agent_transcript_path": None,
    },
)
expect("subagentStop schema emits no permission", out == {}, out)
_, out, _ = run(".cursor/hooks/subagent_pretool_guard.py", {"conversation_id": "eval-parent", "tool_name": "Task", "tool_input": {}})
expect("preToolUse Task allowed with available slot", out.get("permission") == "allow", out)
_, out, _ = run(
    ".cursor/hooks/subagent_guard.py",
    {
        "conversation_id": "eval-parent",
        "parent_conversation_id": "eval-parent",
        "subagent_id": "sub-4",
        "subagent_type": "generalPurpose",
        "task": "task-4",
    },
)
expect("new-wave subagent allowed after slot released", out.get("permission") == "allow", out)
if bucket.exists():
    shutil.rmtree(bucket)

# Official postToolUseFailure payload + privacy.
conversation_id = "conv-official-failure"
filename = hashlib.sha256(conversation_id.encode("utf-8")).hexdigest()[:20] + ".jsonl"
target = ROOT / ".cursor/runtime/observations" / filename
target.unlink(missing_ok=True)
payload = {
    "conversation_id": conversation_id,
    "tool_name": "Shell",
    "duration": 42,
    "failure_type": "permission_denied",
    "error_message": "permission denied: secret detail must not persist",
    "is_interrupt": False,
}
rc, out, stderr = run(".cursor/hooks/failure_observer.py", payload)
expect("official failure hook returncode", rc == 0, stderr)
expect("postToolUseFailure emits no output fields", out == {}, out)
expect("official failure observation created", target.exists(), str(target))
if target.exists():
    rec = json.loads(target.read_text(encoding="utf-8").splitlines()[-1])
    expect("official failure_type mapped", rec.get("error_class") == "CURSOR_PERMISSION_DENIED", rec)
    expect("official is_interrupt mapped", rec.get("is_interrupt") is False, rec)
    persisted = json.dumps(rec, ensure_ascii=False)
    expect("failure observer redacts raw error", "secret detail" not in persisted and "permission denied" not in persisted, persisted)
    expect("failure observer schema", set(rec) == {"at", "tool_name", "duration_ms", "is_interrupt", "error_class", "error_signature"}, rec)
    target.unlink(missing_ok=True)

# MCP policy: secret material/path denied; ordinary external call requires explicit approval.
def mcp(payload: dict) -> dict:
    rc, out, stderr = run(".cursor/hooks/mcp_guard.py", payload)
    expect("mcp guard returncode", rc == 0, stderr)
    return out

safe = mcp({"tool_name": "papers.search", "tool_input": {"query": "agent systems"}, "url": "https://example.test/mcp"})
expect("safe MCP input requires approval", safe.get("permission") == "ask", safe)
denied = mcp({"tool_name": "fs.read", "tool_input": {"path": "/home/alice/.ssh/id_ed25519"}})
expect("credential path MCP input denied", denied.get("permission") == "deny", denied)
denied_secret = mcp({"tool_name": "remote.call", "tool_input": {"token": "sk-" + ("x" * 28)}})
expect("credential material MCP input denied", denied_secret.get("permission") == "deny", denied_secret)

# Stop audit hook must emit schema-valid JSON and persist no raw machine path.
audit_dir = ROOT / ".cursor/runtime/git-audit"
if audit_dir.exists():
    shutil.rmtree(audit_dir)
_, out, stderr = run(
    ".cursor/hooks/snapshot_commit.py",
    {"hook_event_name": "stop", "conversation_id": "eval-stop", "status": "completed"},
)
expect("stop snapshot emits valid empty JSON", out == {}, {"out": out, "stderr": stderr})
audits = list(audit_dir.glob("*.json")) if audit_dir.exists() else []
expect("stop snapshot creates sanitized audit", len(audits) == 1, audits)
if audits:
    record = json.loads(audits[0].read_text(encoding="utf-8"))
    expect("snapshot audit schema", set(record) == {"schema_version", "conversation", "status", "counts", "path_digests"}, record)
    expect("snapshot audit contains no repository path", str(ROOT) not in json.dumps(record, ensure_ascii=False), record)
if audit_dir.exists():
    shutil.rmtree(audit_dir)

# A few true subprocess smokes keep the Cursor command-hook JSON/stdin/stdout contract covered.
for label, script, payload, predicate in [
    ("subprocess secret guard", ".cursor/hooks/secret_guard.py", {"file_path": str(ROOT / ".env.local")}, lambda x: x.get("permission") == "deny"),
    ("subprocess mcp ask", ".cursor/hooks/mcp_guard.py", {"tool_name": "papers.search", "tool_input": {"query": "x"}}, lambda x: x.get("permission") == "ask"),
    ("subprocess subagentStop schema", ".cursor/hooks/subagent_stop.py", {"subagent_type": "generalPurpose", "status": "completed", "task": "none"}, lambda x: x == {}),
]:
    rc, out, stderr, raw_stdout = run_subprocess(script, payload)
    expect(label + " rc", rc == 0, stderr)
    expect(label + " output", predicate(out), {"out": out, "stdout_hex": raw_stdout.hex()})

if failures:
    print("HOOK EVAL FAILED")
    for failure in failures:
        print("-", failure)
    raise SystemExit(1)
print("HOOK EVAL PASS: in-process matrix + subprocess JSON protocol smokes")
