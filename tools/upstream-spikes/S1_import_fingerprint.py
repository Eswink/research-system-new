"""S1: import + 版本指纹。

验证：SDK 可导入、版本号、核心符号存在。mock credential，无外部副作用。
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def main() -> int:
    print(f"python: {sys.version}")
    mods = [
        "openhands.sdk.agent",
        "openhands.sdk.conversation",
        "openhands.sdk.llm",
        "openhands.sdk.tool",
        "openhands.sdk.workspace",
        "openhands.sdk.event",
        "openhands.sdk.mcp",
    ]
    for name in mods:
        mod = importlib.import_module(name)
        print(f"import OK: {name} -> {Path(mod.__file__).resolve() if mod.__file__ else 'n/a'}")

    from openhands.sdk.conversation.state import ConversationExecutionStatus
    from openhands.sdk.event.base import Event
    from openhands.sdk.llm.llm import LLM

    print(f"ConversationExecutionStatus: {[s for s in dir(ConversationExecutionStatus) if not s.startswith('_')]}")
    print(f"Event bases: {[c.__name__ for c in Event.__mro__]}")
    print(f"LLM fields: {list(LLM.model_fields.keys())}")

    # 版本指纹
    try:
        import openhands.sdk

        print(f"openhands.sdk module: {openhands.sdk.__file__}")
    except Exception as exc:  # noqa: BLE001
        print(f"openhands.sdk package introspection failed: {exc}")

    print("S1 PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())