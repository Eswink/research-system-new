"""SSE 行解析测试。"""

from __future__ import annotations

import pytest

from adapters.relay.sse import parse_sse_events


def _events(text: str) -> list[dict[str, object]]:
    return list(parse_sse_events(iter(text.splitlines())))


class TestParseSseEvents:
    def test_single_event(self) -> None:
        events = _events('data: {"id":"1"}\n\n')
        assert events == [{"id": "1"}]

    def test_multiple_events_with_done(self) -> None:
        text = 'data: {"id":"1"}\n\ndata: {"id":"2"}\n\ndata: [DONE]\n\n'
        assert _events(text) == [{"id": "1"}, {"id": "2"}]

    def test_ignores_event_and_id_lines(self) -> None:
        text = 'event: message\nid: 42\ndata: {"a":1}\n\n'
        assert _events(text) == [{"a": 1}]

    def test_ignores_comment_lines(self) -> None:
        text = ': keep-alive\ndata: {"a":1}\n\n'
        assert _events(text) == [{"a": 1}]

    def test_multiline_data_joined(self) -> None:
        text = 'data: {"a":\ndata: 1}\n\n'
        assert _events(text) == [{"a": 1}]

    def test_malformed_json_raises(self) -> None:
        with pytest.raises(Exception):
            _events("data: {not-json}\n\n")

    def test_trailing_data_without_blank_line(self) -> None:
        events = _events('data: {"a":1}\n')
        assert events == [{"a": 1}]
