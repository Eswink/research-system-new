"""GOAL-025 EC-03 派生面：读面白名单的**权威契约面** = OpenAPI 快照 + FastAPI 内建框架路由。

**为什么这个面是权威的**（写在源码里，不靠散文）：

- `docs/api/openapi.m13.json` 由 `tests/contracts/test_openapi_snapshot.py` **重新生成**并与
  提交前的字节**逐字比对** ⇒ 它不会静默漂移（DTO / 路由一变，那条门先红）；
- 它同时是**前端类型的生成源**（`tools/gen_openapi.py` → web 类型）⇒ 它是「应用对外声明的
  读面」的单一事实源，比人手写的 `docs/api/CONTROL_PLANE_API.md` 更适合当权威面
  （后者是文档，会漂移）。
- `FRAMEWORK_ROUTES` 是**差集那一半**：FastAPI 内建文档路由**不在** OpenAPI schema 里
  （`/docs` / `/redoc` / `/openapi.json` / `/docs/oauth2-redirect`），必须逐条显式登记理由；
  它们不登记就变成「派生面与人工清单永远差 4 条」的噪声。

**受判命题**：`derive(snapshot) ∪ FRAMEWORK_ROUTES` **等于** 人工清单
（`read_face_route_registry`）的全部路径 —— 差异**两向**逐条点名；差异非空即判红。
GOAL-024 的 `G24-3` 是「白名单是人工判定 + 机械自审，不是从契约派生」，本模块把
**派生**这一半补上；**人工清单本身只读**（不改既有判据）。
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[2]
#: 权威快照（相对仓库根）。
SNAPSHOT = Path("docs") / "api" / "openapi.m13.json"

#: 派生面**下界**（快照为空 / 读不到 ⇒ 判红，不许静默退化成「无差异」）。
MIN_DERIVED = 40


@dataclass(frozen=True, slots=True)
class FrameworkRoute:
    """OpenAPI schema **不含**的读面路由（框架内建），逐条带理由。"""

    path: str
    note: str


#: FastAPI 内建文档路由：它们出现在应用路由表上，但**不**进 OpenAPI schema。
FRAMEWORK_ROUTES: tuple[FrameworkRoute, ...] = (
    FrameworkRoute("/docs", "FastAPI 内建 Swagger UI（框架资产，不属于应用 schema）"),
    FrameworkRoute("/docs/oauth2-redirect", "FastAPI 内建 OAuth2 回调页（框架资产）"),
    FrameworkRoute("/openapi.json", "FastAPI 内建 schema 端点（schema 本身，不进 schema）"),
    FrameworkRoute("/redoc", "FastAPI 内建 ReDoc（框架资产）"),
)


def snapshot_paths(root: Path = REPO_ROOT) -> tuple[str, ...]:
    """从**提交的** OpenAPI 快照派生 GET 路径（读不到 / 结构不符 ⇒ 空元组，由判据判红）。"""
    path = root / SNAPSHOT
    if not path.is_file():
        return ()
    try:
        schema = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    except (ValueError, OSError):
        return ()
    paths = schema.get("paths")
    if not isinstance(paths, Mapping):
        return ()
    return tuple(
        sorted(
            str(item)
            for item, operations in paths.items()
            if isinstance(operations, Mapping) and "get" in operations
        )
    )


def schema_paths(schema: Mapping[str, Any]) -> tuple[str, ...]:
    """从**任意** OpenAPI schema（如应用实时 `app.openapi()`）派生 GET 路径。"""
    paths = schema.get("paths")
    if not isinstance(paths, Mapping):
        return ()
    return tuple(
        sorted(
            str(item)
            for item, operations in paths.items()
            if isinstance(operations, Mapping) and "get" in operations
        )
    )


def framework_paths() -> tuple[str, ...]:
    return tuple(route.path for route in FRAMEWORK_ROUTES)


def derived_read_face(root: Path = REPO_ROOT) -> tuple[str, ...]:
    """派生的读面 = 快照 GET 路径 ∪ 框架内建路由（去重、排序）。"""
    return tuple(sorted(set(snapshot_paths(root)) | set(framework_paths())))


def diff_findings(derived: Iterable[str], registered: Iterable[str]) -> list[str]:
    """两向差异（逐条点名）：`派生 − 登记` 与 `登记 − 派生`。"""
    left = set(derived)
    right = set(registered)
    findings = [f"派生面有而清单没有:{path}" for path in sorted(left - right)]
    findings.extend(f"清单有而派生面没有:{path}" for path in sorted(right - left))
    return findings


def derivation_findings(
    derived: Iterable[str], registered: Iterable[str], *, floor: int = MIN_DERIVED
) -> list[str]:
    """派生面自审 + 两向差异（判据的唯一入口；失败消息里就是差异清单本身）。"""
    derived_tuple = tuple(derived)
    findings: list[str] = []
    if len(derived_tuple) < floor:
        findings.append(f"派生面低于下界:{len(derived_tuple)} < {floor} ⇒ 快照可能读不到")
    findings.extend(diff_findings(derived_tuple, registered))
    return findings


def framework_findings(routes: Iterable[FrameworkRoute] = FRAMEWORK_ROUTES) -> list[str]:
    """框架登记自审：理由非空、不重复。"""
    findings: list[str] = []
    seen: set[str] = set()
    for route in routes:
        if not route.note.strip():
            findings.append(f"框架路由没有理由:{route.path}")
        if route.path in seen:
            findings.append(f"框架路由重复登记:{route.path}")
        seen.add(route.path)
    return findings
