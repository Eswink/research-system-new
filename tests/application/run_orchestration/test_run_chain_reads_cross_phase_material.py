"""GOAL-20261019-089 EC-01：**上游问题真的成为下游检索词**（双向判据）。

**判什么**（每一条都可证伪）：

1. **材料来自上游**：`A:research_question` 的产物按**产物名**进 B 的 run-chain 参数材料
   ⇒ `arguments_from_input=("research_question.query",)` 取到的是**A 写的那句话**，
   并且它逐字出现在 provider 实际收到的请求里（不是「配置里写了」）。
2. **换产出 ⇒ 换 query**：同一份协议、只改 A 的产出 ⇒ 两个变体的检索词**不同**，
   且各自等于自己那一份产出里的 `query`。
3. **摘掉 A ⇒ 编译期点名**：B 的 `inputs` 指向一个不存在的产出方 ⇒ 编译期
   `CROSS_PHASE_INPUT_INVALID`（**不是**运行期静默用默认值）。
4. **零回归**：未声明跨相输入的 phase ⇒ 参数材料**逐字节**等于拆出前的实现
   （只有本地声明输入），且 `resolve_cross_phase_material` 提前返回空。

判据走**产品那条链**（`execute_run_chain_capabilities` + 真实 `NcbiEutilsProvider` +
`httpx.MockTransport`，离线不出网），不测夹具形状。
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx

from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger, FakePolicyEvaluator
from adapters.fakes.workflow_engine import FakeWorkflowEngine
from adapters.research_tools import NcbiEutilsConfig, NcbiEutilsProvider
from packages.application.protocol_compile.cross_phase_inputs import (
    resolve_cross_phase_inputs,
)
from packages.application.run_orchestration.phase_capabilities import (
    CapabilityDeps,
    RunChainCall,
    execute_run_chain_capabilities,
)
from packages.application.run_orchestration.phase_input_material import (
    CrossPhaseMaterial,
    declared_object,
    input_material,
    resolve_cross_phase_material,
)
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest
from packages.domain.enums import (
    ActivationPolicy,
    ArtifactState,
    EffectClass,
    ModelBindingMode,
    ProviderType,
    RoleCategory,
    TrustLabel,
    TrustLevel,
)
from packages.domain.protocols import (
    CapabilityExecution,
    PhaseStrategy,
    ProtocolDefinition,
    ProtocolPhase,
)
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from packages.domain.tasks import ResearchTask
from packages.domain.tools import ToolProviderSpec

_PRODUCER = "question"
_READER = "retrieval"
_ARTIFACT = "research_question"
_RUN = "7a1c9e04-3b62-4f18-9a55-0d2e6b8c4a17"
_SPEC_IDS = ["38000101", "38000102"]
_SEARCH_JSON = {"esearchresult": {"count": str(len(_SPEC_IDS)), "idlist": list(_SPEC_IDS)}}
_EFETCH_XML = (
    b'<?xml version="1.0" encoding="UTF-8"?><PubmedArticleSet><PubmedArticle>'
    b"<MedlineCitation><PMID>38000101</PMID><Article><ArticleTitle>t</ArticleTitle>"
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
    """检索词**只**来自上游问题（`research_question.query`）——正是 EC-01 的形态。"""
    return (
        RunChainCall(
            provider_id="ncbi_eutils",
            tool_id="literature_search",
            capability="literature.search",
            arguments_from_input=("research_question.query",),
            fixed_arguments={"retmax": 2},
        ),
        RunChainCall(
            provider_id="ncbi_eutils",
            tool_id="literature_read",
            capability="literature.read",
            ids_from_previous="ids",
        ),
    )


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


def _spec(
    cross_phase: tuple[tuple[str, str, TrustLabel], ...] = (
        (_PRODUCER, _ARTIFACT, TrustLabel.GENERATED),
    ),
) -> SessionSpecContext:
    return SessionSpecContext(
        role=_ROLE,
        agent=_AGENT,
        frozen_manifest_digest="manifest-digest",
        frozen_tool_set=("ncbi_eutils",),
        run_chain_tool_ids=("ncbi_eutils",),
        cross_phase_inputs=cross_phase,
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
            contract_id="goal089_retrieval",
            idempotency_key=f"{_RUN}:{_READER}:agent-1",
        )
        self.producer = ResearchTask(
            id=ID.generate(),
            run_id=self.task.run_id,
            contract_id="goal089_question",
            idempotency_key=f"{_RUN}:{_PRODUCER}:agent-1",
        )
        self.workflow = FakeWorkflowEngine()
        self.workflow.submit(self.producer, _contract("goal089_question", "research_question"))
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


def _contract(contract_id: str, artifact: str) -> Any:
    from packages.domain.enums import AcceptanceCriterionType
    from packages.domain.tasks import AcceptanceCriterion, TaskContract

    return TaskContract(
        id=contract_id,
        version="1.0.0",
        purpose="test",
        acceptance_criteria=[
            AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS, artifact=artifact)
        ],
    )


# ------------------------------------------------- (1) 材料来自上游（正向）


def test_the_producers_question_is_the_query_the_provider_receives() -> None:
    """A 写的问题 ⇒ B 的检索词（逐字；且真的出现在出站请求里）。"""
    scene = _Scene({"query": "does retrieval improve planning?", "rationale": "gap"})
    queries: list[str] = []

    outcome = execute_run_chain_capabilities(scene.deps(queries), scene.task, _spec())

    assert outcome.failure_message is None, outcome.failure_message
    assert queries == ["does retrieval improve planning?"], queries
    # 两步都跑了：读取步的标识来自检索结果本身（既有链条未被破坏）。
    assert len(outcome.evidences) == 2


# ------------------------------------------------- (2) 换产出 ⇒ 换检索词


def test_a_different_question_changes_the_retrieval_query() -> None:
    """同一协议、只换 A 的产出 ⇒ 检索词**随之改变**（两个变体各自等于自己那份）。"""
    first = _Scene({"query": "question one"})
    second = _Scene({"query": "question two"})
    seen: dict[str, list[str]] = {"one": [], "two": []}

    for name, scene in (("one", first), ("two", second)):
        outcome = execute_run_chain_capabilities(scene.deps(seen[name]), scene.task, _spec())
        assert outcome.failure_message is None, outcome.failure_message

    assert seen["one"] == ["question one"], seen
    assert seen["two"] == ["question two"], seen
    assert seen["one"] != seen["two"], "换产出必须换检索词（否则 query 不是来自上游）"


def test_the_envelope_shape_is_unwrapped() -> None:
    """真会话的交付物是**信封**（`declared_artifact` + `content` 里的正文）⇒ 也要读得出来。

    受控夹具给的是直形态；真实 run 给的是信封 ⇒ 两种形态必须都能取到 query
    （否则判据在夹具上绿、在产品路径上红）。
    """
    scene = _Scene({
        "content": '{"query": "from the envelope", "rationale": "r"}',
        "message_count": 1,
        "declared_artifact": _ARTIFACT,
        "contract_id": "goal089_question",
    })
    queries: list[str] = []

    outcome = execute_run_chain_capabilities(scene.deps(queries), scene.task, _spec())

    assert outcome.failure_message is None, outcome.failure_message
    assert queries == ["from the envelope"], queries


# ------------------------------------------------- (3) 摘掉 A ⇒ 编译期点名


def _phase(
    phase_id: str,
    *,
    outputs: tuple[str, ...] = (),
    inputs: tuple[str, ...] = (),
    depends_on: tuple[str, ...] = (),
) -> ProtocolPhase:
    return ProtocolPhase(
        id=phase_id,
        strategy=PhaseStrategy.SINGLE_AGENT,
        depends_on=list(depends_on),
        inputs=list(inputs),
        outputs=list(outputs),
        capability_execution=CapabilityExecution.RUN_CHAIN,
        required_capabilities=["literature.search"],
    )


class _Catalog:
    def __init__(self) -> None:
        from packages.application.ports import CatalogSnapshot

        self.snapshot = CatalogSnapshot(tool_providers={PROVIDER_SPEC.id: PROVIDER_SPEC})


def _protocol(*phases: ProtocolPhase) -> ProtocolDefinition:
    from packages.domain.core import Version

    return ProtocolDefinition(id="goal089", version=Version("0.1.0"), phases=list(phases))


def test_removing_the_producer_is_named_at_compile_time() -> None:
    """**摘掉 A**（协议里没有那个 phase）⇒ 编译期点名（不留到运行期用默认值）。"""
    protocol = _protocol(
        _phase(
            _READER,
            inputs=(f"{_PRODUCER}:{_ARTIFACT}",),
        ),
    )

    resolution = resolve_cross_phase_inputs(protocol, _Catalog().snapshot)

    assert [item.code for item in resolution.findings] == ["CROSS_PHASE_INPUT_INVALID"], (
        resolution.findings
    )
    assert _PRODUCER in resolution.findings[0].message, resolution.findings[0].message
    assert resolution.for_phase(_READER) == ()


def test_declaring_the_relation_is_accepted_at_compile_time() -> None:
    """对照：A 在且是上游、且真的声明了该产物 ⇒ 编译期通过（正例，防止判据恒红）。"""
    protocol = _protocol(
        _phase(_PRODUCER, outputs=(_ARTIFACT,)),
        _phase(
            _READER,
            inputs=(f"{_PRODUCER}:{_ARTIFACT}",),
            depends_on=(_PRODUCER,),
        ),
    )

    resolution = resolve_cross_phase_inputs(protocol, _Catalog().snapshot)

    assert not resolution.findings, resolution.findings
    assert [item.artifact_name for item in resolution.for_phase(_READER)] == [_ARTIFACT]


def test_a_missing_producer_artifact_is_named_when_resolving_material() -> None:
    """声明了但产出方**没产出** ⇒ 解析材料时点名（不静默拿空材料去检索）。"""
    scene = _Scene({"query": "x"})
    scene.store = FakeArtifactStore()  # 产物不在场

    try:
        resolve_cross_phase_material(
            scene.workflow,
            scene.store,
            scene.task,
            ((_PRODUCER, _ARTIFACT, TrustLabel.GENERATED),),
        )
    except Exception as error:  # noqa: BLE001 - 判据读消息文本
        assert "not in the artifact store" in str(error), error
    else:  # pragma: no cover - 走到这里即判据失效
        raise AssertionError("缺失的上游产物必须点名失败")


# ------------------------------------------------- (4) 零回归


def test_no_cross_phase_input_keeps_the_material_byte_identical() -> None:
    """未声明跨相输入 ⇒ 材料**只**来自本地声明输入（逐字等于拆出前的实现）。"""
    store = FakeArtifactStore()
    _put(store, "input-brief:real_research_v1", {"retrieval": {"query": "local"}})
    spec = SessionSpecContext(
        role=_ROLE,
        agent=_AGENT,
        frozen_manifest_digest="d",
        declared_input_artifacts=("input-brief:real_research_v1",),
        run_chain_tool_ids=("ncbi_eutils",),
    )
    deps = CapabilityDeps(
        calls=_calls(),
        providers={},
        provider_specs={},
        policy=FakePolicyEvaluator(),
        artifacts=store,
        ledger=FakeEvidenceLedger(),
    )

    assert input_material(deps, spec) == {"retrieval": {"query": "local"}}
    assert resolve_cross_phase_material(None, store, _Task(), ()) == ()


def _Task() -> ResearchTask:
    return ResearchTask(id=ID.generate(), run_id=ID(_RUN), contract_id="c")


def test_a_colliding_name_with_different_content_is_refused() -> None:
    """本地输入与上游产物**同名不同内容** ⇒ 点名（不取后写的那个：参数会不可判）。"""
    store = FakeArtifactStore()
    _put(store, "input-brief:real_research_v1", {"research_question": {"query": "local"}})
    _put(store, "p-task:research_question", {"query": "remote"})
    spec = SessionSpecContext(
        role=_ROLE,
        agent=_AGENT,
        frozen_manifest_digest="d",
        declared_input_artifacts=("input-brief:real_research_v1",),
    )
    deps = CapabilityDeps(
        calls=_calls(),
        providers={},
        provider_specs={},
        policy=FakePolicyEvaluator(),
        artifacts=store,
        ledger=FakeEvidenceLedger(),
    )

    try:
        input_material(
            deps,
            spec,
            cross_phase=(
                CrossPhaseMaterial(
                    producer_phase_id=_PRODUCER,
                    artifact_name="research_question",
                    artifact_id="p-task:research_question",
                    trust_label=TrustLabel.GENERATED,
                ),
            ),
        )
    except Exception as error:  # noqa: BLE001 - 判据读消息文本
        assert "undecidable" in str(error), error
    else:  # pragma: no cover
        raise AssertionError("同名不同内容必须点名拒绝")


def test_declared_object_leaves_a_plain_object_untouched() -> None:
    """直形态（没有信封判别键）**原样**返回 —— 不解包、不猜（零回归的另一半）。"""
    payload = {"query": "plain"}
    assert declared_object(payload) is payload
