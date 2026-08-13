"""S7 Executable Spike：mock OpenAI-compatible 端点端到端链路（仓库内测试）。

User test relay（本地 threading HTTP 服务器，无真实网络/凭据）
→ ModelDefinition → build_llm（三要素装配）→ OpenHands Agent → Conversation
→ safe echo tool → isolated Workspace → RuntimeEvents → AgentSessionResult。

验证：LLM Relay 三要素真正到达 SDK/litellm 请求层；事件流归一化；
secret 不出现在任何记录；结果收敛 SUCCEEDED。
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import pytest
from openhands.sdk.tool.registry import register_tool
from openhands.sdk.tool.schema import Action, Observation
from openhands.sdk.tool.tool import ToolDefinition, ToolExecutor

from adapters.fakes import FakeCredentialResolver, FakePolicyEvaluator
from adapters.openhands.llm_factory import build_llm
from adapters.openhands.runtime_adapter import OpenHandsRuntimeAdapter
from adapters.openhands.session_types import AdapterDependencies
from packages.application.ports.agent_runtime import (
    AgentSessionSpec,
    RuntimeEventKind,
)
from packages.application.ports.credential_resolver import SecretValue
from packages.domain.enums import PolicyDecision
from packages.domain.models import LLMEndpoint, ModelDefinition
from packages.domain.session_state import AgentSessionState
from tests.contracts.fixtures import agent_spec, research_task, role_definition, task_contract


class _MockEchoAction(Action):
    """S7 用安全 Action 载体。"""

    text: str = ""


class _MockEchoExecutor(ToolExecutor[Any, Observation]):
    def __call__(self, action: Any, conversation: Any = None) -> Observation:
        return Observation.from_text(str(getattr(action, "text", "echo-ok")))


class MockEchoTool(ToolDefinition[Any, Observation]):
    """安全自定义工具：无副作用，仅回显输入；类名自动推导 name=mock_echo（S3 模式）。"""

    @classmethod
    def create(cls, conv_state: Any = None, **params: Any) -> list["MockEchoTool"]:
        tool = cls(
            description="Echo input back",
            action_type=_MockEchoAction,
            observation_type=None,
            executor=_MockEchoExecutor(),
        )
        # 实例 name 属性在 __init_subclass__ 后由类名推导为 mock_echo
        object.__setattr__(tool, "name", "mock_echo")
        return [tool]


class _RelayHandler(BaseHTTPRequestHandler):
    """最小 OpenAI-compatible chat completions mock。"""

    requests: list[dict[str, Any]] = []

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        _RelayHandler.requests.append(body)
        response = {
            "id": "chatcmpl-mock-1",
            "object": "chat.completion",
            "created": 1755000000,
            "model": body.get("model", "relay-model"),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Done.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15},
        }
        payload = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return


@pytest.fixture(scope="module")
def mock_relay() -> Iterator[str]:
    _RelayHandler.requests.clear()
    server = HTTPServer(("127.0.0.1", 0), _RelayHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}/v1"
    yield base_url
    server.shutdown()
    server.server_close()


def _endpoint(base_url: str) -> LLMEndpoint:
    return LLMEndpoint(
        id="relay-1",
        name="s7 mock relay",
        protocol="OPENAI_COMPATIBLE",
        base_url=base_url,
        credential_ref="S7_RELAY_KEY",
        request_timeout_seconds=10,
        max_retries=0,
    )


def _spec() -> AgentSessionSpec:
    return AgentSessionSpec(
        task_id=research_task().id,
        task_contract=task_contract(),
        role=role_definition(),
        agent=agent_spec(),
        frozen_tool_set=("mock_echo",),
    )


def test_s7_end_to_end_spike(mock_relay: str, tmp_path: Path) -> None:
    # 1) 注册 safe echo tool（S3 模式；进程级，幂等）
    register_tool(MockEchoTool.name, MockEchoTool)

    # 2) LLM Relay：三要素 → OpenHands LLM（真实 HTTP 走本地 mock）
    endpoint = _endpoint(mock_relay)
    model = ModelDefinition(id="m-1", endpoint_id="relay-1", model_name="relay-model")
    credential = SecretValue("sk-s7-secret-000")
    llm = build_llm(endpoint, model, credential, max_output_tokens=512)

    # 3) Agent + Conversation 装配（adapter 组合）
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir(exist_ok=True)
    deps = AdapterDependencies(
        credential_resolver=FakeCredentialResolver({"S7_RELAY_KEY": "sk-s7-secret-000"}),
        policy_evaluator=FakePolicyEvaluator(default=PolicyDecision.ALLOW),
        build_llm=lambda spec: llm,
        build_workspace=lambda lease, session_id: _local_workspace(workspace_root),
        register_tools=lambda frozen: None,
        persistence_dir=str(tmp_path / "persist"),
    )
    runtime = OpenHandsRuntimeAdapter(deps)

    # 4) create → run → result
    handle = runtime.create_session(_spec())
    result = runtime.run(handle.session_id)
    assert result.status == AgentSessionState.State.SUCCEEDED

    # 5) 事件归一化：SESSION_CREATED → (消息/工具事件) → SESSION_SUCCEEDED
    kinds = [event.kind for event in runtime.stream_events(handle.session_id)]
    assert kinds[0] is RuntimeEventKind.SESSION_CREATED
    assert kinds[-1] is RuntimeEventKind.SESSION_SUCCEEDED

    # 6) 请求确实到达 mock relay：model 透传（openai/ 前缀为 runtime 变换，
    #    请求体 model 保留用户配置的 relay-model；litellm 用 custom provider 路由）
    assert _RelayHandler.requests, "mock relay must have received completion requests"
    last_request = _RelayHandler.requests[-1]
    assert last_request["model"] == "openai/relay-model" or "relay-model" in last_request["model"]

    # 7) Secret 不进任何记录
    joined = json.dumps(runtime.calls, ensure_ascii=False)
    assert "sk-s7-secret-000" not in joined
    assert "sk-s7-secret-000" not in str(result)
    assert "sk-s7-secret-000" not in repr(llm)
    runtime.close()


def _local_workspace(workspace_root: Path) -> Any:
    from openhands.sdk.workspace.local import LocalWorkspace

    return LocalWorkspace(working_dir=str(workspace_root))
