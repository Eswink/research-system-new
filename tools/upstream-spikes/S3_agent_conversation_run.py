"""S3: Agent + Conversation 创建、run、事件流（不依赖真实 LLM）。

验证：Agent 构造（LLM 为 mock 配置）、Conversation 创建、注册自定义安全工具、
run 生命周期与事件流。不发起真实网络请求；mock credential。
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from openhands.sdk.agent.agent import Agent
from openhands.sdk.conversation.conversation import Conversation
from openhands.sdk.llm import Message, TextContent
from openhands.sdk.testing import TestLLM
from openhands.sdk.tool.registry import register_tool
from openhands.sdk.tool.spec import Tool
from openhands.sdk.tool.tool import Action, Observation, ToolDefinition, ToolExecutor
from openhands.sdk.workspace.local import LocalWorkspace


class MockEchoAction(Action):
    """Spike 用安全 Action：仅承载文本，无副作用。"""

    text: str = ""


class MockEchoExecutor(ToolExecutor[MockEchoAction, Observation]):
    def __init__(self) -> None:
        super().__init__()

    def __call__(self, action: MockEchoAction, conversation=None) -> Observation:
        return Observation(content=action.text)


class MockEchoTool(ToolDefinition[MockEchoAction, Observation]):
    """安全自定义工具：无副作用，仅返回输入（spike 用）。"""

    @classmethod
    def create(cls, conv_state=None, **params) -> list["MockEchoTool"]:
        return [
            cls(
                name="mock_echo",
                description="Echo input back",
                action_type=MockEchoAction,
                observation_type=None,
                executor=MockEchoExecutor(),
            )
        ]


def main() -> int:
    # 1) 注册自定义工具
    register_tool(MockEchoTool.name, MockEchoTool)
    print(f"tool registered: {MockEchoTool.name}")

    # 2) Agent 构造（TestLLM 脚本化响应，无网络）
    llm = TestLLM.from_messages([
        Message(role="assistant", content=[TextContent(text="Done.")]),
        Message(role="assistant", content=[TextContent(text="All set.")]),
    ])
    try:
        agent = Agent(llm=llm, tools=[Tool(name="mock_echo")])
        print(f"agent constructed: {type(agent).__name__} (tools_map 需 init_state 后访问)")
    except Exception as exc:  # noqa: BLE001
        print(f"Agent 构造失败: {type(exc).__name__}: {exc}")
        return 1

    # 3) Conversation 创建 + run（本地 workspace，无网络）
    tmpdir = Path(tempfile.mkdtemp(prefix="s3-conv-"))
    try:
        workspace = LocalWorkspace(working_dir=str(tmpdir))
        conv = Conversation(
            agent=agent, workspace=workspace, persistence_dir=str(tmpdir / "persist")
        )
        print(f"conversation created: {type(conv).__name__}")
        conv.send_message("Hello from spike (mock).")
        conv.run()
        print(f"run returned: status={conv.state.execution_status}")
        events = list(conv.state.events)
        kinds = sorted({e.__class__.__name__ for e in events})
        print(f"event classes observed: {kinds}")
        conv.close()
        print("S3 PASS")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"S3 FAILED: {type(exc).__name__}: {exc}")
        return 1
    finally:
        import shutil

        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
