"""Runtime 选择面（GOAL-20260919-007 / EC-01 / PLAN-20260919-107）判据。

覆盖四件可判事实：

1. **单侧选择点**（AC-01）：两个组合根都不再直接构造 `FakeAgentRuntime`，都经
   `services.api.runtime_support.build_agent_runtime`。
2. **默认与今日一致**（AC-02）：未配置 ⇒ 受控 demo 执行体，`demo_session_output()`
   逐字段不变。
3. **选择真实 runtime 可判且离线**（AC-03/AC-04）：显式配置构造真实 adapter（构造期
   **不解析凭据、不出网**）；未知取值 fail-closed 并点名取值。
4. **选择结果与指纹进 manifest / 读面**（AC-05）：`RunManifest.execution_backend`
   冻结选择结果，`MANIFEST_FROZEN` payload 把它带到既有事件读面；未声明时保持
   `None`（M7「不伪填充」口径不破）。

反证（AC-06）是**实跑**的（改回硬编码 / 短路选择 / 静默回退 / 去掉填充），记录在
RECHECK 里，不做成常驻用例——常驻的话要么造假要么重复实现。
"""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from adapters.fakes.agent_runtime import FakeAgentRuntime
from adapters.fakes.budget_ledger import FakeBudgetLedger
from adapters.fakes.credential_resolver import FakeCredentialResolver
from packages.application.preflight.preflight import compile_and_preflight, freeze_manifest
from packages.application.run_orchestration.eventing import frozen_payload
from services.api.demo import demo_session_output
from services.api.runtime_support import (
    FAKE_RUNTIME,
    OPENHANDS_RUNTIME,
    RuntimeConfigurationError,
    build_agent_runtime,
    resolve_runtime_selection,
)
from services.api.settings import ApiSettings

ROOT = Path(__file__).resolve().parents[2]
COMPOSITION_ROOTS = (
    ROOT / "services" / "api" / "composition.py",
    ROOT / "services" / "api" / "pg_composition.py",
)


class _ExplodingResolver:
    """解析即炸的凭据面：构造期若解析了凭据，用例会响。"""

    def resolve(self, credential_ref: str) -> Any:  # pragma: no cover - 被调用即失败
        raise AssertionError(f"credential {credential_ref!r} was resolved during construction")

    def has(self, credential_ref: str) -> bool:  # pragma: no cover
        raise AssertionError("credential existence was probed during construction")


def _demo_payload() -> dict[str, object]:
    return {
        "analysis_report": {
            "summary": "controlled fake session output (M13-R1 console demo)",
            "status": "ok",
        }
    }


# ---------------------------------------------------------------- AC-01 结构


def _direct_fake_constructions(path: Path) -> list[int]:
    """文件里直接出现 `FakeAgentRuntime(...)` 调用的行号（AST，不靠 grep 字面量）。"""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if name == "FakeAgentRuntime":
            hits.append(node.lineno)
    return hits


def test_no_composition_root_builds_the_fake_runtime_directly() -> None:
    """AC-01：两个组合根都不得直接构造 runtime（唯一装配点是选择面）。"""
    offenders = {
        path.name: lines
        for path in COMPOSITION_ROOTS
        if (lines := _direct_fake_constructions(path))
    }
    assert offenders == {}, f"composition roots still construct the runtime inline: {offenders}"


def test_composition_roots_call_the_one_selection_point() -> None:
    """AC-01：两个组合根都经同一选择函数取 runtime。"""
    for path in COMPOSITION_ROOTS:
        source = path.read_text(encoding="utf-8")
        assert "build_agent_runtime" in source, f"{path.name} does not use the selection point"


# ---------------------------------------------------------------- AC-02 默认


def test_unconfigured_settings_select_the_controlled_demo_runtime() -> None:
    """AC-02：未配置 ⇒ `fake` 且标记为未显式配置。"""
    selection = resolve_runtime_selection(ApiSettings())
    assert selection.kind == FAKE_RUNTIME
    assert selection.configured is False
    assert isinstance(build_agent_runtime(ApiSettings()), FakeAgentRuntime)


def test_explicit_fake_is_marked_configured() -> None:
    """AC-02：显式选 Fake 与默认不同——读面必须能区分。"""
    selection = resolve_runtime_selection(ApiSettings(agent_runtime=" fake "))
    assert selection.kind == FAKE_RUNTIME
    assert selection.configured is True


def test_demo_session_output_is_unchanged() -> None:
    """AC-02 回归对照：默认路径的 demo 输出逐字段不变。"""
    assert demo_session_output() == _demo_payload()
    runtime = build_agent_runtime(ApiSettings())
    assert cast(Any, runtime)._structured_output == _demo_payload()


# ---------------------------------------------------------- AC-03/04 选择与拒绝


def test_openhands_selection_constructs_the_real_adapter_offline() -> None:
    """AC-03：显式配置 ⇒ 真实 adapter 被构造，且构造期不解析凭据（零出网前提）。"""
    from adapters.openhands.runtime_adapter import OpenHandsRuntimeAdapter

    runtime = build_agent_runtime(
        ApiSettings(agent_runtime=OPENHANDS_RUNTIME),
        credentials=_ExplodingResolver(),
        policy_evaluator=cast(Any, object()),
    )
    assert isinstance(runtime, OpenHandsRuntimeAdapter)


def test_openhands_without_required_faces_names_what_is_missing() -> None:
    """AC-03：缺凭据面/缺 policy 面 ⇒ **点名**拒绝，不静默降级成 Fake。"""
    with pytest.raises(RuntimeConfigurationError) as missing_both:
        build_agent_runtime(ApiSettings(agent_runtime=OPENHANDS_RUNTIME))
    assert "credential_resolver" in str(missing_both.value)
    assert "policy_evaluator" in str(missing_both.value)

    with pytest.raises(RuntimeConfigurationError) as missing_policy:
        build_agent_runtime(
            ApiSettings(agent_runtime=OPENHANDS_RUNTIME),
            credentials=_ExplodingResolver(),
        )
    assert "policy_evaluator" in str(missing_policy.value)
    assert "credential_resolver" not in str(missing_policy.value)


def test_unknown_runtime_fails_closed_naming_the_value() -> None:
    """AC-04：未知取值装配期报错并点名取值与非法的原因；绝不静默回退 Fake。"""
    with pytest.raises(RuntimeConfigurationError) as excinfo:
        resolve_runtime_selection(ApiSettings(agent_runtime="gpt-4o-sidecar"))
    message = str(excinfo.value)
    assert "gpt-4o-sidecar" in message
    assert FAKE_RUNTIME in message and OPENHANDS_RUNTIME in message

    with pytest.raises(RuntimeConfigurationError):
        build_agent_runtime(ApiSettings(agent_runtime="gpt-4o-sidecar"))


def test_settings_read_the_runtime_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-02/AC-04：环境变量是配置面（默认空串 = 未配置）。"""
    monkeypatch.delenv("RESEARCHOS_AGENT_RUNTIME", raising=False)
    assert ApiSettings.from_env().agent_runtime == ""
    monkeypatch.setenv("RESEARCHOS_AGENT_RUNTIME", OPENHANDS_RUNTIME)
    assert resolve_runtime_selection(ApiSettings.from_env()).kind == OPENHANDS_RUNTIME


# ------------------------------------------------- AC-05 manifest / 读面可判


def _frozen_manifest(ctx: Any) -> Any:
    from services.api.composition import ApiDeps
    from services.api.protocol_source import load_protocol_with_body

    deps = cast(ApiDeps, _StubDeps())
    protocol, _body = load_protocol_with_body(deps, "console_demo_research_v1.yaml", None)
    plan, report = compile_and_preflight(protocol, ctx.catalog, ctx.project, ctx)
    assert plan is not None and report.passed, "fixture preflight must pass"
    return freeze_manifest("run-ec01", plan, report, ctx)


class _StubDeps:
    """只服务协议加载的最小 deps 面（`load_protocol_with_body` 读协议来源）。"""

    def __init__(self) -> None:
        self.protocol_draft_service = None


def _preflight_context() -> Any:
    from tests.api.run_fixtures import _build_preflight

    credentials = FakeCredentialResolver()
    credentials.register("LLM_MAIN_KEY", "sk-test-e2e-secret")
    return _build_preflight(credentials, FakeBudgetLedger())


def test_frozen_manifest_records_the_selected_substrate() -> None:
    """AC-05：选择结果冻结进 `RunManifest.execution_backend`（digest 自动覆盖）。"""
    ctx = replace(_preflight_context(), execution_substrate=FAKE_RUNTIME)
    manifest = _frozen_manifest(ctx)
    assert manifest.execution_backend == FAKE_RUNTIME
    assert manifest.digest() != replace(manifest, execution_backend=None).digest()


def test_frozen_manifest_stays_undeclared_without_a_selection() -> None:
    """AC-05 边界：没有选择面时保持 `None`（M7「不伪填充」口径不破）。"""
    manifest = _frozen_manifest(_preflight_context())
    assert manifest.execution_backend is None


def test_runtime_fingerprints_are_explicitly_not_verified() -> None:
    """AC-05：指纹槽位是显式状态，不是留空——空槽分不清「没探」与「探了没问题」。"""
    selection = resolve_runtime_selection(ApiSettings())
    record = selection.fingerprint_record()
    assert record["status"] == "NOT_VERIFIED"
    assert record["substrate"] == FAKE_RUNTIME
    assert str(record["reason"])

    ctx = replace(
        _preflight_context(),
        execution_substrate=FAKE_RUNTIME,
        runtime_fingerprints=record,
    )
    manifest = _frozen_manifest(ctx)
    assert manifest.model_runtime_fingerprints == record


def test_frozen_event_payload_carries_the_substrate_to_the_read_face() -> None:
    """AC-05 读面：`MANIFEST_FROZEN` payload 带执行基质 ⇒ 既有 events 读面即可判。

    零 DTO / 路由 / OpenAPI / 迁移变化（与 GOAL-006 EC-06 同形态）。
    """
    from packages.domain.core import ID
    from packages.domain.run import ResearchRun
    from packages.domain.run_state import ResearchRunState

    ctx = replace(_preflight_context(), execution_substrate=OPENHANDS_RUNTIME)
    manifest = _frozen_manifest(ctx)
    run = ResearchRun(
        id=ID("00000000-0000-4000-8000-0000000000ec"),
        project_id="example-project",
        protocol_id="console_demo_research_v1",
        state=ResearchRunState.State.READY,
    )
    assert frozen_payload(run, manifest)["execution_backend"] == OPENHANDS_RUNTIME
