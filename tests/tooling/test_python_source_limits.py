from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PRODUCT_ROOTS = ("apps", "services", "packages", "adapters", "tests")
FUNCTION_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)


def python_sources() -> Iterator[Path]:
    for directory in PRODUCT_ROOTS:
        root = ROOT / directory
        if root.is_dir():
            yield from root.rglob("*.py")


def function_spans(path: Path) -> Iterator[tuple[str, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, FUNCTION_NODES) and node.end_lineno is not None:
            yield node.name, node.end_lineno - node.lineno + 1


@pytest.mark.parametrize(
    "path", tuple(python_sources()), ids=lambda path: str(path.relative_to(ROOT))
)
def test_python_source_size_limits(path: Path) -> None:
    line_count = len(path.read_text(encoding="utf-8").splitlines())
    assert line_count <= 300, f"{path.relative_to(ROOT)} 超过 300 行"
    oversized = [(name, lines) for name, lines in function_spans(path) if lines > 50]
    assert not oversized, f"{path.relative_to(ROOT)} 存在超过 50 行的函数: {oversized}"
