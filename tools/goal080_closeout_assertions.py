#!/usr/bin/env python3
"""GOAL-20261015-080 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…079 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-080 特有的断言**。

五条主轴（逐条对 GOAL-080 的 EC）：

1. **EC-01 设计来源可声明 + 读取器确定 / run 作用域 / fail-closed**：
   `read_design_from_plan` 在树 + `design_source` 装配位在树 + 例数下界。
2. **EC-02 内容真正决定实验**：装配面解释点（`_arms_for`）+ **来源唯一**（两条并存 ⇒ 拒）
   + 未认得的来源名 ⇒ 点名（**不**回落）。
3. **EC-03 换计划 ⇒ 换实验**：e2e 在树 + 例数下界（同一装配 + 两份计划 ⇒ 两套实验）。
4. **EC-04 live 达成**：live 判据在树 + **参数真的生效**的断言在树（两层名字映射）
   + 读数归档在树（`CR=0`）。
5. **EC-05 自举收口**：两条脚本进两处射程 + 按压归档在树 + cycle 4 的**三处产品缺陷**
   被钉住（循环控制豁免 / finish 投影 / 正文取自正文而非 repr）。

**五条纪律**（承 GOAL-027…079）：不读两树判词做一致性断言（那是输入即输出）；
判词行不含绝对路径；f-string 分片按**子串**；`defines` 收**含类方法**的版本；
**一律判关系**（抽函数会让钉调用点的判据假红）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/test_experiment_design_reader.py", 22),
    ("tests/application/test_experiment_design_decides.py", 11),
    ("tests/e2e/test_experiment_design_from_the_plan.py", 8),
    ("tests/adapters/openhands/test_policy_enforcement.py", 10),
    ("tests/adapters/openhands/test_adapter_core.py", 18),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tools/verify_goal079_closeout.py",
    "tests/e2e/test_research_report_chain_live.py",
    "tests/architecture/python/test_declared_input_sources.py",
)

#: 落点常量（逐条点名；缺一即判红）。
READER = "packages/application/experiments/design_from_plan.py"
SUPPORT = "services/api/experiment_support.py"
E2E = "tests/e2e/test_experiment_design_from_the_plan.py"
LIVE = "tests/e2e/test_experiment_design_from_the_plan_live.py"
ADAPTER = "adapters/openhands/runtime_adapter.py"
MAPPING = "adapters/openhands/event_mapping.py"
ENFORCING = "adapters/openhands/policy_enforcing_agent.py"

#: 本轮引入的形态（**逐条点名**）。
READ_FN = "def read_design_from_plan("
DESIGN_SOURCE_FIELD = "design_source: str | None = None"
DESIGN_SOURCE_PLAN = 'DESIGN_SOURCE_PLAN = "plan"'
ARMS_FOR_FN = "def _arms_for("
UNDECIDABLE = "would be undecidable"
UNKNOWN_SOURCE = "unknown experiment design source"
PLAN_ARTIFACT_NAME = 'PLAN_ARTIFACT_NAME = "research_plan"'
ENVELOPE_KEY = "ENVELOPE_CONTENT_KEY"
FINAL_ANSWER_FN = "def final_answer_text("
LOOP_VERBS = "LOOP_CONTROL_VERBS"
FINISH_NAME = 'FINISH_TOOL_NAME = "finish"'
CONTENT_TEXT_FN = "def _content_text("
PARAM_EFFECT_FN = "_assert_the_declared_parameters_took_effect"

#: 按压归档（**进树**、二进制写盘）。
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261015-080-ec01-press-two-way.txt"
PRESS_ARCHIVE_2 = ".cursor/plans/goals/evidence/GOAL-20261015-080-ec02-press-two-way.txt"
#: EC-04 的读数归档两份（阻塞点取证 + 达成读数）。
BLOCKER_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261015-080-ec04-blocker.txt"
LIVE_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261015-080-ec04-design-evidence.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal080_closeout.py"
ASSERTIONS = "tools/goal080_closeout_assertions.py"

#: 三向按压（EC-01）与三向按压（EC-02）：各自的**受判面用例**必须在树。
_PRESS_JUDGES: tuple[tuple[str, str], ...] = (
    ("V10-1", "TestTheReadIsRunScoped"),
    ("V10-2", "TestTheWhitelistIsEnforcedOnTheDesign"),
    ("V10-3", "TestTheFailureModesAreNamedSeparately"),
    ("V10-4", "TestTheSourceMustBeUnambiguous"),
    ("V10-5", "TestThePlanContentDecides"),
    ("V10-6", "TestTheUnchangedPathStaysUnchanged"),
)


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


def _captures(root: Path, relative: str, *markers: str) -> bool:
    source = _text(root, relative)
    return all(marker in source for marker in markers)


def _ec01_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：读取器 + 装配位 + 契约 + 例数下界。"""
    reader = _text(root, READER)
    return [
        toolbox.verdict(
            "ec01-the-reader-is-in-tree",
            READ_FN in reader and PLAN_ARTIFACT_NAME in reader and ENVELOPE_KEY in reader,
            "读取器必须在树，且认计划制品的两种形态（含交付物信封）",
        ),
        toolbox.verdict(
            "ec01-the-source-is-declarable",
            DESIGN_SOURCE_FIELD in _text(root, SUPPORT)
            and DESIGN_SOURCE_PLAN in _text(root, SUPPORT),
            "装配面必须能声明设计来源（缺省 ⇒ 既有语义不变）",
        ),
        toolbox.verdict(
            "ec01-the-fail-modes-are-named-separately",
            # 六条判词各自不同（无登记 / 无制品 / 无设计块 / 畸形 / 空臂 / 多制品）
            all(
                marker in reader
                # 逐条取自**源码实际措辞**（跨行拼接的句子用其**行内片段**，
                # 否则断言会因换行位置而假红 —— 实测踩过一次）。
                for marker in (
                    "nothing is ",
                    "readable '",
                    "carries no",
                    "must be an object",
                    "declares no arms",
                    "more than one plan artifact",
                )
            ),
            "fail-closed 的六条判词必须**互不相同**（否则「计划没写」与「读不到」不可区分）",
        ),
        toolbox.verdict(
            "ec01-the-judge-covers-positive-scope-and-fail-closed",
            _count_test_cases(root, CASE_FLOORS[0][0]) >= CASE_FLOORS[0][1],
            f"读取器判据例数低于下界 {CASE_FLOORS[0][1]}",
        ),
    ]


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：解释点 + 来源唯一 + 未知名点名。"""
    support = _text(root, SUPPORT)
    return [
        toolbox.verdict(
            "ec02-the-interpretation-point-is-in-tree",
            ARMS_FOR_FN in support,
            "装配面的解释点必须在树（唯一一处说「臂从哪来」）",
        ),
        toolbox.verdict(
            "ec02-two-sources-at-once-are-refused",
            UNDECIDABLE in support,
            "两条来源并存必须**点名拒绝**（静默取其一正是要消灭的含混）",
        ),
        toolbox.verdict(
            "ec02-an-unknown-source-is-refused",
            UNKNOWN_SOURCE in support,
            "未认得的来源名必须点名（**不**当成「没有来源」回落）",
        ),
        toolbox.verdict(
            "ec02-the-judge-covers-uniqueness-and-zero-regression",
            _count_test_cases(root, CASE_FLOORS[1][0]) >= CASE_FLOORS[1][1],
            f"判据例数低于下界 {CASE_FLOORS[1][1]}",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：换计划 ⇒ 换实验的 e2e 在树 + 例数下界。"""
    e2e = _text(root, E2E)
    return [
        toolbox.verdict("ec03-the-e2e-is-in-tree", bool(e2e), "e2e 判据文件不在树"),
        toolbox.verdict(
            "ec03-the-e2e-covers-plan-change-params-and-no-source",
            all(
                marker in e2e
                for marker in (
                    "test_a_different_plan_runs_a_different_experiment",
                    "test_the_plan_parameters_reach_the_container_environment",
                    "test_no_source_runs_exactly_one_experiment_with_the_legacy_id",
                )
            ),
            "e2e 必须覆盖：换计划 / 参数逐键 / 未声明来源零回归",
        ),
        toolbox.verdict(
            "ec03-the-e2e-meets-the-floor",
            _count_test_cases(root, CASE_FLOORS[2][0]) >= CASE_FLOORS[2][1],
            f"例数低于下界 {CASE_FLOORS[2][1]}",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：live 判据 + **参数真的生效**的断言 + 两份读数归档（`CR=0`）。"""
    live = _text(root, LIVE)
    blocker = (root / BLOCKER_ARCHIVE).read_bytes() if (root / BLOCKER_ARCHIVE).is_file() else b""
    achieved = (root / LIVE_ARCHIVE).read_bytes() if (root / LIVE_ARCHIVE).is_file() else b""
    return [
        toolbox.verdict(
            "ec04-the-live-judge-is-in-tree",
            bool(live) and "requires_live_llm" in live,
            "live 判据必须在树且带 requires_live_llm（默认门如实 skip）",
        ),
        toolbox.verdict(
            "ec04-the-parameter-propagation-is-asserted",
            PARAM_EFFECT_FN in live and "duplicates_expected" in live,
            "判据必须断言**参数真的落到该臂指标里**（只对臂名会让「参数没进容器」假绿）",
        ),
        toolbox.verdict(
            "ec04-the-blocker-evidence-is-archived",
            bool(blocker) and bytes([13]) not in blocker,
            "missing/empty" if not blocker else "contains CR",
        ),
        toolbox.verdict(
            "ec04-the-achieved-evidence-is-archived",
            bool(achieved) and bytes([13]) not in achieved,
            "missing/empty" if not achieved else "contains CR",
        ),
    ]


def _ec05_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-05：两处射程 + 按压归档 + cycle 4 的三处缺陷被钉住。"""
    enforcing = _text(root, ENFORCING)
    mapping = _text(root, MAPPING)
    adapter = _text(root, ADAPTER)
    scope = toolbox.module_literal(_text(root, SCOPE_JUDGE), "IN_SCOPE")
    declared = set(scope) if isinstance(scope, tuple) else set()
    verifiers = toolbox.module_literal(_text(root, VERIFIER_JUDGE), "_VERIFIERS")
    press1 = (root / PRESS_ARCHIVE).read_bytes() if (root / PRESS_ARCHIVE).is_file() else b""
    press2 = (root / PRESS_ARCHIVE_2).read_bytes() if (root / PRESS_ARCHIVE_2).is_file() else b""
    return [
        toolbox.verdict(
            "ec05-the-loop-verbs-are-exempt-by-name",
            LOOP_VERBS in enforcing and '"think"' in enforcing and '"finish"' in enforcing,
            "循环控制豁免必须是**逐字白名单**（不是「放过某类工具」的规则）",
        ),
        toolbox.verdict(
            "ec05-the-finish-message-is-projected",
            FINISH_NAME in mapping,
            "`finish` 的 message（SDK 逐字 *Final message to send to the user*）必须被投影",
        ),
        toolbox.verdict(
            "ec05-the-content-is-text-not-repr-and-the-deliverable-is-untruncated",
            CONTENT_TEXT_FN in mapping
            and FINAL_ANSWER_FN in mapping
            and "final_answer_text(" in adapter,  # adapter 侧是**调用**（定义在 mapping）
            "正文必须取自 `TextContent.text`；交付物必须用**不截断**的 `final_answer_text`",
        ),
        toolbox.verdict(
            "ec05-scope-in-scope-pure-tightening",
            not [item for item in (SELF, ASSERTIONS) if item not in declared],
            "两个脚本都必须显式登记进 IN_SCOPE（纯收紧 ⇒ 只增不删）",
        ),
        toolbox.verdict(
            "ec05-verifier-registered",
            isinstance(verifiers, tuple) and SELF in verifiers,
            "验证器必须登记进 _VERIFIERS",
        ),
        toolbox.verdict(
            "ec05-the-press-archives-are-binary-safe",
            bool(press1)
            and bool(press2)
            and bytes([13]) not in press1
            and bytes([13]) not in press2,
            "press archive missing/empty/contains CR",
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


def _press_judge_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """六条按压各自的**受判面**必须在树（判据不被删除 / 改名才有的保证）。"""
    joined = _text(root, "tests/application/test_experiment_design_reader.py") + _text(
        root, "tests/application/test_experiment_design_decides.py"
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
        *_press_judge_verdicts(root, toolbox),
    ]


__all__ = ["assertion_verdicts"]
