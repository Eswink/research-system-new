"""报告汇编任务的**派发与准入**（GOAL-20261014-077 EC-02；读面在 `report_facts.py`）。

**它补哪一环**：EC-01 把**汇编器**（`deliverable/research_report.py`）放进树，但那个模块
**没有产品路径** —— 它只会被测试调用。本模块把它接成**一个 phase 的执行体**：契约声明
`report` ⇒ 派发到这里（与 `experiment` 声明派发到沙箱实验**同形同层**，见
`experiment_task.py` 的 docstring）。

**事实从哪来**：全部经 `report_facts` 的四个**既有**读面（run 存储 / 证据投影 / 制品内容 /
评审存储）SELECT，本模块**不重算**任何数字、**不创造**任何结论。

**判定两条、各自点名**（承「点名失败而非静默降级」）：

- **缺装配**（缺 RunStore / ledger / 评审存储）⇒ 失败并点名缺哪一个 —— 不产出一份
  「读不到事实但看起来像报告」的制品；
- **缺事实**（某节没有内容）⇒ **不是**失败：汇编器把该节写成「无 + 原因」（EC-01 (c)），
  报告如实说明它为什么空。

**制品落点**：`{run_id}:research_report.md`（**run 级**交付物，不是某一 phase 的中间产物；
`text/markdown` ⇒ 命中 `services/api/routers/artifacts.py` 既有的内联预览白名单，
不需要改任何路由）。内容寻址：digest 由报告字节**重算**。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from packages.application.deliverable.report_narrative import NarrativeError
from packages.application.deliverable.research_report import (
    REPORT_ARTIFACT_NAME,
    REPORT_MIME,
    ReportBuildError,
    ReportInputs,
    build_research_report,
    report_digest_payload,
    report_metadata,
)
from packages.application.ports.agent_runtime import AgentSessionResult
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.run_orchestration.acceptance_observation import (
    record_acceptance_evaluation,
)
from packages.application.run_orchestration.manuscript_assembly import (
    assembled_message,
    maybe_assemble_manuscript,
)
from packages.application.run_orchestration.report_facts import (
    evidence_of_run,
    report_inputs,
    tool_evidence,
)
from packages.application.run_orchestration.report_narrative_task import narrate
from packages.application.run_orchestration.result_handler import (
    RegistrationDeps,
    ResultRegistration,
    register_declared_input_sources,
)
from packages.application.run_orchestration.task_executor import (
    SessionSpecContext,
    TaskExecutionResult,
)
from packages.application.run_orchestration.task_phase_helpers import (
    PhaseStep,
    evaluate_gate,
    failure_step,
    finish_task_step,
    gate_rejection_reason,
)
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import ArtifactState, FailureCategory, TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.session_state import AgentSessionState
from packages.domain.tasks import ResearchTask, TaskContract

#: 报告制品名（与汇编器的常量同值；判据里读得懂）。
_REPORT_NAME = REPORT_ARTIFACT_NAME


def report_artifact_id(run_id: str) -> str:
    """报告的 canonical 制品 id（**run 级**名字；判据与读面共用这一处）。"""
    return f"{run_id}:{_REPORT_NAME}"


@dataclass(frozen=True, slots=True)
class ReportTaskDeps:
    """报告汇编的装配面（Port 组合；缺任一件 ⇒ 该任务**点名拒绝**）。

    `runs` **不在这里**：run 实体是**执行期在场的事实**（`spec_context.run`），
    不从存储读 —— 执行期间控制面还没把 run 行落库（见 `SessionSpecContext.run`）。

    `narrator`（GOAL-20261022-062）：接上了 ⇒ 正文由**模型**撰写、数字留在确定性事实表；
    缺省 `None` ⇒ 逐字回到**确定性汇编**（既有行为零回归）。**不把它做成「有就偷偷用、
    没有就猜」**：两条路径的报告字节与 `created_by` 都不同，「谁写的」在制品上可读。
    """

    artifacts: ArtifactStore
    ledger: EvidenceLedger | None = None
    reviews: Any | None = None
    actor: str = "system:report-assembler"
    narrator: Any | None = None
    #: GOAL-20261028-099：**同时汇编投稿形状的手稿**（`manuscript.md`）。
    #: 缺省 `False` ⇒ 既有报告路径**逐字节不变**（不读、不写、不登记任何手稿面）。
    #: 开它也不保证产出：本 run 没有 `manuscript_narrative` 制品 ⇒ 返回 `None`
    #: （这次 run 没走手稿相 ⇒ 无手稿是**正确**读数，不是失败）。
    manuscript: bool = False


@dataclass(frozen=True, slots=True)
class ReportAdmission:
    """一次报告汇编的产物（登记面与判据共用；字段就是它产出了什么）。"""

    artifact: Artifact
    report: str
    inputs: ReportInputs
    #: 报告制品**自身**的证据（本任务自产 ⇒ 不计入覆盖来源）。
    own_evidence: Evidence
    #: 本次汇编**消费**的检索证据（挂进同一个 claim；读面才看得到）。
    consumed: tuple[Evidence, ...]
    #: 本次汇编的 claim（报告的可复核归属）。
    claim: Claim
    #: 同源元数据（JSON 文本；供 `SCHEMA_VALID` 类判据与读面核对，不进报告正文）。
    metadata: str
    #: 叙述的归因面（GOAL-20261022-062；`None` = 确定性汇编，没有模型作者）。
    narrative: Any | None = None


def dispatch_report(deps: Any, tctx: Any) -> TaskExecutionResult:
    """契约**声明了**「由报告汇编器执行」⇒ 交给装配方声明的缝。

    声明是承诺：装配方没把汇编器接进来时**点名拒绝**（fail-closed），**不**静默回退到
    会话 —— 否则「声明了汇编」与「真的汇编了」会分叉，而 run 仍会显示成功
    （与 `dispatch_experiment` 同一条纪律）。
    """
    runner = deps.report_task
    if runner is None:
        return TaskExecutionResult(
            task=tctx.task,
            outcome="FAILED",
            message=(
                f"contract {tctx.contract.id} declares a report assembly "
                "but no report assembler is wired into this assembly"
            ),
            failure_category=FailureCategory.CONFIGURATION,
        )
    return runner(tctx.task, tctx.contract, tctx.spec_context, tctx.ctx.trace_id)  # type: ignore[no-any-return]


def execute_report_task(
    deps: ReportTaskDeps,
    task: ResearchTask,
    contract: TaskContract,
    spec_context: SessionSpecContext,
    trace_id: str,
) -> TaskExecutionResult:
    """一次报告汇编任务（契约声明 `report` ⇒ 派发到这里；**不**建会话）。"""
    del trace_id  # 本任务的执行体不是会话，没有会话级标识可用
    blocked = _admission_blocker(deps, task, contract, spec_context)
    if blocked is not None:
        return blocked
    try:
        assert deps.ledger is not None and deps.reviews is not None
        inputs = report_inputs(
            deps.artifacts, deps.ledger, deps.reviews, spec_context.run, task.run_id.value
        )
        report, narrative = _body(deps, inputs)
        admission = _admit(deps, task, inputs, report, narrative)
        manuscript = maybe_assemble_manuscript(deps, task, spec_context)
    except NarrativeError as error:
        # `ManuscriptError` 是 `NarrativeError` 的子类 ⇒ 手稿的每一种点名拒绝
        # （缺键 / 正文含数字 / 引用不闭合）都经这里以 `EXECUTION_FAILURE` 收敛。
        return _failed(
            task,
            f"narrative for run {task.run_id.value} is unusable: {error}",
            FailureCategory.EXECUTION_FAILURE,
        )
    except (ReportBuildError, ValueError, KeyError) as error:
        return _failed(
            task,
            f"report assembly for run {task.run_id.value} failed: {error}",
            FailureCategory.EXECUTION_FAILURE,
        )
    return TaskExecutionResult(
        task=task,
        outcome="SUCCEEDED",
        report_outcome=admission,
        attempts=task.attempt,
        message=assembled_message(admission, manuscript),
    )


def _admission_blocker(
    deps: ReportTaskDeps,
    task: ResearchTask,
    contract: TaskContract,
    spec_context: SessionSpecContext,
) -> TaskExecutionResult | None:
    """准入前的两件**声明面**缺件（缺则点名拒绝；齐了返回 `None`）。

    run 实体取自 spec（**在场的那份事实**）：执行期间控制面还没把 run 行落库
    （`run_from_execution` 在编排返回之后才写），去存储读只会读到「未知 run」。
    """
    missing = _missing_faces(deps)
    if missing is not None:
        return _failed(
            task,
            f"contract {contract.id} declares a report assembly but {missing} "
            "is not wired into this assembly",
            FailureCategory.CONFIGURATION,
        )
    if spec_context.run is None:
        return _failed(
            task,
            f"contract {contract.id} declares a report assembly but this run carries no "
            "RunContext entity: the report reads the run's protocol/state from it",
            FailureCategory.CONFIGURATION,
        )
    return None


def _failed(task: ResearchTask, message: str, category: FailureCategory) -> TaskExecutionResult:
    return TaskExecutionResult(
        task=task, outcome="FAILED", message=message, failure_category=category
    )


def _missing_faces(deps: ReportTaskDeps) -> str | None:
    """缺哪件装配（点名到**字段名**；齐了返回 `None`）。"""
    for name in ("ledger", "reviews"):
        if getattr(deps, name) is None:
            return name
    return None


def _body(deps: ReportTaskDeps, inputs: ReportInputs) -> tuple[str, Any | None]:
    """报告正文：接上了叙述者 ⇒ 模型写正文（数字留在事实表）；否则确定性汇编。

    **两态各自可判**：返回的第二个值是叙述归因面（`None` = 汇编器写的）——
    制品的 `created_by` 与 `report_metadata` 都从它推出「谁写的」。
    """
    if deps.narrator is None:
        return build_research_report(inputs), None
    narrated = narrate(inputs, deps.narrator)
    return narrated.report, narrated.admission


def _admit(
    deps: ReportTaskDeps,
    task: ResearchTask,
    inputs: ReportInputs,
    report: str,
    narrative: Any | None,
) -> ReportAdmission:
    """报告字节 → 内容寻址制品 + SourceRecord/Evidence/Claim（**唯一**准入入口）。"""
    assert deps.ledger is not None
    run_id = str(task.run_id.value)
    consumed = tool_evidence(evidence_of_run(deps.ledger, run_id))
    artifact = _put_report(deps.artifacts, task, report_digest_payload(report), inputs, narrative)
    own = _register_report_evidence(deps, run_id, artifact)
    claim = _register_report_claim(deps, task, run_id, own, consumed)
    return ReportAdmission(
        artifact=artifact,
        report=report,
        inputs=inputs,
        own_evidence=own,
        consumed=consumed,
        claim=claim,
        metadata=report_metadata(inputs, narrative),
        narrative=narrative,
    )


def _register_report_evidence(deps: ReportTaskDeps, run_id: str, artifact: Artifact) -> Evidence:
    """报告制品 → SourceRecord + Evidence（**GENERATED**：本系统汇编，不是外部取得）。"""
    assert deps.ledger is not None
    source = SourceRecord(
        origin=f"report:{run_id}:{_REPORT_NAME}",
        content_digest=str(artifact.digest),
        trust_label=TrustLabel.GENERATED,
        access_time=Timestamp.now(),
        parser_version="research-report-assembler-v1",
    )
    deps.ledger.register_source(source)
    own = Evidence(
        id=f"evidence:{artifact.id}",
        source_ref=source.origin,
        content_digest=str(artifact.digest),
        extracted_by=deps.actor,
        captured_at=Timestamp.now(),
        artifact_id=artifact.id,
        run_id=run_id,
    )
    deps.ledger.register_evidence(own)
    return own


def _register_report_claim(
    deps: ReportTaskDeps,
    task: ResearchTask,
    run_id: str,
    own: Evidence,
    consumed: tuple[Evidence, ...],
) -> Claim:
    """报告 + 它消费的检索证据 → 同一个 Claim（relations 全挂上；读面才看得到）。"""
    assert deps.ledger is not None
    claim_id = f"claim:{task.id.value}:result"
    related = (own, *consumed)
    claim = Claim(
        id=claim_id,
        statement=(
            f"Run {run_id} assembled {_REPORT_NAME} from its persisted facts "
            f"({len(consumed)} retrieval source(s) consumed)"
        ),
        status=ClaimStatus.PROPOSED,
        author=deps.actor,
        evidence_relations=[(item.id, EvidenceRelationType.SUPPORTS) for item in related],
    )
    deps.ledger.register_claim(claim)
    for item in related:
        deps.ledger.attach_relation(
            EvidenceRelation(
                claim_id=claim_id,
                evidence_id=item.id,
                relation=EvidenceRelationType.SUPPORTS,
            )
        )
    return claim


def _put_report(
    artifacts: ArtifactStore,
    task: ResearchTask,
    content: bytes,
    inputs: ReportInputs,
    narrative: Any | None,
) -> Artifact:
    """写报告制品（run 级 id；同一 run 重复汇编 ⇒ 覆盖写，内容寻址语义不变）。

    `created_by` 读得懂「谁写的」：`model:<endpoint>/<returned>`（模型撰写正文）或
    `system:report-assembler`（确定性汇编）—— 不靠读正文猜。
    """
    artifact = Artifact(
        id=report_artifact_id(inputs.run_id),
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type=REPORT_MIME,
        storage_uri=None,
        created_by=narrative.author if narrative is not None else "system:report-assembler",
        source_refs=[f"task:{task.id.value}", f"run:{inputs.run_id}"],
        classification="research_report",
    )
    artifacts.put(artifact, content)
    artifacts.mark(artifact.id, ArtifactState.VERIFIED)
    return artifact


def report_session_result(admission: ReportAdmission) -> AgentSessionResult:
    """给门一个**会话形状**的输入面（门接口既定；`SCHEMA_VALID` 类判据读它）。

    载荷是报告自己的**同源元数据**（`report_metadata`：run / 协议 / 计数 / 节清单），
    不是编造的研究结论 —— 它只让 `SCHEMA_VALID` 这类判据有东西可判。
    """
    payload = json.loads(admission.metadata)
    return AgentSessionResult(
        session_id=f"report:{admission.inputs.run_id}",
        status=AgentSessionState.State.SUCCEEDED,
        structured_output={_REPORT_NAME: payload, "report_metadata": payload},
    )


def registration_from_report(
    deps: Any, tctx: Any, admission: ReportAdmission
) -> ResultRegistration:
    """报告汇编 → `ResultRegistration`（自产件**不算**来源；声明输入 + 消费的检索证据算）。"""
    inputs = register_declared_input_sources(
        RegistrationDeps(
            store=deps.artifacts,
            agent_id=tctx.spec_context.agent.id,
            ledger=deps.ledger,
            declared_inputs=tctx.spec_context.declared_input_artifacts,
        ),
        tctx.task,
        claim_id=admission.claim.id,
    )
    if deps.ledger is not None:
        for evidence in inputs:
            deps.ledger.attach_relation(
                EvidenceRelation(
                    claim_id=admission.claim.id,
                    evidence_id=evidence.id,
                    relation=EvidenceRelationType.SUPPORTS,
                )
            )
    return ResultRegistration(
        artifacts=(admission.artifact,),
        evidence=(admission.own_evidence, *inputs, *admission.consumed),
        claims=(admission.claim,),
        # 自产件（报告本身）不计入覆盖 —— 与两条既有路径同一判别性质。
        self_artifact_ids=frozenset({admission.artifact.id}),
    )


def register_and_gate_report(deps: Any, tctx: Any, execution: Any) -> PhaseStep:
    """注册 + 验收一次报告汇编（与 `register_and_gate_experiment` 同形）。"""
    admission = execution.report_outcome
    assert isinstance(admission, ReportAdmission)
    registration = registration_from_report(deps, tctx, admission)
    gate = evaluate_gate(deps, tctx, registration, report_session_result(admission))
    record_acceptance_evaluation(deps, tctx, gate)
    if not gate.passed:
        return failure_step(
            deps,
            tctx,
            f"task {tctx.task.id.value} rejected by acceptance gate "
            f"({gate_rejection_reason(gate)})",
            False,
        )
    return finish_task_step(
        deps,
        tctx,
        registration,
        gate,
        producer=f"report:{tctx.spec_context.agent.id}",
    )


__all__ = [
    "ReportAdmission",
    "ReportTaskDeps",
    "dispatch_report",
    "execute_report_task",
    "register_and_gate_report",
    "registration_from_report",
    "report_artifact_id",
    "report_session_result",
]
