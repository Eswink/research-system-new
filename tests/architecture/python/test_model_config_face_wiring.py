"""配置面装配判据（GOAL-20260920-008 EC-02 / PLAN-20260920-115 AC-03）。

AC-03 要求证明「两个组合根共用同一配置面」，而不是只测 SQLite 一侧。这里用 AST
读**装配事实**（不是跑一遍装配），因为它判的正是「谁来构造、谁被传进去」：

1. `services/api/composition.assemble` 里 `SqliteModelStore` **只被构造一次**，
   同一个名字被传给 `_assemble_sqlite` 与 `_assemble_postgres` 两个分支；
2. `services/api/pg_composition.build_postgres_assembly` **不构造**任何配置面实现，
   它从 `config` 取现成实例并原样交给 `PostgresAssembly`；
3. `adapters/postgres/migrations/*.sql` **不存在**名为 `models` 的表——一旦有人新建
   模型配置表，第 1/2 条的「同一份配置」假设就被破坏（那属于 Canonical State 边界，
   需 escalation），本用例会在那时变红。

反证：把任一条破坏（分支各建一个实例 / PG 根自建 / 迁移里建 `models` 表）即红。
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
COMPOSITION = ROOT / "services" / "api" / "composition.py"
PG_COMPOSITION = ROOT / "services" / "api" / "pg_composition.py"
MIGRATIONS = ROOT / "adapters" / "postgres" / "migrations"

_CONFIG_FACE_FACTORY = "SqliteModelStore"
_BRANCHES = ("_assemble_sqlite", "_assemble_postgres")
_MIGRATION_TABLE = re.compile(
    r"create\s+table\s+(?:if\s+not\s+exists\s+)?[\"']?models[\"']?\s*\(",
    re.IGNORECASE,
)


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"function not found: {name}")


def _called_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        item for item in ast.walk(node) if isinstance(item, ast.Call) and _called_name(item) == name
    ]


def _assigned_name(function: ast.FunctionDef, value: ast.AST) -> str:
    for item in ast.walk(function):
        if isinstance(item, ast.Assign) and item.value is value:
            target = item.targets[0]
            assert isinstance(target, ast.Name), "配置面实例必须赋给一个名字才能被传下去"
            return target.id
    raise AssertionError("配置面构造结果没有被赋给任何名字")


def test_assemble_builds_one_config_face_and_feeds_both_branches() -> None:
    assemble = _function(_parse(COMPOSITION), "assemble")
    constructions = _calls(assemble, _CONFIG_FACE_FACTORY)
    assert len(constructions) == 1, (
        f"assemble 构造了 {len(constructions)} 个 {_CONFIG_FACE_FACTORY}；"
        "两个分支各建一个会让 API 注册的模型对运行时不可见"
    )
    store_name = _assigned_name(assemble, constructions[0])
    for branch in _BRANCHES:
        branch_calls = _calls(assemble, branch)
        assert len(branch_calls) == 1, f"assemble 应恰好调用一次 {branch}"
        passed = {arg.id for arg in branch_calls[0].args if isinstance(arg, ast.Name)}
        assert store_name in passed, f"{branch} 没有收到同一个配置面实例（{store_name}）"


def test_pg_root_takes_the_config_face_from_config() -> None:
    tree = _parse(PG_COMPOSITION)
    build = _function(tree, "build_postgres_assembly")
    assert _calls(build, _CONFIG_FACE_FACTORY) == [], (
        "PG 组合根不得自建配置面实现——模型配置面只有一份（SQLite JSON blob 行）"
    )
    from_config: set[str] = set()
    for item in ast.walk(build):
        if (
            isinstance(item, ast.Assign)
            and isinstance(item.value, ast.Attribute)
            and item.value.attr == "model_store"
        ):
            from_config.update(target.id for target in item.targets if isinstance(target, ast.Name))
    assert from_config, "PG 组合根应从 config 取配置面实例"
    assemblies = _calls(build, "PostgresAssembly")
    assert len(assemblies) == 1
    passed = {
        keyword.value.id
        for keyword in assemblies[0].keywords
        if keyword.arg == "model_store" and isinstance(keyword.value, ast.Name)
    }
    assert passed & from_config, "PostgresAssembly 收到的不是 config 里那一个配置面实例"


def test_no_pg_migration_defines_a_model_config_table() -> None:
    offenders = [
        path.name
        for path in sorted(MIGRATIONS.glob("*.sql"))
        if _MIGRATION_TABLE.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == [], (
        "PG 迁移里出现了 models 表：模型配置面是 SQLite 配置面，"
        "把它搬进 PG canonical state 需要 escalation 与 ADR；命中文件：" + ", ".join(offenders)
    )
