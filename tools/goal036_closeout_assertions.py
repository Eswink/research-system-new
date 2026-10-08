#!/usr/bin/env python3
"""GOAL-20261008-036 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…035 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— `tools/verify_goal036_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-036 特有的断言**。

四条主轴（逐条对 GOAL-036 的 EC）：

1. **EC-02 承接链五件事**：实现（`review_read.py` 定义 `review_read`）/ 工具面描述子与能力
   映射 / provider 依赖位与 handler / 会话绑定表 / 两个组合根接线 / 出厂目录声明 /
   `policy.yaml` 的**一条只读 allow**（scope 与同级读能力对齐）。
2. **EC-03 真用**：协议 `review_consumption_v1.yaml`（两 phase 都 `capability_execution:
   run_chain`、`consume` 声明 `review.read`）与合约 `review_consumption_deliverable` 在树；
   判据文件在树且例数达下界；**下游消费**的核心断言在判据里（工具结果含落库逐字判词）。
3. **EC-04 登记面与读数**：`_IN_SCOPE` 含 `review.read` 且它**不在**登记表里（搬迁）；
   出厂形态夹具同轮 +1；差集文档里它在**交集清单**、差集表里**无行**、登记计数为 7。
4. **记录面（本轮自己的交付面）**：判词归档在树（两份、非空、`CR=0`）；`IN_SCOPE`
   纯收紧（本轮两个新脚本都在清单里）。

**两条纪律**（承 GOAL-027…035 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**与非空、`CR=0`；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 AST 读而不是文本巧合。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮新增 / 相关的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
#: 第二条是**既有**夹具同步面（cycle 1 给 `_PROVIDER.capabilities` +1）：下界取建档当日的
#: 实测例数 `7`（**只防删减**；它不是本轮新增的判据，固不以新判据的例数为底）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/e2e/test_review_read_on_the_run_path.py", 6),
    ("tests/adapters/canonical/test_canonical_read_provider.py", 7),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/architecture/python/test_capability_coverage_is_implemented.py",
    "tests/application/preflight/test_release_expansion_is_read_only.py",
    "tests/application/preflight/test_read_grant_is_per_item.py",
    "tests/e2e/test_granted_read_capabilities_used_in_a_run.py",
)

#: EC-02 落点（承接链五件事）。
REVIEW_READ = "adapters/canonical/review_read.py"
SURFACE = "adapters/canonical/read_surface.py"
PROVIDER = "adapters/canonical/read_provider.py"
BINDINGS = "services/api/session_tool_support.py"
PG_ROOT = "services/api/pg_composition.py"
CATALOG = "examples/config/tool_providers.yaml"
POLICY = "examples/config/policy.yaml"
SCOPE_MIRROR = "packages/application/preflight/policy_check.py"

#: EC-03 落点（真用）。
PROTOCOL = "examples/protocols/review_consumption_v1.yaml"
CONTRACTS = "examples/contracts/task_contracts.yaml"
CONSUME_CONTRACT = "review_consumption_deliverable"
JUDGE = "tests/e2e/test_review_read_on_the_run_path.py"

#: EC-04 落点（登记面）。
COVERAGE_JUDGE = "tests/architecture/python/test_capability_coverage_is_implemented.py"
AUDIT_DOC = "docs/architecture/POLICY_SURFACE_AUDIT.md"
FIXTURE = "tests/adapters/canonical/test_canonical_read_provider.py"

#: 归档（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261008-036-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261008-036-verdict-clean.txt"

#: `IN_SCOPE` 清单所在判据（纯收紧：本轮两个新脚本必须在里面）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
SELF = "tools/verify_goal036_closeout.py"
ASSERTIONS = "tools/goal036_closeout_assertions.py"

#: 会话绑定表里的那一条（逐字）。
BINDING_ROW = '("review.read", "m12_artifact", "review_read")'


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _has_def(root: Path, relative: str, name: str) -> bool:
    """模块里是否**定义**了该函数 / 类（AST，不看文本巧合）。"""
    source = _text(root, relative)
    if not source:
        return False
    try:
        parsed = ast.parse(source)
    except SyntaxError:  # pragma: no cover - 语法坏掉时判据会判红
        return False
    return any(
        isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        and node.name == name
        for node in ast.walk(parsed)
    )


def _count_test_cases(root: Path, relative: str) -> int:
    source = _text(root, relative)
    if not source:
        return 0
    parsed = ast.parse(source)
    return sum(
        1
        for node in ast.walk(parsed)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name.startswith("test_")
    )


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：承接链五件事（实现 / 工具面 / provider 依赖位 / 绑定 / 接线 / 声明 / 放行）。"""
    return [
        toolbox.verdict("ec02-implementation-module", _has_def(root, REVIEW_READ, "review_read")),
        toolbox.verdict(
            "ec02-tool-capability-mapping", '"review_read": "review.read"' in _text(root, SURFACE)
        ),
        toolbox.verdict(
            "ec02-provider-handler", '"review_read": self._review_read' in _text(root, PROVIDER)
        ),
        toolbox.verdict(
            "ec02-provider-dependency",
            "_review_read" in _text(root, PROVIDER) and "review_store" in _text(root, PROVIDER),
        ),
        toolbox.verdict("ec02-session-binding", BINDING_ROW in _text(root, BINDINGS)),
        toolbox.verdict(
            "ec02-both-roots-wired",
            "review_store=ports.review_findings" in _text(root, BINDINGS)
            and 'c["review_findings"]' in _text(root, PG_ROOT),
        ),
        toolbox.verdict("ec02-catalog-declares-it", "- review.read" in _text(root, CATALOG)),
        toolbox.verdict(
            "ec02-policy-grants-it-once",
            _text(root, POLICY).count("- capability: review.read") == 1,
        ),
        toolbox.verdict(
            "ec02-scope-mirror-synced", '"review.read": "project"' in _text(root, SCOPE_MIRROR)
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：真用（协议声明 + 合约 + 判据 + 两 phase 都走运行链）。"""
    protocol = _text(root, PROTOCOL)
    return [
        toolbox.verdict("ec03-protocol-present", (root / PROTOCOL).is_file()),
        toolbox.verdict(
            "ec03-consume-declares-capability", "- review.read" in protocol.split("id: consume")[-1]
        ),
        toolbox.verdict(
            "ec03-both-phases-run-chain", protocol.count("capability_execution: run_chain") == 2
        ),
        toolbox.verdict(
            "ec03-consumption-contract",
            f"  {CONSUME_CONTRACT}:" in _text(root, CONTRACTS),
        ),
        toolbox.verdict("ec03-judge-present", (root / JUDGE).is_file()),
        toolbox.verdict(
            "ec03-downstream-consumption-is-asserted",
            "读到的判词必须与落库的逐字一致" in _text(root, JUDGE),
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：登记面（射程 +1、登记表 −1、夹具同轮、差集文档搬迁、计数 7）与只读面。"""
    coverage = _text(root, COVERAGE_JUDGE)
    audit = _text(root, AUDIT_DOC)
    return [
        toolbox.verdict("ec04-in-scope-lists-it", '"review.read",' in coverage),
        toolbox.verdict(
            "ec04-registry-no-longer-lists-it",
            '"review.read": "B 组' not in coverage and '"review.read":' not in coverage,
        ),
        toolbox.verdict("ec04-fixture-synced", '"review.read",' in _text(root, FIXTURE)),
        toolbox.verdict("ec04-difference-table-has-no-row", "| `review.read` |" not in audit),
        toolbox.verdict("ec04-registered-count-is-seven", "该登记 = 7 条" in audit),
        toolbox.verdict(
            "ec04-intersection-lists-it", "`review.read`" in audit.split("两侧都有")[-1]
        ),
    ]


def _judge_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """判据面：例数下界 + 既有判据仍在树（引用而非重复）。"""
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


def _has_carriage_return(raw: bytes) -> bool:
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023/035 的实测教训）。"""
    return bytes([13]) in raw


def _archive_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """记录面：判词归档形态（两份、非空、CR=0）。**不读内容做断言**（输入即输出）。"""
    verdicts: list[Any] = []
    for label, relative in (("current", ARCHIVE_CURRENT), ("clean", ARCHIVE_CLEAN)):
        path = root / relative
        raw = path.read_bytes() if path.is_file() else b""
        verdicts.append(
            toolbox.verdict(
                f"verdict-archive-{label}",
                bool(raw) and not _has_carriage_return(raw),
                "missing/empty" if not raw else "contains CR",
            )
        )
    return verdicts


def _scope_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """`IN_SCOPE` 纯收紧：本轮两个新脚本都在必备清单里（**只查在不在**）。"""
    literal = toolbox.module_literal(_text(root, SCOPE_JUDGE), "IN_SCOPE")
    declared = set(literal) if isinstance(literal, tuple) else set()
    missing = [item for item in (SELF, ASSERTIONS) if item not in declared]
    return [
        toolbox.verdict("scope-declares-this-rounds-scripts", not missing, ",".join(missing)),
        toolbox.verdict(
            "scope-still-pins-the-entry",
            {"tools/two_tree_recheck.py", "tools/closeout_recheck_assertions.py"} <= declared,
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有断言（每条都能被单变量按压判红）。"""
    return [
        *_ec02_verdicts(root, toolbox),
        *_ec03_verdicts(root, toolbox),
        *_ec04_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]
