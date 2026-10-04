#!/usr/bin/env python3
"""收口复检的小工具集（GOAL-029 EC-05）：读树、AST 取函数/类/字面量、判词构造。

**为什么单列**：`tools/verify_goal029_closeout.py` 有 450 行硬上限（规模门），而它的断言
又必须逐条可读 —— 把「怎么读树」与「断言什么」分开，两边都保持在可读长度内。
本模块只做只读的机械动作，**不含**任何 GOAL-029 特有的断言。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Protocol, cast


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


__all__ = [
    "VerdictLike",
    "binding_tool_names",
    "count_test_defs",
    "defines",
    "module_literal",
    "text",
    "tree",
    "verdict",
]
