#!/usr/bin/env python3
"""GOAL-20261006-031 收口复检的**特有断言**（从 `verify_goal031_closeout.py` 拆出守 450 行门）。

**为什么单列**：收口验证器与工具集之间有 450 行硬上限（规模门），而断言又要逐条可读 ——
把「断言什么」（本模块）与「怎么跑 / 怎么打印」（验证器）分开，两边都在可读长度内。
**公共面一行不重写**：受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 / 规范页 /
记录自洽全部由 `tools/closeout_recheck_assertions.py` 提供（验证器直接调）。
**单向依赖**：本模块 import 工具箱（`closeout_recheck_tools`），验证器 import 本模块 +
标准断言集；无环。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class VerdictLike(Protocol):
    """判词的结构面（只读三个字段，不 import 标准集的类型）。"""

    name: str
    ok: bool
    detail: str


class Toolbox(Protocol):
    """`closeout_recheck_tools` 的结构面（按路径加载的模块满足它）。"""

    def tree(self, root: Path, relative: str) -> Path: ...
    def text(self, root: Path, relative: str) -> str: ...
    def verdict(self, name: str, ok: bool, detail: str = ...) -> Any: ...
    def defines(self, text_body: str, name: str) -> bool: ...
    def count_test_defs(self, text_body: str) -> int: ...
    def module_literal(self, text_body: str, assignment: str) -> object | None: ...
    def binding_tool_names(self, text_body: str, assignment: str) -> set[str]: ...


STANDARD = "tools/closeout_recheck_assertions.py"
SELF = "tools/verify_goal031_closeout.py"
TOOLING_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
GOAL = ".cursor/plans/goals/GOAL-20261006-031-capability-release-and-the-research-loop.md"

#: 本轮主干交付物（存在性 + AST 结构）。
POLICY = "examples/config/policy.yaml"
POLICY_CHECK = "packages/application/preflight/policy_check.py"
NCBI = "adapters/research_tools/ncbi.py"
PARSING = "adapters/research_tools/parsing.py"
PHASE_CAPABILITIES = "packages/application/run_orchestration/phase_capabilities.py"
TRIGGERS = "packages/application/run_orchestration/phase_capability_triggers.py"
OUTCOMES = "packages/application/run_orchestration/outcomes.py"
PHASE_RUNNER = "packages/application/run_orchestration/phase_runner.py"
DTO_INSPECTION = "services/api/dto/inspection.py"
LINEAGE_PROJECTION = "services/api/lineage_projection.py"
SESSION_TOOL_SUPPORT = "services/api/session_tool_support.py"
TOOL_PROVIDERS = "examples/config/tool_providers.yaml"
SNAPSHOT = "docs/api/openapi.m13.json"

#: EC-01 的 6 条放行（逐条，不写成类）。
RELEASED_READS: tuple[str, ...] = (
    "run.read",
    "claim.read",
    "deliverable.read",
    "budget.read",
    "experiment.read",
    "experiment_plan.read",
)
#: EC-02 的三态判词（逐字）。
VERDICTS: tuple[str, ...] = ("SUPPORTED", "UNSUPPORTED", "UNDETERMINED")
#: EC-03 的三个声明字段（逐字）。
DECLARED_FIELDS: tuple[str, ...] = (
    "requires_previous_ids",
    "phase_id",
    "artifact_from_previous",
)

#: 逐 EC：判据文件 + **例数下界**（下界取本 GOAL 实测的 `def test_` 声明数 —— 与
#: `closeout_recheck_tools.count_test_defs` 同一计数口径）。
EC_FILES: dict[str, tuple[tuple[str, ...], tuple[int, ...]]] = {
    "ec01": (
        (
            "tests/application/preflight/test_release_expansion_is_read_only.py",
            "tests/e2e/test_granted_read_capabilities_used_in_a_run.py",
        ),
        (16, 15),
    ),
    "ec02": (("tests/contracts/test_citation_validate_three_state.py",), (12,)),
    "ec03": (("tests/e2e/test_research_loop_second_round_derived.py",), (13,)),
    "ec04": (("tests/tooling/test_lineage_label_rename_is_complete.py",), (11,)),
}

#: 本轮新增的两条协议 → (路径, phase 数, 必须 `run_chain` 的 phase)。
NEW_PROTOCOLS: dict[str, tuple[str, int, tuple[str, ...]]] = {
    "granted_reads": (
        "examples/protocols/granted_reads_used_in_a_run_v1.yaml",
        2,
        ("probe", "review"),
    ),
    "two_round_loop": (
        "examples/protocols/two_round_research_loop_v1.yaml",
        2,
        ("round1", "round2"),
    ),
}

#: 本轮的判词归档（进树 + 二进制写盘；逐文件核存在性与 CR=0）。
EVIDENCE_ARCHIVES: tuple[str, ...] = (
    ".cursor/plans/goals/evidence/GOAL-20261006-031-ec01-release-ledger.txt",
    ".cursor/plans/goals/evidence/GOAL-20261006-031-ec01-refutation-verdicts.txt",
    ".cursor/plans/goals/evidence/GOAL-20261006-031-ec01-run-usage-evidence.txt",
    ".cursor/plans/goals/evidence/GOAL-20261006-031-ec02-release-and-pin-ledger.txt",
    ".cursor/plans/goals/evidence/GOAL-20261006-031-ec03-two-arms-and-derivation.txt",
    ".cursor/plans/goals/evidence/GOAL-20261006-031-ec04-rename-and-zero-hit-ledger.txt",
)


def ec_verdicts(root: Path, toolbox: Toolbox) -> list[VerdictLike]:
    """逐 EC：判据文件在树 + 例数下界（缺文件、例数掉下去，两向都判红）。"""
    verdicts: list[VerdictLike] = []
    for ec_id, (files, floors) in sorted(EC_FILES.items()):
        for relative, floor in zip(files, floors, strict=True):
            source = toolbox.text(root, relative)
            count = toolbox.count_test_defs(source)
            verdicts.append(
                toolbox.verdict(
                    f"judge-{ec_id}-{Path(relative).name}",
                    bool(source) and count >= floor,
                    f"{count} >= {floor}",
                )
            )
    return verdicts


def _run_completed_carries_the_skip_facts(root: Path, runner: str) -> bool:
    """`run.completed` 的载荷是否**带上跳过事实**（**结构判据**，与在哪个模块无关）。

    **为什么改这里**（GOAL-20261010-043）：本判据原按**文本**要求在 `phase_runner.py` 里
    出现 `"skipped"` 字面量。GOAL-20261009-042 EC-03 把 `run.completed` 的载荷抽成
    **唯一构造点**（`run_completion_payload.py` —— 消除「两处各写一份字段清单」的漂移
    风险）⇒ 那个字面量**搬了家**，行为**逐字保持**（同一份载荷、同一个键），而本判据
    因**盯错位置**判负。**判行为与判位置是两件事**（与 `MEM-20261010-212` 同一族）。

    改法：接受两种形态 ——
    ① 载荷在 `runner` 里直接构造（旧形态，字面量在原地）；
    ② 载荷由**被 runner 调用的构造点**产出（新形态）⇒ 顺着 `run_completion_payload`
       的导入找一个模块，在其源码里找那个键。
    **受判面等价**：仍然要求「`run.completed` 的载荷带上 `skipped` 键」这一件事；
    **不**放宽（两种形态都没找到 ⇒ 判负）。
    """
    if '"skipped"' in runner:
        return True
    builder = "run_completion_payload.py"
    candidate = root / "packages" / "application" / "run_orchestration" / builder
    if not candidate.is_file():
        return False
    return '"skipped"' in candidate.read_text(encoding="utf-8", errors="replace")


def _declared_field_names(source: str, class_name: str) -> set[str]:
    """某数据类 / 模型类的字段注解名集合（AST 读声明，不靠文本搜索）。"""
    import ast

    if not source:
        return set()
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                item.target.id
                for item in node.body
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
            }
    return set()


def ec01_verdicts(root: Path, toolbox: Toolbox) -> list[VerdictLike]:
    """EC-01：6 条放行逐条在 `allow` + 镜像表同轮同步（逐条断言）。"""
    policy = toolbox.text(root, POLICY)
    mirror = toolbox.text(root, POLICY_CHECK)
    verdicts: list[VerdictLike] = []
    for capability in RELEASED_READS:
        verdicts.append(
            toolbox.verdict(
                f"ec01-policy-allows-{capability}",
                f"capability: {capability}" in policy,
            )
        )
        verdicts.append(
            toolbox.verdict(
                f"ec01-mirror-carries-{capability}",
                f'"{capability}":' in mirror,
            )
        )
    return verdicts


def ec02_verdicts(root: Path, toolbox: Toolbox) -> list[VerdictLike]:
    """EC-02：三态常量 + 判定函数在树 + 取数点唯一（`elink.fcgi` 恰 1 次）。"""
    parsing = toolbox.text(root, PARSING)
    ncbi = toolbox.text(root, NCBI)
    verdicts: list[VerdictLike] = [
        toolbox.verdict(
            "ec02-three-verdict-constants",
            all(f'CITATION_{item} = "{item}"' in parsing for item in VERDICTS),
        ),
        toolbox.verdict(
            "ec02-validate-function-present",
            toolbox.defines(parsing, "validate_citation_support"),
        ),
        toolbox.verdict(
            "ec02-single-fetch-point",
            ncbi.count('"elink.fcgi"') == 1,
            f"{ncbi.count(chr(34) + 'elink.fcgi' + chr(34))} 处",
        ),
    ]
    return verdicts


def ec03_verdicts(root: Path, toolbox: Toolbox) -> list[VerdictLike]:
    """EC-03：三个声明字段 + 触发判定模块 + 跳过贯通到任务终局读面。"""
    fields = _declared_field_names(toolbox.text(root, PHASE_CAPABILITIES), "RunChainCall")
    triggers = toolbox.text(root, TRIGGERS)
    outcomes = toolbox.text(root, OUTCOMES)
    runner = toolbox.text(root, PHASE_RUNNER)
    verdicts: list[VerdictLike] = [
        toolbox.verdict(
            f"ec03-declared-field-{field_name}",
            field_name in fields,
            f"{sorted(fields)}",
        )
        for field_name in DECLARED_FIELDS
    ]
    verdicts.extend([
        toolbox.verdict(
            "ec03-trigger-judgements-present",
            all(
                toolbox.defines(triggers, name)
                for name in ("planned_in_this_phase", "should_skip", "select_artifact_id")
            ),
        ),
        toolbox.verdict(
            "ec03-skip-reaches-the-task-outcome",
            toolbox.defines(outcomes, "TaskOutcome")
            and "skipped" in _declared_field_names(outcomes, "TaskOutcome"),
        ),
        toolbox.verdict(
            "ec03-run-completed-carries-the-skip-facts",
            _run_completed_carries_the_skip_facts(root, runner),
        ),
    ])
    return verdicts


def ec04_verdicts(root: Path, toolbox: Toolbox) -> list[VerdictLike]:
    """EC-04：两个 DTO 字段是 `text` + 快照同步 + 旧名在血缘上下文零命中。"""
    dto = toolbox.text(root, DTO_INSPECTION)
    snapshot = toolbox.text(root, SNAPSHOT)
    verdicts: list[VerdictLike] = []
    for class_name in ("LineageNodeDto", "ProjectLineageNodeDto"):
        fields = _declared_field_names(dto, class_name)
        verdicts.append(
            toolbox.verdict(
                f"ec04-{class_name}-declares-text",
                "text" in fields and "label" not in fields,
                f"{sorted(fields)}",
            )
        )
    verdicts.extend([
        toolbox.verdict(
            "ec04-snapshot-declares-text",
            '"text"' in snapshot and '"label"' not in snapshot,
        ),
        toolbox.verdict(
            "ec04-old-name-absent-from-the-producer",
            "text=text" in toolbox.text(root, LINEAGE_PROJECTION)
            and "label=label" not in toolbox.text(root, LINEAGE_PROJECTION),
        ),
    ])
    return verdicts


def _phase_flags(source: str) -> tuple[int, dict[str, str]]:
    """极简读协议 YAML 的 phase 面（只用标准库，不引入 yaml 依赖）。"""

    ids: list[str] = []
    flags: dict[str, str] = {}
    current: str | None = None
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("- id: "):
            current = stripped.split(":", 1)[1].strip()
            ids.append(current)
        elif stripped.startswith("capability_execution:") and current is not None:
            flags[current] = stripped.split(":", 1)[1].strip()
    return len(ids), flags


def protocol_verdicts(root: Path, toolbox: Toolbox) -> list[VerdictLike]:
    """两条新协议：phase 数 + 必须声明 `capability_execution: run_chain` 的 phase。"""
    verdicts: list[VerdictLike] = []
    for label, (relative, phase_count, run_chain_phases) in sorted(NEW_PROTOCOLS.items()):
        count, flags = _phase_flags(toolbox.text(root, relative))
        verdicts.append(
            toolbox.verdict(
                f"protocol-phases-{label}",
                count == phase_count,
                f"{count} == {phase_count}",
            )
        )
        for phase_id in run_chain_phases:
            verdicts.append(
                toolbox.verdict(
                    f"protocol-run-chain-{label}-{phase_id}",
                    flags.get(phase_id) == "run_chain",
                    f"capability_execution={flags.get(phase_id)!r}",
                )
            )
    return verdicts


def onboarding_verdicts(root: Path, toolbox: Toolbox) -> list[VerdictLike]:
    """EC-02 的承接：目录声明 `citation.validate` + 出厂绑定表条目。"""
    providers = toolbox.text(root, TOOL_PROVIDERS)
    declared = False
    for line in providers.splitlines():
        if line.strip() == "- citation.validate":
            declared = True
    bound = toolbox.binding_tool_names(
        toolbox.text(root, SESSION_TOOL_SUPPORT), "DEFAULT_SESSION_TOOL_BINDINGS"
    )
    return [
        toolbox.verdict("citation-validate-declared-in-catalog", declared),
        toolbox.verdict(
            "citation-validate-in-factory-binding-table",
            "citation.validate" in bound,
            f"{sorted(bound)}",
        ),
    ]


def archive_verdicts(root: Path, toolbox: Toolbox) -> list[VerdictLike]:
    """本轮的判词归档在树（逐文件核存在性 + 二进制写盘 ⇒ CR=0）。"""
    verdicts: list[VerdictLike] = []
    for relative in EVIDENCE_ARCHIVES:
        path = toolbox.tree(root, relative)
        if not path.is_file():
            verdicts.append(toolbox.verdict(f"archive-{Path(relative).name}", False, "不在树"))
            continue
        raw = path.read_bytes()
        cr_count = raw.count(b"\r")
        verdicts.append(
            toolbox.verdict(
                f"archive-{Path(relative).name}",
                bool(raw) and cr_count == 0,
                f"bytes={len(raw)} cr={cr_count}",
            )
        )
    return verdicts


def tooling_scope_verdict(root: Path, toolbox: Toolbox) -> Any:
    """`IN_SCOPE` 纯收紧：本轮新增的验证器必须已在清单里。"""
    literal = toolbox.module_literal(toolbox.text(root, TOOLING_JUDGE), "IN_SCOPE")
    listed = isinstance(literal, tuple) and SELF in literal
    return toolbox.verdict(f"in-scope-{SELF}", listed)


__all__ = [
    "EVIDENCE_ARCHIVES",
    "SELF",
    "assertion_verdicts",
]


def assertion_verdicts(root: Path, toolbox: Toolbox) -> list[Any]:
    """本 GOAL 特有的**全部**断言（验证器按顺序调用；`toolbox` = 按路径加载的工具集）。"""
    built: list[Any] = []
    built.extend(ec_verdicts(root, toolbox))
    built.extend(ec01_verdicts(root, toolbox))
    built.extend(ec02_verdicts(root, toolbox))
    built.extend(ec03_verdicts(root, toolbox))
    built.extend(ec04_verdicts(root, toolbox))
    built.extend(protocol_verdicts(root, toolbox))
    built.extend(onboarding_verdicts(root, toolbox))
    built.extend(archive_verdicts(root, toolbox))
    built.append(tooling_scope_verdict(root, toolbox))
    return built
