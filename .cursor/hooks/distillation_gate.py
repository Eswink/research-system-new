#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone

from common import RUNTIME, atomic_json, emit, read_event, safe_id


def _session_failures(cid: str) -> int:
    path = RUNTIME / "observations" / f"{cid}.jsonl"
    if not path.is_file():
        return 0
    try:
        return len(path.read_text(encoding="utf-8").splitlines())
    except OSError:
        return 0


def _repeated_signatures() -> list[str]:
    counts: dict[str, int] = {}
    for path in sorted((RUNTIME / "observations").glob("*.jsonl")) if (RUNTIME / "observations").is_dir() else []:
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            signature = str(record.get("error_signature") or "")
            if signature:
                counts[signature] = counts.get(signature, 0) + 1
    return [signature for signature, count in counts.items() if count >= 2]


def _prompted(cid: str) -> bool:
    return (RUNTIME / "distillation" / f"{cid}.prompted").is_file()


def _mark_prompted(cid: str) -> None:
    target = RUNTIME / "distillation" / f"{cid}.prompted"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"at": datetime.now(timezone.utc).isoformat(), "cid": cid}
    atomic_json(target, payload)


def main() -> int:
    event = read_event()
    status = str(event.get("status") or "").lower()
    if status and status != "completed":
        emit({})
        return 0
    if int(event.get("loop_count") or 0) >= 1:
        emit({})
        return 0

    cid = safe_id(event.get("conversation_id"))
    failures = _session_failures(cid)
    if failures == 0 or _prompted(cid):
        emit({})
        return 0

    _mark_prompted(cid)
    repeated = _repeated_signatures()
    parts = [f"本会话有 {failures} 次工具失败；若已形成稳定解法，可运行 capture-experience 沉淀到 .cursor/experience/。"]
    if repeated:
        parts.append(f"有 {len(repeated)} 类失败签名已在 ≥2 次会话中出现，建议 capture-learning 生成 LEARN 提案。")
    emit({"followup_message": " ".join(parts)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())