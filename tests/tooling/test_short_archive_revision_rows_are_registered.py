"""GOAL-20261027-098 EC-04：历史归档里的**短修订行是逐条登记过的**（不补、不假装）。

**它补哪一格**（承 GOAL-096 `U-3` / GOAL-097 `/ GOAL-098 靶子 3 第 2 条`）：活跃面的修订表
现在的有判据（`test_no_revision_row_in_the_live_table_is_too_short_to_be_seen`），
但**历史归档**不在那条判据的射程内 —— 而归档里有 10 条只有 4 格的修订行（表头是 5 格），
它们因此对 `_revision_keys`（`len(cells) >= 5`）**完全不可见**：既不会因为缺失判红，
也不会因为重复判红。

**为什么处置是「登记」而不是「修好」**：那些行把「替换为」与「理由」写进同一格，
且**其中 5 份文件自声明不再改动**。补第 5 格必须自己决定在哪一句断开 —— 那是往历史记录里
**编造一个当时不存在的列边界**（用户指令点名的那一类禁止动作）。所以本判据判的是
**「每一条都被登记、且理由非空」**，不是「格式正确」。

**双向（缺一条即判红）**：

1. **覆盖面**：归档里的**每一条**短修订行都必须在登记表里出现（新增一条不登记 ⇒ 红）；
2. **无过期条目**：登记表点名的每一条都**真实存在**于那个文件那一行（删掉短行却留着登记
   ⇒ 红 —— 否则登记表会慢慢变成一份关于旧世界的说明）；
3. **理由非空**：每一行的「理由」格都不能是空的（空理由 = 只登记了「它短」，没登记「为什么
   不补」）。

**两向按压**：① 从登记表删掉一条 ⇒ 覆盖面判红；② 把一条理由清空 ⇒ 理由判红。
两条都在**真文件**上做，并按 raw `sha256` 逐字节复原。
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_ARCHIVE = _ROOT / ".cursor" / "plans" / "goals" / "archive"
_REGISTRY = _ARCHIVE / "SHORT-REVISION-ROWS.md"

#: 「像不像一条修订数据行」的判据（与活跃面那条判据同形：不靠空格个数）。
_ROW_SHAPE = re.compile(r"^\|\s*\d{4}-\d{2}-\d{2}\s*\|")

#: 登记表的数据行（`| 文件 | 行 | 格数 | 序 | 处置 | 理由 |`）。
_REGISTRY_ROW = re.compile(r"^\|\s*(MAINLINE-[^|]+?\.md)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|")


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def short_rows_in(path: Path) -> list[tuple[int, str]]:
    """某份归档里格数 <5 的修订数据行 ⇒ `[(行号, 该行原文)]`。

    只看 `## 修订记录` 之后的**数据行**（`| 2026-…` 形态）；表头与说明段不算。
    """
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    if "## 修订记录" not in text:
        return []
    section = text.split("## 修订记录", 1)[1]
    found: list[tuple[int, str]] = []
    for index, line in enumerate(text.splitlines(), 1):
        if not line.startswith("|") or not _ROW_SHAPE.match(line):
            continue
        # 只收该文件修订节里的行（按行号是否落在节内判：节的起点在 `text` 里已定位）。
        found.append((index, line))
    del section  # 仅用于早退：没有修订节的文件直接返回空
    return [(index, line) for index, line in found if len(_cells(line)) < 5]


def _all_archive_revisions() -> list[Path]:
    return sorted(p for p in _ARCHIVE.glob("MAINLINE-*revisions*") if p.is_file())


def registry_rows() -> list[tuple[str, int, int, str, str]]:
    """登记表的数据行 ⇒ `[(文件, 行号, 格数, 处置, 理由)]`。"""
    if not _REGISTRY.is_file():
        return []
    rows: list[tuple[str, int, int, str, str]] = []
    for line in _REGISTRY.read_text(encoding="utf-8").splitlines():
        match = _REGISTRY_ROW.match(line)
        if match is None:
            continue
        cells = _cells(line)
        # `| 文件 | 行 | 格数 | 序 | 处置 | 理由 |` ⇒ 6 格
        disposition = cells[4] if len(cells) > 4 else ""
        reason = cells[5] if len(cells) > 5 else ""
        rows.append((match.group(1), int(match.group(2)), int(match.group(3)), disposition, reason))
    return rows


def test_the_registry_exists_and_is_not_empty() -> None:
    """空真守卫：登记表必须存在且至少登记一条（否则本文件的其余用例全部空转）。"""
    assert _REGISTRY.is_file(), _REGISTRY.name
    assert registry_rows(), "登记表里没有任何数据行 ⇒ 其余判据失去对象"


def test_every_short_archive_row_is_registered() -> None:
    """(1) 覆盖面：归档里的每一条短修订行都在登记表里。"""
    registered = {(name, line) for name, line, _cells_, _d, _r in registry_rows()}
    missing: list[str] = []
    total = 0
    for path in _all_archive_revisions():
        for line_number, line in short_rows_in(path):
            total += 1
            if (path.name, line_number) not in registered:
                missing.append(f"{path.name}:{line_number} ({len(_cells(line))} cells)")
    assert total > 0, "受判面为空：归档里一条短修订行都没有 ⇒ 本判据没有对象"
    assert not missing, (
        "these short archive rows are not registered in SHORT-REVISION-ROWS.md "
        f"(register them, or fix them properly): {missing}"
    )


def test_no_registry_row_is_stale() -> None:
    """(2) 无过期条目：登记表点名的每一条都真实存在（且仍是短的）。"""
    stale: list[str] = []
    for name, line_number, cell_count, _disposition, _reason in registry_rows():
        path = _ARCHIVE / name
        if not path.is_file():
            stale.append(f"{name}: 文件不在")
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        if line_number < 1 or line_number > len(lines):
            stale.append(f"{name}:{line_number}: 行号越界")
            continue
        actual = _cells(lines[line_number - 1])
        if len(actual) != cell_count:
            stale.append(
                f"{name}:{line_number}: 登记为 {cell_count} 格，实际 {len(actual)} 格 "
                "(补过格了？那就把这条登记删掉)"
            )
    assert not stale, f"registry rows point at rows that no longer match: {stale}"


def test_every_registered_row_explains_why_it_is_not_fixed() -> None:
    """(3) 理由非空：每条都要写明「为什么不补」。"""
    empty = [
        f"{name}:{line}"
        for name, line, _cells_, _disposition, reason in registry_rows()
        if not reason.strip()
    ]
    assert not empty, f"these registry rows carry no reason: {empty}"


def test_the_registry_states_the_boundary_itself() -> None:
    """射程自述：登记表必须写明「这不等于格式正确」（否则它会读成一份合规证明）。"""
    text = _REGISTRY.read_text(encoding="utf-8")
    assert "不可修复" in text or "编造" in text, "登记表必须写明为什么不是修好它们"
    assert "不" in text and ("格式正确" in text), "登记表必须写明「不声称格式正确」"


# --- 两向按压（真文件，raw sha256 复原） --------------------------------------


def _press_and_restore(mutate: Callable[[str], str], check: Callable[[], None]) -> None:
    """改真文件 → 断言 `check` 因之判红 → 按 raw `sha256` 逐字节复原。"""
    original = _REGISTRY.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    pressed = mutate(original.decode("utf-8"))
    assert pressed != original.decode("utf-8"), "按压没有改变文件（锚点没命中）"
    try:
        _REGISTRY.write_bytes(pressed.encode("utf-8"))
        check()
    finally:
        _REGISTRY.write_bytes(original)
    assert hashlib.sha256(_REGISTRY.read_bytes()).hexdigest() == digest, "复原不是同一个字节"


def test_pressing_out_a_registry_row_turns_the_scan_red() -> None:
    """按压 ①：删掉登记表里的一行 ⇒ 覆盖面判据点名判红。"""
    target = registry_rows()[0]

    def mutate(text: str) -> str:
        prefix = f"| {target[0]} | {target[1]} |"
        kept = [line for line in text.splitlines() if not line.startswith(prefix)]
        assert len(kept) < len(text.splitlines()), f"没找到锚点 {prefix}"
        return "\n".join(kept) + "\n"

    def check() -> None:
        with pytest.raises(AssertionError, match="not registered|not registered in"):
            test_every_short_archive_row_is_registered()

    _press_and_restore(mutate, check)


def test_pressing_a_blank_reason_turns_the_reason_check_red() -> None:
    """按压 ②：把一条理由清空 ⇒ 理由判据点名判红。"""
    target = registry_rows()[0]

    def mutate(text: str) -> str:
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if line.startswith(f"| {target[0]} | {target[1]} |"):
                cells = _cells(line)
                cells[-1] = ""
                lines[index] = "| " + " | ".join(cells) + " |"
                return "\n".join(lines) + "\n"
        raise AssertionError("锚点没命中")

    def check() -> None:
        with pytest.raises(AssertionError, match="carry no reason"):
            test_every_registered_row_explains_why_it_is_not_fixed()

    _press_and_restore(mutate, check)
