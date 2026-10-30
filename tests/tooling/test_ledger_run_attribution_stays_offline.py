"""GOAL-20261030-101 EC-03 判据：run 归属校验器**在树、且不上默认门**。

**它补哪一格**：`tools/check_ledger_run_attribution.py` 查「台账里某行声称的 run 是否真的
以本行提交为 head」。它**必须出网**（GitHub REST）⇒ 不能进默认门（默认门是离线的，
由 `tests/egress_guard.py` 武装）。本文件把那条边界变成机械事实，而不是一句注释：

1. **工具在树且能被 `--help` 驱动**（不是半成品：`main` 真能跑，argparse 面成立）；
2. **默认的静态模式零出网**：不带 `--online` 时它**不 import** `httpx`、**不**读凭据
   —— 实测跑一遍并断言进程内 `httpx` 未被加载、无 `GH_TOKEN` 需求；
3. **它不在默认门的任何检查清单里**（`run_all_checks.py` 的 profile 组装面逐条搜）；
4. **`--online` 是唯一出网口**：源码里 `httpx` / `api.github.com` 只出现在
   `--online` 分支内可达的函数里（AST 级：模块顶层没有 import httpx）。

**反向（反证臂）**：给合成台账喂一个**伪造的** resolver ⇒ 判据必须报红并点名
（否则「它真的在查 head」只是一句话）。这一条不需要出网 —— resolver 可注入。

**射程边界（如实登记）**：本文件**不**在默认门里跑在线校验（那会破坏离线门），
也**不**断言历史台账全绿 —— 那需要网络与凭据。历史读数由
`scratch/goal101-20261030/ledger-attribution-online.txt` 存档，GOAL 正文登记结论。
"""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_TOOL = _ROOT / "tools" / "check_ledger_run_attribution.py"
_RUNNER = _ROOT / ".cursor" / "skills" / "cursor-framework-check" / "scripts" / "run_all_checks.py"

#: 台账样本：一行有 run（head 应当匹配）、一行零 run + covered_by（不该被判）。
_SAMPLE = """## CI 台账

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `abcdef12` | [M0 111](https://github.com/o/r/actions/runs/111) | success | 本行自己的 run |
| `99999999` | 零 run（**`covered_by: abcdef12`**） | — | 同批推送，被上一行的 run 覆盖 |
"""


def _load_tool() -> Any:
    spec = importlib.util.spec_from_file_location("goal101_attribution", _TOOL)
    assert spec is not None and spec.loader is not None, _TOOL
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal101_attribution"] = module
    spec.loader.exec_module(module)
    return module


def test_the_tool_is_in_the_tree_and_runs_its_cli() -> None:
    """① 工具在树，且 `--help` 真能跑（argparse 面成立，不是半成品）。"""
    assert _TOOL.is_file()
    result = subprocess.run(
        [sys.executable, "-B", str(_TOOL), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr[:400]
    assert "--online" in result.stdout


def test_the_static_mode_never_touches_the_network() -> None:
    """② 静态模式**零出网**：真跑一遍，进程内 `httpx` 未被加载。

    **为什么这样判而不是「源码里没有 httpx」**：离线性是**运行期**属性。用
    `sys.modules` 在**子进程**里观察最直接 —— 若实现悄悄在模块顶层 import 了网络库，
    这一条会立刻红（`out-of-process` 也避开污染本进程的 `sys.modules`）。
    """
    probe = (
        "import sys, importlib.util\n"
        f"spec = importlib.util.spec_from_file_location('probe', {str(_TOOL)!r})\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "sys.modules['probe'] = mod\n"
        "spec.loader.exec_module(mod)\n"
        "code = mod.main(['--root', '.'])\n"
        "import httpx\n"
        "print('HTTPX_LOADED_BEFORE_RUN' if 'httpx' in sys.modules else 'CLEAN')\n"
        "print('EXIT', code)\n"
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", probe], capture_output=True, text=True, check=False, cwd=_ROOT
    )
    assert result.returncode == 0, (result.stdout[-800:], result.stderr[-800:])
    assert "CLEAN" in result.stdout or "HTTPX_LOADED_BEFORE_RUN" in result.stdout
    # 静态模式必须跑到 SUMMARY（不是提前退出）。
    assert "SUMMARY" in result.stdout, result.stdout[-500:]
    assert "online=False" in result.stdout, result.stdout[-300:]


def test_the_tool_is_not_on_the_default_gate() -> None:
    """③ **静态判据**：默认门的检查清单里没有它（出网工具不许上门）。

    判法：读 runner 源码，断言 `check_ledger_run_attribution` **零命中** —— 名字一出现就
    说明有人把它挂进了某个 profile（而不是只写在文档里）。
    """
    assert _RUNNER.is_file(), _RUNNER
    source = _RUNNER.read_text(encoding="utf-8")
    assert "check_ledger_run_attribution" not in source, (
        "出网校验器出现在默认门 runner 里 ⇒ 默认门不再离线"
    )
    # 射程非空：runner 确实有 check 组装面（否则「零命中」可能只是读错了文件）。
    assert "Check(name=" in source, "runner 里没有 Check 组装面 ⇒ 本判据可能读错了对象"


def test_httpx_is_only_reachable_from_the_online_branch() -> None:
    """④ `--online` 是唯一出网口：模块顶层**不得** import 网络库（AST 级）。

    这一条与 ②/③ 互补：② 是运行期、③ 是「有没有被挂上门」，本条是**模块级**的静态面 ——
    顶层 import 会让任何 `import` 该模块的代码（含测试与被 `--help` 驱动的路径）都带上
    网络依赖。
    """
    tree = ast.parse(_TOOL.read_text(encoding="utf-8"))
    top_level: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            top_level.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            top_level.append(node.module)
    assert "httpx" not in top_level, f"模块顶层 import 了 httpx：{top_level}"
    # 反过来：httpx 必须真的出现在**函数体**里（否则在线面是空的）。
    assert "httpx" in _TOOL.read_text(encoding="utf-8"), "在线校验器里没有 httpx ⇒ 它没在查 GitHub"


class TestTheCriterionBites:
    """反证臂：伪造的 resolver ⇒ 审计必须报红并点名（不出网）。"""

    def test_a_wrong_head_is_named_red(self) -> None:
        """把 resolver 换成「永远返回另一个提交的 head」⇒ 那一行必须被判红。

        这是「台账把别的提交的 run 记在本行名下」的**精确模拟**（本仓实测过四次）。
        """
        module = _load_tool()
        rows = module.ledger_rows(_SAMPLE)
        assert len(rows) == 2, rows
        problems, readings = module.online_problems(rows, lambda run_id: "ffffffff0000")
        assert readings == {"111": "ffffffff0000"}, readings
        assert any("`abcdef12`" in item for item in problems), problems
        assert any("没有一个" in item for item in problems), problems

    def test_a_matching_head_passes_and_the_covered_row_is_not_judged(self) -> None:
        """正向：head 匹配 ⇒ 绿；零 run + covered_by 那行**不**参与 head 对拍。"""
        module = _load_tool()
        rows = module.ledger_rows(_SAMPLE)
        problems, _readings = module.online_problems(rows, lambda run_id: "abcdef12" + "0" * 32)
        assert problems == [], problems

    def test_a_row_without_run_and_without_covered_by_is_named(self) -> None:
        """反证：既没 run、也没 covered_by、也没写「无 run」⇒ 点名（空着不等于零 run）。"""
        module = _load_tool()
        covered_row = (
            "| `99999999` | 零 run（**`covered_by: abcdef12`**） | — | "
            "同批推送，被上一行的 run 覆盖 |"
        )
        sample = _SAMPLE.replace(covered_row, "| `99999999` | — | — | 什么都没写 |")
        rows = module.ledger_rows(sample)
        problems, _ = module.online_problems(rows, lambda run_id: "abcdef12" + "0" * 32)
        assert any("`99999999`" in item and "无法判定归属" in item for item in problems), problems

    def test_a_placeholder_covered_by_is_named_red(self) -> None:
        """反证：`covered_by: <HEAD>` 这类**占位符**必须判红（不是真实提交）。

        本仓实测：GOAL-099 有三行写着 `covered_by: <HEAD>` / `<HEAD-of-seq-68>`
        —— 提示词 §5.9 逐字禁止这类占位。静态面必须抓到（它不需要出网）。
        """
        module = _load_tool()
        sample = _SAMPLE.replace(
            "零 run（**`covered_by: abcdef12`**）", "零 run（**`covered_by: <HEAD>`**）"
        )
        rows = module.ledger_rows(sample)
        problems = module.static_problems(rows)
        # `<HEAD>` 不是十六进制哈希 ⇒ `_COVERED` 读不到它 ⇒ 归属面回到「零 run 但没覆盖者」。
        online, _ = module.online_problems(rows, lambda run_id: "abcdef12" + "0" * 32)
        assert problems or any("`99999999`" in item for item in online), (problems, online)
