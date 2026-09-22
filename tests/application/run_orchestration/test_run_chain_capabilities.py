"""GOAL-011 EC-01 机制判据：运行链能力步真的执行了检索，并把**真实标识**带进证据链。

判据走**真实 provider**（`NcbiEutilsProvider`）+ `httpx.MockTransport`（离线、不出网，
与 `tests/contracts/test_ncbi_provider_contract.py` 同一手法）：被测量的不是"夹具长什么样"，
而是**生产那条链**——参数经 ArtifactStore → 策略（含 scope 注入）→ provider 执行 →
spill → `register_tool_evidence` 准入。

失败面（fail closed）单列：provider 未注册 / 参数缺字段 / 策略 DENY / 结果没落盘 /
不在冻结集，**没有一条**会静默降级成"没有观测但照样继续"。
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace

import httpx
import pytest

from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger, FakePolicyEvaluator
from adapters.research_tools import NcbiEutilsConfig, NcbiEutilsProvider
from packages.application.run_orchestration.phase_capabilities import (
    CapabilityDeps,
    RunChainCall,
    execute_run_chain_capabilities,
)
from packages.application.run_orchestration.result_handler import (
    ResultRegistration,
    count_retrieved_sources,
)
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest
from packages.domain.enums import (
    ActivationPolicy,
    EffectClass,
    ModelBindingMode,
    PolicyDecision,
    ProviderType,
    RoleCategory,
    TrustLabel,
    TrustLevel,
)
from packages.domain.evidence import Evidence, SourceRecord
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from packages.domain.tasks import ResearchTask
from packages.domain.tools import ToolProviderSpec

#: 检索响应里的标识（**夹具值**；live 判据用的是真实响应里的 PMID）。
_SEARCH_IDS = ["38000001", "38000002"]
_SEARCH_JSON = {"esearchresult": {"count": "2", "idlist": list(_SEARCH_IDS)}}
_EFETCH_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>38000001</PMID>
      <Article>
        <ArticleTitle>Frozen embeddings for low-resource classification</ArticleTitle>
        <Journal><Title>J Test Res</Title></Journal>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""

PROVIDER_SPEC = ToolProviderSpec(
    id="ncbi_eutils",
    kind=ProviderType.REST,
    trust_level=TrustLevel.VERIFIED,
    capabilities=["literature.search", "literature.read"],
    effect_class=EffectClass.READ_ONLY,
    network_domains=["eutils.ncbi.nlm.nih.gov"],
)

_BRIEF = {"retrieval": {"query": "reproducible research", "retmax": 2}}


def _handler(calls: list[str]) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path.rsplit("/", 1)[-1])
        if request.url.path.endswith("esearch.fcgi"):
            return httpx.Response(200, json=_SEARCH_JSON)
        return httpx.Response(200, content=_EFETCH_XML)

    return handler


def _task() -> ResearchTask:
    return ResearchTask(id=ID.generate(), run_id=ID.generate(), contract_id="research_task")


def _store_with_brief(payload: dict[str, object] | None = None) -> FakeArtifactStore:
    store = FakeArtifactStore()
    content = json.dumps(_BRIEF if payload is None else payload).encode("utf-8")
    store.put(
        Artifact(
            id="input-brief:real_research_v1",
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            created_by="composition-root",
            classification="declared-input",
        ),
        content,
    )
    return store


def _provider(store: FakeArtifactStore, calls: list[str], *, spill: int = 1) -> NcbiEutilsProvider:
    """真实 adapter，传输层换成本机 MockTransport（不出网）。

    `spill` 默认 1：运行链证据要求**内容在场**（准入会重算 digest），默认的 32KiB
    阈值会让小响应不落盘；`test_unspilled_result_fails_closed` 用默认阈值反证这一点。
    """
    return NcbiEutilsProvider(
        store,
        config=NcbiEutilsConfig(min_request_interval_seconds=0.0),
        http_client=httpx.Client(transport=httpx.MockTransport(_handler(calls))),
        spill_threshold_bytes=spill,
    )


def _spec_context(*, run_chain: tuple[str, ...] = ("ncbi_eutils",)) -> SessionSpecContext:
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
        frozen_tool_set=("openhands_workspace", "m12_artifact", "ncbi_eutils"),
        declared_input_artifacts=("input-brief:real_research_v1",),
        run_chain_tool_ids=run_chain,
    )


def _retrieval_calls() -> tuple[RunChainCall, ...]:
    return (
        RunChainCall(
            provider_id="ncbi_eutils",
            tool_id="literature_search",
            capability="literature.search",
            arguments_from_input=("retrieval.query",),
            fixed_arguments={"retmax": 2},
        ),
        RunChainCall(
            provider_id="ncbi_eutils",
            tool_id="literature_read",
            capability="literature.read",
            ids_from_previous="ids",
        ),
    )


def _deps(
    store: FakeArtifactStore,
    provider: NcbiEutilsProvider,
    *,
    policy: FakePolicyEvaluator | None = None,
) -> tuple[CapabilityDeps, FakeEvidenceLedger]:
    ledger = FakeEvidenceLedger()
    deps = CapabilityDeps(
        calls=_retrieval_calls(),
        providers={"ncbi_eutils": provider},
        provider_specs={"ncbi_eutils": PROVIDER_SPEC},
        policy=policy or FakePolicyEvaluator(),
        artifacts=store,
        ledger=ledger,
    )
    return deps, ledger


def test_run_chain_executes_retrieval_and_admits_tool_evidence() -> None:
    """两步都真的执行；两条证据落 canonical 登记面；读取步的标识来自检索结果本身。"""
    store = _store_with_brief()
    http_calls: list[str] = []
    deps, ledger = _deps(store, _provider(store, http_calls))
    task = _task()

    outcome = execute_run_chain_capabilities(deps, task, _spec_context())

    assert outcome.failure_message is None, outcome.failure_message
    assert http_calls == ["esearch.fcgi", "efetch.fcgi"], http_calls
    assert len(outcome.evidences) == 2
    search, read = outcome.evidences
    assert search.tool_refs == ("ncbi_eutils", "literature_search")
    assert read.tool_refs == ("ncbi_eutils", "literature_read")
    # 真实标识进证据链：读取步的 id 与 source_ref 里逐字带着检索返回的 PMID。
    assert _SEARCH_IDS[0] in read.id and _SEARCH_IDS[0] in read.source_ref, read
    assert read.run_id == task.run_id.value
    assert read.manifest_digest == "manifest-digest"
    spilled = read.artifact_id
    assert spilled is not None and spilled.startswith("tool-result:")
    # 内容寻址：库里的字节与 evidence 声称的 digest 一致（可复算）。
    assert Digest.of_bytes(store.get(spilled)) == Digest.parse(read.content_digest)
    # 两条来源都在 canonical 登记面（未经本模块之外的写法）。
    assert ledger.get_source(read.source_ref).origin == read.source_ref
    assert ledger.get_evidence(read.id) == read
    assert ledger.get_evidence(search.id) == search


def test_capabilities_not_declared_as_run_chain_are_not_executed() -> None:
    """声明面决定是否执行：本 phase 没声明 ⇒ **一个请求都不发**（不是"发了但没记"）。"""
    store = _store_with_brief()
    http_calls: list[str] = []
    deps, _ledger = _deps(store, _provider(store, http_calls))

    outcome = execute_run_chain_capabilities(deps, _task(), _spec_context(run_chain=()))

    assert outcome.evidences == () and outcome.failure_message is None
    assert http_calls == []


def test_missing_provider_instance_fails_closed() -> None:
    store = _store_with_brief()
    deps, _ledger = _deps(store, _provider(store, []))

    outcome = execute_run_chain_capabilities(replace(deps, providers={}), _task(), _spec_context())

    assert outcome.failure_message is not None
    assert "no registered instance" in outcome.failure_message


def test_missing_declared_query_fails_closed() -> None:
    """声明输入里没有 query ⇒ 点名失败，**不**拿空串或默认词去检索。"""
    store = _store_with_brief({"brief_id": "real_research_brief_v1", "documents": []})
    http_calls: list[str] = []
    deps, _ledger = _deps(store, _provider(store, http_calls))

    outcome = execute_run_chain_capabilities(deps, _task(), _spec_context())

    assert outcome.failure_message is not None
    assert "retrieval.query" in outcome.failure_message
    assert http_calls == []


def test_policy_deny_stops_before_the_provider() -> None:
    store = _store_with_brief()
    http_calls: list[str] = []
    policy = FakePolicyEvaluator()
    policy.set_decision("literature.search", PolicyDecision.DENY)
    deps, _ledger = _deps(store, _provider(store, http_calls), policy=policy)

    outcome = execute_run_chain_capabilities(deps, _task(), _spec_context())

    assert outcome.failure_message is not None and "policy denied" in outcome.failure_message
    assert http_calls == [], "策略拒绝不得触达 provider"


def test_unspilled_result_fails_closed() -> None:
    """结果没落盘 ⇒ 没有内容可准入 ⇒ 点名失败（不伪造 digest、不假装有观测）。"""
    store = _store_with_brief()
    http_calls: list[str] = []
    deps, _ledger = _deps(store, _provider(store, http_calls, spill=32 * 1024))

    outcome = execute_run_chain_capabilities(deps, _task(), _spec_context())

    assert outcome.failure_message is not None, outcome


def test_provider_outside_the_frozen_tool_set_is_refused() -> None:
    """ADR-0004：不在冻结集里的 provider 一律拒绝执行（声明化排除 ≠ 越权执行）。"""
    store = _store_with_brief()
    http_calls: list[str] = []
    deps, _ledger = _deps(store, _provider(store, http_calls))
    spec = replace(_spec_context(), frozen_tool_set=("openhands_workspace", "m12_artifact"))

    outcome = execute_run_chain_capabilities(deps, _task(), spec)

    assert outcome.failure_message is not None and "frozen tool set" in outcome.failure_message
    assert http_calls == []


def test_retrieved_evidence_is_stamped_by_the_provider_declaration() -> None:
    """GOAL-011 EC-02：来源性质**由 provider 的声明**决定，且落在 canonical 的 SourceRecord 上。

    本 provider 声明了 `network_domains`（真实打到 `eutils.ncbi.nlm.nih.gov`）⇒ 两条工具
    证据的来源都盖 `RETRIEVED`；「检索来源数」按 SourceRecord 判出来是 2 —— 这是覆盖判据
    的性质维度唯一认的那个数（读面 `source_trust_label` 与它同源）。
    """
    store = _store_with_brief()
    http_calls: list[str] = []
    deps, ledger = _deps(store, _provider(store, http_calls))

    outcome = execute_run_chain_capabilities(deps, _task(), _spec_context())

    assert outcome.failure_message is None, outcome.failure_message
    labels = {ledger.get_source(item.source_ref).trust_label for item in outcome.evidences}
    assert labels == {TrustLabel.RETRIEVED}, labels
    assert count_retrieved_sources(ledger, outcome.evidences) == 2


def test_local_provider_evidence_is_not_stamped_retrieved() -> None:
    """反向：provider **没有**声明外部网络域 ⇒ 不得自称「系统取得」（`GENERATED`）。"""
    store = _store_with_brief()
    http_calls: list[str] = []
    deps, ledger = _deps(store, _provider(store, http_calls))
    local = replace(PROVIDER_SPEC, network_domains=[])
    deps = replace(deps, provider_specs={"ncbi_eutils": local})

    outcome = execute_run_chain_capabilities(deps, _task(), _spec_context())

    assert outcome.failure_message is None, outcome.failure_message
    labels = {ledger.get_source(item.source_ref).trust_label for item in outcome.evidences}
    assert labels == {TrustLabel.GENERATED}, labels
    assert count_retrieved_sources(ledger, outcome.evidences) == 0


def test_model_self_report_is_not_counted_as_a_retrieved_source() -> None:
    """「计数 ≥ 1」不能代替来源性质：模型自述的证据再多，检索来源数仍是 0。

    构造的是**会话自述证据**的形状（`GENERATED` 来源 + 指向它的 evidence），
    与 `register_session_result` 落盘的那一类同形；本判据证明的是**门看的那个数**
    只由来源性质决定——证据条数不参与。
    """
    ledger = FakeEvidenceLedger()
    ledger.register_source(
        SourceRecord(
            origin="task-1:analysis_report",
            content_digest="0" * 64,
            trust_label=TrustLabel.GENERATED,
        )
    )
    self_reported = Evidence(
        id="evidence:task-1:analysis_report",
        source_ref="task-1:analysis_report",
        content_digest="0" * 64,
        run_id="run-1",
    )
    ledger.register_evidence(self_reported)

    assert count_retrieved_sources(ledger, (self_reported,)) == 0
    # 而同一个门在「总数」这一维上仍然看到它（两维并存，互不顶替）。
    assert ResultRegistration(evidence=(self_reported,)).evidence_source_count == 1


def test_retrieved_count_is_unknown_without_a_ledger() -> None:
    """没有 ledger ⇒ 性质数**未知**（`None`）：声明了该维度的合约据此 fail-closed 判拒。"""
    assert count_retrieved_sources(None, ()) is None


if __name__ == "__main__":  # pragma: no cover - 手动入口（判据在 pytest 里）
    raise SystemExit(pytest.main([__file__, "-q"]))
