"""台账判据的**反方向**：提交链 → 台账（GOAL-20261023-095）。

**它补哪一道缝**：`test_goal_ledger_covers_every_commit.py` 判的是 `台账 ⊆ 迭代日志`。
反方向 —— 「提交链里每个提交是否都被台账收录」—— **没有判据**。实测（按 GOAL-094 收口
时的读数）：`git log --grep=goal094` 得 **10** 个提交，台账 **6** 行，`e8a1500c` /
`ca4565d7` / `2c913d1f` / `f8c61422` 四个**只改记录**的提交不在表里，而收口验证器仍全绿。
这不是「记录漏了」，是**没有那项检查** —— 同一毛病的第五个面。

**受判面与正向判据共用**（`SCOPE` / `LEDGER` / `CUTOFF_SEQ` / `CUTOFF_DATE` 全部 import，
**不另造一套**）：只有一份受判面，新增 GOAL 建档即自动进两条方向。

**判什么**（缺一即判红）：

1. 受判面内每个终态 GOAL：主题行点名该 GOAL 的每个提交，都在 `## CI 台账` 里。
   **HEAD 除外** —— 一个提交的哈希写不进它自己携带的内容（结构必然，不是豁免）。
   受判的是「除 HEAD 之外的全部」，所以漏记立刻可见，且链**收敛**（下一个提交补记上一个）。
2. 台账点名了**不在本链**的哈希 ⇒ 判红（张冠李戴会掩盖缺行：行数够了但记的是别人的）。
3. 主题行不点名任何 GOAL 却改了 `.cursor/` 之外的文件 ⇒ 判红（无法归属 = 漏记）。
4. 链为空 / 区间为空 ⇒ 判红（空真不是通过）。

**归因只认主题行**（实测的坑）：`git log --grep` 搜**整条消息**。`068e16c4` 的正文提到
GOAL-093，于是出现在 `--grep=goal093` 里，而它的主题是 `test(goal094)` —— 按整条消息
归因会把别人的提交算进链里，缺行就被判成「有」。

**编号 vs 序**（实测踩到）：`GOAL-…-093` 的**序**是 61，而它的提交主题写 `goal093`。
按序取链会捞到 `GOAL-…-061` 的 9 个提交、把本链报成幽灵 ⇒ **序管祖父条款，编号管归因**。

**CI 侧历史可得性（如实登记 `W-1`）**：`actions/checkout` 默认 `fetch-depth: 1`
（`m0-quality.yml` 六处 checkout 均未声明 depth）⇒ CI 里只有 HEAD 一个提交，本判据
**取不到链**。加 `fetch-depth: 0` 属**基础设施改动**（本轮授权把「改 CI workflow」列为
必须停下登记的项）⇒ 这里**点名 skip**（`pytest` 的 skip 可见且带理由），本地真执法、
CI 不执法。**需要用户决定是否加 `fetch-depth: 0`。**
"""

from __future__ import annotations

import re

import pytest

from tests.tooling import goal_commit_chain
from tests.tooling.test_goal_ledger_covers_every_commit import (
    _CUTOFF_DATE,
    _CUTOFF_SEQ,
    _ROOT,
    _ledger_commits,
    _terminal_goals_in_scope,
)

#: 与正向判据**同一个**受判面（import 而非重写；`test_the_reverse_direction_is_wired…` 钉住）。
SCOPE = _terminal_goals_in_scope
LEDGER = _ledger_commits
CUTOFF_SEQ = _CUTOFF_SEQ
CUTOFF_DATE = _CUTOFF_DATE

_SHALLOW_REASON = (
    "shallow checkout: `git log` cannot see the chain, so commit→ledger cannot be judged "
    "here (W-1: the M0 job needs `fetch-depth: 0`, which is a user decision)"
)


def _chains() -> list[tuple[str, str, tuple[tuple[str, str], ...]]]:
    """受判面内每个终态 GOAL 的提交链 ⇒ `[(id, 理由, 链)]`。"""
    return [
        (
            goal_id,
            reason,
            goal_commit_chain.chain_for(_ROOT, goal_commit_chain.goal_number(goal_id)),
        )
        for goal_id, reason, _text in SCOPE()
    ]


def test_every_commit_in_a_goal_chain_reaches_that_goals_ledger() -> None:
    """**核心（反方向）**：主题行点名某终态 GOAL 的每个提交，都在该 GOAL 的台账里。"""
    if goal_commit_chain.is_shallow(_ROOT):
        pytest.skip(_SHALLOW_REASON)
    goals = SCOPE()
    assert goals, "受判面为空 ⇒ 本条失去判据对象（空真不算通过）"
    head = goal_commit_chain.head_sha(_ROOT)
    problems: list[str] = []
    for goal_id, reason, text in goals:
        number = goal_commit_chain.goal_number(goal_id)
        chain = goal_commit_chain.chain_for(_ROOT, number)
        if not chain:
            problems.append(f"{goal_id}（{reason}）：主题行点名 goal{number} 的提交一个都取不到")
            continue
        ledger = LEDGER(text, [])
        missing = goal_commit_chain.unledgered(chain, ledger, head)
        if missing:
            problems.append(
                f"{goal_id}（{reason}）：{len(missing)} 个提交不在台账"
                f"（链 {len(chain)} 个，台账 {len(ledger)} 个）："
                f"{goal_commit_chain.describe(missing)}"
            )
        strays = goal_commit_chain.phantom(chain, ledger)
        if strays:
            problems.append(f"{goal_id}（{reason}）：台账点名了不属于本链的哈希：{strays}")
    assert problems == [], "提交链与台账对不上：\n" + "\n".join(problems)


def test_a_code_commit_that_names_no_goal_is_named_not_ignored() -> None:
    """改了 `.cursor/` 之外的文件、主题却不点名任何 GOAL ⇒ 点名（无法归属 = 漏记）。

    受判区间从**受判面内所有链里最老的那个提交**起算 —— 与祖父条款同一口径：
    更早的区段不追认（那些轮次收口时本判据还不存在）。
    """
    if goal_commit_chain.is_shallow(_ROOT):
        pytest.skip(_SHALLOW_REASON)
    chains = [chain for _goal, _reason, chain in _chains()]
    floor = goal_commit_chain.floor_commit(_ROOT, chains)
    assert floor is not None, "受判面内没有任何链 ⇒ 受判区间为空（空真不算通过）"
    untagged = goal_commit_chain.untagged_code_commits(_ROOT, floor)
    assert untagged == [], (
        "这些提交改了产品面却不点名任何 GOAL（无从归属）：" + goal_commit_chain.describe(untagged)
    )


def test_the_chain_predicate_bites_both_ways_on_synthetic_chains() -> None:
    """反证：**同一条谓词**在合成链上红 / 绿（真树绿不能证明它会咬）。"""
    chain = (("a" * 40, "feat(goal094): one"), ("b" * 40, "docs(goal094): two"))
    head = chain[1][0]
    assert goal_commit_chain.unledgered(chain, ["a" * 8], head) == []
    missing = goal_commit_chain.unledgered(chain, [], head)
    assert [sha for sha, _ in missing] == [chain[0][0]], missing
    # HEAD 不在台账里**不算**漏（它写不进自身内容）—— 与「漏记」严格区分。
    assert chain[1][0] not in [sha for sha, _ in missing]
    # 张冠李戴：台账记了别人的提交 ⇒ 判红（行数够了但记错人）。
    assert goal_commit_chain.phantom(chain, ["c" * 8]) == ["c" * 8]


def test_the_attribution_reads_the_subject_line_and_the_goal_number() -> None:
    """归因只认**主题行** + **编号**（两个空间：序管祖父条款、编号管归因）。

    实测形态：`068e16c4` 的正文提到 GOAL-093，`--grep`（搜整条消息）会把它算成
    GOAL-093 的提交；而按**序** 62 取链会捞到 `GOAL-…-062` 的 8 个提交。
    """
    token = re.compile(r"\bgoal0*(\d+)\b", re.IGNORECASE)
    assert [int(m) for m in token.findall("test(goal094): prove created_by")] == [94]
    assert [int(m) for m in token.findall("chore(goal94): x")] == [94]
    assert goal_commit_chain.goal_number("GOAL-20261022-093") == 93
    assert goal_commit_chain.goal_number("GOAL-20261023-095") == 95


def test_the_empty_chain_is_named_not_skipped() -> None:
    """链为空 ⇒ 点名（不是静默通过）。非浅克隆下应当有真实链。"""
    if goal_commit_chain.is_shallow(_ROOT):
        pytest.skip(_SHALLOW_REASON)
    chains = _chains()
    assert chains, "受判面为空 ⇒ 空真"
    for goal_id, reason, chain in chains:
        assert chain, f"{goal_id}（{reason}）：取不到链，但工作副本不是浅克隆 ⇒ 判据失去对象"
