"""MAINLINE 战役宪章（`.cursor/plans/goals/MAINLINE.md`）的**程序面判据**。

宪章抬头块自己声明了这个落点：

> 本文件只持有「程序与顺序」，不持有「状态」。
> 状态的唯一权威是各 GOAL 的 frontmatter（`status` / `exit_criteria`）；
> 本文件**不得**镜像、复述或缓存任何 GOAL 的状态。
> 冲突时以 `.cursor/plans/goals/README.md` 与各 GOAL frontmatter 为准。
> 判据：`tests/tooling/test_mainline_program_is_intact.py`。

本判据把那几句变成机器可检的事实（缺一即判红）：

1. **宪章在树且非空** —— 否则后面每条都会退化成空断言（承 `MEM-156`）；
2. **结构在位** —— 总目标 / 三分轴表 / 程序表 / 战役预算 / 进展记录 / 修订记录，
   且**表格列**与宪章约定的列一致（列被改名 = 契约被改）；
3. **状态不落本文件** —— GOAL 状态枚举与 EC 状态枚举**零命中**，`status:` 字段形态
   也零命中 ⇒ 「把状态抄进宪章」在构造上不可能通过；
4. **程序表是程序** —— 每行的轴列取自三分轴或保留槽，id 列是 `GOAL-YYYYMMDD-NNN`
   或未指派；**至少一行**已指派真实 id（否则程序表只是形状）；
5. **进展记录的复核性** —— 每条 `RECHECK` 链接都解析到 `../rechecks/` 下**真实存在**
   的文件（宪章原文：RECHECK 列必须是指向 `../rechecks/` 下真实文件的相对链接）；
6. **预算是数** —— `max_goals` / `replan_every_goals` 是正整数。

**射程边界（如实登记，不假装覆盖）**：

- 第 3 条是**词法**判据（枚举词 + `status:` 形态）。换个说法把状态写进来不会被它抓到；
  它挡的是「顺手把状态抄进宪章」这类默认漂移，不是规避 —— 与
  `test_reproducibility_wording.py` 对「加引号的提及」的处理同一类边界登记。
- 第 5 条只判**链接可解析**，不判被链接的复检是什么结论（那是各 GOAL / RECHECK 面的事）。
- 本判据**不**读任何 GOAL 的 frontmatter ⇒ 它不会因某个 GOAL 的状态流转而红，
  这正是「状态不落本文件」的负向自证。
- `进展记录` 起初**只有表头**（宪章：只追加，收口时追加一行）⇒ 那条链接判据当前对真文件
  是空真的；空真不当作覆盖 —— 判据形态本身由 `test_the_helpers_are_not_vacuous`
  在合成输入上取证（合成里有一条**坏链接**必须被报出）。
"""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_CHARTER = _ROOT / ".cursor" / "plans" / "goals" / "MAINLINE.md"
_RECHECK_DIR = _ROOT / ".cursor" / "plans" / "rechecks"

#: 必含小节（宪章结构；缺一即「程序不完整」）。
_REQUIRED_SECTIONS: tuple[str, ...] = (
    "## 总目标",
    "## 程序表",
    "## 战役预算",
    "## 进展记录",
    "## 修订记录",
)
#: 三分轴（宪章原文的**轴名**；改词即改契约）。
_AXES: tuple[str, ...] = ("连续性", "深度", "质量")
#: 轴列还允许的取值：宪章程序表里的**组合轴**（深度+质量）、**广度的受判位**
#: （宪章：广度不是一条轴，只在研究循环**真正用到**时补 ⇒ 它出现即须带「真实用到」的
#: 语义，由「一句话目标」列承担）与**保留槽**占位。
_AXIS_FREE_VALUES: tuple[str, ...] = ("广度", "深度+质量", "—")
#: 程序表列头（宪章：不得改表格列）。
_PROGRAM_COLUMNS: tuple[str, ...] = ("序", "GOAL id", "轴", "一句话目标", "依赖")
#: 进展记录列头。
_PROGRESS_COLUMNS: tuple[str, ...] = ("日期", "GOAL", "一句话结论", "RECHECK")
#: 总目标下的轴定义表列头（`反面` 列在 ⇒ 三分轴的判据不含糊化）。
_AXIS_TABLE_COLUMNS: tuple[str, ...] = ("轴", "定义", "反面（不算推进）")

_GOAL_ID = re.compile(r"^GOAL-\d{8}-\d{3}$")
_RECHECK_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")

#: **状态**词表：GOAL 状态枚举 + EC 状态枚举（`packages`/治理契约的取值域）。
#: 它们出现在宪章里 = 状态被镜像/缓存/复述 ⇒ 判红。
_STATUS_LEXEMES: tuple[str, ...] = (
    "DRAFT",
    "ACTIVE",
    "PAUSED",
    "BLOCKED",
    "ABORTED",
    "ACHIEVED",
    "PENDING",
    "PASS",
    "PASS_WITH_WARNINGS",
)
#: 字段形态：`status:` 这类**结构**上的状态镜像（词表抓不到的写法由这条兜）。
_STATUS_FIELD = re.compile(r"\bstatus\s*:", re.IGNORECASE)
#: 预算键（宪章原文的两个键，必须都在且有正整数取值）。
_BUDGET_KEYS: tuple[str, ...] = ("max_goals", "replan_every_goals")


def _charter_text() -> str:
    assert _CHARTER.is_file(), f"宪章不在树：{_CHARTER.relative_to(_ROOT)}"
    return _CHARTER.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    """取某二级小节（到下一个 `## ` 为止；节外内容不算数）。"""
    assert heading in text, f"宪章缺少小节 {heading!r}"
    rest = text.split(heading, 1)[1]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def _cells(line: str) -> list[str]:
    return [_plain(cell) for cell in line.strip().strip("|").split("|")]


def _plain(cell: str) -> str:
    """去 Markdown 强调标记（`**`/`` ` ``）—— 判的是**词**不是装饰。"""
    return cell.replace("**", "").replace("`", "").strip()


def _separator(cells: list[str]) -> bool:
    return bool(cells) and all(set(cell) <= set("-: ") and cell for cell in cells)


def _table_rows(section: str) -> list[list[str]]:
    """小节里的**数据行**（跳过表头与分隔行；非表格行不算）。

    表头 = 该节第一个表格行，分隔行 = 全由 `-:` 组成的那行 ⇒ 其余表格行都是数据。
    """
    rows: list[list[str]] = []
    header_seen = False
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = _cells(line)
        if _separator(cells):
            header_seen = True
            continue
        if not header_seen:
            continue
        rows.append(cells)
    return rows


def _table_header(section: str) -> list[str]:
    for line in section.splitlines():
        if line.startswith("|"):
            return _cells(line)
    raise AssertionError("小节里没有表格（宪章结构假设失效）")


def _status_lexemes_in(text: str) -> list[str]:
    return [token for token in _STATUS_LEXEMES if re.search(rf"\b{token}\b", text)]


def _bad_recheck_links(section: str, base: Path) -> list[str]:
    """返回**不解析**的 RECHECK 链接（空列表 = 全部可复核）。"""
    bad: list[str] = []
    for row in _table_rows(section):
        links = _RECHECK_LINK.findall(row[-1])
        if not links:
            bad.append(f"缺链接行: {row}")
            continue
        for target in links:
            clean = target.split("#", 1)[0].strip()
            if not clean.startswith("../rechecks/"):
                bad.append(f"链接不在 ../rechecks/ 下: {target}")
                continue
            resolved = (base / clean).resolve()
            if not resolved.is_file():
                bad.append(f"链接目标不存在: {target}")
    return bad


def test_the_charter_exists_and_is_not_empty() -> None:
    text = _charter_text()
    assert len(text.splitlines()) >= 30, "宪章过短 ⇒ 受判面不成立"
    for section in _REQUIRED_SECTIONS:
        assert section in text, f"宪章缺少小节 {section!r}"


def test_the_thresholds_table_keeps_the_three_axes_and_their_counterexamples() -> None:
    """三分轴：名字、**反面**列、以及每条轴的反面取值都要在位（不得含糊化）。"""
    table = _section(_charter_text(), "## 总目标")
    assert _table_header(table) == list(_AXIS_TABLE_COLUMNS), _table_header(table)
    rows = {row[0]: row for row in _table_rows(table)}
    for axis in _AXES:
        assert axis in rows, f"缺轴：{axis}"
        assert len(rows[axis]) == 3, f"轴 {axis} 的定义/反面列缺失：{rows[axis]}"
        assert rows[axis][2], f"轴 {axis} 的反面列为空 ⇒ 判据可被含糊化通过"


def test_no_goal_or_criterion_status_is_mirrored_in_the_charter() -> None:
    """**状态不落本文件**：状态枚举词与 `status:` 字段形态零命中。"""
    text = _charter_text()
    found = _status_lexemes_in(text)
    assert found == [], f"宪章镜像了状态枚举词：{found}（状态的权威是各 GOAL frontmatter）"
    field = _STATUS_FIELD.search(text)
    assert field is None, f"宪章出现状态字段形态（{field.group(0)!r}）⇒ 状态被缓存进宪章"


def test_the_program_table_rows_are_well_formed() -> None:
    """程序表：列头、轴取值、id 形态，且**至少一行**已指派真实 GOAL id。"""
    table = _section(_charter_text(), "## 程序表")
    assert _table_header(table) == list(_PROGRAM_COLUMNS), _table_header(table)
    rows = _table_rows(table)
    assert rows, "程序表没有数据行 ⇒ 空真"
    assigned: list[str] = []
    for row in rows:
        assert len(row) == len(_PROGRAM_COLUMNS), f"程序表行列数不符：{row}"
        axis = row[2]
        assert axis in (*_AXES, *_AXIS_FREE_VALUES), f"轴列取值不在三分轴内：{axis!r}"
        goal_id = row[1]
        if goal_id == "—":
            continue
        assert _GOAL_ID.match(goal_id), f"GOAL id 形态非法：{goal_id!r}"
        assert row[3], f"已指派行的「一句话目标」为空：{row}"
        assigned.append(goal_id)
    assert assigned, "程序表没有任何已指派 GOAL id ⇒ 这只是形状，不是程序"


def test_every_recorded_recheck_link_resolves_under_rechecks() -> None:
    """进展记录：每条 RECHECK 链接都解析到 `../rechecks/` 下真实文件。"""
    section = _section(_charter_text(), "## 进展记录")
    assert _table_header(section) == list(_PROGRESS_COLUMNS), _table_header(section)
    bad = _bad_recheck_links(section, _CHARTER.parent)
    assert bad == [], f"进展记录里不可复核的 RECHECK 链接：{bad}"
    assert _RECHECK_DIR.is_dir(), "复检目录不存在 ⇒ 上面那条判据的解析面失效"


def test_the_campaign_budget_keys_are_positive_integers() -> None:
    section = _section(_charter_text(), "## 战役预算")
    for key in _BUDGET_KEYS:
        match = re.search(rf"`{key}`:\s*(\d+)", section)
        assert match is not None, f"缺预算键 `{key}`"
        assert int(match.group(1)) >= 1, f"预算键 `{key}` 必须是正整数"


def test_the_revision_log_is_append_only_so_replaced_rows_survive() -> None:
    """修订记录小节在位、且本文件**不**留下被替换行的删除痕迹（只追加的口径）。"""
    text = _charter_text()
    section = _section(text, "## 修订记录")
    assert "只追加" in section or "原样移入" in section, (
        "修订记录的「只追加」口径必须写在节内（否则替换行会被顺手删掉）"
    )
    assert "GOAL-PLACEHOLDER" not in text, (
        "程序表仍留着建档占位符 ⇒ 序 1 的 GOAL id 尚未换成实际建档的 id"
    )


def test_the_helpers_are_not_vacuous(tmp_path: Path) -> None:
    """受判面自检：辅助函数在**合成输入**上给出预期读数（正例 + 反例各一）。

    合成面自带 `goals/` 与 `rechecks/` 两个目录 ⇒ 「正例通过」不是因为链接恰好
    解析到真文件，而是因为解析逻辑本身成立（隔离真树，免得判据跟着树漂）。
    """
    base = tmp_path / "goals"
    base.mkdir()
    (tmp_path / "rechecks").mkdir()
    (tmp_path / "rechecks" / "RECHECK-20260101-002-x.md").write_text("x", encoding="utf-8")
    good = (
        "## 进展记录\n\n| 日期 | GOAL | 一句话结论 | RECHECK |\n"
        "| --- | --- | --- | --- |\n"
        "| 2026-01-01 | GOAL-20260101-001 | 例子 | "
        "[RECHECK-20260101-002](../rechecks/RECHECK-20260101-002-x.md) |\n"
    )
    section = _section(good, "## 进展记录")
    assert _bad_recheck_links(section, base) == [], "正例应通过"

    missing = good.replace("../rechecks/RECHECK-20260101-002-x.md", "../rechecks/nope.md")
    assert _bad_recheck_links(_section(missing, "## 进展记录"), base), "坏链接应被报出"

    no_link = good.replace("[RECHECK-20260101-002](../rechecks/RECHECK-20260101-002-x.md)", "已核")
    assert _bad_recheck_links(_section(no_link, "## 进展记录"), base), "缺链接应被报出"

    outside = good.replace("../rechecks/RECHECK-20260101-002-x.md", "RECHECK-x.md")
    assert _bad_recheck_links(_section(outside, "## 进展记录"), base), "越界链接应被报出"

    assert _status_lexemes_in("本文件状态：ACTIVE") == ["ACTIVE"], "状态词表应命中"
    assert _status_lexemes_in("本文件只持有程序与顺序") == [], "无关文本不应命中"
    assert _STATUS_FIELD.search("status: ACTIVE") is not None, "字段形态应命中"
    assert _RECHECK_DIR.is_dir()
    assert _table_header(good) == list(_PROGRESS_COLUMNS), _table_header(good)
