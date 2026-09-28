"""GOAL-20260928-023 EC-01 判据：标准收口断言集**在树、可跑、不空转、条款不悬空**。

判什么（缺一不可）：

1. **在树且声明公开面**：`tools/closeout_recheck_assertions.py` 存在，且按 **AST** 真的
   声明了 `Verdict` / `standard_verdicts` / `emit`（不是「文本里出现过这些名字」）；
2. **判词纯度**（规范页第 ② 条）：`--verdict-only` 的输出**只有** `PASS` / `FAIL` 行；
3. **判词路径无关**（第 ⑥ 条）：两棵**不同**的树跑出来的判词行都不含各自的树根
   —— 否则两树入口会（正确地）拒绝它；
4. **不空转**：在**空树**上必须有一批 `FAIL`。恒真的断言集不是判据（承 MEM-156：
   受判集合为空 ⇒ 判据尚未生效）；
5. **条款不得悬空**：规范页的断言集小节**点名**它，且**被点名的那个文件**按 **AST**
   真的定义了口径入口 ⇒ 改名 / 搬走即判红；
6. **抽走 ⇒ 判红**：把它从一棵树里抽走，`closeout-assertions-present` 这条判词必须翻转。

夹具（空树）由本判据在 `tmp_path` 里运行时生成，不落进仓库。
"""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "closeout_recheck_assertions.py"
DOC = ROOT / "docs" / "architecture" / "RECHECK_SCRIPT_CONVENTIONS.md"

#: 断言集小节的结构性锚点（增补文案保持它即可）。
SECTION = "## 标准收口断言集"

#: 判词行的前缀（与两树入口的 `VERDICT_PREFIXES` 同源口径）。
PREFIXES = ("PASS", "FAIL")

#: 该断言集必须声明的公开面（按 AST 读声明）。
PUBLIC_FACE = ("Verdict", "standard_verdicts", "emit")

#: 「抽走 ⇒ 判红」要观察的那条判词。
SELF_VERDICT = "closeout-assertions-present"


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, f"无法加载模块: {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _declared_names(path: Path) -> set[str]:
    """模块里**声明**的名字（函数 / 类）；按 AST 判，不按文本巧合判。"""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
    return names


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPT), "--root", str(root), "--verdict-only"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _verdict_lines(stdout: str) -> list[str]:
    return [line for line in stdout.splitlines() if line.strip()]


def test_the_assertion_set_is_in_the_tree_and_declares_its_public_face() -> None:
    """在树，且**按 AST** 声明 `Verdict` / `standard_verdicts` / `emit`。"""
    assert SCRIPT.is_file(), f"标准收口断言集不在树：{SCRIPT}"
    declared = _declared_names(SCRIPT)
    missing = [name for name in PUBLIC_FACE if name not in declared]
    assert not missing, f"断言集没有声明公开面 {missing}"


def test_verdict_only_output_is_pure_and_all_green_on_this_tree() -> None:
    """纯度为判据；且本树上的公共断言**全绿**（有红就逐行报出来）。"""
    result = _run(ROOT)
    lines = _verdict_lines(result.stdout)
    assert lines, f"断言集没有产出任何判词行：{result.stdout}{result.stderr}"
    impure = [line for line in lines if not line.startswith(PREFIXES)]
    assert not impure, f"输出不纯（非判词行）：{impure}"
    reds = [line for line in lines if line.startswith("FAIL")]
    assert not reds, "公共断言在本树上判红：" + "; ".join(reds)


def test_verdicts_are_path_independent_across_two_different_trees(tmp_path: Path) -> None:
    """两棵**不同**的树：判词行都不含各自的树根（第 ⑥ 条口径）。"""
    empty = tmp_path / "empty-tree"
    empty.mkdir(parents=True, exist_ok=True)
    for root in (ROOT, empty):
        result = _run(root)
        lines = _verdict_lines(result.stdout)
        assert lines, f"{root} 上没有产出判词行"
        leaked = [line for line in lines if str(root) in line]
        assert not leaked, f"判词与路径相关（含 {root}）：{leaked}"


def test_an_empty_tree_is_not_vacuously_green(tmp_path: Path) -> None:
    """**不空转**：空树上必须有一批判红 —— 否则「全绿」只是恒真（承 MEM-156）。"""
    empty = tmp_path / "empty-tree"
    empty.mkdir(parents=True, exist_ok=True)
    result = _run(empty)
    reds = [line for line in _verdict_lines(result.stdout) if line.startswith("FAIL")]
    assert len(reds) >= 5, f"空树上只判红了 {len(reds)} 条 ⇒ 断言集接近恒真：{reds}"
    assert result.returncode != 0, "空树却以 0 退出 ⇒ 判红没有传播给退出码"


def test_the_doc_section_names_the_assertion_set_and_the_file_defines_it() -> None:
    """**条款不得悬空**：规范页点名它，且被点名的文件**按 AST** 真的定义了口径入口。"""
    text = DOC.read_text(encoding="utf-8")
    assert SECTION in text, f"规范页缺少断言集小节 {SECTION!r}"
    section = text.split(SECTION, 1)[1].split("\n## ", 1)[0]
    relative = "tools/closeout_recheck_assertions.py"
    assert relative in section, f"断言集小节里没有点名 {relative}"
    named = ROOT.joinpath(*relative.split("/"))
    assert named.is_file(), f"条款点名的 {relative} 不存在 ⇒ 条款悬空"
    assert "standard_verdicts" in _declared_names(named), (
        f"条款点名的 {relative} 没有声明 standard_verdicts ⇒ 点名的是一个空壳"
    )


def test_taking_the_assertion_set_away_flips_its_own_verdict(tmp_path: Path) -> None:
    """**抽走 ⇒ 判红**：把它从一棵树里抽走，`closeout-assertions-present` 必须翻转。"""
    module = _load(SCRIPT, "goal023_closeout_assertions_probe")
    here = {item.name: item for item in module.standard_verdicts(ROOT)}
    assert here[SELF_VERDICT].ok, f"本树上 {SELF_VERDICT} 应当是绿的：{here[SELF_VERDICT]}"
    empty = tmp_path / "empty-tree"
    empty.mkdir(parents=True, exist_ok=True)
    away = {item.name: item for item in module.standard_verdicts(empty)}
    assert not away[SELF_VERDICT].ok, (
        f"断言集被抽走却仍判绿 ⇒ 这条判词没有真的在断言：{away[SELF_VERDICT]}"
    )
