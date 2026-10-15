"""GOAL-20261015-080 EC-01 判据：设计的**来源可声明**，且读是**确定性 / run 作用域 /
fail-closed** 的。

判据成对（正向 / 反证 / 零回归 / 自检）：

- **正向**：合法的计划产物 ⇒ 逐臂读出，参数逐键过白名单；
- **run 作用域**：他 run 登记的计划制品**读不到**（经 claim → relation 投影按
  `evidence.run_id` 过滤 —— 与 `GET /runs/{id}/evidence` 同一口径）；
- **fail-closed**：无登记 / 无制品 / 无设计块 / 设计块畸形 / 空臂 / 多制品 ⇒ 各自**点名**
  （判词**互不相同**：混成一句话会让「计划没写」与「读不到」不可区分）；
- **白名单**：设计块里的键逐键过既有点 `ALLOWED_PARAMETERS`（§9），越界点名且点出白名单。
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
    read_design_from_plan,
)
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import ArtifactState
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
)

PLAN_TASK = "11111111-1111-4111-8111-111111111111"
OTHER_TASK = "22222222-2222-4222-8222-222222222222"
RUN_ID = "33333333-3333-4333-8333-333333333333"
OTHER_RUN = "44444444-4444-4444-8444-444444444444"


def _put_plan(store: FakeArtifactStore, task_id: str, payload: object) -> str:
    content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    artifact_id = plan_artifact_id(task_id)
    store.put(
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            storage_uri=None,
            created_by="agent:research_director",
            source_refs=[f"task:{task_id}"],
            classification="execution_result",
        ),
        content,
    )
    store.mark(artifact_id, ArtifactState.VERIFIED)
    return artifact_id


def _register(ledger: FakeEvidenceLedger, *, run_id: str, artifact_id: str, tag: str) -> None:
    """把一个制品登记进证据链（**这是它对本 run「在场」的机械含义**）。"""
    evidence = Evidence(
        id=f"evidence:plan:{tag}",
        source_ref=f"tool:{artifact_id}",
        content_digest="0" * 64,
        extracted_by="agent:research_director",
        captured_at=Timestamp.now(),
        artifact_id=artifact_id,
        run_id=run_id,
    )
    claim = Claim(
        id=f"claim:plan:{tag}",
        statement=f"plan artifact {artifact_id}",
        status=ClaimStatus.PROPOSED,
        author="agent:research_director",
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


def _setup(
    payload: object, *, run_id: str = RUN_ID, task_id: str = PLAN_TASK
) -> tuple[FakeArtifactStore, FakeEvidenceLedger]:
    store = FakeArtifactStore()
    ledger = FakeEvidenceLedger()
    artifact_id = _put_plan(store, task_id, payload)
    _register(ledger, run_id=run_id, artifact_id=artifact_id, tag=f"p-{task_id[:4]}")
    return store, ledger


def _design(arms: object) -> dict[str, object]:
    return {DESIGN_KEY: {"arms": arms}}


class TestTheDesignIsReadFromThePlanArtifact:
    """正向：计划产物的内容 → 臂与参数（**逐键**）。"""

    def test_the_declared_arms_come_back_with_their_parameters(self) -> None:
        store, ledger = _setup(_design({"control": {}, "treatment": {"n_items": 120, "seed": 11}}))
        design = read_design_from_plan(store, ledger, run_id=RUN_ID)
        assert [arm.name for arm in design.arms] == ["control", "treatment"], design.arms
        assert dict(design.arms[0].parameters) == {}
        assert dict(design.arms[1].parameters) == {"n_items": 120, "seed": 11}

    def test_the_result_carries_the_artifact_id_and_the_run(self) -> None:
        """来源是**可复核的**：制品 id 与 run 都在读数里（不是「某处读到了」）。"""
        store, ledger = _setup(_design({"a": {}}))
        design = read_design_from_plan(store, ledger, run_id=RUN_ID)
        assert design.artifact_id == plan_artifact_id(PLAN_TASK)
        assert design.run_id == RUN_ID

    def test_the_explicit_list_shape_is_accepted(self) -> None:
        """设计块里的臂也认**显式列表**形态（与 `parse_arms` 同一口径）。"""
        store, ledger = _setup(
            _design([{"name": "control", "parameters": {}}, {"name": "treatment"}])
        )
        design = read_design_from_plan(store, ledger, run_id=RUN_ID)
        assert [arm.name for arm in design.arms] == ["control", "treatment"]


class TestTheReadIsRunScoped:
    """**run 作用域**：他 run 的计划制品读不到（这是「本 run 的计划」的机械含义）。"""

    def test_another_runs_plan_artifact_is_not_in_view(self) -> None:
        """他 run 登记的计划**不属于本 run 的投影** ⇒ 本 run 视角里「什么都没登记」。"""
        store, ledger = _setup(_design({"control": {}}), run_id=OTHER_RUN)
        with pytest.raises(ExperimentDesignUnreadableError, match="nothing is registered"):
            read_design_from_plan(store, ledger, run_id=RUN_ID)

    def test_the_other_runs_artifact_does_not_leak_when_both_exist(self) -> None:
        """两份都在场时，读到的**必须**是本 run 那份（不是「先扫到的」）。"""
        store = FakeArtifactStore()
        ledger = FakeEvidenceLedger()
        foreign_id = _put_plan(store, OTHER_TASK, _design({"foreign": {}}))
        mine_id = _put_plan(store, PLAN_TASK, _design({"mine": {}}))
        _register(ledger, run_id=OTHER_RUN, artifact_id=foreign_id, tag="f")
        _register(ledger, run_id=RUN_ID, artifact_id=mine_id, tag="m")
        design = read_design_from_plan(store, ledger, run_id=RUN_ID)
        assert [arm.name for arm in design.arms] == ["mine"], design.arms

    def test_no_registration_is_named(self) -> None:
        """**未登记 ⇒ 读不到**（只 put 制品不登记证据 ⇒ 不在本 run 的投影里）。"""
        store = FakeArtifactStore()
        ledger = FakeEvidenceLedger()
        _put_plan(store, PLAN_TASK, _design({"a": {}}))
        with pytest.raises(ExperimentDesignUnreadableError, match="nothing is registered"):
            read_design_from_plan(store, ledger, run_id=RUN_ID)


class TestTheFailureModesAreNamedSeparately:
    """fail-closed 多态：每条判词**互不相同**（「计划没写」与「读不到」必须分得开）。"""

    def test_a_missing_artifact_is_named(self) -> None:
        """登记了（evidence 指向该 id）但制品**不在场** ⇒ 与「没有登记」分开点名。"""
        store = FakeArtifactStore()
        ledger = FakeEvidenceLedger()
        _register(ledger, run_id=RUN_ID, artifact_id=plan_artifact_id(PLAN_TASK), tag="ghost")
        with pytest.raises(ExperimentDesignUnreadableError, match="no readable"):
            read_design_from_plan(store, ledger, run_id=RUN_ID)

    def test_a_missing_design_block_is_named(self) -> None:
        store, ledger = _setup({"question": "something else entirely"})
        with pytest.raises(ExperimentDesignUnreadableError, match="carries no 'experiment_design'"):
            read_design_from_plan(store, ledger, run_id=RUN_ID)

    def test_a_malformed_design_block_is_named(self) -> None:
        store, ledger = _setup({DESIGN_KEY: ["not", "an", "object"]})
        with pytest.raises(ExperimentDesignUnreadableError, match="must be an object"):
            read_design_from_plan(store, ledger, run_id=RUN_ID)

    def test_an_empty_arm_set_is_named(self) -> None:
        store, ledger = _setup(_design({}))
        with pytest.raises(ExperimentDesignUnreadableError, match="declares no arms"):
            read_design_from_plan(store, ledger, run_id=RUN_ID)

    def test_more_than_one_plan_artifact_is_named(self) -> None:
        """两个计划制品 ⇒ 来源**不可判定** ⇒ 点名（**不猜**哪个说了算）。"""
        store = FakeArtifactStore()
        ledger = FakeEvidenceLedger()
        first = _put_plan(store, PLAN_TASK, _design({"a": {}}))
        second = _put_plan(store, OTHER_TASK, _design({"b": {}}))
        _register(ledger, run_id=RUN_ID, artifact_id=first, tag="1")
        _register(ledger, run_id=RUN_ID, artifact_id=second, tag="2")
        with pytest.raises(ExperimentDesignUnreadableError, match="more than one plan artifact"):
            read_design_from_plan(store, ledger, run_id=RUN_ID)


class TestTheWhitelistIsEnforcedOnTheDesign:
    """§9 纪律：设计块里的键**逐键**过既有白名单（不是「计划写的就照单全收」）。"""

    def test_a_parameter_outside_the_whitelist_is_refused_by_name(self) -> None:
        store, ledger = _setup(_design({"treatment": {"learning_rate": 0.1}}))
        with pytest.raises(ExperimentDesignUnreadableError, match="learning_rate"):
            read_design_from_plan(store, ledger, run_id=RUN_ID)

    def test_the_refusal_names_what_is_allowed(self) -> None:
        """点名**白名单本身**（读者不必去翻源码才知道能写什么）。"""
        store, ledger = _setup(_design({"treatment": {"nope": 1}}))
        with pytest.raises(ExperimentDesignUnreadableError, match="allowed:"):
            read_design_from_plan(store, ledger, run_id=RUN_ID)

    def test_every_whitelisted_key_is_accepted(self) -> None:
        """白名单内的键**全部**可用（否则「白名单」与实际能力不符）。"""
        store, ledger = _setup(
            _design({"treatment": {"seed": 1, "n_items": 2, "duplicate_pairs": 3}})
        )
        design = read_design_from_plan(store, ledger, run_id=RUN_ID)
        assert dict(design.arms[0].parameters) == {"seed": 1, "n_items": 2, "duplicate_pairs": 3}

    def test_a_duplicate_arm_name_is_refused(self) -> None:
        """重复臂名 ⇒ 既有解析器点名（本模块**不**吞掉它的判词，而是带上来源）。"""
        store, ledger = _setup(
            _design([{"name": "a", "parameters": {}}, {"name": "a", "parameters": {}}])
        )
        with pytest.raises(ExperimentDesignUnreadableError, match="duplicate arm names"):
            read_design_from_plan(store, ledger, run_id=RUN_ID)


class TestTheNonObjectivesAreRefusedToo:
    """非目标**不**被静默跳过：非 JSON / 超大制品各自走「读不到」的点名。"""

    def test_a_non_json_artifact_is_treated_as_unreadable(self) -> None:
        store = FakeArtifactStore()
        ledger = FakeEvidenceLedger()
        content = b"this is not json at all"
        artifact_id = plan_artifact_id(PLAN_TASK)
        store.put(
            Artifact(
                id=artifact_id,
                digest=Digest.of_bytes(content),
                size_bytes=len(content),
                media_type="text/plain",
                storage_uri=None,
                created_by="agent:research_director",
                source_refs=[f"task:{PLAN_TASK}"],
                classification="execution_result",
            ),
            content,
        )
        store.mark(artifact_id, ArtifactState.VERIFIED)
        _register(ledger, run_id=RUN_ID, artifact_id=artifact_id, tag="raw")
        with pytest.raises(ExperimentDesignUnreadableError, match="no readable"):
            read_design_from_plan(store, ledger, run_id=RUN_ID)

    def test_an_oversized_artifact_is_not_silently_truncated(self) -> None:
        """超界 ⇒ 与「读不到」同一处置（**不**截断：截断的设计看起来像读到了）。"""
        store, ledger = _setup(_design({"a": {}}))
        with pytest.raises(ExperimentDesignUnreadableError, match="no readable"):
            read_design_from_plan(store, ledger, run_id=RUN_ID, max_chars=10)


class TestTheWhitelistIsTheOneFromTheParameterSurface:
    """自检：本模块判的白名单**就是**参数面的那一份（不是抄的第二个词表）。"""

    def test_the_allowed_keys_match_the_parameter_surface(self) -> None:
        from packages.application.experiments.plan_parameters import ALLOWED_PARAMETERS

        assert "n_items" in ALLOWED_PARAMETERS
        assert "seed" in ALLOWED_PARAMETERS
        store, ledger = _setup(_design({"a": {"definitely_not_allowed": 1}}))
        with pytest.raises(ExperimentDesignUnreadableError) as info:
            read_design_from_plan(store, ledger, run_id=RUN_ID)
        for key in sorted(ALLOWED_PARAMETERS):
            assert key in str(info.value), f"点名里必须含白名单键 {key}"
