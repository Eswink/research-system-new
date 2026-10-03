#!/usr/bin/env python3
"""GOAL-20261001-028 收口复检（EC-05）：**标准断言集 + 本轮特有断言**。

与 GOAL-023…027 的收口验证器同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 直接调用
`tools/closeout_recheck_assertions.py`；本文件**只写 GOAL-028 特有的断言**：

- **逐 EC：交付物在树 + 例数下界**（缺文件、例数掉下去，两向都判红）；
- **本 GOAL 的主干交付物逐条在位**（AST 断言，不是文本巧合）：
  ① `packages/domain/protocols.py` 的 `SessionToolBinding` 声明；
  ② `adapters/openhands/tool_mapping.py` 的 `bind_session_tools`；
  ③ `adapters/openhands/session_tools.py` 的 `build_session_tools` 与 `BoundSessionTool`；
  ④ `services/api/runtime_support.py` 的 `build_agent_runtime` **接收** `register_session_tools`；
  ⑤ `tools/research_mcp_server.py` 的 `build_server` **接收** `live` 参数（活检索模式）；
  ⑥ `tools/research_mcp_live.py` 的 `live_search` / `live_read`（真上游，复用既有 provider 零件）；
  ⑦ `tools/audit_goal028_ledger.py` 的 `audit`（台账逐提交审计）；
- **协议面的绑定声明在树**（`multi_role_research_v1.yaml` 的 review phase 四条）；
- **IN_SCOPE 纯收紧**（本轮三条新脚本逐条在位）；
- **记录面**：五个 EC 的终态、复检路径、子计划与记忆、残余与未覆盖逐条。

用法：`python tools/verify_goal028_closeout.py --root <树根> --verdict-only`；判词行只有
`PASS` / `FAIL` 且不含任何树的绝对路径（否则两树入口会（正确地）拒绝）。

**时间口径**：GOAL 的 `EC-05` 在**本收口复检跑之前**仍是 `PENDING`（它的判词就是本文件产出的），
所以 EC-05 那条断言接受 `PASS ∪ PENDING` —— **不是**放宽，是**时序**（承 GOAL-027 同款注释）。
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
SELF = "tools/verify_goal028_closeout.py"
TOOLING_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
GOAL = ".cursor/plans/goals/GOAL-20261001-028-research-subiteration-on-the-default-assembly.md"
GOVERNANCE = ".cursor/skills/governance-check/scripts/validate.py"

#: 本 GOAL 的主干交付物（存在性 + AST 结构）。
DOMAIN_PROTOCOLS = "packages/domain/protocols.py"
TOOL_MAPPING = "adapters/openhands/tool_mapping.py"
SESSION_TOOLS = "adapters/openhands/session_tools.py"
SESSION_RESOLUTION = "packages/application/run_orchestration/session_resolution.py"
RUNTIME_SUPPORT = "services/api/runtime_support.py"
MCP_SERVER = "tools/research_mcp_server.py"
MCP_LIVE = "tools/research_mcp_live.py"
LEDGER_AUDIT = "tools/audit_goal028_ledger.py"
REAL_PROTOCOL = "examples/protocols/multi_role_research_v1.yaml"
MCP_DOC = "docs/integration/MCP_TOOL_PROVIDERS.md"

#: 逐 EC：判据文件 + **例数下界**（下界取本轮实测的 `def test_` 声明数 —— 与
#: `closeout_recheck_assertions` 同一计数口径；`pytest` 的**收集**数会因参数化更大，
#: 两者不是一个量，故下界按声明数取）。
EC_FILES: dict[str, tuple[tuple[str, ...], tuple[int, ...]]] = {
    "ec01": (
        (
            "tests/e2e/test_tool_binding_on_the_default_assembly.py",
            "tests/architecture/python/test_session_tool_bindings_exposure.py",
        ),
        (13, 9),
    ),
    "ec02": (
        ("tests/contracts/test_mcp_live_retrieval_offline.py",),
        (13,),
    ),
    "ec03": (
        ("tests/e2e/test_multi_role_on_the_default_assembly.py",),
        (4,),
    ),
    "ec04": (
        ("tests/tooling/test_goal028_ledger_covers_every_commit.py",),
        (11,),
    ),
}

#: 本轮新增的协议（逐条点名）。
NEW_PROTOCOLS: tuple[str, ...] = (
    "examples/protocols/tool_binding_research_v1.yaml",
    "examples/protocols/tool_binding_partial_v1.yaml",
    "examples/protocols/tool_binding_unwired_v1.yaml",
)

#: 残余与未覆盖范围在记录里必须逐条出现的字面量。
RESIDUAL_MARKERS: tuple[str, ...] = ("W-1", "W-2", "未覆盖范围")

#: 未覆盖范围五条（承继项；逐条必须明写）。
UNCOVERED_MARKERS: tuple[str, ...] = (
    "读面未认证",
    "多租户未做",
    "BOLA·BFLA 未做",
    "部署面未验证",
    "R-M1 未收口",
)

#: 本轮新增文件（规模契约）。
MAX_NEW_FILE_LINES = 450
NEW_FILES: tuple[str, ...] = (
    "tools/research_mcp_live.py",
    "tools/audit_goal028_ledger.py",
    SELF,
    "adapters/openhands/session_tools.py",
    "adapters/openhands/session_tool_invocation.py",
    "tests/e2e/test_tool_binding_on_the_default_assembly.py",
    "tests/architecture/python/test_session_tool_bindings_exposure.py",
    "tests/contracts/test_mcp_live_retrieval_offline.py",
    "tests/e2e/test_multi_role_on_the_default_assembly.py",
    "tests/tooling/test_goal028_ledger_covers_every_commit.py",
)


def _tree(root: Path, relative: str) -> Path:
    return root.joinpath(*relative.split("/"))


def _text(root: Path, relative: str) -> str:
    path = _tree(root, relative)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _verdict(name: str, ok: bool, detail: str = "") -> VerdictLike:
    return cast(VerdictLike, _SimpleVerdict(name, ok, detail))


class _SimpleVerdict:
    """最小判词对象（三字段；与标准集的 `Verdict` 结构一致）。"""

    def __init__(self, name: str, ok: bool, detail: str) -> None:
        self.name = name
        self.ok = ok
        self.detail = detail


def _defines(text: str, name: str) -> bool:
    """按 **AST** 读**模块级**声明（不是「文本里出现过这个名字」）。

    只认模块级：`def` 出现在别的函数体里不算（那可能只是内部辅助）。
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
        for node in tree.body
    )


def _defines_class(text: str, name: str) -> bool:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    return any(isinstance(node, ast.ClassDef) and node.name == name for node in tree.body)


def _parameter_named(text: str, function: str, parameter: str) -> bool:
    """某个模块级函数（或类方法）的签名里是否有该参数名（AST，含 keyword-only 与 `**kw`）。"""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name != function:
            continue
        args = node.args
        names = {arg.arg for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs)}
        if args.vararg is not None:
            names.add(args.vararg.arg)
        if args.kwarg is not None:
            names.add(args.kwarg.arg)
        if parameter in names:
            return True
    return False


def load_standard(root: Path) -> object | None:
    """加载标准断言集（公共面；本文件不重写它）。"""
    spec = importlib.util.spec_from_file_location(
        "goal028_standard_assertions", root.joinpath(*STANDARD.split("/"))
    )
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal028_standard_assertions"] = module
    try:
        spec.loader.exec_module(module)
    except Exception:  # 加载失败 ⇒ 该条判词判红，而不是整轮崩掉
        return None
    return module


def _binding_face_verdicts(root: Path) -> list[VerdictLike]:
    """会话工具绑定面：声明 → 解释 → 翻译 → 真实实现 → 组合根接缝（逐条 AST 判定）。"""
    domain = _text(root, DOMAIN_PROTOCOLS)
    mapping = _text(root, TOOL_MAPPING)
    session_tools = _text(root, SESSION_TOOLS)
    resolution = _text(root, SESSION_RESOLUTION)
    runtime = _text(root, RUNTIME_SUPPORT)
    return [
        _verdict(
            "session-tool-binding-declared",
            _defines_class(domain, "SessionToolBinding"),
            f"{DOMAIN_PROTOCOLS} 缺 SessionToolBinding 类声明",
        ),
        _verdict(
            "session-tool-visibility-declared",
            "session_tool_bindings" in domain and "session_tool_bindings" in resolution,
            "域与解析面缺 session_tool_bindings",
        ),
        _verdict(
            "bind-session-tools-defined",
            _defines(mapping, "bind_session_tools"),
            f"{TOOL_MAPPING} 缺模块级 bind_session_tools",
        ),
        _verdict(
            "bound-session-tool-defined",
            _defines_class(session_tools, "BoundSessionTool")
            and _defines(session_tools, "build_session_tools"),
            f"{SESSION_TOOLS} 缺 BoundSessionTool 类或 build_session_tools",
        ),
        _verdict(
            "runtime-accepts-session-tools",
            _parameter_named(runtime, "build_agent_runtime", "register_session_tools"),
            f"{RUNTIME_SUPPORT} 的 build_agent_runtime 不再接收 register_session_tools",
        ),
    ]


def _retrieval_and_ledger_verdicts(root: Path) -> list[VerdictLike]:
    """活检索面与台账审计面（逐条 AST / 关键字判定）。"""
    server = _text(root, MCP_SERVER)
    live = _text(root, MCP_LIVE)
    ledger = _text(root, LEDGER_AUDIT)
    return [
        _verdict(
            "mcp-server-accepts-live-mode",
            _parameter_named(server, "build_server", "live"),
            f"{MCP_SERVER} 的 build_server 不再接收 live 参数",
        ),
        _verdict(
            "mcp-live-retrieval-defined",
            _defines(live, "live_search") and _defines(live, "live_read"),
            f"{MCP_LIVE} 缺 live_search / live_read",
        ),
        _verdict(
            "mcp-live-declares-network-domains",
            "NETWORK_DOMAINS" in live and "assert_url_allowed" in live,
            f"{MCP_LIVE} 缺 NETWORK_DOMAINS 或未在触网前判 URL 策略",
        ),
        _verdict(
            "ledger-audit-defined",
            _defines(ledger, "audit") and "covered_by" in ledger,
            f"{LEDGER_AUDIT} 缺 audit 或覆盖声明字段",
        ),
    ]


def deliverable_verdicts(root: Path) -> list[VerdictLike]:
    """主干交付物：存在 + 关键结构（AST 判定，逐条点名）。"""
    return [*_binding_face_verdicts(root), *_retrieval_and_ledger_verdicts(root)]


def protocol_verdicts(root: Path) -> list[VerdictLike]:
    """协议面：真实协议的 review phase 声明了绑定（四条逐条点名）。"""
    text = _text(root, REAL_PROTOCOL)
    missing = [item for item in NEW_PROTOCOLS if not _tree(root, item).is_file()]
    pairs = (
        "provider_id: m12_artifact",
        "provider_id: openhands_workspace",
        "provider_id: ncbi_eutils",
        "provider_id: europe_pmc",
    )
    absent = [item for item in pairs if item not in text]
    return [
        _verdict("new-protocols-present", not missing, f"缺少判据专用协议：{missing}"),
        _verdict(
            "real-protocol-declares-four-bindings",
            not absent and "session_tool_bindings" in text,
            f"{REAL_PROTOCOL} 缺绑定声明：{absent}",
        ),
    ]


def in_scope_verdicts(root: Path) -> list[VerdictLike]:
    """射程：本轮三条新脚本逐条进 `IN_SCOPE`（纯收紧 ⇒ 只查在不在）。"""
    judge = _text(root, TOOLING_JUDGE)
    required = (
        "tools/research_mcp_live.py",
        "tools/audit_goal028_ledger.py",
        "tools/verify_goal028_closeout.py",
    )
    missing = [item for item in required if item not in judge]
    return [_verdict("new-scripts-in-scope", not missing, f"未进 IN_SCOPE：{missing}")]


def _count_defs(text: str) -> int:
    """`def test_` 的**声明**数（与 `closeout_recheck_assertions` 同一口径）。

    只按行首缩进匹配（类内方法一层缩进、模块级函数零缩进），避免把字符串里的
    `def test_` 计进来。**注意**：这不是 `pytest` 的收集数 —— 参数化会让收集数更大，
    两者不是一个量，下界按声明数取。
    """
    return sum(
        1
        for line in text.splitlines()
        if line.startswith("def test_") or line.startswith("    def test_")
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
            count = _count_defs(_text(root, relative))
            verdicts.append(
                _verdict(
                    f"{label}-{Path(relative).stem}-example-floor",
                    count >= floor,
                    f"{relative} 有 {count} 例，下界是 {floor}",
                )
            )
    return verdicts


def record_verdicts(root: Path) -> list[VerdictLike]:
    """记录面：EC 终态、未覆盖五条、残余、复检路径与子计划。"""
    goal = _text(root, GOAL)
    uncovered = [item for item in UNCOVERED_MARKERS if item not in goal]
    residuals = [item for item in RESIDUAL_MARKERS if item not in goal]
    ec_statuses = {
        "ec01": "| EC-01 |" in goal and "**PASS**" in goal,
        "ec02": "| EC-02 |" in goal and goal.count("**PASS**") >= 2,
        "ec03": "| EC-03 |" in goal and goal.count("**PASS**") >= 3,
        "ec04": "| EC-04 |" in goal and goal.count("**PASS**") >= 4,
        "ec05": "| EC-05 |" in goal,
    }
    return [
        _verdict("goal-record-present", bool(goal), f"缺少 {GOAL}"),
        _verdict("uncovered-scope-listed", not uncovered, f"未覆盖范围缺失：{uncovered}"),
        _verdict("residuals-listed", not residuals, f"残余缺失：{residuals}"),
        _verdict("ec-table-has-five-rows", all(ec_statuses.values()), f"EC 行不齐：{ec_statuses}"),
        _verdict(
            "child-plans-and-recheck-in-record",
            ".cursor/plans/tasks/PLAN-20261001-267" in goal
            and ".cursor/plans/rechecks/RECHECK-20261001-272" in goal,
            "子计划或复检未登记进 GOAL",
        ),
    ]


def size_verdict(root: Path) -> VerdictLike:
    """本轮新增文件**恰好存在**且不超规模门（450 行）。"""
    problems: list[str] = []
    for relative in NEW_FILES:
        path = _tree(root, relative)
        if not path.is_file():
            problems.append(f"{relative} 不存在")
            continue
        lines = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        if lines > MAX_NEW_FILE_LINES:
            problems.append(f"{relative} 有 {lines} 行 > {MAX_NEW_FILE_LINES}")
    return _verdict("new-files-within-size", not problems, "; ".join(problems))


def docs_verdict(root: Path) -> VerdictLike:
    """文档同源：可行性结论（四维判定）写在 MCP 文档里。"""
    doc = _text(root, MCP_DOC)
    needed = ("第三方 MCP", "可 pin", "不可行")
    missing = [item for item in needed if item not in doc]
    return _verdict("mcp-feasibility-documented", not missing, f"{MCP_DOC} 缺：{missing}")


def custom_verdicts(root: Path) -> list[VerdictLike]:
    return [
        *deliverable_verdicts(root),
        *protocol_verdicts(root),
        *in_scope_verdicts(root),
        *ec_file_verdicts(root),
        *record_verdicts(root),
        size_verdict(root),
        docs_verdict(root),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GOAL-028 收口复检（标准集 + 本轮特有断言）")
    parser.add_argument("--root", required=True, help="树根（不硬编码仓库根 ⇒ 可跑任意树）")
    parser.add_argument("--verdict-only", action="store_true", help="只打印判词行")
    return parser


def _line(verdict: VerdictLike) -> str:
    head = "PASS" if verdict.ok else "FAIL"
    detail = f" -> {verdict.detail}" if verdict.detail else ""
    return f"{head} {verdict.name}{detail}"


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    if not root.is_dir():
        print("FAIL goal028-root-missing -> 树根不存在")
        return 1
    standard = load_standard(root)

    def emit(items: Iterable[VerdictLike]) -> None:
        for item in items:
            print(_line(item))

    if standard is None:
        print("FAIL goal028-standard-assertions-loadable -> 标准断言集加载失败")
        return 1
    standard_verdicts = cast(
        Callable[[Path], list[VerdictLike]], getattr(standard, "standard_verdicts")
    )
    emit(standard_verdicts(root))
    emit(custom_verdicts(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
