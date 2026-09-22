"""GOAL-011 EC-03：沙箱实验阶段在**真实 preflight 路径**上的可达性与它的阻断点。

两段判据，都**离线**（不连端点、不起容器、不出网）：

1. **装配面成立**：run-ready 装配给执行阶段合约加上「沙箱实验」声明后，
   (a) 解析出来的合约确实带声明，(b) 实验缝被装进编排依赖，
   (c) 派发判据看得见它（`contract.experiment is not None`）。
2. **阻断点如实钉住**：`sort_analysis_v1` 今天**过不了**真实的
   compile → preflight → freeze 三步——不是会话起不来，而是**预检报告是 `WARN`**：
   它的执行阶段要求 `code.execute`，对应 provider `openhands_workspace` 的
   `effect_class: EXECUTE` 在 `classify_risk` 里**无条件**是 `HIGH`
   （`packages/domain/tools.py:143-144`）⇒ 四条 `TOOL_RISK_ELEVATED` WARNING ⇒
   `freeze_manifest` 的 `if not report.passed: raise ManifestFreezeError`
   （`preflight.py:186-187`）**拒绝冻结** ⇒ run 在**执行之前**终止：
   `manifest_digest` 为 `None`、`/tasks` 为空、零工具观测。

   这条**不是本 PLAN 引入的**：同一装配下**不做**任何沙箱实验声明时，实测同一签名
   （`FAILED` + `manifest_digest: null` + `tasks: []`）。它是**既有**的语义交叉，
   与 `real_retrieval_research_v1` 头部登记的那一类（「预检报告 WARN ⇒ 拒绝冻结」
   与服务侧口径不一致）同源。**本判据不修它**，只把它钉成可复核的形态：
   一旦有人为了跑通而放宽 `classify_risk` / `freeze_manifest` / 该警告的严重级，
   两条判据里至少一条会红。
"""

from __future__ import annotations

from typing import Any

import pytest

from packages.domain.enums import EffectClass, RiskClass, TrustLevel
from packages.domain.protocols import PreflightStatus
from packages.domain.tools import classify_risk
from tests.e2e.live_run_support import (
    EXPERIMENT_CONTRACT,
    EXPERIMENT_IMAGE,
    EXPERIMENT_SCRIPT,
    with_sandbox_experiment,
)

_PROTOCOL = "examples/protocols/sort_analysis_v1.yaml"
_PROVIDER = "openhands_workspace"


def _deps() -> Any:
    from tests.api.run_fixtures import make_run_ready_deps

    return make_run_ready_deps()


def _preflight() -> tuple[Any, Any]:
    from adapters.contracts.protocol_loaders import load_protocol
    from packages.application.preflight.preflight import compile_and_preflight

    deps = _deps()
    context = deps.preflight_override
    protocol = load_protocol(_PROTOCOL)
    plan, report = compile_and_preflight(protocol, context.catalog, context.project, context)
    return plan, report


def test_the_declaration_and_the_seam_land_on_the_run_assembly() -> None:
    """装配面：合约带声明、缝已装、派发判据看得见（判据不空转）。"""
    deps = _deps()
    with_sandbox_experiment(deps, script=EXPERIMENT_SCRIPT, image=EXPERIMENT_IMAGE)
    contract = deps.preflight_override.catalog.task_contracts[EXPERIMENT_CONTRACT]
    assert contract.experiment is not None
    assert contract.experiment.script == EXPERIMENT_SCRIPT
    assert contract.experiment.image == EXPERIMENT_IMAGE
    assert deps.runs._deps.experiment_task is not None, "实验缝没装进编排依赖"


def test_the_execute_provider_is_high_risk_by_construction() -> None:
    """风险分层的**结构事实**：`EXECUTE` ⇒ `HIGH`，与 trust level 无关。"""
    assert classify_risk(EffectClass.EXECUTE, TrustLevel.BUILT_IN) is RiskClass.HIGH


def test_sort_analysis_is_refused_before_freeze_on_the_risk_warning() -> None:
    """阻断点：计划编得出来，报告是 `WARN`，`freeze_manifest` 拒绝（如实钉住）。"""
    from packages.application.preflight.preflight import freeze_manifest

    plan, report = _preflight()
    assert plan is not None, ("协议应能编译（阻断点是预检/冻结，不是编译）", report.findings)
    assert report.status is PreflightStatus.WARN, report.findings
    warnings = [finding.code for finding in report.findings if finding.code == "TOOL_RISK_ELEVATED"]
    assert warnings, [finding.code for finding in report.findings]
    assert any(_PROVIDER in finding.message for finding in report.findings), [
        finding.message for finding in report.findings
    ]
    with pytest.raises(Exception, match="passing preflight"):
        freeze_manifest("run-blocker", plan, report, _deps().preflight_override)
