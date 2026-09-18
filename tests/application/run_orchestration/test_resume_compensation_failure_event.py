"""补偿失败留痕的形状与同源判据（GOAL-20260918-006 cycle 6 = EC-06 (b)）。

EC-06 选 (b)：把「哪一步炸的仍需读事件链上下文」登记为一等边界，**并**把守护线程补偿失败的
静默降级做成读面可见。本文件钉住后者：

1. `publish_compensation_failure` 发的是 `run.resume_compensation_failed`，payload 键集合与
   它在 `run_terminals` docstring 里**写明的键集合**逐字一致（少写/多写都红——文本与实现互钉；
   这正是 cycle 5 那套「点名必须可机器校验」的同一手法）；
2. `canonical_state` 如实回答「补偿失败时 run 还停在哪」，**不是**伪造的 `PAUSED`；
3. 同源：`docs/architecture/EVENT_MODEL.md` 的词表列出该事件、`docs/api/CONTROL_PLANE_API.md`
   写明读法，两份文档都写出同一组 payload 键，并都写明「不含任务级归因」这条一等边界。
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from packages.application.run_orchestration import run_terminals
from packages.domain.events import EventType
from packages.domain.run_state import ResearchRunState

_ROOT = Path(__file__).resolve().parents[3]
_KEY_MARKER = "payload 键（判据按这一行核对）："
_EVENT = "run.resume_compensation_failed"
_DOCS = ("docs/architecture/EVENT_MODEL.md", "docs/api/CONTROL_PLANE_API.md")
_BACKTICKED = re.compile(r"`([^`]+)`")
_RUN_ID = "d4e5f607-1829-4a3b-8c4d-5e6f708192a3"


def _docstring() -> str:
    source = Path(run_terminals.__file__).read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name == "publish_compensation_failure":
            return ast.get_docstring(node) or ""
    raise AssertionError("run_terminals 里找不到 publish_compensation_failure")


def _declared_keys() -> set[str]:
    """契约文本里写明的 payload 键集合（只认标记行——散落的词不算声明）。"""
    for line in _docstring().splitlines():
        if _KEY_MARKER in line:
            declared = _BACKTICKED.findall(line)
            assert declared, f"声明行里没有键：{line}"
            return set(declared)
    raise AssertionError(f"docstring 里找不到声明行：{_KEY_MARKER}")


class _RecordingPublish:
    """与真实 publish 同形的记录器（只记录，不落库）。"""

    def __init__(self) -> None:
        self.calls: list[tuple[Any, dict[str, Any], dict[str, Any]]] = []

    def __call__(self, event_type: Any, payload: dict[str, Any], **kwargs: Any) -> None:
        self.calls.append((event_type, dict(payload), kwargs))


def test_the_event_is_the_declared_one_and_carries_the_original_state() -> None:
    publish = _RecordingPublish()

    run_terminals.publish_compensation_failure(
        publish, _RUN_ID, RuntimeError("store down"), ResearchRunState.State.RUNNING
    )

    assert len(publish.calls) == 1
    event_type, payload, kwargs = publish.calls[0]
    assert event_type is EventType.RUN_RESUME_COMPENSATION_FAILED
    assert event_type.value == _EVENT, "线上字符串是读面契约的一部分"
    assert kwargs == {"run_id": _RUN_ID, "trace_id": ""}, "与相邻发布同形（run 级 + 空 trace）"
    assert payload["run_id"] == _RUN_ID
    assert payload["failure_type"] == "RuntimeError"
    assert payload["message"] == "store down"
    assert payload["canonical_state"] == ResearchRunState.State.RUNNING, (
        "如实回答补偿失败时 run 停在哪——不伪造成 PAUSED"
    )


def test_the_payload_keys_equal_the_declared_keys() -> None:
    """文本与实现互钉：多写一个键或少写一个键都要红。"""
    publish = _RecordingPublish()

    run_terminals.publish_compensation_failure(
        publish, _RUN_ID, TimeoutError("compensation timed out"), ResearchRunState.State.PAUSED
    )

    _event_type, payload, _kwargs = publish.calls[0]
    assert set(payload) == _declared_keys(), {
        "契约文本声明": sorted(_declared_keys()),
        "实现实际发": sorted(payload),
    }


def test_the_docs_list_the_event_and_the_same_keys() -> None:
    """同源：词表列出事件、控制面文档写明读法，两份文档都写出同一组 payload 键。"""
    keys = _declared_keys()
    for relative in _DOCS:
        source = (_ROOT / relative).read_text(encoding="utf-8")
        assert _EVENT in source, f"{relative} 必须点名 {_EVENT}"
        for key in keys:
            assert f"`{key}`" in source, f"{relative} 必须写出 payload 键 {key}"


def test_both_docs_state_the_attribution_boundary() -> None:
    """一等边界（EC-06 的另一半）：两处都写明"不含任务级归因"，不靠读者猜。"""
    for relative in _DOCS:
        source = (_ROOT / relative).read_text(encoding="utf-8")
        assert "不含任务级归因" in source, f"{relative} 必须登记「不含任务级归因」这条边界"
