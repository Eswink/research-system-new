#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone

from common import RUNTIME, atomic_json, emit, load_json, read_event

STATE = RUNTIME / "evolution_state.json"


def main() -> int:
    event = read_event()
    state = load_json(STATE, {}) or {}
    if not state.get("active"):
        emit({})
        return 0
    if state.get("release_gate") == "PASS":
        emit({})
        return 0

    status = str(event.get("status") or "").lower()
    if status and status != "completed":
        state["recovery_required"] = True
        state["last_stop_status"] = status
        state["next_action"] = "人工检查异常会话并显式恢复 evolution；禁止 Stop Hook 自动续跑。"
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        atomic_json(STATE, state)
        emit({})
        return 0

    if int(event.get("loop_count") or 0) >= int(state.get("max_followups") or 5):
        emit({})
        return 0

    next_action = state.get("next_action") or "继续当前 evolution stage，并运行 replay/validators。"
    emit({"followup_message": f"继续已授权的 Framework {state.get('target_version')} 自我迭代：{next_action}"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
