"""GOAL-20260927-027 EC-03 判据：**新能力接进运行链**（声明 / 真标识 / 读面 / 性质）。

**被测对象**：产品那条链 —— `capability_execution: run_chain` 的协议声明 ⇒
`RunChainCall` 三类给参 ⇒ `execute_run_chain_capabilities`（策略 + 冻结集 + 真 provider）
⇒ `register_tool_evidence` 准入 ⇒ `GET /runs/{id}/evidence` 读面。

**本 EC 的净增量**（相对既有 `test_run_chain_retrieval_offline.py`）：那条判据把
`ncbi_eutils` 接进链（GOAL-011）；本文件把**两个新能力来源**接进链 ——
`europe_pmc`（EC-01 新增的第二个真实文献源）与自建 MCP server（EC-02）——
并断言**同一批产品对象**上的五件事：

1. **声明在树且进编译产物**：新协议 `real_literature_chain_v1.yaml` 的
   `capability_execution: run_chain` + `plan.tool_requirements.provider_ids` 含 `europe_pmc`；
2. **三类给参各自正反向**：`arguments_from_input`（brief 的 `retrieval.query`）/
   `fixed_arguments`（`retmax`）/ `ids_from_previous`（检索结果里的**真 PMID**）——
   正向断言真的取到并发给 provider（离线传输里可见），反向断言缺一即点名拒绝、零请求；
3. **`trust_label` 由声明决定（唯一判定点）**：`europe_pmc` 声明了 `network_domains`
   ⇒ `RETRIEVED`；同一份内容换一份**不声明**网络域的 spec ⇒ `GENERATED`；
4. **读面四列可见**（本 EC 的核心）：一次离线 run 里 ≥2 条真 PMID 来源经
   `GET /runs/{id}/evidence` 读到 `id` / `source_ref` / `content_digest` /
   `source_trust_label` 四列与 `tool_refs`；run 收敛 `SUCCEEDED`（覆盖判据**两维**都过）；
5. **反证**：不接能力步 ⇒ 零工具观测 ⇒ 覆盖判据判拒 ⇒ run `FAILED`（判词点名
   「检索来源」这一维）。

MCP 侧另有一例：`structured.ids` 点分路径（EC-02 的信封）在**同一条产品链**上取到 id。
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import httpx
import yaml
from fastapi.testclient import TestClient

from adapters.contracts.protocol_loaders import load_protocol
from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger, FakePolicyEvaluator
from adapters.research_tools import EuropePmcConfig, EuropePmcProvider
from packages.application.protocol_compile import compile_protocol
from packages.application.run_orchestration.phase_capabilities import (
    CapabilityDeps,
    execute_run_chain_capabilities,
)
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest
from packages.domain.enums import (
    ActivationPolicy,
    EffectClass,
    ModelBindingMode,
    ProviderType,
    RoleCategory,
    TrustLabel,
    TrustLevel,
)
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from packages.domain.tasks import ResearchTask
from packages.domain.tools import ToolProviderSpec
from services.api.app import create_app
from services.api.catalog_merge import merged_catalog_snapshot, merged_project_settings
from services.api.deps import get_deps
from tests.api.run_fixtures import make_run_ready_deps
from tests.contracts.mcp_research_support import PROVIDER as MCP_SPEC
from tests.contracts.mcp_research_support import make_provider as make_mcp_provider
from tests.e2e.literature_chain_support import (
    BRIEF_QUERY,
    DECLARED_BRIEF,
    EC03_PROTOCOL,
    EUROPE_PMC_ID,
    EUROPEPMC_CAPABILITIES,
    MCP_PROVIDER_ID,
    REAL_PMID_PRIMARY,
    REAL_PMID_SECONDARY,
    OfflineEuropePmc,
    capabilities_for,
    europepmc_calls,
    europepmc_run_chain_provider,
    mcp_calls,
    with_capabilities,
)
from tests.e2e.live_run_support import openhands_deps, run_failures, start_run
from tests.e2e.test_ec03_real_runtime_offline_chain import mock_relay

__all__ = ["mock_relay"]

_ROLE = RoleDefinition(
    id="domain_researcher",
    role_type="domain_researcher",
    category=RoleCategory.DISCOVERY,
    activation_default=ActivationPolicy.ALWAYS,
)
_AGENT = AgentSpec(
    id="agent-1",
    role="domain_researcher",
    model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="model-1"),
)


def _spec_context(run_chain: tuple[str, ...], tools: tuple[str, ...]) -> SessionSpecContext:
    return SessionSpecContext(
        role=_ROLE,
        agent=_AGENT,
        frozen_manifest_digest="manifest-digest",
        frozen_tool_set=tools,
        declared_input_artifacts=(DECLARED_BRIEF,),
        run_chain_tool_ids=run_chain,
    )


def _store_with_brief(payload: Mapping[str, object] | None = None) -> FakeArtifactStore:
    store = FakeArtifactStore()
    body: object = payload if payload is not None else {"retrieval": {"query": BRIEF_QUERY}}
    content = json.dumps(body).encode("utf-8")
    store.put(
        Artifact(
            id=DECLARED_BRIEF,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            created_by="composition-root",
            classification="declared-input",
        ),
        content,
    )
    return store


def _task() -> ResearchTask:
    return ResearchTask(id=ID.generate(), run_id=ID.generate(), contract_id="research_task")


def _europepmc_spec(*, network_domains: list[str] | None) -> ToolProviderSpec:
    """与目录声明同形的 spec（`network_domains` 由调用方决定：AC-3 的两向靠它）。"""
    domains = ["www.ebi.ac.uk"] if network_domains is None else network_domains
    return ToolProviderSpec(
        id=EUROPE_PMC_ID,
        kind=ProviderType.REST,
        trust_level=TrustLevel.VERIFIED,
        capabilities=list(EUROPEPMC_CAPABILITIES),
        effect_class=EffectClass.READ_ONLY,
        transport="rest",
        network_domains=domains,
    )


def _capability_deps(
    store: FakeArtifactStore, transport: OfflineEuropePmc, *, spec: ToolProviderSpec
) -> tuple[CapabilityDeps, FakeEvidenceLedger]:
    provider = EuropePmcProvider(
        store,
        config=EuropePmcConfig(min_request_interval_seconds=0.0),
        http_client=transport.client(),
        spill_threshold_bytes=1,
    )
    ledger = FakeEvidenceLedger()
    deps = CapabilityDeps(
        calls=europepmc_calls(),
        providers={EUROPE_PMC_ID: provider},
        provider_specs={EUROPE_PMC_ID: spec},
        policy=FakePolicyEvaluator(),
        artifacts=store,
        ledger=ledger,
    )
    return deps, ledger


def _labels(ledger: FakeEvidenceLedger) -> set[TrustLabel]:
    return {record.trust_label for record in ledger._sources.values()}  # noqa: SLF001


class TestDeclarationReachesTheCompiledPlan:
    """AC-1：声明不是散文 —— 它在 YAML 里，也在编译产物里。"""

    def test_the_protocol_declares_run_chain_in_the_document_itself(self) -> None:
        raw = yaml.safe_load(
            Path(f"examples/protocols/{EC03_PROTOCOL}").read_text(encoding="utf-8")
        )
        phase = raw["phases"][0]
        assert phase["capability_execution"] == "run_chain"
        assert set(phase["required_capabilities"]) >= {"literature.search", "literature.read"}

    def test_the_plan_carries_the_new_provider_in_its_tool_requirements(self) -> None:
        with TestClient(create_app(make_run_ready_deps())) as client:
            from starlette.requests import Request

            scope = {
                "type": "http",
                "app": client.app,
                "headers": [],
                "method": "GET",
                "path": "/",
            }
            deps = get_deps(Request(scope))
            result = compile_protocol(
                load_protocol(f"examples/protocols/{EC03_PROTOCOL}"),
                merged_catalog_snapshot(deps),
                merged_project_settings(deps),
            )
        assert result.plan is not None, result.findings
        providers = {
            provider
            for requirement in result.plan.tool_requirements
            for provider in requirement.provider_ids
        }
        assert EUROPE_PMC_ID in providers, result.plan.tool_requirements


class TestThreeArgumentSources:
    """AC-2：三类给参各自正向（真取到 → 真发出）+ 反向（缺一 ⇒ 点名拒绝、零请求）。"""

    def test_search_carries_the_brief_query_and_read_carries_the_searched_pmid(self) -> None:
        store = _store_with_brief()
        transport = OfflineEuropePmc(requests=[])
        deps, _ledger = _capability_deps(
            store, transport, spec=_europepmc_spec(network_domains=None)
        )

        outcome = execute_run_chain_capabilities(
            deps, _task(), _spec_context((EUROPE_PMC_ID,), ("m12_artifact", EUROPE_PMC_ID))
        )

        assert outcome.failure_message is None, outcome.failure_message
        assert len(outcome.evidences) == 2, outcome.evidences
        # 正向：第一步发出去的就是 brief 里那条 query；第二步按检索回来的**真 PMID**取。
        assert transport.requests[0] == BRIEF_QUERY, transport.requests
        assert transport.requests[1] == f"EXT_ID:{REAL_PMID_PRIMARY}", transport.requests
        assert f"EXT_ID:{REAL_PMID_SECONDARY}" in transport.requests, transport.requests

    def test_missing_declared_query_source_fails_closed_with_zero_requests(self) -> None:
        store = _store_with_brief({"retrieval": {"note": "query removed"}})
        transport = OfflineEuropePmc(requests=[])
        deps, _ledger = _capability_deps(
            store, transport, spec=_europepmc_spec(network_domains=None)
        )

        outcome = execute_run_chain_capabilities(
            deps, _task(), _spec_context((EUROPE_PMC_ID,), ("m12_artifact", EUROPE_PMC_ID))
        )

        assert outcome.failure_message is not None
        assert "retrieval.query" in outcome.failure_message
        assert transport.requests == [], "声明路径取不到值时不得发请求"

    def test_empty_search_result_leaves_the_read_step_fail_closed(self) -> None:
        """读取步的 id 只能来自检索结果本身：零命中 ⇒ 点名拒绝、不再发读取请求。"""
        store = _store_with_brief()
        transport = OfflineEuropePmc(requests=[])

        def empty_handler(request: httpx.Request) -> httpx.Response:
            transport.requests.append(request.url.params.get("query", ""))
            return httpx.Response(
                200, json={"version": "6.9", "hitCount": 0, "resultList": {"result": []}}
            )

        provider = EuropePmcProvider(
            store,
            config=EuropePmcConfig(min_request_interval_seconds=0.0),
            http_client=httpx.Client(transport=httpx.MockTransport(empty_handler)),
            spill_threshold_bytes=1,
        )
        base_deps, _ledger = _capability_deps(
            store, transport, spec=_europepmc_spec(network_domains=None)
        )
        outcome = execute_run_chain_capabilities(
            replace(base_deps, providers={EUROPE_PMC_ID: provider}),
            _task(),
            _spec_context((EUROPE_PMC_ID,), ("m12_artifact", EUROPE_PMC_ID)),
        )
        assert outcome.failure_message is not None
        assert "'ids'" in outcome.failure_message
        assert transport.requests == [BRIEF_QUERY], "零命中后不得再发读取请求"


class TestTrustLabelFollowsTheDeclaration:
    """AC-3：性质由**声明**决定（唯一判定点 `_trust_label_for`），两向都在判据里。

    两向用**两个** provider 取证，因为「不声明网络域」在两个 adapter 上是**两种真实语义**：

    - `europe_pmc` 有 URL 策略（EC-01 的净增量）：**声明**同时是运行期出口门
      ⇒ 声明为空时它在触网前**拒绝**（不是降级成 `GENERATED`，而是 fail closed）；
    - MCP provider（stdio、离线、**不声明**网络域）⇒ 如实 `GENERATED`。

    这条区别必须写在判据里，否则「声明为空 ⇒ GENERATED」会变成一条**假的**普遍断言
    （对 europe_pmc 实测为假：它拒绝）。
    """

    def _labels_for_europepmc(self, spec: ToolProviderSpec) -> tuple[set[TrustLabel], Any, Any]:
        store = _store_with_brief()
        transport = OfflineEuropePmc(requests=[])
        deps, ledger = _capability_deps(store, transport, spec=spec)
        outcome = execute_run_chain_capabilities(
            deps, _task(), _spec_context((EUROPE_PMC_ID,), ("m12_artifact", EUROPE_PMC_ID))
        )
        return _labels(ledger), outcome, transport

    def test_declared_network_domains_yield_retrieved(self) -> None:
        labels, outcome, _transport = self._labels_for_europepmc(
            _europepmc_spec(network_domains=None)
        )
        assert outcome.failure_message is None, outcome.failure_message
        assert labels == {TrustLabel.RETRIEVED}

    def test_empty_declaration_is_refused_before_any_request_not_downgraded(self) -> None:
        """实测语义：声明为空 ⇒ URL 策略在**触网前**拒绝（零请求），不是静默降级。

        若把这条读成「降级为 GENERATED」，判据就会与产品行为相反——本条把真实行为钉住。
        """
        _labels, outcome, transport = self._labels_for_europepmc(
            _europepmc_spec(network_domains=[])
        )
        assert outcome.failure_message is not None
        assert "outside the declared network_domains" in outcome.failure_message
        assert transport.requests == [], "策略拒绝必须发生在触网之前"

    def test_undeclared_stdio_provider_yields_generated(self) -> None:
        """不声明网络域的 provider（MCP、stdio、离线）⇒ 如实 `GENERATED`。"""
        store = _store_with_brief()
        provider, _ = make_mcp_provider(store=store)
        ledger = FakeEvidenceLedger()
        deps = CapabilityDeps(
            calls=mcp_calls(),
            providers={MCP_SPEC.id: provider},
            provider_specs={MCP_SPEC.id: MCP_SPEC},
            policy=FakePolicyEvaluator(),
            artifacts=store,
            ledger=ledger,
        )
        assert MCP_SPEC.network_domains == [], "MCP 声明面必须无网络域（离线路径）"
        outcome = execute_run_chain_capabilities(
            deps, _task(), _spec_context((MCP_SPEC.id,), ("m12_artifact", MCP_SPEC.id))
        )
        assert outcome.failure_message is None, outcome.failure_message
        assert _labels(ledger) == {TrustLabel.GENERATED}


class TestMcpEnvelopeChainsThroughTheSameProductPath:
    """AC-2（MCP 侧）：信封结果的点分路径在**同一批产品对象**上取到 id。"""

    def test_structured_ids_are_read_from_the_envelope(self) -> None:
        store = _store_with_brief()
        provider, _ = make_mcp_provider(store=store)
        ledger = FakeEvidenceLedger()
        deps = CapabilityDeps(
            calls=mcp_calls(),
            providers={MCP_SPEC.id: provider},
            provider_specs={MCP_SPEC.id: MCP_SPEC},
            policy=FakePolicyEvaluator(),
            artifacts=store,
            ledger=ledger,
        )
        outcome = execute_run_chain_capabilities(
            deps, _task(), _spec_context((MCP_SPEC.id,), ("m12_artifact", MCP_SPEC.id))
        )
        assert outcome.failure_message is None, outcome.failure_message
        assert len(outcome.evidences) == 2, outcome.evidences
        refs = [evidence.tool_refs for evidence in outcome.evidences]
        assert (MCP_PROVIDER_ID, "literature_read") in refs, refs


class TestReadFaceShowsTheRetrievedSources:
    """AC-4 / AC-5：读面四列可见 + 反证（不接线 ⇒ 零观测 ⇒ 覆盖判拒 ⇒ FAILED）。"""

    def _run(
        self, base_url: str, transport: OfflineEuropePmc, *, wire_chain: bool
    ) -> dict[str, Any]:
        """跑一次离线 run 并取回读面快照。

        `wire_chain=False` 是**反证面**：同一份协议、同一套装配，只去掉能力步接线 ——
        这正是既有离线判据的成对手法（此处换成本 EC 的协议与 provider）。
        """
        deps = openhands_deps(base_url, map_tools=False)
        if wire_chain:
            provider = europepmc_run_chain_provider(deps, transport)
            with_capabilities(
                deps,
                capabilities_for(
                    deps, provider_id=EUROPE_PMC_ID, provider=provider, calls=europepmc_calls()
                ),
            )
        app = create_app(deps)
        with TestClient(app) as client:
            run = start_run(client, EC03_PROTOCOL)
            evidence = cast(list[dict[str, Any]], client.get(f"/runs/{run['id']}/evidence").json())
            failures = run_failures(client, run["id"])
        return {
            "run": run,
            "evidence": evidence,
            "failures": failures,
            "transport": transport,
        }

    def test_two_real_pmids_are_readable_from_the_evidence_face(self, mock_relay: str) -> None:
        reads = self._run(mock_relay, OfflineEuropePmc(requests=[]), wire_chain=True)
        assert reads["run"]["state"] == "SUCCEEDED", (reads["run"], reads["failures"])
        tool_evidence = [item for item in reads["evidence"] if item["tool_refs"]]
        by_tool = {tuple(item["tool_refs"]): item for item in tool_evidence}
        assert set(by_tool) == {
            (EUROPE_PMC_ID, "literature_search"),
            (EUROPE_PMC_ID, "literature_read"),
        }, (tool_evidence, reads["failures"])
        read_step = by_tool[(EUROPE_PMC_ID, "literature_read")]
        # 四列：id / source_ref / content_digest / source_trust_label。
        assert read_step["id"], read_step
        assert read_step["source_ref"], read_step
        assert read_step["content_digest"], read_step
        assert read_step["source_trust_label"] == "RETRIEVED", read_step
        # 真标识进证据链（读取步读的就是检索响应里返回的那条 PMID）。
        assert REAL_PMID_PRIMARY in read_step["id"], read_step
        assert REAL_PMID_PRIMARY in read_step["source_ref"], read_step
        assert str(read_step["artifact_id"]).startswith("tool-result:"), read_step
        # ≥2 条真实来源（两条工具步骤 + 声明输入）。
        retrieved = [
            item for item in reads["evidence"] if item["source_trust_label"] == "RETRIEVED"
        ]
        assert len(retrieved) >= 2, reads["evidence"]
        declared = [
            item for item in reads["evidence"] if item["source_trust_label"] == "USER_PROVIDED"
        ]
        assert declared and all(not item["tool_refs"] for item in declared), declared

    def test_without_the_wiring_there_is_no_observation_and_coverage_is_rejected(
        self, mock_relay: str
    ) -> None:
        reads = self._run(mock_relay, OfflineEuropePmc(requests=[]), wire_chain=False)
        assert [item for item in reads["evidence"] if item["tool_refs"]] == [], reads["evidence"]
        assert reads["run"]["state"] == "FAILED", (reads["run"], reads["failures"])
        assert any("acceptance gate" in message for message in reads["failures"]), reads["failures"]
        # 判定来自**覆盖判据**（不是别的门）：判词点名缺的是「检索来源」这一维。
        assert any("retrieved sources" in message for message in reads["failures"]), reads[
            "failures"
        ]
        assert reads["transport"].requests == [], "没接线 ⇒ 一个请求都不该发"
