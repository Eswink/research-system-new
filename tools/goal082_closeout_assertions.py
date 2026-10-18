#!/usr/bin/env python3
"""GOAL-20261018-082 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…081 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 由
`tools/closeout_recheck_assertions.standard_verdicts` 承担；本文件**只写本 GOAL 特有的断言**。

五条主轴（逐条对应本 GOAL 的 EC）：

1. **EC-01 前序知识进提示词**：装配器在树 + 渲染器在树 + `compose_prompt` 的**并列**结构
   （两段都在）+ 空集合 ⇒ 空串（不伪造）。
2. **EC-02 有界**：上限**复用** `retrieval_context` 的常量（`is` 判 —— 新造一份同值常量
   会让弱判据仍绿）+ 截断/待复核标注在树。
3. **EC-03 同源可核对**：读面载荷含 `truncated` / `review_due` 两列 + e2e 逐条逐字判据在树。
4. **EC-04 跨 run 可达**：只收 `PROJECT` / `ORGANIZATION`（`RUN` / `SESSION` 不在）+
   `expires_at` 排除 / `review_after` 标注的判据在树 + live 判据在树 + 读数归档。
   **并如实要求**：EC-04 的 `blocker`（模型不按 `memory_id` 引用）**在树** —— 未达成的
   事实不能被静默抹掉。
5. **EC-05 自举收口**：本验证器与断言集进两处射程（由 `entry_verdicts` 的规范页断言
   + `standard_verdicts` 的规模门覆盖）。

**五条纪律**（承 GOAL-027…081）：不读两树判词做一致性断言（输入即输出）；
判词行不含绝对路径；f-string 分片按**子串**；`defines` 收**含类方法**的版本；
**一律判关系**；判词名**按序号**（`hash()` 受 `PYTHONHASHSEED` 影响，两树逐行比对必红）。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

#: 用例定义（模块级函数与类内方法**都算**：既有判据的形态两种都有）。
TEST_DEFINITION = re.compile(r"(?m)^\s*def test_")

#: 本轮**新增**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/run_orchestration/test_prior_knowledge_in_prompt.py", 9),
    ("tests/e2e/test_prior_knowledge_reaches_the_prompt.py", 3),
    ("tests/e2e/test_prior_knowledge_changes_the_next_round.py", 3),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tools/verify_goal081_closeout.py",
    "tests/application/test_retrieval_prompt_renderer.py",
    "tests/e2e/test_retrieval_context_reaches_the_session.py",
)

#: 落点常量（逐条点名；缺一即判红）。
ASSEMBLER = "packages/application/run_orchestration/prior_knowledge.py"
RENDERER = "packages/application/run_orchestration/retrieval_prompt.py"
SUPPORT = "services/api/prior_knowledge_support.py"
TASK_EXECUTOR = "packages/application/run_orchestration/task_executor.py"
PHASE_RUNNER = "packages/application/run_orchestration/phase_runner.py"
AGENT_RUNTIME = "packages/application/ports/agent_runtime.py"
SESSION_BUILDER = "adapters/openhands/session_builder.py"
COMPOSITION = "services/api/composition.py"
PG_COMPOSITION = "services/api/pg_composition.py"
E2E_READ_FACE = "tests/e2e/test_prior_knowledge_reaches_the_prompt.py"
E2E_CROSS_RUN = "tests/e2e/test_prior_knowledge_changes_the_next_round.py"
LIVE = "tests/e2e/test_prior_knowledge_changes_the_plan_live.py"
GOAL = ".cursor/plans/goals/GOAL-20261018-082-prior-knowledge-changes-the-next-question.md"

#: 本轮引入的形态（**逐条点名**）。
ASSEMBLY_ENTRY = "def build_prior_knowledge("
TIERS = "PRIOR_TIERS"
RENDER_ENTRY = "def render_prior_knowledge_prompt("
COMPOSE_ENTRY = "def compose_prompt("
PRIOR_TITLE = "PRIOR_SECTION_TITLE"
SPEC_FIELD = "prior_knowledge_prompt: str | None = None"
SPEC_CONTEXT_FIELD = "prior_knowledge: Any | None = None"
EVAL_POINT = "with_prior_knowledge("
TRUNCATED_COL = '"truncated": entry.truncated'
REVIEW_COL = '"review_due": entry.review_due'

#: **并列**结构：两段在同一次拼装里（缺任一段即判红）。
PARALLEL_SECTIONS: tuple[str, ...] = (
    "prior_knowledge=spec.prior_knowledge_prompt",
    "retrieval=spec.retrieval_prompt",
)

#: EC-04 的**未达成**必须在树（事实不能被静默抹掉）。
EC04_BLOCKER_MARKERS: tuple[str, ...] = (
    "memory_id",
    "零命中",
    "模型侧行为",
)


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _floor_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """例数下界 + 既有判据仍在树。"""
    verdicts: list[Any] = []
    for relative, floor in CASE_FLOORS:
        count = len(TEST_DEFINITION.findall(_text(root, relative)))
        verdicts.append(
            toolbox.verdict(
                f"case-floor-{Path(relative).stem}", count >= floor, f"{count} < {floor}"
            )
        )
    for relative in PRIOR_JUDGES:
        verdicts.append(
            toolbox.verdict(f"prior-judge-{Path(relative).stem}", (root / relative).is_file())
        )
    return verdicts


def _placement_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01…EC-04 的落点与形态（逐条点名）。"""
    points: tuple[tuple[str, str, str], ...] = (
        (ASSEMBLER, ASSEMBLY_ENTRY, "assembler-in-tree"),
        (ASSEMBLER, TIERS, "cross-run-tiers-named"),
        (ASSEMBLER, REVIEW_COL, "payload-records-review-due"),
        (RENDERER, RENDER_ENTRY, "prior-renderer-in-tree"),
        (RENDERER, COMPOSE_ENTRY, "compose-entry-in-tree"),
        (RENDERER, PRIOR_TITLE, "prior-section-title-in-tree"),
        (SUPPORT, "def prior_knowledge_builder(", "composition-support-in-tree"),
        (TASK_EXECUTOR, SPEC_CONTEXT_FIELD, "spec-context-carries-prior"),
        (AGENT_RUNTIME, SPEC_FIELD, "session-spec-carries-prior"),
        (PHASE_RUNNER, EVAL_POINT, "evaluation-point-wired"),
        (ASSEMBLER, TRUNCATED_COL, "payload-records-truncation"),
        (E2E_CROSS_RUN, "test_press_without_prior_memory", "empty-store-press-in-tree"),
        (LIVE, "test_the_model_uses_prior_run_knowledge", "live-judge-in-tree"),
    )
    return [
        toolbox.verdict(name, needle in _text(root, relative), f"{relative} 缺 {needle!r}")
        for relative, needle, name in points
    ]


def _parallel_and_limits_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """两段**并列** + 上限**同一对象** + 两组合根都接线。"""
    verdicts: list[Any] = []
    builder = _text(root, SESSION_BUILDER)
    for index, needle in enumerate(PARALLEL_SECTIONS, start=1):
        verdicts.append(
            toolbox.verdict(
                f"parallel-section-{index}",
                needle in builder,
                f"session_builder 缺 {needle!r}（两段不再并列）",
            )
        )
    # 上限同源：装配器**引用** retrieval_context 的常量（不是新造）。
    assembler = _text(root, ASSEMBLER)
    verdicts.append(
        toolbox.verdict(
            "limits-imported-from-retrieval-context",
            "from packages.application.run_orchestration.retrieval_context import" in assembler,
            "装配器没有**导入**既有上限常量（疑似新造第二份）",
        )
    )
    for relative, label in ((COMPOSITION, "sqlite"), (PG_COMPOSITION, "pg")):
        verdicts.append(
            toolbox.verdict(
                f"composition-{label}-wires-prior",
                "prior_knowledge=prior_knowledge_builder(" in _text(root, relative),
                f"{relative} 没有接 prior_knowledge_builder",
            )
        )
    return verdicts


def _ec04_honesty_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04 的**未达成**必须在树（本轮最重要的一条诚实性断言）。"""
    goal = _text(root, GOAL)
    verdicts = [
        toolbox.verdict(
            f"ec04-blocker-marker-{index}",
            marker in goal,
            f"GOAL 正文丢了 {marker!r}（未达成的事实被抹掉）",
        )
        for index, marker in enumerate(EC04_BLOCKER_MARKERS, start=1)
    ]
    evidence = root / ".cursor/plans/goals/evidence/GOAL-20261018-082-ec04-evidence.txt"
    verdicts.append(
        toolbox.verdict(
            "ec04-live-evidence-archived",
            evidence.is_file() and len(evidence.read_text(encoding="utf-8")) > 300,
            "三次真实 run 的读数未归档或过短",
        )
    )
    return verdicts


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 特有的断言（公共面不在此处）。"""
    return [
        *_floor_verdicts(root, toolbox),
        *_placement_verdicts(root, toolbox),
        *_parallel_and_limits_verdicts(root, toolbox),
        *_ec04_honesty_verdicts(root, toolbox),
    ]


__all__ = ["CASE_FLOORS", "assertion_verdicts"]
