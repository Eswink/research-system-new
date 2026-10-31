#!/usr/bin/env python3
"""GOAL-20261031-102 的本轮特有断言（产品面 + 记录面）。

与 `tools/goal023…101_closeout_assertions.py` 同形：只写**本 GOAL 特有**的断言，公共面
（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 / 规范页）由
`closeout_recheck_assertions.standard_verdicts` 判，一行不重写。

**五组**：
1. **supersedes 面**：域字段 + 链校验在树、两侧序列化都带上父指针、migration 在树；
2. **改稿闭环**：装配模块与引用判据在树、附加链顺序钉住（改稿 → 投稿包 → 应答信）、
   合约声明 `revised_manuscript` 与引用义务、旧形状兼容的判据在树；
3. **投稿包**：装配/渲染/映射三模块在树、27 角色闭集、五件制品名、十一相协议与
   七产物报告相、两份判据文件的用例数下界；
4. **期刊闭集**：声明面在树且无评分字段、解析/校验面在树、合约镜像；
5. **登记面**：两个 `tools/` 脚本进 `_VERIFIERS` 与 `IN_SCOPE`（纯收紧：只增不删）。

每条断言都**只读树**（零出网、零时钟、不写盘），与 GOAL-023…101 的断言集同一纪律。
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

#: supersedes 面的落点（逐条点名；缺一即判红）。
DOMAIN = "packages/domain/artifacts.py"
SQLITE_STORE = "adapters/sqlite/artifact_store.py"
SQLITE_DB = "adapters/sqlite/db.py"
PG_STORE = "adapters/postgres/artifact_store.py"
PG_MIGRATION = "adapters/postgres/migrations/030_artifact_supersedes.sql"
DOMAIN_JUDGE = "tests/domain/test_artifacts.py"
SQLITE_JUDGE = "tests/adapters/sqlite/test_artifact_store.py"
PG_JUDGE = "tests/postgres/test_artifact_supersedes_pg.py"

#: 改稿闭环的落点。
REVISION = "packages/application/run_orchestration/revision_assembly.py"
REPORT_EXTRAS = "packages/application/run_orchestration/report_extras.py"
MANUSCRIPT_ASSEMBLY = "packages/application/run_orchestration/manuscript_assembly.py"
CONTRACTS = "examples/contracts/task_contracts.yaml"
REVISION_JUDGE = "tests/application/test_revision_closure.py"

#: 投稿包的落点。
SUBMISSION = "packages/application/run_orchestration/submission_assembly.py"
RENDERERS = "packages/application/run_orchestration/submission_renderers.py"
CREDIT_ROLES = "packages/application/deliverable/credit_roles.py"
PROTOCOL = "examples/protocols/direction_to_manuscript_v1.yaml"
SUBMISSION_JUDGE = "tests/application/test_submission_package.py"
E2E_JUDGE = "tests/e2e/test_goal102_product_path.py"

#: 期刊闭集的落点。
JOURNALS = "examples/config/journals.yaml"
JOURNAL_SELECTION = "packages/application/deliverable/journal_selection.py"
JOURNAL_JUDGE = "tests/application/test_journal_selection.py"

#: 登记面（两份清单判据）。
VERIFIER_REGISTRY = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
GATE_SCOPE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"

#: 五件投稿制品（**逐字**；协议产物与渲染面按这些名字对拍）。
FIVE_ARTIFACTS: tuple[str, ...] = (
    "cover_letter.md",
    "author_contributions.md",
    "conflicts_of_interest.md",
    "data_availability.md",
    "supplementary.md",
)
#: 期刊闭集里**不许出现**的评分/排名字段（声明面不是评价面）。
RANKING_TERMS: tuple[str, ...] = ("impact factor", "impact_factor", "quartile", "h-index")
#: 判据文件的用例数下界（口径 = `def test_` 的条数；取本轮实测值 ⇒ 删一条即判红）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    (REVISION_JUDGE, 8),
    (SUBMISSION_JUDGE, 11),
    (JOURNAL_JUDGE, 9),
    (E2E_JUDGE, 6),
)


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _ast_of(source: str) -> ast.Module | None:
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def _defines(source: str, name: str) -> bool:
    tree = _ast_of(source)
    if tree is None:
        return False
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
        for node in ast.walk(tree)
    )


def _assign_names(source: str, name: str) -> list[str]:
    """模块级 `NAME = [...] / {...}` 容器字面量的**顶层字符串元素**（不 import）。

    `NAME: type = ...`（带注解的赋值）与裸赋值**都认**（本仓的闭集常量两种写法都有）。
    """
    tree = _ast_of(source)
    if tree is None:
        return []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        if not any(isinstance(t, ast.Name) and t.id == name for t in targets):
            continue
        if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            return [
                e.value
                for e in value.elts
                if isinstance(e, ast.Constant) and isinstance(e.value, str)
            ]
        if isinstance(value, ast.Dict):
            return [
                k.value
                for k in value.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, str)
            ]
    return []


def _count_defs(source: str) -> int:
    tree = _ast_of(source)
    if tree is None:
        return 0
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    )


def supersedes_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：域字段 + 链校验 + 两侧序列化 + migration，各点其名。"""
    domain = _text(root, DOMAIN)
    sqlite_store = _text(root, SQLITE_STORE)
    pg_store = _text(root, PG_STORE)
    return [
        toolbox.verdict(
            "domain-declares-supersedes-field",
            "supersedes: str | None = None" in domain,
            "域 Artifact 缺少 supersedes 字段（缺省 None）",
        ),
        toolbox.verdict(
            "domain-declares-the-chain-validator",
            _defines(domain, "validate_supersedes"),
            "域缺少 validate_supersedes 链校验",
        ),
        toolbox.verdict(
            "domain-names-all-three-violations",
            all(
                marker in domain
                for marker in ("supersedes cycle", "outside run", "does not exist in run")
            ),
            "链校验必须逐条点名：成环 / 跨 run / 目标缺席",
        ),
        toolbox.verdict(
            "sqlite-schema-carries-the-column",
            "supersedes TEXT" in _text(root, SQLITE_DB),
            "SQLite SCHEMA_SQL 没有 supersedes 列",
        ),
        toolbox.verdict(
            "sqlite-store-round-trips-supersedes",
            sqlite_store.count("supersedes") >= 4,
            "SQLite 存储面带 supersedes 的点少于 4（insert/update/读回）："
            f"{sqlite_store.count('supersedes')}",
        ),
        toolbox.verdict(
            "pg-migration-in-tree",
            "ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS supersedes TEXT"
            in _text(root, PG_MIGRATION),
            f"{PG_MIGRATION} 缺失或没有加列语句",
        ),
        toolbox.verdict(
            "pg-store-round-trips-supersedes",
            pg_store.count("supersedes") >= 4,
            f"PG 存储面带 supersedes 的点少于 4：{pg_store.count('supersedes')}",
        ),
        toolbox.verdict(
            "digest-is-content-addressed-only",
            "父指针" in _text(root, DOMAIN) or "supersedes 是元数据" in _text(root, DOMAIN),
            "域注释必须写明父指针不进内容哈希（digest 仍是内容寻址）",
        ),
        toolbox.verdict(
            "domain-judge-present", toolbox.tree(root, DOMAIN_JUDGE).is_file(), DOMAIN_JUDGE
        ),
        toolbox.verdict(
            "sqlite-judge-present", toolbox.tree(root, SQLITE_JUDGE).is_file(), SQLITE_JUDGE
        ),
        toolbox.verdict("pg-judge-present", toolbox.tree(root, PG_JUDGE).is_file(), PG_JUDGE),
    ]


def revision_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：装配模块 + 引用判据 + 附加链顺序 + 合约义务 + 判据下界。"""
    revision = _text(root, REVISION)
    extras = _text(root, REPORT_EXTRAS)
    contracts = _text(root, CONTRACTS)
    author_block = contracts.split("  author_response:", 1)[1].split("\n  submission_package:", 1)[
        0
    ]
    order_ok = (
        extras.index("revision_closure_step(")
        < extras.index("maybe_assemble_submission(")
        < extras.index("maybe_assemble_response_letter(")
    )
    return [
        toolbox.verdict(
            "revision-module-in-tree",
            _defines(revision, "revision_closure_step")
            and _defines(revision, "revision_closure_of_run"),
            "改稿装配/读面模块缺少入口函数",
        ),
        toolbox.verdict(
            "revision-names-the-v2-artifact",
            'MANUSCRIPT_V2_NAME = "manuscript_v2.md"' in revision,
            "改稿制品名没有钉成常量",
        ),
        toolbox.verdict(
            "revision-error-is-in-the-manuscript-family",
            "class RevisionError(ManuscriptError)" in revision,
            "RevisionError 必须是 ManuscriptError 家族（报告任务同一收敛）",
        ),
        toolbox.verdict(
            "citation-validator-in-tree",
            _defines(revision, "validate_action_references"),
            "缺少 action_taken 引用判据",
        ),
        toolbox.verdict(
            "extras-chain-order-is-revision-submission-letter",
            order_ok,
            "附加链顺序必须是 改稿 → 投稿包 → 应答信（引用判据要指着 v2 在场）",
        ),
        toolbox.verdict(
            "contract-demands-the-revised-block",
            "revised_manuscript" in author_block and "manuscript_v2.md" in author_block,
            "author_response 合约必须声明第二块 revised_manuscript 与 v2 引用义务",
        ),
        toolbox.verdict(
            "manuscript-assembly-hook-in-place",
            "assemble_report_extras" in _text(root, MANUSCRIPT_ASSEMBLY),
            "手稿装配面没有接附加链（改稿闭环只活在测试里 = 死代码）",
        ),
        toolbox.verdict(
            "revision-judge-floor",
            _count_defs(_text(root, REVISION_JUDGE)) >= 8,
            "改稿判据用例数低于下界 8",
        ),
    ]


def submission_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：三模块 + 27 角色闭集 + 五件制品 + 十一相协议 + 判据下界。"""
    submission = _text(root, SUBMISSION)
    renderers = _text(root, RENDERERS)
    credit = _text(root, CREDIT_ROLES)
    protocol = _text(root, PROTOCOL)
    roles = _assign_names(credit, "ROLE_CREDIT")
    report_outputs_ok = all(name in protocol for name in (*FIVE_ARTIFACTS, "manuscript.md"))
    submission_contract = contracts_block(_text(root, CONTRACTS), "submission_package")
    return [
        toolbox.verdict(
            "submission-trio-in-tree",
            all(
                _defines(submission, name)
                for name in ("maybe_assemble_submission", "dispatched_roles")
            )
            and "def contributions_md" in renderers,
            "投稿装配/渲染模块缺少入口函数",
        ),
        toolbox.verdict(
            "credit-mapping-covers-27-roles",
            len(roles) == 27,
            f"ROLE_CREDIT 必须覆盖 27 个角色（实测 {len(roles)}）",
        ),
        toolbox.verdict(
            "five-artifacts-named",
            all(name in renderers for name in FIVE_ARTIFACTS),
            "五件制品名必须在渲染面逐字声明",
        ),
        toolbox.verdict(
            "protocol-declares-the-submission-phase",
            "  - id: submission\n" in protocol and "task_contract: submission_package" in protocol,
            "协议缺少 submission 相或没点名本合约",
        ),
        toolbox.verdict(
            "report-phase-declares-seven-products",
            report_outputs_ok,
            "报告相产物集必须含手稿 + 五件投稿制品",
        ),
        toolbox.verdict(
            "submission-contract-in-tree",
            "has_conflict" in submission_contract and "cover_letter" in submission_contract,
            "合约 submission_package 缺失或没声明信正文与结构化字段",
        ),
        toolbox.verdict(
            "submission-judge-floor",
            _count_defs(_text(root, SUBMISSION_JUDGE)) >= 11,
            "投稿包判据用例数低于下界 11",
        ),
        toolbox.verdict(
            "e2e-judge-floor",
            _count_defs(_text(root, E2E_JUDGE)) >= 6,
            "产品入口判据用例数低于下界 6",
        ),
    ]


_TOP_LEVEL_KEY = re.compile(r"^  [A-Za-z_][A-Za-z0-9_]*:", re.MULTILINE)


def contracts_block(contracts: str, name: str) -> str:
    """合约文件里某个合约块的粗切（到下一个**顶级**两空格键或文件尾）。

    嵌套键缩进 ≥ 4 空格 ⇒ `^  [A-Za-z_]` 只匹配顶级键（`\n  ` 子串会切进嵌套层）。
    """
    marker = f"  {name}:"
    if marker not in contracts:
        return ""
    tail = contracts.split(marker, 1)[1]
    match = _TOP_LEVEL_KEY.search(tail)
    return tail[: match.start()] if match else tail


def journal_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：闭集声明无评分字段 + 解析/校验面 + 合约镜像 + 判据下界。"""
    journals = _text(root, JOURNALS)
    selection = _text(root, JOURNAL_SELECTION)
    editorial_block = contracts_block(_text(root, CONTRACTS), "editorial_decision")
    lowered = journals.lower()
    mirror_names = (
        "Journal of Reproducible Research Tooling",
        "Open Science Methods",
        "Applied AI Evaluation",
    )
    return [
        toolbox.verdict(
            "journals-closed-set-in-tree",
            "journals:" in journals and journals.count("name:") >= 2,
            "期刊闭集缺失或条目过少",
        ),
        toolbox.verdict(
            "journals-carry-no-ranking",
            all(term not in lowered for term in RANKING_TERMS),
            "闭集声明面出现评分/排名字段（声明面不是评价面）",
        ),
        toolbox.verdict(
            "journal-selection-face-in-tree",
            all(
                _defines(selection, name)
                for name in ("load_journals", "validate_selection", "contract_mirror_verdict")
            ),
            "期刊选择解析/校验/镜像面缺少入口函数",
        ),
        toolbox.verdict(
            "editorial-contract-names-the-two-fields",
            "target_journal" in editorial_block and "selection_rationale" in editorial_block,
            "editorial_decision 合约没有声明期刊选择两字段",
        ),
        toolbox.verdict(
            "editorial-contract-mirrors-the-closed-set",
            all(name in editorial_block for name in mirror_names),
            "合约 purpose 与闭集漂移（模型看见的集合必须与判据用的集合同名）",
        ),
        toolbox.verdict(
            "journal-judge-floor",
            _count_defs(_text(root, JOURNAL_JUDGE)) >= 9,
            "期刊判据用例数低于下界 9",
        ),
    ]


def registration_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-05：两个脚本进两份清单（纯收紧：只查在不在）。

    `_VERIFIERS` 收**验证器**（断言集由验证器自己加载 —— `self-loads-its-own-assertions`
    钉住）；`IN_SCOPE` 收**两个脚本**（它们都要过四道门）。
    """
    registry = _text(root, VERIFIER_REGISTRY)
    scope = _text(root, GATE_SCOPE)
    self_name = "tools/verify_goal102_closeout.py"
    assertions_name = "tools/goal102_closeout_assertions.py"
    missing_scope = [item for item in (self_name, assertions_name) if item not in scope]
    return [
        toolbox.verdict(
            "verifier-registered-in-the-registry",
            self_name in registry,
            f"{self_name} 不在 _VERIFIERS（没有人看它）",
        ),
        toolbox.verdict(
            "scope-declares-this-rounds-scripts",
            not missing_scope,
            ",".join(missing_scope),
        ),
        toolbox.verdict(
            "scope-still-pins-the-entry",
            {"tools/two_tree_recheck.py", "tools/closeout_recheck_assertions.py"}
            <= set(_assign_names(scope, "IN_SCOPE")),
            "IN_SCOPE 不得丢既有条目",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有断言的入口（验证器 import 它；与 GOAL-031…101 同形）。"""
    return [
        *supersedes_verdicts(root, toolbox),
        *revision_verdicts(root, toolbox),
        *submission_verdicts(root, toolbox),
        *journal_verdicts(root, toolbox),
        *registration_verdicts(root, toolbox),
    ]


__all__ = ["assertion_verdicts"]
