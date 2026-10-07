"""GOAL-20261007-032 EC-02：relay 的**启用面**取证（离线；`R26-5` 的追认之一）。

判据 ④（GOAL-032 EC-02(c)(4)）：**未启用的组合根如实登记**，且启用面与禁用面的**真值
路径**都被机械钉住（不是散文）：

1. **PG 组合根默认启用**：`services/api/pg_composition.py` 的 `build_postgres_apideps`
   在返回前设 `deps.outbox_relay_enabled = True`（AST 级断言：恰好一处 `True` 字面量）；
2. **启用面不扩散**：除 PG 组合根外，**产品根**（`packages` / `services` / `adapters` /
   `apps` / `tools`）里没有第二处把它设为 `True`；
3. **默认是假**：`ApiDeps.outbox_relay_enabled` 的 dataclass 默认是 `False`，且组合根显式
   写出该默认（`outbox_relay_enabled: bool = False`）；
4. **门控真的生效（行为臂两向）**：未启用 ⇒ `_start_outbox_scheduler` 返回 `None`；
   **翻成真 ⇒ 门控穿过**（构造出调度器，本判据不 `start()` 线程）——
   没有第二臂的话，「恒 None 的假实现」也能让前半条判绿；
5. **单一读取点**：`app.py` 里该字段名字面量**恰好一处**（不散落第二个判断）。

**射程**：本文件离线（读源码 + 构造装配），不起守护线程、不连 PG；线程级行为由
`tests/postgres/test_outbox_relay_forensics.py::test_the_scheduler_wraps_the_same_relay_pass`
覆盖（真 PG、真 pass）。`/ops/schedules` 读面 `executor_attached=False` 的**行为**判据在
`tests/api/test_ops_schedules_api.py`（既有；本文件不重复它的断言）。
"""

from __future__ import annotations

import ast
from pathlib import Path

from services.api.composition import ApiDeps

_ROOT = Path(__file__).resolve().parents[3]
_PG_COMPOSITION = _ROOT / "services" / "api" / "pg_composition.py"
_COMPOSITION = _ROOT / "services" / "api" / "composition.py"
_APP = _ROOT / "services" / "api" / "app.py"

#: 启用面的**唯一**真值来源（其余产品文件不得把该字段设为真）。
_ENABLEMENT_FILE = "services/api/pg_composition.py"

#: 产品扫描面（不含 scratch / .venv 等非产品目录）。
_PRODUCT_ROOTS = ("packages", "services", "adapters", "apps", "tools")


def _true_assignments(path: Path) -> list[ast.Attribute]:
    """文件里所有 `*.outbox_relay_enabled = True` 的赋值目标（AST；非 Python 残留跳过）。"""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return []
    hits: list[ast.Attribute] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        target = node.targets[0] if node.targets else None
        if (
            isinstance(target, ast.Attribute)
            and target.attr == "outbox_relay_enabled"
            and isinstance(node.value, ast.Constant)
            and node.value.value is True
        ):
            hits.append(target)
    return hits


def test_the_postgres_root_enables_the_relay_with_a_true_literal() -> None:
    """**判据 ④-1**：生产 PG 组合根默认启用（恰好一处 `True` 赋值，AST 级）。"""
    hits = _true_assignments(_PG_COMPOSITION)
    assert len(hits) == 1, (
        f"{_ENABLEMENT_FILE} 必须**恰好**有一处把 outbox_relay_enabled 设为 True"
        f"（实测 {len(hits)} 处）"
    )


def test_no_other_product_file_enables_the_relay() -> None:
    """**判据 ④-2**：启用面不扩散（产品根里除 PG 组合根外零处 `True`）。"""
    offenders: list[str] = []
    for root in _PRODUCT_ROOTS:
        for path in sorted((_ROOT / root).rglob("*.py")):
            if "__pycache__" in path.parts or path == _PG_COMPOSITION:
                continue
            if _true_assignments(path):
                offenders.append(path.relative_to(_ROOT).as_posix())
    assert offenders == [], f"启用面不得扩散（这些文件也把它设为 True：{offenders}）"


def test_the_api_deps_default_is_disabled() -> None:
    """**判据 ④-3**：`ApiDeps` 的默认是 `False`，且组合根**显式**写出它。"""
    assert ApiDeps.__dataclass_fields__["outbox_relay_enabled"].default is False, (
        "ApiDeps.outbox_relay_enabled 的默认必须是 False（未启用组合根不得被默认打开）"
    )
    assert "outbox_relay_enabled: bool = False" in _COMPOSITION.read_text(encoding="utf-8"), (
        "组合根的默认必须是**显式**写出的 False（不是靠省略字段的隐含行为）"
    )


def test_the_gate_returns_none_when_disabled_and_passes_when_enabled() -> None:
    """**判据 ④-4（行为臂两向）**：假 ⇒ `None`；**真 ⇒ 穿过门控**（构造出调度器）。

    第二臂不可省：没有它，「恒返回 None」的假实现也能让前半条判绿。
    """
    from services.api.app import _start_outbox_scheduler
    from tests.api.base_fixtures import build_base_deps

    deps = build_base_deps()
    assert deps.outbox_relay_enabled is False, "基础装配（未启用组合根）必须是假"
    assert _start_outbox_scheduler(deps) is None, "未启用 ⇒ 不得起守护线程"

    deps.outbox_relay_enabled = True
    try:
        scheduler = _start_outbox_scheduler(deps)
        assert scheduler is not None, "真值必须穿过门控（否则门控是恒 None 的假实现）"
    finally:
        deps.outbox_relay_enabled = False


def test_the_flag_has_a_single_reader_in_app() -> None:
    """**判据 ④-5**：`app.py` 里该字段名字面量恰好一处（不散落第二个判断）。"""
    tree = ast.parse(_APP.read_text(encoding="utf-8"), filename=str(_APP))
    mentions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and node.value == "outbox_relay_enabled"
    ]
    assert len(mentions) == 1, f"app.py 对该标志只应有一处读取（实测 {len(mentions)} 处）"
