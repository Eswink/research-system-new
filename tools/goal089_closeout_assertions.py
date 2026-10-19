#!/usr/bin/env python3
"""GOAL-20261019-089 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…088 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 由
`tools/closeout_recheck_assertions.standard_verdicts` 承担；本文件**只写本 GOAL 特有的断言**。

三条主轴（逐条对应本 GOAL 的 EC）：

1. **EC-01 方向 → 问题 → 检索**：跨相材料进 run-chain 的参数材料（`resolve_cross_phase_material`
   + `input_material` 的 `cross_phase=` 形参）；悬空引用是**编译期**错误
   （`LOCAL_INPUT_PREFIXES` 之外的前缀一律按跨相引用处理）；歧义**点名**（不取最后一条）。
2. **EC-02 方向进 canonical**：`ProjectDefinition.direction` 是**可选**字段且与
   `renamed()` **分开**的 `with_direction` 在位；DTO 三处（读出 / 创建 / 修补）与
   `PUT /projects/{id}/direction` 在位；提示词那一段的渲染器在位。
3. **EC-03 迭代自动起来**：`ScheduleJob.PROGRAM_ADVANCE` + 内置定义 + `JOB_PURPOSE`；
   推进装配是**同一个** `advance_for`（端点与作业都调它，不建第二套）；作业的
   `executor_attached` 面在场。

**判据规则**（承 GOAL-027…088）：一律判**关系**；判词行**不含绝对路径**。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

#: 本轮**新增**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/run_orchestration/test_run_chain_reads_cross_phase_material.py", 9),
    ("tests/contracts/test_direction_to_question_protocol.py", 4),
    ("tests/api/test_project_direction.py", 13),
    ("tests/application/ops/test_program_advance_job.py", 5),
    ("tests/e2e/test_direction_to_question_to_retrieval.py", 2),
    ("tests/e2e/test_direction_to_question_to_retrieval_live.py", 1),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/application/run_orchestration/test_cross_phase_inputs.py",
    "tests/tooling/test_mainline_research_ladder_advances.py",
)

#: 落点常量（逐条点名；缺一即判红）。
MATERIAL = "packages/application/run_orchestration/phase_input_material.py"
CAPABILITIES = "packages/application/run_orchestration/phase_capabilities.py"
COMPILE_CROSS = "packages/application/protocol_compile/cross_phase_inputs.py"
PROTOCOL = "examples/protocols/direction_to_question_v1.yaml"
CONTRACTS = "examples/contracts/task_contracts.yaml"
PROJECTS_DOMAIN = "packages/domain/projects.py"
PROJECTS_DTO = "services/api/dto/projects.py"
PROJECTS_ROUTER = "services/api/routers/projects.py"
PROMPT = "packages/application/run_orchestration/retrieval_prompt.py"
SCHEDULES = "packages/domain/schedules.py"
ADVANCE = "services/api/program_advance.py"
ADVANCE_JOB = "services/api/program_advance_scheduler.py"
PROGRAMS_ROUTER = "services/api/routers/programs.py"

#: EC-01 的形态（跨相材料进参数材料）。
MATERIAL_ENTRY = "def resolve_cross_phase_material("
MATERIAL_INPUT = "def input_material("
MATERIAL_CROSS_PARAM = "cross_phase: tuple[CrossPhaseMaterial, ...] = ()"
MATERIAL_ENVELOPE = 'ENVELOPE_MARK_KEY = "declared_artifact"'
MATERIAL_AMBIGUOUS = "the run-chain argument would be undecidable"
MATERIAL_NAMED_MISSING = "carries no JSON object with the key"
CAPABILITIES_WIRES = "cross_phase = resolve_cross_phase_material("
CAPABILITIES_PASSES = "cross_phase=cross_phase"
LOCAL_PREFIXES = 'LOCAL_INPUT_PREFIXES: tuple[str, ...] = ("input-brief", "input-corpus")'
DANGLING_IS_CROSS_PHASE = "return not is_local_input_namespace(left)"
PROTOCOL_QUESTION = "task_contract: research_question_proposal"
PROTOCOL_RETRIEVAL_INPUT = "inputs: [question:research_question]"
CONTRACT_QUERY_RULES = "three to six"
CONTRACT_RETRIEVAL = "research_question_retrieval:"

#: EC-02 的形态（方向进 canonical，且**不是** name）。
PROJECT_FIELD = "direction: str | None = None"
PROJECT_MAX = "MAX_PROJECT_DIRECTION_LENGTH = 2000"
PROJECT_SETTER = "def with_direction("
PROJECT_RENAME_KEPT = "def renamed("
DTO_READ = "direction: str | None = None"
ROUTER_PUT = '@router.put("/projects/{project_id}/direction"'
ROUTER_PATCH_KEYS = '"name", "status", "direction"'
PROMPT_TITLE = 'DIRECTION_SECTION_TITLE = "PROJECT DIRECTION'
PROMPT_RENDER = "def render_direction_prompt("

#: EC-03 的形态（迭代自动起来，且只有**一条**装配链）。
JOB_CONST = 'PROGRAM_ADVANCE = "program_advance"'
JOB_PURPOSE = "按落库事实推进研究程序（第 N 轮终态后进入第 N+1 轮）"
JOB_BUILTIN = "name=ScheduleJob.PROGRAM_ADVANCE.value"
ADVANCE_ENTRY = "def advance_for("
ADVANCE_STORE = "def store_of("
ROUTER_USES_SHARED = "advance_for(deps, program_id)"
SCHEDULER_CLASS = "class ProgramAdvanceScheduler("
SCHEDULER_JOB = "job = ScheduleJob.PROGRAM_ADVANCE"

#: 成对用例（逐条点名）。
PAIR_CASES: tuple[tuple[str, str], ...] = (
    (
        "tests/application/run_orchestration/test_run_chain_reads_cross_phase_material.py",
        "test_the_producers_question_is_the_query_the_provider_receives",
    ),
    (
        "tests/application/run_orchestration/test_run_chain_reads_cross_phase_material.py",
        "test_a_different_question_changes_the_retrieval_query",
    ),
    (
        "tests/application/run_orchestration/test_run_chain_reads_cross_phase_material.py",
        "test_removing_the_producer_is_named_at_compile_time",
    ),
    (
        "tests/contracts/test_direction_to_question_protocol.py",
        "test_removing_the_question_phase_breaks_compilation_naming_the_producer",
    ),
    ("tests/api/test_project_direction.py", "test_sqlite_round_trip_keeps_the_direction"),
    (
        "tests/api/test_project_direction.py",
        "test_renamed_keeps_the_direction_and_with_direction_keeps_the_name",
    ),
    (
        "tests/api/test_project_direction.py",
        "test_patch_has_three_distinguishable_direction_states",
    ),
    (
        "tests/application/ops/test_program_advance_job.py",
        "test_the_job_calls_the_same_assembly_as_the_manual_endpoint",
    ),
    (
        "tests/application/ops/test_program_advance_job.py",
        "test_a_finished_round_advances_without_any_manual_call",
    ),
    (
        "tests/application/ops/test_program_advance_job.py",
        "test_a_declared_gate_still_stops_the_program_with_a_readable_reason",
    ),
    (
        "tests/e2e/test_direction_to_question_to_retrieval.py",
        "test_the_direction_reaches_the_question_phase_and_its_query_drives_the_search",
    ),
)

TEST_DEFINITION = re.compile(r"(?m)^\s*def test_")


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def collected_case_count(root: Path, relative: str) -> int:
    """模块的**真实用例条数**（正则按 `def test_`；本轮的判据文件不用 parametrize）。"""
    return len(TEST_DEFINITION.findall(_text(root, relative)))


def _material_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01(a)：跨相材料**进**参数材料，且歧义/缺件都点名。"""
    verdict = toolbox.verdict
    material = _text(root, MATERIAL)
    capabilities = _text(root, CAPABILITIES)
    return [
        verdict("material-resolver-is-in-tree", MATERIAL_ENTRY in material, MATERIAL_ENTRY),
        verdict("material-merge-keeps-one-shape", MATERIAL_INPUT in material, MATERIAL_INPUT),
        verdict(
            "material-declares-the-cross-phase-slot",
            MATERIAL_CROSS_PARAM in material,
            MATERIAL_CROSS_PARAM,
        ),
        verdict(
            "material-unwraps-the-declared-envelope",
            MATERIAL_ENVELOPE in material,
            MATERIAL_ENVELOPE,
        ),
        verdict(
            "material-names-an-ambiguous-object", MATERIAL_AMBIGUOUS in material, MATERIAL_AMBIGUOUS
        ),
        verdict(
            "material-names-a-missing-key",
            MATERIAL_NAMED_MISSING in material,
            MATERIAL_NAMED_MISSING,
        ),
        verdict(
            "capabilities-resolves-cross-phase",
            CAPABILITIES_WIRES in capabilities,
            CAPABILITIES_WIRES,
        ),
        verdict(
            "capabilities-passes-it-to-the-material",
            CAPABILITIES_PASSES in capabilities,
            CAPABILITIES_PASSES,
        ),
    ]


def _dangling_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01(b)：摘掉上游 ⇒ **编译期**点名（悬空引用不再被当成本地输入）。"""
    verdict = toolbox.verdict
    compile_text = _text(root, COMPILE_CROSS)
    return [
        verdict(
            "compile-declares-local-namespaces", LOCAL_PREFIXES in compile_text, LOCAL_PREFIXES
        ),
        verdict(
            "compile-treats-the-rest-as-cross-phase",
            DANGLING_IS_CROSS_PHASE in compile_text,
            DANGLING_IS_CROSS_PHASE,
        ),
    ]


def _declaration_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01(c)：出厂协议把两格按该形态写出来。"""
    verdict = toolbox.verdict
    protocol = _text(root, PROTOCOL)
    contracts = _text(root, CONTRACTS)
    return [
        verdict(
            "protocol-declares-the-question-phase", PROTOCOL_QUESTION in protocol, PROTOCOL_QUESTION
        ),
        verdict(
            "protocol-declares-the-cross-phase-input",
            PROTOCOL_RETRIEVAL_INPUT in protocol,
            PROTOCOL_RETRIEVAL_INPUT,
        ),
        verdict(
            "contract-bounds-the-query-shape",
            CONTRACT_QUERY_RULES in contracts,
            CONTRACT_QUERY_RULES,
        ),
        verdict(
            "contract-declares-the-retrieval-cell",
            CONTRACT_RETRIEVAL in contracts,
            CONTRACT_RETRIEVAL,
        ),
    ]


def _direction_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：方向是**自己的**字段（可选），且与改名语义分开。"""
    verdict = toolbox.verdict
    domain = _text(root, PROJECTS_DOMAIN)
    dto = _text(root, PROJECTS_DTO)
    router = _text(root, PROJECTS_ROUTER)
    prompt = _text(root, PROMPT)
    return [
        verdict("domain-has-an-optional-direction", PROJECT_FIELD in domain, PROJECT_FIELD),
        verdict("domain-bounds-the-length", PROJECT_MAX in domain, PROJECT_MAX),
        verdict("domain-has-a-separate-setter", PROJECT_SETTER in domain, PROJECT_SETTER),
        verdict(
            "the-rename-semantics-survives", PROJECT_RENAME_KEPT in domain, PROJECT_RENAME_KEPT
        ),
        verdict("dto-carries-the-direction", DTO_READ in dto, DTO_READ),
        verdict("router-has-the-direction-endpoint", ROUTER_PUT in router, ROUTER_PUT),
        verdict("router-patch-knows-the-new-key", ROUTER_PATCH_KEYS in router, ROUTER_PATCH_KEYS),
        verdict("prompt-has-a-direction-section", PROMPT_TITLE in prompt, PROMPT_TITLE),
        verdict("prompt-renders-it", PROMPT_RENDER in prompt, PROMPT_RENDER),
    ]


def _advance_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：作业进词表，且**端点与作业共用**同一条装配链。"""
    verdict = toolbox.verdict
    schedules = _text(root, SCHEDULES)
    advance = _text(root, ADVANCE)
    job = _text(root, ADVANCE_JOB)
    router = _text(root, PROGRAMS_ROUTER)
    return [
        verdict("schedule-vocabulary-has-the-job", JOB_CONST in schedules, JOB_CONST),
        verdict("schedule-declares-a-purpose", JOB_PURPOSE in schedules, JOB_PURPOSE),
        verdict("schedule-ships-a-builtin", JOB_BUILTIN in schedules, JOB_BUILTIN),
        verdict("advance-assembly-is-one-entry", ADVANCE_ENTRY in advance, ADVANCE_ENTRY),
        verdict("advance-names-a-missing-store", ADVANCE_STORE in advance, ADVANCE_STORE),
        verdict(
            "the-endpoint-uses-the-shared-entry", ROUTER_USES_SHARED in router, ROUTER_USES_SHARED
        ),
        verdict("the-job-is-a-periodic-daemon", SCHEDULER_CLASS in job, SCHEDULER_CLASS),
        verdict("the-job-declares-its-schedule", SCHEDULER_JOB in job, SCHEDULER_JOB),
    ]


def _case_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """成对用例在位 + 例数下界（删掉任一条用例即判红）。"""
    verdict = toolbox.verdict
    verdicts: list[Any] = []
    for relative, name in PAIR_CASES:
        verdicts.append(
            verdict(f"case-{name}", f"def {name}(" in _text(root, relative), f"{relative}:{name}")
        )
    for relative, floor in CASE_FLOORS:
        count = collected_case_count(root, relative)
        verdicts.append(
            verdict(
                f"case-floor-{Path(relative).stem}",
                count >= floor,
                f"{count} < {floor}" if count < floor else "",
            )
        )
    for relative in PRIOR_JUDGES:
        verdicts.append(verdict(f"prior-judge-{Path(relative).name}", (root / relative).is_file()))
    return verdicts


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有的断言（逐条一个判词；按 EC 分组，每组一个函数）。"""
    return [
        *_material_verdicts(root, toolbox),
        *_dangling_verdicts(root, toolbox),
        *_declaration_verdicts(root, toolbox),
        *_direction_verdicts(root, toolbox),
        *_advance_verdicts(root, toolbox),
        *_case_verdicts(root, toolbox),
    ]


__all__ = [
    "CASE_FLOORS",
    "PAIR_CASES",
    "assertion_verdicts",
    "collected_case_count",
]
