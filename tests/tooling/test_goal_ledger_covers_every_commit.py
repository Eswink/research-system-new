"""GOAL 记录面判据：**CI 台账里的每一个提交，都必须落在某一条 cycle 行的 `commits` 格里**。

**它补哪一道缝**：这条对账原先只写在 `tools/goal092_closeout_assertions.py` 里
（`_log_verdicts`）。它属于**某一个 GOAL 的收口断言集** ⇒ 只保护 GOAL-092 自己：
GOAL-092 因此被补正过一次（迭代日志 1 行 → 6 行），而**下一个 GOAL 没有这条判据**。
实测后果（GOAL-093）：迭代日志 2 行、实际提交 7 个，`ff7546d7` / `c626aced` /
`2998649d` **既不进台账、也不进任何 cycle 行**，它的收口验证器仍报 68 PASS / 0 FAIL。
同一个毛病以「**另一个 GOAL**」的面貌重现 —— 因为判据原本是**继承来的**，而继承靠
每个验证器**主动**把自己的 GOAL 传进去，那正是失效点。

**本判据的形状**：不继承、不传参，**遍历树里的 GOAL 文件**。落在 `tests/tooling/`
⇒ 在 m0 的 `python/tests` 收集面内 ⇒ 每新增一个 GOAL **自动**受判，无需任何登记。

**为什么不把 `_log_verdicts` 上提到 `tools/closeout_recheck_assertions.py`**：
`standard_verdicts(root: Path)` 只收**树根**，它不知道「当前在验哪个 GOAL」 ⇒ 上提之后
仍要每个验证器把 GOAL 路径**主动**传进来 ⇒ 继承问题原样存在（换了个地方而已）。

判什么（缺一即判红）：

1. **台账 → 日志的逐提交覆盖** —— `## CI 台账` 的 `提交` 列里出现的每个哈希，必须出现在
   `## 迭代日志` 某一行 `commits` 列的格里。**只认 `commits` 列**：同一行别的格里
   （`CI run/结论` / `修复` / `剩余差距`）出现该哈希**不算收录** —— 那恰好是「把提交塞进
   散文」的形态，而本判据要挡的就是它。
2. **不许空真** —— 终态 GOAL 的台账为空、日志没有数据行、台账某一行没写提交，
   **分别**点名失败（空集合 = 未取证，不是 OK）。
3. **祖父条款** —— 只有**本判据落地时及之后**的轮次进受判面（`_CUTOFF_SEQ` / `_CUTOFF_DATE`）。
   **为什么不回填历史**：那 60 多个 GOAL 收口时这条纪律还不存在，回填等于**改写历史记录**
   （把今天的要求追认成当时的义务），且会让本轮为了凑绿去批量改旧记录 —— 那正是
   GOAL-092 诊断出的「只补事实，下一轮还会以别的面貌出现」的反面。老 GOAL 的记账粒度
   问题由各自的 RECHECK 承担，不由本判据追认。

**射程边界（如实登记）**：

- 本判据**不读 git 历史**。CI 的 `actions/checkout` 默认 `fetch-depth: 1`（实测：
  `m0-quality.yml` 六处 checkout 均未声明 depth）⇒ 在 CI 里只有 HEAD 一个提交，
  任何「数这一轮有多少提交」的判据在 CI 上都会**恒真**（空真）。所以这里判的是
  **台账与日志两份记录之间的关系**，不是「台账是否穷尽了 git」。
  「穷尽 git」那一面由收口复检在本机取证（`git log --oneline <baseline>..HEAD` 逐条对账）。
- 本判据**不判**台账的**结论**对不对（run 真实终态由 CI 侧取证），也不判 cycle 行的
  「修复 / 剩余差距」写得是否如实 —— 那是各 GOAL 的 RECHECK 面。
"""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_GOALS = _ROOT / ".cursor" / "plans" / "goals"
_CHARTER = _GOALS / "MAINLINE.md"

#: 终态取值（与 `tests/tooling/test_mainline_research_ladder_advances.py` 同源）。
_TERMINAL = frozenset({"ACHIEVED", "BLOCKED", "ABORTED"})

#: **祖父条款**：本判据落地 = 序 62（GOAL-20261022-062）⇒ 只判序 ≥ 61 的轮次。
#: 取 61（而不是 62）是**有意**的：序 61（GOAL-093）的记账粒度正是本轮的**受判对象**
#: —— 它必须在**新判据下**通过，否则判据从第一天起就没有真实受判对象（空真的绿不算收口）。
_CUTOFF_SEQ = 61
_CUTOFF_DATE = "2026-10-22"

#: 台账与日志里提交哈希的形态（**反引号包裹**；仓内 17 行的既有形态逐字如此）。
_COMMIT = re.compile(r"`([0-9a-f]{7,40})`")


def _charter_text() -> str:
    assert _CHARTER.is_file(), f"宪章不在树：{_CHARTER.relative_to(_ROOT)}"
    return _CHARTER.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    """某个二级小节的正文（到下一个 `## ` 为止；缺节 ⇒ 空串）。

    **标题只认行首**（不是任意位置的子串）：实测抓到的形态是某一行**正文里**写了
    `` `## CI 台账` ``（反引号包着的引用），而朴素的 `find` 会把它当成小节起点 ⇒ 小节被
    提前截断，判词变成「缺少 CI 台账表格」（看似受判面缺节，实则读法错误）。
    与 `## 迭代日志` 同理：正文里提到另一个小节的**名字**不该改变解析。
    """
    lines = text.splitlines(keepends=True)
    start: int | None = None
    for index, line in enumerate(lines):
        if line.rstrip("\r\n") == heading:
            start = index
            break
    if start is None:
        return ""
    body: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        body.append(line)
    return "".join(body)


def _cells(line: str) -> list[str]:
    """表格行 → 格（**保留反引号**：提交哈希的形态就是反引号包裹的）。"""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _separator(cells: list[str]) -> bool:
    return bool(cells) and all(set(cell) <= set("-: ") and cell for cell in cells)


def _table(section: str) -> tuple[list[str] | None, list[list[str]]]:
    """小节里的**第一张**表 ⇒ `(表头, 数据行)`；没有表 ⇒ `(None, [])`。

    **遇到表格结束就停**（不把后续表格的列头当数据行）：一个小节里可以有第二张表
    （GOAL-094 的 `## CI 台账` 之后紧跟 `## 状态历史` 时不会串，但同一小节的第二张表会）——
    实测抓到的形态是「把 `| 日期 | 状态 | 说明 |` 这样的**另一张表的列头**当成台账数据行」，
    于是判词说「第 2 行的 `提交` 格里没有哈希」。表格边界的判法：**连续**的 `|` 行，
    且列数与表头一致；不连续（中间有空行或别的行）或列数变化 ⇒ 这一张表结束。
    """
    header: list[str] | None = None
    rows: list[list[str]] = []
    for line in section.splitlines():
        if not line.startswith("|"):
            if header is not None:
                break  # 表已结束：非表行之后的内容属于别的东西
            continue
        cells = _cells(line)
        if _separator(cells):
            continue
        if header is None:
            header = cells
            continue
        if len(cells) != len(header):
            break  # 列数变了 ⇒ 这是**另一张表**的列头，不是本表的数据行
        rows.append(cells)
    return header, rows


def _column(header: list[str], name: str, label: str) -> int:
    """按**列名**定位（不按位置猜）；缺列 ⇒ 点名失败。"""
    if name not in header:
        raise AssertionError(f"{label} 表的列头里没有 {name!r}（读到 {header}）")
    return header.index(name)


def _commits(cell: str) -> list[str]:
    return _COMMIT.findall(cell)


def _ledger_commits(goal_text: str, problems: list[str]) -> list[str]:
    """`## CI 台账` 的 `提交` 列 → 逐行哈希（每行必须至少写一个 ⇒ 否则点名）。"""
    header, rows = _table(_section(goal_text, "## CI 台账"))
    if header is None:
        problems.append("缺少 `## CI 台账` 表格（终态 GOAL 必须逐提交记台账）")
        return []
    index = _column(header, "提交", "CI 台账")
    found: list[str] = []
    for number, row in enumerate(rows, start=1):
        cell = row[index] if index < len(row) else ""
        hashes = _commits(cell)
        if not hashes:
            problems.append(f"CI 台账第 {number} 行的 `提交` 格里没有反引号包裹的提交哈希")
        found.extend(hashes)
    return found


def _log_commits(goal_text: str, problems: list[str]) -> list[str]:
    """`## 迭代日志` 的 `commits` 列 → 逐行哈希（**只认这一列**）。"""
    header, rows = _table(_section(goal_text, "## 迭代日志"))
    if header is None:
        problems.append("缺少 `## 迭代日志` 表格（无法对账）")
        return []
    index = _column(header, "commits", "迭代日志")
    if not rows:
        problems.append("迭代日志没有数据行（逐 cycle 一行是契约）")
    found: list[str] = []
    for row in rows:
        found.extend(_commits(row[index] if index < len(row) else ""))
    return found


def ledger_problems(goal_text: str) -> list[str]:
    """**唯一谓词**：该 GOAL 的台账 → 日志覆盖问题（空列表 = 通过）。

    单独成函数是为了让反证能在**合成文本**上跑（不必改真树），而正例与反例
    走的是**同一个**谓词 —— 否则「红来自事实」与「红来自另一段代码」分不开。
    """
    problems: list[str] = []
    ledgered = _ledger_commits(goal_text, problems)
    logged = set(_log_commits(goal_text, problems))
    if not ledgered:
        problems.append("CI 台账里一个提交都没有 ⇒ 本条失去判据对象（空真不算通过）")
    unlogged = sorted({item for item in ledgered if item not in logged})
    if unlogged:
        problems.append(
            f"CI 台账里的 {len(unlogged)} 个提交没有任何 cycle 行的 `commits` 格收录：{unlogged}"
        )
    return problems


def _frontmatter_value(text: str, key: str) -> str | None:
    """frontmatter 里的**顶层**键（缩进行不算：EC 块里也有 `status:`）。"""
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    for line in parts[1].splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    return None


def _program_seq(goal_id: str) -> int | None:
    """该 GOAL 在宪章程序表里的**序**（不在表里 ⇒ None）。"""
    header, rows = _table(_section(_charter_text(), "## 程序表"))
    if header is None:
        return None
    index = _column(header, "GOAL id", "程序表")
    for row in rows:
        if index < len(row) and row[index] == goal_id:
            try:
                return int(row[0])
            except ValueError:
                return None
    return None


def _scope_reason(goal_id: str, created_at: str) -> str | None:
    """进受判面 ⇒ 返回理由串（进失败消息）；不进 ⇒ None。"""
    seq = _program_seq(goal_id)
    if seq is not None:
        return f"序 {seq}" if seq >= _CUTOFF_SEQ else None
    if created_at >= _CUTOFF_DATE:
        return f"created_at {created_at}"
    return None


def _terminal_goals_in_scope() -> list[tuple[str, str, str]]:
    """树里**终态**且**在受判面内**的 GOAL ⇒ `[(id, 理由, 文本)]`（按 id 排序）。"""
    found: list[tuple[str, str, str]] = []
    for path in sorted(_GOALS.glob("GOAL-*.md")):
        text = path.read_text(encoding="utf-8")
        goal_id = _frontmatter_value(text, "id") or ""
        if _frontmatter_value(text, "status") not in _TERMINAL:
            continue
        reason = _scope_reason(goal_id, _frontmatter_value(text, "created_at") or "")
        if reason is not None:
            found.append((goal_id, reason, text))
    return found


def test_every_terminal_goal_in_scope_ledgers_its_commits_in_a_cycle_row() -> None:
    """**核心**：受判面内每个终态 GOAL 的台账提交，都被某条 cycle 行收录。"""
    goals = _terminal_goals_in_scope()
    assert goals, "受判面为空 ⇒ 本条失去判据对象（空真不算通过）"
    problems = [
        f"{goal_id}（{reason}）：{problem}"
        for goal_id, reason, text in goals
        for problem in ledger_problems(text)
    ]
    assert problems == [], "台账与迭代日志对不上：\n" + "\n".join(problems)


def test_the_scope_reaches_this_generation_and_skips_the_grandfathered_ones() -> None:
    """祖父条款**两向**：序 61 在受判面内；序 60（前一世代）被如实跳过。

    两向都要断言 —— 只断言「093 在内」时，若 `_scope_reason` 恒返回理由（= 不回填条款
    写成了「全判」），历史 GOAL 会一起进受判面而被本轮的记录改写连坐，而本条仍绿。
    """
    goals = {goal_id: reason for goal_id, reason, _text in _terminal_goals_in_scope()}
    assert "GOAL-20261022-093" in goals, (
        "序 61 必须在受判面内 —— 它的记账粒度正是本判据的第一个真实受判对象"
    )
    assert goals["GOAL-20261022-093"] == f"序 {_CUTOFF_SEQ}"
    early: dict[str, int] = {}
    for goal_id in goals:
        seq = _program_seq(goal_id)
        if goal_id != "GOAL-20261022-093" and seq is not None and seq < _CUTOFF_SEQ:
            early[goal_id] = seq
    assert early == {}, f"这些更早的轮次不该进受判面：{early}"
    # 前一世代（序 60 = GOAL-092，2026-10-21 收口）必须**不在**受判面内：它的记账
    # 粒度过的是自己那份 `_log_verdicts`，本轮不回填。
    assert "GOAL-20261021-092" not in goals, sorted(goals)
    assert _scope_reason("GOAL-20261021-092", "2026-10-21") is None
    assert _scope_reason("GOAL-20261022-093", "2026-10-22") == "序 61"
    # 不在程序表里但 created_at 够新 ⇒ 按日期纳入（新 GOAL 建档即受判，不必等登记）。
    assert _scope_reason("GOAL-20990101-999", "2026-10-22") == "created_at 2026-10-22"


def test_the_predicate_bites_both_ways_on_synthetic_records() -> None:
    """反证：**同一条谓词**在合成记录上红 / 绿（真树绿不能证明它会咬）。"""
    good = _sample(
        ledger=("`aaaaaaa`", "`bbbbbbb`"),
        log=("`aaaaaaa` → `bbbbbbb`",),
    )
    assert ledger_problems(good) == []

    # 一向：把日志压成一行（丢掉整条 cycle）⇒ 判红并**点名**缺席的提交
    compressed = _sample(ledger=("`aaaaaaa`", "`bbbbbbb`"), log=("`aaaaaaa`",))
    problems = ledger_problems(compressed)
    assert problems, "压缩日志必须判红"
    assert "`bbbbbbb`".strip("`") in problems[0], problems

    # 另一向：从 cycle 行里删掉一个提交 ⇒ 判红并点名它
    dropped = _sample(ledger=("`aaaaaaa`", "`bbbbbbb`"), log=("`bbbbbbb`",))
    assert any("aaaaaaa" in problem for problem in ledger_problems(dropped))


def test_a_commit_written_outside_the_commits_column_does_not_count() -> None:
    """**只认 `commits` 列**：同一行 `修复` 格里出现该哈希不算收录（散文掩蔽）。"""
    goal = _sample(ledger=("`aaaaaaa`",), log=("（未提交）",), fix="`aaaaaaa`")
    assert any("aaaaaaa" in problem for problem in ledger_problems(goal))


def test_an_empty_ledger_or_an_unattributed_row_is_not_evidence() -> None:
    """空台账 / 台账行没写提交 / 日志没有数据行 —— 三者**分别**点名（不许空真）。"""
    empty = _sample(ledger=(), log=("`aaaaaaa`",))
    assert any("一个提交都没有" in problem for problem in ledger_problems(empty))
    unattributed = _sample(ledger=("（未提交）",), log=("`aaaaaaa`",))
    assert any("没有反引号包裹的提交哈希" in problem for problem in ledger_problems(unattributed))
    no_rows = _sample(ledger=("`aaaaaaa`",), log=())
    assert any("没有数据行" in problem for problem in ledger_problems(no_rows))


def test_a_missing_section_is_named_not_skipped() -> None:
    """缺小节 ⇒ 点名（而不是「找不到就跳过」的静默恒真）。"""
    assert any("## CI 台账" in problem for problem in ledger_problems("## 迭代日志\n\n没有表"))
    assert any("## 迭代日志" in problem for problem in ledger_problems("## CI 台账\n\n没有表"))


def _sample(ledger: tuple[str, ...], log: tuple[str, ...], fix: str = "") -> str:
    """合成一份 GOAL 正文（两张表，列头与真实 GOAL 逐字一致）。"""
    lines = [
        "## 迭代日志",
        "",
        "| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    lines += [
        f"| {number} | PLAN | {cell} | — | — | {fix} | — | — |"
        for number, cell in enumerate(log, start=1)
    ]
    lines += [
        "",
        "## CI 台账",
        "",
        "| 提交 | run | 结论 | 说明 |",
        "| --- | --- | --- | --- |",
    ]
    lines += [f"| {cell} | — | — | — |" for cell in ledger]
    return "\n".join(lines) + "\n"


def test_a_second_table_in_the_same_section_is_not_read_as_ledger_rows() -> None:
    """**表格边界**：同一小节里的第二张表不得被当成本表的数据行。

    实测形态（本判据第一次跑到自己身上时抓到的**真缺陷**）：GOAL 的 `## CI 台账` 之后
    紧跟 `## 状态历史`，而当时的 `_table` 在整个小节里**继续收集** `|` 行 ⇒ 把
    `| 日期 | 状态 | 说明 |` 这样的**另一张表的列头**当成了台账数据行，判词说
    「第 2 行的 `提交` 格里没有哈希」。表格边界 = **连续**的 `|` 行 + 列数一致。
    """
    goal = (
        "## CI 台账\n\n"
        "| 提交 | run | 结论 | 说明 |\n"
        "| --- | --- | --- | --- |\n"
        "| `aaaaaaa` | — | — | — |\n"
        "\n"
        "| 日期 | 状态 | 说明 |\n"
        "| --- | --- | --- |\n"
        "| 2026-01-01 | ACTIVE | 甲 |\n"
        "\n"
        "## 迭代日志\n\n"
        "| # | 子 PLAN | commits |\n"
        "| --- | --- | --- |\n"
        "| 1 | PLAN | `aaaaaaa` |\n"
    )
    assert ledger_problems(goal) == [], ledger_problems(goal)
    # 单元面：两张表都在同一个小节里（中间只有空行）
    header, rows = _table(
        "| 提交 | run |\n| --- | --- |\n| `aaaaaaa` | — |\n\n| 日期 | 状态 |\n| --- | --- |\n"
    )
    assert header == ["提交", "run"], header
    assert rows == [["`aaaaaaa`", "—"]], rows


def test_a_heading_quoted_inside_prose_does_not_start_a_section() -> None:
    """**标题只认行首**：正文里提到另一个小节的**名字**不该改变解析。

    实测形态（本判据第二次跑到自己身上时抓到的**真缺陷**）：某一 cycle 行的正文里写了
    `` `## CI 台账` ``（反引号包着的引用），而朴素的 `find` 把它当成小节起点 ⇒ 小节被
    提前截断，判词变成「缺少 CI 台账表格」—— 看似受判面缺节，实则读法错误。
    """
    text = (
        "## 迭代日志\n\n"
        "| # | commits |\n"
        "| --- | --- |\n"
        "| 1 | `aaaaaaa` |\n"
        "并同时说明 `## CI 台账` 那一节的要求。\n"
        "\n"
        "## CI 台账\n\n"
        "| 提交 | run |\n"
        "| --- | --- |\n"
        "| `aaaaaaa` | — |\n"
    )
    log = _section(text, "## 迭代日志")
    assert "`aaaaaaa`" in log
    ledger = _section(text, "## CI 台账")
    assert "| `aaaaaaa` | — |" in ledger, ledger
    assert ledger_problems(text) == [], ledger_problems(text)
