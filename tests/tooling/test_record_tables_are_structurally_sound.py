"""记录面 markdown 表的**结构**判据：表体必须连续、列数一致、无孤立数据行。

**它补哪一格**（2026-10-30 实测的真缺陷，已连犯两次）：

1. 序 66 的归档轮：一条 `>` 指针被插在**进展表的数据行之间** ⇒ 它下面那行成了孤立
   数据行（上方既非表头/分隔行、也非同表数据行）；
2. 序 68 的记录轮：`MAINLINE.md` 的**程序表**在 `| 67 |` 与 `| 68 |` 之间多了一个
   **空行**；**修订记录**同样。

两次都**没有被任何判据抓到**，而且暴露了一个更糟的事实：两个解析器对同一棵树给出
**不同答案**——

- `test_goal_ledger_covers_every_commit._table()` 遇空行 **`break`** ⇒ 程序表读到
  **67** 行 ⇒ `_program_seq("GOAL-20261029-100")` 返回 `None` ⇒ 该 GOAL 在台账判据的
  scope 里**退化到 `created_at` 兜底**，序 68 对它**不可见**；
- `test_mainline_program_is_intact._table_rows()` 遇空行 **`continue`** ⇒ 读到 **68** 行、
  全绿。

⇒ 宽松的那个在跑、严格的那个被绕过。**结构坏了，但所有判据都是绿的。** 本判据把
「结构」本身变成受判对象，两种解析器的分歧就无处藏身。

**判什么**（三条，缺一即判红）：
1. **表体连续** —— 一张表的数据行之间不得出现空行（空行 = markdown 表结束）；
2. **列数一致** —— 每一行的格数必须等于该表表头的格数（多一列/少一列都会让某些
   解析器按「另一张表的列头」处理而 `break`）；
3. **无孤立数据行** —— 以 `|` 开头、且「看起来是数据行」（首格是日期或 `GOAL-…`）
   的行，上方必须是同表的表头/分隔行/数据行；否则它**不属于任何表**，阅读与解析
   都会丢。

**不判什么**（射程边界，如实登记）：
- 不判内容对错（那是各 GOAL 自己的面）；
- 不判归档文件的表（历史资产，见 `test_short_archive_revision_rows_are_registered`
  的登记面）；
- 不判「表格是否应该存在」（只判存在的表**结构**是否成立）。
"""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_GOALS = _ROOT / ".cursor" / "plans" / "goals"
_CHARTER = _GOALS / "MAINLINE.md"

#: 受判面：宪章 + 序 61 起的终态 GOAL（与两个台账判据同一 scope 口径）。
_CUTOFF_SEQ = 61
_CUTOFF_DATE = "2026-10-22"
_TERMINAL = frozenset({"ACHIEVED", "BLOCKED", "ABANDONED"})

#: 「看起来是数据行」的两种形态：首格是日期，或首格是 GOAL id。
_DATA_ROW = re.compile(r"^\|\s*(\d{4}-\d\d-\d\d|GOAL-\d{8}-\d{3})\b")
#: 表的分隔行（`| --- | --- |`）。
_SEPARATOR = re.compile(r"^\|(?:\s*:?-{3,}:?\s*\|)+\s*$")


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_pipe(line: str) -> bool:
    return line.lstrip().startswith("|")


def _table_problems(lines: list[str]) -> list[str]:
    """一份文件里所有表的结构问题（逐条点名行号）。"""
    problems: list[str] = []
    index = 0
    total = len(lines)
    while index < total:
        if not _is_pipe(lines[index]) or _SEPARATOR.match(lines[index].strip()):
            index += 1
            continue
        header = _cells(lines[index])
        header_line = index + 1
        # 表头下一行必须是分隔行，否则这不是一张表（而是孤立数据行）。
        if index + 1 >= total or not _SEPARATOR.match(lines[index + 1].strip()):
            index += 1
            continue
        width = len(header)
        index += 2
        while index < total:
            line = lines[index]
            if not _is_pipe(line):
                if line.strip():
                    break  # 非空非表行：表结束
                # 空行：只有后面**紧接**还是本表的数据行才算「表体被切断」。
                later = index + 1
                if (
                    later < total
                    and _is_pipe(lines[later])
                    and not _SEPARATOR.match(lines[later].strip())
                ):
                    problems.append(
                        f"第 {index + 1} 行是表体内的空行（表头在第 {header_line} 行）："
                        "空行会结束 markdown 表 ⇒ 之后的数据行不属于这张表"
                    )
                    index = later
                    continue
                break
            if _SEPARATOR.match(line.strip()):
                problems.append(f"第 {index + 1} 行是表体内的第二个分隔行（同一张表只该有一个）")
                index += 1
                continue
            cells = _cells(line)
            if len(cells) != width:
                problems.append(
                    f"第 {index + 1} 行有 {len(cells)} 格，表头（第 {header_line} 行）有 {width} 格"
                )
            index += 1
    return problems


def _orphan_rows(lines: list[str]) -> list[str]:
    """看起来像数据行、但上方不属于任何表的行。"""
    findings: list[str] = []
    for index, line in enumerate(lines):
        if not _DATA_ROW.match(line):
            continue
        if index == 0:
            findings.append("第 1 行是数据行但没有表头")
            continue
        above = index - 1
        if _is_pipe(lines[above]) or _SEPARATOR.match(lines[above].strip()):
            continue
        findings.append(f"第 {index + 1} 行是孤立数据行（上一行不是表行：{lines[above][:40]!r}）")
    return findings


def _scope_files() -> list[Path]:
    """宪章 + 序 61 起的终态 GOAL。"""
    files = [_CHARTER]
    for path in sorted(_GOALS.glob("GOAL-*.md")):
        text = path.read_text(encoding="utf-8")
        status = re.search(r"^status:\s*(\S+)", text, re.MULTILINE)
        if status is None or status.group(1) not in _TERMINAL:
            continue
        created = re.search(r"^created_at:\s*(\S+)", text, re.MULTILINE)
        if created is None or created.group(1) < _CUTOFF_DATE:
            continue
        files.append(path)
    return files


def test_the_charter_and_scoped_goals_have_sound_tables() -> None:
    """真文件：宪章 + 受判面内 GOAL 的表结构全部成立。"""
    offenders: dict[str, list[str]] = {}
    for path in _scope_files():
        lines = path.read_text(encoding="utf-8").splitlines()
        problems = _table_problems(lines) + _orphan_rows(lines)
        if problems:
            offenders[path.name] = problems
    assert not offenders, "记录面存在 markdown 表结构缺陷：\n" + "\n".join(
        f"  {name}: {items}" for name, items in offenders.items()
    )


def test_the_scope_is_not_empty() -> None:
    """受判面非空（空真不算通过）。"""
    files = _scope_files()
    assert len(files) >= 2, f"受判面只有 {len(files)} 个文件 ⇒ 判据失去对象"
    assert _CHARTER in files


def test_a_blank_line_inside_a_table_is_named_red() -> None:
    """**反证臂 1**：表体中间插一个空行 ⇒ 点名判红（并指出行号）。"""
    lines = [
        "| 序 | GOAL id |",
        "| --- | --- |",
        "| 1 | GOAL-20260101-001 |",
        "",
        "| 2 | GOAL-20260102-002 |",
    ]
    problems = _table_problems(lines)
    assert problems, "表体内的空行没有被判红"
    assert any("空行" in item and "第 4 行" in item for item in problems), problems


def test_a_row_with_the_wrong_cell_count_is_named_red() -> None:
    """**反证臂 2**：某行格数与表头不符 ⇒ 点名判红。"""
    lines = [
        "| 序 | GOAL id |",
        "| --- | --- |",
        "| 1 | GOAL-20260101-001 |",
        "| 2 | GOAL-20260102-002 | 多余的一格 |",
    ]
    problems = _table_problems(lines)
    assert problems, "格数不符没有被判红"
    assert any("3 格" in item and "2 格" in item for item in problems), problems


def test_an_orphan_data_row_is_named_red() -> None:
    """**反证臂 3**：数据行上方不是表行 ⇒ 点名判红（本轮第 3 处缺陷的形态）。"""
    lines = [
        "## 进展记录",
        "",
        "| 日期 | GOAL |",
        "| --- | --- |",
        "| 2026-01-01 | GOAL-20260101-001 |",
        "",
        "> 一条被插进表中间的指针",
        "| 2026-01-02 | GOAL-20260102-002 |",
    ]
    problems = _orphan_rows(lines)
    assert problems, "孤立数据行没有被判红"
    assert any("第 8 行" in item for item in problems), problems


def test_a_well_formed_table_produces_no_findings() -> None:
    """正例：结构完好的表 + 表后的指针块 ⇒ 零发现（不误报）。"""
    lines = [
        "## 进展记录",
        "",
        "| 日期 | GOAL |",
        "| --- | --- |",
        "| 2026-01-01 | GOAL-20260101-001 |",
        "| 2026-01-02 | GOAL-20260102-002 |",
        "",
        "> 序 1 的进展记录已移入 [X](archive/X.md)（原文搬运）。",
        "",
        "## 修订记录",
        "",
        "| 日期 | 序 |",
        "| --- | --- |",
        "| 2026-01-01 | 1（新增） |",
    ]
    assert _table_problems(lines) == [], _table_problems(lines)
    assert _orphan_rows(lines) == [], _orphan_rows(lines)
