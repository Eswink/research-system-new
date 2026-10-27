#!/usr/bin/env python3
"""GOAL-20261023-095 收口复检的**本轮特有断言集**（EC-01…EC-05；2026-10-27 回填）。

**为什么是回填**：`tools/verify_goal095_closeout.py` **从未存在**（GOAL-096 的 `W-3` 记的
就是这件事）。`_CUTOFF_SEQ = 64` 把序 63 挡在受判面外 ⇒ 它不判红。本文件 + 同名验证器
**补齐历史**：让「序 63 的收口资产齐备」此后可复检 —— 这**不等于**它当年过了门。

**五条主轴**（逐条对应本 GOAL 的 EC）：

1. **EC-01 反方向判据**：`test_goal_commit_chain_reaches_the_ledger.py` 在树，且它
   **import 正向判据的四个受判原语**（不另造受判面）；正向判据的 8 条用例逐条仍在。
2. **EC-02 判据真的会咬**：两向按压的**形态**可读（判据里点名「受判面」与「祖父条款」
   两件事）；按压用的常量（`_CUTOFF_SEQ` / `_CUTOFF_DATE`）从正向判据**导入**而不是各写一份。
3. **EC-03 GOAL-094 台账补齐**：那四个提交（`e8a1500c` / `ca4565d7` / `2c913d1f` /
   `f8c61422`）在 GOAL-094 的 CI 台账里逐行可查。
4. **EC-04 证据域前进一格**：`conflict_sweep.py` 在树（跨记录矛盾聚合，确定性纯函数）；
   `sweep_conflicts` 是**显式请求**才附的键（缺省载荷逐字不变）。
5. **EC-05 记录面**：程序表序 63 在位；本验证器被两份射程清单收录。

**判据规则**（承 GOAL-027…097）：一律判**关系**；判词行**不含绝对路径**。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

PROGRAM_SEQ = 63
GOAL_ID = "GOAL-20261023-095"

GOAL = ".cursor/plans/goals/GOAL-20261023-095-the-ledger-judge-reads-both-directions.md"
PRIOR_GOAL = (
    ".cursor/plans/goals/GOAL-20261022-094-goal-ledger-judge-and-the-model-written-report.md"
)
SELF = "tools/verify_goal095_closeout.py"
ASSERTIONS = "tools/goal095_closeout_assertions.py"

#: EC-01 的两份判据（正 / 反方向）。
FORWARD_JUDGE = "tests/tooling/test_goal_ledger_covers_every_commit.py"
REVERSE_JUDGE = "tests/tooling/test_goal_commit_chain_reaches_the_ledger.py"

#: 反方向判据**必须复用**的受判原语（缺一条 = 另造受判面）。
SHARED_PRIMITIVES: tuple[str, ...] = (
    "_terminal_goals_in_scope",
    "_ledger_commits",
    "_CUTOFF_SEQ",
    "_CUTOFF_DATE",
)

#: EC-04 的落点。聚合函数在 `conflict_sweep`，而**「显式请求才附键」**那条在
#: `adapters/canonical/memory_read.py`（读面才是决定「缺省载荷变不变」的地方）。
SWEEP = "packages/application/memory/conflict_sweep.py"
SWEEP_JUDGE = "tests/application/memory/test_conflict_sweep.py"
MEMORY_READ = "adapters/canonical/memory_read.py"
#: 显式请求才附的键（缺省载荷逐字不变）。
SWEEP_KEY = "sweep_conflicts"

#: EC-03：GOAL-094 的四个提交（逐条点名；缺一即判红）。
COMMITS: tuple[str, ...] = ("e8a1500c", "ca4565d7", "2c913d1f", "f8c61422")

SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"

TEST_DEFINITION = re.compile(r"(?m)^\s*def test_")


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def collected_case_count(root: Path, relative: str) -> int:
    return len(TEST_DEFINITION.findall(_text(root, relative)))


def _reverse_judge_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：反方向判据在树，且**复用**正向判据的受判原语（不另造受判面）。"""
    verdict = toolbox.verdict
    reverse = _text(root, REVERSE_JUDGE)
    verdicts: list[Any] = [
        verdict("ec01-forward-judge-in-tree", (root / FORWARD_JUDGE).is_file(), FORWARD_JUDGE),
        verdict("ec01-reverse-judge-in-tree", (root / REVERSE_JUDGE).is_file(), REVERSE_JUDGE),
        verdict(
            "ec01-forward-judge-keeps-eight-cases",
            collected_case_count(root, FORWARD_JUDGE) >= 8,
            f"正向判据 {collected_case_count(root, FORWARD_JUDGE)} < 8（既有受判面被收窄？）",
        ),
        verdict(
            "ec01-reverse-judge-has-cases",
            collected_case_count(root, REVERSE_JUDGE) >= 4,
            f"反方向判据 {collected_case_count(root, REVERSE_JUDGE)} < 4",
        ),
    ]
    for primitive in SHARED_PRIMITIVES:
        verdicts.append(
            verdict(
                f"ec01-reverse-imports-{primitive.strip('_').lower()}",
                primitive in reverse,
                f"反方向判据必须复用 `{primitive}`（不另造受判面）",
            )
        )
    return verdicts


def _bite_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：判据真的会咬的**形态**可读（受判面理由 / 祖父条款 / 主题行 / HEAD）。"""
    verdict = toolbox.verdict
    reverse = _text(root, REVERSE_JUDGE)
    forward = _text(root, FORWARD_JUDGE)
    return [
        verdict(
            "ec02-scope-reason-is-recorded",
            "_scope_reason" in reverse or "_scope_reason" in forward,
            "受判面的理由必须写下来（为什么这个 GOAL 在面内）",
        ),
        verdict(
            "ec02-annex-clause-is-named",
            "祖父" in reverse or "祖父" in forward,
            "祖父条款必须在判据里点名（受判面下界靠它）",
        ),
        verdict(
            "ec02-attribution-keys-on-the-subject-line",
            "subject" in reverse,
            "归因只认主题行（`--grep` 搜整条消息会把别的 GOAL 的提交算进来）",
        ),
        verdict(
            "ec02-head-is-the-structural-exception",
            "HEAD" in reverse,
            "HEAD 是唯一结构例外（提交哈希写不进自身内容）",
        ),
    ]


def _goal094_ledger_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：GOAL-094 的台账里逐行列出那四个补记的提交。"""
    verdict = toolbox.verdict
    prior_goal = _text(root, PRIOR_GOAL)
    return [
        verdict(
            f"ec03-goal094-ledger-lists-{commit}",
            commit in prior_goal,
            f"GOAL-094 的 CI 台账必须逐行列出 `{commit}`",
        )
        for commit in COMMITS
    ]


def _evidence_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：证据域前进一格（跨记录聚合 + 显式请求才附键）。"""
    verdict = toolbox.verdict
    sweep = _text(root, SWEEP)
    return [
        verdict("ec04-conflict-sweep-in-tree", (root / SWEEP).is_file(), SWEEP),
        verdict("ec04-conflict-sweep-judge-in-tree", (root / SWEEP_JUDGE).is_file(), SWEEP_JUDGE),
        verdict(
            "ec04-sweep-is-an-explicit-request",
            SWEEP_KEY in _text(root, MEMORY_READ),
            f"`{SWEEP_KEY}` 必须是**显式请求**才附的键（读面在这里：{MEMORY_READ}）",
        ),
        verdict(
            "ec04-sweep-judge-has-nine-cases",
            collected_case_count(root, SWEEP_JUDGE) >= 9,
            f"{collected_case_count(root, SWEEP_JUDGE)} < 9",
        ),
        verdict(
            "ec04-sweep-is-deterministic",
            "零出网" in sweep or "确定性" in sweep,
            "聚合必须是确定性纯函数（零出网 / 零模型 / 零时钟）",
        ),
    ]


def _backfill_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-05：回填自身被登记（**回填 ≠ 过门禁**）。"""
    verdict = toolbox.verdict
    return [
        verdict("self-verifier-in-tree", (root / SELF).is_file(), SELF),
        verdict("self-assertions-in-tree", (root / ASSERTIONS).is_file(), ASSERTIONS),
        verdict(
            "listed-in-verifier-registry",
            "verify_goal095_closeout.py" in _text(root, VERIFIER_JUDGE),
            f"{VERIFIER_JUDGE} 必须登记本验证器",
        ),
        verdict(
            "listed-in-product-gate-scope",
            "verify_goal095_closeout.py" in _text(root, SCOPE_JUDGE),
            f"{SCOPE_JUDGE} 的 IN_SCOPE 必须收录本验证器",
        ),
        verdict(
            "the-backfill-is-declared-as-backfill",
            "回填" in _text(root, ASSERTIONS),
            "断言集必须写明自身是回填（不是当年就有的收口资产）",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有的断言（按 EC 分组；每组一个函数 —— 单函数 50 行门）。"""
    return [
        *_reverse_judge_verdicts(root, toolbox),
        *_bite_verdicts(root, toolbox),
        *_goal094_ledger_verdicts(root, toolbox),
        *_evidence_verdicts(root, toolbox),
        *_backfill_verdicts(root, toolbox),
    ]


__all__ = [
    "ASSERTIONS",
    "COMMITS",
    "GOAL",
    "GOAL_ID",
    "PROGRAM_SEQ",
    "SELF",
    "SHARED_PRIMITIVES",
    "assertion_verdicts",
    "collected_case_count",
]
