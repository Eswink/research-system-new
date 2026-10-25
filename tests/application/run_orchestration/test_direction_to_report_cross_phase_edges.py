"""GOAL-20261024-096 EC-02 的**机制级**判据：六相协议的跨相边两向可判。

与 `tests/e2e/test_direction_to_report_arc_offline.py` 分工（互不替代）：

- 本文件判**机制**：改 `question` 产出 ⇒ `retrieval` 实际发给 provider 的 query 随之变
  （(i)）；把 `question` 从协议里摘掉 ⇒ **编译期**点名（(iii)）；协议声明的跨相引用与
  运行链参数路径**逐字对齐**（声明 ⇔ 消费不分叉）。
- e2e 那份判**编排**：一次完整离线 run 里 (i) 在 provider 传输层逐字成立、(ii)
  `plan` 的提示词材料随检索产出变、报告第 1 节逐字包含问题正文（EC-03 (i)）。

判据走**产品那条链**（真实出厂协议 + `execute_run_chain_capabilities` +
真实 `NcbiEutilsProvider` + `httpx.MockTransport`，离线不出网），不测夹具形状。
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from typing import Any

import httpx

from adapters.contracts.protocol_loaders import load_protocol
from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger, FakePolicyEvaluator
from adapters.fakes.workflow_engine import FakeWorkflowEngine
from adapters.research_tools import NcbiEutilsConfig, NcbiEutilsProvider
from packages.application.protocol_compile import compile_protocol
from packages.application.protocol_compile.cross_phase_inputs import (
    resolve_cross_phase_inputs,
)
from packages.application.run_orchestration.phase_capabilities import (
    CapabilityDeps,
    RunChainCall,
    execute_run_chain_capabilities,
)
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest
from packages.domain.enums import (
    ArtifactState,
    EffectClass,
    ModelBindingMode,
    ProviderType,
    RoleCategory,
    TrustLabel,
    TrustLevel,
)
from packages.domain.protocols import CompileFindingCode, FindingSeverity
from packages.domain.tasks import ResearchTask
from packages.domain.tools import ToolProviderSpec

_PROTOCOL = "direction_to_report_v1.yaml"
_PRODUCER = "question"
_READER = "retrieval"
_ARTIFACT = "research_question"
_RUN = "6c4e1a90-3b62-4f18-9a55-0d2e6b8c4a17"
_QUERY_A = "retrieval augmented hypothesis generation"
_QUERY_B = "systematic review automation pipeline"
_SPEC_IDS = ["39000101", "39000102"]
_SEARCH_JSON = {"esearchresult": {"count": str(len(_SPEC_IDS)), "idlist": list(_SPEC_IDS)}}
_EFETCH_XML = (
    b'<?xml version="1.0" encoding="UTF-8"?><PubmedArticleSet><PubmedArticle>'
    b"<MedlineCitation><PMID>39000101</PMID><Article><ArticleTitle>t</ArticleTitle>"
    b"<Journal><Title>J</Title></Journal></Article></MedlineCitation>"
    b"</PubmedArticle></PubmedArticleSet>"
)

PROVIDER_SPEC = ToolProviderSpec(
    id="ncbi_eutils",
    kind=ProviderType.REST,
    trust_level=TrustLevel.VERIFIED,
    capabilities=["literature.search", "literature.read"],
    effect_class=EffectClass.READ_ONLY,
    network_domains=["eutils.ncbi.nlm.nih.gov"],
)


def _handler(queries: list[str]) -> Callable[[httpx.Request], httpx.Response]:
    """记录**真正发给 provider 的 query**（判据据此证明检索词来自上游产出）。"""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("esearch.fcgi"):
            queries.append(request.url.params.get("term", ""))
            return httpx.Response(200, json=_SEARCH_JSON)
        return httpx.Response(200, content=_EFETCH_XML)

    return handler


def _provider(store: FakeArtifactStore, queries: list[str]) -> NcbiEutilsProvider:
    return NcbiEutilsProvider(
        store,
        config=NcbiEutilsConfig(min_request_interval_seconds=0.0),
        http_client=httpx.Client(transport=httpx.MockTransport(_handler(queries))),
        spill_threshold_bytes=1,
    )


def _calls() -> tuple[RunChainCall, ...]:
    """出厂装配对**本协议 retrieval 相**声明的两步链（检索词只来自上游问题）。"""
    return (
        RunChainCall(
            provider_id="ncbi_eutils",
            tool_id="literature_search",
            capability="literature.search",
            arguments_from_input=("research_question.query",),
            fixed_arguments={"retmax": 2},
            phase_id=_READER,
        ),
        RunChainCall(
            provider_id="ncbi_eutils",
            tool_id="literature_read",
            capability="literature.read",
            ids_from_previous="ids",
            phase_id=_READER,
        ),
    )


def _spec() -> SessionSpecContext:
    from packages.domain.enums import ActivationPolicy as _Policy
    from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition

    return SessionSpecContext(
        role=RoleDefinition(
            id="domain_researcher",
            role_type="domain_researcher",
            category=RoleCategory.DISCOVERY,
            activation_default=_Policy.ALWAYS,
        ),
        agent=AgentSpec(
            id="agent-1",
            role="domain_researcher",
            model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="model-1"),
        ),
        frozen_manifest_digest="manifest-digest",
        frozen_tool_set=("ncbi_eutils",),
        run_chain_tool_ids=("ncbi_eutils",),
        phase_id=_READER,
        cross_phase_inputs=(_compiled_cross_phase()),
    )


def _put(store: FakeArtifactStore, artifact_id: str, payload: dict[str, object]) -> None:
    content = json.dumps(payload).encode("utf-8")
    store.put(
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            created_by="agent:producer",
            classification="execution_result",
        ),
        content,
    )
    store.mark(artifact_id, ArtifactState.VERIFIED)


class _Scene:
    """一个 run 的受控现场：workflow 里登记**上游任务**，store 里放**上游产物**。"""

    def __init__(self, question: dict[str, object]) -> None:
        self.task = ResearchTask(
            id=ID.generate(),
            run_id=ID(_RUN),
            contract_id="research_question_retrieval",
            idempotency_key=f"{_RUN}:{_READER}:agent-1",
        )
        self.producer = ResearchTask(
            id=ID.generate(),
            run_id=self.task.run_id,
            contract_id="research_question_proposal",
            idempotency_key=f"{_RUN}:{_PRODUCER}:agent-1",
        )
        self.workflow = FakeWorkflowEngine()
        self.workflow.submit(self.producer, _contract("research_question_proposal"))
        self.store = FakeArtifactStore()
        self.artifact_id = f"{self.producer.id.value}:{_ARTIFACT}"
        _put(self.store, self.artifact_id, question)

    def deps(self, queries: list[str]) -> CapabilityDeps:
        return CapabilityDeps(
            calls=_calls(),
            providers={"ncbi_eutils": _provider(self.store, queries)},
            provider_specs={"ncbi_eutils": PROVIDER_SPEC},
            policy=FakePolicyEvaluator(),
            artifacts=self.store,
            ledger=FakeEvidenceLedger(),
            workflow=self.workflow,
        )


def _contract(contract_id: str) -> Any:
    from packages.domain.enums import AcceptanceCriterionType
    from packages.domain.tasks import AcceptanceCriterion, TaskContract

    return TaskContract(
        id=contract_id,
        version="1.0.0",
        purpose="test",
        acceptance_criteria=[
            AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS, artifact="x")
        ],
    )


def _compiled_cross_phase() -> tuple[tuple[str, str, TrustLabel], ...]:
    """出厂协议 retrieval 相的编译期跨相引用（真实产品路径，不手写）。"""
    protocol = load_protocol(f"examples/protocols/{_PROTOCOL}")
    from services.api.catalog import load_catalog_snapshot, load_project_settings

    result = compile_protocol(protocol, load_catalog_snapshot(), load_project_settings())
    assert result.plan is not None, result.findings
    retrieval = next(phase for phase in result.plan.phases if phase.id == _READER)
    return tuple((item[0], item[1], item[2]) for item in retrieval.cross_phase_inputs)


# ------------------------------------------------- (i) 换产出 ⇒ 换检索词


def test_a_different_question_changes_the_query_the_provider_receives() -> None:
    """两个变体各自检索**自己那份**问题里的 query（同源读出，不是配置常量）。"""
    seen: list[tuple[str, str]] = []
    for query in (_QUERY_A, _QUERY_B):
        scene = _Scene({"query": query, "rationale": "the direction implies this"})
        queries: list[str] = []
        outcome = execute_run_chain_capabilities(scene.deps(queries), scene.task, _spec())
        assert outcome.failure_message is None, outcome.failure_message
        assert queries == [query], (query, queries)
        seen.append((query, queries[0]))
    # 两向取证的核心一行：两个变体的检索词**不同**，且各自等于自己的产出。
    assert seen[0][0] != seen[1][0]
    assert seen[0][1] == seen[0][0] and seen[1][1] == seen[1][0]


def test_the_declared_reference_and_the_argument_path_align() -> None:
    """协议声明的跨相引用与运行链参数路径**逐字对齐**（声明 ⇔ 消费不分叉）。"""
    cross_phase = _compiled_cross_phase()
    assert cross_phase == ((_PRODUCER, _ARTIFACT, TrustLabel.RETRIEVED),)
    producer, artifact, _label = cross_phase[0]
    search_call = next(call for call in _calls() if call.tool_id == "literature_search")
    assert search_call.arguments_from_input == (f"{artifact}.query",)
    assert search_call.phase_id == _READER
    assert producer == _PRODUCER


# ------------------------------------------------- (iii) 摘掉上游 ⇒ 编译期点名


def test_removing_the_question_phase_fails_at_compile_time() -> None:
    """把 `question` 从协议里摘掉 ⇒ 编译期 `CROSS_PHASE_INPUT_INVALID`（不静默降级）。"""
    protocol = load_protocol(f"examples/protocols/{_PROTOCOL}")
    tampered = replace(
        protocol,
        phases=[phase for phase in protocol.phases if phase.id != _PRODUCER],
    )
    from services.api.catalog import load_catalog_snapshot

    resolution = resolve_cross_phase_inputs(tampered, load_catalog_snapshot())
    failures = [
        finding
        for finding in resolution.findings
        if finding.code == CompileFindingCode.CROSS_PHASE_INPUT_INVALID.value
        and finding.severity is FindingSeverity.ERROR
    ]
    assert failures, [finding.message for finding in resolution.findings]
    joined = " ".join(finding.message for finding in failures)
    # 摘掉产出方后检索相的引用被判「unknown phase」（点名 `question`）；若产出方在
    # 协议里但不在上游，同一条判据会点名「not upstream」。两种点名都是编译期。
    assert "question" in joined and "unknown phase" in joined, joined
