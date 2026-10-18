"""GOAL-20261018-084 EC-04：评审独立性判据**接进产品路径**且默认零回归。

**判什么**（全部走产品入口 `services.api.catalog` + `compile_and_preflight`）：

1. **出厂协议真的能过**：`m12_reference_research_v1` 的编译+预检里
   **没有任何 `HETEROGENEITY_VIOLATION`** —— 这是上一轮拒冻的那个协议；
2. **反向按压仍然咬得住**：只把评审 agent 指回生产者的模型（`reviewer_gamma`，与
   `research_alpha` **同一个 `model_name`**）⇒ 同一条 preflight **必须**给出
   `HETEROGENEITY_VIOLATION`，且**点名相交的目标** `main/deepseek-v4-flash-vision`；
3. **未声明评审关系 ⇒ 不判**（既有语义逐字不变）：一个没有 WRITER/REVIEWER
   `review_panel_role` 的目录 ⇒ 无该码 finding。

**按压形态**：内存内 `replace`（不改仓库文件），由 `test_the_press_leaves_the_tree_untouched`
钉住按压前后的文件 `sha256` 相同 —— 判据**不靠改树**取得结论。
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

from packages.application.ports import CatalogSnapshot, PreflightContext
from packages.application.preflight.preflight import compile_and_preflight
from packages.domain.enums import ModelBindingMode, ReviewPanelRole
from packages.domain.protocols import PreflightReport
from packages.domain.roles import AgentBinding
from services.api.catalog import (
    load_catalog_snapshot,
    load_project_settings,
    load_protocol_definition,
)

ROOT = Path(__file__).resolve().parents[3]
PROTOCOL = "m12_reference_research_v1.yaml"
PRODUCER_MODEL = "reviewer_gamma"  # 与生产者同 `model_name`（== research_alpha）
PRODUCER_TARGET = "main/deepseek-v4-flash-vision"
VIOLATION = "HETEROGENEITY_VIOLATION"


def _preflight(catalog: CatalogSnapshot) -> PreflightReport:
    """走**产品入口**编译 + 预检（不另开只有判据知道的路）。"""
    project = load_project_settings()
    protocol = load_protocol_definition(PROTOCOL)
    _, report = compile_and_preflight(
        protocol, catalog, project, PreflightContext(catalog=catalog, project=project)
    )
    return report


def _violations(report: PreflightReport) -> list[str]:
    return [item.message for item in report.findings if item.code == VIOLATION]


def _with_reviewer_on(model_id: str) -> CatalogSnapshot:
    """内存内把 `reviewer_a` 改成显式绑定到 `model_id`（不改仓库文件）。"""
    catalog = load_catalog_snapshot()
    agents = dict(catalog.agents)
    agents["reviewer_a"] = replace(
        agents["reviewer_a"],
        model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value=model_id),
    )
    return replace(catalog, agents=agents)


def test_the_factory_protocol_passes_the_independence_gate() -> None:
    """出厂协议 `m12_reference_research_v1` 不再被本判据拒冻。"""
    report = _preflight(load_catalog_snapshot())
    assert _violations(report) == [], _violations(report)


def test_the_gate_still_bites_when_the_reviewer_goes_back_to_the_producer_model() -> None:
    """**反向按压**：评审者指回生产者模型 ⇒ 判红并点名相交目标。"""
    report = _preflight(_with_reviewer_on(PRODUCER_MODEL))
    messages = _violations(report)
    assert len(messages) == 1, messages
    assert PRODUCER_TARGET in messages[0], messages[0]
    assert "research_writer" in messages[0] and "scientific_reviewer" in messages[0], messages[0]


def test_the_press_is_reversible_and_leaves_the_config_bytes_untouched() -> None:
    """按压**不改树**：`sha256` 前后相同（判据不靠改仓库取得结论）。"""
    paths = (
        "examples/config/agents.yaml",
        "examples/config/model_profiles.yaml",
        "examples/config/models.yaml",
    )
    before = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}
    _preflight(_with_reviewer_on(PRODUCER_MODEL))
    after = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}
    assert before == after, (before, after)


def test_a_catalog_without_writer_or_reviewer_panels_is_not_judged() -> None:
    """**未声明评审关系 ⇒ 不判**（既有语义逐字不变；不是「全域两两互查」）。"""
    catalog = load_catalog_snapshot()
    cleared = {
        role_id: replace(role, review_panel_role=ReviewPanelRole.NONE)
        for role_id, role in catalog.roles.items()
    }
    report = _preflight(replace(catalog, roles=cleared))
    assert _violations(report) == [], _violations(report)
