#!/usr/bin/env python3
"""宪章「进展记录」的**共享读取面**：活跃面 + 归档，一次取全。

**它补哪一格**（2026-10-30 实测，同一缺陷第三次被独立发现）：

1. **收口验证器侧**：`verify_goal0NN_closeout.py` 的 `_ladder_verdicts` / `_progress_verdicts`
   只读 `MAINLINE.md` 的**活跃面**，而宪章的归档惯例只保留**最近 3 条** ⇒ 任何 GOAL 的
   进展行一旦被移入 `archive/`，它自己的收口验证器就产出 **2 条假负**
   （`progress-records-this-goal` / `progress-row-names-the-recheck`）。实测：16 个验证器
   里 14 个无归档回退 ⇒ **28 条假负**，全部「绿在扫描面外」（负判扫描只跑断言集模块，
   不看主文件）。GOAL-098 当年手工加过一次归档回退（见
   `verify_goal098_closeout._ladder_verdicts` 的注释），**只有那一个文件有**
   —— 17 处各写一遍必然漂移，故提为共享 helper。
2. **charter 读取器侧**：`charter_parse.residuals` 只认 ``- **`W-N`**``（**加粗**）形态，
   而本仓 **87 / 109** 条残余写的是 ``- `W-N` ``（不加粗）⇒ 连续三轮
   `REFUSED RESIDUAL_EMPTY`（GOAL-098 / 099 / 100 各自登记过同一拒绝码）。
   （那一面修在 `charter_parse._W_ITEM`；本模块只负责进展行。）

**为什么是「活跃面或归档」而不是「只活跃面」**：断言问的是「**当初有没有写这一行**」，
不是「它现在还在活跃面吗」。后者是归档惯例的**正常结果**，判成负就是**假负** —— 资产
绑错了面。反过来，把判据整个删掉是另一种错（那就没人再看这一行了）⇒ 必须**两侧都读**。

**形态独立（这是本模块为什么会是现在这个样子）**：归档文件有**两种**写法 ——
`## 进展记录（移出部分，原文搬运）` 起头的，和**没有小节标题**（表格直接跟在 `#` 标题下）。
按小节标题定位会漏掉后者（实测：082…087 四份归档就是这么写的）。因此判据**按行的形状**
辨认进展数据行：

* 以 `| ` 开头，**且第二格是一个 GOAL id**（`| 日期 | GOAL-… | 一句话结论 | 能力域 | RECHECK |`）。

这同时把**修订记录**的行排除在外（那类第二格是 `序`，如 `| 2026-10-28 | 67（新增） | …`）
—— 两者若混在一起，「这行有没有写本轮复检」会被另一张表的行喂饱。

**射程边界（如实登记）**：
- 本模块只做**读取**，不含判断（「这一行该不该在」由调用方判）；
- 归档面取 `goals/archive/*.md`（宪章归档的既有落点），**不**递归、**不**读别的目录；
- 「活跃面优先、缺失才读归档」而不是并集：同一行不应两处并存（归档惯例要求原文搬运、
  不得两处并存）；两侧都有时活跃面那份是答案，归档那份的残渣由
  `test_mainline_archive_is_continuous` 判，本模块不越权重复判它。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

#: 宪章的相对路径（所有调用方同一个口径）。
CHARTER = ".cursor/plans/goals/MAINLINE.md"
#: 归档目录（宪章「归档惯例」的落点；`MAINLINE-*.md`）。
ARCHIVE_DIR = ".cursor/plans/goals/archive"
#: 进展记录小节的标题（活跃面用它定位；归档面按行形状认，不依赖它）。
PROGRESS_HEADING = "## 进展记录"

#: 进展数据行的形状：首格任意、**第二格是 GOAL id**。
_PROGRESS_ROW = re.compile(r"^\|\s*[^|]*\|\s*(GOAL-\d{8}-\d{3})\s*\|")


@dataclass(frozen=True, slots=True)
class ProgressRead:
    """一次「进展记录」读取的**归因面**（读到了什么、从哪读到的）。

    `rows` 是**逐字原文**的数据行（不摘要、不改写）；`sources` 与 `rows` 一一对应，说明
    每一行来自哪个文件 —— 判据点名时能说「这行在归档里，不在活跃面」，这正是
    「归档后的正常移出」与「断言失败」的分界。
    """

    rows: tuple[str, ...]
    sources: tuple[str, ...]
    #: 活跃面里本小节的正文（定位失败 ⇒ 空串；调用方据此点名「小节不见了」）。
    live_section: str
    #: 与 `rows` 一一对应的**所在正文**（活跃面那一份是小节；归档那一份是整份文件）。
    #: 「插在最上面」这类**位置**断言要在行所在的正文里判，否则归档后就没有对象。
    contexts: tuple[str, ...] = ()

    @property
    def anywhere(self) -> tuple[str, ...]:
        """活跃面与归档两处合计的行（调用方只关心「有没有」时用它）。"""
        return self.rows


def _section(text: str, heading: str) -> str:
    """某个二级小节的正文（到下一个 `## ` 为止）；不存在 ⇒ 空串。"""
    start = text.find(heading)
    if start == -1:
        return ""
    tail = text[start + len(heading) :]
    stop = tail.find("\n## ")
    return tail[: stop if stop != -1 else len(tail)]


def _data_rows(text: str, goal_id: str) -> list[str]:
    """正文里点名了该 GOAL 的**进展**数据行（按行形状判，不看小节标题）。"""
    rows: list[str] = []
    for line in text.splitlines():
        match = _PROGRESS_ROW.match(line)
        if match is not None and match.group(1) == goal_id:
            rows.append(line)
    return rows


def progress_rows(root: Path, goal_id: str) -> ProgressRead:
    """该 GOAL 在「进展记录」里的数据行 —— **活跃面优先，缺失才读归档**。"""
    charter_path = root.joinpath(*CHARTER.split("/"))
    live = ""
    rows: list[str] = []
    sources: list[str] = []
    contexts: list[str] = []
    if charter_path.is_file():
        live = _section(charter_path.read_text(encoding="utf-8"), PROGRESS_HEADING)
        rows = _data_rows(live, goal_id)
        if rows:
            sources = [CHARTER] * len(rows)
            contexts = [live] * len(rows)
    if rows:
        return ProgressRead(tuple(rows), tuple(sources), live, tuple(contexts))
    archive_dir = root.joinpath(*ARCHIVE_DIR.split("/"))
    if not archive_dir.is_dir():
        return ProgressRead((), (), live, ())
    for path in sorted(archive_dir.glob("*.md")):
        # 历史档案可能不是合法 UTF-8；读失败 ⇒ 跳过（按「没有」处理，由调用方点名）。
        # **不**用 errors="replace"：那会让乱码行伪装成一行记录。
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        found = _data_rows(text, goal_id)
        if found:
            rows.extend(found)
            sources.extend([f"{ARCHIVE_DIR}/{path.name}"] * len(found))
            contexts.extend([text] * len(found))
    return ProgressRead(tuple(rows), tuple(sources), live, tuple(contexts))


__all__ = [
    "ARCHIVE_DIR",
    "CHARTER",
    "PROGRESS_HEADING",
    "ProgressRead",
    "progress_rows",
]
