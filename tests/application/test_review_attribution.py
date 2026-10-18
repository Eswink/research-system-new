"""GOAL-20261018-085 EC-01：**评审判词点名它的模型**（不是 agent 名）。

**建档实测的缺口**：`evidence.ReviewFinding` 只有 `reviewed_by`，而它逐字是
`gate:<agent id>` —— **agent 名**。GOAL-084 已证明 agent 名与底层模型可以完全脱钩
（出厂目录里四个 ModelDefinition 曾共用同一个 `model_name`）⇒ 只凭 `reviewed_by`，
「这条评审是谁判的」**不可归因**。

**本文件判四件事**：

1. **判词带模型身份**，形态是 `endpoint/model_name`（与 `preflight/review_independence`
   的解析面**同源**）；
2. **身份取装配好的执行目标**（`SessionSpecContext.endpoint` / `.model`），
   不是 agent 名、不是 profile 名、不是 model id；
3. **解析不了 ⇒ `None` 并点名**（`None` 不是「同一个模型」，也不是「独立」）；
4. **既有 `reviewed_by` 语义逐字不变**（仍是 `gate:<agent id>`）。
"""

from __future__ import annotations

from packages.application.run_orchestration.evaluation_gate import evaluate_task_gate
from packages.application.run_orchestration.review_attribution import reviewer_model_of
from packages.domain.evidence import ReviewFinding
from packages.domain.models import LLMEndpoint, ModelDefinition
from packages.domain.tasks import ResearchTask


def _task() -> ResearchTask:
    from packages.domain.core import ID

    return ResearchTask(id=ID.generate(), run_id=ID.generate())


def _contract_args() -> dict[str, object]:
    """最小合约：只判产物存在（与本文件要考的归因面无关）。"""
    from packages.domain.enums import AcceptanceCriterionType
    from packages.domain.tasks import AcceptanceCriterion, TaskContract

    return {
        "contract": TaskContract(
            id="g085_review",
            version="1.0.0",
            purpose="g085",
            acceptance_criteria=[
                AcceptanceCriterion(
                    type=AcceptanceCriterionType.ARTIFACT_EXISTS, artifact="review_decision"
                )
            ],
        )
    }


def _gate(reviewer_model: str | None) -> object:
    from packages.application.run_orchestration.evaluation_gate import EvaluationInputs

    args = _contract_args()
    return evaluate_task_gate(
        _task(),
        args["contract"],  # type: ignore[arg-type]
        EvaluationInputs(artifacts={"review_decision": "present"}),
        reviewer="gate:reviewer_a",
        reviewer_model=reviewer_model,
    )


def _endpoint() -> LLMEndpoint:
    return LLMEndpoint(
        id="main",
        name="Main",
        protocol="OPENAI_COMPATIBLE",
        base_url="https://example.invalid/v1",
        credential_ref="LLM_MAIN_KEY",
    )


def _model(model_id: str, name: str) -> ModelDefinition:
    return ModelDefinition(id=model_id, endpoint_id="main", model_name=name)


# --------------------------------------------------- 判词带模型身份


def test_the_verdict_carries_the_reviewer_model() -> None:
    """**正向**：判词的 `reviewer_model` 是 `endpoint/model_name`。"""
    outcome = _gate("main/glm-5.3")
    assert outcome.review_finding.reviewer_model == "main/glm-5.3"  # type: ignore[attr-defined]


def test_the_existing_reviewed_by_wording_is_unchanged() -> None:
    """**既有字段逐字不变**：`reviewed_by` 仍是 `gate:<agent id>`。"""
    outcome = _gate("main/glm-5.3")
    assert outcome.review_finding.reviewed_by == "gate:reviewer_a"  # type: ignore[attr-defined]


def test_an_unattributed_verdict_stays_none() -> None:
    """**反证**：调用方未声明模型 ⇒ `None`（不是「同一个模型」、也不是独立）。"""
    outcome = _gate(None)
    assert outcome.review_finding.reviewer_model is None  # type: ignore[attr-defined]


# ------------------------------- 身份取装配好的执行目标（不是 agent 名）


def test_the_target_comes_from_the_resolved_endpoint_and_model() -> None:
    spec = _spec(endpoint=_endpoint(), model=_model("reviewer_independent", "glm-5.3"))
    assert reviewer_model_of(spec) == "main/glm-5.3"


def test_the_target_is_not_the_agent_id_or_the_profile_name() -> None:
    """**机械分界**：agent id 是 `reviewer_a`、model id 是 `reviewer_independent`、
    `model_name` 是 `glm-5.3` —— 身份必须落在**最后一个**上。"""
    spec = _spec(endpoint=_endpoint(), model=_model("reviewer_independent", "glm-5.3"))
    target = reviewer_model_of(spec)
    assert target == "main/glm-5.3"
    assert target != "gate:reviewer_a"
    assert target != "reviewer_independent"
    assert target != "critic_independent"


def test_a_missing_endpoint_or_model_is_not_half_a_target() -> None:
    """**反证**：任一缺失 ⇒ `None`（**不**拼「半个目标」）。"""
    assert reviewer_model_of(_spec(endpoint=None, model=_model("m", "glm-5.3"))) is None
    assert reviewer_model_of(_spec(endpoint=_endpoint(), model=None)) is None
    assert reviewer_model_of(_spec(endpoint=None, model=None)) is None


def test_the_target_shape_matches_the_preflight_resolver() -> None:
    """**同源**：与 `preflight/review_independence.describe_target` 的形态一致。"""
    from packages.application.preflight.review_independence import describe_target

    assert describe_target(("main", "glm-5.3")) == "main/glm-5.3"
    assert reviewer_model_of(
        _spec(endpoint=_endpoint(), model=_model("x", "glm-5.3"))
    ) == describe_target(("main", "glm-5.3"))


# --------------------------------------------------- 落库面（sqlite）


def test_the_sqlite_store_round_trips_the_reviewer_model() -> None:
    """落库可读回（否则「可归因」只活在内存里）。"""
    from adapters.sqlite.review_finding_store import SqliteReviewFindingStore
    from packages.application.ports.review_finding_store import ScopedReviewFinding

    store = SqliteReviewFindingStore()
    try:
        store.put(
            ScopedReviewFinding(
                finding=ReviewFinding(
                    id="f-1",
                    review_type="acceptance_gate",
                    verdict="PASS",
                    findings=["ok"],
                    reviewed_by="gate:reviewer_a",
                    reviewer_model="main/glm-5.3",
                ),
                run_id="run-1",
                task_id="task-1",
                contract_id="c-1",
            )
        )
        records = store.for_run("run-1")
    finally:
        store.close()
    assert [item.finding.reviewer_model for item in records] == ["main/glm-5.3"]
    assert [item.finding.reviewed_by for item in records] == ["gate:reviewer_a"]


def _spec(*, endpoint: LLMEndpoint | None, model: ModelDefinition | None) -> object:
    """最小 spec 视图（只带本判据要读的两个字段）。"""
    from packages.domain.enums import ModelBindingMode
    from packages.domain.roles import AgentBinding, AgentSpec

    class _Spec:
        def __init__(self) -> None:
            self.endpoint = endpoint
            self.model = model
            self.agent = AgentSpec(
                id="reviewer_a",
                role="scientific_reviewer",
                model_binding=AgentBinding(
                    mode=ModelBindingMode.MODEL_PROFILE, value="critic_independent"
                ),
            )

    return _Spec()


# ---------------------------------------- 落库链（运行链这一步）真的搬运归因


def test_the_run_chain_record_carries_the_reviewer_model() -> None:
    """**产品路径这一步**：`acceptance_observation.acceptance_finding` 必须把门上的
    归因**原样搬运**到落库记录 —— 不搬运的话，读面又只剩 `reviewed_by`（agent 名）。"""
    from packages.application.run_orchestration.acceptance_observation import (
        acceptance_finding,
    )

    outcome = _gate("main/glm-5.3")
    scoped = acceptance_finding("run-1", "task-1", "contract-1", outcome)
    assert scoped.finding.reviewer_model == "main/glm-5.3"
    assert scoped.finding.reviewed_by == "gate:reviewer_a"


def test_the_run_chain_record_leaves_it_none_when_the_gate_did_not_name_it() -> None:
    """**反证**：门上没有归因 ⇒ 落库也是 `None`（不编造）。"""
    from packages.application.run_orchestration.acceptance_observation import (
        acceptance_finding,
    )

    scoped = acceptance_finding("run-1", "task-1", "contract-1", _gate(None))
    assert scoped.finding.reviewer_model is None
