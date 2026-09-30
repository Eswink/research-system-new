"""GOAL-20260927-027 EC-02 判据 B：**注册面流程 + 三条点名反证 + 批准后的执行面**。

注册面（既有写面，本 GOAL 未改一行）：`POST /tool-provider-registrations`
⇒ `PENDING` → `POST .../approve` ⇒ `ACTIVE` → `POST .../revoke` ⇒ `REVOKED`。
本文件把 EC-02 的四种状态**真的走一遍**（MCP kind + stdio transport），并在每个状态上
断言**消费面**的后果，而不是只看注册行本身：

- `PENDING`：不进 `GET /tool-providers`、不进合并目录、不进 `tool_pack_digests`；
- `ACTIVE`：进目录（`USER_APPROVED`）、进 pin 表、协议编译的 `tool_requirements`
  里出现该 provider id ⇒ 它真的进入了运行链的候选面；
- `REVOKED`：退出目录与 pin 表（终态）。

**三条反证**（各自**点名**拒绝、**不得**静默降级）：

1. **未 pin**：provider 在目录里但 `tool_pack_digests` 没有它 ⇒ preflight 报
   `SUPPLY_CHAIN_UNPINNED`（ERROR）；补上 pin 后同一份协议不再报（成对）。写入面另有
   一层：可漂移的 `pinned_revision`（如 `v1.2.3`）在注册时就被 422 拒（既有机制）。
2. **未批准**：`PENDING` 状态下该 provider **不在**编译产物的 `tool_requirements`
   里，`require_frozen_tool_set` 对未在册的 provider **点名** `POLICY_DENIED`
   （拒绝在执行之前）；批准后同一调用通过（成对）。
3. **schema 不符**：`tests/mcp_server/raw_shapeless_tools.py`（申报一条 `name` 为空的
   工具声明）⇒ `list_tools` 抛 `TOOL_SCHEMA_MISMATCH` 且**点名**（`tool id must not be
   empty`）；`check_health` 如实收敛 `OPEN_CIRCUIT` 且不留 schema 指纹（不伪装健康）。
   另一半：调用方声明的参数本身不合规（畸形 JSON 字节）也在**触达 server 之前**被
   点名拒绝（`mcp protocol error`）。

**执行面（ACTIVE 之后）**：经 `execute_run_chain_capabilities` 用**真 MCP provider
实例** + **目录口径的 spec** 跑一次两步链（检索 → 读取），两条证据落 canonical、
`tool_refs` 指向本 provider、读取步的 id 来自检索结果本身。本 provider **不声明**
`network_domains`（stdio 离线路径运行期不触网）⇒ 来源性质如实为 `GENERATED`；
同一条链换一份**声明了**网络域的规格 ⇒ `RETRIEVED` —— 两向都在判据里，
证明该标签由**声明**决定（`_trust_label_for` 是唯一判定点），本步不自称。
"""

from __future__ import annotations

from typing import Any, cast

from fastapi.testclient import TestClient

from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger, FakePolicyEvaluator
from packages.application.ports.errors import PermanentPortError
from packages.application.preflight.preflight import run_preflight
from packages.application.protocol_compile import compile_protocol
from packages.application.run_orchestration.phase_capabilities import (
    CapabilityDeps,
    RunChainCall,
    execute_run_chain_capabilities,
)
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.application.tool_plane.execution import require_frozen_tool_set
from packages.domain.core import ID, Digest
from packages.domain.enums import (
    ActivationPolicy,
    EffectClass,
    FailureCategory,
    ModelBindingMode,
    ProviderType,
    RoleCategory,
    TrustLabel,
    TrustLevel,
)
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from packages.domain.tasks import ResearchTask
from packages.domain.tools import ToolCallRecord, ToolProviderSpec
from services.api.app import create_app
from services.api.catalog import load_catalog_snapshot
from services.api.catalog_merge import merged_catalog_snapshot, merged_project_settings
from services.api.deps import get_deps
from tests.contracts.mcp_research_support import (
    PROVIDER_ID,
    QUERY_DOCKING,
    READ_CAPABILITY,
    READ_TOOL,
    REAL_PMID,
    SEARCH_CAPABILITY,
    SEARCH_TOOL,
    SHAPELESS_FIXTURE,
    call_port,
    make_provider,
    put_raw_args,
)
from tests.contracts.test_europe_pmc_pin_and_registration import fixture_provider_ids

PIN = "sha256:" + "b" * 64
REAL_PROTOCOL = "examples/protocols/real_retrieval_research_v1.yaml"
_NETWORK_SPEC_DOMAINS = ["www.ebi.ac.uk"]


def _request(client: TestClient) -> Any:
    from starlette.requests import Request

    scope = {"type": "http", "app": client.app, "headers": [], "method": "GET", "path": "/"}
    return Request(scope)


def _client() -> TestClient:
    from tests.api.run_fixtures import make_run_ready_deps

    return TestClient(create_app(make_run_ready_deps()))


def _post(client: TestClient, path: str, seed: str, payload: dict[str, Any] | None = None) -> Any:
    return client.post(path, json=payload, headers={"Idempotency-Key": seed})


def _body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "id": PROVIDER_ID,
        "kind": "MCP",
        "capabilities": [SEARCH_CAPABILITY, READ_CAPABILITY],
        "pinned_revision": PIN,
        "transport": "stdio",
        "protocol_version": "2025-11-25",
        "health_check": True,
    }
    body.update(overrides)
    return body


def _approve(client: TestClient, seed: str) -> dict[str, Any]:
    response = _post(client, f"/tool-provider-registrations/{PROVIDER_ID}/approve", seed)
    assert response.status_code == 200, response.text
    return cast(dict[str, Any], response.json())


def _merged(client: TestClient) -> Any:
    return merged_catalog_snapshot(get_deps(_request(client)))


def _mcp_spec(*, network_domains: list[str] | None = None) -> ToolProviderSpec:
    """目录口径的同 id 规格（stdio；缺省不声明网络域 —— 离线路径运行期不触网）。"""
    return ToolProviderSpec(
        id=PROVIDER_ID,
        kind=ProviderType.MCP,
        trust_level=TrustLevel.USER_APPROVED,
        capabilities=[SEARCH_CAPABILITY, READ_CAPABILITY],
        effect_class=EffectClass.READ_ONLY,
        transport="stdio",
        network_domains=list(network_domains or []),
    )


def _call_with_raw_args(raw: bytes, operation_key: str) -> ToolCallRecord:
    """以**原始字节**构造调用：`argument_digest` 与这些字节自洽（先过防篡改关）。"""
    from tests.contracts.mcp_research_support import TASK_ID

    return ToolCallRecord(
        task_id=TASK_ID,
        attempt=1,
        operation_key=operation_key,
        tool_id=SEARCH_TOOL,
        capability=SEARCH_CAPABILITY,
        argument_digest=Digest.of_bytes(raw),
    )


def _raw_spec() -> ToolProviderSpec:
    return ToolProviderSpec(
        id="raw_fixture",
        kind=ProviderType.MCP,
        trust_level=TrustLevel.UNTRUSTED,
        capabilities=[SEARCH_CAPABILITY],
        effect_class=EffectClass.READ_ONLY,
        transport="stdio",
    )


class TestRegistrationLifecycle:
    """PENDING → ACTIVE → REVOKED：每个状态都被消费面真的看见。"""

    def test_pending_is_registered_but_invisible_to_every_consumer(self) -> None:
        with _client() as client:
            created = _post(client, "/tool-provider-registrations", "ec02-reg", _body())
            assert created.status_code == 201, created.text
            assert created.json()["state"] == "PENDING"
            assert created.json()["trust_level"] == "UNTRUSTED"
            assert created.json()["catalog_active"] is False
            catalog_ids = {item["id"] for item in client.get("/tool-providers").json()["providers"]}
            assert PROVIDER_ID not in catalog_ids
            merged = _merged(client)
            assert PROVIDER_ID not in merged.tool_providers
            assert PROVIDER_ID not in merged.tool_pack_digests

    def test_approve_makes_it_visible_with_the_user_approved_trust_level(self) -> None:
        with _client() as client:
            _post(client, "/tool-provider-registrations", "ec02-reg-2", _body())
            approved = _approve(client, "ec02-approve-2")
            assert approved["state"] == "ACTIVE"
            assert approved["trust_level"] == "USER_APPROVED"
            assert approved["catalog_active"] is True
            catalog = {
                item["id"]: item for item in client.get("/tool-providers").json()["providers"]
            }
            assert catalog[PROVIDER_ID]["trust_level"] == "USER_APPROVED"
            assert catalog[PROVIDER_ID]["kind"] == "MCP"
            assert catalog[PROVIDER_ID]["transport"] == "stdio"
            merged = _merged(client)
            assert PROVIDER_ID in merged.tool_providers
            assert merged.tool_pack_digests[PROVIDER_ID] == PIN

    def test_revoke_is_terminal_and_removes_it_from_every_consumer(self) -> None:
        with _client() as client:
            _post(client, "/tool-provider-registrations", "ec02-reg-3", _body())
            _approve(client, "ec02-approve-3")
            revoked = _post(
                client,
                f"/tool-provider-registrations/{PROVIDER_ID}/revoke",
                "ec02-revoke-3",
                {"reason": "EC-02 判据：吊销后必须退出目录与 pin 表"},
            )
            assert revoked.status_code == 200, revoked.text
            assert revoked.json()["state"] == "REVOKED"
            assert revoked.json()["trust_level"] == "REVOKED"
            merged = _merged(client)
            assert PROVIDER_ID not in merged.tool_providers
            assert PROVIDER_ID not in merged.tool_pack_digests

    def test_drift_prone_pin_is_rejected_at_the_write_face(self) -> None:
        """未 pin（可漂移字面量）在写入面就被 422 拒 —— 反证 ① 的另一半。"""
        with _client() as client:
            response = _post(
                client,
                "/tool-provider-registrations",
                "ec02-drift",
                _body(pinned_revision="v1.2.3"),
            )
            assert response.status_code == 422, response.text
            assert "digest" in response.json()["detail"]

    def test_the_fixture_pin_source_covers_the_demo_catalog_providers(self) -> None:
        """下界断言（承 MEM-160）：demo 装配的 pin 源覆盖目录内每个非 NATIVE provider。"""
        catalog = load_catalog_snapshot()
        required = {
            provider_id
            for provider_id, provider in catalog.tool_providers.items()
            if provider.kind.value != "NATIVE"
        }
        assert required, "受判集合非空是交付前提"
        fixture_ids = set(fixture_provider_ids())
        assert required <= fixture_ids, sorted(required - fixture_ids)


class TestApprovalReachesTheCompiledPlan:
    """ACTIVE 之后，协议编译真的把该 provider 放进候选面；PENDING 时不在。"""

    def _provider_ids(self, client: TestClient) -> set[str]:
        from adapters.contracts.protocol_loaders import load_protocol

        protocol = load_protocol(REAL_PROTOCOL)
        deps = get_deps(_request(client))
        result = compile_protocol(protocol, _merged(client), merged_project_settings(deps))
        assert result.plan is not None, result.findings
        return {
            provider
            for requirement in result.plan.tool_requirements
            for provider in requirement.provider_ids
        }

    def test_pending_is_absent_and_approved_joins_the_plan(self) -> None:
        with _client() as client:
            _post(client, "/tool-provider-registrations", "ec02-compile", _body())
            before = self._provider_ids(client)
            assert PROVIDER_ID not in before, "PENDING 不得进入编译产物"

            approved = _approve(client, "ec02-approve-compile")
            assert approved["state"] == "ACTIVE"
            after = self._provider_ids(client)
            assert PROVIDER_ID in after, "ACTIVE 之后必须进入编译产物"


class TestUnapprovedRefutation:
    """反证 ②：未批准 ⇒ 编译面看不到、冻结集**点名**拒绝（批准后同一调用通过）。"""

    def test_frozen_set_names_the_unapproved_provider_and_accepts_it_once_approved(self) -> None:
        plan_providers = ("m12_artifact", "ncbi_eutils")
        with_exc: PermanentPortError | None = None
        try:
            require_frozen_tool_set(plan_providers, PROVIDER_ID)
        except PermanentPortError as exc:
            with_exc = exc
        assert with_exc is not None, "不在冻结集内必须被拒"
        assert with_exc.failure_category is FailureCategory.POLICY_DENIED
        assert PROVIDER_ID in str(with_exc)
        require_frozen_tool_set((*plan_providers, PROVIDER_ID), PROVIDER_ID)  # 批准后不抛


def _pinned_catalog() -> Any:
    """受控目录：MCP provider 在册（供反证 ① 的成对断言），由调用方决定 pin 表。"""
    from dataclasses import replace

    from tests.application import protocol_fixtures

    catalog = protocol_fixtures.catalog()
    return replace(
        catalog,
        tool_providers={**catalog.tool_providers, PROVIDER_ID: _mcp_spec()},
        tool_pack_digests={},
    )


def _finding_codes(catalog: Any) -> set[str]:
    from tests.application import protocol_fixtures

    context = protocol_fixtures.context(catalog)
    result = compile_protocol(protocol_fixtures.protocol(), catalog, context.project)
    assert result.plan is not None, result.findings
    return {str(item.code) for item in run_preflight(result.plan, context).findings}


class TestUnpinnedRefutation:
    """反证 ①：目录里有 provider、pin 表里没有 ⇒ preflight **点名** `SUPPLY_CHAIN_UNPINNED`。"""

    def test_unpinned_mcp_provider_is_named_and_pinning_clears_it(self) -> None:
        from dataclasses import replace

        unpinned = _finding_codes(_pinned_catalog())
        assert "SUPPLY_CHAIN_UNPINNED" in unpinned
        pinned = _finding_codes(
            replace(_pinned_catalog(), tool_pack_digests={PROVIDER_ID: "sha256:" + "0" * 64})
        )
        assert "SUPPLY_CHAIN_UNPINNED" not in pinned, "补上 pin 后必须不再报（成对）"


class TestSchemaMismatchRefutation:
    """反证 ③：声明形状不符 / 参数不合规，各自**点名**拒绝。"""

    def test_shapeless_tool_declaration_is_rejected_by_name(self) -> None:
        provider, _store = make_provider(SHAPELESS_FIXTURE)
        with_exc: PermanentPortError | None = None
        try:
            provider.list_tools(_raw_spec())
        except PermanentPortError as exc:
            with_exc = exc
        assert with_exc is not None, "形状不符的工具声明必须被拒，不得静默丢弃"
        assert with_exc.failure_category is FailureCategory.TOOL_SCHEMA_MISMATCH
        assert "tool id must not be empty" in str(with_exc)

    def test_shapeless_fixture_reports_open_circuit_without_a_schema_digest(self) -> None:
        provider, _store = make_provider(SHAPELESS_FIXTURE)
        report = provider.check_health(_raw_spec())
        assert str(report.status) == "OPEN_CIRCUIT"
        assert report.observed_schema_digest is None, "探测失败不得留下一个 schema 指纹"

    def test_malformed_declared_arguments_are_rejected_before_the_server(self) -> None:
        """畸形 JSON 字节：digest 与字节自洽（先过防篡改那一关），在触达 server 前被拒。"""
        raw = b'{"query": '
        provider, store = make_provider()
        call = _call_with_raw_args(raw, "op-malformed")
        put_raw_args(store, call, raw)
        with_exc: PermanentPortError | None = None
        try:
            call_port(provider, _mcp_spec(), call)
        except PermanentPortError as exc:
            with_exc = exc
        assert with_exc is not None
        assert with_exc.failure_category is FailureCategory.TOOL_SCHEMA_MISMATCH
        assert "mcp protocol error" in str(with_exc)


def _chain_calls() -> tuple[RunChainCall, ...]:
    return (
        RunChainCall(
            provider_id=PROVIDER_ID,
            tool_id=SEARCH_TOOL,
            capability=SEARCH_CAPABILITY,
            fixed_arguments={"query": QUERY_DOCKING},
        ),
        RunChainCall(
            provider_id=PROVIDER_ID,
            tool_id=READ_TOOL,
            capability=READ_CAPABILITY,
            ids_from_previous="structured.ids",
        ),
    )


def _spec_context() -> SessionSpecContext:
    return SessionSpecContext(
        role=RoleDefinition(
            id="domain_researcher",
            role_type="domain_researcher",
            category=RoleCategory.DISCOVERY,
            activation_default=ActivationPolicy.ALWAYS,
        ),
        agent=AgentSpec(
            id="agent-1",
            role="domain_researcher",
            model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="model-1"),
        ),
        frozen_manifest_digest="manifest-digest",
        frozen_tool_set=("openhands_workspace", "m12_artifact", PROVIDER_ID),
        run_chain_tool_ids=(PROVIDER_ID,),
    )


def _capability_deps(
    store: FakeArtifactStore, spec: ToolProviderSpec
) -> tuple[CapabilityDeps, FakeEvidenceLedger]:
    from tests.contracts.mcp_research_support import make_provider as _mcp_provider

    provider, _ = _mcp_provider(store=store)
    ledger = FakeEvidenceLedger()
    deps = CapabilityDeps(
        calls=_chain_calls(),
        providers={PROVIDER_ID: provider},
        provider_specs={PROVIDER_ID: spec},
        policy=FakePolicyEvaluator(),
        artifacts=store,
        ledger=ledger,
    )
    return deps, ledger


class TestExecutionAfterApproval:
    """ACTIVE 之后执行面：真 provider 跑两步链；来源性质由**声明**决定（两向）。"""

    def _run(self, spec: ToolProviderSpec) -> tuple[Any, FakeEvidenceLedger, ResearchTask]:
        store = FakeArtifactStore()
        deps, ledger = _capability_deps(store, spec)
        task = ResearchTask(id=ID.generate(), run_id=ID.generate(), contract_id="research_task")
        outcome = execute_run_chain_capabilities(deps, task, _spec_context())
        return outcome, ledger, task

    def _labels(self, ledger: FakeEvidenceLedger) -> set[TrustLabel]:
        return {record.trust_label for record in ledger._sources.values()}  # noqa: SLF001

    def test_two_step_chain_registers_two_evidences_with_the_real_identifier(self) -> None:
        outcome, ledger, task = self._run(_mcp_spec())
        assert outcome.failure_message is None, outcome.failure_message
        evidences = ledger._evidence.values()  # noqa: SLF001
        by_tool = {evidence.tool_refs: evidence for evidence in evidences}
        assert set(by_tool) == {
            (PROVIDER_ID, SEARCH_TOOL),
            (PROVIDER_ID, READ_TOOL),
        }, sorted(by_tool)
        read_step = by_tool[(PROVIDER_ID, READ_TOOL)]
        assert REAL_PMID in read_step.id, read_step
        assert task.run_id.value in read_step.id
        # 不声明网络域 ⇒ 如实 GENERATED（stdio 离线快照，运行期不触网）。
        assert self._labels(ledger) == {TrustLabel.GENERATED}

    def test_declaring_network_domains_flips_the_label_to_retrieved(self) -> None:
        outcome, ledger, _task = self._run(_mcp_spec(network_domains=_NETWORK_SPEC_DOMAINS))
        assert outcome.failure_message is None, outcome.failure_message
        assert self._labels(ledger) == {TrustLabel.RETRIEVED}, (
            "同一份内容：标签由 provider 的**声明**决定，不由本步自称"
        )
