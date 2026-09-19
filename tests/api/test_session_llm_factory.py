"""Session 期执行目标与会话 LLM 工厂（GOAL-20260919-007 / EC-03 / PLAN-20260919-109）。

覆盖三件可判事实：

1. **执行目标由上层解析**：`session_resolution.execution_target` 把
   `plan.resolved_models[agent_id]` → `catalog.models` → `catalog.endpoints` 串成
   `(endpoint, model)`，任一环缺失返回 `None`（不编造、不回退别的 model）。
2. **spec 携带目标**：`_run_session` 把解析结果放进 `AgentSessionSpec`；Fake 不看这两个
   字段（默认路径不变）。
3. **会话 LLM 工厂受门**：`session_llm_factory` 按与 EC-02 同一条链裁决
   （URL 策略 → 凭据存在性），任一步失败**点名**拒绝且**在构造 LLM 之前**——
   即拒绝不产生任何出站调用。

反证（拆掉门 ⇒ 判据红）与端到端四段判据记录在 RECHECK 里。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from adapters.fakes.credential_resolver import FakeCredentialResolver
from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
from packages.application.run_orchestration.session_resolution import execution_target
from packages.domain.models import EndpointDiscoveryConfig, LLMEndpoint, ModelDefinition
from services.api.runtime_support import RuntimeConfigurationError, session_llm_factory

_CREDENTIAL_REF = "LLM_MAIN_KEY"
# Computed fixture credential（源码不出现可用字面量）。
_FIXTURE_KEY = "fixture-" + "k" * 20
_PUBLIC_URL = "https://relay.example.com/api/v1"


class _Context:
    """`execution_target` 只需要的两面（plan.resolved_models + catalog）。"""

    def __init__(self, *, resolved: dict[str, str], models: Any, endpoints: Any) -> None:
        self.plan = type("_Plan", (), {"resolved_models": resolved})()
        self.catalog = type("_Catalog", (), {"models": models, "endpoints": endpoints})()


def _endpoint(base_url: str = _PUBLIC_URL, endpoint_id: str = "main") -> LLMEndpoint:
    return LLMEndpoint(
        id=endpoint_id,
        name="Main Relay",
        protocol="OPENAI_COMPATIBLE",
        base_url=base_url,
        credential_ref=_CREDENTIAL_REF,
        max_retries=0,
        discovery=EndpointDiscoveryConfig(),
    )


def _model(endpoint_id: str = "main", model_id: str = "research_alpha") -> ModelDefinition:
    return ModelDefinition(id=model_id, endpoint_id=endpoint_id, model_name="relay-model")


def _context(
    *,
    resolved: dict[str, str] | None = None,
    model: ModelDefinition | None = None,
    endpoint: LLMEndpoint | None = None,
) -> _Context:
    model_id = (model or _model()).id
    return _Context(
        resolved=resolved if resolved is not None else {"domain_a": model_id},
        models={model_id: model or _model()},
        endpoints={(endpoint or _endpoint()).id: endpoint or _endpoint()},
    )


class _SpyBuilder:
    """记录是否有人真的去装配 LLM——「拒绝在构造之前」就靠它可判。"""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover - 被调用即失败
        self.calls += 1
        raise AssertionError("LLM construction must not happen when the gate refuses")


def _spec(endpoint: LLMEndpoint | None, model: ModelDefinition | None) -> Any:
    from packages.application.ports.agent_runtime import AgentSessionSpec
    from packages.domain.core import ID

    return AgentSessionSpec(
        task_id=ID.generate(),
        task_contract=cast(Any, None),
        role=cast(Any, None),
        agent=cast(Any, None),
        endpoint=endpoint,
        model=model,
    )


# ------------------------------------------------------- WP-A 解析（AC-01 的前半）


def test_execution_target_resolves_through_the_compiled_binding() -> None:
    """AC-01：agent → model → endpoint 由编译期绑定串起来（同一份事实，不另立一份）。"""
    endpoint = _endpoint()
    model = _model()
    found_endpoint, found_model = execution_target(
        cast(Any, _context(model=model, endpoint=endpoint)), "domain_a"
    )
    assert found_endpoint is endpoint
    assert found_model is model


def test_execution_target_returns_none_instead_of_guessing() -> None:
    """AC-01/AC-03：缺失环保留「已解析出的那一半」，不编造、不回退别的 model。"""
    assert execution_target(cast(Any, _context(resolved={})), "domain_a") == (None, None)
    assert execution_target(cast(Any, _context(resolved={"domain_a": "ghost"})), "domain_a") == (
        None,
        None,
    )
    orphan = _model(endpoint_id="ghost-endpoint")
    missing_endpoint, kept_model = execution_target(cast(Any, _context(model=orphan)), "domain_a")
    assert missing_endpoint is None
    assert kept_model is not None and kept_model.id == "research_alpha"


# --------------------------------------------------- WP-B 工厂受门（AC-03/AC-05）


def _factory(*, policy: EndpointUrlPolicy, registered: bool = True) -> tuple[Any, _SpyBuilder]:
    credentials = FakeCredentialResolver()
    if registered:
        credentials.register(_CREDENTIAL_REF, _FIXTURE_KEY)
    spy = _SpyBuilder()
    return session_llm_factory(credentials, policy), spy


def test_factory_names_a_missing_execution_target(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-03：没有目标 ⇒ 点名缺的是哪一件，且**不构造 LLM**。"""
    import adapters.openhands.llm_factory as llm_factory

    build, spy = _factory(policy=EndpointUrlPolicy())
    monkeypatch.setattr(llm_factory, "build_llm", spy)

    with pytest.raises(RuntimeConfigurationError) as excinfo:
        build(_spec(None, _model()))
    assert "endpoint" in str(excinfo.value)
    assert "model" not in str(excinfo.value)
    assert spy.calls == 0

    with pytest.raises(RuntimeConfigurationError) as both_missing:
        build(_spec(None, None))
    assert "endpoint" in str(both_missing.value) and "model" in str(both_missing.value)
    assert spy.calls == 0


def test_factory_refuses_a_denied_url_before_building(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-03/AC-05：URL 被策略拒绝 ⇒ 点名 URL 与放行方式，且**不构造 LLM**。"""
    import adapters.openhands.llm_factory as llm_factory

    build, spy = _factory(policy=EndpointUrlPolicy())
    monkeypatch.setattr(llm_factory, "build_llm", spy)

    localhost = _endpoint("http://127.0.0.1:9/v1")
    with pytest.raises(RuntimeConfigurationError) as excinfo:
        build(_spec(localhost, _model()))
    message = str(excinfo.value)
    assert "http://127.0.0.1:9/v1" in message
    assert "RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS=1" in message
    assert spy.calls == 0


def test_factory_refuses_an_unresolvable_credential(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-03：凭据不可解析 ⇒ 点名 `credential_ref`（不是秘密值），且**不构造 LLM**。"""
    import adapters.openhands.llm_factory as llm_factory

    build, spy = _factory(policy=EndpointUrlPolicy(), registered=False)
    monkeypatch.setattr(llm_factory, "build_llm", spy)

    with pytest.raises(RuntimeConfigurationError) as excinfo:
        build(_spec(_endpoint(), _model()))
    message = str(excinfo.value)
    assert _CREDENTIAL_REF in message and "main" in message
    assert _FIXTURE_KEY not in message
    assert spy.calls == 0


def test_factory_builds_when_the_chain_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    """反面：链全通过 ⇒ 工厂**确实**调用 `build_llm`（拒绝用例因此不是恒真）。"""
    import adapters.openhands.llm_factory as llm_factory

    build, spy = _factory(policy=EndpointUrlPolicy())
    sentinel = object()
    seen: dict[str, Any] = {}

    def _capture(endpoint: Any, model: Any, credential: Any, **kwargs: Any) -> Any:
        seen["endpoint"] = endpoint
        seen["model"] = model
        seen["value"] = credential.value
        return sentinel

    monkeypatch.setattr(llm_factory, "build_llm", _capture)
    assert build(_spec(_endpoint(), _model())) is sentinel
    assert seen["endpoint"].id == "main"
    assert seen["model"].id == "research_alpha"
    assert seen["value"] == _FIXTURE_KEY
    assert spy.calls == 0


def test_localhost_is_allowed_when_the_policy_says_so(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-02/AC-05：策略显式放行 localhost ⇒ 同一目标通过（开发/离线 e2e 的入口）。"""
    import adapters.openhands.llm_factory as llm_factory

    credentials = FakeCredentialResolver()
    credentials.register(_CREDENTIAL_REF, _FIXTURE_KEY)
    build = session_llm_factory(credentials, EndpointUrlPolicy(allow_localhost=True))
    monkeypatch.setattr(llm_factory, "build_llm", lambda *a, **k: "llm-sentinel")
    assert build(_spec(_endpoint("http://127.0.0.1:9/v1"), _model())) == "llm-sentinel"


def test_spec_carries_the_target_without_leaking_the_secret() -> None:
    """AC-03：spec 只带 `credential_ref`（键名）——凭据值不进 spec、不进 repr。"""
    spec = _spec(_endpoint(), _model())
    assert spec.endpoint is not None and spec.model is not None
    assert spec.endpoint.credential_ref == _CREDENTIAL_REF
    assert _FIXTURE_KEY not in repr(spec)


def test_fake_path_ignores_the_new_fields() -> None:
    """AC-02 回归：Fake 执行体不看执行目标 ⇒ 默认路径行为不变。"""
    from adapters.fakes.agent_runtime import FakeAgentRuntime

    runtime = FakeAgentRuntime(structured_output={"analysis_report": {"status": "ok"}})
    handle = runtime.create_session(_spec(_endpoint(), _model()))
    result = runtime.run(handle.session_id)
    assert result.structured_output == {"analysis_report": {"status": "ok"}}


def test_resolution_is_pure_theory_free() -> None:
    """结构判据：解析器不读环境、不读文件（纯映射），因此可离线复现。"""
    source = (
        Path(__file__).resolve().parents[2]
        / "packages"
        / "application"
        / "run_orchestration"
        / "session_resolution.py"
    ).read_text(encoding="utf-8")
    assert "os.environ" not in source
    assert "getenv" not in source
    assert "session_resolution" in str(execution_target.__module__)
