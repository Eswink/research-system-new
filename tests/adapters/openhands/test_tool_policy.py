"""Tool + Policy 测试：PolicyWrappedToolExecutor 门禁 + tool_mapping 纯函数。"""

from __future__ import annotations

import pytest

from adapters.fakes import FakePolicyEvaluator
from adapters.openhands.policy_wrapper import (
    PolicyApprovalRequiredError,
    PolicyDeniedError,
    PolicyWrappedToolExecutor,
)
from adapters.openhands.tool_mapping import (
    normalize_mcp_config,
    tools_for_frozen_set,
)
from packages.application.ports.agent_runtime import RuntimeEventKind
from packages.domain.enums import FailureCategory, PolicyDecision


class _RecordingSink:
    def __init__(self) -> None:
        self.events: list[object] = []

    def __call__(self, event: object) -> None:
        self.events.append(event)


def _wrapper(evaluator: FakePolicyEvaluator, sink: _RecordingSink) -> PolicyWrappedToolExecutor:
    return PolicyWrappedToolExecutor(evaluator, actor="agent-a", scope="session-1", emit=sink)


class TestPolicyWrappedToolExecutor:
    def test_allow_executes(self) -> None:
        calls: list[tuple[str, str]] = []

        def fake_execute(tool_name: str, action: object) -> object:
            calls.append((tool_name, str(action)))
            return "ok"

        wrapper = _wrapper(FakePolicyEvaluator(default=PolicyDecision.ALLOW), _RecordingSink())
        result = wrapper.execute(fake_execute, "echo", "payload")
        assert result == "ok"
        assert calls == [("echo", "payload")]

    def test_deny_blocks_before_sdk(self) -> None:
        called: list[str] = []

        def fake_execute(tool_name: str, action: object) -> object:
            called.append(tool_name)
            return "ok"

        wrapper = _wrapper(FakePolicyEvaluator(default=PolicyDecision.DENY), _RecordingSink())
        with pytest.raises(PolicyDeniedError) as excinfo:
            wrapper.execute(fake_execute, "danger_tool", "payload")
        assert excinfo.value.failure_category is FailureCategory.POLICY_DENIED
        assert called == []  # 不得触达 SDK 执行面

    def test_require_approval_blocks_and_emits_event(self) -> None:
        sink = _RecordingSink()
        wrapper = _wrapper(FakePolicyEvaluator(default=PolicyDecision.REQUIRE_APPROVAL), sink)
        with pytest.raises(PolicyApprovalRequiredError):
            wrapper.execute(lambda *_: "unreachable", "sensitive_tool", {})
        assert len(sink.events) == 1
        event = sink.events[0]
        assert event.kind is RuntimeEventKind.APPROVAL_REQUESTED  # type: ignore[attr-defined]
        assert event.payload["tool_name"] == "sensitive_tool"  # type: ignore[attr-defined]

    def test_allow_with_constraints_executes(self) -> None:
        evaluator = FakePolicyEvaluator(default=PolicyDecision.ALLOW_WITH_CONSTRAINTS)
        wrapper = _wrapper(evaluator, _RecordingSink())
        result = wrapper.execute(lambda *_: "ok", "echo", {})
        assert result == "ok"


class TestToolMapping:
    def test_frozen_set_maps_to_tool_specs(self) -> None:
        tools = tools_for_frozen_set(("TerminalTool", "FileEditorTool"))
        assert [tool.name for tool in tools] == ["TerminalTool", "FileEditorTool"]

    def test_empty_frozen_set_produces_empty_tools(self) -> None:
        assert tools_for_frozen_set(()) == []

    def test_mcp_config_normalization(self) -> None:
        normalized = normalize_mcp_config({
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-everything"],
        })
        assert normalized["command"] == "npx"
        assert "transport" not in normalized

    def test_mcp_config_rejects_unknown_keys(self) -> None:
        with pytest.raises(ValueError):
            normalize_mcp_config({"command": "npx", "unknown_key": 1})
