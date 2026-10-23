"""台账判据的**反方向**：提交链 → 台账（GOAL-20261023-095）。

**它补哪一道缝**：`tests/tooling/test_goal_ledger_covers_every_commit.py` 判的是
`台账 ⊆ 迭代日志`。反方向 —— 「提交链里的每个提交是否都被某张台账收录」 —— **没有判据**。
实测（GOAL-094 收口时）：`git log --grep=goal094` 得 **10** 个提交，台账只有 **6** 行，
`e8a1500c` / `ca4565d7` / `2c913d1f` / `f8c61422` 四个只改记录的提交**不进台账**，
而收口验证器仍全绿。这不是「记录漏了」，是**没有那项检查** —— 同一毛病的第五个面。

**判什么**（缺一即判红）：

1. 受判面内每个终态 GOAL：主题行点名该 GOAL 的每个提交，都必须在 `## CI 台账` 的
   提交集合里 —— **HEAD 除外**。这一条不是豁免而是**结构必然**：一个提交的哈希写不进
   它自己携带的内容。链因此**收敛**（下一个提交补记上一个），而不是开环（GOAL-094
   的散文正是卡在这里：写它自己那一行会再产生一个提交，无终止）。受判的是
   **除 HEAD 之外的全部**，所以「漏了上一个」立刻可见。
2. 台账里点名了一个**不属于本 GOAL 提交链**的哈希 ⇒ 点名失败。张冠李戴会**掩盖缺行**
   （行数够了、但那一行记的是别人的提交）。
3. 提交链为空（**非浅克隆**时）⇒ 点名失败。空真不是通过。
4. 主题行**不点名任何 GOAL** 却改了 `.cursor/` 之外的文件 ⇒ 点名失败。
   「无法归属的代码提交」与「漏记」是同一件事的两面：它连该进哪张表都无从判定。

**归因只认主题行**（实测的坑）：`git log --grep` 搜的是**整条消息**。`068e16c4` 的正文
提到 GOAL-093，于是它出现在 `--grep=goal093` 里，而它的主题是 `test(goal094)` ——
按整条消息归因会把别人的提交算进链里（链变长 ⇒ 缺行被判成「有」）。

**CI 侧的历史可得性**（如实登记 `W-1`）：`actions/checkout` 默认 `fetch-depth: 1`
（`.github/workflows/m0-quality.yml` 六处 checkout 均未声明 depth）⇒ CI 里只有 HEAD
一个提交，本判据**取不到链**。加 `fetch-depth: 0` 属**基础设施改动**（本轮授权把它列为
必须停下登记的项）⇒ 这里选择**点名 skip**（不是静默通过：`pytest` 的 skip 可见且带理由），
本地真执法、CI 不执法。**需要用户决定是否加 `fetch-depth: 0`。**
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Sequence
from pathlib import Path

#: 主题行里的 GOAL 标记形态（`goal094` / `goal94`；大小写不敏感）。
_ANY_TAG = re.compile(r"\bgoal0*\d+\b", re.IGNORECASE)

#: 记录面（**只改这里面的提交**不必点名 GOAL：宪章归档、见证重封这类簿记不属任何 GOAL）。
_RECORD_PREFIX = ".cursor/"


class HistoryUnavailable(RuntimeError):
    """取不到 git 历史（缺仓 / git 不在 / 浅克隆）—— 调用方**点名**处理，不静默吞。"""


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        raise HistoryUnavailable(
            f"`git {' '.join(args)}` exited {result.returncode}: {result.stderr.strip()[:200]}"
        )
    return result.stdout


def is_shallow(root: Path) -> bool:
    """工作副本是不是浅克隆（`true` ⇒ 历史被截断，链取不全）。"""
    try:
        return _git(root, "rev-parse", "--is-shallow-repository").strip() == "true"
    except HistoryUnavailable:
        return True


def head_sha(root: Path) -> str:
    try:
        return _git(root, "rev-parse", "HEAD").strip()
    except HistoryUnavailable as error:  # 无提交的树：判据失去对象
        raise HistoryUnavailable(str(error)) from error


def goal_number(goal_id: str) -> int:
    """GOAL id 的**编号**（`GOAL-20261022-093` ⇒ `93`；提交主题写的是这个数）。

    与程序表的**序**是两个空间：094 的序是 62、编号是 94。混用会让判据捞到另一条
    GOAL 的提交（实测过一次：按序 62 取链捞到 `GOAL-…-062` 的 8 个提交，本链被当成幽灵）。
    """
    return int(goal_id.rsplit("-", 1)[1])


def chain_for(root: Path, number: int) -> tuple[tuple[str, str], ...]:
    """主题行点名 `goal<number>` 的提交 ⇒ `[(完整 sha, 主题)]`（新 → 旧）。

    **只认主题行**（见模块 docstring）：正文提到别的 GOAL 不算。

    **`number` 是 GOAL 的编号（id 里的 `NNN`），不是程序表的「序」**—— 实测踩到过：
    `GOAL-20261022-093` 的序是 **61**，而它的提交主题写的是 `goal093`；按序取会捞到
    另一条 GOAL（`GOAL-…-061`）的 9 个提交，于是「自己的链」全是别人的提交，
    真正的本链被报成 `phantom`。**两个编号空间必须分开用**：序号管祖父条款，
    编号管提交归因。
    """
    token = re.compile(rf"\bgoal0*{number}\b", re.IGNORECASE)
    found: list[tuple[str, str]] = []
    for line in _git(root, "log", "--format=%H%x1f%s", "HEAD").splitlines():
        sha, _, subject = line.partition("\x1f")
        if sha and token.search(subject):
            found.append((sha, subject))
    return tuple(found)


def _matches(sha: str, entry: str) -> bool:
    """台账写的是前缀（仓内既有形态 7–8 位）；两向都试，短于 7 位不算命中。"""
    entry = entry.strip().lower()
    return len(entry) >= 7 and (sha.startswith(entry) or entry.startswith(sha))


def unledgered(
    chain: Sequence[tuple[str, str]], ledger: Sequence[str], head: str
) -> list[tuple[str, str]]:
    """链里**没进台账**的提交（HEAD 除外 —— 它写不进自己携带的内容）。"""
    return [
        (sha, subject)
        for sha, subject in chain
        if sha != head and not any(_matches(sha, entry) for entry in ledger)
    ]


def phantom(chain: Sequence[tuple[str, str]], ledger: Sequence[str]) -> list[str]:
    """台账点名了、但**不在本 GOAL 链里**的哈希（张冠李戴 / 打错一位都落在这里）。"""
    shas = [sha for sha, _ in chain]
    return [entry for entry in ledger if not any(_matches(sha, entry) for sha in shas)]


def floor_commit(root: Path, chains: Sequence[Sequence[tuple[str, str]]]) -> str | None:
    """所有链里**最老**的那个提交（受判的提交区间下界；祖父条款由此自动生效）。"""
    wanted = {sha for chain in chains for sha, _ in chain}
    if not wanted:
        return None
    for sha in _git(root, "rev-list", "--reverse", "HEAD").split():
        if sha in wanted:
            return sha
    return None


def untagged_code_commits(root: Path, floor: str) -> list[tuple[str, str]]:
    """`floor..HEAD` 里**主题不点名任何 GOAL** 却改了 `.cursor/` 之外文件的提交。"""
    found: list[tuple[str, str]] = []
    for line in _git(root, "log", "--format=%H%x1f%s", f"{floor}..HEAD").splitlines():
        sha, _, subject = line.partition("\x1f")
        if not sha or _ANY_TAG.search(subject):
            continue
        touched = _git(root, "show", "--name-only", "--format=", sha).splitlines()
        if any(path.strip() and not path.startswith(_RECORD_PREFIX) for path in touched):
            found.append((sha, subject))
    return found


def describe(items: Sequence[tuple[str, str]]) -> str:
    """判词里的点名形态（**前缀 + 主题**；不含绝对路径，两树复检可逐字比对）。"""
    return "; ".join(f"{sha[:8]} {subject}" for sha, subject in items)


__all__ = [
    "HistoryUnavailable",
    "chain_for",
    "describe",
    "floor_commit",
    "head_sha",
    "is_shallow",
    "phantom",
    "unledgered",
    "untagged_code_commits",
]
