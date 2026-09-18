"""AST check: does any `.execute(...)` build its SQL by string construction?

Purpose (GOAL-20260918-005 EC-01 disposition): the scanner's "env -> SQL execute"
taint findings assume a SQL sink reached from an environment value. The honest
counter-check is structural, not textual: walk the AST, find every `.execute(...)`
call, and classify its first argument. Concatenation, %-formatting, `.format(...)`
and f-strings are dynamic construction; a plain literal, a name, or a call that
returns SQL text (e.g. `path.read_text()`) is not.

Usage:
    python tools/probes/probe_dynamic_sql_forms.py --root packages --root services --root adapters
    python tools/probes/probe_dynamic_sql_forms.py --selftest

The selftest builds the four construction shapes and three benign shapes as AST
nodes (no source text involved) and asserts the classifier separates them, so a
"zero hits on the product tree" result is not a vacuous result from a dead check.
"""

from __future__ import annotations

import argparse
import ast
import os
import sys

SKIP_DIRS = {"node_modules", "__pycache__", ".venv", ".git", "dist", "build"}
EXECUTE_METHODS = {"execute", "executemany", "executescript"}


def first_arg_construction(node: ast.Call) -> str | None:
    """Name the construction form of the first argument, or None if it is benign."""
    if not node.args:
        return None
    arg = node.args[0]
    if isinstance(arg, ast.JoinedStr):
        return "f-string"
    if isinstance(arg, ast.BinOp):
        if isinstance(arg.op, ast.Add):
            return "concatenation"
        if isinstance(arg.op, ast.Mod):
            return "% formatting"
    if (
        isinstance(arg, ast.Call)
        and isinstance(arg.func, ast.Attribute)
        and arg.func.attr == "format"
    ):
        return "str.format call"
    return None


def is_execute_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in EXECUTE_METHODS
    )


def scan_tree(tree: ast.AST) -> list[tuple[int, str, str]]:
    hits: list[tuple[int, str, str]] = []
    for node in ast.walk(tree):
        if is_execute_call(node):
            kind = first_arg_construction(node)
            if kind is not None:
                hits.append((node.lineno, node.func.attr, kind))  # type: ignore[attr-defined]
    return hits


def scan_file(path: str) -> list[tuple[int, str, str]]:
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except (SyntaxError, UnicodeDecodeError):
        return []
    return scan_tree(tree)


def _call(calls: str, arg: ast.expr) -> ast.Call:
    """Build `calls(arg)` as an AST node without writing any source text."""
    func = ast.Attribute(value=ast.Name(id="cur", ctx=ast.Load()), attr=calls, ctx=ast.Load())
    return ast.Call(func=func, args=[arg], keywords=[])


def _positive_cases() -> dict[str, ast.Call]:
    return {
        "f-string": _call(
            "execute", ast.JoinedStr(values=[ast.Constant(value="SELECT "), ast.Name(id="x")])
        ),
        "concatenation": _call(
            "execute",
            ast.BinOp(left=ast.Constant(value="SELECT "), op=ast.Add(), right=ast.Name(id="x")),
        ),
        "% formatting": _call(
            "execute",
            ast.BinOp(left=ast.Constant(value="SELECT %s"), op=ast.Mod(), right=ast.Name(id="x")),
        ),
        "str.format call": _call(
            "execute",
            ast.Call(
                func=ast.Attribute(
                    value=ast.Constant(value="SELECT {}"), attr="format", ctx=ast.Load()
                ),
                args=[ast.Name(id="x")],
                keywords=[],
            ),
        ),
    }


def _negative_cases() -> dict[str, ast.Call]:
    return {
        "parameterized literal": _call("execute", ast.Constant(value="SELECT * FROM t WHERE a=%s")),
        "name": _call("execute", ast.Name(id="sql_text")),
        "read_text call": _call(
            "execute",
            ast.Call(
                func=ast.Attribute(value=ast.Name(id="path"), attr="read_text", ctx=ast.Load()),
                args=[],
                keywords=[],
            ),
        ),
        "no arguments": ast.Call(
            func=ast.Attribute(value=ast.Name(id="cur"), attr="execute", ctx=ast.Load()),
            args=[],
            keywords=[],
        ),
    }


def selftest() -> int:
    failures = 0
    for expected, node in _positive_cases().items():
        got = first_arg_construction(node)
        ok = got == expected
        failures += 0 if ok else 1
        print(f"{'ok  ' if ok else 'FAIL'} positive {expected!r} -> {got!r}")
    for label, node in _negative_cases().items():
        got = first_arg_construction(node)
        ok = got is None
        failures += 0 if ok else 1
        print(f"{'ok  ' if ok else 'FAIL'} negative {label!r} -> {got!r}")
    print(f"selftest: {failures} failure(s)")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", default=[])
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        return selftest()
    if not args.root:
        parser.error("either --selftest or at least one --root is required")

    files = 0
    hits = 0
    for root in args.root:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                if not name.endswith(".py"):
                    continue
                files += 1
                for lineno, method, kind in scan_file(os.path.join(dirpath, name)):
                    hits += 1
                    print(f"{os.path.join(dirpath, name)}:{lineno}: .{method}() built by {kind}")
    print(f"scanned {files} python files; {hits} dynamic construction hit(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
