"""GOAL-20261018-088 EC-01/EC-02：**实验设计由检索派生**（来源换成系统真的取回了什么）。

**它补哪一格**（阶梯「实验」域的 `下一级`）：GOAL-080 让设计可以取自**计划产物**，而计划
是**模型写的正文** —— 于是「设计由检索派生」实际是「设计由**计划作者**派生」。本轮新增
第二个来源 `design_source="retrieval"`：臂与参数从**本 run 的系统取得证据**
（`TrustLabel.RETRIEVED`，与覆盖门同一判据）的**记录内容**里读出。

**四条读数（成对）**：

1. **正向**：检索记录里带设计块 ⇒ 臂**就是**记录里那些（参数逐键）；
2. **换记录 ⇒ 换设计**：同一装配，两份不同的检索记录 ⇒ 两套臂（设计真的由来源决定）；
3. **性质维度**：把同一条证据的来源改成**非** `RETRIEVED`（如 `USER_PROVIDED`）⇒
   点名拒绝 —— 「检索派生」**不**认模型自产或声明输入；
4. **两个来源互斥 + fail-closed**：`retrieval` 与显式 `arms` 同时在场 ⇒ 点名拒绝；
   没有系统取得证据 / 记录里没有设计块 / 多份设计 / 参数越白名单 ⇒ **逐条点名**。

**如实边界**：本文件用受控证据账本与制品店（与 GOAL-080 的计划来源判据同一手法），
证明的是**读取与判定**这条链；真容器与真检索由既有的 `requires_docker` / live 套件承担。
"""

from __future__ import annotations

import json

import pytest

from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.evidence_ledger import FakeEvidenceLedger
from packages.application.experiments.design_from_plan import DESIGN_KEY
from packages.application.experiments.design_from_retrieval import (
    DESIGN_SOURCE_RETRIEVAL,
    read_design_from_retrieval,
)
from packages.application.ports.errors import InvalidInputError
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest, Timestamp
from packages.domain.enums import ArtifactState, TrustLabel
from packages.domain.evidence import (
    Claim,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.tasks import ResearchTask
from services.api.experiment_support import (
    DESIGN_SOURCE_PLAN,
    DESIGN_SOURCES,
    SandboxExperimentAssembly,
    _arms_for,
)

RUN_ID = "88888888-8888-4888-8888-888888888888"
TASK_ID = "99999999-9999-4999-8999-999999999999"
#: 工具结果制品的 id 前缀（与产品口径同源；不 import 产品常量当预言机）。
_TOOL_PREFIX = "tool-result:"


def _task() -> ResearchTask:
    return ResearchTask(id=ID(TASK_ID), run_id=ID(RUN_ID))


def _assembly(
    *, design_source: str | None, arms: object | None = None
) -> SandboxExperimentAssembly:
    return SandboxExperimentAssembly(
        execution=object(),
        artifacts=FakeArtifactStore(),
        policy=object(),
        image="test:image",
        ledger=FakeEvidenceLedger(),
        arms=arms,
        design_source=design_source,
    )


class _Seed:
    """一条被种入的检索记录的**可控面**（参数对象，守住函数签名 <= 5）。"""

    def __init__(
        self,
        *,
        run_id: str = RUN_ID,
        trust: TrustLabel = TrustLabel.RETRIEVED,
        evidence_id: str = "evidence:retrieval:seed",
        suffix: str = "literature_search",
    ) -> None:
        self.run_id = run_id
        self.trust = trust
        self.evidence_id = evidence_id
        self.suffix = suffix


def _seed_retrieval(
    assembly: SandboxExperimentAssembly,
    payload: object,
    seed: _Seed | None = None,
) -> None:
    """把一条**工具结果**登记进本 run 的证据链（= 它对本次 run「系统取得」了）。"""
    where = seed or _Seed()
    ledger = assembly.ledger
    assert ledger is not None, "本夹具的装配面总是带 ledger"
    content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    artifact_id = f"{_TOOL_PREFIX}{TASK_ID}:op:{where.suffix}"
    assembly.artifacts.put(
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            storage_uri=None,
            created_by="system:run-chain",
            source_refs=[f"task:{TASK_ID}"],
            classification="tool_result",
        ),
        content,
    )
    assembly.artifacts.mark(artifact_id, ArtifactState.VERIFIED)
    source = SourceRecord(
        origin=f"tool:{artifact_id}",
        content_digest=str(Digest.of_bytes(content)),
        trust_label=where.trust,
        access_time=Timestamp.now(),
        parser_version="retrieval-design-test",
    )
    ledger.register_source(source)
    evidence = Evidence(
        id=where.evidence_id,
        source_ref=source.origin,
        content_digest=str(source.content_digest),
        extracted_by="system:run-chain",
        captured_at=Timestamp.now(),
        artifact_id=artifact_id,
        run_id=where.run_id,
    )
    claim = Claim(id=f"claim:{where.evidence_id}", statement=f"retrieved {artifact_id}")
    ledger.register_evidence(evidence)
    ledger.register_claim(claim)
    ledger.attach_relation(
        EvidenceRelation(
            claim_id=claim.id,
            evidence_id=evidence.id,
            relation=EvidenceRelationType.SUPPORTS,
        )
    )


def _design(arms: object) -> dict[str, object]:
    return {DESIGN_KEY: {"arms": arms}}


class TestTheRetrievedContentDecides:
    """正向：`design_source="retrieval"` ⇒ 臂**就是**检索记录里那些。"""

    def test_the_arms_come_from_the_retrieved_record(self) -> None:
        assembly = _assembly(design_source=DESIGN_SOURCE_RETRIEVAL)
        _seed_retrieval(assembly, _design({"from_retrieval_a": {"n_items": 40}, "b": {}}))
        arms = _arms_for(assembly, _task())
        assert [arm.name for arm in arms] == ["from_retrieval_a", "b"], arms
        assert dict(arms[0].parameters) == {"n_items": 40}

    def test_a_different_record_yields_a_different_design(self) -> None:
        """**设计因检索而不同**（同一装配、两份记录 ⇒ 两套臂）。"""
        first = _assembly(design_source=DESIGN_SOURCE_RETRIEVAL)
        _seed_retrieval(first, _design({"only_arm": {}}))
        second = _assembly(design_source=DESIGN_SOURCE_RETRIEVAL)
        _seed_retrieval(second, _design({"control": {}, "treatment": {"n_items": 90}}))
        assert [a.name for a in _arms_for(first, _task())] == ["only_arm"]
        assert [a.name for a in _arms_for(second, _task())] == ["control", "treatment"]

    def test_the_design_names_the_evidence_it_came_from(self) -> None:
        """来源**可归因**：读出的设计点名它读了哪条证据（不是「从空气里读的」）。"""
        assembly = _assembly(design_source=DESIGN_SOURCE_RETRIEVAL)
        _seed_retrieval(assembly, _design({"a": {}}), _Seed(evidence_id="evidence:named"))
        assert assembly.ledger is not None
        design = read_design_from_retrieval(assembly.artifacts, assembly.ledger, run_id=RUN_ID)
        assert design.arm_source_evidence == ("evidence:named",)
        assert design.run_id == RUN_ID


class TestTheNatureDimensionIsNotForged:
    """**性质维度**：非 `RETRIEVED` 的同一份内容**不算**「系统取得」。"""

    def test_a_provided_record_is_not_retrieval(self) -> None:
        assembly = _assembly(design_source=DESIGN_SOURCE_RETRIEVAL)
        _seed_retrieval(assembly, _design({"a": {}}), _Seed(trust=TrustLabel.USER_PROVIDED))
        with pytest.raises(InvalidInputError) as caught:
            _arms_for(assembly, _task())
        message = str(caught.value)
        assert "no system-retrieved evidence" in message, message

    def test_another_runs_record_is_out_of_view(self) -> None:
        assembly = _assembly(design_source=DESIGN_SOURCE_RETRIEVAL)
        _seed_retrieval(
            assembly,
            _design({"a": {}}),
            _Seed(run_id="00000000-0000-4000-8000-000000000000"),
        )
        with pytest.raises(InvalidInputError) as caught:
            _arms_for(assembly, _task())
        assert "no system-retrieved evidence" in str(caught.value)


class TestTheSourceMustBeUnambiguous:
    """**来源唯一 + fail-closed**（逐条点名，不静默回落到装配面）。"""

    def test_retrieval_source_plus_declared_arms_is_refused(self) -> None:
        assembly = _assembly(design_source=DESIGN_SOURCE_RETRIEVAL, arms={"explicit": {}})
        _seed_retrieval(assembly, _design({"a": {}}))
        with pytest.raises(InvalidInputError) as caught:
            _arms_for(assembly, _task())
        message = str(caught.value)
        assert "undecidable" in message, message
        assert "explicit" in message, message

    def test_a_record_without_a_design_block_is_named(self) -> None:
        assembly = _assembly(design_source=DESIGN_SOURCE_RETRIEVAL)
        _seed_retrieval(assembly, {"ids": ["39000001"]})
        with pytest.raises(InvalidInputError) as caught:
            _arms_for(assembly, _task())
        assert DESIGN_KEY in str(caught.value)

    def test_two_designs_are_refused_instead_of_guessed(self) -> None:
        assembly = _assembly(design_source=DESIGN_SOURCE_RETRIEVAL)
        _seed_retrieval(assembly, _design({"a": {}}), _Seed(evidence_id="evidence:one", suffix="a"))
        _seed_retrieval(assembly, _design({"b": {}}), _Seed(evidence_id="evidence:two", suffix="b"))
        with pytest.raises(InvalidInputError) as caught:
            _arms_for(assembly, _task())
        assert "more than one" in str(caught.value)

    def test_a_parameter_outside_the_whitelist_is_named(self) -> None:
        assembly = _assembly(design_source=DESIGN_SOURCE_RETRIEVAL)
        _seed_retrieval(assembly, _design({"a": {"not_a_parameter": 1}}))
        with pytest.raises(InvalidInputError) as caught:
            _arms_for(assembly, _task())
        message = str(caught.value)
        assert "outside the whitelist" in message, message
        assert "not_a_parameter" in message, message

    def test_both_sources_are_known_and_distinct(self) -> None:
        """两个来源都**在词表里**且不同（未认得的来源名仍点名拒绝）。"""
        assert DESIGN_SOURCES == (DESIGN_SOURCE_PLAN, DESIGN_SOURCE_RETRIEVAL)
        assert DESIGN_SOURCE_PLAN != DESIGN_SOURCE_RETRIEVAL
        assembly = _assembly(design_source="neither")
        with pytest.raises(InvalidInputError) as caught:
            _arms_for(assembly, _task())
        assert "unknown experiment design source" in str(caught.value)
