from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(
    os.environ.get("CURSOR_FRAMEWORK_ROOT")
    or os.environ.get("CURSOR_PROJECT_DIR")
    or Path(__file__).resolve().parents[2]
).resolve()
RUNTIME = ROOT / ".cursor" / "runtime"
SAFE_CREDENTIAL_EXAMPLE_NAMES = frozenset({".env.example", ".env.sample", ".env.template"})
SAFE_CREDENTIAL_EXAMPLE_RE = re.compile(r"(?i)\.env\.(?:example|sample|template)\b")
SENSITIVE_REFERENCE_RE = re.compile(
    r"(?i)(?:^|[\s'\"=:/\\();,])(?:"
    r"\.env[.A-Za-z0-9_-]*|[^\s'\";|()]+\.env|"
    r"credentials?\.json|secrets?\.json|"
    r"[^\s'\";|()]+\.(?:pem|key|p12|pfx)|"
    r"\.ssh[/\\](?:id_[^\s'\";|()]+|authorized_keys)|"
    r"\.aws[/\\]credentials|"
    r"\.config[/\\]gcloud[/\\]application_default_credentials\.json"
    r")(?:$|[\s'\";&|),])"
)


def is_sensitive_path(value: Any) -> bool:
    normalized = str(value or "").strip().strip("'\"").replace("\\", "/")
    lowered = normalized.casefold().rstrip("/")
    basename = lowered.rsplit("/", 1)[-1]
    if basename in SAFE_CREDENTIAL_EXAMPLE_NAMES:
        return False
    if basename.startswith(".env") or basename.endswith(".env"):
        return True
    if basename in {"credential.json", "credentials.json", "secret.json", "secrets.json"}:
        return True
    if basename.endswith((".pem", ".key", ".p12", ".pfx")):
        return True
    return bool(
        re.search(r"(?:^|/)\.ssh/(?:id_[^/]+|authorized_keys)$", lowered)
        or lowered.endswith("/.aws/credentials")
        or lowered.endswith("/.config/gcloud/application_default_credentials.json")
    )


def contains_sensitive_reference(value: Any) -> bool:
    scrubbed = SAFE_CREDENTIAL_EXAMPLE_RE.sub("", str(value or ""))
    return SENSITIVE_REFERENCE_RE.search(scrubbed) is not None


def read_event_result() -> tuple[dict[str, Any] | None, str | None]:
    binary_stream = getattr(sys.stdin, "buffer", None)
    try:
        if binary_stream is not None:
            raw = binary_stream.read().decode("utf-8-sig")
        else:
            raw = sys.stdin.read().lstrip("\ufeff")
    except UnicodeDecodeError as exc:
        return None, f"invalid UTF-8: {exc}"
    if not raw.strip():
        return None, "empty input"
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        return None, (f"invalid JSON: {exc.msg}; pos={exc.pos}; chars={len(raw)}; sha256={digest}")
    if not isinstance(value, dict):
        return None, "hook input must be a JSON object"
    return value, None


def read_event() -> dict[str, Any]:
    event, _ = read_event_result()
    return event or {}


def require_event(*required_fields: str) -> dict[str, Any] | None:
    event, error = read_event_result()
    if error is not None:
        deny(
            "安全门禁无法解析 Cursor Hook 输入，已按 fail-closed 拒绝操作。",
            f"修复 Hook JSON 协议后重试；原因：{error}",
        )
        return None
    assert event is not None
    missing = [field for field in required_fields if event.get(field) in (None, "")]
    if missing:
        deny(
            "安全门禁缺少必填 Hook 字段，已按 fail-closed 拒绝操作。",
            f"缺少字段：{', '.join(missing)}",
        )
        return None
    return event


def emit(payload: dict[str, Any] | None = None) -> None:
    serialized = json.dumps(payload or {}, ensure_ascii=False) + "\n"
    binary_stream = getattr(sys.stdout, "buffer", None)
    if binary_stream is not None:
        binary_stream.write(serialized.encode("utf-8"))
        binary_stream.flush()
        return
    sys.stdout.write(serialized)
    sys.stdout.flush()


def safe_id(value: Any) -> str:
    return hashlib.sha256(str(value or "unknown").encode("utf-8")).hexdigest()[:20]


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def load_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def deny(user_message: str, agent_message: str | None = None) -> None:
    payload = {"permission": "deny", "user_message": user_message}
    if agent_message:
        payload["agent_message"] = agent_message
    emit(payload)


def ask(user_message: str, agent_message: str | None = None) -> None:
    payload = {"permission": "ask", "user_message": user_message}
    if agent_message:
        payload["agent_message"] = agent_message
    emit(payload)


def allow() -> None:
    emit({"permission": "allow"})
