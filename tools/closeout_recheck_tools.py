#!/usr/bin/env python3
"""收口复检的小工具集（GOAL-029 EC-05）：读树、AST 取函数/类/字面量、判词构造。

**为什么单列**：`tools/verify_goal029_closeout.py` 有 450 行硬上限（规模门），而它的断言
又必须逐条可读 —— 把「怎么读树」与「断言什么」分开，两边都保持在可读长度内。
本模块只做只读的机械动作，**不含**任何 GOAL-029 特有的断言。
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from typing import Any, Protocol, cast


class VerdictLike(Protocol):
    """标准集 `Verdict` 的结构面（只读三个字段，不 import 其类型）。"""

    name: str
    ok: bool
    detail: str


class _SimpleVerdict:
    def __init__(self, name: str, ok: bool, detail: str = "") -> None:
        self.name = name
        self.ok = ok
        self.detail = detail


def tree(root: Path, relative: str) -> Path:
    return root.joinpath(*relative.split("/"))


def text(root: Path, relative: str) -> str:
    path = tree(root, relative)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def verdict(name: str, ok: bool, detail: str = "") -> VerdictLike:
    return cast(VerdictLike, _SimpleVerdict(name, ok, detail))


def defines(text_body: str, name: str) -> bool:
    """模块里是否定义了该函数 / 类（AST，不靠文本搜索）。"""
    if not text_body:
        return False
    try:
        parsed = ast.parse(text_body)
    except SyntaxError:
        return False
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.name == name
        for node in ast.walk(parsed)
    )


def module_literal(text_body: str, assignment: str) -> object | None:
    """取模块级 `assignment = (...)` 的字面量（`Assign` 与 `AnnAssign` 都认）。"""
    if not text_body:
        return None
    try:
        parsed = ast.parse(text_body)
    except SyntaxError:
        return None
    for node in parsed.body:
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if assignment in targets:
                try:
                    value: object = ast.literal_eval(node.value)
                except ValueError:
                    return None
                return value
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", None) == assignment:
            if node.value is None:
                return None
            try:
                ann_value: object = ast.literal_eval(node.value)
            except ValueError:
                return None
            return ann_value
    return None


def binding_tool_names(text_body: str, assignment: str) -> set[str]:
    """出厂绑定表的**工具名**集合（表是 `(工具名, provider_id, tool_id)` 三元组的元组）。"""
    value = module_literal(text_body, assignment)
    if not isinstance(value, tuple):
        return set()
    return {str(item[0]) for item in value if isinstance(item, tuple) and item}


def count_test_defs(text_body: str) -> int:
    if not text_body:
        return 0
    try:
        parsed = ast.parse(text_body)
    except SyntaxError:
        return 0
    return sum(
        1
        for node in ast.walk(parsed)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    )


def _charter_progress_module() -> Any:
    """按**路径**加载共享读取面（`tools/` 不是包；先写 `sys.modules` 再 `exec_module`）。"""
    path = Path(__file__).resolve().parent / "charter_progress.py"
    spec = importlib.util.spec_from_file_location("charter_progress_shared", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["charter_progress_shared"] = module
    spec.loader.exec_module(module)
    return module


def _read(root: Path, goal_id: str) -> Any:
    """共享读取面的 `ProgressRead`（结构面：`rows` / `sources` / `contexts`）。"""
    reader = getattr(_charter_progress_module(), "progress_rows")
    return cast(Any, reader)(root, goal_id)


def progress_rows(root: Path, goal_id: str) -> list[str]:
    """宪章「进展记录」里点名该 GOAL 的数据行（**活跃面或归档**）。

    这条委托是 GOAL-101 EC-02 的修法：14 个验证器此前各自只读**活跃面**，于是进展行一被
    归档，它们自己的收口复检就产出 2 条**假负**（实测 14×2 = 28 条）。共享 helper 让
    「活跃面或归档」只有**一处**实现 —— 17 处各写一遍必然漂移（098 曾手工加过一次，
    只有它有）。

    加载失败 ⇒ 抛 `AssertionError`（**不**静默返回空表：空表会被读成「这一行不存在」，
    那是把资产故障伪装成判负 —— 与「崩了就不是判据」同一条纪律的反面）。
    """
    return [str(row) for row in _read(root, goal_id).rows]


def progress_context(root: Path, goal_id: str) -> str:
    """该 GOAL 的进展行所在**正文**（活跃面那份是小节正文；归档那份是整份文件）。

    供「插在最上面」这类**位置**断言使用：判的是「这一行在它所在的那张表里的位置」，
    不是「它永居活跃面第一行」。
    """
    contexts = _read(root, goal_id).contexts
    return str(contexts[0]) if contexts else ""


def progress_sources(root: Path, goal_id: str) -> list[str]:
    """与 `progress_rows` 一一对应的来源路径（判词里能说「这行在归档里」）。"""
    return [str(item) for item in _read(root, goal_id).sources]


__all__ = [
    "VerdictLike",
    "binding_tool_names",
    "count_test_defs",
    "defines",
    "module_literal",
    "progress_rows",
    "progress_sources",
    "text",
    "tree",
    "verdict",
]
