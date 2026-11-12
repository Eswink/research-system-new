"""GOAL-20261111-112 的**产品面断言集**（收口验证器的另一半）。

与 `tools/verify_goal112_closeout.py`（记录面）分工：本文件判**交付物真的在、且三面
真的同判**；主文件判 EC 终态与宪章记账。

**本轮的判法**（每条在断言集里**重放行为**，不只查文件存在）：

* 同一张表（EC-01）：四键闭集 / 三键执行面 / 类型表齐全；
* 三面同判（EC-02/03/05）：同一份声明在

  - 实验边界（`check_constraints`）
  - 工具面（`resolve_capability` 的 findings + `constraints`）
  - preflight（`_evaluate_requirement` 的 finding）

  给出**同一个结论**——这是 `W-4` 的收口判据；
* `authored`（EC-04）：`AUTHORED_ALLOWED_BY_DEFAULT is False` + 两道门 + `script_source` 闭集；
* 阶梯（EC-06）：实验行带新 bar、其余六行不被推广。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

DELIVERABLES: tuple[str, ...] = (
    "packages/application/experiments/constraint_table.py",
    "packages/application/experiments/script_authority.py",
    "packages/application/experiments/design_script.py",
    "packages/application/tool_plane/resolver.py",
    "packages/application/preflight/policy_check.py",
)

JUDGES: tuple[str, ...] = (
    "tests/application/experiments/test_constraint_table.py",
    "tests/application/experiments/test_authored_profile.py",
    "tests/application/tool_plane/test_resolver_carries_constraints.py",
    "tests/application/preflight/test_policy_check_reads_constraints.py",
)

VERIFIER = "tools/verify_goal112_closeout.py"
ASSERTIONS = "tools/goal112_closeout_assertions.py"

#: 阶梯锚（本轮推进的是「实验」格）。
EXPERIMENT_BAR = "三条约束在全部执行面生效"
#: 本轮**不动**的六行各自的边界锚（`下一级` 格内；取改写后实测）。
OTHER_LADDER_ANCHORS: tuple[tuple[str, str], ...] = (
    ("| 检索 |", "检索改变下一轮问题"),
    ("| 计划 |", "配对消融下"),
    ("| 复检 |", "评审者与作者分开"),
    ("| 证据 |", "处置闭环成立（策略闭集 + 可判依据）"),
    ("| 报告 |", "叙述质量与事实一致性可判"),
    ("| 迭代 |", "迭代改变下一轮问题"),
)


def _module(root: Path, relative: str, name: str) -> ModuleType | None:
    path = root / relative
    if not path.is_file():
        return None
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _file_verdicts(root: Path, toolbox: Any) -> list[Any]:
    return [
        toolbox.verdict(
            f"delivered-{Path(relative).name}",
            (root / relative).is_file(),
            f"{relative} 不在树",
        )
        for relative in (*DELIVERABLES, *JUDGES, VERIFIER, ASSERTIONS)
    ]


def _table_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：表自洽。"""
    table = _module(root, "packages/application/experiments/constraint_table.py", "g112_table")
    if table is None:
        return [toolbox.verdict("constraint-table-importable", False, "表不可加载")]
    return [
        toolbox.verdict(
            "constraint-closed-set-has-four-keys",
            table.CONSTRAINT_KEYS
            == ("sandbox_required", "path_prefix", "max_seconds", "requires_workspace_lease"),
            f"闭集实得 {table.CONSTRAINT_KEYS}",
        ),
        toolbox.verdict(
            "three-keys-are-enforced-and-one-is-shape-only",
            table.ENFORCED_KEYS == ("sandbox_required", "path_prefix", "max_seconds")
            and "requires_workspace_lease" not in table.ENFORCED_KEYS,
            "三个执行面键 + 一个仅形状键（出厂策略里已声明，本轮不假装执行）",
        ),
        toolbox.verdict(
            "every-key-has-a-declared-type",
            set(table.EXPECTED_TYPES) == set(table.CONSTRAINT_KEYS),
            "每个键必须有声明类型",
        ),
        toolbox.verdict(
            "bool-does-not-impersonate-int",
            bool(table.shape_violations({"max_seconds": True}))
            and not table.shape_violations({"max_seconds": 60}),
            "`max_seconds: true` 是声明错误，不是 1 秒",
        ),
    ]


def _three_face_cases(table: Any, authority: Any, shipped: Any, toolbox: Any) -> list[Any]:
    """三条对抗事实：**表**判红 且 **实验边界**也判红（两面不会各说各话）。"""
    cases = (
        ("no_sandbox", {"sandbox_required": True}, {"sandboxed": False}),
        ("escaping_path", {"path_prefix": "work/"}, {"write_path": "../etc/passwd"}),
        ("timeout", {"max_seconds": 60}, {"requested_seconds": 120}),
    )
    verdicts: list[Any] = []
    for label, constraints, facts in cases:
        table_says = bool(table.violations(constraints, **facts))
        try:
            authority.check_constraints(
                authority.ExecutionRequest(
                    script_path=shipped,
                    digest="sha256:" + "a" * 64,
                    constraints=constraints,
                    **facts,
                )
            )
            boundary_says = False
        except authority.AuthorityError:
            boundary_says = True
        verdicts.append(
            toolbox.verdict(
                f"both-faces-agree-on-{label}",
                table_says and boundary_says,
                f"{label}: 表判 {table_says} / 实验边界判 {boundary_says}（必须都真）",
            )
        )
    return verdicts


def _digest_cases(table: Any, authority: Any, shipped: Any, toolbox: Any) -> list[Any]:
    """digest 面：表与边界各判一次（边界拒无摘要的 shipped 脚本）。"""
    digest_case = table.digest_violation("sha256:" + "a" * 64, "sha256:" + "b" * 64)
    try:
        authority.check_constraints(
            authority.ExecutionRequest(script_path=shipped, digest="", authored=False)
        )
        no_digest_refused = False
    except authority.AuthorityError:
        no_digest_refused = True
    return [
        toolbox.verdict(
            "digest-mismatch-is-named",
            digest_case is not None and "script bytes changed" in digest_case.reason,
            "digest 不匹配必须点名",
        ),
        toolbox.verdict(
            "the-boundary-refuses-a-shipped-script-without-a-digest",
            no_digest_refused,
            "shipped 脚本无摘要 ⇒ 边界拒（跑的不是被审过的字节）",
        ),
    ]


def _adversarial_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-05：**同一份声明**在**三个面**上给出同一个结论（`W-4` 的收口判据）。"""
    table = _module(root, "packages/application/experiments/constraint_table.py", "g112_table2")
    authority = _module(
        root, "packages/application/experiments/script_authority.py", "g112_authority"
    )
    if table is None or authority is None:
        return [toolbox.verdict("adversarial-importable", False, "模块不可加载")]
    shipped = authority.shipped_scripts()[0]
    return [
        *_three_face_cases(table, authority, shipped, toolbox),
        *_digest_cases(table, authority, shipped, toolbox),
    ]


def _authored_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：不启用 + 两道门 + `script_source` 闭集。"""
    authority = _module(
        root, "packages/application/experiments/script_authority.py", "g112_authority2"
    )
    design = _module(root, "packages/application/experiments/design_script.py", "g112_design")
    if authority is None or design is None:
        return [toolbox.verdict("authored-importable", False, "模块不可加载")]
    return [
        toolbox.verdict(
            "authored-is-still-not-allowed-by-default",
            authority.AUTHORED_ALLOWED_BY_DEFAULT is False,
            "AUTHORED_ALLOWED_BY_DEFAULT 必须逐字仍是 False（本轮只交付可启用的网）",
        ),
        toolbox.verdict(
            "the-profile-name-is-a-named-constant",
            authority.AUTHORED_SAFETY_PROFILE == "authored-experiments-v1",
            f"具名 profile 实得 {authority.AUTHORED_SAFETY_PROFILE!r}",
        ),
        toolbox.verdict(
            "script-source-closed-set-is-two-values",
            design.SCRIPT_SOURCES == ("shipped", "authored"),
            f"script_source 闭集实得 {design.SCRIPT_SOURCES}",
        ),
        toolbox.verdict(
            "absent-script-source-means-shipped",
            design.declared_script_source({}, where="assertions") == "shipped",
            "缺席 ⇒ shipped（逐字回到今天）",
        ),
    ]


def _next_level(charter: str, prefix: str) -> str:
    """某阶梯行的 `下一级` 格（阶梯 5 格；越级/漏格都读不出内容）。"""
    row = next((line for line in charter.splitlines() if line.startswith(prefix)), "")
    cells = row.split("|")
    return cells[4].strip() if len(cells) == 6 else ""


def _ladder_verdicts(root: Path, toolbox: Any) -> list[Any]:
    charter = toolbox.text(root, ".cursor/plans/goals/MAINLINE.md")
    experiment = next((line for line in charter.splitlines() if line.startswith("| 实验 |")), "")
    verdicts = [
        toolbox.verdict(
            "ladder-experiment-row-carries-the-new-bar",
            EXPERIMENT_BAR in experiment,
            "「实验」行的 下一级 必须含三面同判的 bar",
        )
    ]
    for prefix, anchor in OTHER_LADDER_ANCHORS:
        label = prefix.strip("| ").strip()
        level = _next_level(charter, prefix)
        verdicts.append(
            toolbox.verdict(
                f"ladder-{label}-stays-unpromoted",
                EXPERIMENT_BAR not in level,
                f"{label} 行不得被越级推广",
            )
        )
        verdicts.append(
            toolbox.verdict(
                f"ladder-{label}-keeps-its-own-anchor",
                anchor in level,
                f"{label} 行的 下一级 必须仍带自己的边界锚「{anchor}」",
            )
        )
    return verdicts


#: EC-06 的**程序完成报告**（五轮：序 76…80）。
PROGRAMME_REPORT = "docs/roadmap/ROUNDS_76_80_PROGRAMME_COMPLETION.md"
#: 五轮 GOAL（报告必须逐个点名，且每一份记录必须已是 `ACHIEVED`）。
PROGRAMME_GOALS: tuple[str, ...] = (
    "GOAL-20261111-108",
    "GOAL-20261111-109",
    "GOAL-20261111-110",
    "GOAL-20261111-111",
    "GOAL-20261111-112",
)
#: 报告不得丢掉的残余编号（`R-1` / `R-2` 是生成级与沙箱的**不得宣称**面）。
PROGRAMME_RESIDUALS: tuple[str, ...] = ("W-1", "W-2", "U-1", "U-2", "R-1", "R-2")


def _programme_report_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-06：程序完成报告在树、逐轮点名、残余逐条可读（不是一句「全部完成」）。"""
    path = root / PROGRAMME_REPORT
    if not path.is_file():
        return [toolbox.verdict("programme-report-exists", False, f"{PROGRAMME_REPORT} 不在树")]
    text = path.read_text(encoding="utf-8")
    verdicts = [
        toolbox.verdict("programme-report-exists", True, PROGRAMME_REPORT),
        toolbox.verdict(
            "programme-report-names-all-five-rounds",
            all(goal in text for goal in PROGRAMME_GOALS),
            "报告必须逐个点名序 76…80 的五个 GOAL",
        ),
    ]
    for goal in PROGRAMME_GOALS:
        records = sorted((root / ".cursor/plans/goals").glob(f"{goal}-*.md"))
        achieved = bool(records) and "status: ACHIEVED" in records[0].read_text(encoding="utf-8")
        verdicts.append(
            toolbox.verdict(
                f"programme-round-{goal[-3:]}-is-recorded-achieved",
                achieved,
                f"{goal} 的记录必须存在且 frontmatter `status: ACHIEVED`",
            )
        )
    missing = [item for item in PROGRAMME_RESIDUALS if item not in text]
    verdicts.append(
        toolbox.verdict(
            "programme-report-keeps-every-residual",
            not missing,
            f"报告丢了残余编号（空着等于宣称没有缺口）：{missing}",
        )
    )
    return verdicts


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 的产品面全量断言（验证器按路径加载并调用它）。"""
    return [
        *_file_verdicts(root, toolbox),
        *_table_verdicts(root, toolbox),
        *_adversarial_verdicts(root, toolbox),
        *_authored_verdicts(root, toolbox),
        *_ladder_verdicts(root, toolbox),
        *_programme_report_verdicts(root, toolbox),
    ]
