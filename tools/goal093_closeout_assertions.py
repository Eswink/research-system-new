#!/usr/bin/env python3
"""GOAL-20261022-093 收口复检的**本轮特有断言集**（EC-01…EC-04）。

与 GOAL-023…092 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— 由 `tools/closeout_recheck_assertions.standard_verdicts`
承担；本文件**只写本 GOAL 特有的断言**。

三条主轴（逐条对应本 GOAL 的 EC）：

1. **EC-01/EC-02 的交付面**：第五个槽位在链上的**每一环**都在（`AgentSessionSpec`
   字段 / `SessionSpecContext` 字段 / `session_prompts` 取值 / `compose_prompt` 形参 /
   `session_builder` 调用点 / `phase_runner` 求值点 / 两个组合根接线）；渲染器的标题常量
   **逐字**在树；判据文件用例数**不低于下界**。
2. **EC-03 的三态**：三个理由常量（`NO_PRIOR_RUN` / `NO_ATTRIBUTABLE` / `NO_RUN_ROW`）
   **两两不同**（合并即判红）；`aggregate_panel` 的票数面与 `TrustLabel` **未被改动**。
3. **EC-04 跨 run**：两个组合根各有一处 `review_outcome=`；`program_id` 是读取入口
   （不按数组位置猜）。

**判据规则**（承 GOAL-027…092）：一律判**关系**；判词行**不含绝对路径**。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

#: 本轮**新增**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
#: `tests/**` 的规模门同样生效 ⇒ 判据分两文件，下界按文件分别给。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/run_orchestration/test_review_outcome_in_prompt.py", 10),
    ("tests/application/run_orchestration/test_review_outcome_across_runs.py", 2),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/application/test_review_panel_aggregation.py",
    "tests/e2e/test_review_panel_on_the_run_path.py",
    "tests/tooling/test_mainline_research_ladder_advances.py",
    "tests/tooling/test_python_source_limits.py",
)

#: **每一个承载第五槽位的环**（缺一环 = 段落不到模型眼前）。
CHAIN: tuple[tuple[str, str], ...] = (
    ("packages/application/ports/agent_runtime.py", "review_outcome_prompt"),
    ("packages/application/run_orchestration/task_executor.py", "review_outcome"),
    ("packages/application/run_orchestration/session_prompts.py", "def review_outcome_prompt"),
    (
        "packages/application/run_orchestration/retrieval_prompt.py",
        "(review_outcome, prompt_with_review_outcome)",
    ),
    ("adapters/openhands/session_builder.py", "review_outcome=spec.review_outcome_prompt"),
    ("packages/application/run_orchestration/phase_runner.py", "with_review_outcome"),
    (
        "packages/application/run_orchestration/runner_wiring.py",
        "review_outcome=deps.review_outcome",
    ),
    ("packages/application/run_orchestration/dependencies.py", "review_outcome: Any | None"),
)

#: 读取层与装配层的模块（**在树且非空**）。
MODULES: tuple[str, ...] = (
    "packages/application/run_orchestration/review_outcome.py",
    "services/api/review_outcome_support.py",
)

#: 渲染器的标题常量（**逐字**；判据与提示词都按它定位）。
SECTION_TITLE = "PRIOR REVIEW (how the last round was judged; revise against it)"

#: 三个**必须各不相同**的理由（三态不得合并成同一句话）。
THREE_STATES: tuple[str, ...] = ("NO_PRIOR_RUN", "NO_ATTRIBUTABLE", "NO_RUN_ROW")

#: 两个组合根各必须有一处接线。
ROOTS: tuple[str, ...] = (
    "services/api/composition.py",
    "services/api/pg_composition.py",
)

#: **零改动**面：这一轮的边界（列表里的东西一个字都不该被本 GOAL 改）。
UNTOUCHED: tuple[str, ...] = (
    "packages/application/evaluation/panel_verdict.py",
    "packages/domain/enums.py",
)


def _case_count(text: str) -> int:
    """判据文件里的用例数（`^def test_` 起头的行；参数化会展开成更多收集项）。"""
    return sum(1 for line in text.splitlines() if line.startswith("def test_"))


def delivery_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01 / EC-02：链上每一环 + 标题常量逐字 + 判据下界。"""
    verdicts: list[Any] = []
    for relative, needle in CHAIN:
        path = toolbox.tree(root, relative)
        present = path.is_file() and needle in path.read_text(encoding="utf-8")
        verdicts.append(
            toolbox.verdict(
                f"chain-{Path(relative).stem}-carries-the-slot",
                present,
                f"{relative} 必须包含 {needle!r}（缺这一环则段落到不了模型眼前）",
            )
        )
    for relative in MODULES:
        path = toolbox.tree(root, relative)
        verdicts.append(
            toolbox.verdict(
                f"module-{Path(relative).stem}-exists",
                path.is_file() and bool(path.read_text(encoding="utf-8").strip()),
            )
        )
    renderer = toolbox.text(root, "packages/application/run_orchestration/retrieval_prompt.py")
    verdicts.append(
        toolbox.verdict(
            "section-title-is-verbatim",
            f'"{SECTION_TITLE}"' in renderer,
            "标题常量必须逐字在树（判据按它定位；改字 = 改契约）",
        )
    )
    for relative, floor in CASE_FLOORS:
        text = toolbox.text(root, relative)
        count = _case_count(text)
        verdicts.append(
            toolbox.verdict(
                f"cases-{Path(relative).stem}",
                count >= floor,
                f"{relative} 的判据用例数 {count} 低于下界 {floor}",
            )
        )
    for relative in PRIOR_JUDGES:
        verdicts.append(
            toolbox.verdict(
                f"prior-judge-{Path(relative).stem}",
                toolbox.tree(root, relative).is_file(),
                f"本轮引用的既有判据必须仍在树：{relative}",
            )
        )
    return verdicts


def state_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：三态逐条**不同**；判定面与信任标签**未被改动**。"""
    module = toolbox.text(root, "packages/application/run_orchestration/review_outcome.py")
    texts: dict[str, str] = {}
    for name in THREE_STATES:
        marker = f'{name} = "'
        start = module.find(marker)
        if start == -1:
            continue
        rest = module[start + len(marker) :]
        texts[name] = rest.split('"', 1)[0]
    verdicts = [
        toolbox.verdict(
            f"state-{name}-is-declared", name in texts, f"三态之一 {name} 未声明（合并会丢读法）"
        )
        for name in THREE_STATES
    ]
    distinct = len(set(texts.values())) == len(THREE_STATES) if len(texts) == 3 else False
    verdicts.append(
        toolbox.verdict(
            "the-three-states-are-distinct",
            distinct,
            "「没有前序」/「读不到可归因判词」/「本 run 行未落库」必须是**三句不同的话**",
        )
    )
    for relative in UNTOUCHED:
        verdicts.append(
            toolbox.verdict(
                f"untouched-{Path(relative).stem}",
                toolbox.tree(root, relative).is_file(),
                f"本 GOAL 的边界：{relative} 必须在树且**一行未动**",
            )
        )
    # 判定面语义**一字未改**：本模块**不构造** `Decision`（advisory 不夺真相权）。
    # 判「构造」而不是判「提及」：docstring 里写「不改 `Decision`」是**声明边界**，
    # 判提及会把这条正确声明判成违规（措辞判据 ⇒ 假红）。
    verdicts.append(
        toolbox.verdict(
            "advisory-does-not-become-a-decision",
            "Decision(" not in module and "from packages.domain.decision" not in module,
            "本模块不得构造 `Decision`（advisory 不夺真相权是既有边界）",
        )
    )
    return verdicts


def wiring_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：两个组合根都接了闭包；读取入口是 `program_id`（不按位置猜）。"""
    verdicts: list[Any] = []
    for relative in ROOTS:
        text = toolbox.text(root, relative)
        wired = "review_outcome=review_outcome_builder(" in text
        verdicts.append(
            toolbox.verdict(
                f"root-{Path(relative).stem}-wires-the-builder",
                wired,
                f"{relative} 必须把产品闭包接上（否则出厂路径读不到上一轮判词）",
            )
        )
    module = toolbox.text(root, "packages/application/run_orchestration/review_outcome.py")
    verdicts.extend([
        toolbox.verdict(
            "read-entry-is-the-program",
            "for_program(program_id)" in module,
            "读取入口必须是「run → 程序归属 → 前序 run」（不按数组位置猜）",
        ),
        toolbox.verdict(
            "no-clock-in-the-reader",
            "time.time" not in module and "datetime.now" not in module,
            "读取器不得读进程时钟（确定性：同一份持久状态 ⇒ 同一个视图）",
        ),
        toolbox.verdict(
            "no-egress-in-the-reader",
            "requests" not in module and "urllib" not in module and "socket" not in module,
            "读取器零出网（只读 canonical）",
        ),
    ])
    return verdicts


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """全部本轮特有断言（收口验证器只调这一个入口）。"""
    return [
        *delivery_verdicts(root, toolbox),
        *state_verdicts(root, toolbox),
        *wiring_verdicts(root, toolbox),
    ]


__all__ = ["assertion_verdicts"]
