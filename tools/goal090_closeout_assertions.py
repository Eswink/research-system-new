#!/usr/bin/env python3
"""GOAL-20261020-090 收口复检的**本轮特有断言集**（EC-01…EC-05；2026-10-27 回填）。

**为什么是回填**：`tools/verify_goal090_closeout.py` **从未存在**（GOAL-096 正文的 `W-3`
记的就是这件事）。`_CUTOFF_SEQ = 64` 把序 58 挡在受判面外 ⇒ 它不判红。本文件 + 同名验证器
**补齐历史**：让「序 58 的收口资产齐备」此后可复检 —— 这**不等于**它当年过了门。

**五条主轴**（逐条对应本 GOAL 的 EC）：

1. **EC-01 工具维**：`minimum_tool_evidences` 在域/加载器/schema 三处落地；`CriterionInputs`
   有 `tool_evidence_count`；`count_tool_evidences` 在树（判据 = `tool_refs` 非空）；
   判据文件与例数下界；
2. **EC-02/EC-03 声明面**：出厂 `research_question_retrieval` 升版并声明工具维；
3. **EC-04 m0 见证**：`run_m0_with_witness.py` + `test_m0_witness_matches_the_tree.py` 在树；
   见证文件与三态语义的落点；
4. **EC-05 收口**：见证终态行常量、GOAL 的五个 EC **逐条 PASS**（它确实收口了）。
5. **回填本身**：本验证器被两份射程清单收录（回填 ≠ 过门禁）。

**判据规则**（承 GOAL-027…097）：一律判**关系**；判词行**不含绝对路径**。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

PROGRAM_SEQ = 58
GOAL_ID = "GOAL-20261020-090"

GOAL = ".cursor/plans/goals/GOAL-20261020-090-evidence-coverage-tool-dimension-and-m0-witness.md"
SELF = "tools/verify_goal090_closeout.py"
ASSERTIONS = "tools/goal090_closeout_assertions.py"

#: EC-01 的落点（逐条点名）。域 DTO 在 `packages/domain/tasks.py`，三态判定在
#: `packages/domain/acceptance.py`，计数在 `result_handler.py`，加载在 `tasks_loaders.py`。
TASKS_DTO = "packages/domain/tasks.py"
ACCEPTANCE = "packages/domain/acceptance.py"
RESULT_HANDLER = "packages/application/run_orchestration/result_handler.py"
TASKS_LOADER = "adapters/contracts/tasks_loaders.py"
SCHEMA = "schemas/task-contract.schema.json"
CONTRACTS = "examples/contracts/task_contracts.yaml"
TOOL_DIM_JUDGE = "tests/application/run_orchestration/test_evidence_coverage_tool_dimension.py"

#: EC-04 的落点。
WITNESS_ENTRY = "tools/run_m0_with_witness.py"
WITNESS_JUDGE = "tests/tooling/test_m0_witness_matches_the_tree.py"
WITNESS_FILE = ".cursor/plans/goals/evidence/M0-WITNESS.json"

SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"

#: 工具维的形态锚点（缺一即判红）。
FIELD = "minimum_tool_evidences"
COUNT_FN = "def count_tool_evidences("
INPUTS_FIELD = "tool_evidence_count"
#: 见证的终态行（m0 的判据就是它）。
TERMINAL_LINE = "PASS: profile=m0; 23 deterministic checks"
#: 见证被判文件的自我指涉白名单（见证不进受判面）。
SELF_REFERENTIAL = "SELF_REFERENTIAL"

TEST_DEFINITION = re.compile(r"(?m)^\s*def test_")


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _ec_statuses(goal: str) -> dict[str, str]:
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


def collected_case_count(root: Path, relative: str) -> int:
    return len(TEST_DEFINITION.findall(_text(root, relative)))


def _declared_in_retrieval_contract(contracts: str) -> bool:
    """`minimum_tool_evidences: 1` 是否落在 `research_question_retrieval` 的块里。

    判法：从该合约的键起，到下一个**顶格两空格**的合约键为止的那一段里找那一行
    （YAML 的缩进就是它的作用域；文本层面只需这一条）。搜索从 `tail[1:]` 起步 ⇒
    命中位置要**加 1** 回到 `tail` 的坐标系（本轮第一次写漏了这一步，判据自己判红）。
    """
    start = contracts.find("\n  research_question_retrieval:\n")
    if start == -1:
        return False
    tail = contracts[start + 1 :]
    match = re.search(r"\n  \w[\w_]*:\n", tail[1:])
    block = tail[: match.start() + 1] if match else tail
    return re.search(rf"\n {{8}}{FIELD}: 1\n", block) is not None


def _tool_dimension_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：工具维在域 / 判定 / 计数 / 加载 / schema 五处落地。"""
    verdict = toolbox.verdict
    tasks_dto = _text(root, TASKS_DTO)
    acceptance = _text(root, ACCEPTANCE)
    handler = _text(root, RESULT_HANDLER)
    return [
        verdict("ec01-domain-declares-the-field", FIELD in tasks_dto, f"{TASKS_DTO}:{FIELD}"),
        verdict(
            "ec01-domain-refuses-negative",
            "minimum_tool_evidences must be >= 0" in tasks_dto,
            "负值必须在构造期点名拒绝",
        ),
        verdict("ec01-acceptance-carries-the-count", INPUTS_FIELD in acceptance, INPUTS_FIELD),
        verdict("ec01-count-function-in-tree", COUNT_FN in handler, f"{RESULT_HANDLER}:{COUNT_FN}"),
        verdict(
            "ec01-count-keys-on-tool-refs",
            "tool_refs" in handler.split(COUNT_FN, 1)[1][:600] if COUNT_FN in handler else False,
            "计数判据必须是「`tool_refs` 非空」（不是别的代理）",
        ),
        verdict("ec01-loader-reads-the-field", FIELD in _text(root, TASKS_LOADER), TASKS_LOADER),
        verdict("ec01-schema-registers-the-field", FIELD in _text(root, SCHEMA), SCHEMA),
        verdict("ec01-judge-in-tree", (root / TOOL_DIM_JUDGE).is_file(), TOOL_DIM_JUDGE),
        verdict(
            "ec01-judge-has-ten-cases",
            collected_case_count(root, TOOL_DIM_JUDGE) >= 10,
            f"{collected_case_count(root, TOOL_DIM_JUDGE)} < 10",
        ),
    ]


def _declaration_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02/EC-03：出厂检索格**真的**声明了工具维。"""
    verdict = toolbox.verdict
    contracts = _text(root, CONTRACTS)
    return [
        verdict(
            "ec03-shipped-contract-declares-the-dimension",
            # 8 空格缩进（`acceptance_criteria` 项下的子键；本轮第一次写 6 空格是错的）。
            re.search(r"\n {8}minimum_tool_evidences: 1\n", contracts) is not None,
            "出厂检索格必须声明 `minimum_tool_evidences: 1`（不是夹具）",
        ),
        verdict(
            "ec03-the-declaration-is-in-the-retrieval-contract",
            _declared_in_retrieval_contract(contracts),
            "那一行必须在 `research_question_retrieval` 的块里（别处声明等于没声明）",
        ),
        verdict(
            "ec03-shipped-contract-is-bumped",
            "research_question_retrieval:" in contracts and "version: 1.1.0" in contracts,
            "出厂检索格升到 1.1.0（声明变更要可读）",
        ),
    ]


def _witness_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：m0 见证的入口、判据、文件与三态口径。"""
    verdict = toolbox.verdict
    witness = _text(root, WITNESS_ENTRY)
    return [
        verdict("ec04-witness-entry-in-tree", (root / WITNESS_ENTRY).is_file(), WITNESS_ENTRY),
        verdict("ec04-witness-judge-in-tree", (root / WITNESS_JUDGE).is_file(), WITNESS_JUDGE),
        verdict("ec04-witness-file-in-tree", (root / WITNESS_FILE).is_file(), WITNESS_FILE),
        verdict(
            "ec04-witness-names-the-terminal-line",
            TERMINAL_LINE in witness or TERMINAL_LINE in _text(root, WITNESS_JUDGE),
            f"见证口径必须点名终态行 `{TERMINAL_LINE}`",
        ),
        verdict(
            "ec04-self-referential-boundary-is-marked",
            SELF_REFERENTIAL in witness or SELF_REFERENTIAL in _text(root, WITNESS_JUDGE),
            "见证文件自身必须在受判面之外（自我指涉边界要可读）",
        ),
    ]


def _closeout_and_backfill_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-05：它**确实**收口了（五 EC 全 PASS）+ 回填登记（回填 ≠ 过门禁）。"""
    verdict = toolbox.verdict
    statuses = _ec_statuses(_text(root, GOAL))
    all_pass = bool(statuses) and all(value == "PASS" for value in statuses.values())
    return [
        verdict("ec05-goal-declares-five-ecs", len(statuses) == 5, sorted(statuses)),
        verdict(
            "ec05-every-ec-is-pass",
            all_pass,
            f"090 已收口 ⇒ 五个 EC 应逐条 PASS；实际 {statuses}",
        ),
        verdict("self-verifier-in-tree", (root / SELF).is_file(), SELF),
        verdict("self-assertions-in-tree", (root / ASSERTIONS).is_file(), ASSERTIONS),
        verdict(
            "listed-in-verifier-registry",
            "verify_goal090_closeout.py" in _text(root, VERIFIER_JUDGE),
            f"{VERIFIER_JUDGE} 必须登记本验证器",
        ),
        verdict(
            "listed-in-product-gate-scope",
            "verify_goal090_closeout.py" in _text(root, SCOPE_JUDGE),
            f"{SCOPE_JUDGE} 的 IN_SCOPE 必须收录本验证器",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有的断言（按 EC 分组；每组一个函数 —— 单函数 50 行门）。"""
    return [
        *_tool_dimension_verdicts(root, toolbox),
        *_declaration_verdicts(root, toolbox),
        *_witness_verdicts(root, toolbox),
        *_closeout_and_backfill_verdicts(root, toolbox),
    ]


__all__ = [
    "ASSERTIONS",
    "GOAL",
    "GOAL_ID",
    "PROGRAM_SEQ",
    "SELF",
    "TERMINAL_LINE",
    "assertion_verdicts",
    "collected_case_count",
]
