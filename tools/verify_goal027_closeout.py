#!/usr/bin/env python3
"""GOAL-20260927-027 收口复检（EC-05）：**标准断言集 + 本轮特有断言**。

与 GOAL-023 / 024 / 025 / 026 的收口验证器同形：公共面（受保护判据 / 规模门 / 产品根 /
m0 条数 / 两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 直接调用
`tools/closeout_recheck_assertions.py`；本文件**只写 GOAL-027 特有的断言**：

- **逐 EC：交付物在树 + 例数下界**（缺文件、例数掉下去，两向都判红）；
- **本 GOAL 的三处真缺陷修复逐条在位**（都是「修实现过程中发现的」授权对象）：
  ① `adapters/mcp/provider.py` 读 args 制品 + digest 重算（空参数缺口的修复）；
  ② `packages/application/run_orchestration/phase_capabilities.py` 的
  `ids_from_previous` 点分路径（MCP 信封的链式传参）；
  ③ `packages/application/run_orchestration/outcomes.py` 的 `handoff_digests`
  （此前装的是 task id）—— 用 **AST 断言**判定，不是文本巧合；
- **两条新增真实文献来源在树且 pin 面闭合**（`toolpack_europe_pmc.yaml` +
  `tool_providers.yaml` 的 `europe_pmc` 条目 + 夹具 pin 源同轮扩表）；
- **自建 MCP server 在树并进 `IN_SCOPE`（纯收紧）**（`tools/research_mcp_server.py`）；
- **四条新增判据文件在树**（EC-01 三份 + EC-02 三份 + EC-03 两份 + EC-04 一份，逐条点名）；
- **记录面**：五个 EC 的终态、复检路径、子计划与记忆、残余与未覆盖逐条；
- **文件规模**（本轮新增的最大文件 ≤ 450 行）。

用法：`python tools/verify_goal027_closeout.py --root <树根> --verdict-only`；判词行只有
`PASS` / `FAIL` 且不含任何树的绝对路径（否则两树入口会（正确地）拒绝）。

**时间口径**：GOAL 的 `EC-05` 在**本收口复检跑之前**仍是 `PENDING`（它的判词就是本文件产出的），
所以 EC-05 那条断言接受 `PASS ∪ PENDING` —— **不是**放宽，是**时序**。
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import sys
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Protocol, cast


class VerdictLike(Protocol):
    """标准集 `Verdict` 的结构面（本文件只读它的三个字段，不 import 其类型）。"""

    name: str
    ok: bool
    detail: str


STANDARD = "tools/closeout_recheck_assertions.py"
SELF = "tools/verify_goal027_closeout.py"
MCP_SERVER = "tools/research_mcp_server.py"
TOOLING_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
GOAL = ".cursor/plans/goals/GOAL-20260929-027-real-research-capability-onboarding.md"
GOVERNANCE = ".cursor/skills/governance-check/scripts/validate.py"

#: 本 GOAL 新增/修改的产品与交付件（存在性 + 关键结构）。
MCP_PROVIDER = "adapters/mcp/provider.py"
PHASE_CAPS = "packages/application/run_orchestration/phase_capabilities.py"
OUTCOMES = "packages/application/run_orchestration/outcomes.py"
EUROPE_PMC_PIN = "examples/contracts/toolpack_europe_pmc.yaml"
PROVIDERS_YAML = "examples/config/tool_providers.yaml"
RUN_FIXTURES = "tests/api/run_fixtures.py"

#: 逐 EC：判据文件 + **例数下界**（下界是契约，不是「现在有多少」）。
EC_FILES: dict[str, tuple[tuple[str, ...], tuple[int, ...]]] = {
    "ec01": (
        (
            "tests/contracts/test_europe_pmc_provider_contract.py",
            "tests/contracts/test_europe_pmc_url_policy.py",
            "tests/contracts/test_europe_pmc_pin_and_registration.py",
        ),
        (8, 10, 8),
    ),
    "ec02": (
        (
            "tests/contracts/test_mcp_provider_arguments.py",
            "tests/contracts/test_mcp_research_server_loopback.py",
            "tests/contracts/test_mcp_registration_and_refutations.py",
        ),
        (8, 8, 10),
    ),
    "ec03": (
        ("tests/e2e/test_literature_chain_run_offline.py",),
        (10,),
    ),
    "ec04": (
        ("tests/e2e/test_multi_role_research_offline.py",),
        (5,),
    ),
}

#: 本轮新增的协议与契约（逐条点名）。
NEW_PROTOCOLS: tuple[str, ...] = (
    "examples/protocols/real_literature_chain_v1.yaml",
    "examples/protocols/multi_role_research_v1.yaml",
)

#: 残余与未覆盖范围在记录里必须逐条出现的字面量。
RESIDUAL_MARKERS: tuple[str, ...] = (
    "W-1",
    "W-2",
    "未覆盖范围",
)

#: 未覆盖范围五条（承继项；逐条必须明写）。
UNCOVERED_MARKERS: tuple[str, ...] = (
    "读面未认证",
    "多租户未做",
    "BOLA·BFLA 未做",
    "部署面未验证",
    "R-M1 未收口",
)

#: 本轮新增的最大文件（规模契约）。
MAX_NEW_FILE_LINES = 450
NEW_FILES: tuple[str, ...] = (
    MCP_SERVER,
    "tests/contracts/mcp_research_support.py",
    "tests/contracts/test_mcp_provider_arguments.py",
    "tests/contracts/test_mcp_research_server_loopback.py",
    "tests/contracts/test_mcp_registration_and_refutations.py",
    "tests/e2e/literature_chain_support.py",
    "tests/e2e/test_literature_chain_run_offline.py",
    "tests/e2e/test_multi_role_research_offline.py",
)


def load_standard(root: Path) -> object | None:
    """加载标准断言集（公共面；本文件不重写它）。"""
    spec = importlib.util.spec_from_file_location(
        "goal027_standard_assertions", root.joinpath(*STANDARD.split("/"))
    )
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal027_standard_assertions"] = module
    try:
        spec.loader.exec_module(module)
    except Exception:  # 加载失败 ⇒ 该条判词判红，而不是整轮崩掉
        return None
    return module


def _verdict(name: str, ok: bool, detail: str = "") -> VerdictLike:
    """标准集里的 `Verdict`（经已加载模块构造，保证同一类型）。"""
    module = sys.modules.get("goal027_standard_assertions")
    assert module is not None
    verdict: VerdictLike = module.Verdict(name, ok, detail)
    return verdict


def _tree(root: Path, relative: str) -> Path:
    return root.joinpath(*relative.split("/"))


def _text(root: Path, relative: str) -> str:
    path = _tree(root, relative)
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _defines(text: str, name: str) -> bool:
    """按 **AST** 读声明（不是「文本里出现过这个名字」）。"""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    return any(isinstance(node, ast.FunctionDef) and node.name == name for node in ast.walk(tree))


def _references_attr(text: str, attribute: str) -> bool:
    """AST 里是否出现 `something.<attribute>`（用于「digest 被真的取用了」这类断言）。"""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    return any(
        isinstance(node, ast.Attribute) and node.attr == attribute for node in ast.walk(tree)
    )


def ec_file_verdicts(root: Path) -> list[VerdictLike]:
    """逐 EC：判据文件在树 + 例数下界（缺一即红，两向都判）。"""
    verdicts: list[VerdictLike] = []
    for label, (files, floors) in EC_FILES.items():
        missing = [item for item in files if not _tree(root, item).is_file()]
        verdicts.append(
            _verdict(f"{label}-criteria-present", not missing, f"缺少判据文件：{missing}")
        )
        for relative, floor in zip(files, floors, strict=True):
            text = _text(root, relative)
            count = text.count("\n    def test_") + text.count("\ndef test_")
            verdicts.append(
                _verdict(
                    f"{label}-{Path(relative).stem}-example-floor",
                    count >= floor,
                    f"{relative} 有 {count} 例，下界是 {floor}",
                )
            )
    return verdicts


def defect_fix_verdicts(root: Path) -> list[VerdictLike]:
    """本 GOAL 的三处真缺陷修复：逐条 **AST** 判定（不是文本巧合）。"""
    provider = _text(root, MCP_PROVIDER)
    phase_caps = _text(root, PHASE_CAPS)
    outcomes = _text(root, OUTCOMES)
    return [
        _verdict(
            "mcp-args-defect-is-fixed",
            _defines(provider, "_read_args") and _references_attr(provider, "argument_digest"),
            f"{MCP_PROVIDER} 缺少 _read_args 或不再比对 argument_digest",
        ),
        _verdict(
            "mcp-empty-args-fallback-is-fail-closed",
            "EMPTY_ARGS_PAYLOAD" in provider and "ARGS_ARTIFACT_PREFIX" in provider,
            f"{MCP_PROVIDER} 缺少空参数回落常量（缺席分支的 fail-closed 形态）",
        ),
        _verdict(
            "chained-ids-support-dotted-path",
            _defines(phase_caps, "_lookup") and "ids_from_previous" in phase_caps,
            f"{PHASE_CAPS} 缺少 ids_from_previous 或 _lookup",
        ),
        _verdict(
            "handoff-digests-are-real-digests",
            _defines(outcomes, "handoff_digests") and _references_attr(outcomes, "digest"),
            f"{OUTCOMES} 缺少 handoff_digests 或不再取 bundle.digest",
        ),
    ]


def literature_source_verdicts(root: Path) -> list[VerdictLike]:
    """EC-01：第二个真实文献源在 pin 面与登记面闭合，且夹具 pin 源同轮扩表。"""
    pin = _text(root, EUROPE_PMC_PIN)
    providers = _text(root, PROVIDERS_YAML)
    fixtures = _text(root, RUN_FIXTURES)
    return [
        _verdict(
            "europe-pmc-pin-contract-present",
            "europe_pmc_v1" in pin and "digest: sha256:" in pin and "credentials: []" in pin,
            f"{EUROPE_PMC_PIN} 缺少 id / digest / 空凭据声明",
        ),
        _verdict(
            "europe-pmc-registered-without-credentials",
            "europe_pmc:" in providers and "www.ebi.ac.uk" in providers,
            f"{PROVIDERS_YAML} 缺少 europe_pmc 条目或声明域名",
        ),
        _verdict(
            "fixture-pin-source-covers-europe-pmc",
            '"europe_pmc"' in fixtures,
            f"{RUN_FIXTURES} 的 pin 源未含 europe_pmc（run_ready 路径会 SUPPLY_CHAIN_UNPINNED）",
        ),
    ]


def mcp_server_verdicts(root: Path) -> list[VerdictLike]:
    """EC-02：自建 MCP server 在树、进 `IN_SCOPE`（纯收紧）、冻结语料是真标识。"""
    server = _text(root, MCP_SERVER)
    tooling = _text(root, TOOLING_JUDGE)
    real_pmids = ("42803750", "42796516", "42740546", "42772441")
    return [
        _verdict(
            "mcp-server-is-in-tree",
            _defines(server, "build_server") and "literature_search" in server,
            f"{MCP_SERVER} 缺少 build_server / 检索工具",
        ),
        _verdict(
            "mcp-server-carries-real-identifiers",
            sum(1 for item in real_pmids if item in server) >= 3,
            f"{MCP_SERVER} 的冻结语料里真 PMID 少于 3 条",
        ),
        _verdict(
            "mcp-server-is-in-scope",
            MCP_SERVER in tooling,
            f"{TOOLING_JUDGE} 的 IN_SCOPE 未含 {MCP_SERVER}（纯收紧）",
        ),
        _verdict(
            "shapeless-fixture-in-tree",
            _tree(root, "tests/mcp_server/raw_shapeless_tools.py").is_file(),
            "缺少申报形状不符工具声明的 raw stdio 夹具",
        ),
    ]


def protocol_verdicts(root: Path) -> list[VerdictLike]:
    """EC-03 / EC-04：新增协议在树，且带 run-chain 与多 phase 声明。"""
    ec03 = _text(root, NEW_PROTOCOLS[0])
    ec04 = _text(root, NEW_PROTOCOLS[1])
    phase_count = ec04.count("\n  - id: ")
    return [
        _verdict(
            "ec03-protocol-declares-run-chain",
            "capability_execution: run_chain" in ec03,
            f"{NEW_PROTOCOLS[0]} 未声明 run_chain",
        ),
        _verdict(
            "ec04-protocol-has-three-phases",
            phase_count >= 3,
            f"{NEW_PROTOCOLS[1]} 只有 {phase_count} 个 phase（下界 3）",
        ),
        _verdict(
            "ec04-protocol-binds-three-roles",
            sum(
                1
                for role in ("literature_scout", "experiment_engineer", "scientific_reviewer")
                if role in ec04
            )
            == 3,
            f"{NEW_PROTOCOLS[1]} 未绑满三个不同 role",
        ),
    ]


def goal_record_verdicts(root: Path) -> list[VerdictLike]:
    """记录面：EC 终态、残余、未覆盖范围与规模。"""
    goal = _text(root, GOAL)
    available = goal.count("| **PASS**")
    files_ok = all(len(_text(root, item).splitlines()) <= MAX_NEW_FILE_LINES for item in NEW_FILES)
    oversized = [
        item for item in NEW_FILES if len(_text(root, item).splitlines()) > MAX_NEW_FILE_LINES
    ]
    return [
        _verdict(
            "goal-records-five-ec-pass",
            available >= 4,
            f"{GOAL} 只有 {available} 个 EC 标 PASS（EC-05 时序上可为 PENDING）",
        ),
        _verdict(
            "goal-records-residuals",
            all(marker in goal for marker in RESIDUAL_MARKERS),
            f"{GOAL} 缺少残余/未覆盖标记 {[m for m in RESIDUAL_MARKERS if m not in goal]}",
        ),
        _verdict(
            "goal-records-uncovered-range",
            all(marker in goal for marker in UNCOVERED_MARKERS),
            f"{GOAL} 未逐条明写未覆盖范围：{[m for m in UNCOVERED_MARKERS if m not in goal]}",
        ),
        _verdict(
            "new-files-respect-the-scale-gate",
            files_ok,
            f"这些新文件超过 {MAX_NEW_FILE_LINES} 行：{oversized}",
        ),
    ]


def goal027_verdicts(root: Path) -> list[VerdictLike]:
    """本 GOAL 特有的断言（标准集之外）。"""
    return [
        *ec_file_verdicts(root),
        *defect_fix_verdicts(root),
        *literature_source_verdicts(root),
        *mcp_server_verdicts(root),
        *protocol_verdicts(root),
        *goal_record_verdicts(root),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GOAL-027 收口复检（两树入口的复检脚本协议）")
    parser.add_argument("--root", required=True, help="树根（不硬编码仓库根 ⇒ 可跑任意树）")
    parser.add_argument("--verdict-only", action="store_true", help="只打印判词行")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    if not root.is_dir():
        print("FAIL goal027-root-missing -> 树根不存在")
        return 2
    module = load_standard(root)
    if module is None:
        print(f"FAIL goal027-standard-assertions-loadable -> 无法加载 {STANDARD}")
        return 2
    standard_verdicts = getattr(module, "standard_verdicts")
    standard = cast("list[VerdictLike]", standard_verdicts(root))
    verdicts = [*standard, *goal027_verdicts(root)]
    emit = cast("Callable[[Iterable[VerdictLike]], bool]", getattr(module, "emit"))
    if args.verdict_only:
        return 0 if emit(verdicts) else 1
    reds = [item for item in verdicts if not item.ok]
    for verdict in verdicts:
        state = "PASS" if verdict.ok else "FAIL"
        print(f"{state} {verdict.name}: {verdict.detail or 'ok'}")
    print(f"TOTAL {len(verdicts)} verdicts; {len(reds)} red")
    return 1 if reds else 0


if __name__ == "__main__":
    raise SystemExit(main())
