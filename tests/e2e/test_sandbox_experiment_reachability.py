"""GOAL-011 EC-03 / GOAL-012 EC-01：沙箱实验阶段在**真实 preflight 路径**上的可达性。

三段判据，都**离线**（不连端点、不起容器、不出网）：

1. **装配面成立**：run-ready 装配给执行阶段合约加上「沙箱实验」声明后，
   (a) 解析出来的合约确实带声明，(b) 实验缝被装进编排依赖，
   (c) 派发判据看得见它（`contract.experiment is not None`）。
2. **风险分层的结构事实**：`classify_risk(EXECUTE, …) → HIGH` 与 trust level 无关
   ——**GOAL-012 的授权明确不动它**：谁放宽它，这条判据就红。
3. **冻结门的显式策略通道（GOAL-012 EC-01，路径 (A)）**：`sort_analysis_v1` 的报告
   **仍是 `WARN`**（四条 `TOOL_RISK_ELEVATED` 一条不少），但当那些 EXECUTE 风险已被
   **显式策略声明**允许时，冻结**可完成**且**留痕**在场；**成对反证**：把显式允许撤掉
   ⇒ 回到**拒冻**，且消息**点名** `code.execute`。

   历史（保留，不抹掉）：GOAL-011 cycle 6 实测这里是**阻断点**——`freeze_manifest` 的
   `if not report.passed: raise` 拒冻 ⇒ run 在执行前终止（`manifest_digest: null`、
   零 task / 零实验）。cycle 10 把它登记为「需要一次拍板」的项；GOAL-012 建档当日用户
   **拍板路径 (A)**：新增一条显式、留痕、可审计的接受口径，而**不是**放宽风险分类、
   也**不是**让 `WARN` 无条件可冻。第 3 段判据因此按新语义重钉，并**同时**钉住反方向。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from packages.domain.enums import EffectClass, PolicyDecision, RiskClass, TrustLevel
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
_FROZEN_PAIR = ("execution", "code.execute")


def _deps() -> Any:
    from tests.api.run_fixtures import make_run_ready_deps

    return make_run_ready_deps()


def _preflight(context: Any | None = None) -> tuple[Any, Any]:
    from adapters.contracts.protocol_loaders import load_protocol
    from packages.application.preflight.preflight import compile_and_preflight

    chosen = context if context is not None else _deps().preflight_override
    protocol = load_protocol(_PROTOCOL)
    plan, report = compile_and_preflight(protocol, chosen.catalog, chosen.project, chosen)
    return plan, report


@pytest.mark.requires_docker
def test_the_declaration_and_the_seam_land_on_the_run_assembly() -> None:
    """装配面：合约带声明、缝已装、派发判据看得见（判据不空转）。

    挂 `requires_docker`：本用例走**真实装配**（`with_sandbox_experiment`），
    而该装配会构造 `DockerExecutionBackend`——**没有 Linux 可用的 daemon 时构造即抛**
    （CI 的 windows 跑者实测 `DockerException: Error while fetching server API version`）。
    标记让它落到 `container-quality` 那个容器门禁作业里**真跑**，其余作业如实 skip。
    """
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


def test_the_allowed_execute_risk_freezes_with_a_trace() -> None:
    """**新语义**：报告仍 `WARN`，但策略显式允许的 EXECUTE 风险可冻结 + 留痕。"""
    from packages.application.preflight.preflight import freeze_manifest

    plan, report = _preflight()
    assert plan is not None, ("协议应能编译（阻断点是预检/冻结，不是编译）", report.findings)
    assert report.status is PreflightStatus.WARN, report.findings
    assert report.passed is False, "通道不改 `passed` 的语义（PASS 才 passed）"
    warnings = [finding.code for finding in report.findings if finding.code == "TOOL_RISK_ELEVATED"]
    assert warnings, [finding.code for finding in report.findings]
    assert any(_PROVIDER in finding.message for finding in report.findings), [
        finding.message for finding in report.findings
    ]
    manifest = freeze_manifest("run-allowed", plan, report, _deps().preflight_override)
    pairs = {
        (str(item["phase_id"]), str(item["capability"]))
        for item in manifest.accepted_policy_exceptions
    }
    assert _FROZEN_PAIR in pairs, manifest.accepted_policy_exceptions
    assert all(item["accepted_at"] for item in manifest.accepted_policy_exceptions)


def test_withdrawing_the_allowance_refuses_and_names_the_capability() -> None:
    """**成对反证**：撤掉显式允许 ⇒ 回到拒冻，消息点名 `code.execute`（先红后绿）。"""
    from adapters.fakes.policy_evaluator import FakePolicyEvaluator
    from packages.application.preflight.preflight import ManifestFreezeError, freeze_manifest

    evaluator = FakePolicyEvaluator()
    evaluator.set_decision("code.execute", PolicyDecision.REQUIRE_APPROVAL)
    context = replace(_deps().preflight_override, policy_evaluator=evaluator)
    plan, report = _preflight(context)
    assert plan is not None
    assert report.status is PreflightStatus.WARN, [item.code for item in report.findings]
    with pytest.raises(ManifestFreezeError) as excinfo:
        freeze_manifest("run-withdrawn", plan, report, context)
    message = str(excinfo.value)
    assert "code.execute" in message, message
    assert "REQUIRE_APPROVAL" in message or "no acceptance channel" in message, message
