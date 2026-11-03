"""协议相级 `retmax`（GOAL-20261103-105 EC-03 第二步）。

**它补哪一格**：`retmax` 此前只能从**项目设置**或**进程环境**来 ⇒ 同一 run 里的两个检索相
不可能取不同深度，而「这一相该取几条」是**协议**的事。本轮给 `ProtocolPhase` /
`CompiledPhase` 加 `run_chain_arguments`，并在施加点按固定顺序取值：

    显式参数 > 协议相级 > 项目声明（仅当已声明） > RESEARCHOS_RETMAX > DEFAULT_RETMAX=3

**判据走真链路**（`retrieval_calls()` → `execute_run_chain_capabilities` → **真实
`EuropePmcProvider`** + `MockTransport`），读数取 **provider 实际发出的查询串**
（`retmax` 在 Europe PMC 的线上形态是 `pageSize`）。这不是函数签名判据：值传进
`CapabilityDeps` 却没被 `apply_retmax` 施加时，出站参数不会变。

**三条判据**（对应 EC-03 的 (i)–(iii)）：

1. 协议声明 `retmax: 5` ⇒ 出站 `pageSize == 5`；
2. **反证**：协议不声明 ⇒ 逐字节回到第一步修完后的行为（项目 / env / 默认各一臂）；
3. **反证**：协议声明非法值 ⇒ 点名拒绝，判词**指出是协议相级**。

**零回归**：不声明 `run_chain_arguments` 的 28 份出厂协议**一个字节都不改**
（schema 新增属性是可选的 ⇒ 既有文档加载期照旧通过）。
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, cast

import httpx
import pytest

from adapters.contracts.protocol_loaders import _phase_from_mapping, load_protocol
from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger, FakePolicyEvaluator
from adapters.research_tools.europe_pmc import EuropePmcConfig, EuropePmcProvider
from packages.application.run_orchestration.phase_call_arguments import declared_retmax
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
    TrustLevel,
)
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from packages.domain.tasks import ResearchTask
from packages.domain.tools import ToolProviderSpec
from services.api.retrieval_wiring import (
    EUROPE_PMC_ID,
    MAX_RETMAX,
    RETMAX_ENV,
    retrieval_calls,
)

_PROTOCOL = "examples/protocols/direction_to_manuscript_v1.yaml"

#: 检索响应的最小合法形态（`normalize_search` 要 `resultList.result` 是列表）。
_SEARCH_BODY = {
    "hitCount": 1,
    "resultList": {
        "result": [
            {
                "pmid": "38000001",
                "title": "Frozen embeddings for low-resource classification",
                "authorString": "Doe J.",
                "journalTitle": "J Test Res",
                "pubYear": "2024",
                "doi": "10.1000/test",
            }
        ]
    },
}

PROVIDER_SPEC = ToolProviderSpec(
    id=EUROPE_PMC_ID,
    kind=ProviderType.REST,
    trust_level=TrustLevel.VERIFIED,
    capabilities=["literature.search", "literature.read"],
    effect_class=EffectClass.READ_ONLY,
    network_domains=["www.ebi.ac.uk"],
)
_BRIEF = {"research_question": {"query": "reproducible research"}}


class _Recorded:
    """provider 实际收到的请求参数（出站面的读数）。"""

    def __init__(self) -> None:
        self.searches: list[dict[str, str]] = []


def _handler(recorded: _Recorded) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        params = dict(request.url.params)
        if "query" in params:
            recorded.searches.append(params)
            return httpx.Response(200, json=_SEARCH_BODY)
        return httpx.Response(200, json=_SEARCH_BODY)

    return handler


def _store() -> FakeArtifactStore:
    store = FakeArtifactStore()
    content = json.dumps(_BRIEF).encode("utf-8")
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


def _spec(*, run_chain_arguments: dict[str, object] | None) -> SessionSpecContext:
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
        frozen_tool_set=(EUROPE_PMC_ID,),
        declared_input_artifacts=("input-brief:real_research_v1",),
        run_chain_tool_ids=(EUROPE_PMC_ID,),
        # `retrieval_calls()` 的两条调用都标了 `phase_id="retrieval"` ⇒ 本相必须是它，
        # 否则 `_planned_in_this_phase` 把它们全过滤掉（那会让本文件静默测到「零调用」）。
        phase_id="retrieval",
        run_chain_arguments=run_chain_arguments,
    )


def _run(
    *, run_chain_arguments: dict[str, object] | None, project_retmax: int | None = None
) -> tuple[Any, _Recorded]:
    """走**真实链路**：真实 provider + MockTransport（离线），读数取出站查询串。"""
    store = _store()
    recorded = _Recorded()
    provider = EuropePmcProvider(
        store,
        config=EuropePmcConfig(min_request_interval_seconds=0.0),
        http_client=httpx.Client(transport=httpx.MockTransport(_handler(recorded))),
        spill_threshold_bytes=1,
    )
    deps = CapabilityDeps(
        calls=retrieval_calls(),
        providers={EUROPE_PMC_ID: provider},
        provider_specs={EUROPE_PMC_ID: PROVIDER_SPEC},
        policy=FakePolicyEvaluator(),
        artifacts=store,
        ledger=FakeEvidenceLedger(),
        retmax=project_retmax,
    )
    task = ResearchTask(id=ID.generate(), run_id=ID.generate(), contract_id="research_task")
    return (
        execute_run_chain_capabilities(deps, task, _spec(run_chain_arguments=run_chain_arguments)),
        recorded,
    )


def _page_size(recorded: _Recorded) -> str:
    assert recorded.searches, "检索没有被执行（调用被 phase 过滤掉或提前失败）"
    return recorded.searches[0]["pageSize"]


def test_a_protocol_phase_value_reaches_the_outgoing_request() -> None:
    """**(i)** 协议相级 `retmax: 5` ⇒ provider 实际发出的 `pageSize` 是 `5`。"""
    outcome, recorded = _run(run_chain_arguments={"retmax": 5})
    assert outcome.failure_message is None, outcome.failure_message
    assert _page_size(recorded) == "5"


def test_the_phase_value_beats_the_project_declaration() -> None:
    """协议相级 **>** 项目声明（项目 9、协议 5 ⇒ 出站 5）。"""
    outcome, recorded = _run(run_chain_arguments={"retmax": 5}, project_retmax=9)
    assert outcome.failure_message is None, outcome.failure_message
    assert _page_size(recorded) == "5"


def test_without_a_phase_value_the_project_declaration_still_applies() -> None:
    """**(ii) 反证（项目臂）**：协议不声明 + 项目 6 ⇒ 出站 6（第一步语义逐字保留）。"""
    outcome, recorded = _run(run_chain_arguments=None, project_retmax=6)
    assert outcome.failure_message is None, outcome.failure_message
    assert _page_size(recorded) == "6"


def test_without_any_declaration_the_default_still_applies() -> None:
    """**(ii) 反证（默认臂）**：协议与项目都不声明 ⇒ 出站是出厂默认 3。"""
    outcome, recorded = _run(run_chain_arguments=None, project_retmax=None)
    assert outcome.failure_message is None, outcome.failure_message
    assert _page_size(recorded) == "3"


def test_the_environment_survives_when_the_protocol_says_nothing() -> None:
    """**(ii) 反证（env 臂）**：协议与项目都不声明 + env 10 ⇒ 出站 10。

    这一条把第二步与第一步**焊在一起**：协议相级插在「项目声明」之上，但不能把 env
    那一级压掉 —— 那正是本轮修掉的缺陷形态，不能从另一条路重新引入。
    """
    import os

    previous = os.environ.get(RETMAX_ENV)
    os.environ[RETMAX_ENV] = "10"
    try:
        outcome, recorded = _run(run_chain_arguments=None, project_retmax=None)
    finally:
        if previous is None:
            os.environ.pop(RETMAX_ENV, None)
        else:
            os.environ[RETMAX_ENV] = previous
    assert outcome.failure_message is None, outcome.failure_message
    assert _page_size(recorded) == "10"


@pytest.mark.parametrize("bad", [0, -1, MAX_RETMAX + 1, "three", True])
def test_an_illegal_phase_value_is_named_as_a_protocol_phase_value(bad: object) -> None:
    """**(iii) 反证**：协议声明非法值 ⇒ 点名拒绝，且判词**指出是协议相级**。

    五条各自点名（不合并成一句「retmax 不合法」）：同一个越界值来自 env / 项目面时
    有各自的判据与措辞 —— 混起来就没人能从判词知道该改哪里。
    """
    with pytest.raises(Exception) as caught:
        declared_retmax({"retmax": bad})
    message = str(caught.value)
    assert "protocol phase" in message, message
    assert "retmax" in message, message


def test_a_non_mapping_declaration_is_named() -> None:
    """`run_chain_arguments` 不是映射 ⇒ 点名（不静默当成「没声明」）。"""
    with pytest.raises(Exception) as caught:
        declared_retmax(["retmax", 5])
    assert "must be a mapping" in str(caught.value)


def test_an_absent_key_is_undeclared_not_zero() -> None:
    """缺键 ⇒ `None`（**未声明**），不是 0 —— 声明了别的键不等于声明了 retmax。"""
    assert declared_retmax({"other": 1}) is None
    assert declared_retmax(None) is None
    assert declared_retmax({}) is None


# --------------------------------------------------------- 解析面：协议文档 → 领域 → 编译


def test_the_loader_carries_the_declaration_onto_the_phase() -> None:
    """**声明面**：`run_chain_arguments` 从 YAML 进 `ProtocolPhase`（缺键 ⇒ `None`）。"""
    with_declaration = _phase_from_mapping({
        "id": "retrieval",
        "strategy": "single_agent",
        "run_chain_arguments": {"retmax": 5},
    })
    without = _phase_from_mapping({"id": "retrieval", "strategy": "single_agent"})
    assert with_declaration.run_chain_arguments == {"retmax": 5}
    assert without.run_chain_arguments is None, "缺键必须是 None（未声明），不是空字典"


def test_the_compiler_carries_it_onto_the_compiled_phase() -> None:
    """**编译面**：`CompiledPhase.run_chain_arguments` 原样携带（编译不解释它）。

    两向：① 声明的相符价值必须出现在编译结果里（真的搬了）；② 出厂协议的十一相
    全是 `None` —— 这是「28 份协议文档一个字节都没改」的机械证据。

    用 `_compiled_phases` 而不是 `compile_protocol`：本判据问的是「字段有没有被搬过去」，
    不是「这份协议能不能过全量编译」（后者要整个 catalog，与本字段无关）。
    """
    from packages.application.protocol_compile.compiler import _compiled_phases
    from packages.application.protocol_compile.cross_phase_inputs import CrossPhaseResolution

    empty_cross = CrossPhaseResolution(by_phase={}, findings=())

    phase = _phase_from_mapping({
        "id": "retrieval",
        "strategy": "single_agent",
        "run_chain_arguments": {"retmax": 7},
    })
    protocol = cast(Any, type("P", (), {"phases": [phase]})())
    compiled = _compiled_phases(protocol, ("retrieval",), empty_cross)
    assert len(compiled) == 1
    assert compiled[0].run_chain_arguments == {"retmax": 7}, (
        "编译器必须原样携带相级参数（搬丢了 ⇒ 协议里写的值永远到不了调用表）"
    )

    real = load_protocol(_PROTOCOL)
    ordered = tuple(item.id for item in real.phases)
    shipped = _compiled_phases(real, ordered, empty_cross)
    assert tuple(item.id for item in shipped) == ordered, "相集不许被本轮改动"
    carried = {
        item.id: item.run_chain_arguments
        for item in shipped
        if item.run_chain_arguments is not None
    }
    assert carried == {}, f"出厂协议不声明 run_chain_arguments，但有相携带了值：{carried}"


def test_the_protocol_phase_count_is_unchanged() -> None:
    """相集**一字未动**（本轮只加字段）：十一相、顺序逐字。"""
    protocol = load_protocol(_PROTOCOL)
    assert tuple(phase.id for phase in protocol.phases) == (
        "question",
        "retrieval",
        "novelty",
        "plan",
        "experiment",
        "review",
        "manuscript",
        "editorial",
        "revision",
        "submission",
        "report",
    )


def test_the_schema_accepts_the_new_property_and_still_rejects_unknown_ones() -> None:
    """**schema 面**：`run_chain_arguments` 被接受，且封闭对象语义生效（两向 + 一深层）。

    三向都判：① 新属性加进去了（不加会在**加载期**就被拒 —— 这是本靶子必须动 schema 的
    原因）；② 相级的未知键仍被拒（`additionalProperties: false` 没被顺手放开）；
    ③ **`run_chain_arguments` 内部**也是封闭的：写一个没有解释器的参数名（`topk`）在
    加载期就被点名 —— 这堵住了「键名写错但静默无效」那个缺口（GOAL 的 `W-3`）。
    """
    from adapters.contracts.base import load_json_schema, validate_instance

    schema = load_json_schema("protocol.schema.json")
    phase_def = {"$ref": "#/$defs/phase", "$defs": schema["$defs"]}
    phase_ok = {"id": "retrieval", "strategy": "single_agent", "run_chain_arguments": {"retmax": 5}}
    phase_bad = {"id": "retrieval", "strategy": "single_agent", "not_a_real_key": 1}
    unknown_argument = {
        "id": "retrieval",
        "strategy": "single_agent",
        "run_chain_arguments": {"topk": 5},
    }
    validate_instance(phase_def, phase_ok, "phase")  # 不抛 ⇒ 新属性被接受
    with pytest.raises(Exception):
        validate_instance(phase_def, phase_bad, "phase")
    with pytest.raises(Exception) as caught:
        validate_instance(phase_def, unknown_argument, "phase")
    assert "topk" in str(caught.value), (
        f"未知的相级参数名必须在加载期点名（不让它静默无效）：{caught.value}"
    )
