#!/usr/bin/env python3
"""GOAL-20261016-081 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…080 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 由
`tools/closeout_recheck_assertions.standard_verdicts` 承担；本文件**只写本 GOAL 特有的断言**。

五条主轴（逐条对应本 GOAL 的 EC）：

1. **EC-01/EC-02 摘录进提示词且**有界**：渲染器在树 + 上限常量**同一份**（不新造第二套）
   + 截断标注在树 + e2e 成对读数在树。
2. **EC-03 同源可核对**：读面载荷含 `truncated` 列 + 逐条逐字判据在树。
3. **EC-04 立题由检索派生**：**跨相输入**的编译期解析器在树 + 运行期解析在树 +
   性质**由产出方决定**（`TrustLabel` 在 `CompiledPhase` 上）+ 协议接线 +
   e2e 主判据与按压臂在树 + live 判据在树 + 读数归档（`CR=0`）。
4. **反编造门未被削弱**（本轮最容易做错的一处）：`_input_evidence` 的内容校验
   **仍在**（`store.verify` 那一句）+ `count_retrieved_sources` 的「不接受自称」口径
   **仍在**（只读 `SourceRecord`）+ **纯收紧**：`result_handler` 里跨相来源与组合根供给
   **并列**（两类都在 `_merged_evidence` 里）。
5. **EC-05 自举收口**：本验证器与断言集进两处射程（由 `entry_verdicts` 的规范页断言
   + `standard_verdicts` 的规模门覆盖）。

**五条纪律**（承 GOAL-027…080）：不读两树判词做一致性断言（输入即输出）；
判词行不含绝对路径；f-string 分片按**子串**；`defines` 收**含类方法**的版本；
**一律判关系**（抽函数会让钉调用点的判据假红）。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

#: 用例定义（模块级函数与类内方法**都算**：既有判据的形态两种都有）。
TEST_DEFINITION = re.compile(r"(?m)^\s*def test_")

#: 本轮**新增**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/run_orchestration/test_cross_phase_inputs.py", 11),
    ("tests/e2e/test_cross_phase_inputs_reach_the_plan_phase.py", 2),
    ("tests/application/test_retrieval_prompt_renderer.py", 14),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tools/verify_goal080_closeout.py",
    "tests/architecture/python/test_declared_input_sources.py",
    "tests/e2e/test_retrieval_context_reaches_the_session.py",
)

#: 落点常量（逐条点名；缺一即判红）。
COMPILE_RESOLVER = "packages/application/protocol_compile/cross_phase_inputs.py"
RUNTIME_RESOLVER = "packages/application/run_orchestration/cross_phase_inputs.py"
CARRY = "packages/application/run_orchestration/session_carry.py"
RESULT_HANDLER = "packages/application/run_orchestration/result_handler.py"
PROTOCOLS = "packages/domain/protocols.py"
TASK_EXECUTOR = "packages/application/run_orchestration/task_executor.py"
PROTOCOL = "examples/protocols/grounded_report_chain_v1.yaml"
E2E = "tests/e2e/test_cross_phase_inputs_reach_the_plan_phase.py"
LIVE = "tests/e2e/test_the_model_cites_the_retrieved_identifiers_live.py"
RENDERER = "packages/application/run_orchestration/retrieval_prompt.py"
READ_FACE = "packages/application/run_orchestration/retrieval_context.py"

#: 本轮引入的形态（**逐条点名**）。
COMPILE_ENTRY = "def resolve_cross_phase_inputs("
TRUST_FROM_PRODUCER = "def producer_trust_label("
RUNTIME_ENTRY = "def resolve_cross_phase_sources("
CARRY_ENTRY = "def build_session_carry("
LEDGER_FIELD = "cross_phase_evidence: tuple[Evidence, ...] = ()"
COMPILED_FIELD = "cross_phase_inputs: tuple[tuple[str, str, TrustLabel], ...]"
PROTOCOL_INPUT = "scouting:scouting_report"
INVALID_CODE = "CROSS_PHASE_INPUT_INVALID"

#: **反编造门的既有断言必须仍在**（本轮硬要求 (c)：不改弱）。
ANTI_FABRICATION: tuple[tuple[str, str], ...] = (
    (RESULT_HANDLER, "if not deps.store.verify(artifact_id):"),
    (RESULT_HANDLER, "declared input artifact {artifact_id} is not in the artifact store"),
    (RESULT_HANDLER, "if ledger.get_source(item.source_ref).trust_label is TrustLabel.RETRIEVED:"),
    (RESULT_HANDLER, "判据面**不**接受调用方的自称"),
)

#: **并列**结构：两类非自述来源在同一条通道里（缺任一类即判红）。
PARALLEL_SOURCES: tuple[str, ...] = (
    "deps.cross_phase_evidence",
    "deps.retrieved_evidence",
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
        (COMPILE_RESOLVER, COMPILE_ENTRY, "compile-resolver-in-tree"),
        (COMPILE_RESOLVER, TRUST_FROM_PRODUCER, "trust-label-from-producer"),
        (COMPILE_RESOLVER, INVALID_CODE, "invalid-reference-named"),
        (RUNTIME_RESOLVER, RUNTIME_ENTRY, "runtime-resolver-in-tree"),
        (CARRY, CARRY_ENTRY, "session-carry-in-tree"),
        (RESULT_HANDLER, LEDGER_FIELD, "ledger-carries-cross-phase"),
        (PROTOCOLS, COMPILED_FIELD, "compiled-phase-carries-trust"),
        (TASK_EXECUTOR, COMPILED_FIELD, "spec-context-carries-trust"),
        (PROTOCOL, PROTOCOL_INPUT, "protocol-declares-cross-phase"),
        (E2E, "点名**性质维**", "press-arm-names-the-nature-dimension"),
        (LIVE, "_assert_the_model_cited_what_it_saw", "live-judge-in-tree"),
        (RENDERER, "def render_retrieval_prompt(", "renderer-in-tree"),
        (READ_FACE, '"truncated": entry.truncated', "read-face-records-truncation"),
    )
    return [
        toolbox.verdict(name, needle in _text(root, relative), f"{relative} 缺 {needle!r}")
        for relative, needle, name in points
    ]


def _anti_fabrication_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """(c) 反编造门的既有断言逐条仍在 + 并列结构仍在。

    判词名**按序号**（不用 `hash()` —— 它受 `PYTHONHASHSEED` 影响，两树会把同一个断言
    打印成不同名字 ⇒ 逐行比对必红；实测踩过一次）。
    """
    verdicts: list[Any] = [
        toolbox.verdict(
            f"anti-fabrication-{index}",
            needle in _text(root, relative),
            f"{relative} 丢了 {needle!r}（门被削弱）",
        )
        for index, (relative, needle) in enumerate(ANTI_FABRICATION, start=1)
    ]
    handler = _text(root, RESULT_HANDLER)
    merged = handler.split("def _merged_evidence", 1)[-1].split("\ndef ", 1)[0]
    verdicts.extend(
        toolbox.verdict(
            f"parallel-source-{needle.split('.')[-1]}",
            needle in merged,
            "_merged_evidence 里缺 {needle}（两条来源不再并列）".format(needle=needle),
        )
        for needle in PARALLEL_SOURCES
    )
    return verdicts


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 特有的断言（公共面不在此处）。"""
    verdicts = [
        *_floor_verdicts(root, toolbox),
        *_placement_verdicts(root, toolbox),
        *_anti_fabrication_verdicts(root, toolbox),
    ]
    evidence = root / ".cursor/plans/goals/evidence/GOAL-20261016-081-ec04-live-citations.txt"
    verdicts.append(
        toolbox.verdict(
            "ec04-live-evidence-archived",
            evidence.is_file() and len(evidence.read_text(encoding="utf-8")) > 200,
            "live 读数未归档或过短",
        )
    )
    return verdicts


__all__ = ["CASE_FLOORS", "assertion_verdicts"]
