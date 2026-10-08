"""GOAL-20260928-023 EC-02 判据：被点名的 `tools/` 脚本也要过产品同款的四道门。

**为什么需要**：`tools/` **不在** `PRODUCT_ROOTS`（`("apps", "services", "packages",
"adapters", "tests")`）⇒ 落在 `tools/` 的脚本**不被** `python/product-lint`、
`python/format-check`、`python/typecheck` 与规模门覆盖（GOAL-022 EC-01 的 `W-1` / `W-4`）。
本判据**不改** `PRODUCT_ROOTS`、**不改**任何既有 check、**不改** m0 条数 ——
它以**新增判据**的形式，对一个**有界射程**执行同样的四道检查：

1. `ruff format --check`；
2. `ruff check`（既有 `pyproject.toml` 配置已含 `max-complexity = 10` 与 `line-length = 100`）；
3. **规模**：函数 ≤ 50 行（口径 `end_lineno - lineno + 1`）、文件 ≤ 450 行（`splitlines()`）；
4. `mypy`（既有 `strict = true` 配置；**实测可稳定机械执行** ⇒ 无豁免）。

**射程有界、且射程写在判据源码里**（承 MEM-141：只靠文档取射程会被改文案绕过）：

- **必备清单** `IN_SCOPE`（源码里固化，至少含两树入口、标准收口断言集，以及
  收口验证器本身）—— 每加一个脚本都要**显式**加进来（见下方分区判据）；
- **加**规范页点名的脚本（`docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md` 里出现的
  `tools/**.py`）—— 这条是**推导**，不是手改；
- **不得**是「扫整个 `tools/`」：实测既有 `ruff check` **73 条**错误、
  `ruff format --check` **10 个文件**待重排，是历史遗留资产 ⇒
  它们以**清单 + 理由**逐条登记在 `LEGACY_OUT_OF_SCOPE`（不纳入射程），
  **清单增删必须显式**（`test_scope_partitions_every_tools_script_explicitly` 会把
  未分类的脚本判红）。
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONVENTIONS_DOC = ROOT / "docs" / "architecture" / "RECHECK_SCRIPT_CONVENTIONS.md"
TOOLS_DIR = "tools"

#: 规范页里「点名一个脚本」的合法形态（**通配写法不算点名**）。
_SCRIPT_PATH = re.compile(r"tools/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+\.py")

#: 规模的既有计数口径（与 `tests/tooling/test_python_source_limits.py` 同源）。
MAX_FILE_LINES = 450
MAX_FUNCTION_LINES = 50

#: **必备清单**（源码里固化）：射程的下界由它给出，不由文档给出。
#: `tools/research_mcp_server.py` 由 GOAL-20260927-027 EC-02 显式加入、
#: `tools/verify_goal027_closeout.py` 由 EC-05 显式加入（均为纯收紧：
#: 新增受判文件，不删任何条目）；它是交付型产品件（MCP server 本体），必须过四道门。
IN_SCOPE: tuple[str, ...] = (
    "tools/two_tree_recheck.py",
    "tools/closeout_recheck_assertions.py",
    "tools/verify_goal023_closeout.py",
    "tools/verify_goal024_closeout.py",
    "tools/verify_goal025_closeout.py",
    "tools/verify_goal026_closeout.py",
    "tools/audit_goal026_ledger.py",
    "tools/research_mcp_server.py",
    "tools/research_mcp_live.py",
    "tools/verify_goal027_closeout.py",
    "tools/audit_goal028_ledger.py",
    "tools/verify_goal028_closeout.py",
    # GOAL-029 EC-05：收口验证器 + 它复用的只读工具集（纯收紧 ⇒ 只增不删）。
    "tools/closeout_recheck_tools.py",
    "tools/verify_goal029_closeout.py",
    # GOAL-030 EC-05：收口验证器（复用同一只读工具集；纯收紧 ⇒ 只增不删）。
    "tools/verify_goal030_closeout.py",
    # GOAL-031 EC-05：收口验证器 + 它复用的本轮断言集（纯收紧 ⇒ 只增不删）。
    "tools/goal031_closeout_assertions.py",
    "tools/verify_goal031_closeout.py",
    # GOAL-032 EC-04：收口验证器 + 它复用的本轮断言集（纯收紧 ⇒ 只增不删）。
    "tools/goal032_closeout_assertions.py",
    "tools/verify_goal032_closeout.py",
    # GOAL-033 EC-04：收口验证器 + 它复用的本轮断言集（纯收紧 ⇒ 只增不删）。
    "tools/goal033_closeout_assertions.py",
    "tools/verify_goal033_closeout.py",
    # GOAL-034 EC-04：收口验证器 + 它复用的本轮断言集（纯收紧 ⇒ 只增不删）。
    "tools/goal034_closeout_assertions.py",
    "tools/verify_goal034_closeout.py",
    # GOAL-035 EC-04：收口验证器 + 它复用的本轮断言集（纯收紧 ⇒ 只增不删）。
    "tools/goal035_closeout_assertions.py",
    "tools/verify_goal035_closeout.py",
    # GOAL-036 EC-05：收口验证器 + 它复用的本轮断言集（纯收紧 ⇒ 只增不删）。
    "tools/goal036_closeout_assertions.py",
    "tools/verify_goal036_closeout.py",
    # GOAL-037 EC-05：收口验证器 + 它复用的本轮断言集（纯收紧 ⇒ 只增不删）。
    "tools/goal037_closeout_assertions.py",
    "tools/verify_goal037_closeout.py",
)

_REASON_PA1R = "PA-1R 历史资产（非 ASCII 命名落在 R-N1 豁免面）；纳入射程需另行授权"
_REASON_PROBE = "历史取证探针（一次性使用，非交付面）"
_REASON_SPIKE = "上游调研脚本（历史调研资产）"
_REASON_M12 = "M12 参考 / 冒烟脚本（历史里程碑资产）"
_REASON_GOAL015 = "GOAL-015 专属脚本（其收口验证器是 GOAL-023 的一般化先例）；纳入射程需另行授权"
_REASON_CLI = "历史 CLI / 工具（有 tests/tooling 行为判据，但无格式 / 规模 / 类型门）"
_REASON_LAB = "M12 / M13 实验门禁脚本（历史里程碑资产）"

#: 射程**之外**的历史遗留（**清单 + 理由**；不纳入射程，且不为其变绿而改历史资产）。
LEGACY_OUT_OF_SCOPE: tuple[tuple[str, str], ...] = (
    ("tools/PA1R发布真相v1.py", _REASON_PA1R),
    ("tools/PA1R密钥审计v1.py", _REASON_PA1R),
    ("tools/PA1R恢复闭包v1.py", _REASON_PA1R),
    ("tools/PA1R故障演练v1.py", _REASON_PA1R),
    ("tools/PA1R质量门禁v1.py", _REASON_PA1R),
    ("tools/PA1R运行演练v1.py", _REASON_PA1R),
    ("tools/backup.py", _REASON_CLI),
    ("tools/classify_local_gate_reds.py", _REASON_GOAL015),
    ("tools/credential_audit.py", _REASON_CLI),
    ("tools/docs_consistency_check.py", _REASON_CLI),
    ("tools/freeze_eval_dataset.py", _REASON_LAB),
    ("tools/gen_openapi.py", _REASON_CLI),
    ("tools/m12_ncbi_smoke.py", _REASON_M12),
    ("tools/m12_reference_workflow.py", _REASON_M12),
    ("tools/m12_relay_smoke.py", _REASON_M12),
    ("tools/personal_reference_workflow.py", _REASON_CLI),
    ("tools/probes/enumerate_clock_injected_pg_tests.py", _REASON_PROBE),
    ("tools/probes/probe_cancel_race.py", _REASON_PROBE),
    ("tools/probes/probe_canonical_state.py", _REASON_PROBE),
    ("tools/probes/probe_db_failure.py", _REASON_PROBE),
    ("tools/probes/probe_dependency_advisories.py", _REASON_PROBE),
    ("tools/probes/probe_dynamic_sql_forms.py", _REASON_PROBE),
    ("tools/probes/probe_migration.py", _REASON_PROBE),
    ("tools/probes/probe_outbox.py", _REASON_PROBE),
    ("tools/probes/probe_perf.py", _REASON_PROBE),
    ("tools/probes/probe_scheduled_recovery.py", _REASON_PROBE),
    ("tools/probes/probe_stale_worker.py", _REASON_PROBE),
    ("tools/probes/probe_telemetry_soak.py", _REASON_PROBE),
    ("tools/quarantine_and_run_m0.py", _REASON_GOAL015),
    ("tools/restore.py", _REASON_CLI),
    ("tools/snapshot_migrate.py", _REASON_CLI),
    ("tools/upstream-spikes/S1_import_fingerprint.py", _REASON_SPIKE),
    ("tools/upstream-spikes/S2_llm_construction.py", _REASON_SPIKE),
    ("tools/upstream-spikes/S3_agent_conversation_run.py", _REASON_SPIKE),
    ("tools/upstream-spikes/S4_cancel_pause_error.py", _REASON_SPIKE),
    ("tools/upstream-spikes/S5_local_workspace.py", _REASON_SPIKE),
    ("tools/upstream-spikes/S6_persistence_resume.py", _REASON_SPIKE),
    ("tools/verify_goal015_closeout.py", _REASON_GOAL015),
)


def tools_python_scripts() -> tuple[str, ...]:
    """`tools/` 下的全部 `.py`（**不**跟随符号链接；悬空链接会让 `rglob` 直接炸）。"""
    found: list[str] = []
    for base, directories, files in os.walk(ROOT / TOOLS_DIR, followlinks=False):
        directories[:] = [item for item in directories if item != "__pycache__"]
        for name in files:
            if name.endswith(".py"):
                found.append(Path(base).joinpath(name).relative_to(ROOT).as_posix())
    return tuple(sorted(found))


def doc_named_scripts() -> tuple[str, ...]:
    """规范页点名的 `tools/**.py`（推导出射程，不需手改清单）。

    只认**真实路径形态**（字母 / 数字 / `_` / `.` / `-` / `/`）——
    像 `tools/**.py` 这样的**通配写法**是散文里的泛指，**不是**点名；
    把它当路径会让射程里出现一个不存在的文件（本判据的第一次自跑就抓到了这一点）。
    """
    text = CONVENTIONS_DOC.read_text(encoding="utf-8") if CONVENTIONS_DOC.is_file() else ""
    named: set[str] = set()
    for token in text.replace("`", " ").split():
        cleaned = token.strip("()[]<>,.;:\"'")
        if _SCRIPT_PATH.fullmatch(cleaned):
            named.add(cleaned)
    return tuple(sorted(named))


def scope() -> tuple[str, ...]:
    """射程 = 必备清单 ∪ 规范页点名。"""
    return tuple(sorted(set(IN_SCOPE) | set(doc_named_scripts())))


def _run(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", *command],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def format_problems(root: Path, relatives: Sequence[str]) -> list[str]:
    """`ruff format --check`：不通过即返回问题（不是「打印一下」）。"""
    paths = [str(root.joinpath(*item.split("/"))) for item in relatives]
    result = _run(["ruff", "format", "--check", *paths])
    if result.returncode == 0:
        return []
    return [f"ruff format --check 不通过：{result.stdout.strip() or result.stderr.strip()}"]


def lint_problems(root: Path, relatives: Sequence[str]) -> list[str]:
    """`ruff check`：既有配置（含 `max-complexity = 10`、行宽 100）原样生效。"""
    paths = [str(root.joinpath(*item.split("/"))) for item in relatives]
    result = _run(["ruff", "check", *paths])
    if result.returncode == 0:
        return []
    return [f"ruff check 不通过：{result.stdout.strip() or result.stderr.strip()}"]


def typecheck_problems(root: Path, relatives: Sequence[str]) -> list[str]:
    """`mypy`：既有 `strict = true` 配置；**实测可稳定机械执行** ⇒ 不得假绿。"""
    paths = [str(root.joinpath(*item.split("/"))) for item in relatives]
    result = _run(["mypy", *paths])
    if result.returncode == 0:
        return []
    return [f"mypy 不通过：{result.stdout.strip() or result.stderr.strip()}"]


def function_spans(path: Path) -> Iterator[tuple[str, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.end_lineno:
            yield node.name, node.end_lineno - node.lineno + 1


def size_problems(root: Path, relatives: Sequence[str]) -> list[str]:
    """规模：函数 ≤ 50 行（`end_lineno - lineno + 1`）、文件 ≤ 450 行（`splitlines()`）。"""
    problems: list[str] = []
    for relative in relatives:
        path = root.joinpath(*relative.split("/"))
        if not path.is_file():
            problems.append(f"{relative} 不存在")
            continue
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_FILE_LINES:
            problems.append(f"{relative} 超过 {MAX_FILE_LINES} 行（{line_count}）")
        oversized = [name for name, span in function_spans(path) if span > MAX_FUNCTION_LINES]
        if oversized:
            problems.append(f"{relative} 有超过 {MAX_FUNCTION_LINES} 行的函数：{oversized}")
    return problems


def test_the_pinned_scope_contains_the_entry_and_the_assertion_set() -> None:
    """射程的**下界来自判据源码**：必备清单里必须有入口与标准收口断言集。"""
    required = ("tools/two_tree_recheck.py", "tools/closeout_recheck_assertions.py")
    missing = [item for item in required if item not in IN_SCOPE]
    assert not missing, f"必备清单缺少 {missing} ⇒ 射程下界不能只靠文档"
    assert set(IN_SCOPE) <= set(scope()), "推导出的射程吞掉了必备清单"


def test_doc_named_scripts_exist_and_join_the_scope() -> None:
    """规范页点名的脚本必须**存在**，且自动进入射程。"""
    named = doc_named_scripts()
    assert named, "规范页没有点名任何 tools/ 脚本 ⇒ 推导面失效"
    for relative in named:
        assert ROOT.joinpath(*relative.split("/")).is_file(), f"规范页点名的 {relative} 不存在"
        assert relative in scope(), f"规范页点名的 {relative} 没有进入射程"


def test_scope_partitions_every_tools_script_explicitly() -> None:
    """**清单增删必须显式**：`tools/` 下每个 `.py` 都恰好落在射程内或登记在案。"""
    inventory = set(tools_python_scripts())
    in_scope = set(scope())
    legacy = dict(LEGACY_OUT_OF_SCOPE)
    overlap = sorted(in_scope & set(legacy))
    assert not overlap, f"同一条脚本既在射程内又被登记为遗留：{overlap}"
    unclassified = sorted(inventory - in_scope - set(legacy))
    assert not unclassified, (
        f"这些 tools/ 脚本没有分类（新增脚本必须显式决定是否纳入射程）：{unclassified}"
    )
    stale = sorted((in_scope | set(legacy)) - inventory)
    assert not stale, f"清单引用了不存在的脚本（清单已陈旧）：{stale}"
    missing_reasons = sorted(path for path, reason in LEGACY_OUT_OF_SCOPE if not reason.strip())
    assert not missing_reasons, f"这些遗留条目没有给出理由：{missing_reasons}"
    assert len(legacy) >= 30, f"遗留清单只有 {len(legacy)} 条 ⇒ 疑似被清空"


def test_in_scope_scripts_are_formatted() -> None:
    problems = format_problems(ROOT, scope())
    assert not problems, "; ".join(problems)


def test_in_scope_scripts_pass_ruff_check() -> None:
    problems = lint_problems(ROOT, scope())
    assert not problems, "; ".join(problems)


def test_in_scope_scripts_pass_mypy() -> None:
    problems = typecheck_problems(ROOT, scope())
    assert not problems, "; ".join(problems)


def test_in_scope_scripts_respect_the_size_limits() -> None:
    problems = size_problems(ROOT, scope())
    assert not problems, "; ".join(problems)


def _broken_tree(directory: Path) -> Path:
    """一棵最小的「树」：一个同时违反四道门的脚本（去格式化 / 未用导入 / 未注解 / 超长函数）。"""
    target = directory / "tools" / "broken_probe.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"    step_{index} = {index}" for index in range(60))
    target.write_text(
        "import os\n\n\ndef broken(x):\n" + body + "\n    return 'single-quoted'\n",
        encoding="utf-8",
        newline="\n",
    )
    return target


def test_every_gate_actually_detects_a_broken_script(tmp_path: Path) -> None:
    """**判据自身按压**：四道门各自都能在一个人造坏脚本上报出问题（不是恒真）。

    没有这一例，「四道门全绿」可能只是四个**空转**的函数。
    """
    _broken_tree(tmp_path)
    relative = ["tools/broken_probe.py"]
    detected = {
        "format": format_problems(tmp_path, relative),
        "lint": lint_problems(tmp_path, relative),
        "mypy": typecheck_problems(tmp_path, relative),
        "size": size_problems(tmp_path, relative),
    }
    silent = sorted(name for name, problems in detected.items() if not problems)
    assert not silent, f"这些门在人造坏脚本上**没有**报出问题 ⇒ 门是空转的：{silent}"
