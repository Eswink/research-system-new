"""制品内容 Diff 应用层测试（PLAN-20260914-047 WP-A）。

诚实边界回归：相同 digest = 无差异事实；二进制/非 UTF-8 不解码；超限不截断冒充；
超长展示置 truncated；行文本不含换行（DTO 层直接可序列化）。
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from packages.application.artifacts.diff import (
    MAX_DIFF_BYTES,
    MAX_DIFF_LINES,
    DiffLineKind,
    DiffSide,
    DiffUnavailable,
    diff_artifacts,
)


def _side(digest: str, content: bytes, label: str = "") -> DiffSide:
    return DiffSide(digest=digest, content=content, label=label)


def test_identical_digest_is_a_fact_not_an_empty_implementation() -> None:
    view = diff_artifacts(_side("sha256:a", b"same"), _side("sha256:a", b"same"))
    assert view.available is True
    assert view.identical is True
    assert view.lines == ()
    assert view.reason is None


def test_text_change_produces_added_and_removed_lines() -> None:
    view = diff_artifacts(
        _side("sha256:a", b"line one\nline two\n"),
        _side("sha256:b", b"line one\nline 2\nline three\n"),
    )
    assert view.available is True
    assert view.identical is False
    kinds = [line.kind for line in view.lines]
    assert DiffLineKind.REMOVED in kinds
    assert DiffLineKind.ADDED in kinds
    assert view.stats.removed >= 1 and view.stats.added >= 2
    assert any("line three" in line.text for line in view.lines)


def test_same_content_different_digest_is_identical() -> None:
    """内容相等但 digest 不同（不同存储实例）：结论仍是"无差异"。"""
    view = diff_artifacts(_side("sha256:a", b"body\n"), _side("sha256:b", b"body\n"))
    assert view.available is True
    assert view.identical is True
    assert view.lines == ()


def test_binary_content_is_not_decoded() -> None:
    view = diff_artifacts(
        _side("sha256:a", b"\x00\x01binary"),
        _side("sha256:b", b"\x00\x02binary"),
    )
    assert view.available is False
    assert view.reason is DiffUnavailable.NOT_TEXT
    assert view.lines == ()


def test_non_utf8_content_is_not_decoded() -> None:
    view = diff_artifacts(
        _side("sha256:a", b"caf\xe9 latin-1"),
        _side("sha256:b", b"caf\xe9 latin-1 changed"),
    )
    assert view.available is False
    assert view.reason is DiffUnavailable.NOT_TEXT


def test_oversized_content_is_refused_not_truncated() -> None:
    big = b"x" * (MAX_DIFF_BYTES + 1)
    view = diff_artifacts(_side("sha256:a", big), _side("sha256:b", b"small"))
    assert view.available is False
    assert view.reason is DiffUnavailable.TOO_LARGE
    assert view.lines == ()


def test_many_differences_are_truncated_with_a_flag() -> None:
    left = "\n".join(f"old {index}" for index in range(MAX_DIFF_LINES))
    right = "\n".join(f"new {index}" for index in range(MAX_DIFF_LINES))
    view = diff_artifacts(_side("sha256:a", left.encode()), _side("sha256:b", right.encode()))
    assert view.available is True
    assert view.truncated is True
    assert len(view.lines) == MAX_DIFF_LINES


def test_long_lines_are_clamped_and_never_contain_newlines() -> None:
    view = diff_artifacts(
        _side("sha256:a", b"short\n"),
        _side("sha256:b", b"x" * 5000 + b"\n"),
    )
    assert view.available is True
    assert all("\n" not in line.text for line in view.lines)
    assert any(line.text.endswith("…") for line in view.lines)


def test_unavailable_view_rejects_lines_and_missing_reason() -> None:
    from packages.application.artifacts.diff import ArtifactDiff

    with pytest.raises(ValueError):
        ArtifactDiff(
            left_digest="a",
            right_digest="b",
            available=False,
            identical=False,
            reason=None,
        )


def test_digits_only_change_is_reported() -> None:
    """类型变化（int → Decimal 字面量）也是真实差异，不是噪声。"""
    view = diff_artifacts(
        _side("sha256:a", b'{"value": 1}'),
        _side("sha256:b", str({"value": Decimal("1")}).encode()),
    )
    assert view.available is True
    assert view.identical is False
