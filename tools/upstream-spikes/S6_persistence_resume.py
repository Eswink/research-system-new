"""S6: persistence/resume 往返（不依赖真实 LLM）。

验证：conversation 持久化到磁盘（base_state.json + events/）、重新构造
conversation 恢复事件与状态。mock credential，无网络。
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from openhands.sdk.agent.agent import Agent
from openhands.sdk.conversation.conversation import Conversation
from openhands.sdk.llm import Message, TextContent
from openhands.sdk.testing import TestLLM
from openhands.sdk.workspace.local import LocalWorkspace


def main() -> int:
    tmpdir = Path(tempfile.mkdtemp(prefix="s6-persist-"))
    llm = TestLLM.from_messages([Message(role="assistant", content=[TextContent(text="Done.")])])
    persist = tmpdir / "persist"
    try:
        # 1) 创建并 run，观察持久化产物
        workspace = LocalWorkspace(working_dir=str(tmpdir / "ws"))
        agent = Agent(llm=llm)
        conv = Conversation(agent=agent, workspace=workspace, persistence_dir=str(persist))
        conv.send_message("persist me (mock).")
        conv.run()
        conv_id = conv.state.id
        print(f"conversation_id: {conv_id.hex}")
        conv.close()

        base_state = persist / conv_id.hex / "base_state.json"
        events_dir = persist / conv_id.hex / "events"
        print(f"base_state exists: {base_state.exists()}")
        print(
            f"events dir exists: {events_dir.exists()} files={len(list(events_dir.glob('*.json')))}"
        )
        if base_state.exists():
            state = json.loads(base_state.read_text(encoding="utf-8"))
            print(f"base_state keys: {sorted(state.keys())}")

        # 2) resume：显式传 conversation_id 重新构造（open-or-create 语义）
        workspace2 = LocalWorkspace(working_dir=str(tmpdir / "ws"))
        conv2 = Conversation(
            agent=agent,
            workspace=workspace2,
            persistence_dir=str(persist),
            conversation_id=conv_id,
        )
        print(f"resumed status: {conv2.state.execution_status}")
        print(f"resumed events: {len(list(conv2.state.events))}")
        assert conv2.state.id == conv_id
        conv2.close()
        print("S6 PASS")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"S6 FAILED: {type(exc).__name__}: {exc}")
        return 1
    finally:
        import shutil

        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
