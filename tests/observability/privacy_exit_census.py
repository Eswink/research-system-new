"""GOAL-024 EC-01 支撑面:非 canonical 出口的 AST 普查与分区(机械部分)。

`test_privacy_exit_census.py` 里是**分类清单**(哪条出口受判 / 哪条登记豁免且为什么);
这里只提供机械部分:

- `discover_emitters()`:按**形态谓词**遍历产品根,产出 `(module, kind)` 候选集。
  形态谓词与扫描根都写在源码里 —— 新增一种发射形态必须显式加进来,不会静默漏掉。
- `partition_findings()`:把候选集与清单对账,返回问题清单(空 = 每个候选被**恰好一条**
  显式分类认领)。**没有第三种状态**:未分类 / 重复分类 / 登记陈旧 / 空理由都是问题。

边界(canonical 不算出口):PG 域实体 / SQLite 域表持有的用户任务输入是**业务真相**,
不是泄漏;受判面是**非 canonical 出口**(遥测 wire、应用日志、磁盘制品、读面响应、
失败载荷、进程内投影)。
"""

from __future__ import annotations

import ast
import os
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from pathlib import Path

PRODUCT_ROOTS: tuple[str, ...] = ("apps", "services", "packages", "adapters")
SKIPPED_DIRS: frozenset[str] = frozenset({"__pycache__", "node_modules", ".venv", ".git"})

JUDGED = "judged"
EXEMPT = "exempt"
CLASSIFICATIONS: frozenset[str] = frozenset({JUDGED, EXEMPT})


class EmitterKind(StrEnum):
    """可机械发现的发射形态;每种形态对应一条出口面。"""

    application_log = "application_log"
    stdout = "stdout"
    otlp_span = "otlp_span"
    otlp_metric = "otlp_metric"
    disk_write = "disk_write"
    read_face = "read_face"
    failure_payload = "failure_payload"


@dataclass(frozen=True, slots=True)
class Emitter:
    """一个发射点候选:某模块里出现了某种发射形态。"""

    module: str
    kind: EmitterKind


@dataclass(frozen=True, slots=True)
class ExitSurface:
    """一条非 canonical 出口面。

    `observation`(受判面)说明"本次运行里怎么真实观测到它";`reason`(豁免面)说明豁免理由。
    `producers` 是**显式模块清单** —— 下界由它给出,不由文档给出(承 MEM-160)。
    """

    id: str
    kind: EmitterKind
    classification: str
    observation: str
    reason: str
    producers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExemptProducer:
    """受判形态在**默认路径之外**的生产者:显式登记 + 理由,不是静默放过。"""

    module: str
    kind: EmitterKind
    reason: str


def _is_attr_call(node: ast.AST, names: frozenset[str]) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in names
    )


def _is_named_call(node: ast.AST, names: frozenset[str]) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in names


def _is_logger_lookup(node: ast.AST) -> bool:
    return _is_attr_call(node, frozenset({"getLogger"}))


def _is_stdout_write(node: ast.AST) -> bool:
    return _is_named_call(node, frozenset({"print"}))


def _is_span(node: ast.AST) -> bool:
    if not isinstance(node, ast.With):
        return False
    return any(
        isinstance(item.context_expr, ast.Call)
        and isinstance(item.context_expr.func, ast.Name)
        and item.context_expr.func.id == "operation"
        for item in node.items
    )


def _is_metric(node: ast.AST) -> bool:
    return _is_attr_call(
        node, frozenset({"record_metric", "record_metric_safely"})
    ) or _is_named_call(node, frozenset({"record_metric_safely"}))


def _is_disk_write(node: ast.AST) -> bool:
    return _is_attr_call(node, frozenset({"write_text", "write_bytes"}))


def _is_read_route(node: ast.AST) -> bool:
    if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        return False
    return any(
        isinstance(item, ast.Call)
        and isinstance(item.func, ast.Attribute)
        and item.func.attr in {"get", "head"}
        for item in node.decorator_list
    )


def _is_failure_payload(node: ast.AST) -> bool:
    if not isinstance(node, ast.Raise) or node.exc is None:
        return False
    raised = node.exc
    if not isinstance(raised, ast.Call):
        return False
    if isinstance(raised.func, ast.Name):
        return raised.func.id == "ApiError"
    return isinstance(raised.func, ast.Attribute) and raised.func.attr == "ApiError"


SHAPES: dict[EmitterKind, Callable[[ast.AST], bool]] = {
    EmitterKind.application_log: _is_logger_lookup,
    EmitterKind.stdout: _is_stdout_write,
    EmitterKind.otlp_span: _is_span,
    EmitterKind.otlp_metric: _is_metric,
    EmitterKind.disk_write: _is_disk_write,
    EmitterKind.read_face: _is_read_route,
    EmitterKind.failure_payload: _is_failure_payload,
}


def _python_files(root: Path, roots: tuple[str, ...]) -> Iterator[Path]:
    for base in roots:
        base_path = root / base
        if not base_path.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base_path, followlinks=False):
            dirnames[:] = sorted(name for name in dirnames if name not in SKIPPED_DIRS)
            for filename in sorted(filenames):
                if filename.endswith(".py"):
                    yield Path(dirpath) / filename


def classify_module(tree: ast.AST) -> set[EmitterKind]:
    """该模块源码里出现的全部发射形态。"""
    return {
        kind for node in ast.walk(tree) for kind, predicate in SHAPES.items() if predicate(node)
    }


@lru_cache(maxsize=8)
def discover_emitters(root: Path, roots: tuple[str, ...] = PRODUCT_ROOTS) -> tuple[Emitter, ...]:
    """走一遍产品根,产出排序稳定的 `(module, kind)` 候选集。"""
    found: list[Emitter] = []
    for path in _python_files(root, roots):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        relative = path.relative_to(root).as_posix()
        found.extend(Emitter(module=relative, kind=kind) for kind in classify_module(tree))
    return tuple(sorted(found, key=lambda emitter: (emitter.module, emitter.kind)))


def _claimants(
    emitter: Emitter,
    surfaces: tuple[ExitSurface, ...],
    exempt: tuple[ExemptProducer, ...],
) -> list[str]:
    claims = [
        surface.id
        for surface in surfaces
        if surface.kind == emitter.kind and emitter.module in surface.producers
    ]
    claims.extend(
        f"exempt:{item.module}"
        for item in exempt
        if item.module == emitter.module and item.kind == emitter.kind
    )
    return claims


def partition_findings(
    emitters: tuple[Emitter, ...],
    surfaces: tuple[ExitSurface, ...],
    exempt: tuple[ExemptProducer, ...],
) -> tuple[str, ...]:
    """候选集对账:返回问题清单(空 = 每个候选被恰好一条显式分类认领,且无陈旧登记)。"""
    problems: list[str] = []
    for emitter in emitters:
        claims = _claimants(emitter, surfaces, exempt)
        if not claims:
            problems.append(f"未分类的非 canonical 出口:{emitter.module} [{emitter.kind}]")
        elif len(claims) > 1:
            problems.append(
                f"重复分类的非 canonical 出口:{emitter.module} [{emitter.kind}] -> {sorted(claims)}"
            )
    known = {(emitter.module, emitter.kind) for emitter in emitters}
    for surface in surfaces:
        for module in surface.producers:
            if (module, surface.kind) not in known:
                problems.append(
                    f"登记陈旧:{surface.id} 声称 {module} 会发射 [{surface.kind}],实际没有"
                )
    for item in exempt:
        if (item.module, item.kind) not in known:
            problems.append(f"豁免登记陈旧:{item.module} 已不再发射 [{item.kind}]")
    return tuple(problems)


def surface_findings(
    surfaces: tuple[ExitSurface, ...], exempt: tuple[ExemptProducer, ...]
) -> tuple[str, ...]:
    """清单自身的完整性:分类取值合法、受判面有观测方式、豁免面有理由、受判面生产者非空。"""
    problems: list[str] = []
    for surface in surfaces:
        if surface.classification not in CLASSIFICATIONS:
            problems.append(f"{surface.id}: 非法分类 {surface.classification!r}")
        if surface.classification == JUDGED:
            if not surface.producers:
                problems.append(f"{surface.id}: 受判出口的生产者清单为空(下界会退化成空真)")
            if not surface.observation.strip():
                problems.append(f"{surface.id}: 受判出口缺少观测方式")
        if surface.classification == EXEMPT and not surface.reason.strip():
            problems.append(f"{surface.id}: 豁免出口缺少理由")
    for item in exempt:
        if not item.reason.strip():
            problems.append(f"豁免生产者 {item.module} [{item.kind}]: 缺少理由")
    return tuple(problems)


def lower_bound_findings(judged_ids: frozenset[str], required: tuple[str, ...]) -> tuple[str, ...]:
    """必备出口清单的**下界**断言(承 MEM-160:并集射程会掩盖清单收缩)。

    下界来自判据源码里的 `required`,不由文档点名给出 —— 文档只是并集的另一半。
    """
    missing = sorted(item for item in required if item not in judged_ids)
    return (f"必备受判出口缺失:{missing}",) if missing else ()
