"""GOAL-20260925-016 EC-01（D-01(b)）：出厂组合根「缝为空」⇒ preflight 必须**逐字点名能力**。

**要钉住的决定（D-01(b)，用户 2026-09-25 拍板）**：出厂组合根**不**自己接执行体缝
（`ApiDeps.tool_providers` 生产为空），缝由**装配方**补。代价是「出厂组合根跑不通带执行体的
协议」——所以这条缝的契约必须**可判**：缺执行体时 preflight 必须**点名哪个能力没人执行**，
而不是给一句「工具面有问题」。

**判据口径 = 反向搜索 + 行为证据成对**（本文件即证据面）：

1. **行为证据（正向）**：把**出厂目录**（`services.api.catalog` = 产品路径）的
   `tool_providers` 置空（= D-01(b) 的生产形态）后用**产品入口** `compile_and_preflight`
   编译 + 预检 ⇒ 每一条 `ToolRequirement` 都必须在报告里得到一条
   `TOOL_UNAVAILABLE`，其消息**逐字等于** `no provider is available for capability {能力名}`
   且 `subject_ref` 指向**该 phase**。
2. **行为证据（反证成对）**：同一协议、同一判据，**只**恢复出厂 provider ⇒ 上述点名的
   finding **全部消失**（且该码在该报告里计数归零）。⇒ 证明点名的是**供给面的缺失**，
   不是协议本身的固定文本。
3. **反向搜索**：点名模板在**生产源**（`packages/` / `services/` / `adapters/`）里
   **只有一个来源**（`packages/application/preflight/checks.py`）⇒ 该命名是**单一实现点的
   稳定事实**，不是多处巧合。测试 / 夹具目录**不参与**该搜索（本文件自身就必须写出模板，
   把测试算进去会让「唯一来源」变成恒假）。
4. **按压自身**：把消息模板改坏（**内存内变体**，不改仓库文件）⇒ 匹配器判空
   ⇒ 证明判据真的在读那条消息，而不是在空转。

**边界（D-01(b) 明文）**：`packages/application/preflight/checks.py` 的**点名实现不得改动**。
若某天判据要求改点名词，那属**改产品行为** ⇒ 停下登记，由 GOAL 层拍板，不在判据里迁就。

**判据性质披露**：本判据**不**断言 `PreflightStatus` 的具体取值以外的 finding 集合
（协议缺 provider 时报告里同时有**编译面**的同名码 `no tool provider exposes capability …`，
那是 `CompileFindingCode` 的另一条链，**不**在本判据的断言面内）；也**不**断言 provider
健康 / 信任面（那是 `no healthy provider is available …` 的第三种形态）。
"""

from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path
from typing import Any

from packages.application.ports import PreflightContext
from packages.application.preflight.preflight import compile_and_preflight
from packages.domain.protocols import (
    CompiledRunPlan,
    PreflightFinding,
    PreflightFindingCode,
    PreflightReport,
    PreflightStatus,
)
from services.api.catalog import (
    load_catalog_snapshot,
    load_project_settings,
    load_protocol_definition,
)

ROOT = Path(__file__).resolve().parents[3]
PRODUCTION_ROOTS = ("packages", "services", "adapters")
TEMPLATE = "no provider is available for capability"
TEMPLATE_SOURCE = "packages/application/preflight/checks.py"
PROTOCOL = "sort_analysis_v1.yaml"


def _factory_catalog() -> Any:
    """出厂目录（产品路径：`services.api.catalog`）。"""
    return load_catalog_snapshot()


def _without_executors(catalog: Any) -> Any:
    """D-01(b) 的生产形态：执行体缝为空（装配方补）。"""
    return replace(catalog, tool_providers={})


def _preflight(protocol_name: str, catalog: Any) -> tuple[CompiledRunPlan | None, PreflightReport]:
    """走**产品入口**编译 + 预检（不另开一条只有判据知道的路）。"""
    project = load_project_settings()
    protocol = load_protocol_definition(protocol_name)
    context = PreflightContext(catalog=catalog, project=project)
    return compile_and_preflight(protocol, catalog, project, context)


def _named(report: PreflightReport, capability: str) -> list[PreflightFinding]:
    """报告里**点名该能力**的缺执行体 finding（模板 + 能力名逐字拼接）。"""
    expected = f"{TEMPLATE} {capability}"
    return [
        finding
        for finding in report.findings
        if finding.code == PreflightFindingCode.TOOL_UNAVAILABLE.value
        and finding.message == expected
    ]


def _names_requirement(report: PreflightReport, requirement: Any) -> bool:
    """报告里是否有**恰好指向该 (phase, capability)** 的点名。

    同一能力可被**多个 phase** 需要（`workspace.read` 在 `execution` 与 `review` 上都出现），
    所以配对必须按 `(phase_id, capability)` 而不是只按能力名——否则一条点名会被读成
    覆盖了两处需求。
    """
    expected = (f"{TEMPLATE} {requirement.capability}", f"phase:{requirement.phase_id}")
    return any(
        (finding.message, finding.subject_ref) == expected
        for finding in report.findings
        if finding.code == PreflightFindingCode.TOOL_UNAVAILABLE.value
    )


def _tool_unavailable_count(report: PreflightReport) -> int:
    code = PreflightFindingCode.TOOL_UNAVAILABLE.value
    return sum(1 for finding in report.findings if finding.code == code)


def _unavailable_pairs(report: PreflightReport) -> list[tuple[str, str | None]]:
    """报告里该码的全部 (消息, 归属)，供判词点名实际观测到什么。"""
    code = PreflightFindingCode.TOOL_UNAVAILABLE.value
    return [
        (finding.message, finding.subject_ref)
        for finding in report.findings
        if finding.code == code
    ]


def _production_template_hits() -> list[str]:
    """**反向搜索**：点名模板在生产源里的出现位置（只扫产品代码，不扫测试/夹具）。

    用 `os.walk(followlinks=False)`：仓库里有悬空链接（`node_modules` 的 pnpm 链接），
    `pathlib.rglob` 会直接抛错。
    """
    hits: list[str] = []
    for root_name in PRODUCTION_ROOTS:
        for dirpath, dirnames, filenames in os.walk(ROOT / root_name, followlinks=False):
            dirnames[:] = [name for name in dirnames if name != "__pycache__"]
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                path = Path(dirpath) / filename
                if TEMPLATE in path.read_text(encoding="utf-8", errors="replace"):
                    hits.append(path.relative_to(ROOT).as_posix())
    return sorted(hits)


def test_missing_executors_are_named_capability_by_capability() -> None:
    """缝为空 ⇒ 计划里**每一条** `ToolRequirement` 都被逐字点名（含 phase 归属）。"""
    plan, report = _preflight(PROTOCOL, _without_executors(_factory_catalog()))

    assert plan is not None, "缝为空不应该让编译产出计划（协议本身可编译）"
    assert plan.tool_requirements, "该协议必须有工具需求，否则本判据在空转"
    for requirement in plan.tool_requirements:
        assert requirement.provider_ids == (), (
            f"生产形态下 {requirement.capability} 不应有 provider，"
            f"实测 {requirement.provider_ids!r}"
        )
        assert _names_requirement(report, requirement), (
            f"{requirement.phase_id} 上的能力 {requirement.capability} 缺执行体却没有被点名；"
            f"报告里的 TOOL_UNAVAILABLE = {_unavailable_pairs(report)!r}"
        )
    assert report.status is PreflightStatus.FAIL, "缺执行体是 ERROR 级事实，不得降级为 WARN/PASS"


def test_restoring_executors_removes_the_named_findings() -> None:
    """**反证成对**：只恢复出厂 provider ⇒ 点名全部消失、该码计数归零。"""
    catalog = _factory_catalog()
    plan, report = _preflight(PROTOCOL, _without_executors(catalog))

    assert plan is not None
    requirements = list(plan.tool_requirements)
    for requirement in requirements:
        assert _names_requirement(report, requirement), (
            f"反证前提不成立：缝为空时 {requirement.phase_id} 的 "
            f"{requirement.capability} 本应被点名"
        )

    restored_plan, restored_report = _preflight(PROTOCOL, catalog)
    assert restored_plan is not None
    for requirement in requirements:
        assert not _names_requirement(restored_report, requirement), (
            f"补上 provider 之后 {requirement.phase_id} 的 {requirement.capability} 仍被点名为"
            f"「没人执行」⇒ 点名与供给面无关，判据的配对不成立"
        )
    assert _tool_unavailable_count(restored_report) == 0, (
        "出厂 provider 覆盖该协议全部能力 ⇒ 该码不应再出现"
    )


def test_naming_template_has_a_single_production_source() -> None:
    """反向搜索：点名模板在生产源里只有**一个**来源。"""
    assert _production_template_hits() == [TEMPLATE_SOURCE], (
        "点名模板必须来自单一生产实现点；多处出现意味着「碰巧在场」而非稳定事实。"
        "若这次判红是因为新增了第二处实现 ⇒ 先判它是否重复了 D-01(b) 的点名契约，"
        "**不得**为让它变绿而放宽本判据。"
    )


def test_criterion_is_pressable_by_breaking_the_template() -> None:
    """按压自身：模板被改坏 ⇒ 匹配器判空（判据不是恒真）。"""
    _, report = _preflight(PROTOCOL, _without_executors(_factory_catalog()))
    capability = next(
        finding.message.removeprefix(f"{TEMPLATE} ")
        for finding in report.findings
        if finding.code == PreflightFindingCode.TOOL_UNAVAILABLE.value
        and finding.message.startswith(f"{TEMPLATE} ")
    )
    assert _named(report, capability), "现状下该能力必须被点名（否则后续按压无意义）"

    broken = replace(
        report,
        findings=[
            replace(finding, message=finding.message.replace(TEMPLATE, "tool problem"))
            if finding.message.startswith(f"{TEMPLATE} ")
            else finding
            for finding in report.findings
        ],
    )
    assert _named(broken, capability) == [], "模板改坏后仍被匹配 ⇒ 判据在读别的字，不是在读这条消息"
