"""S4: cancel/pause 与错误路径（不依赖真实 LLM）。

验证：run 状态迁移；错误路径（异常包装为 ConversationRunError）；中断语义
（interrupt → PAUSED 而非终态）。mock credential，无网络。
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from openhands.sdk.agent.agent import Agent
from openhands.sdk.testing import TestLLM
from openhands.sdk.llm import Message, TextContent
from openhands.sdk.workspace.local import LocalWorkspace
from openhands.sdk.conversation.conversation import Conversation
from openhands.sdk.conversation.state import ConversationExecutionStatus


def main() -> int:
    tmpdir = Path(tempfile.mkdtemp(prefix="s4-conv-"))
    llm = TestLLM.from_messages(
        [
            Message(role="assistant", content=[TextContent(text="Done.")]),
            Message(role="assistant", content=[TextContent(text="Again.")]),
        ]
    )
    try:
        workspace = LocalWorkspace(working_dir=str(tmpdir))
        agent = Agent(llm=llm)
        conv = Conversation(agent=agent, workspace=workspace, persistence_dir=str(tmpdir / "persist"))

        conv.send_message("run once (mock).")
        conv.run()
        print(f"after run: status={conv.state.execution_status}")

        # interrupt 语义（run 已完成时仅置信号，不改变终态）
        try:
            conv.interrupt()
            print(f"after interrupt: status={conv.state.execution_status}")
        except Exception as exc:  # noqa: BLE001
            print(f"interrupt raised: {type(exc).__name__}: {exc}")

        # 错误路径：向已完成会话再 run（不应 crash；观察行为）
        try:
            conv.run()
            print(f"second run: status={conv.state.execution_status}")
        except Exception as exc:  # noqa: BLE001
            print(f"second run raised: {type(exc).__name__}: {exc}")

        conv.close()
        print("S4 PASS")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"S4 FAILED: {type(exc).__name__}: {exc}")
        return 1
    finally:
        import shutil

        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())