"""**跨相输入**的运行期解析与登记（GOAL-20261016-081 EC-04）。

**编译期**（`protocol_compile/cross_phase_inputs.py`）已把 `inputs` 里的
`{phase_id}:{artifact_name}` 校验并拆成 `(产出方 phase, 产物名, 性质)`。
**运行期**这里只做两件事：

1. **(a) 解析成真实制品 id**：run 内制品的 id 是 `{task_id}:{artifact_name}`，而任务 id
   在**编排期**才生成 ⇒ 协议里写不死。本模块按 **canonical 的任务身份**（idempotency key
   `{run_id}:{phase}:{agent}`，与 `service._remaining_specs` 同一句口径）把产出方的任务找出来，
   拼成真 id。**解析不了 / 产物不在库 / 内容校验不过 ⇒ 点名失败**（不静默跳过：
   那会让覆盖门在「来源其实不在」时通过）。

2. **(b) 性质随来源带走**：`trust_label` **原样取自编译产物**（`CompiledPhase
   .cross_phase_inputs` 的第三项），**不由读取方自报**。编译期那条判据是
   「产出方声明 `capability_execution: run_chain` 且它的 provider 声明了
   `network_domains`」—— 与 `phase_capabilities._trust_label_for` 同一口径。
   本模块**不**重新推导性质：运行期能看到的（ledger 里有没有 `RETRIEVED`）是**今天**
   的状态，而性质是**这个 phase 的声明性质**；两处各推一次必然漂。

**为什么是独立 origin（`cross-phase:`）而不是复用产出方的 origin**：产出方登记自己的产物时
已经写过一条 `SourceRecord(origin={task}:{name}, trust_label=GENERATED)`（那是**它的**自述）。
同 origin 再写一条不同性质的记录会被账本按 `same_source` 判成冲突 —— 这是既有语义，不该放宽。
跨相输入因此是一条**有向边**：`(读取方任务, 产出方产物)` 两个端点都在 origin 里，
与产出方自己的记录**不可能**相撞，也不会覆盖它。

**为什么需要 canonical 身份而不是内存传递**：跨 phase 没有内存通道
（`e2e/two_round_loop_support.py:20` 逐字），且 resume 会重算 tasks ⇒ 只有
idempotency key 是稳定身份（`WorkflowEngine.task_identities` 的既定语义）。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.ports.workflow_engine import WorkflowEngine
from packages.domain.enums import TrustLabel
from packages.domain.evidence import Evidence, SourceRecord
from packages.domain.tasks import ResearchTask

#: 跨相输入来源的 origin 前缀（有向边：读取方任务 + 产出方产物）。
CROSS_PHASE_ORIGIN_PREFIX = "cross-phase:"


@dataclass(frozen=True, slots=True)
class CrossPhaseSource:
    """一条**已解析**的跨相输入（读什么 + 它是什么性质）。"""

    origin: str
    artifact_id: str
    producer_phase_id: str
    artifact_name: str
    content_digest: str
    trust_label: TrustLabel


def producer_task_id(
    workflow: WorkflowEngine,
    task: ResearchTask,
    producer_phase_id: str,
) -> str:
    """产出方 phase 在本 run 的**真实任务 id**（按 idempotency key 的稳定身份）。

    `ResearchTask.idempotency_key` 的形状是 `{run_id}:{phase}:{agent}`
    （`session_resolution.resolve_sessions`）；产出方 phase 的 key 因此以
    `{run_id}:{producer_phase_id}:` 开头。找不到 / 多于一个 ⇒ **点名失败**。
    """
    prefix = f"{task.run_id.value}:{producer_phase_id}:"
    matches = [
        identity.task_id
        for identity in workflow.task_identities(task.run_id.value)
        if identity.idempotency_key.startswith(prefix)
    ]
    if not matches:
        raise InvalidInputError(
            f"cross-phase input from {producer_phase_id!r} cannot be resolved: no task of that"
            f" phase is registered in run {task.run_id.value}"
        )
    if len(matches) > 1:
        raise InvalidInputError(
            f"cross-phase input from {producer_phase_id!r} is ambiguous in run"
            f" {task.run_id.value}: {sorted(matches)}"
        )
    return matches[0]


def resolve_cross_phase_sources(
    workflow: WorkflowEngine,
    artifacts: ArtifactStore,
    task: ResearchTask,
    declared: tuple[tuple[str, str, TrustLabel], ...],
) -> tuple[CrossPhaseSource, ...]:
    """本 phase 的跨相输入 → `CrossPhaseSource` 序列（解析 / 校验失败 ⇒ 点名失败）。

    `declared` 来自 `CompiledPhase.cross_phase_inputs`（编译期已校验结构面与性质）。
    """
    resolved: list[CrossPhaseSource] = []
    for producer_phase_id, artifact_name, trust_label in declared:
        producer_task = producer_task_id(workflow, task, producer_phase_id)
        artifact_id = f"{producer_task}:{artifact_name}"
        meta = artifacts.meta(artifact_id)
        if meta is None:
            raise InvalidInputError(
                f"cross-phase input {producer_phase_id}:{artifact_name} is not in the artifact"
                f" store as {artifact_id} (the producer phase did not emit it)"
            )
        if not artifacts.verify(artifact_id):
            raise InvalidInputError(f"cross-phase input {artifact_id} failed content verification")
        resolved.append(
            CrossPhaseSource(
                origin=f"{CROSS_PHASE_ORIGIN_PREFIX}{task.id.value}:{artifact_id}",
                artifact_id=artifact_id,
                producer_phase_id=producer_phase_id,
                artifact_name=artifact_name,
                content_digest=str(meta.digest),
                trust_label=trust_label,
            )
        )
    return tuple(resolved)


def register_cross_phase_sources(
    ledger: EvidenceLedger | None,
    task: ResearchTask,
    sources: tuple[CrossPhaseSource, ...],
) -> tuple[Evidence, ...]:
    """跨相输入 → canonical 的 `SourceRecord` + `Evidence`（性质随来源带走）。

    与 `result_handler._input_evidence` 的**并列**关系（本 EC 的 (c)）：那条处理
    「组合根供给」（`USER_PROVIDED`，读仓库文件字节），本条处理「有性质的 phase 产出」
    （读上游产物 + 编译期性质）。两条都**不**看模型叙述。
    没有 ledger（装配未接）⇒ 不登记、返回空（覆盖门据实判拒，不静默通过）。
    """
    if ledger is None:
        return ()
    registered: list[Evidence] = []
    for source in sources:
        if not ledger.has_source(source.origin):
            ledger.register_source(
                SourceRecord(
                    origin=source.origin,
                    content_digest=source.content_digest,
                    trust_label=source.trust_label,
                    access_time=None,
                    parser_version="ec04-cross-phase-input-v1",
                )
            )
        evidence = Evidence(
            id=f"evidence:cross-phase:{source.artifact_id}:{task.id.value}",
            source_ref=source.origin,
            content_digest=source.content_digest,
            extracted_by="system:cross-phase-input",
            artifact_id=source.artifact_id,
            run_id=str(task.run_id.value),
        )
        ledger.register_evidence(evidence)
        registered.append(evidence)
    return tuple(registered)


def cross_phase_evidence(
    workflow: WorkflowEngine,
    artifacts: ArtifactStore,
    ledger: EvidenceLedger | None,
    task: ResearchTask,
    declared: tuple[tuple[str, str, TrustLabel], ...],
) -> tuple[Evidence, ...] | str:
    """本任务的跨相输入 → 登记出的证据；失败 ⇒ **点名的消息串**（调用方转成 task 失败）。

    把「解析 + 登记」收在一处（`phase_runner` 卡在 450 行规模门上，且这两步是同一件事
    的两半：解析出来的性质与登记时写下的性质必须是**同一条**事实）。
    """
    if not declared:
        return ()
    try:
        sources = resolve_cross_phase_sources(workflow, artifacts, task, declared)
    except InvalidInputError as error:
        return f"task {task.id.value} cannot read its cross-phase inputs: {error}"
    return register_cross_phase_sources(ledger, task, sources)


__all__ = [
    "CROSS_PHASE_ORIGIN_PREFIX",
    "CrossPhaseSource",
    "cross_phase_evidence",
    "producer_task_id",
    "register_cross_phase_sources",
    "resolve_cross_phase_sources",
]
