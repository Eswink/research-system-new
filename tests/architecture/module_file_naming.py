from __future__ import annotations

import ast
import os
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

PRODUCT_ROOTS = ("apps", "services", "packages", "adapters", "tests")
IGNORED_DIRECTORIES = frozenset({
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "htmlcov",
    "node_modules",
})
LEGACY_PATH_EXCEPTIONS = frozenset({
    "adapters/execution/容器归属v1.py",
    "adapters/postgres/migrations/010_GPU显存计量宽度v1.sql",
    "adapters/postgres/migrations/011_GPU时间精度v1.sql",
    "adapters/postgres/migrations/012_执行用量重放v1.sql",
    "packages/application/m12_reference/恢复生命周期v1.py",
    "packages/application/m12_reference/证据重放v1.py",
    "services/worker/计量观测v1.py",
    "tests/adapters/execution/test_容器归属v1.py",
    "tests/adapters/execution/test_重放计量v1.py",
    "tests/adapters/test_重连事务边界v1.py",
    "tests/postgres/test_GPU显存宽度v1.py",
    "tests/tooling/test_个人生产续审v2.py",
    "tests/tooling/test_恢复生命周期v1.py",
    "tests/worker/test_计量观测v1.py",
    # 高保真控制台重建（PLAN-20260908-033~036）引入的原型命名遗留；
    # 重命名牵动 import 面与快照，登记为 baseline（新文件仍受规则约束）。
    "apps/web/src/components/TableRows.tsx",
    "apps/web/src/features/example-console/fieldContext.ts",
    "apps/web/src/features/example-console/reference/BudgetMetricCard.tsx",
    "apps/web/src/features/example-console/reference/kv.tsx",
    "apps/web/src/features/example-console/reference/evaluation-section/EvaluationDetails.tsx",
    "apps/web/src/features/inspection/Views.tsx",
    "apps/web/src/features/team/TeamAgentCards.tsx",
    "apps/web/tests/e2e/apiFixtures.ts",
    "apps/web/tests/e2e/apiHarness.ts",
    "apps/web/tests/helpers/registerStyles.mjs",
    "apps/web/tests/helpers/styleModuleLoader.mjs",
    "apps/web/tests/unit/consoleFixtures.ts",
})

_SNAKE_CASE_RE = re.compile(r"^_?[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_PYTHON_DIRECTORY_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_LOWER_DIRECTORY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_TYPESCRIPT_SOURCE_RE = re.compile(r"^(?:[a-z][A-Za-z0-9]*|[A-Z][A-Za-z0-9]*)$")
_KEBAB_CASE_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_MIGRATION_RE = re.compile(r"^[0-9]{3}_[a-z][a-z0-9]*(?:_[a-z0-9]+)*\.sql$")
_VERSION_SUFFIX_RE = re.compile(r"(?:^|[-_])v[0-9]+$", re.IGNORECASE)
_LIFECYCLE_LABEL_RE = re.compile(
    r"(?:^|[-_.])(copy|final|new|old|temp|tmp)(?:[-_.]|$)", re.IGNORECASE
)
_EXPORT_RE = re.compile(
    r"\bexport\s+(?:default\s+)?(?:async\s+)?(?:class|const|function)\s+"
    r"([A-Za-z][A-Za-z0-9]*)"
)
_PYTHON_SPECIAL_FILES = frozenset({"__init__.py", "__main__.py", "conftest.py"})


@dataclass(frozen=True, slots=True)
class NamingViolation:
    path: str
    reason: str


def _common_reasons(relative: PurePosixPath) -> tuple[str, ...]:
    reasons: list[str] = []
    for part in relative.parts:
        if not part.isascii():
            reasons.append("path segments must use ASCII")
            break
    if any(any(character.isspace() for character in part) for part in relative.parts):
        reasons.append("path segments must not contain whitespace")
    return tuple(reasons)


def _directory_reasons(relative: PurePosixPath, *, python_style: bool) -> tuple[str, ...]:
    pattern = _PYTHON_DIRECTORY_RE if python_style else _LOWER_DIRECTORY_RE
    label = (
        "Python package directory must use snake_case"
        if python_style
        else "source directory must use lowercase kebab-case"
    )
    return tuple(label for part in relative.parts[1:-1] if pattern.fullmatch(part) is None)


def _logical_stem(name: str) -> str:
    for marker in (".test.", ".spec.", ".config."):
        if marker in name:
            return name.split(marker, 1)[0]
    return name.rsplit(".", 1)[0]


def _semantic_label_reasons(name: str) -> tuple[str, ...]:
    stem = _logical_stem(name)
    reasons: list[str] = []
    if _VERSION_SUFFIX_RE.search(stem):
        reasons.append("filename must not use a trailing version suffix such as v2")
    if _LIFECYCLE_LABEL_RE.search(stem):
        reasons.append("filename must not use a lifecycle label such as final, new, or tmp")
    return tuple(reasons)


def _python_reasons(relative: PurePosixPath) -> tuple[str, ...]:
    if relative.name in _PYTHON_SPECIAL_FILES:
        return ()
    suffix = relative.suffix.lower()
    stem = relative.name[: -len(suffix)]
    if _SNAKE_CASE_RE.fullmatch(stem) is None:
        return ("Python module filename must use snake_case",)
    return ()


def _is_test_or_fixture(relative: PurePosixPath) -> bool:
    return relative.parts[0] == "tests" or "tests" in relative.parts or "fixtures" in relative.parts


def _typescript_reasons(relative: PurePosixPath) -> tuple[str, ...]:
    name = relative.name
    for marker in (".test.", ".spec."):
        if marker in name:
            subject = name.split(marker, 1)[0]
            if _KEBAB_CASE_RE.fullmatch(subject) is None:
                return ("TypeScript test or fixture filename must use kebab-case",)
            return ()
    suffix = relative.suffix.lower()
    stem = name[: -len(suffix)]
    if stem.endswith(".d"):
        stem = stem[:-2]
    if stem.endswith(".config"):
        stem = stem[:-7]
    if _is_test_or_fixture(relative):
        if _KEBAB_CASE_RE.fullmatch(stem) is None:
            return ("TypeScript test or fixture filename must use kebab-case",)
        return ()
    if _TYPESCRIPT_SOURCE_RE.fullmatch(stem) is None:
        return ("TypeScript source filename must use lowerCamelCase or PascalCase",)
    if stem.startswith("use") and len(stem) > 3 and not stem[3].isupper():
        return ("TypeScript hook filename must use usePascalCase",)
    return ()


def _sql_reasons(relative: PurePosixPath) -> tuple[str, ...]:
    if relative.parent.as_posix() == "adapters/postgres/migrations":
        if _MIGRATION_RE.fullmatch(relative.name) is None:
            return ("SQL migration filename must use NNN_snake_case.sql",)
        return ()
    if _SNAKE_CASE_RE.fullmatch(relative.stem) is None:
        return ("SQL filename must use snake_case",)
    return ()


def classify_path(relative: PurePosixPath) -> tuple[str, ...]:
    if not relative.parts or relative.parts[0] not in PRODUCT_ROOTS:
        return ()
    reasons = [*_common_reasons(relative), *_semantic_label_reasons(relative.name)]
    suffix = relative.suffix.lower()
    if suffix in {".py", ".pyi"}:
        reasons.extend(_directory_reasons(relative, python_style=True))
        reasons.extend(_python_reasons(relative))
    elif suffix == ".sql":
        reasons.extend(_directory_reasons(relative, python_style=True))
        reasons.extend(_sql_reasons(relative))
    elif suffix in {".cjs", ".js", ".jsx", ".mjs", ".ts", ".tsx"}:
        reasons.extend(_directory_reasons(relative, python_style=False))
        reasons.extend(_typescript_reasons(relative))
    return tuple(dict.fromkeys(reasons))


def _iter_product_files(root: Path) -> Iterator[Path]:
    for product_root in PRODUCT_ROOTS:
        start = root / product_root
        if not start.is_dir():
            continue
        for directory, child_directories, filenames in os.walk(start, topdown=True):
            child_directories[:] = sorted(
                name for name in child_directories if name not in IGNORED_DIRECTORIES
            )
            current = Path(directory)
            for filename in sorted(filenames):
                yield current / filename


def _python_test_contract_reasons(path: Path, relative: PurePosixPath) -> tuple[str, ...]:
    if relative.suffix.lower() != ".py" or relative.parts[0] != "tests":
        return ()
    if relative.name.startswith("test_") or relative.name in _PYTHON_SPECIAL_FILES:
        return ()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        is_test_function = isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)) and (
            node.name.startswith("test_")
        )
        is_test_class = isinstance(node, ast.ClassDef) and node.name.startswith("Test")
        if is_test_function or is_test_class:
            return ("Python test module filename must use test_<subject>.py",)
    return ()


def _source_contract_reasons(path: Path, relative: PurePosixPath) -> tuple[str, ...]:
    python_reasons = _python_test_contract_reasons(path, relative)
    if python_reasons:
        return python_reasons
    if relative.suffix.lower() not in {".ts", ".tsx"} or "src" not in relative.parts:
        return ()
    text = path.read_text(encoding="utf-8")
    exports = tuple(_EXPORT_RE.findall(text))
    stem = relative.stem
    components = tuple(name for name in exports if name[:1].isupper())
    if relative.suffix.lower() == ".tsx" and len(components) == 1:
        if components[0] != stem:
            return ("PascalCase component filename must match its only component export",)
    hooks = tuple(name for name in exports if name.startswith("use"))
    if len(hooks) == 1 and hooks[0] != stem:
        return ("hook export must match its usePascalCase filename",)
    return ()


def collect_violations(root: Path) -> tuple[NamingViolation, ...]:
    violations: list[NamingViolation] = []
    for path in _iter_product_files(root):
        relative = PurePosixPath(path.relative_to(root).as_posix())
        rendered = relative.as_posix()
        if rendered in LEGACY_PATH_EXCEPTIONS:
            continue
        reasons = (*classify_path(relative), *_source_contract_reasons(path, relative))
        violations.extend(NamingViolation(rendered, reason) for reason in reasons)
    return tuple(violations)


def stale_legacy_exceptions(root: Path) -> tuple[str, ...]:
    stale: list[str] = []
    for rendered in sorted(LEGACY_PATH_EXCEPTIONS):
        relative = PurePosixPath(rendered)
        path = root.joinpath(*relative.parts)
        if not path.is_file():
            stale.append(rendered)
            continue
        if not classify_path(relative) and not _source_contract_reasons(path, relative):
            stale.append(rendered)
    return tuple(stale)
