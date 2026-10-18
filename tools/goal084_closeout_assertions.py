#!/usr/bin/env python3
"""GOAL-20261018-084 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…083 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 由
`tools/closeout_recheck_assertions.standard_verdicts` 承担；本文件**只写本 GOAL 特有的断言**。

五条主轴（逐条对应本 GOAL 的 EC）：

1. **EC-01 解析面在树**：模块 + 三个入口（`resolve_agent_targets` /
   `resolve_targets_by_role` / `describe_target`）+ **零出网**（AST 扫 import 黑名单）。
2. **EC-02 判定面按解析目标**：`role_checks` 引用解析面（`describe_target` /
   `resolve_targets_by_role`），且**判词形态含 `(endpoint/model_name)`**（不是 model id），
   出厂目录里生产者与评审者的底层 `model_name` **不同**。
3. **EC-03 fallback 覆盖**：解析面展开 `profile.fallback`（源码级）+ 判据里有
   「fallback 相交」与「清空 fallback ⇒ 不相交」的成对用例。
4. **EC-04 产品路径**：出厂协议 `m12_reference_research_v1` 的门判据在树 + **按压用例**
   （把评审者指回生产者的模型 ⇒ 判红）在位 + **未声明评审关系 ⇒ 不判**在位。
5. **EC-05 自举收口**：本验证器与断言集进两处射程（由规范页断言 + 规模门覆盖）。

**判据规则**（承 GOAL-027…083）：一律判**关系**；判词名**按序号**；判词行**不含绝对路径**。
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

#: 本轮**新增**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/test_review_independence.py", 8),
    ("tests/application/test_review_independence_judgment.py", 9),
    ("tests/application/preflight/test_review_independence_gate.py", 4),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tools/verify_goal083_closeout.py",
    "tests/application/test_m4_heterogeneity.py",
    "tests/loaders/test_contract_loaders.py",
)

#: 落点常量（逐条点名；缺一即判红）。
RESOLVER = "packages/application/preflight/review_independence.py"
ROLE_CHECKS = "packages/application/preflight/role_checks.py"
RESOLVER_TEST = "tests/application/test_review_independence.py"
JUDGMENT_TEST = "tests/application/test_review_independence_judgment.py"
GATE_TEST = "tests/application/preflight/test_review_independence_gate.py"
FIXTURES = "tests/application/review_independence_fixtures.py"

#: 解析面入口与形态（逐条点名）。
RESOLVER_ENTRY = "def resolve_agent_targets("
RESOLVER_BY_ROLE = "def resolve_targets_by_role("
RESOLVER_DESCRIBE = "def describe_target("
#: fallback 展开（关系式：源码里真的读 `profile.fallback`）。
FALLBACK_READ = "profile.fallback"
#: 判词形态：`(endpoint, model_name)` 二元组（不是 model id）。
TARGET_TUPLE = "Target = tuple[str, str]"
TARGET_DOC = "同一个 `(endpoint, model_name)` = 同一个底层模型"

#: 判定面接入（关系式：`role_checks` 真的调用解析面）。
ROLE_CHECK_IMPORT = "from packages.application.preflight.review_independence import ("
ROLE_CHECK_USES = "describe_target(target)"

#: 解析失败点名（不是静默跳过）。
UNRESOLVED_CODE = "PreflightFindingCode.MODEL_MISSING.value"
UNRESOLVED_PROMPT = "review independence cannot be judged for this role"

#: 出厂目录的真实读数：评审者与生产者的 `model_name` 必须不同。
FACTORY_MODELS = "examples/config/models.yaml"
FACTORY_PROFILES = "examples/config/model_profiles.yaml"
PRODUCER_MODEL_NAME = "deepseek-v4-flash-vision"
REVIEWER_MODEL_NAME = "glm-5.3"
SECOND_REVIEWER_MODEL_NAME = "kimi-k2.6"
CRITIC_PROFILE = "critic_independent"

#: EC-04 的按压与边界用例（逐条点名）。
PRESS_CASE = "test_the_gate_still_bites_when_the_reviewer_goes_back_to_the_producer_model"
NO_PANEL_CASE = "test_a_catalog_without_writer_or_reviewer_panels_is_not_judged"
FACTORY_PASS_CASE = "test_the_factory_protocol_passes_the_independence_gate"

#: EC-03 的成对用例。
FALLBACK_OVERLAP_CASE = "test_a_fallback_creates_the_overlap_even_when_primaries_differ"
FALLBACK_CLEARED_CASE = "test_clearing_the_fallback_removes_the_overlap"

#: 解析面**不得** import 的依赖（纯函数纪律的机械形态）。
FORBIDDEN_IMPORTS: tuple[str, ...] = (
    "socket",
    "http",
    "httpx",
    "requests",
    "urllib",
    "random",
    "datetime",
    "time",
    "openai",
    "anthropic",
    "litellm",
    "openhands",
    "subprocess",
)

TEST_DEFINITION = re.compile(r"(?m)^\s*def test_")


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def imported_roots(source: str) -> set[str]:
    """模块的顶层 import 根名（AST；解析失败 ⇒ 空集）。"""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    return found


def collected_case_count(root: Path, relative: str) -> int:
    """模块的**真实用例条数**（正则按 `def test_` 数；本轮的判据文件不用 parametrize）。"""
    return len(TEST_DEFINITION.findall(_text(root, relative)))


def _names_model_names(source: str) -> tuple[str, str, str]:
    """从 `models.yaml` 里按 `model_name:` 取值（本判据只判「是否有这三个底层名」）。"""
    names = re.findall(r"^\s+model_name:\s*(\S+)\s*$", source, re.MULTILINE)
    return (
        PRODUCER_MODEL_NAME if PRODUCER_MODEL_NAME in names else "",
        REVIEWER_MODEL_NAME if REVIEWER_MODEL_NAME in names else "",
        SECOND_REVIEWER_MODEL_NAME if SECOND_REVIEWER_MODEL_NAME in names else "",
    )


def _resolver_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：解析面在树 + 三个入口 + 零出网。"""
    verdict = toolbox.verdict
    resolver = _text(root, RESOLVER)
    banned = imported_roots(resolver) & set(FORBIDDEN_IMPORTS)
    return [
        verdict("resolver-module-exists", bool(resolver), RESOLVER),
        verdict("resolver-entry", RESOLVER_ENTRY in resolver, RESOLVER_ENTRY),
        verdict("resolver-by-role", RESOLVER_BY_ROLE in resolver, RESOLVER_BY_ROLE),
        verdict("resolver-describe", RESOLVER_DESCRIBE in resolver, RESOLVER_DESCRIBE),
        verdict("resolver-uses-target-tuple", TARGET_TUPLE in resolver, TARGET_TUPLE),
        verdict(
            "resolver-states-the-target-identity",
            TARGET_DOC in resolver,
            "解析面必须写明「同一个 (endpoint, model_name) = 同一个底层模型」",
        ),
        verdict(
            "resolver-has-no-outbound-imports",
            bool(resolver) and not banned,
            ",".join(sorted(banned)),
        ),
    ]


def _judgment_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：判定面接上解析面 + 解析失败点名 + 出厂目录真实读数。"""
    verdict = toolbox.verdict
    role_checks = _text(root, ROLE_CHECKS)
    producer_name, reviewer_name, second_name = _names_model_names(_text(root, FACTORY_MODELS))
    critic_block = _text(root, FACTORY_PROFILES).split(f"{CRITIC_PROFILE}:", 1)[-1]
    return [
        verdict(
            "role-checks-imports-resolver", ROLE_CHECK_IMPORT in role_checks, ROLE_CHECK_IMPORT
        ),
        verdict("role-checks-uses-target-labels", ROLE_CHECK_USES in role_checks, ROLE_CHECK_USES),
        verdict(
            "unresolved-role-is-named",
            UNRESOLVED_CODE in role_checks and UNRESOLVED_PROMPT in role_checks,
            "解析失败必须逐条 MODEL_MISSING 点名（不得静默跳过 ⇒ 不得把空集读成「无交集」）",
        ),
        verdict("factory-producer-model-present", bool(producer_name), PRODUCER_MODEL_NAME),
        verdict("factory-reviewer-model-present", bool(reviewer_name), REVIEWER_MODEL_NAME),
        verdict("factory-second-reviewer-present", bool(second_name), SECOND_REVIEWER_MODEL_NAME),
        verdict(
            "factory-reviewer-differs-from-producer",
            bool(reviewer_name) and reviewer_name != producer_name,
            f"{producer_name} vs {reviewer_name}",
        ),
        verdict(
            "critic-primary-is-the-third-party-model",
            "primary: reviewer_independent" in critic_block,
            critic_block.strip()[:80],
        ),
        verdict(
            "critic-does-not-fall-back-to-the-producer-model",
            "research_alpha" not in critic_block,
            "critic_independent 的 fallback 不得回落生产者模型",
        ),
    ]


def _coverage_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03 / EC-04：fallback 成对用例 + 产品路径三条用例。"""
    verdict = toolbox.verdict
    resolver = _text(root, RESOLVER)
    judgment = _text(root, JUDGMENT_TEST)
    gate = _text(root, GATE_TEST)
    return [
        verdict("resolver-reads-profile-fallback", FALLBACK_READ in resolver),
        verdict("fallback-overlap-case", FALLBACK_OVERLAP_CASE in judgment, FALLBACK_OVERLAP_CASE),
        verdict("fallback-cleared-case", FALLBACK_CLEARED_CASE in judgment, FALLBACK_CLEARED_CASE),
        verdict("factory-protocol-passes-case", FACTORY_PASS_CASE in gate),
        verdict("reverse-press-case", PRESS_CASE in gate),
        verdict("no-panel-is-not-judged-case", NO_PANEL_CASE in gate),
    ]


def _floor_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """判据文件在位 + 例数下界（删掉任一条用例即判红）。"""
    verdict = toolbox.verdict
    verdicts: list[Any] = []
    for relative, floor in CASE_FLOORS:
        count = collected_case_count(root, relative)
        verdicts.append(
            verdict(
                f"case-floor-{Path(relative).stem}",
                count >= floor,
                f"{count} < {floor}" if count < floor else "",
            )
        )
    verdicts.append(verdict("fixtures-module-exists", bool(_text(root, FIXTURES)), FIXTURES))
    for relative in PRIOR_JUDGES:
        verdicts.append(verdict(f"prior-judge-{Path(relative).name}", (root / relative).is_file()))
    return verdicts


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有的断言（逐条一个判词；按 EC 分组，每组一个函数）。"""
    return [
        *_resolver_verdicts(root, toolbox),
        *_judgment_verdicts(root, toolbox),
        *_coverage_verdicts(root, toolbox),
        *_floor_verdicts(root, toolbox),
    ]


__all__ = [
    "CASE_FLOORS",
    "assertion_verdicts",
    "collected_case_count",
    "imported_roots",
]
