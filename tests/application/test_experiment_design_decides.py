"""GOAL-20261015-080 EC-02 判据：**设计的内容真正决定实验**（来源唯一 + fail-closed）。

判据成对（正向 / 反证 / 来源唯一 / 零回归）：

- **正向**：`design_source="plan"` + 计划产物里的设计 ⇒ 跑出来的臂**就是**计划里那些；
- **来源唯一**：`design_source="plan"` **与**装配面声明的臂同时在场 ⇒ **点名拒绝**
  （「哪个说了算」不可判定是最坏形态）；
- **未认得的来源** ⇒ 点名（**不**当成「没有来源」静默回落装配面）；
- **零回归**：未声明 `design_source` ⇒ 既有装配面语义逐字不变（单臂 / 声明臂两条都判）。
"""

from __future__ import annotations

import json

import pytest

from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.evidence_ledger import FakeEvidenceLedger
from packages.application.experiments.design_from_plan import (
    DESIGN_KEY,
    ExperimentDesignUnreadableError,
    plan_artifact_id,
)
from packages.application.ports.errors import InvalidInputError
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest, Timestamp
from packages.domain.enums import ArtifactState
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
)
from packages.domain.tasks import ResearchTask
from services.api.experiment_support import (
    DESIGN_SOURCE_PLAN,
    SandboxExperimentAssembly,
    _arms_for,
)

RUN_ID = "33333333-3333-4333-8333-333333333333"
TASK_ID = "11111111-1111-4111-8111-111111111111"


def _task() -> ResearchTask:
    return ResearchTask(id=ID(TASK_ID), run_id=ID(RUN_ID))


def _assembly_of(*, design_source: str | None, arms: object | None) -> SandboxExperimentAssembly:
    store = FakeArtifactStore()
    ledger = FakeEvidenceLedger()
    return SandboxExperimentAssembly(
        execution=object(),
        artifacts=store,
        policy=object(),
        image="test:image",
        ledger=ledger,
        arms=arms,
        design_source=design_source,
    )


def _seed_plan(assembly: SandboxExperimentAssembly, payload: object) -> None:
    """把一份计划产物**登记进本 run 的证据链**（= 它对本 run「在场」）。"""
    ledger = assembly.ledger
    assert ledger is not None, "本夹具的装配面总是带 ledger"
    content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    artifact_id = plan_artifact_id(TASK_ID)
    assembly.artifacts.put(
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            storage_uri=None,
            created_by="agent:research_director",
            source_refs=[f"task:{TASK_ID}"],
            classification="execution_result",
        ),
        content,
    )
    assembly.artifacts.mark(artifact_id, ArtifactState.VERIFIED)
    evidence = Evidence(
        id="evidence:plan:seed",
        source_ref=f"tool:{artifact_id}",
        content_digest="0" * 64,
        extracted_by="agent:research_director",
        captured_at=Timestamp.now(),
        artifact_id=artifact_id,
        run_id=RUN_ID,
    )
    claim = Claim(
        id="claim:plan:seed",
        statement=f"plan {artifact_id}",
        status=ClaimStatus.PROPOSED,
    )
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


class TestThePlanContentDecides:
    """正向：`design_source="plan"` ⇒ 臂**就是**计划产物里那些（参数逐键）。"""

    def test_the_arms_come_from_the_plan_not_from_the_assembly(self) -> None:
        assembly = _assembly_of(design_source=DESIGN_SOURCE_PLAN, arms=None)
        _seed_plan(assembly, _design({"from_plan_a": {"n_items": 50}, "from_plan_b": {}}))
        arms = _arms_for(assembly, _task())
        assert [arm.name for arm in arms] == ["from_plan_a", "from_plan_b"], arms
        assert dict(arms[0].parameters) == {"n_items": 50}

    def test_a_different_plan_yields_a_different_design(self) -> None:
        """**设计因计划而不同**（同一装配、两份计划 ⇒ 两套臂）。"""
        first = _assembly_of(design_source=DESIGN_SOURCE_PLAN, arms=None)
        _seed_plan(first, _design({"only_arm": {}}))
        second = _assembly_of(design_source=DESIGN_SOURCE_PLAN, arms=None)
        _seed_plan(second, _design({"control": {}, "treatment": {"n_items": 120}}))
        assert [a.name for a in _arms_for(first, _task())] == ["only_arm"]
        assert [a.name for a in _arms_for(second, _task())] == ["control", "treatment"]


class TestTheSourceMustBeUnambiguous:
    """**来源唯一**：两条来源同时在场 ⇒ 点名拒绝（不静默取其一）。"""

    def test_plan_source_plus_declared_arms_is_refused(self) -> None:
        assembly = _assembly_of(design_source=DESIGN_SOURCE_PLAN, arms={"explicit": {}})
        _seed_plan(assembly, _design({"from_plan": {}}))
        with pytest.raises(InvalidInputError, match="would be undecidable"):
            _arms_for(assembly, _task())

    def test_the_refusal_names_the_declared_arms(self) -> None:
        """点名已声明的臂（读者一眼看出冲突在哪）。"""
        assembly = _assembly_of(design_source=DESIGN_SOURCE_PLAN, arms={"explicit_arm": {}})
        _seed_plan(assembly, _design({"from_plan": {}}))
        with pytest.raises(InvalidInputError, match="explicit_arm"):
            _arms_for(assembly, _task())

    def test_an_unknown_source_is_refused_by_name(self) -> None:
        """未认得的来源名 ⇒ 点名（**不**当成「没有来源」静默回落装配面）。"""
        assembly = _assembly_of(design_source="from_the_ether", arms=None)
        with pytest.raises(InvalidInputError, match="unknown experiment design source"):
            _arms_for(assembly, _task())

    def test_the_unknown_source_is_refused_even_when_arms_are_declared(self) -> None:
        """未知名 + 已声明臂 ⇒ **仍拒绝**（不得退化成「有臂就照跑」）。"""
        assembly = _assembly_of(design_source="from_the_ether", arms={"a": {}})
        with pytest.raises(InvalidInputError, match="unknown experiment design source"):
            _arms_for(assembly, _task())


class TestThePlanSourceIsFailClosed:
    """计划来源的失败**不**回落装配常量（那会把「计划没写」伪装成「计划驱动」）。"""

    def test_a_missing_plan_is_a_named_failure_not_a_fallback(self) -> None:
        assembly = _assembly_of(design_source=DESIGN_SOURCE_PLAN, arms=None)
        with pytest.raises(ExperimentDesignUnreadableError):
            _arms_for(assembly, _task())

    def test_a_plan_without_the_design_block_is_a_named_failure(self) -> None:
        assembly = _assembly_of(design_source=DESIGN_SOURCE_PLAN, arms=None)
        _seed_plan(assembly, {"question": "no design here"})
        with pytest.raises(ExperimentDesignUnreadableError, match="carries no"):
            _arms_for(assembly, _task())


class TestTheUnchangedPathStaysUnchanged:
    """零回归：未声明 `design_source` ⇒ 既有装配面语义逐字不变。"""

    def test_no_declaration_means_no_arms(self) -> None:
        assembly = _assembly_of(design_source=None, arms=None)
        assert _arms_for(assembly, _task()) == ()

    def test_no_declaration_uses_the_declared_arms(self) -> None:
        assembly = _assembly_of(design_source=None, arms={"control": {}, "treatment": {}})
        assert [arm.name for arm in _arms_for(assembly, _task())] == ["control", "treatment"]

    def test_the_plan_is_not_even_read_when_no_source_is_declared(self) -> None:
        """未声明来源 ⇒ **不读计划**（连坏计划也不影响 —— 读取器根本不该被调用）。"""
        assembly = _assembly_of(design_source=None, arms=None)
        _seed_plan(assembly, {"not": "a design"})
        assert _arms_for(assembly, _task()) == ()
