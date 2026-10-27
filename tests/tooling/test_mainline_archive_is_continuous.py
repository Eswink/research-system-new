"""MAINLINE 归档连续性判据：活跃面瘦身后，**移出的历史必须仍可复核**。

为什么需要它：`MAINLINE.md` 的两段累积物（进展记录 / 修订记录）是**只追加**的，
轮次越多越长。宪章把「活跃面只保留最近若干条、更早的移入归档」写成惯例，
并**挂判据**——否则「归档」会退化成两种坏形态：

1. **顺手删掉**：移出的行谁也没留下 ⇒ 历史不可复核（`MEM-158` 的「静默逃逸」同族）；
2. **留而不断**：归档文件存在，但内容与 MOVED 声明对不上（少搬 / 多搬 / 搬重）
   ⇒ 读者以为历史在，实际缺一块。

本判据把三件事变成机器可检的事实（缺一即判红）：

1. **MOVED 声明在树且可解析** —— 活跃面提到归档文件名时，该文件必须真实存在；
2. **不漏** —— 归档文件里的进展行数 + 活跃面保留的行数 **≥** 原文该段的行数
   （用 `git show HEAD:<charter>` 取原文；取不到 ⇒ **点名失败**，不静默跳过）；
3. **不重** —— 同一条进展记录（按 `| 日期 | GOAL id |` 前两格）**不得**同时出现在
   活跃面与归档里。

**射程边界（如实登记）**：

- 「不漏」用的是**行数上界**而不是逐行集合相等：原文里同一天同一 GOAL 可能有多行
  （修复 cycle 就是这种形态），逐行集合相等会把正当的重复形态判红。行数上界 +
  「不重」两条合起来足以抓住「少搬」与「搬重」，抓不住的是「搬错行」——
  那一面由归档搬运脚本的 `sha256` 留档承担（记录里引用）。
- 本判据**不**判归档内容的**结论**对不对（那是各 GOAL / RECHECK 面的事）。
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_GOALS = _ROOT / ".cursor" / "plans" / "goals"
_CHARTER = _GOALS / "MAINLINE.md"
_ARCHIVE_DIR = _GOALS / "archive"

#: 进展记录的数据行：`| 日期 | GOAL id … |`。
#: id 后允许括注（修复 cycle 的既有形态逐字是
#: `| 2026-10-09 | GOAL-20261008-040（收口后**纪律回溯修复** cycle） | … |`）
#: ⇒ **不得**要求 id 后紧跟 `|`，否则这类行会被漏判（实测：一条真实记录被判成「谁也没收录」）。
_PROGRESS_ROW = re.compile(r"^\|\s*(\d{4}-\d\d-\d\d)\s*\|\s*(GOAL-\d{8}-\d{3})")
#: 活跃面里指向归档文件的相对链接。
_ARCHIVE_LINK = re.compile(r"\]\((archive/[^)]+\.md)\)")
#: 修订记录数据行的**形状**（容忍竖线后的任意空白 —— 手写常有双空格）。
_REVISION_ROW_SHAPE = re.compile(r"^\|\s*\d{4}-\d\d-\d\d\s*\|")


def _charter_text() -> str:
    assert _CHARTER.is_file(), f"宪章不在树：{_CHARTER.relative_to(_ROOT)}"
    return _CHARTER.read_text(encoding="utf-8")


def _original_charter_text() -> str:
    """取**上一个提交**的宪章文本（原文行数基线）。

    **点名失败**而不是跳过：取不到 ⇒ 判红。跳过会让「不漏」这条在无 git 的环境里
    静默变成恒真。
    """
    result = subprocess.run(
        ["git", "show", "HEAD:.cursor/plans/goals/MAINLINE.md"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 0, (
        "取不到 HEAD 版宪章（`git show`) ⇒ 「不放走历史」这条无法取证；"
        f"stderr={result.stderr.strip()[:200]}"
    )
    return result.stdout


def _progress_keys(text: str) -> list[tuple[str, str]]:
    """进展记录行 → `(日期, GOAL id)`。**取前两格的首个匹配**（id 后可有括注）。"""
    keys: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = _PROGRESS_ROW.match(line)
        if match is not None:
            keys.append((match.group(1), match.group(2)))
    return keys


#: 修订记录的数据行（`| 日期 | 序 | 被替换的行（原文） | …`）—— 与进展行**格数不同**
#: （修订 **5** 格 / 进展 **4** 格）⇒ 用格数把它们分开，**不**靠列内容猜。
def _revision_keys(text: str) -> list[tuple[str, str]]:
    """修订记录行 → `(日期, 序格)`（**只取该节** —— 进展行也在别处出现 5 格表格）。"""
    if "## 修订记录" not in text:
        return []
    section = text.split("## 修订记录", 1)[1]
    keys: list[tuple[str, str]] = []
    for line in section.splitlines():
        if not line.startswith("| 20"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 5:  # 修订行 5 格；进展行 4 格
            keys.append((cells[0], cells[1][:24]))
    return keys


def _archive_paths(charter: str) -> list[Path]:
    """活跃面提到的归档文件（**去重**）。

    去重是**判据正确性的一部分**：同一份归档会被三段指针各提一次（进展 / 修订 / 预算），
    重复计数会让「不漏」的右端虚高（实测：21 行被算成 63 行）⇒ 删掉几行也不会判红。
    """
    seen: dict[str, Path] = {}
    for relative in _ARCHIVE_LINK.findall(charter):
        seen.setdefault(relative, (_GOALS / relative).resolve())
    return list(seen.values())


def _short_revision_rows(text: str) -> list[str]:
    """`## 修订记录` 里**格数不足 5** 的数据行（原样返回，供判据点名）。

    **为什么单列一条判据**（2026-10-27 实测的真缺陷）：`_revision_keys` 用
    `len(cells) >= 5` 把修订行与进展行分开 ⇒ 一条写成 3 格的修订行会被**静默跳过**，
    于是它对「不漏 / 不重」两条判据**完全不可见**：既不会因为缺失而判红，也不会因为
    重复而判红。序 65 的条目就是这样写坏的（`| 日期 | 序 | 说明 |`，3 格），
    在活跃面里待了一整轮而全部判据仍绿 —— 与 GOAL-096 `U-3` 登记的老归档 4 格行同族。

    **射程边界**：本判据只扫**活跃面**（`MAINLINE.md` 的 `## 修订记录`）。
    历史归档里的短行不在此列 —— 那需要逐条判断「原文是否本来就只有那几列」，
    硬补等于编造；它们由各自的记录逐条登记（见 GOAL-096 `U-3` / 序 66 的靶子）。

    **前缀匹配不能用 `startswith("| 20")`**（实测的坑）：那个字面量要求「竖线后
    **恰好一个**空格再跟 `20`」。一条手写成 `|  2026-…`（两个空格）的行会**既不**
    被 `_revision_keys` 收录、**也不**被本判据看到 ⇒ 两条判据同时沉默。这里改用
    正则，让「像不像数据行」由一个明确的正则决定，而不是由空格的个数决定。
    """
    if "## 修订记录" not in text:
        return []
    section = text.split("## 修订记录", 1)[1]
    short: list[str] = []
    for line in section.splitlines():
        if not _REVISION_ROW_SHAPE.match(line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            short.append(line[:120])
    return short


def test_the_archive_claimed_by_the_charter_exists_and_is_not_empty() -> None:
    """活跃面提到的归档文件必须真实存在且非空（否则 MOVED 是一句空话）。"""
    paths = _archive_paths(_charter_text())
    for path in paths:
        assert path.is_file(), f"宪章提到的归档文件不存在：{path.relative_to(_ROOT)}"
        assert path.read_text(encoding="utf-8").strip(), (
            f"归档文件为空：{path.relative_to(_ROOT)}（移出的历史必须有内容）"
        )


def test_no_progress_row_was_dropped_in_the_move() -> None:
    """**不漏**：活跃面保留 + 归档收录 的进展行数 ≥ 原文该段行数。"""
    charter = _charter_text()
    original = _original_charter_text()
    archived = 0
    for path in _archive_paths(charter):
        archived += len(_progress_keys(path.read_text(encoding="utf-8")))
    kept = len(_progress_keys(charter))
    baseline = len(_progress_keys(original))
    # **强判据**（2026-10-13 收紧，与修订面同形）：基线（HEAD 版）里的**每一条**进展行
    # 都必须仍然可复核 —— 要么在活跃面、要么在归档里。只比**行数**会被「归档补上」掩蔽
    # （实测：删一条活跃行而归档行数不变时，行数上界仍成立 ⇒ 假绿）。
    live = set(_progress_keys(charter))
    gone = set(_progress_keys(original)) - live
    for path in _archive_paths(charter):
        gone -= set(_progress_keys(path.read_text(encoding="utf-8")))
    assert gone == set(), (
        f"进展记录**丢了** {len(gone)} 条（既不在活跃面、也不在任何归档）：{sorted(gone)} —— "
        "移出时必须原样搬进归档，不得顺手删"
    )
    assert archived + kept >= baseline, (
        f"进展记录少了 {baseline - archived - kept} 行（原文 {baseline} / "
        f"活跃面保留 {kept} / 归档 {archived}）"
    )


def test_no_progress_row_appears_on_both_sides() -> None:
    """**不重**：同一条进展记录不得同时出现在活跃面与归档里。"""
    charter = _charter_text()
    kept = set(_progress_keys(charter))
    for path in _archive_paths(charter):
        archived = set(_progress_keys(path.read_text(encoding="utf-8")))
        both = sorted(kept & archived)
        assert both == [], (
            f"{path.relative_to(_ROOT)} 与宪章同时收录了同一条进展记录：{both} —— "
            "「移入」意味着只在一处（不重则两处读者会看到两个版本）"
        )


def test_no_revision_row_was_dropped_in_the_move() -> None:
    """**不漏（修订面）**：活跃面保留 + 归档收录 的修订行数 ≥ 原文该段行数。

    **为什么要有这一条**（2026-10-13 实测的 Coverage 缺口）：原判据**只**覆盖进展行
    ⇒ 修订记录**丢行不会被抓到**。本轮实测到一次**真丢失**：连续插入修订行时用了
    「按行替换」而非「追加」，六行（序 27/28/29 / 30 / 31 / 32 / 33 / 34）被逐次**顶掉**
    ⇒ 活跃面长期停在 4 行而**判据全绿**。已从各提交复原并补齐，同时把这一面**纳入受判面**。
    """
    charter = _charter_text()
    original = _original_charter_text()
    archived = 0
    for path in _archive_paths(charter):
        archived += len(_revision_keys(path.read_text(encoding="utf-8")))
    kept = len(_revision_keys(charter))
    baseline = len(_revision_keys(original))
    # **强判据**：基线（HEAD 版）里的**每一条**修订行都必须仍然可复核 ——
    # 要么在活跃面、要么在归档里。只比**行数**会被「归档补上」掩蔽（实测：
    # 删一条活跃行、归档里恰好有同数 ⇒ 行数上界仍成立 ⇒ 假绿）。
    live = set(_revision_keys(charter))
    gone = set(_revision_keys(original)) - live
    for path in _archive_paths(charter):
        gone -= set(_revision_keys(path.read_text(encoding="utf-8")))
    assert gone == set(), (
        f"修订记录**丢了** {len(gone)} 条（既不在活跃面、也不在任何归档）：{sorted(gone)} —— "
        "移出时必须原样搬进归档，且**插入新行时必须是追加**（顶掉旧行正是本轮实测到的形态）"
    )
    assert archived + kept >= baseline, (
        f"修订记录少了 {baseline - archived - kept} 行（原文 {baseline} / "
        f"活跃面保留 {kept} / 归档 {archived}）"
    )


def test_no_revision_row_appears_on_both_sides() -> None:
    """**不重（修订面）**：同一条修订记录不得同时出现在活跃面与归档里。"""
    charter = _charter_text()
    kept = set(_revision_keys(charter))
    for path in _archive_paths(charter):
        archived = set(_revision_keys(path.read_text(encoding="utf-8")))
        both = sorted(kept & archived)
        assert both == [], (
            f"{path.relative_to(_ROOT)} 与宪章同时收录了同一条修订记录：{both} —— "
            "「移入」意味着只在一处"
        )


def test_no_revision_row_in_the_live_table_is_too_short_to_be_seen() -> None:
    """**活跃面**的修订行必须够 5 格 —— 否则它对「不漏 / 不重」两条判据**不可见**。

    这是 2026-10-27 实测到的真缺陷（不是假想）：序 65 的修订行写成
    `| 2026-10-26 | 序 65 / GOAL-… | 说明 |`（**3 格**），而 `_revision_keys` 用
    `len(cells) >= 5` 区分修订行与进展行 ⇒ 它被静默跳过，于是「移出时会不会丢」
    与「两处并存」这两条判据都对它**无话可说**。它在活跃面待了一整轮、全部判据皆绿。

    这与 `test_the_helpers_are_not_vacuous` 里那条「进展行 4 格不得被当成修订行」
    是同一把尺子的另一面：**跳过**是正确语义（两类行格数不同），但**沉默**不是
    —— 所以短行必须被单独点名，而不是被合法地忽略。
    """
    short = _short_revision_rows(_charter_text())
    assert short == [], (
        f"`## 修订记录` 有 {len(short)} 行不足 5 格 ⇒ 它们对「不漏 / 不重」判据不可见"
        "（`_revision_keys` 会静默跳过）：\n" + "\n".join(short)
    )


def test_the_short_revision_row_judge_catches_a_real_short_row(tmp_path: Path) -> None:
    """**反证臂**：合成一条 3 格的修订行 ⇒ 判据必须点名它（不是空真）。"""
    text = (
        "## 修订记录\n\n| 日期 | 序 | 被替换的行（原文） | 替换为 | 理由 |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| 2026-01-01 | 7（新增） | （无替换） | 序 7 | 理由 |\n"
        "| 2026-01-02 | 序 8 / GOAL-20260102-008 | 只有三格的说明 |\n"
    )
    short = _short_revision_rows(text)
    assert len(short) == 1, short
    assert "序 8" in short[0], short


def test_the_helpers_are_not_vacuous(tmp_path: Path) -> None:
    """受判面自检：合成输入上给出预期读数（正例 + 反例），隔离真树。"""
    good = (
        "| 2026-01-01 | GOAL-20260101-001 | 甲 | [R](../rechecks/R.md) |\n"
        "| 2026-01-02 | GOAL-20260102-002 | 乙 | [R](../rechecks/R.md) |\n"
    )
    keys = _progress_keys(good)
    assert keys == [("2026-01-01", "GOAL-20260101-001"), ("2026-01-02", "GOAL-20260102-002")]
    assert _progress_keys("| 序 | GOAL id | 轴 | 一句话目标 | 依赖 |\n") == [], (
        "程序表行不应被当进展记录（它没有日期格）"
    )
    assert _ARCHIVE_LINK.findall("见 [A](archive/X.md) 与 [B](archive/Y.md)") == [
        "archive/X.md",
        "archive/Y.md",
    ]
    assert _ARCHIVE_LINK.findall("见 [R](../rechecks/R.md)") == [], "复检链接不是归档链接"
    rev = (
        "## 修订记录\n\n| 日期 | 序 | 被替换的行（原文） | 替换为 | 理由 |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| 2026-01-01 | 7（新增） | （无替换） | 序 7 | 理由 |\n"
    )
    assert _revision_keys(rev) == [("2026-01-01", "7（新增）")], _revision_keys(rev)
    assert (
        _revision_keys("| 2026-01-01 | GOAL-20260101-001 | 甲 | [R](../rechecks/R.md) |") == []
    ), "进展行（4 格）不得被当成修订行"
