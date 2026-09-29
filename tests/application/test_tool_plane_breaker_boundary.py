"""GOAL-026 EC-03（AC-1 的**登记面**）：工具面断路器的边界是**机械事实**。

建档勘察实测（GOAL-026 事实层结论第 9 条）：

- `packages/application/tool_plane/health.py` 只 import `initial_state` / `apply_success` /
  `apply_failure`（**没有** `apply_tick`）⇒ 一旦 OPEN **永不半开**；
- 产品根下**零调用方**（只有包内 `__init__` 再导出与测试）；
- `monitor_config()` **无参**且恒返回默认配置（阈值不可注入）。

接通它 = **新能力**（需用户拍板，见 GOAL-026 的 `R26-2`）⇒ 本轮**只登记**，
把边界钉成**结构化 / 枚举化**的机械事实，免得「代码里有」被读成「已成立」。
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from packages.application.tool_plane.health import (
    ToolHealthSnapshot,
    is_circuit_open,
    record_probe,
    record_probe_failure,
)
from packages.domain.circuit_breaker import CircuitBreakerConfig, CircuitBreakerTransitionError
from packages.domain.enums import EndpointHealth
from packages.domain.tools import ToolHealthReport

REPO_ROOT = Path(__file__).resolve().parents[2]

#: 产品根（**不含** `tests/`）：工具面断路器的接线必须出现在这些根的某处才算「已接通」。
PRODUCT_ROOTS: tuple[str, ...] = ("packages", "adapters", "services", "apps")

#: 该模块对外符号；任何**包外**引用都意味着出现了新的产品装配点。
_SYMBOLS: tuple[str, ...] = (
    "ToolHealthSnapshot",
    "record_probe_failure",
    "health_for_resolver",
    "is_circuit_open",
)

#: 合法引用面：包自己的实现 + 包 `__init__` 的再导出（实测下界，见断言）。
_IN_PACKAGE = "packages/application/tool_plane/"

#: 扫描面下界（实测 `packages`+`adapters`+`services` = 529 个 `.py`）。
_MIN_SCANNED = 400


def _iter_product_sources() -> list[Path]:
    found: list[Path] = []
    for root in PRODUCT_ROOTS:
        base = REPO_ROOT / root
        if not base.is_dir():
            continue
        for dirpath, _dirnames, filenames in os.walk(base, followlinks=False):
            found.extend(Path(dirpath) / name for name in filenames if name.endswith(".py"))
    return found


def _open_after_threshold_failures(threshold: int) -> ToolHealthSnapshot:
    snapshot = ToolHealthSnapshot()
    config = CircuitBreakerConfig(failure_threshold=threshold)
    for _ in range(threshold):
        snapshot = record_probe_failure(snapshot, "provider-a")
    assert config  # 阈值口径来自 Domain 默认配置（monitor_config 不可注入）
    return snapshot


def test_open_tool_breaker_is_absorbing() -> None:
    """行为事实：达阈值 ⇒ OPEN；此后**成功探针也无法闭合**（OPEN 是吸收态）。"""
    snapshot = _open_after_threshold_failures(CircuitBreakerConfig().failure_threshold)
    assert is_circuit_open(snapshot, "provider-a") is True

    with pytest.raises(CircuitBreakerTransitionError):
        record_probe(
            snapshot,
            "provider-a",
            ToolHealthReport(provider_id="provider-a", status=EndpointHealth.HEALTHY),
        )

    assert is_circuit_open(snapshot, "provider-a") is True, "工具面断路器一旦 OPEN 不会自行恢复"


def test_no_product_module_outside_the_package_references_the_tool_breaker() -> None:
    """枚举事实：工具面断路器的**产品装配点为零**（只有包内实现与再导出）。"""
    sources = _iter_product_sources()
    assert len(sources) >= _MIN_SCANNED, f"扫描面过低（{len(sources)}）⇒ 受判面不成立"

    hits = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in sources
        if any(symbol in path.read_text(encoding="utf-8", errors="ignore") for symbol in _SYMBOLS)
    )
    outside = [rel for rel in hits if not rel.startswith(_IN_PACKAGE)]
    assert outside == [], f"包外出现了工具面断路器的引用（= 接线面变更）: {outside}"
    assert any(rel.endswith("tool_plane/health.py") for rel in hits), "受判面非空：必须命中实现文件"
