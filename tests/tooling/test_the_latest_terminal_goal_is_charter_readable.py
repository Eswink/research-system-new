"""GOAL-20261117-114 EC-01：**最新一轮的残余必须真的能被下一轮读出来**。

**它补哪一道缝**（本轮勘测实测）：`tools/next_round_charter.py` 是「上一轮 GOAL → 下一轮
charter」的确定性读取器，宪章的「迭代」行据此宣称「下一轮的输入由上一轮残余机械派生」。
但读取器读的是 GOAL 的 `## 残余与未覆盖范围` 小节；**113 份 GOAL 里只有 35 份有这个节**
（077…112 基本连续，095 与 113 缺）。GOAL-113 写了 `W-1`、`RECHECK-113` 也逐条登记了它，
但**节本身缺席** ⇒ 读取器抛 `RESIDUAL_SECTION_MISSING`、`exit 2`、不写盘。

**为什么既有判据没抓到**：`tools/verify_goal113_closeout.py` 只判 `` `W-1` `` 这个**子串**
在文件里（出现 3 次 ⇒ 绿）。「残余写没写」与「读取器读不读得到」是两件事，子串判据把
前者当成了后者 —— 与 GOAL-082 的混淆论证同一形态（**在场** ≠ **可读**）。

**判什么**（缺一即判红）：

1. **最新一轮可读**：编号最大的**终态** GOAL 必须能被 `build_skeleton` 读出非空骨架
   （不是「节存在」，而是**真的跑通整条读取链**：终态 → 复检 → 阶梯收录 → 残余逐条）；
2. **残余逐条在场**：产出的「二、」节里 `W` 条目数 == GOAL 文件里边首 `W` 条目数
   （读取器**不丢**；「读出来但少一条」与「读不到」同样是断链）；
3. **反证臂（节缺席 ⇒ 拒）**：合成树里删掉整个小节 ⇒ 读取器**必须**抛
   `RESIDUAL_SECTION_MISSING`（证明判据 1 不是无条件绿）；
4. **反证臂（断号 ⇒ 拒）**：合成树里删掉首条 `W` 却留着后面的编号 ⇒ 必须抛
   `RESIDUAL_GAP`（证明第 2 条不是在数「碰巧等于」）。

**射程边界（如实登记）**：本判据**只覆盖最新一轮**，不回溯 78 份历史 GOAL。理由与
`test_terminal_goals_have_closeout_verifiers.py` 的祖父条款同源：回填旧记录等于把今天的
要求追认成历史义务，且会让本轮为凑绿去批量补文件。历史缺口登记在 GOAL-114 的残余节。
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "next_round_charter.py"
GOALS_DIR = ROOT / ".cursor" / "plans" / "goals"
RESIDUAL_HEADING = "## 残余与未覆盖范围"
NEXT_ID = "GOAL-20261117-901"

#: 终态词表（与 `charter_parse.TERMINAL` 同源；此处置一份**判据自己的**读法）。
_TERMINAL = frozenset({"ACHIEVED", "BLOCKED", "ABORTED"})
#: 条目起头（两种形态都认，与 `charter_parse._W_ITEM` 同一放宽方向）。
_W_ITEM = re.compile(r"^- (?:\*\*)?`W-(\d+)`(?:\*\*)?")
_GOAL_FILE = re.compile(r"^GOAL-\d{8}-(\d{3})-.*\.md$")
_STATUS = re.compile(r"^status:\s*(\S+)\s*$", re.MULTILINE)


def _load(path: Path, name: str) -> ModuleType:
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, f"无法加载 {path}"
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def _reader() -> ModuleType:
    return _load(TOOL, "goal114_next_round_charter")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _status(text: str) -> str:
    if not text.startswith("---"):
        return ""
    match = _STATUS.search(text.split("---", 2)[1])
    return match.group(1) if match is not None else ""


def _latest_terminal_goal() -> Path:
    """编号最大的**终态** GOAL 文件（本判据的受判对象；找不到 ⇒ 判据自己点名失败）。"""
    candidates: list[tuple[int, Path]] = []
    for path in GOALS_DIR.glob("GOAL-*.md"):
        match = _GOAL_FILE.match(path.name)
        if match is not None and _status(_text(path)) in _TERMINAL:
            candidates.append((int(match.group(1)), path))
    assert candidates, "没有任何终态 GOAL ⇒ 本判据失去对象（空真不算通过）"
    return max(candidates)[1]


def _section(text: str, heading: str) -> list[str] | None:
    """某个二级小节的行（判据自己的切分，**不调被测实现**）。"""
    lines = text.splitlines()
    start = next((index + 1 for index, line in enumerate(lines) if line.startswith(heading)), None)
    if start is None:
        return None
    body: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    return body


def _w_numbers(text: str) -> list[int]:
    body = _section(text, RESIDUAL_HEADING)
    if body is None:
        return []
    return [int(match.group(1)) for line in body if (match := _W_ITEM.match(line)) is not None]


#: 骨架里残余节的标题（与 GOAL 里的不同：带序号与括注）——**判据自己的**读法。
_PRODUCED_HEADING = "## 二、"


def _produced_w_numbers(text: str) -> list[int]:
    """骨架文本里「二、」节的 `W` 编号（读取器的产出面，不是 GOAL 正文）。"""
    body = _section(text, _PRODUCED_HEADING)
    if body is None:
        return []
    return [int(match.group(1)) for line in body if (match := _W_ITEM.match(line)) is not None]


def _skeleton(root: Path, goal_name: str) -> str:
    reader = _reader()
    return reader.build_skeleton(root, f".cursor/plans/goals/{goal_name}", NEXT_ID)  # type: ignore[no-any-return]


def test_the_latest_terminal_goal_is_readable() -> None:
    """编号最大的终态 GOAL 必须能跑通整条读取链（不是「节存在」）。"""
    goal = _latest_terminal_goal()
    text = _skeleton(ROOT, goal.name)
    assert "## 二、上一轮的残余与未覆盖范围" in text, (
        f"{goal.name} 的骨架里没有残余节 ⇒ 读取器没有真的读出残余"
    )


def test_the_read_residuals_are_not_fewer_than_the_written_ones() -> None:
    """读出来的 `W` 条目数必须与文件里逐条写的相同（不丢；多认形态不算少）。"""
    goal = _latest_terminal_goal()
    written = _w_numbers(_text(goal))
    assert written, f"{goal.name} 的残余节里没有任何 `W-NN` 条目 ⇒ 本判据失去对象"
    produced = _produced_w_numbers(_skeleton(ROOT, goal.name))
    assert produced == written, f"残余条目读少了：写出 {written}，读出 {produced}"


def _synthetic_tree(tmp_path: Path, transform: Callable[[str], str]) -> tuple[Path, str]:
    """真宪章 + 真最新 GOAL + 真复检的副本，只在需要处改 GOAL 正文。"""
    goal = _latest_terminal_goal()
    reader = _reader()
    plans = tmp_path / ".cursor" / "plans"
    (plans / "goals").mkdir(parents=True)
    (plans / "rechecks").mkdir(parents=True)
    shutil.copyfile(GOALS_DIR / "MAINLINE.md", plans / "goals" / "MAINLINE.md")
    recheck = ROOT / str(reader.PARSE.frontmatter(_text(goal))["latest_recheck"])
    shutil.copyfile(recheck, plans / "rechecks" / recheck.name)
    (plans / "goals" / goal.name).write_bytes(transform(_text(goal)).encode("utf-8"))
    return tmp_path, goal.name


def _refuses(root: Path, goal_name: str) -> str:
    """跑读取器，返回拒绝码（不拒 ⇒ 判据自己点名失败）。"""
    reader = _reader()
    with pytest.raises(reader.PARSE.Refusal) as caught:
        reader.build_skeleton(root, f".cursor/plans/goals/{goal_name}", NEXT_ID)
    return str(caught.value.code)


def _drop_section(text: str) -> str:
    """删掉整个残余小节（标题到下一个 `## ` 之前）。"""
    kept: list[str] = []
    skipping = False
    for line in text.splitlines():
        if line.startswith(RESIDUAL_HEADING):
            skipping = True
            continue
        if skipping and line.startswith("## "):
            skipping = False
        if not skipping:
            kept.append(line)
    return "\n".join(kept) + "\n"


def _drop_middle_item(text: str) -> str:
    """把残余节换成**三条合成条目** `W-1/W-2/W-3`，再删掉 `W-2` ⇒ 断号。

    为什么合成：当前最新 GOAL 只有 1 条残余 ⇒ 「删一条」会退化成 `RESIDUAL_EMPTY`
    （另一条拒绝臂），测不到 `RESIDUAL_GAP`。断号这条臂要的是「编号序列里少了一个」，
    与条目正文无关 ⇒ 用固定正文的三条合成条目，把被测形态钉死。
    """
    kept: list[str] = []
    skipping = False
    for line in text.splitlines():
        if line.startswith(RESIDUAL_HEADING):
            skipping = True
            kept.append(line)
            kept.extend(["", "- **`W-1`** 合成条目一。", "- **`W-3`** 合成条目三。", ""])
            continue
        if skipping and line.startswith("## "):
            skipping = False
        if not skipping:
            kept.append(line)
    return "\n".join(kept) + "\n"


def test_a_missing_residual_section_is_refused_by_name(tmp_path: Path) -> None:
    """反证：删掉整个小节 ⇒ 必须点名拒绝（证明上一条不是无条件绿）。"""
    root, goal_name = _synthetic_tree(tmp_path, _drop_section)
    assert _refuses(root, goal_name) == "RESIDUAL_SECTION_MISSING"


def test_a_gap_in_the_w_numbering_is_refused_by_name(tmp_path: Path) -> None:
    """反证：`W-1 / W-3` 形态 ⇒ `RESIDUAL_GAP`（证明「数相等」不是在数巧合）。"""
    root, goal_name = _synthetic_tree(tmp_path, _drop_middle_item)
    assert _refuses(root, goal_name) == "RESIDUAL_GAP"
