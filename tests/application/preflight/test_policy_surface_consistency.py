"""GOAL-20260924-014 EC-01：同一协议在两套装配下**结论一致**（策略面一致性主干）。

`W-A` / `W-C`（GOAL-012 cycle 1 登记、GOAL-013 原样承继）说的是同一件事：
`sort_analysis_v1` 在**真实控制面**判 `FAIL`、在 **live / run-ready 装配**判 `WARN`。

**两套装配的载体是产品入口本身**（D-1）——不是本判据手工拼的上下文：

- `services.api.run_execution.execution_inputs()` 在 `deps.preflight_override is None` 时
  走 `_live_preflight()`（**真实控制面**：`NativePolicyEvaluator(catalog.policy)`，
  policy 取自目录里真实的 `examples/config/policy.yaml`）；
- `preflight_override` 在场时直接用该上下文（**live / run-ready 装配**，
  GOAL-009…013 全部真实 run 走的路径）。

**判据（每条都离线：零出网、零容器、零凭据读取；网关是 `FakeModelGateway`「无网络」）**：

1. 真实控制面**不再 `FAIL`**，且**无 `POLICY_DENIED`**；
2. 两套装配 `status` **相等**且**都不含 `FAIL`**（`W-C` 的消灭）；
3. **自检**：真实控制面的求值器确实是 `NativePolicyEvaluator`、其 policy 确实来自
   `examples/config/policy.yaml`，且 `allow` 里确实有 `evidence.read`
   ——防「判据在空转时假绿」；
4. **执行期同源**（F-5）：`policy_scope_for("evidence.read")` 与 preflight 的求值 scope
   一致，且真实求值器对该请求判 `ALLOW`——只放行 preflight 会让同一能力在门链处落回
   `DENY`（「同一能力两处结论」的第二形态）。

**判据性质披露（D-3，写进断言而不是散文）**：两套装配在**非策略维度**上本来就**不同源**
（真实控制面用合并目录的端点/health 事实；live 装配用夹具声明的 catalog）⇒ 本判据只对
**结论**（`status`）与**策略维度**（`POLICY_DENIED` 计数）下断言，**不**断言两份 findings
逐字相等。**能被什么按压**：撤掉 allow 规则（策略维度立刻红）；**不能被什么按压**：
改非策略的 finding 文案（本判据不读它）。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from packages.application.policy.native import NativePolicyEvaluator, PolicyRequest
from packages.application.preflight.policy_check import policy_scope_for
from packages.domain.enums import PolicyDecision
from packages.domain.protocols import PreflightStatus
from services.api.run_execution import ExecutionRequest, execution_inputs

_PROTOCOL = "sort_analysis_v1.yaml"
_PROTOCOL_PATH = "examples/protocols/sort_analysis_v1.yaml"
_PROJECT_ID = "example-project"
_CAPABILITY = "evidence.read"
_EXPECTED_SCOPE = "project"

_REAL_RUN = "b7c31d40-0001-4f21-8a02-000000000001"
_OVERRIDE_RUN = "b7c31d40-0002-4f21-8a02-000000000002"


def _deps() -> Any:
    from tests.api.run_fixtures import make_run_ready_deps

    return make_run_ready_deps()


def _execution_inputs(deps: Any, run_id: str) -> Any:
    """走**产品入口**解析一次运行输入（`context` 由装配决定，本判据不另开一条路）。"""
    from packages.domain.core import ID

    request = ExecutionRequest(
        deps=deps,
        protocol_path=_PROTOCOL,
        run_id=ID(run_id),
        trace_id=None,
        draft_ref=None,
        project_id=_PROJECT_ID,
    )
    return execution_inputs(request)


def _preflight_under(deps: Any, run_id: str) -> tuple[Any, Any]:
    """走**产品入口**求一次 preflight；返回 (context, report)。

    装配由 `deps.preflight_override` 的在场与否决定——本判据不在产品入口之外另开一条路。
    """
    inputs = _execution_inputs(deps, run_id)
    context = inputs.preflight
    plan, report = _run_preflight(context)
    assert plan is not None, _verdict(report)
    return context, report


def _run_preflight(context: Any) -> tuple[Any, Any]:
    from adapters.contracts.protocol_loaders import load_protocol
    from packages.application.preflight.preflight import compile_and_preflight

    protocol = load_protocol(_PROTOCOL_PATH)
    return compile_and_preflight(protocol, context.catalog, context.project, context)


def _verdict(report: Any) -> str:
    """判词逐字（按压时判据失败消息里点名的是这些行）。"""
    lines = [
        f"[{item.code}] severity={item.severity} {item.subject_ref}: {item.message}"
        for item in report.findings
    ]
    return f"status={report.status} passed={report.passed}\n" + "\n".join(lines)


def _policy_denials(report: Any) -> list[str]:
    return [item.message for item in report.findings if item.code == "POLICY_DENIED"]


def _real_control_plane_report() -> Any:
    """真实控制面（**无** `preflight_override`）——`W-A` 的那一套装配。"""
    deps = replace(_deps(), preflight_override=None)
    _context, report = _preflight_under(deps, _REAL_RUN)
    return report


def _run_ready_report() -> Any:
    """live / run-ready 装配（`preflight_override` 在场）——`W-C` 的另一套装配。"""
    _context, report = _preflight_under(_deps(), _OVERRIDE_RUN)
    return report


def test_the_real_control_plane_is_no_longer_fail() -> None:
    """EC-01 ①：真实控制面**不再 `FAIL`**，且策略维度清零（`W-A` 的消灭）。"""
    report = _real_control_plane_report()
    assert report.status is not PreflightStatus.FAIL, _verdict(report)
    assert _policy_denials(report) == [], _verdict(report)


def test_both_assemblies_reach_the_same_conclusion() -> None:
    """EC-01 ②：两套装配 `status` **相等**且都不含 `FAIL`（`W-C` 的消灭）。"""
    real = _real_control_plane_report()
    override = _run_ready_report()
    assert real.status is not PreflightStatus.FAIL, _verdict(real)
    assert override.status is not PreflightStatus.FAIL, _verdict(override)
    assert real.status == override.status, (
        f"两套装配结论仍不一致：real={real.status} override={override.status}\n"
        f"--- real ---\n{_verdict(real)}\n--- override ---\n{_verdict(override)}"
    )
    assert _policy_denials(real) == [], _verdict(real)
    assert _policy_denials(override) == [], _verdict(override)


def test_the_real_control_plane_really_is_the_real_policy() -> None:
    """自检（防判据空转）：求值器是 `NativePolicyEvaluator`，策略来自 `policy.yaml`。"""
    deps = replace(_deps(), preflight_override=None)
    context, _report = _preflight_under(deps, _REAL_RUN)
    assert isinstance(context.policy_evaluator, NativePolicyEvaluator), type(
        context.policy_evaluator
    ).__name__
    policy = context.catalog.policy
    assert policy is not None, "真实控制面必须带上目录里的 policy.yaml"
    assert policy.default_effect is PolicyDecision.DENY, policy.default_effect
    allowed = {rule.capability for rule in policy.allow}
    assert _CAPABILITY in allowed, sorted(allowed)


def test_the_real_control_plane_warn_is_freezable() -> None:
    """EC-01 ②「同为 `WARN`+**可冻结**」的冻结面：真实控制面的 `WARN` **能冻**。

    只断言 `status` 相等是不够的——「可跑」还要求 `freeze_manifest` 能完成：
    `TOOL_RISK_ELEVATED` 的 EXECUTE 风险必须由**策略显式允许**才可转换
    （GOAL-012 EC-01 的通道）。本 EC 要的正是**真实控制面**上这条路能走通
    （此前它死在 `POLICY_DENIED`，从未被走到过）。

    留痕只断言 **(phase, capability) 对集合**，**不**断言 `decision`：
    两套装配用的是**不同的求值器**，各自记各自的判定（真实控制面是
    `ALLOW_WITH_CONSTRAINTS`（`code.execute` / `workspace.write.code` 带约束），
    live 装配的 Fake 求值器全放行记 `ALLOW`）——那是**装配差异的正确表现**，
    不是不一致；本判据的射程是**结论**（可冻、留痕覆盖同一批对）。
    """
    from adapters.contracts.protocol_loaders import load_protocol
    from packages.application.preflight.preflight import (
        ManifestFreezeError,
        compile_and_preflight,
        freeze_manifest,
    )

    deps = replace(_deps(), preflight_override=None)
    inputs = _execution_inputs(deps, _REAL_RUN)
    context = inputs.preflight
    protocol = load_protocol(_PROTOCOL_PATH)
    plan, report = compile_and_preflight(protocol, context.catalog, context.project, context)
    assert plan is not None, _verdict(report)
    try:
        manifest = freeze_manifest(_REAL_RUN, plan, report, context)
    except ManifestFreezeError as exc:  # pragma: no cover - 失败即判据红
        raise AssertionError(f"真实控制面的 WARN 不可冻结：{exc}\n{_verdict(report)}") from exc
    assert manifest.frozen_at is not None
    pairs = {(item["phase_id"], item["capability"]) for item in manifest.accepted_policy_exceptions}
    assert pairs == {
        ("execution", "code.execute"),
        ("execution", "workspace.read"),
        ("execution", "workspace.write.code"),
        ("review", "workspace.read"),
    }, sorted(pairs)


def test_the_capability_is_allowed_at_execution_time_too() -> None:
    """EC-01 ④（F-5）：执行期复用同一张 scope 表，且真实求值器对该请求判 `ALLOW`。

    只放行 preflight 会让执行期落回 `default_effect`（DENY）——「同一能力两处结论」。
    """
    from adapters.contracts import load_policy

    assert policy_scope_for(_CAPABILITY) == _EXPECTED_SCOPE
    policy = load_policy("examples/config/policy.yaml")
    evaluator = NativePolicyEvaluator(policy)
    result = evaluator.evaluate(
        PolicyRequest(
            actor="project:example-project",
            capability=_CAPABILITY,
            scope=_EXPECTED_SCOPE,
            resource="phase:review",
        )
    )
    assert result.decision is not PolicyDecision.DENY, result.reason
