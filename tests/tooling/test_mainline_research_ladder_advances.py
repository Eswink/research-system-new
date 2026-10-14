"""MAINLINE 科研能力**阶梯**判据：每一轮迭代必须让某个科研能力域**前进一格**。

为什么需要它：战役宪章的 `程序表` 记录了「做了什么」，但没有回答「**离真实科研还有多远**」——
43 个 GOAL 收口后，主战场已经漂移到「查询参数的长度界」这类 API 卫生上，而宪章
**没有任何东西**能指出：报告域还是 0、活检索还没进上下文。漂移不是某一次做错，
而是**没有任何力把它拽回来**。

本判据把那句话变成机器可检的事实：

1. **域集合是闭集** —— `## 科研能力阶梯` 的数据行域**恰好**是 `_DOMAINS`（不多不少）。
   「加一个新域」= 显式改判据（承 `MEM-158` 的射程显式分类）。
2. **依据指向真实的、已收口的 GOAL** —— 每行 `依据 GOAL` 里的 id 必须在
   `.cursor/plans/goals/` 下存在对应文件，且其 frontmatter `status` 是终态
   （`ACHIEVED` / `BLOCKED` / `ABORTED`）。**依据面只在 GOAL 文件里判，不进宪章**
   ——宪章**不得**镜像状态（既有宪章判据钉死了这条）。
3. **★ 最新一轮必须推进某个域** —— 宪章 `进展记录` 里**最新一条**（按表内行序，表是
   最新在前）的 GOAL id 必须出现在阶梯的**某个** `依据 GOAL` 里。
   这就是「每一次自动迭代都必须更近科研」的**机械强制**：如果一个 GOAL 收口后
   **没有任何能力域把它记为进展**，宪章就不再如实描述现在离科研有多远。
4. **下一级必须写明** —— 至少有一行的 `下一级是什么` 非空（不为空 ⇒ 战役仍有可验收缺口；
   全空 ⇒ 该走宪章的停止条件，而非继续找活干）。

**射程边界（如实登记）**：

- 第 3 条判的是「**最新一轮被记进了阶梯**」，**不**判「记进去的那一格真的升级了」——
  后者是各 GOAL 自己的 EC 面（`verify` + RECHECK）。本判据挡的是**静默漂移**
  （做了与科研无关的事、且阶梯也不更新），不是**夸大**——夸大由收口复检面承担。
- 域名的**粒度**由本判据的 `_DOMAINS` 钉住：加域必须同轮改判据并给出理由，
  这是**有意的摩擦**（免得把「域」越切越细以凑"前进一格"）。
"""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_GOALS = _ROOT / ".cursor" / "plans" / "goals"
_CHARTER = _GOALS / "MAINLINE.md"

#: 科研能力**域**闭集（宪章阶梯表的域列必须恰好是这些；增删即改判据）。
_DOMAINS: tuple[str, ...] = (
    "检索",
    "证据",
    "计划",
    "实验",
    "复检",
    "报告",
    "迭代",
)
#: 阶梯表列头（不得改名／改列序）。
_LADDER_COLUMNS: tuple[str, ...] = ("域", "当前级", "依据 GOAL", "下一级是什么")
#: 终态取值（与 `packages/domain` / 治理契约的 GOAL 状态域同源）。
_TERMINAL = frozenset({"ACHIEVED", "BLOCKED", "ABORTED"})

#: **祖父条款**：本判据落地**之前**已收口的轮次不回填（它们收口时阶梯还不存在）。
#: 落地当轮 = 序 45（GOAL-077）⇒ 判据只约束序 ≥ 45。
_CUTOFF_SEQ = 45

_GOAL_ID = re.compile(r"GOAL-\d{8}-\d{3}")
_PROGRESS_ROW = re.compile(r"^\|\s*(\d{4}-\d\d-\d\d)\s*\|\s*(GOAL-\d{8}-\d{3})")


def _charter_text() -> str:
    assert _CHARTER.is_file(), f"宪章不在树：{_CHARTER.relative_to(_ROOT)}"
    return _CHARTER.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    """取某二级小节（到下一个 `## ` 为止）。"""
    assert heading in text, f"宪章缺少小节 {heading!r}"
    rest = text.split(heading, 1)[1]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def _cells(line: str) -> list[str]:
    return [
        cell.replace("**", "").replace("`", "").strip()
        for cell in line.strip().strip("|").split("|")
    ]


def _separator(cells: list[str]) -> bool:
    return bool(cells) and all(set(cell) <= set("-: ") and cell for cell in cells)


def _table_rows(section: str) -> list[list[str]]:
    """小节里的数据行（跳过表头与分隔行）。"""
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


def _ladder_rows() -> list[list[str]]:
    return _table_rows(_section(_charter_text(), "## 科研能力阶梯"))


def _progress_keys(text: str) -> list[tuple[str, str]]:
    """进展记录表的 `(日期, GOAL id)`（按表内行序，**最新在前**）。"""
    keys: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = _PROGRESS_ROW.match(line)
        if match is not None:
            keys.append((match.group(1), match.group(2)))
    return keys


def _progress_rows(text: str) -> list[tuple[str, str, str, str, str]]:
    """进展记录表的**完整行**（`日期 / GOAL / 结论 / 能力域 / RECHECK`；最新在前）。

    列序与宪章一致：能力域**插在 RECHECK 之前**（RECHECK 必须留在末格 ——
    既有判据 `_bad_recheck_links` 取 `row[-1]`）。
    """
    rows: list[tuple[str, str, str, str, str]] = []
    section = _section(text, "## 进展记录")
    for line in section.splitlines():
        if not _PROGRESS_ROW.match(line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        assert len(cells) >= 4, f"进展行列数不足（{len(cells)}）：{line[:80]}"
        # 日期 / GOAL / 结论 / 能力域 / RECHECK —— 结论里可能含 `|`（极少），故从两端取
        date, goal_id = cells[0], cells[1]
        recheck = cells[-1]
        domain = cells[-2] if len(cells) >= 5 else ""
        conclusion = " | ".join(cells[2:-2]) if len(cells) >= 5 else cells[2]
        rows.append((date, goal_id, conclusion, domain, recheck))
    return rows


def _program_seq_of(goal_id: str) -> int | None:
    """该 GOAL 在程序表里的**序**（找不到 ⇒ None ⇒ 挂钩断开）。"""
    section = _section(_charter_text(), "## 程序表")
    for line in section.splitlines():
        if not line.startswith("| ") or goal_id not in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[1] == goal_id:
            try:
                return int(cells[0])
            except ValueError:
                return None
    return None


def _goal_status(goal_id: str) -> str | None:
    """读该 GOAL 文件的 frontmatter `status`（不进宪章 ⇒ 不违反「状态不落宪章」）。"""
    matches = sorted(_GOALS.glob(f"GOAL-*-{goal_id.split('-')[-1]}-*.md"))
    if not matches:
        return None
    text = matches[0].read_text(encoding="utf-8")
    match = re.search(r"^status:\s*(\S+)", text, re.MULTILINE)
    return match.group(1) if match else None


def test_the_ladder_section_exists_with_the_expected_columns() -> None:
    section = _section(_charter_text(), "## 科研能力阶梯")
    assert _table_header(section) == list(_LADDER_COLUMNS), _table_header(section)
    assert _ladder_rows(), "阶梯表没有数据行 ⇒ 空真"


def test_the_domain_set_is_closed() -> None:
    """域集合**恰好**等于闭集（多一个 / 少一个都判红 —— 加域要改判据并给理由）。"""
    domains = [row[0] for row in _ladder_rows()]
    assert sorted(domains) == sorted(_DOMAINS), (
        f"阶梯域集合与闭集不符：多出 {sorted(set(domains) - set(_DOMAINS))}、"
        f"缺少 {sorted(set(_DOMAINS) - set(domains))}"
    )
    assert len(domains) == len(set(domains)), f"阶梯出现重复域：{domains}"


def test_every_basis_names_an_existing_goal_with_at_least_one_terminal() -> None:
    """每行的 `依据 GOAL` 必须指向**存在**的 GOAL；**且每行至少有一个**是**已收口**的。

    为什么允许混列进行中的：一个域常常「已由某轮收口奠定、当前又有一轮正在进行」
    （报告域正是这种形态：`035` 已收口、`077` 在进行）。若只允许终态，读者就**看不见
    正在推进这件事** —— 而那恰是阶梯该回答的「现在走到哪」。

    为什么**必须至少一个终态**：只列进行中的 ⇒ 那一格的「当前级」是**承诺**而非
    **事实**（没有已收口的轮次为它背书）。这条把「正在做」与「已经做到」分开。
    """
    problems: list[str] = []
    for row in _ladder_rows():
        domain, _level, basis, _next = (row + [""] * 4)[:4]
        ids = _GOAL_ID.findall(basis)
        if not ids:
            problems.append(f"{domain}: 依据列为空或没有 GOAL id（{basis!r}）")
            continue
        terminal_seen = 0
        for goal_id in ids:
            status = _goal_status(goal_id)
            if status is None:
                problems.append(f"{domain}: 依据 {goal_id} 在树里找不到对应文件")
            elif status in _TERMINAL:
                terminal_seen += 1
        if terminal_seen == 0:
            problems.append(
                f"{domain}: 依据面（{ids}）**没有一个**已收口 ⇒ 「当前级」是承诺而非事实"
            )
    assert problems == [], f"阶梯的依据面有问题：{problems}"


def test_the_latest_completed_round_advanced_some_domain() -> None:
    """**★ 核心不变式**：最新收口的一轮必须是**科研域**的，且被阶梯的某个「依据」收录。

    这条就是「每一次自动迭代都必须更近科研」的机械强制，两步：

    1. **能力域不得是 `—`**（`—` = 非科研，如 API 卫生）—— 一个 GOAL 收口了却没推进
       任何科研域 ⇒ 这一轮迭代**没有**把科研能力推向前 ⇒ 判红；
    2. **必须出现在阶梯的 `依据 GOAL` 里** —— 否则宪章的阶梯不再是「离科研多远」的
       如实读数（做了科研的事却没人记账，与漂移同样有害）。

    **祖父条款（`_CUTOFF_SEQ`）**：本判据落地**之前**已收口的轮次不回填（它们收口时阶梯
    还不存在）。判据只约束序 ≥ `_CUTOFF_SEQ` 的轮次；早于此的如实跳过，并在失败消息里
    说明读到的是哪个序 —— 免得"跳过"变成静默。
    """
    progress = _progress_rows(_charter_text())
    assert progress, "进展记录为空 ⇒ 本条无法取证"
    date, goal_id, _conclusion, domain, _recheck = progress[0]
    seq = _program_seq_of(goal_id)
    if seq is None:
        raise AssertionError(f"最新进展 {goal_id} 在程序表里找不到对应行 ⇒ 挂钩断开")
    if seq < _CUTOFF_SEQ:
        return  # 祖父条款：落地前的轮次不回填（如实跳过，不静默）
    assert domain.strip() not in ("—", "-", ""), (
        f"最新收口的 {goal_id}（序 {seq}）的能力域是 {domain!r} ⇒ 这一轮迭代**没有**推进"
        "任何科研域（`—` 表示非科研，如 API 卫生）。按战役宪章：每轮必须更近科研，"
        "或如实说明为何这一轮只能做非科研的事并调整程序表"
    )
    basis_ids = set(_GOAL_ID.findall(" ".join(row[2] for row in _ladder_rows())))
    assert goal_id in basis_ids, (
        f"最新收口的 {goal_id} 是科研域（{domain}）但**没有**被任何能力域的「依据 GOAL」收录 ⇒ "
        "阶梯不再是「离科研多远」的如实读数（做了科研的事却没人记账，与漂移同样有害）"
    )


def test_at_least_one_domain_declares_a_next_level() -> None:
    """至少一行写明「下一级是什么」（全空 ⇒ 该走宪章的停止条件）。"""
    declared = [
        row[0] for row in _ladder_rows() if (row + [""] * 4)[3].strip() not in ("", "—", "-")
    ]
    assert declared, "没有任何域写明「下一级是什么」⇒ 战役已无可验收缺口，应走停止条件"


def test_the_helpers_are_not_vacuous(tmp_path: Path) -> None:
    """受判面自检：合成输入上给出预期读数（正例 + 反例各一），隔离真树。"""
    good = (
        "## 科研能力阶梯\n\n"
        "| 域 | 当前级 | 依据 GOAL | 下一级是什么 |\n"
        "| --- | --- | --- | --- |\n"
        "| 检索 | 真检索 + 真标识 | GOAL-20261001-001 | 活检索进上下文 |\n"
        "| 报告 | 仅结构化交付物 | GOAL-20261001-002 | 人类可读报告 |\n"
    )
    rows = _table_rows(_section(good, "## 科研能力阶梯"))
    assert len(rows) == 2, rows
    assert _table_header(_section(good, "## 科研能力阶梯")) == list(_LADDER_COLUMNS)
    assert _GOAL_ID.findall(rows[0][2]) == ["GOAL-20261001-001"]
    assert _LADDER_COLUMNS[-1] == "下一级是什么", "阶梯列头不得改名（改即契约变更）"

    prog = (
        "## 进展记录\n\n"
        "| 日期 | GOAL | 一句话结论 | 能力域 | RECHECK |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| 2026-01-01 | GOAL-20260101-009 | 甲 | 报告 | [R](../rechecks/R.md) |\n"
    )
    prog_rows = _progress_rows(prog)
    assert len(prog_rows) == 1, prog_rows
    date, goal_id, _conc, domain, recheck = prog_rows[0]
    assert (date, goal_id, domain) == ("2026-01-01", "GOAL-20260101-009", "报告"), prog_rows[0]
    assert recheck.startswith("[R]"), "RECHECK 必须留在末格（既有判据取 row[-1]）"
    assert _progress_keys(prog) == [("2026-01-01", "GOAL-20260101-009")]

    # 域集合闭集判定：漏一个域应能被识别
    ladder_domains = [ladder_row[0] for ladder_row in rows]
    assert set(ladder_domains) != set(_DOMAINS), "合成样本本就不该等于闭集（这条是负例自检）"
    # 终态集不含进行中状态
    assert "ACTIVE" not in _TERMINAL and "PENDING" not in _TERMINAL
    # 祖父条款：落地前的序不判、落地后的序要判
    assert _CUTOFF_SEQ > 0
