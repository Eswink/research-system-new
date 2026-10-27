#!/usr/bin/env python3
"""GOAL-20261014-076 的**记录面**断言集（2026-10-27 回填；它**不是**收口证明）。

**为什么这个文件的第一句话是「不是收口证明」**（如实登记，不粉饰）：

- `tools/verify_goal076_closeout.py` **从未存在** —— GOAL-076 的 EC-05 正文里点名了它，
  那是一句**悬空引用**；
- 更根本的是：**GOAL-076 的 status 是 `PAUSED`**（不是 `ACHIEVED`/`BLOCKED`/`ABANDONED`）。
  它的 EC-01…EC-05 在树里的取值全是 `PENDING`，而那 10 条查询参数的显式长度界**从来没有**
  被加进去（实测：`services/api/routers/` 只有 `operations.py` 的两处 `max_length=10`，
  正是 GOAL 建档时**已经存在**的那两条）。
- `tests/tooling/test_terminal_goals_have_closeout_verifiers.py` 的 `_CUTOFF_SEQ = 64`
  （祖父条款）把序 44 挡在受判面之外 ⇒ 它**不判红**。

⇒ 本断言集断言的是**「记录与树一致」**，不是「GOAL-076 达成了它宣称的事」。具体说：它判
PAUSED 状态在位、判那批长度界**确实缺席**（把「未做」写成可复核的事实）、判 GOAL 正文的
自述与实测口径不矛盾。**把「不可修复/未完成」硬补成编造内容**是本轮 `fix_policy` 明令禁止的
那一项，本文件是那条禁令的机械形态。

**五组**（逐条对应 GOAL-076 的 EC，但取的是「它的真实读数」）：

1. GOAL 文件的**状态就是 `PAUSED`**（改回 PAUSED 之外的值 ⇒ 判红，因为那会暗示它已收口）；
2. EC 状态**逐条仍是 `PENDING`**（把它改成 PASS 而无实现 ⇒ 判红）；
3. 那 10 条参数的长度界**仍然缺席**（一旦有人补上，本条判红 ⇒ 提示去把它收口，而不是
   让本文件继续声称「未做」）；
4. 五面（序 37/40/41/42/43）的判据**真的在树**（射程事实，与「076 是否完成」无关）；
5. 收口资产的**缺位**是记录在案的（本文件 + 验证器在位，且它们**不**声称完成）。

**判据规则**（承 GOAL-027…097）：一律判**关系**；判词行**不含绝对路径**。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

PROGRAM_SEQ = 44
GOAL_ID = "GOAL-20261014-076"

GOAL = ".cursor/plans/goals/GOAL-20261014-076-declared-query-params-have-explicit-length-bounds.md"
SELF = "tools/verify_goal076_closeout.py"
ASSERTIONS = "tools/goal076_closeout_assertions.py"
ROUTERS = "services/api/routers"

#: GOAL-076 点名要补界的那 10 条参数（正文逐字列出）。
UNBOUNDED_PARAMETERS: tuple[str, ...] = (
    "endpoint_id",
    "cursor",
    "poll",
    "dataset_id",
    "state",
    "scope",
    "proposed_by",
    "at",
)

#: 五面（序 37/40/41/42/43）的判据落点 —— 这些**确实存在**（与 076 的完成度无关）。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/api/test_undeclared_query_params_are_refused.py",
    "tests/api/test_unknown_query_params_cover_every_declared_route.py",
    "tests/api/test_write_face_query_params_are_refused.py",
    "tests/api/test_duplicate_scalar_query_params_are_refused.py",
    "tests/api/test_empty_query_values_are_refused.py",
)

SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _frontmatter(goal: str, key: str) -> str:
    """frontmatter 里某个键的值（只扫首个 `---` 块）。"""
    if not goal.startswith("---"):
        return ""
    end = goal.find("\n---", 3)
    block = goal[: end if end != -1 else len(goal)]
    for line in block.splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    return ""


def _ec_statuses(goal: str) -> dict[str, str]:
    """GOAL 正文里每条 EC 的 `status:`（按 EC 块定位）。"""
    found: dict[str, str] = {}
    for match in re.finditer(r"  - id: (EC-\d+)\n", goal):
        ec = match.group(1)
        tail = goal[match.end() :]
        stop = tail.find("\n  - id: ")
        block = tail[: stop if stop != -1 else len(tail)]
        for line in block.splitlines():
            if line.strip().startswith("status:"):
                found[ec] = line.split(":", 1)[1].strip()
                break
    return found


def _max_length_parameters(root: Path) -> set[str]:
    """出厂路由里**已经**声明了 `max_length=` 的参数名集合。"""
    declared: set[str] = set()
    directory = root / ROUTERS
    if not directory.is_dir():
        return declared
    for path in sorted(directory.glob("*.py")):
        for match in re.finditer(
            r"(\w+)\s*:\s*[^=\n]+=\s*Query\((?P<args>[^)]*)\)", path.read_text(encoding="utf-8")
        ):
            if "max_length=" in match.group("args"):
                declared.add(match.group(1))
    return declared


def _status_verdicts(goal: str, toolbox: Any) -> list[Any]:
    """1 + 2：状态就是 `PAUSED`、EC 逐条仍是 `PENDING`（**不声称收口**）。"""
    verdict = toolbox.verdict
    statuses = _ec_statuses(goal)
    verdicts: list[Any] = [
        verdict("goal-in-tree", bool(goal), GOAL),
        verdict(
            "goal-status-is-paused-not-achieved",
            _frontmatter(goal, "status") == "PAUSED",
            f"status={_frontmatter(goal, 'status')!r}；"
            "076 从未收口，改成终态会让「它做过什么」失真",
        ),
        verdict(
            "goal-does-not-claim-completion",
            "ACHIEVED" not in _frontmatter(goal, "status"),
            "状态行不得是 ACHIEVED（那 10 条长度界从未加进去）",
        ),
        verdict("goal-declares-five-ecs", len(statuses) == 5, sorted(statuses)),
    ]
    for ec in sorted(statuses):
        verdicts.append(
            verdict(
                f"{ec.lower()}-still-pending",
                statuses[ec] == "PENDING",
                f"{ec} status={statuses[ec]!r}（改成 PASS 而无实现 = 伪造）",
            )
        )
    return verdicts


def _delivery_verdicts(root: Path, goal: str, toolbox: Any) -> list[Any]:
    """3 + 4：那 10 条界**仍然缺席**；五面判据在树（射程事实）。"""
    verdict = toolbox.verdict
    declared = _max_length_parameters(root)
    missing = [name for name in UNBOUNDED_PARAMETERS if name not in declared]
    verdicts: list[Any] = [
        verdict(
            "the-unbounded-parameters-are-still-unbounded",
            len(missing) == len(UNBOUNDED_PARAMETERS),
            f"已声明界的：{sorted(declared)}；若这里开始变红，说明有人补了界 ⇒ 应去收口 076",
        ),
        verdict(
            "only-the-two-pre-existing-bounds-are-present",
            declared <= {"date_from", "date_to"},
            "超出建档时既有的两条 ⇒ 076 的交付面被做了："
            f"{sorted(declared - {'date_from', 'date_to'})}",
        ),
        verdict(
            "the-goal-body-records-the-gap",
            "10 条" in goal or "10/16" in goal,
            "正文必须记录「10 条无界」这个读数（否则记录与实测脱节）",
        ),
    ]
    for relative in PRIOR_JUDGES:
        verdicts.append(
            verdict(f"prior-judge-{Path(relative).name}", (root / relative).is_file(), relative)
        )
    return verdicts


def _backfill_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """5：收口资产的**缺位**被记录在案（回填 ≠ 过门禁）。"""
    verdict = toolbox.verdict
    return [
        verdict("self-verifier-in-tree", (root / SELF).is_file(), SELF),
        verdict("self-assertions-in-tree", (root / ASSERTIONS).is_file(), ASSERTIONS),
        verdict(
            "listed-in-verifier-registry",
            "verify_goal076_closeout.py" in _text(root, VERIFIER_JUDGE),
            f"{VERIFIER_JUDGE} 必须登记本验证器（回填 ≠ 过门禁）",
        ),
        verdict(
            "listed-in-product-gate-scope",
            "verify_goal076_closeout.py" in _text(root, SCOPE_JUDGE),
            f"{SCOPE_JUDGE} 的 IN_SCOPE 必须收录本验证器",
        ),
        verdict(
            "the-backfill-is-declared-as-backfill",
            "回填" in _text(root, ASSERTIONS),
            "断言集必须写明自身是回填（不是当年就有的收口资产）",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """记录面 vs 树的**一致性**（不声称 GOAL-076 已完成）。"""
    goal = _text(root, GOAL)
    return [
        *_status_verdicts(goal, toolbox),
        *_delivery_verdicts(root, goal, toolbox),
        *_backfill_verdicts(root, toolbox),
    ]


__all__ = [
    "ASSERTIONS",
    "GOAL",
    "GOAL_ID",
    "PROGRAM_SEQ",
    "PRIOR_JUDGES",
    "SELF",
    "UNBOUNDED_PARAMETERS",
    "assertion_verdicts",
]
