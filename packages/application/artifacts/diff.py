"""制品内容 Diff（PLAN-20260914-047 WP-A，EC-04「artifact diff」）。

口径：**制品 = 内容寻址的版本对象**（ArtifactStore 的 digest 即版本）。本模块对两个
已持久化制品的内容做行级 diff，不触碰工作区文件系统（控制面无 workspace 快照枚举面）。

诚实边界：

- 二进制/非 UTF-8 内容不解码：`available=False` + reason——不给"看起来一样"的假结论；
- 任一侧超过上限：`available=False` + reason——不截断成半份 diff 冒充全量；
- 两侧 digest 相同：`identical=True` 且 hunks 为空——这是"无差异"的事实，不是空实现；
- 差异行数超过展示上限：保留头部并置 `truncated=True`（明确"还有更多"）。
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from enum import StrEnum

# 单侧内容解码上限（与 /content 的 10 MiB 内联上限分开：diff 还要建行索引）。
MAX_DIFF_BYTES = 2 * 1024 * 1024
# 展示的 hunk 行上限（超出置 truncated，不静默丢弃）。
MAX_DIFF_LINES = 2000
# 差异行中的单行长度上限（超长行截断展示，避免整页被一行撑爆）。
MAX_LINE_LENGTH = 500


class DiffLineKind(StrEnum):
    CONTEXT = "CONTEXT"
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    HUNK_HEADER = "HUNK_HEADER"


class DiffUnavailable(StrEnum):
    """不可比的原因（available=False 时必须带上其一）。"""

    BINARY_CONTENT = "BINARY_CONTENT"
    TOO_LARGE = "TOO_LARGE"
    NOT_TEXT = "NOT_TEXT"


@dataclass(frozen=True, slots=True)
class DiffLine:
    kind: DiffLineKind
    text: str

    def __post_init__(self) -> None:
        if "\n" in self.text or "\r" in self.text:
            raise ValueError("diff line text must not contain line breaks")


@dataclass(frozen=True, slots=True)
class DiffStats:
    added: int
    removed: int
    context: int


@dataclass(frozen=True, slots=True)
class ArtifactDiff:
    """两个制品内容比对结果（只读派生；不可比时 lines 为空且必须带 reason）。"""

    left_digest: str
    right_digest: str
    available: bool
    identical: bool
    reason: DiffUnavailable | None
    lines: tuple[DiffLine, ...] = ()
    stats: DiffStats = DiffStats(0, 0, 0)
    truncated: bool = False

    def __post_init__(self) -> None:
        if self.available and self.reason is not None:
            raise ValueError("available diff must not carry an unavailable reason")
        if not self.available and self.reason is None:
            raise ValueError("unavailable diff must carry a reason")
        if not self.available and self.lines:
            raise ValueError("unavailable diff must not carry lines")
        if self.identical and self.lines:
            raise ValueError("identical diff must not carry lines")


@dataclass(frozen=True, slots=True)
class DiffSide:
    """diff 的一侧：内容寻址引用 + 内容 + 展示标签。"""

    digest: str
    content: bytes
    label: str = ""


def diff_artifacts(left: DiffSide, right: DiffSide) -> ArtifactDiff:
    """内容寻址制品的行级 diff（纯函数；不写任何持久面）。"""
    left_digest, right_digest = left.digest, right.digest
    left_bytes, right_bytes = left.content, right.content
    left_label = left.label or "left"
    right_label = right.label or "right"
    if left_digest == right_digest:
        return ArtifactDiff(
            left_digest=left_digest,
            right_digest=right_digest,
            available=True,
            identical=True,
            reason=None,
        )
    too_large = _too_large(left_bytes, right_bytes)
    if too_large is not None:
        return _unavailable(left_digest, right_digest, too_large)
    left_text = _decode(left_bytes)
    right_text = _decode(right_bytes)
    if left_text is None or right_text is None:
        return _unavailable(left_digest, right_digest, DiffUnavailable.NOT_TEXT)
    lines, stats, truncated = _unified_lines(
        left_text, right_text, left_label=left_label, right_label=right_label
    )
    return ArtifactDiff(
        left_digest=left_digest,
        right_digest=right_digest,
        available=True,
        identical=not lines,
        reason=None,
        lines=lines,
        stats=stats,
        truncated=truncated,
    )


def _too_large(left_bytes: bytes, right_bytes: bytes) -> DiffUnavailable | None:
    if max(len(left_bytes), len(right_bytes)) > MAX_DIFF_BYTES:
        return DiffUnavailable.TOO_LARGE
    return None


def _unavailable(left_digest: str, right_digest: str, reason: DiffUnavailable) -> ArtifactDiff:
    return ArtifactDiff(
        left_digest=left_digest,
        right_digest=right_digest,
        available=False,
        identical=False,
        reason=reason,
    )


def _decode(payload: bytes) -> str | None:
    """UTF-8 文本解码 + 二进制嗅探；不可判定为文本时返回 None。"""
    if b"\x00" in payload[:4096]:
        return None
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _unified_lines(
    left_text: str,
    right_text: str,
    *,
    left_label: str,
    right_label: str,
) -> tuple[tuple[DiffLine, ...], DiffStats, bool]:
    if left_text == right_text:
        return (), DiffStats(0, 0, 0), False
    raw = list(
        difflib.unified_diff(
            left_text.splitlines(),
            right_text.splitlines(),
            fromfile=left_label,
            tofile=right_label,
            lineterm="",
            n=2,
        )
    )
    truncated = len(raw) > MAX_DIFF_LINES
    lines = tuple(_to_line(item) for item in raw[:MAX_DIFF_LINES])
    return lines, _stats(lines), truncated


def _to_line(item: str) -> DiffLine:
    if item.startswith("+++") or item.startswith("---"):
        return DiffLine(DiffLineKind.HUNK_HEADER, _clamp(item))
    if item.startswith("@@"):
        return DiffLine(DiffLineKind.HUNK_HEADER, _clamp(item))
    if item.startswith("+"):
        return DiffLine(DiffLineKind.ADDED, _clamp(item))
    if item.startswith("-"):
        return DiffLine(DiffLineKind.REMOVED, _clamp(item))
    return DiffLine(DiffLineKind.CONTEXT, _clamp(item))


def _clamp(text: str) -> str:
    return text if len(text) <= MAX_LINE_LENGTH else text[:MAX_LINE_LENGTH] + "…"


def _stats(lines: tuple[DiffLine, ...]) -> DiffStats:
    added = sum(1 for line in lines if line.kind is DiffLineKind.ADDED)
    removed = sum(1 for line in lines if line.kind is DiffLineKind.REMOVED)
    context = sum(1 for line in lines if line.kind is DiffLineKind.CONTEXT)
    return DiffStats(added=added, removed=removed, context=context)
