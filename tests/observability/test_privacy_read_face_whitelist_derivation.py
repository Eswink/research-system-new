"""GOAL-025 EC-03 判据：读面白名单的**契约派生**与差异清单（收 GOAL-024 的残余 `G24-3`）。

**受判命题**：人工清单（`read_face_route_registry`，**只读**）与**从权威契约面派生的读面**
（OpenAPI 快照 ∪ FastAPI 内建框架路由）**逐条一致**；差异**两向**点名，非空即判红。

判据形态（承 MEM-158 / MEM-156 / MEM-160）：

- 派生面有**下界**（`MIN_DERIVED`）：快照读不到 / 变空 ⇒ 判红，不许退化成「空集 ⇒ 无差异」；
- **三条独立路径互相钉住**：①提交的快照 × ②应用**实时** schema（`app.openapi()`）
  ③应用**运行时路由树**（`read_routes(app)`）—— 任一条漂移都会在差异清单里点名；
- **反证两向**：多一条清单项 ⇒ 判红点名；少一条清单项 ⇒ 判红点名；
  **真实应用上新增一条读路由** ⇒ 实时 schema 与快照之间立刻出现差异（点名该路由）；
- 既有判据**只读**：`test_privacy_read_face_canary.py` / `read_face_route_registry.py`
  一字未改（本文件只 import 它的路径集合）。
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.observability.read_face_canary_support import ReadFace, open_read_face, read_routes
from tests.observability.read_face_route_registry import all_rules
from tests.observability.read_face_whitelist_derivation import (
    FRAMEWORK_ROUTES,
    MIN_DERIVED,
    derivation_findings,
    derived_read_face,
    diff_findings,
    framework_findings,
    framework_paths,
    schema_paths,
    snapshot_paths,
)

#: 真实应用上按压用的读路由（只在内存里加，不改树）。
PRESS_ROUTE = "/__derivation-press-probe"


@pytest.fixture(scope="module")
def face() -> Iterator[ReadFace]:
    with open_read_face() as opened:
        yield opened


def registered_paths() -> tuple[str, ...]:
    return tuple(sorted(rule.path for rule in all_rules()))


def test_snapshot_is_present_and_non_empty() -> None:
    """非空取证：权威快照真的读到了，且派生的 GET 面达下界（否则整条判据会空转）。"""
    paths = snapshot_paths()
    assert paths, "OpenAPI 快照读不到 ⇒ 派生面为空，判据会退化成空真"
    assert len(paths) >= MIN_DERIVED, f"快照里的 GET 只有 {len(paths)} 条 < 下界 {MIN_DERIVED}"


def test_derived_read_face_matches_the_manual_registry() -> None:
    """主判据：派生面与人工清单逐条一致；差异（两向）直接进失败消息。"""
    findings = derivation_findings(derived_read_face(), registered_paths())
    assert not findings, f"读面白名单与契约派生面不一致:{findings}"


def test_framework_routes_are_registered_with_reasons() -> None:
    """框架内建路由（快照不含的那一半）逐条显式登记、理由非空，且都在人工清单里。"""
    assert not framework_findings(), framework_findings()
    registered = set(registered_paths())
    missing = [path for path in framework_paths() if path not in registered]
    assert not missing, f"这些框架路由没有进人工清单:{missing}"
    assert len(FRAMEWORK_ROUTES) == 4, [route.path for route in FRAMEWORK_ROUTES]


def test_live_app_schema_agrees_with_the_committed_snapshot(face: ReadFace) -> None:
    """实时 schema 与提交的**快照**一致 ⇒ 「快照是权威面」这句话本身就是被钉住的。"""
    live = schema_paths(face.app.openapi())
    assert live, "实时 schema 里没有 GET ⇒ 该面没被真的取到"
    findings = diff_findings(snapshot_paths(), live)
    assert not findings, f"实时 schema 与提交的快照不一致（快照可能过期）:{findings}"


def test_live_runtime_route_tree_equals_the_derived_read_face(face: ReadFace) -> None:
    """运行时路由树 == 派生面 ⇒ 三条路径（快照 / schema / 路由树）互相钉住。"""
    findings = diff_findings(derived_read_face(), read_routes(face.app))
    assert not findings, f"运行时读面与派生面不一致:{findings}"


def test_an_extra_registry_entry_is_red() -> None:
    """反证：清单里多一条 ⇒ 判红并点名。"""
    findings = diff_findings(derived_read_face(), [*registered_paths(), "/__extra"])
    assert any("清单有而派生面没有:/__extra" in item for item in findings), findings


def test_a_missing_registry_entry_is_red() -> None:
    """反证：清单里少一条 ⇒ 判红并点名（这条正是「新增读路由必须进清单」的机器保证）。"""
    without_health = [path for path in registered_paths() if path != "/health"]
    findings = diff_findings(derived_read_face(), without_health)
    assert any("派生面有而清单没有:/health" in item for item in findings), findings


def test_an_unreadable_snapshot_is_red(tmp_path: Path) -> None:
    """反证：快照读不到 ⇒ 派生面退化并被下界判红（不是「无差异 ⇒ 通过」）。"""
    assert snapshot_paths(tmp_path) == (), "空目录不该派生出任何路径"
    findings = derivation_findings(snapshot_paths(tmp_path), registered_paths())
    assert any("派生面低于下界" in item for item in findings), findings


def test_a_new_read_route_on_the_real_app_is_a_derivation_gap(face: ReadFace) -> None:
    """按压（真实应用）：新增一条读路由 ⇒ 实时读面与提交的快照立刻出现差异并点名。"""

    async def press_probe() -> dict[str, str]:
        return {"status": "ok"}

    face.app.get(PRESS_ROUTE)(press_probe)
    face.app.openapi_schema = None  # 让 FastAPI 重新生成 schema（否则读的是缓存）
    live = schema_paths(face.app.openapi())
    assert PRESS_ROUTE in live, f"按压路由没有进实时 schema:{PRESS_ROUTE}"
    findings = diff_findings(live, snapshot_paths())
    assert any(f"派生面有而清单没有:{PRESS_ROUTE}" in item for item in findings), findings


def test_derivation_is_deterministic() -> None:
    """可复跑：同一棵树上重复派生结果逐条相同（差异清单因此可复核）。"""
    assert derived_read_face() == derived_read_face()
