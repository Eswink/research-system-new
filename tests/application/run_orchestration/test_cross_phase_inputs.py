"""GOAL-20261016-081 EC-04：**跨相输入**的三条硬要求（编译期解析 / 性质来源 / 门不削弱）。

本文件判的是**结构**，不是「某次 run 能跑通」（那由 e2e/live 判据承担）：

- **(a) 形态**：`inputs` 支持 `{phase_id}:{artifact_name}`，且**编译期**就校验 ——
  解析不了的引用**点名判错**（`CROSS_PHASE_INPUT_INVALID`），不留到运行期。
- **(b) 性质不由读取方自报**：跨相输入的 `trust_label` 来自**产出方**的编译期事实
  （`capability_execution: run_chain` + provider 声明了 `network_domains` ⇒ `RETRIEVED`）。
  **按压**：把产出方的 run-chain 声明摘掉 ⇒ 性质必须变成 `GENERATED`（证明它真的由
  产出方决定，而不是被读取方或某个常量写死）。
- **(c) 反编造门**：`result_handler._input_evidence` 的**内容校验**与「组合根供给」
  这条**并列**接受「有性质的 phase 产出」—— 两条分支各自独立可判。**按压**：把跨相
  证据从登记面摘掉 ⇒ 覆盖门必须判拒（`0 < 1 retrieved`），证明它真的是一条来源。

判据只用**既有**构件（`FakeArtifactStore` / `FakeEvidenceLedger` / `FakeWorkflowEngine`），
不新造一套装配。
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger, FakeWorkflowEngine
from packages.application.protocol_compile.cross_phase_inputs import (
    is_cross_phase_reference,
    resolve_cross_phase_inputs,
)
from packages.application.run_orchestration.cross_phase_inputs import (
    CROSS_PHASE_ORIGIN_PREFIX,
    register_cross_phase_sources,
    resolve_cross_phase_sources,
)
from packages.application.run_orchestration.result_handler import (
    RegistrationDeps,
    count_retrieved_sources,
    register_session_result,
)
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest
from packages.domain.enums import ArtifactState, TrustLabel
from packages.domain.evidence import SourceRecord
from packages.domain.protocols import (
    CapabilityExecution,
    PhaseStrategy,
    ProtocolDefinition,
    ProtocolPhase,
)
from packages.domain.roles import AgentSpec, RoleDefinition
from packages.domain.tasks import ResearchTask

_PRODUCER = "scouting"
_READER = "plan"
_ARTIFACT = "scouting_report"


def _phase(
    phase_id: str,
    *,
    outputs: tuple[str, ...] = (),
    inputs: tuple[str, ...] = (),
    depends_on: tuple[str, ...] = (),
    run_chain: bool = False,
) -> ProtocolPhase:
    return ProtocolPhase(
        id=phase_id,
        strategy=PhaseStrategy.SINGLE_AGENT,
        depends_on=list(depends_on),
        inputs=list(inputs),
        outputs=list(outputs),
        capability_execution=(
            CapabilityExecution.RUN_CHAIN if run_chain else CapabilityExecution.SESSION
        ),
        required_capabilities=["literature.search"] if run_chain else [],
    )


def _protocol(*phases: ProtocolPhase) -> ProtocolDefinition:
    return ProtocolDefinition(id="cross-phase-test", version=_version(), phases=list(phases))


def _version() -> Any:
    from packages.domain.core import Version

    return Version("0.1.0")


class _Catalog:
    """最小目录：一个 provider（声明 `network_domains`）+ 一份契约。"""

    def __init__(self, *, network: bool = True, report_executor: bool = False) -> None:
        from packages.application.ports import CatalogSnapshot
        from packages.domain.enums import ProviderType, TrustLevel
        from packages.domain.tools import ToolProviderSpec

        self.snapshot = CatalogSnapshot(
            tool_providers={
                "europe_pmc": ToolProviderSpec(
                    id="europe_pmc",
                    kind=ProviderType.REST,
                    trust_level=TrustLevel.VERIFIED,
                    capabilities=["literature.search"],
                    network_domains=["www.ebi.ac.uk"] if network else [],
                )
            },
            task_contracts={},
        )


# ---------------------------------------------------------------- (a) 编译期解析


def test_a_cross_phase_reference_resolves_to_producer_and_artifact() -> None:
    """`{phase}:{artifact}` → `(产出方, 产物名, 性质)`，且本地输入**原样**留在 `inputs`。

    性质在这里就是 `RETRIEVED`：产出方 `scouting` 声明了 `run_chain` 且它的 provider
    声明了 `network_domains`（与 `phase_capabilities._trust_label_for` 同一口径）。
    """
    protocol = _protocol(
        _phase(_PRODUCER, outputs=(_ARTIFACT,), run_chain=True),
        _phase(
            _READER,
            inputs=("input-brief:real_research_v1", f"{_PRODUCER}:{_ARTIFACT}"),
            depends_on=(_PRODUCER,),
        ),
    )
    resolution = resolve_cross_phase_inputs(protocol, _Catalog().snapshot)

    assert not resolution.findings, resolution.findings
    resolved = resolution.for_phase(_READER)
    assert [(item.producer_phase_id, item.artifact_name) for item in resolved] == [
        (_PRODUCER, _ARTIFACT)
    ]
    assert resolved[0].trust_label is TrustLabel.RETRIEVED
    # 组合根供给那一类**不**被误判成跨相引用。
    assert is_cross_phase_reference(protocol, "input-brief:real_research_v1") is False
    assert is_cross_phase_reference(protocol, f"{_PRODUCER}:{_ARTIFACT}") is True


def test_a_misspelled_producer_is_named_at_compile_time() -> None:
    """**产物名对上了、产出方写错** ⇒ 编译期点名（不留到运行期）。"""
    protocol = _protocol(
        _phase(_PRODUCER, outputs=(_ARTIFACT,), run_chain=True),
        _phase(_READER, inputs=(f"scoutting:{_ARTIFACT}",), depends_on=(_PRODUCER,)),
    )
    resolution = resolve_cross_phase_inputs(protocol, _Catalog().snapshot)

    assert [item.code for item in resolution.findings] == ["CROSS_PHASE_INPUT_INVALID"]
    assert "scoutting" in resolution.findings[0].message, resolution.findings[0].message
    assert resolution.for_phase(_READER) == ()


def test_a_downstream_only_reference_is_refused() -> None:
    """引用**不是自己上游**的 phase ⇒ 编译期点名（执行顺序保证不了产物在场）。"""
    protocol = _protocol(
        _phase(_PRODUCER, outputs=(_ARTIFACT,), run_chain=True),
        _phase(_READER, inputs=(f"{_PRODUCER}:{_ARTIFACT}",)),  # 没有 depends_on
    )
    resolution = resolve_cross_phase_inputs(protocol, _Catalog().snapshot)

    assert [item.code for item in resolution.findings] == ["CROSS_PHASE_INPUT_INVALID"]
    assert "not upstream" in resolution.findings[0].message, resolution.findings[0].message


def test_a_dropped_or_unknown_artifact_name_is_refused() -> None:
    """产出方从不承诺那个产物名 ⇒ 编译期点名（读的是「不存在的东西」）。"""
    protocol = _protocol(
        _phase(_PRODUCER, outputs=("something_else",), run_chain=True),
        _phase(_READER, inputs=(f"{_PRODUCER}:{_ARTIFACT}",), depends_on=(_PRODUCER,)),
    )
    resolution = resolve_cross_phase_inputs(protocol, _Catalog().snapshot)

    assert [item.code for item in resolution.findings] == ["CROSS_PHASE_INPUT_INVALID"]
    assert "does not declare output" in resolution.findings[0].message


def test_an_ambiguous_artifact_is_refused() -> None:
    """两个上游都声明同名产物 ⇒ 引用歧义，编译期点名。"""
    protocol = _protocol(
        _phase(_PRODUCER, outputs=(_ARTIFACT,), run_chain=True, depends_on=("intake",)),
        _phase("intake", outputs=(_ARTIFACT,)),
        _phase(_READER, inputs=(f"{_PRODUCER}:{_ARTIFACT}",), depends_on=(_PRODUCER, "intake")),
    )
    resolution = resolve_cross_phase_inputs(protocol, _Catalog().snapshot)

    assert [item.code for item in resolution.findings] == ["CROSS_PHASE_INPUT_INVALID"]
    assert "ambiguous" in resolution.findings[0].message, resolution.findings[0].message


def test_a_self_reference_is_refused() -> None:
    """自己引用自己的产物 ⇒ 编译期点名。"""
    protocol = _protocol(
        _phase(_READER, outputs=(_ARTIFACT,), inputs=(f"{_READER}:{_ARTIFACT}",)),
    )
    resolution = resolve_cross_phase_inputs(protocol, _Catalog().snapshot)

    assert [item.code for item in resolution.findings] == ["CROSS_PHASE_INPUT_INVALID"]
    assert "its own output" in resolution.findings[0].message


# ------------------------------------------------- (b) 性质由产出方决定（含按压）


def test_b_the_trust_label_comes_from_the_producer_not_the_reader() -> None:
    """产出方声明 run-chain ⇒ `RETRIEVED`；**按压**：摘掉那条声明 ⇒ `GENERATED`。

    按压的是**产出方**的声明（`run_chain`），读取方一字不动 ⇒ 若判据读的是读取方
    或某个常量，按压后仍会是 `RETRIEVED`，两个读数不可能同时成立。
    """
    reader_inputs = (f"{_PRODUCER}:{_ARTIFACT}",)

    with_chain = resolve_cross_phase_inputs(
        _protocol(
            _phase(_PRODUCER, outputs=(_ARTIFACT,), run_chain=True),
            _phase(_READER, inputs=reader_inputs, depends_on=(_PRODUCER,)),
        ),
        _Catalog().snapshot,
    )
    assert with_chain.for_phase(_READER)[0].trust_label is TrustLabel.RETRIEVED

    # 按压：产出方**不**声明 run-chain（读取方与协议其余部分逐字不变）
    without_chain = resolve_cross_phase_inputs(
        _protocol(
            _phase(_PRODUCER, outputs=(_ARTIFACT,), run_chain=False),
            _phase(_READER, inputs=reader_inputs, depends_on=(_PRODUCER,)),
        ),
        _Catalog().snapshot,
    )
    assert without_chain.for_phase(_READER)[0].trust_label is TrustLabel.GENERATED, (
        "性质必须由**产出方**决定：摘掉产出方的 run-chain 声明后仍报 RETRIEVED ⇒ "
        "判据读的不是产出方（性质维会被伪造）"
    )


def test_b_a_provider_without_network_domains_does_not_earn_retrieved() -> None:
    """`run_chain` 但 provider **没**声明 `network_domains` ⇒ `GENERATED`（本地计算不算取得）。"""
    resolution = resolve_cross_phase_inputs(
        _protocol(
            _phase(_PRODUCER, outputs=(_ARTIFACT,), run_chain=True),
            _phase(_READER, inputs=(f"{_PRODUCER}:{_ARTIFACT}",), depends_on=(_PRODUCER,)),
        ),
        _Catalog(network=False).snapshot,
    )
    assert resolution.for_phase(_READER)[0].trust_label is TrustLabel.GENERATED


# ------------------------------------------- (c) 两来源并列 + 覆盖门（含按压）


def _store_with(name: str, payload: dict[str, object]) -> FakeArtifactStore:
    store = FakeArtifactStore()
    content = json.dumps(payload).encode("utf-8")
    store.put(
        Artifact(
            id=name,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            created_by="composition-root",
            classification="declared_input",
        ),
        content,
    )
    store.mark(name, ArtifactState.VERIFIED)
    return store


def _task(run_id: str) -> ResearchTask:
    return ResearchTask(id=ID.generate(), run_id=ID(run_id), contract_id="research_report_plan")


_RUN = "8f2d0e5a-6c4b-4a1e-9d3f-2b7c5e8a1f04"


@pytest.fixture()
def cross_phase_evidence() -> Any:
    """一条**已解析**的跨相输入登记出的证据（性质 `RETRIEVED`，读上游产物的真实字节）。"""
    workflow = FakeWorkflowEngine()
    store = FakeArtifactStore()
    ledger = FakeEvidenceLedger()
    task = _task(_RUN)
    producer_task = ResearchTask(
        id=ID.generate(),
        run_id=task.run_id,
        contract_id="multi_role_scouting",
        idempotency_key=f"{task.run_id.value}:{_PRODUCER}:scout-1",
    )
    workflow.submit(producer_task, _contract_for("multi_role_scouting"))
    content = b'{"summary":"scouted"}'
    artifact_id = f"{producer_task.id.value}:{_ARTIFACT}"
    store.put(
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            created_by=producer_task.id.value,
            classification="execution_result",
        ),
        content,
    )
    store.mark(artifact_id, ArtifactState.VERIFIED)
    sources = resolve_cross_phase_sources(
        workflow,
        store,
        task,
        ((_PRODUCER, _ARTIFACT, TrustLabel.RETRIEVED),),
    )
    return task, store, ledger, register_cross_phase_sources(ledger, task, sources)


def _contract_for(contract_id: str) -> Any:
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


def test_c_a_cross_phase_source_is_registered_with_the_producers_nature(
    cross_phase_evidence: Any,
) -> None:
    """跨相输入的 canonical 来源带着**产出方**的性质，且 origin 是两个端点（不覆盖产出方）。"""
    _task_obj, _store, ledger, evidence = cross_phase_evidence
    assert len(evidence) == 1
    source = ledger.get_source(evidence[0].source_ref)
    assert source.trust_label is TrustLabel.RETRIEVED
    assert source.origin.startswith(CROSS_PHASE_ORIGIN_PREFIX)


def test_c_both_source_kinds_are_accepted_side_by_side(cross_phase_evidence: Any) -> None:
    """**并列关系**：组合根供给（`USER_PROVIDED`）与跨相产出（`RETRIEVED`）同时计入覆盖。

    缺任一支 ⇒ 都只剩自己那一类；这里要求**两类同时在** registration 的 evidence 里，
    且**各自**在 canonical 里有 SourceRecord（不是只挂在返回值上）。
    """
    task, store, ledger, cross_phase = cross_phase_evidence
    seeded = _store_with("input-brief:real_research_v1", {"brief": "x"})
    for artifact_id in ("input-brief:real_research_v1",):
        store.put(
            Artifact(
                id=artifact_id,
                digest=Digest.of_bytes(seeded.get(artifact_id)),
                size_bytes=len(seeded.get(artifact_id)),
                media_type="application/json",
                created_by="composition-root",
                classification="declared_input",
            ),
            seeded.get(artifact_id),
        )
        store.mark(artifact_id, ArtifactState.VERIFIED)

    registration = register_session_result(
        RegistrationDeps(
            store=store,
            agent_id="agent:plan",
            ledger=ledger,
            declared_inputs=("input-brief:real_research_v1",),
            cross_phase_evidence=cross_phase,
        ),
        task,
        _contract_for("research_report_plan"),
        {"research_plan": {"content": "plan"}},
    )

    labels = {
        ledger.get_source(item.source_ref).trust_label
        for item in registration.evidence
        if ledger.has_source(item.source_ref)
    }
    assert TrustLabel.USER_PROVIDED in labels, labels
    assert TrustLabel.RETRIEVED in labels, labels
    # 两支都真的计入：非自产来源 2 条（组合根 1 + 跨相 1）。
    assert registration.evidence_source_count == 2, registration.evidence_source_count
    # 性质维由**跨相那一支**满足（组合根供给不算检索来源）。
    assert count_retrieved_sources(ledger, registration.evidence) == 1


def test_c_press_removing_cross_phase_evidence_makes_coverage_fail(
    cross_phase_evidence: Any,
) -> None:
    """**按压**：把跨相证据从登记面摘掉 ⇒ 覆盖的**性质维**判拒（`0 < 1 retrieved`）。

    与上一条成对：同一份输入、只改「跨相那一支在不在」⇒ 读数必须相反。
    这证明它真的是一条被计数的来源，而不是返回值上的装饰。
    """
    task, store, ledger, _cross_phase = cross_phase_evidence
    seeded = b'{"brief":"x"}'
    store.put(
        Artifact(
            id="input-brief:real_research_v1",
            digest=Digest.of_bytes(seeded),
            size_bytes=len(seeded),
            media_type="application/json",
            created_by="composition-root",
            classification="declared_input",
        ),
        seeded,
    )
    store.mark("input-brief:real_research_v1", ArtifactState.VERIFIED)

    registration = register_session_result(
        RegistrationDeps(
            store=store,
            agent_id="agent:plan",
            ledger=ledger,
            declared_inputs=("input-brief:real_research_v1",),
            # 按压：**不**给跨相证据
        ),
        task,
        _contract_for("research_report_plan"),
        {"research_plan": {"content": "plan"}},
    )

    assert registration.evidence_source_count == 1
    assert count_retrieved_sources(ledger, registration.evidence) == 0, (
        "摘掉跨相输入后检索来源必须归零（否则性质维可被组合根供给伪造成立）"
    )


__all__ = ["AgentSpec", "RoleDefinition", "SourceRecord"]
