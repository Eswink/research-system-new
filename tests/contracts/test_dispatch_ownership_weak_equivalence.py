"""弱同判边界逐条点名，且点名本身可机器校验（GOAL-20260918-006 cycle 5 = EC-05 ②）。

`dispatch_ownership_many` 的契约里有两类轴：**可同判轴**（三实现必须给同一个答案，判据在
契约套件里按 `_FACTORIES` 参数化，**含 Fake**）与**不可同判轴**（Fake 没有那套语义，真实现
判据单列）。把两列写进契约文本还不够——文本会漂：删掉一条轴、把某条"三实现"用例悄悄改成
只跑持久化实现、把引用指到一个不存在的用例，读起来都还像回事。

本文件把点名变成可判定的：port 契约文本（模块 docstring 末节）里每条 `[同判]` / `[不同判]`
都必须点名判据文件与用例名，引用必须解析得到，且**引用关系的强度必须与它声称的一致**——

1. `[同判]` 的判据必须真的在三实现上跑（装饰器引用 `_FACTORIES`），而 `_FACTORIES` 来自
   注册表且确实含 `FakeWorkflowEngine`；
2. `[同判]` 与契约套件里**所有**三实现参数化用例**双向一一对应**（少点名 = 漏登记，
   多点名 = 文本在撒谎）；
3. `[不同判]` 的判据**不许**声称三实现，且文本要点名 Fake 为什么不同判；
4. 上限（EC-05 ①）的值只在 port 常量里写一次，`PORTS.md` / `CONTROL_PLANE_API.md`
   必须点名它并写出同一个数，并指向本文件。

反证（实跑见 PLAN-20260918-104 / RECHECK-20260918-104）：删一条轴、把
`test_the_batch_read_equals_the_per_run_read` 改成 `_PERSISTENT_FACTORIES`、把引用改成
不存在的用例名、改掉文档里的数字——本文件任一条用例都会红。
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from adapters.fakes.workflow_engine import FakeWorkflowEngine
from packages.application.ports import workflow_engine as port
from tests.contracts.registry import PORT_IMPLEMENTATIONS

_ROOT = Path(__file__).resolve().parents[2]
_CONTRACT_FILE = "tests/contracts/test_dispatch_ownership_contract.py"
_JUDGEMENT_FILE = "tests/contracts/test_dispatch_ownership_weak_equivalence.py"
_DOCS = ("docs/architecture/PORTS.md", "docs/api/CONTROL_PLANE_API.md")
_CITED_PATH = re.compile(r"`((?:tests|packages|adapters|services|docs)/[\w./-]+\.py)`")
_CITED_TEST = re.compile(r"`(test_\w+)`")
_DEFAULT_PATH_MARKER = "可同判轴的判据文件："
_THREE_WAY = re.compile(r",\s*_FACTORIES\s*\)")


def _module_docstring() -> str:
    return ast.get_docstring(ast.parse(Path(port.__file__).read_text(encoding="utf-8"))) or ""


def _method_docstring(name: str) -> str:
    source = Path(port.__file__).read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_docstring(node) or ""
    raise AssertionError(f"port 里找不到 {name}")


def _axes() -> list[tuple[str, str]]:
    """`[(kind, text)]`，kind ∈ {同判, 不同判}；续行折进上一条（docstring 会折行）。

    清单落在 port **模块 docstring**（方法 docstring 受 50 行函数门禁约束，只留指针）。
    """
    _default, axes = _axes_section()
    return axes


def _axes_section() -> tuple[str, list[tuple[str, str]]]:
    """返回 `(可同判轴默认判据文件, 轴清单)`。

    轴文本里点名判据文件是**要求**（引用必须可解析）；清单前的
    `可同判轴的判据文件：` 一行给出可同判轴的默认文件，免得每条重复写一遍全路径。
    """
    lines = _module_docstring().splitlines()
    start = next(
        index
        for index, line in enumerate(lines)
        if line.startswith("弱同判边界（GOAL-20260918-006 cycle 5")
    )
    default = ""
    axes: list[tuple[str, str]] = []
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith(_DEFAULT_PATH_MARKER):
            paths = _CITED_PATH.findall(stripped)
            assert len(paths) == 1, f"{_DEFAULT_PATH_MARKER} 行只写一个文件：{stripped}"
            default = paths[0]
            continue
        marker = next(
            (kind for kind in ("同判", "不同判") if stripped.startswith(f"- [{kind}] ")),
            None,
        )
        if marker is not None:
            axes.append((marker, stripped[len(marker) + 4 :]))
        elif axes and stripped:
            kind, text = axes[-1]
            axes[-1] = (kind, f"{text} {stripped}")
    assert default, f"清单前必须有一行 `{_DEFAULT_PATH_MARKER}`"
    return default, axes


def _comparable() -> list[str]:
    return [entry for kind, entry in _axes() if kind == "同判"]


def _excluded() -> list[str]:
    return [entry for kind, entry in _axes() if kind == "不同判"]


def _module_source(relative: str) -> str:
    return (_ROOT / relative).read_text(encoding="utf-8")


def _functions(relative: str) -> dict[str, ast.FunctionDef]:
    tree = ast.parse(_module_source(relative))
    return {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}


def _decorators(node: ast.FunctionDef) -> str:
    return " ".join(ast.unparse(decorator) for decorator in node.decorator_list)


def _cited(entry: str) -> tuple[list[str], list[str]]:
    """轴文本里的 `(文件, 用例名)`；没写文件的轴落到默认判据文件上。"""
    default, _ = _axes_section()
    return _CITED_PATH.findall(entry) or [default], _CITED_TEST.findall(entry)


def _three_way_tests() -> set[str]:
    return {
        name
        for name, node in _functions(_CONTRACT_FILE).items()
        if name.startswith("test_") and _THREE_WAY.search(_decorators(node))
    }


def test_both_axis_lists_are_present_and_substantial() -> None:
    """两类轴都要在契约文本里，且不可同判轴要逐条点名（不是一句"Fake 更弱"带过）。"""
    assert len(_comparable()) >= 5, _comparable()
    assert len(_excluded()) >= 3, _excluded()
    contract = _method_docstring("dispatch_ownership_many")
    assert "MAX_DISPATCH_OWNERSHIP_BATCH" in contract, "上限必须写在契约文本里"
    assert _JUDGEMENT_FILE in contract, "契约文本要指向本判据文件（点名才可复核）"


def test_every_axis_cites_a_resolvable_test() -> None:
    """点名必须落到真实存在的人和文件上——引用不是修辞。"""
    for kind, entry in _axes():
        paths, names = _cited(entry)
        assert paths and names, f"[{kind}] 轴必须点名判据（文件 + 用例名）：{entry}"
        for relative in paths:
            assert (_ROOT / relative).exists(), f"引用指向不存在的文件：{relative}"
        for name in names:
            assert any(name in _functions(relative) for relative in paths), (
                f"点名的用例 {name} 不在本轴引用的任何文件里：{paths}"
            )


def test_a_comparable_axis_really_runs_on_all_three_implementations() -> None:
    """`[同判]` 的判据必须在三实现上跑：装饰器引用 `_FACTORIES`（不是只跑持久化实现）。"""
    for entry in _comparable():
        paths, names = _cited(entry)
        assert paths == [_CONTRACT_FILE], f"同判轴应点名契约套件，而不是 {paths}"
        for name in names:
            decorators = _decorators(_functions(_CONTRACT_FILE)[name])
            assert _THREE_WAY.search(decorators), (
                f"{name} 的装饰器不是三实现参数化，不能当'同判'判据：{decorators}"
            )


def test_the_three_way_fixture_really_contains_the_fake() -> None:
    """`_FACTORIES` 必须来自注册表，且注册表里真的有 Fake（否则"三实现"是空话）。"""
    assert FakeWorkflowEngine in PORT_IMPLEMENTATIONS["workflow_engine"]
    assert re.search(
        r'_FACTORIES[^\n]*PORT_IMPLEMENTATIONS\["workflow_engine"\]', _module_source(_CONTRACT_FILE)
    ), "契约套件的 _FACTORIES 必须直接来自注册表"


def test_the_comparable_axes_cover_every_three_way_test() -> None:
    """双向一一对应：三实现用例集 == 被点名的同判轴集（防止"加了用例没登记"）。"""
    named = {name for entry in _comparable() for name in _cited(entry)[1]}
    in_suite = _three_way_tests()
    assert in_suite == named, {
        "套件里有但没点名": sorted(in_suite - named),
        "点名了但套件里没有": sorted(named - in_suite),
    }


def test_an_excluded_axis_says_why_the_fake_differs() -> None:
    """`[不同判]` 必须点名 Fake 的差异，且判据**不许**声称三实现（那就是同判了）。"""
    for entry in _excluded():
        assert "Fake" in entry, f"不可同判轴要说清 Fake 为什么不同判：{entry}"
        paths, names = _cited(entry)
        for name in names:
            relative = next(path for path in paths if name in _functions(path))
            decorators = _decorators(_functions(relative)[name])
            assert not _THREE_WAY.search(decorators), (
                f"{name} 声称三实现，不能当'不同判'的判据：{decorators}"
            )


def test_the_cap_value_lives_in_one_place_and_the_docs_name_it() -> None:
    """上限（EC-05 ①）：值只在 port 常量里写一次，两个文档点名它、写出同一个数、指向本文件。"""
    assert port.MAX_DISPATCH_OWNERSHIP_BATCH > 0
    value = str(port.MAX_DISPATCH_OWNERSHIP_BATCH)
    for relative in _DOCS:
        source = _module_source(relative)
        lines = [line for line in source.splitlines() if "MAX_DISPATCH_OWNERSHIP_BATCH" in line]
        assert lines, f"{relative} 必须点名上限常量"
        assert any(value in line for line in lines), f"{relative} 必须写出上限的值 {value}"
        assert _JUDGEMENT_FILE in source, f"{relative} 必须指向本判据文件"
