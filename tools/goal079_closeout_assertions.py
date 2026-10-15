#!/usr/bin/env python3
"""GOAL-20261015-079 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…078 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-079 特有的断言**。

五条主轴（逐条对 GOAL-079 的 EC）：

1. **EC-01 参数由声明给出**：白名单在树 + 前缀命名空间与执行器的键**不相交** +
   脚本侧**真读**声明（而不是继续用模块常量）+ 判据在树。
2. **EC-02 多臂/对照真跑**：臂声明在树（两种形态）+ 臂 id **独立派生**（不复用
   「一 run 一实验」那条）+ 派发体**逐臂**跑 + e2e 在树。
3. **EC-03 臂间可比**：对比器在树 + **同名列才比** + 缺指标/非数值**点名**（不折算）。
4. **EC-04 live 取证**：live 判据**逐臂**断言 + 读数归档在树（`CR=0`）+
   **报告多臂渲染**（表头按臂长列）在树。
5. **EC-05 自举收口**：本轮两条脚本进两处射程（`IN_SCOPE` / `_VERIFIERS`）+
   按压归档在树 + **本 cycle 修掉的同族缺陷**被钉住（`verify_goal078` 的
   `ASSERTIONS` 与加载行都指自己那份）。

**五条纪律**（承 GOAL-027…078）：不读两树判词做一致性断言（那是输入即输出）；
判词行不含绝对路径；f-string 分片按**子串**；`defines` 收**含类方法**的版本；
**一律判关系**（抽函数会让钉调用点的判据假红）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/test_experiment_parameters.py", 11),
    ("tests/application/test_experiment_arms.py", 14),
    ("tests/application/test_arm_comparison.py", 13),
    ("tests/e2e/test_two_arm_experiment_offline.py", 8),
    ("tests/application/test_research_report_assembler.py", 9),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tools/verify_goal078_closeout.py",
    "tests/e2e/test_research_report_chain_live.py",
    "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py",
)

#: 落点常量（逐条点名；缺一即判红）。
PARAMETERS = "packages/application/experiments/plan_parameters.py"
ARMS = "packages/application/experiments/arms.py"
COMPARISON = "packages/application/experiments/arm_comparison.py"
SUPPORT = "services/api/experiment_support.py"
SCRIPT = "examples/experiments/exact_match_index_benchmark.py"
PARAM_SUITE = "tests/application/test_experiment_parameters.py"
ARMS_SUITE = "tests/application/test_experiment_arms.py"
COMPARISON_SUITE = "tests/application/test_arm_comparison.py"
E2E_ARMS = "tests/e2e/test_two_arm_experiment_offline.py"
LIVE = "tests/e2e/test_research_report_chain_live.py"
LIVE_SUPPORT = "tests/e2e/retrieval_context_support.py"
ASSEMBLER = "packages/application/deliverable/research_report.py"
REPORT_FACTS = "packages/application/run_orchestration/report_facts.py"

#: 本轮引入的形态（**逐条点名**）。
ALLOWED = "ALLOWED_PARAMETERS"
PREFIX = "EXPERIMENT_PARAM_"
PARAM_ENV_FN = "def parameter_environment("
ARM_ID_FN = "def arm_experiment_id("
DECLARE_ARMS_FN = "def declare_arms("
COMPARE_FN = "def compare_arms("
PER_ARM_LOOP = "for arm in arms:"
MULTI_ARM_HEADER = "| 指标 | 实验 | 值 | 单位 |"
PER_ARM_METRIC_FN = "def _metric_rows("

#: 按压归档（**进树**、二进制写盘）。
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261015-079-press-two-way.txt"
#: EC-04 的读数归档。
LIVE_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261015-079-ec04-arms-evidence.txt"
#: 本 cycle（EC-05）的同族缺陷按压归档。
OWNNESS_PRESS = ".cursor/plans/goals/evidence/GOAL-20261015-079-c5-ownness-press.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal079_closeout.py"
ASSERTIONS = "tools/goal079_closeout_assertions.py"

#: 七条按压：各自的**受判面用例/类**必须在树。
_PRESS_JUDGES: tuple[tuple[str, str], ...] = (
    ("V9-1", "TestTheWhitelistIsEnforced"),
    ("V9-2", "TestTheDeclarationReachesTheRequest"),
    ("V9-3", "TestTheScriptReadsTheDeclaration"),
    ("V9-4", "TestTwoArmsReallyRun"),
    ("V9-5", "TestTheArmsGetDistinctIdentities"),
    ("V9-6", "TestNonNumericValuesAreNamedNotForced"),
    ("V9-7", "TestOnlySharedMetricsAreCompared"),
)

#: 本轮 live 判据里**逐臂遍历**的证据（修复前的形态只查 `entries[0]`）。
#: `for entry in entries` 是**实测**读出的形态（判据遍历**全部**实验记录），
#: 不是「报告里出现某个词」—— 连同 `assert_the_arms_ran` 一起判**关系**。
LIVE_ARM_MARKERS: tuple[str, ...] = ("assert_the_arms_ran", "for entry in entries")


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _count_test_cases(root: Path, relative: str) -> int:
    source = _text(root, relative)
    if not source:
        return 0
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return 0
    return sum(
        1
        for node in ast.walk(parsed)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


def _defines_all(source: str, names: tuple[str, ...]) -> list[str]:
    """哪些名字**没有**被定义（AST 读，不含文本巧合）。"""
    if not source:
        return list(names)
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return list(names)
    found = {
        node.name
        for node in ast.walk(parsed)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    return [name for name in names if name not in found]


def _ec01_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：白名单 + 命名空间不相交 + 脚本**真读**声明 + 判据在树。"""
    parameters = _text(root, PARAMETERS)
    script = _text(root, SCRIPT)
    support = _text(root, SUPPORT)
    return [
        toolbox.verdict(
            "ec01-the-whitelist-is-in-tree",
            ALLOWED in parameters and PREFIX in parameters,
            "参数面必须是**声明白名单** + 固定前缀（§9：不是「转发任意环境变量」）",
        ),
        toolbox.verdict(
            "ec01-the-declaration-reaches-the-request",
            PARAM_ENV_FN in parameters and "parameter_environment(" in support,
            "声明必须经**执行请求**到达容器（装配面调用参数面）",
        ),
        toolbox.verdict(
            "ec01-the-script-reads-the-declaration",
            "_declared_int(" in script and PREFIX in script,
            "脚本必须**真读**声明（继续用模块常量 ⇒ 参数面是装饰）",
        ),
        toolbox.verdict(
            "ec01-the-judge-covers-whitelist-verbatim-and-zero-regression",
            _count_test_cases(root, PARAM_SUITE) >= 11,
            "判据必须覆盖：白名单 / 逐键传递 / 零回归 / 脚本真读 / 非法点名",
        ),
    ]


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：臂声明 + **独立派生** + 逐臂派发 + e2e 在树。"""
    arms = _text(root, ARMS)
    support = _text(root, SUPPORT)
    missing = _defines_all(arms, ("parse_arms", "ArmDeclaration", "arm_experiment_id"))
    return [
        toolbox.verdict(
            "ec02-the-arm-declaration-is-in-tree",
            not missing and ARM_ID_FN in arms,
            f"臂声明面缺：{missing}",
        ),
        toolbox.verdict(
            "ec02-the-arm-ids-live-in-their-own-namespace",
            "experiment-arm" in arms and "experiment_run_id_of" in arms,
            "臂 id 必须**独立派生**（复用「一 run 一实验」那条 ⇒ 两臂撞同一个 id）",
        ),
        toolbox.verdict(
            "ec02-the-dispatch-runs-every-arm",
            PER_ARM_LOOP in support and DECLARE_ARMS_FN in arms and "declare_arms(" in support,
            "派发体必须**逐臂**各跑一次（声明了臂却只跑一个 ⇒ 多臂是装饰）",
        ),
        toolbox.verdict(
            "ec02-the-e2e-covers-arms-refutation-and-the-no-arm-path",
            _count_test_cases(root, E2E_ARMS) >= 8 and _count_test_cases(root, ARMS_SUITE) >= 14,
            "e2e 必须覆盖：两臂真跑 / 参数落对臂 / 消息点名全部臂 / 单臂反证 / 无声明零回归",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：对比器在树 + **同名列才比** + 缺指标 / 非数值**点名**。"""
    comparison = _text(root, COMPARISON)
    return [
        toolbox.verdict(
            "ec03-the-comparison-is-in-tree",
            COMPARE_FN in comparison and "def _as_decimal(" in comparison,
            "臂间对比必须是**纯函数**（输入两份指标映射 ⇒ 输出差值读数）",
        ),
        toolbox.verdict(
            "ec03-only-shared-metrics-are-compared",
            "left_names & right_names" in comparison,
            "**同名列才比**（并集 ⇒ 单侧指标被折算进差值，把「没测」当成「测出 0」）",
        ),
        toolbox.verdict(
            "ec03-missing-and-non-numeric-are-named-not-forced",
            "missing_in_left" in comparison
            and "not_numeric" in comparison
            and "isinstance(value, bool)" in comparison,
            "缺指标与非数值（布尔）必须**逐条点名**，不得折算成 0 / 1",
        ),
        toolbox.verdict(
            "ec03-the-judge-covers-the-direction-and-the-empty-case",
            _count_test_cases(root, COMPARISON_SUITE) >= 13,
            "判据必须覆盖：方向（右减左）/ 缺指标点名 / 非数值排除 / 空对比不是 0",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：live **逐臂**断言 + 读数归档（`CR=0`）+ 报告多臂渲染在树。"""
    live = _text(root, LIVE)
    support = _text(root, LIVE_SUPPORT)
    assembler = _text(root, ASSEMBLER)
    facts = _text(root, REPORT_FACTS)
    raw = (root / LIVE_ARCHIVE).read_bytes() if (root / LIVE_ARCHIVE).is_file() else b""
    missing = [marker for marker in LIVE_ARM_MARKERS if marker not in live + support]
    return [
        toolbox.verdict(
            "ec04-the-live-judge-walks-every-arm",
            not missing,
            f"live 判据必须**逐臂**遍历（只查 entries[0] 的判据**看不见**静默丢臂）：{missing}",
        ),
        toolbox.verdict(
            "ec04-the-arm-blind-spot-is-closed-in-the-assembler",
            MULTI_ARM_HEADER in assembler and PER_ARM_METRIC_FN in facts,
            "报告必须**逐臂一行**且表头随臂长列（按名归并 ⇒ 静默丢一臂；并格 ⇒ 撑破表格）",
        ),
        toolbox.verdict(
            "ec04-the-evidence-archive-is-in-tree",
            bool(raw) and bytes([13]) not in raw,
            "missing/empty" if not raw else "contains CR",
        ),
    ]


def _ec05_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-05：本轮两条脚本进两处射程 + 同族缺陷被钉住 + 按压归档在树。"""
    raw = (root / OWNNESS_PRESS).read_bytes() if (root / OWNNESS_PRESS).is_file() else b""
    verifier_078 = _text(root, "tools/verify_goal078_closeout.py")
    scope = toolbox.module_literal(_text(root, SCOPE_JUDGE), "IN_SCOPE")
    declared = set(scope) if isinstance(scope, tuple) else set()
    verifiers = toolbox.module_literal(_text(root, VERIFIER_JUDGE), "_VERIFIERS")
    return [
        toolbox.verdict(
            "ec05-the-ownness-defect-is-fixed-in-the-verifier",
            'ASSERTIONS = "tools/goal078_closeout_assertions.py"' in verifier_078
            and 'parent / "goal078_closeout_assertions.py"' in verifier_078,
            "同族缺陷（自洽地加载上一轮断言集）必须已被修掉且**两处**都指自己那份",
        ),
        toolbox.verdict(
            "ec05-the-ownness-press-is-in-tree",
            bool(raw)
            and bytes([13]) not in raw
            and "all_red_and_restored=True" in raw.decode("utf-8", errors="replace"),
            "missing/empty/未全红" if not raw else "contains CR 或未全红",
        ),
        toolbox.verdict(
            "ec05-scope-in-scope-pure-tightening",
            not [item for item in (SELF, ASSERTIONS) if item not in declared],
            "两个脚本都必须显式登记进 IN_SCOPE（纯收紧 ⇒ 只增不删）",
        ),
        toolbox.verdict(
            "ec05-verifier-registered",
            isinstance(verifiers, tuple) and SELF in verifiers,
            "验证器必须登记进 _VERIFIERS（否则「跑自己的断言集」这条射程漏了它）",
        ),
    ]


def _judge_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """判据面：例数下界 + 既有判据仍在树。"""
    verdicts: list[Any] = []
    for relative, floor in CASE_FLOORS:
        count = _count_test_cases(root, relative)
        verdicts.append(
            toolbox.verdict(f"cases-{Path(relative).stem}", count >= floor, f"{count} < {floor}")
        )
    for relative in PRIOR_JUDGES:
        verdicts.append(
            toolbox.verdict(f"prior-judge-{Path(relative).stem}", (root / relative).is_file())
        )
    return verdicts


def _archive_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """记录面：按压归档形态（非空、`CR=0`）+ **七条逐条在场**。

    **不读内容做一致性断言**（输入即输出）—— 只判形态与标签在场。
    """
    path = root / PRESS_ARCHIVE
    raw = path.read_bytes() if path.is_file() else b""
    text = raw.decode("utf-8", errors="replace")
    missing = [label for label, _case in _PRESS_JUDGES if label not in text]
    return [
        toolbox.verdict(
            "press-archive-is-binary-safe",
            bool(raw) and bytes([13]) not in raw,
            "missing/empty" if not raw else "contains CR",
        ),
        toolbox.verdict(
            "press-archive-names-every-arm",
            not missing and "all_red_and_restored=True" in text,
            f"缺标签/未全红：{missing}",
        ),
    ]


def _press_judge_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """七条按压各自的**受判面**必须在树（判据不被删除 / 改名才有的保证）。"""
    joined = (
        _text(root, PARAM_SUITE)
        + _text(root, ARMS_SUITE)
        + _text(root, COMPARISON_SUITE)
        + _text(root, E2E_ARMS)
    )
    return [
        toolbox.verdict(f"press-{label.lower()}-arm-is-asserted", case in joined, case)
        for label, case in _PRESS_JUDGES
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 的特有断言（收口验证器唯一入口）。"""
    return [
        *_ec01_verdicts(root, toolbox),
        *_ec02_verdicts(root, toolbox),
        *_ec03_verdicts(root, toolbox),
        *_ec04_verdicts(root, toolbox),
        *_ec05_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_press_judge_verdicts(root, toolbox),
    ]


__all__ = ["assertion_verdicts"]
