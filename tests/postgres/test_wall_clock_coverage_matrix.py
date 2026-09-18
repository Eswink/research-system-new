"""真墙钟覆盖矩阵的**机器判据**（GOAL-006 cycle 4 = EC-04 / RECHECK-096 W-4）。

矩阵写在 `tests/postgres/test_cross_process_real.py` 的模块 docstring 里（与用例同址，
读者不会迷路）。这里把它钉住：

1. **一一对应**：矩阵行 ≡ 该文件里的 `test_*` 函数（少一行 ⇒ 红；多余行 ⇒ 红）；
2. **判据形态可判定**：每行的等待判据必须是 `NO_WAIT` 或
   `BOUNDED_POLL(deadline=<n>s,interval=<m>s)`，且 `m` 真的出现在某个 `time.sleep(m)`、
   `n` 真的出现在某个 `timeout` 默认值上 —— 矩阵不许写一个文件里不存在的等待口径；
3. **没有无界等待**：文件里每个 `time.sleep` 都必须落在**含 deadline 守卫**
   （`time.monotonic()` + 截止时间）的函数里 —— "有界轮询，非固定 sleep" 由此成为结构事实；
4. **诚实边界在位**：docstring 必须写出"未覆盖的时序"小节且非空（不许用"全覆盖"收尾）；
5. **标记口径同源**：该文件必须打 `pytest.mark.timing_sensitive`（真实墙钟 ⇒ 串行跑）。

反证实跑（见 RECHECK-20260918-103）：删一行 ⇒ 第 1 条红；加一条无 deadline 的
`time.sleep(60)` ⇒ 第 3 条红；把某行判据改成 `SLEEP(3s)` ⇒ 第 2 条红。
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_MODULE = Path(__file__).parent / "test_cross_process_real.py"
_BOUNDED = re.compile(r"^BOUNDED_POLL\(deadline=(\d+)s,interval=(\d+(?:\.\d+)?)s\)$")
_NO_WAIT = "NO_WAIT"
_UNCOVERED_HEADING = "未覆盖的时序"


def _source() -> str:
    return _MODULE.read_text(encoding="utf-8")


def _module_docstring() -> str:
    tree = ast.parse(_source())
    return ast.get_docstring(tree) or ""


def _test_names() -> set[str]:
    tree = ast.parse(_source())
    return {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    }


def _matrix_rows() -> dict[str, str]:
    """docstring 里的矩阵行：`| 用例 | 等待判据 |`。"""
    rows: dict[str, str] = {}
    for line in _module_docstring().splitlines():
        stripped = line.strip()
        if not stripped.startswith("| test_"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        assert len(cells) == 2, f"矩阵行必须是 2 列：{stripped}"
        rows[cells[0]] = cells[1]
    return rows


def _timing_bullets() -> dict[str, str]:
    """每条用例的"时序 + 证伪条件"要点：``- `test_xxx`：…``（含折行续行）。"""
    bullets: dict[str, str] = {}
    current: str | None = None
    for line in _module_docstring().splitlines():
        stripped = line.strip()
        if stripped.startswith("- `test_"):
            name, _, rest = stripped[3:].partition("`")
            current = name.lstrip("`")
            bullets[current] = rest
            continue
        if current is None:
            continue
        if not stripped:
            current = None
            continue
        if not stripped.startswith("- "):
            bullets[current] = f"{bullets[current]} {stripped}"
    return bullets


def _sleep_arguments() -> list[float]:
    tree = ast.parse(_source())
    found: list[float] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "sleep":
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, int | float):
                found.append(float(arg.value))
    return found


def _deadline_defaults() -> list[float]:
    tree = ast.parse(_source())
    found: list[float] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        defaults = list(node.args.defaults) + [d for d in node.args.kw_defaults if d is not None]
        for arg, default in zip(
            [
                *node.args.args[len(node.args.args) - len(node.args.defaults) :],
                *node.args.kwonlyargs,
            ],
            defaults,
            strict=False,
        ):
            if arg.arg == "timeout" and isinstance(default, ast.Constant):
                if isinstance(default.value, int | float):
                    found.append(float(default.value))
    return found


def _enclosing_functions() -> list[tuple[int, int, bool, str]]:
    """(起行, 止行, 是否有 deadline 守卫, 名字)——用于判定某个调用落在哪段函数体里。

    "有 deadline 守卫" = 函数体里同时出现 `time.monotonic()` 与 `deadline`：有界轮询的
    结构特征。含嵌套函数时，只要函数链上任何一层有守卫就算有界。
    """
    tree = ast.parse(_source())
    ranges: list[tuple[int, int, bool, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            body = ast.unparse(node)
            guarded = "monotonic()" in body and "deadline" in body
            ranges.append((node.lineno, node.end_lineno or node.lineno, guarded, node.name))
    return ranges


def _unbounded_sleeps() -> list[str]:
    """任何 `time.sleep` 都必须落在**有 deadline 守卫**的函数里（否则就是无界等待）。

    模块级（不在任何函数里）的 sleep 同样算无界——它连"停止条件"都没有。
    """
    ranges = _enclosing_functions()
    offenders: list[str] = []
    for node in ast.walk(ast.parse(_source())):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "sleep":
            continue
        enclosing = [item for item in ranges if item[0] <= node.lineno <= item[1]]
        if not enclosing:
            offenders.append(f"<module>:{node.lineno}")
            continue
        innermost = max(enclosing, key=lambda item: item[0])
        if not any(item[2] for item in enclosing):
            offenders.append(f"{innermost[3]}:{node.lineno}")
    return offenders


def test_matrix_and_test_functions_correspond_one_to_one() -> None:
    rows = _matrix_rows()
    bullets = _timing_bullets()
    tests = _test_names()
    assert set(rows) == tests, {
        "只在矩阵里": sorted(set(rows) - tests),
        "只在文件里": sorted(tests - set(rows)),
    }
    assert set(bullets) == tests, {
        "只在要点里": sorted(set(bullets) - tests),
        "缺时序/证伪要点": sorted(tests - set(bullets)),
    }


def test_every_row_states_a_checkable_wait_criterion() -> None:
    sleeps = _sleep_arguments()
    deadlines = _deadline_defaults()
    for name, criterion in _matrix_rows().items():
        assert "证伪" in _timing_bullets()[name], f"{name} 必须写明证伪条件"
        if criterion == _NO_WAIT:
            continue
        matched = _BOUNDED.match(criterion)
        assert matched is not None, f"{name} 的等待判据形态不可判定：{criterion}"
        deadline, interval = float(matched.group(1)), float(matched.group(2))
        assert interval in sleeps, f"{name} 声明的轮询间隔 {interval}s 不在文件里"
        assert deadline in deadlines, f"{name} 声明的 deadline {deadline}s 不是任何 timeout 默认值"


def test_no_unbounded_sleep_in_the_file() -> None:
    assert _unbounded_sleeps() == [], _unbounded_sleeps()


def test_uncovered_timings_are_stated() -> None:
    docstring = _module_docstring()
    assert _UNCOVERED_HEADING in docstring, "必须写明未覆盖的时序（诚实边界）"
    tail = docstring.split(_UNCOVERED_HEADING, 1)[1]
    bullets = [line for line in tail.splitlines() if line.strip().startswith("-")]
    assert len(bullets) >= 3, f"未覆盖项至少逐条点名：{bullets}"


def test_the_file_is_marked_timing_sensitive() -> None:
    source = _source()
    assert "pytest.mark.timing_sensitive" in source, "真实墙钟用例必须打 timing_sensitive"


@pytest.mark.parametrize("name", sorted(_test_names()))
def test_every_test_declares_its_timing_surface(name: str) -> None:
    """每个用例在矩阵里都有非空的"覆盖的时序 + 证伪条件"要点——不写就是漏登记。"""
    bullet = _timing_bullets().get(name)
    assert bullet is not None, f"{name} 没有时序/证伪要点"
    assert len(bullet) >= 24, f"{name} 的时序说明太短：{bullet!r}"
