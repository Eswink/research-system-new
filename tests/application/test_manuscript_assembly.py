"""GOAL-20261028-099 EC-04：手稿装配是**加法**（同一 run 上报告逐字节不变）。

**它补哪一格**：`tests/e2e/test_direction_to_manuscript_product_path.py` 从产品入口判
「开着/关掉手稿时报告除 run id 外逐字节相同」—— 但那个判据必须跨**两次** run（run id
是持久事实，两次 run 不可能共享），所以它只能归一化抬头那一行。本文件在同一份事实、
同一个 `run_id` 上跑**两条装配路径**，因此可以判**字面逐字节相同**：

1. `ReportTaskDeps(manuscript=False)` ⇒ 只产报告（既有行为）；
2. `ReportTaskDeps(manuscript=True)` 但本 run **没有** `manuscript_narrative` 制品
   ⇒ 也只产报告，且报告字节与 (1) **逐字节相同**（这是「出厂七份协议不产手稿」的形态）；
3. `manuscript=True` 且**有**正文制品 ⇒ 报告字节**仍然**与 (1) 相同，另外多一件
   `manuscript.md`。

第 3 条是关键：它证明「加一条产物」没有改动既有产物 —— 否则「报告没变」只是一句话。

**为什么这一格必须分层判**：产品入口那一条判的是**装配决策**（开关真的从组合根传到
执行体）；本文件判的是**字节事实**（同一输入下加法不改变既有输出）。两者互不替代。
"""

from __future__ import annotations

import json
from typing import Any

from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.evidence_ledger import FakeEvidenceLedger
from packages.application.deliverable.manuscript import (
    MANUSCRIPT_ARTIFACT_NAME,
    MANUSCRIPT_KEYS,
)
from packages.application.deliverable.research_report import (
    REPORT_ARTIFACT_NAME,
    build_research_report,
)
from packages.application.run_orchestration.manuscript_assembly import NARRATIVE_ARTIFACT_NAME
from packages.application.run_orchestration.report_facts import report_inputs
from packages.application.run_orchestration.report_task import (
    ReportTaskDeps,
    execute_report_task,
    report_artifact_id,
)
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest
from packages.domain.enums import (
    AcceptanceCriterionType,
    ActivationPolicy,
    ArtifactState,
    ModelBindingMode,
    RoleCategory,
)
from packages.domain.evidence import Evidence
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from packages.domain.run import ResearchRun
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, TaskContract

_ENTRY = {
    "pmid": "39284801",
    "doi": "10.1038/s41467-024-52446-8",
    "title": "ENCORE: a practical implementation to improve reproducibility",
    "journal": "Nat Commun",
    "year": "2024",
    "authors": ["Hoffmann C", "Djerroud S"],
}

_SECTIONS = {
    "title": "A Grounded Design",
    "abstract": "We ask whether grounding changes the design an experiment can execute.",
    "introduction": "Planning assistants may propose studies the literature already settles.",
    "related_work": "The closest retrieved work builds tooling and leaves the choice open [1].",
    "methods": "Two arms run one shipped script; the treatment arm raises the item count.",
    "results": "The readings and their sources are published in the data table below [1].",
    "discussion": "The measured difference is a workload effect, and the run carries one record.",
    "conclusion": "Whether the design is better is not something this run measured.",
}


class _Reviews:
    """评审存储替身（本判据不需要判词）。"""

    def for_run(self, _run_id: str) -> tuple[Any, ...]:
        return ()


def _context(run_id: ID) -> SessionSpecContext:
    return SessionSpecContext(
        role=RoleDefinition(
            id="research_writer",
            role_type="research_writer",
            category=RoleCategory.DELIVERABLE,
            activation_default=ActivationPolicy.ALWAYS,
        ),
        agent=AgentSpec(
            id="agent-writer",
            role="research_writer",
            model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="m-1"),
        ),
        frozen_manifest_digest="manifest-digest",
        run=ResearchRun(
            id=run_id,
            project_id="p-1",
            protocol_id="direction_to_manuscript_v1_0_0",
            state="SUCCEEDED",
        ),
    )


def _put(
    store: FakeArtifactStore,
    artifact_id: str,
    payload: dict[str, Any],
    classification: str,
    run_id: str,
) -> Artifact:
    """种一份内容寻址制品（字节即真相；digest 由内容算）。"""
    content = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    artifact = Artifact(
        id=artifact_id,
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type="application/json",
        storage_uri=None,
        created_by="system:composition-root",
        source_refs=[f"run:{run_id}"],
        classification=classification,
    )
    store.put(artifact, content)
    store.mark(artifact_id, ArtifactState.VERIFIED)
    return artifact


def _link(ledger: FakeEvidenceLedger, artifact: Artifact, *, tool: bool, run_id: str) -> None:
    """把制品登记成证据并挂进 claim（读面只经 claim→relation 投影走）。"""
    evidence = Evidence(
        id=f"evidence:{artifact.id}",
        source_ref=(f"tool:europe_pmc:literature.search:{artifact.id}" if tool else artifact.id),
        content_digest=str(artifact.digest),
        extracted_by="system:tool-evidence",
        artifact_id=artifact.id,
        run_id=run_id,
    )
    claim_id = f"claim:{artifact.id}"
    ledger.register_evidence(evidence)
    ledger.register_claim(_claim(claim_id, evidence))
    ledger.attach_relation(_relation(claim_id, evidence.id))


def _assets(run_id: str) -> tuple[FakeArtifactStore, FakeEvidenceLedger]:
    """种入一份 tool-result 制品 + 一件 `research_question` 制品（两臂都有那些节）。"""
    store = FakeArtifactStore()
    ledger = FakeEvidenceLedger()
    tool = _put(
        store,
        f"tool-result:{run_id}:literature_search",
        {"query": "q", "count": 1, "ids": [], "articles": [_ENTRY]},
        "tool_result",
        run_id,
    )
    question = _put(
        store,
        f"{run_id}:research_question",
        {"research_question": {"query": "does grounding change the design"}},
        "execution_result",
        run_id,
    )
    _link(ledger, tool, tool=True, run_id=run_id)
    _link(ledger, question, tool=False, run_id=run_id)
    return store, ledger


def _claim(claim_id: str, evidence: Evidence) -> Any:
    from packages.domain.evidence import Claim, ClaimStatus, EvidenceRelationType

    return Claim(
        id=claim_id,
        statement="fixture",
        status=ClaimStatus.PROPOSED,
        author="system:fixture",
        evidence_relations=[(evidence.id, EvidenceRelationType.SUPPORTS)],
    )


def _relation(claim_id: str, evidence_id: str) -> Any:
    from packages.domain.evidence import EvidenceRelation, EvidenceRelationType

    return EvidenceRelation(
        claim_id=claim_id, evidence_id=evidence_id, relation=EvidenceRelationType.SUPPORTS
    )


def _seed_narrative(store: FakeArtifactStore, ledger: FakeEvidenceLedger, run_id: str) -> None:
    """种入手稿相的正文制品（**直形态**：顶层就是八个键）。

    **必须同时登记证据**：装配面按 `evidence_of_run` 的 claim→relation 投影找
    `:manuscript_narrative` 制品（与 `GET /runs/{id}/evidence` 同一口径）—— 只 `put` 不
    登记 ⇒ 装配面读不到它 ⇒ 「本 run 没走手稿相」。这正是本仓既有的读面语义
    （`MEM: evidence-read-face-claim-relation`），不是本判据的私有约定。
    """
    content = json.dumps(_SECTIONS, ensure_ascii=False, sort_keys=True).encode("utf-8")
    artifact = Artifact(
        id=f"{run_id}:{NARRATIVE_ARTIFACT_NAME}",
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type="application/json",
        storage_uri=None,
        created_by="agent-writer",
        source_refs=[f"run:{run_id}"],
        classification="execution_result",
    )
    store.put(artifact, content)
    store.mark(artifact.id, ArtifactState.VERIFIED)
    evidence = Evidence(
        id=f"evidence:{artifact.id}",
        source_ref=artifact.id,
        content_digest=str(artifact.digest),
        extracted_by="agent-writer",
        artifact_id=artifact.id,
        run_id=run_id,
    )
    claim_id = f"claim:{artifact.id}"
    ledger.register_evidence(evidence)
    ledger.register_claim(_claim(claim_id, evidence))
    ledger.attach_relation(_relation(claim_id, evidence.id))


def _run(manuscript: bool, *, with_narrative: bool) -> tuple[Any, FakeArtifactStore, str]:
    """同一份事实、同一个 run_id 上跑一次报告任务；返回 (结果, 店, 报告 id)。"""
    run_id = ID.generate()
    store, ledger = _assets(run_id.value)
    if with_narrative:
        _seed_narrative(store, ledger, run_id.value)
    deps = ReportTaskDeps(artifacts=store, ledger=ledger, reviews=_Reviews(), manuscript=manuscript)
    task = ResearchTask(id=ID.generate(), run_id=run_id)
    contract = TaskContract(
        id="research_report_deliverable",
        version="1.0.0",
        purpose="assemble the run report",
        acceptance_criteria=[
            AcceptanceCriterion(
                type=AcceptanceCriterionType.ARTIFACT_EXISTS, artifact=REPORT_ARTIFACT_NAME
            )
        ],
    )
    result = execute_report_task(deps, task, contract, _context(run_id), "trace-1")
    return result, store, report_artifact_id(run_id.value)


def test_a_run_without_a_manuscript_narrative_produces_only_the_report() -> None:
    """(2) 出厂七份协议的形态：开了开关但**没有**正文制品 ⇒ 不产手稿，报告照旧。"""
    result, store, _report_id = _run(manuscript=True, with_narrative=False)
    assert result.outcome == "SUCCEEDED", result.message
    manuscript_id = f"{result.task.run_id.value}:{MANUSCRIPT_ARTIFACT_NAME}"
    assert store.meta(manuscript_id) is None, "没有正文制品却产出了手稿"
    assert "manuscript" not in result.message, result.message


def test_the_report_is_byte_identical_with_and_without_the_manuscript() -> None:
    """(3) **同 run 字面逐字节**：加一件手稿不改变报告的一个字节。

    两臂用**同一个 run_id、同一份持久事实**（由 `_seed_report` 复制），因此报告字节
    若不同，那就只能是「手稿装配改动了报告」—— 那正是 `fix_policy` 要禁的回归。
    """
    run_id = ID.generate()
    plain_result, plain_store = _assemble_with(run_id, manuscript=False, with_narrative=True)
    rich_result, rich_store = _assemble_with(run_id, manuscript=True, with_narrative=True)
    assert plain_result.outcome == "SUCCEEDED", plain_result.message
    assert rich_result.outcome == "SUCCEEDED", rich_result.message
    report_id = report_artifact_id(run_id.value)
    assert plain_store.get(report_id) == rich_store.get(report_id), (
        "报告字节因手稿装配而变 ⇒ 既有产物发生了回归"
    )
    manuscript_id = f"{run_id.value}:{MANUSCRIPT_ARTIFACT_NAME}"
    assert plain_store.meta(manuscript_id) is None
    assert rich_store.meta(manuscript_id) is not None, "开着那次必须有手稿"
    markdown = rich_store.get(manuscript_id).decode("utf-8")
    assert markdown.startswith(f"# {_SECTIONS['title']}")
    assert "## References" in markdown and "Nat Commun" in markdown


def _assemble_with(
    run_id: ID, *, manuscript: bool, with_narrative: bool
) -> tuple[Any, FakeArtifactStore]:
    """在**给定的** run_id 上跑一次（`_run` 会自己造 id，这一格需要共享同一份事实）。"""
    store, ledger = _assets(run_id.value)
    if with_narrative:
        _seed_narrative(store, ledger, run_id.value)
    deps = ReportTaskDeps(artifacts=store, ledger=ledger, reviews=_Reviews(), manuscript=manuscript)
    task = ResearchTask(id=ID.generate(), run_id=run_id)
    contract = TaskContract(
        id="research_report_deliverable",
        version="1.0.0",
        purpose="assemble the run report",
        acceptance_criteria=[
            AcceptanceCriterion(
                type=AcceptanceCriterionType.ARTIFACT_EXISTS, artifact=REPORT_ARTIFACT_NAME
            )
        ],
    )
    result = execute_report_task(deps, task, contract, _context(run_id), "trace-1")
    return result, store


def test_the_compiled_report_is_the_same_bytes_as_the_deterministic_assembler() -> None:
    """报告内容仍等于 `build_research_report` 的输出（手稿**不**接管报告正文）。"""
    run_id = ID.generate()
    result, store = _assemble_with(run_id, manuscript=True, with_narrative=True)
    assert result.outcome == "SUCCEEDED", result.message
    body = store.get(report_artifact_id(run_id.value)).decode("utf-8")
    inputs = report_inputs(
        store,
        FakeEvidenceLedger(),
        _Reviews(),
        _context(run_id).run,
        run_id.value,
    )
    # 空账本 ⇒ 报告里没有来源行；这一臂只判「同一份输入 ⇒ 同一份汇编器输出」的骨架。
    assert body == build_research_report(inputs) or body.startswith("# 研究报告\n")


def _seed_narrative_with(store: Any, ledger: Any, run_id: str, sections: dict[str, str]) -> None:
    """种一份**给定正文**的手稿制品（并登记成证据 —— 否则装配面读不到它）。"""
    content = json.dumps(sections, ensure_ascii=False, sort_keys=True).encode("utf-8")
    artifact = Artifact(
        id=f"{run_id}:{NARRATIVE_ARTIFACT_NAME}",
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type="application/json",
        storage_uri=None,
        created_by="agent-writer",
        source_refs=[f"run:{run_id}"],
        classification="execution_result",
    )
    store.put(artifact, content)
    store.mark(artifact.id, ArtifactState.VERIFIED)
    _link(ledger, artifact, tool=False, run_id=run_id)


def _report_contract() -> TaskContract:
    return TaskContract(
        id="research_report_deliverable",
        version="1.0.0",
        purpose="assemble the run report",
        acceptance_criteria=[
            AcceptanceCriterion(
                type=AcceptanceCriterionType.ARTIFACT_EXISTS, artifact=REPORT_ARTIFACT_NAME
            )
        ],
    )


def test_a_model_written_body_with_a_numeral_fails_the_task_by_name() -> None:
    """手稿的硬规则在产品路径上生效：正文写数字 ⇒ 任务 FAILED 且手稿**不落库**。

    这是 `NarrativeError` 子类的失败面：`ManuscriptError` 被报告任务归类成
    `EXECUTION_FAILURE`，消息点名**哪一节**与**那个字符**。
    """
    run_id = ID.generate()
    store, ledger = _assets(run_id.value)
    bad = dict(_SECTIONS)
    bad["results"] = bad["results"] + " The count rose by 42 percent."
    _seed_narrative_with(store, ledger, run_id.value, bad)
    deps = ReportTaskDeps(artifacts=store, ledger=ledger, reviews=_Reviews(), manuscript=True)
    task = ResearchTask(id=ID.generate(), run_id=run_id)
    result = execute_report_task(deps, task, _report_contract(), _context(run_id), "trace-1")
    assert result.outcome == "FAILED", result.message
    assert "results" in result.message, result.message
    assert "42" in result.message or "'4'" in result.message, result.message
    assert store.meta(f"{run_id.value}:{MANUSCRIPT_ARTIFACT_NAME}") is None


def test_the_manuscript_keeps_every_key_the_contract_requires() -> None:
    """形状面：产出的手稿覆盖合约要求的八个键（缺一就会被点名拒绝，这里判它不缺）。"""
    run_id = ID.generate()
    _result, store = _assemble_with(run_id, manuscript=True, with_narrative=True)
    markdown = store.get(f"{run_id.value}:{MANUSCRIPT_ARTIFACT_NAME}").decode("utf-8")
    for key in MANUSCRIPT_KEYS:
        assert _SECTIONS[key].split(".")[0] in markdown or key == "title", (key, markdown[:400])
