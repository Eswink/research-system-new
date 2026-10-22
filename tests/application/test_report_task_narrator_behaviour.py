"""`execute_report_task` **接上叙述者之后的真实行为**判据（GOAL-20261022-094 EC-04）。

**为什么要单独一个文件**：`tests/application/test_report_narrative_on_the_product_path.py`
原来判「接不接叙述者 ⇒ `_body` 的返回值不同」，其中「`created_by` 读 `narrative.author`」
只是 **`inspect.getsource` 的子串**证明 —— 那是**代码形态**，不是**行为**：把那一行改成
`narrative.author or "x"` 或干脆写死一个常量，子串判据仍绿而制品上的作者已经错了。

本文件把整条路径**真的跑一遍**：`execute_report_task` → 读事实 → 叙述者 → `_admit` →
`FakeArtifactStore`；然后**从 store 读回 Artifact**，判 `created_by` / digest / 元数据 /
证据。`llm_narrator` 也走**正常解析路径**（假 gateway + 假 resolver），不只测凭据缺失的分支。

判据面（每条独立取证）：

1. **接叙述者 ⇒ 制品作者是模型**：`store.meta(id).created_by == "model:<endpoint>/<returned>"`，
   且**不是** `system:report-assembler`；报告正文有第 5 节事实表；元数据 `narrative` 块
   与制品作者**同源**。
2. **不接 ⇒ 制品作者仍是汇编器**，且正文与既有确定性汇编**逐字节相同**（从 store 读回内容比）。
3. **模型写数字 ⇒ 任务 FAILED 且没有制品落库**（点名键与字符；不产出「看起来像报告」的东西）。
4. **`llm_narrator` 正常路径**：假 gateway 返回合规 JSON ⇒ 归因面正确（`author` 用**返回名**
   而不是声明名，AGENTS.md §4）、digest 由正文重算、四键齐备；声明名与返回名不同时
   **两者都可见**。
5. **`llm_narrator` 畸形输出**（非 JSON / 缺键）⇒ 点名拒绝，**不**把空叙述当成功。
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.evidence_ledger import FakeEvidenceLedger
from packages.application.deliverable.report_narrative import (
    FACT_TABLE_HEADING,
    NarrativeError,
    narrative_digest,
)
from packages.application.deliverable.research_report import (
    REPORT_ARTIFACT_NAME,
    ReportInputs,
    build_research_report,
)
from packages.application.ports.model_gateway import CompletionResult
from packages.application.run_orchestration.report_narrative_task import (
    NarratorUnavailable,
    llm_narrator,
)
from packages.application.run_orchestration.report_task import (
    ReportTaskDeps,
    execute_report_task,
    report_artifact_id,
)
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.domain.core import ID
from packages.domain.enums import (
    AcceptanceCriterionType,
    ActivationPolicy,
    ModelBindingMode,
    RoleCategory,
)
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from packages.domain.run import ResearchRun
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, TaskContract

_BODY = {
    "question": "The run asked how a controlled change affects the work the pipeline performs.",
    "evidence": "The retrieval stage returned records listed in the table.",
    "experiment": "Arms ran under one script; their readings appear in the table by name.",
    "review": "The reviewer accepted the run; the decision is quoted in the table.",
}


class _Reviews:
    """评审存储替身（本判据不需要判词 ⇒ 永远空）。"""

    def for_run(self, _run_id: str) -> tuple[Any, ...]:
        return ()


def _narrator(body: dict[str, str] | None = None, *, author: str = "model:main/twin-a") -> Any:
    sections = dict(_BODY if body is None else body)

    def narrate(_prompt: str) -> Any:
        from packages.application.deliverable.report_narrative import NarrativeAdmission

        return NarrativeAdmission(
            author=author,
            returned_model=author.rsplit("/", 1)[-1],
            digest=narrative_digest(sections),
            sections=sections,
        )

    return narrate


def _context() -> SessionSpecContext:
    run_id = ID.generate()
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
            protocol_id="research_report_chain_v1",
            state="SUCCEEDED",
        ),
    )


def _run_task(narrator: Any | None) -> tuple[Any, FakeArtifactStore, FakeEvidenceLedger, str]:
    """真的跑一次 `execute_report_task`；返回 (结果, 制品店, 账本, 报告 id)。"""
    artifacts = FakeArtifactStore()
    ledger = FakeEvidenceLedger()
    deps = ReportTaskDeps(
        artifacts=artifacts,
        ledger=ledger,
        reviews=_Reviews(),
        narrator=narrator,
    )
    context = _context()
    task = ResearchTask(id=ID.generate(), run_id=context.run.id)  # type: ignore[union-attr]
    contract = TaskContract(
        id="research_report_deliverable",
        version="1.0.0",
        purpose="assemble the run report",
        acceptance_criteria=[
            AcceptanceCriterion(
                type=AcceptanceCriterionType.ARTIFACT_EXISTS,
                artifact=REPORT_ARTIFACT_NAME,
            )
        ],
    )
    result = execute_report_task(deps, task, contract, context, "trace-1")
    # `str(ID)` 是 dataclass 的 repr（`ID(value='…')`），不是 UUID 文本 ⇒ 必须取 `.value`。
    run_uuid = context.run.id.value  # type: ignore[union-attr]
    return result, artifacts, ledger, report_artifact_id(run_uuid)


def test_the_artifact_created_by_is_the_model_when_a_narrator_is_wired() -> None:
    """**核心**：接上叙述者 ⇒ 从 store 读回的 `created_by` 是**模型**（不是写死）。"""
    result, artifacts, _ledger, report_id = _run_task(_narrator())

    assert result.outcome == "SUCCEEDED", result.message
    stored = artifacts.meta(report_id)
    assert stored is not None, "报告制品没有落库"
    assert stored.created_by == "model:main/twin-a", stored.created_by
    assert stored.created_by != "system:report-assembler"

    body = artifacts.get(report_id).decode("utf-8")
    assert FACT_TABLE_HEADING in body
    metadata = json.loads(result.report_outcome.metadata)
    assert metadata["narrative"]["author"] == stored.created_by, metadata["narrative"]
    assert metadata["narrative"]["returned_model"] == "twin-a"


def test_the_created_by_follows_a_different_narrator() -> None:
    """换一个作者 ⇒ 制品作者跟着变（证明它读的是归因面，不是常量）。"""
    _result, artifacts, _ledger, report_id = _run_task(_narrator(author="model:main/other-x"))
    stored = artifacts.meta(report_id)
    assert stored is not None and stored.created_by == "model:main/other-x", stored


def test_without_a_narrator_the_artifact_is_the_compiled_report_byte_for_byte() -> None:
    """零回归：不接叙述者 ⇒ 制品作者是汇编器，且正文与既有汇编**逐字节**相同。"""
    result, artifacts, _ledger, report_id = _run_task(None)

    assert result.outcome == "SUCCEEDED", result.message
    stored = artifacts.meta(report_id)
    assert stored is not None and stored.created_by == "system:report-assembler"
    body = artifacts.get(report_id).decode("utf-8")
    assert FACT_TABLE_HEADING not in body
    # 与既有汇编器对**同一份事实**的输出逐字节相同（事实来自同一批读面）
    inputs = result.report_outcome.inputs
    assert isinstance(inputs, ReportInputs)
    assert body == build_research_report(inputs)


def test_a_numeral_from_the_model_fails_the_task_and_leaves_no_artifact() -> None:
    """模型写数字 ⇒ FAILED **且没有制品落库**（点名键与字符）。"""
    bad = {**_BODY, "experiment": "The count dropped by 125.5 percent."}
    result, artifacts, _ledger, report_id = _run_task(_narrator(bad))

    assert result.outcome == "FAILED", result.message
    assert "experiment" in result.message and "'1'" in result.message, result.message
    assert artifacts.meta(report_id) is None, "失败的叙述不得留下报告制品"


def test_the_artifact_name_is_unchanged() -> None:
    """制品名与既有契约一致（读面 / live 判据都按它取）。"""
    _result, artifacts, _ledger, report_id = _run_task(None)
    assert report_id.endswith(f":{REPORT_ARTIFACT_NAME}")
    assert artifacts.meta(report_id) is not None


class _Gateway:
    """假模型网关：返回预置内容（`returned_model_name` 可不同于声明名）。"""

    def __init__(self, content: str | None, returned: str | None = "dsv4-flash-vision") -> None:
        self.content = content
        self.returned = returned
        self.calls: list[Any] = []

    def complete(self, _endpoint: Any, _secret: Any, request: Any) -> CompletionResult:
        self.calls.append(request)
        return CompletionResult(content=self.content, returned_model_name=self.returned)


class _Resolver:
    """假凭据解析器：正常路径返回一个占位 secret（**不读环境、不落盘**）。"""

    def resolve(self, ref: str) -> str:
        assert ref == "LLM_MAIN_KEY", ref
        return "placeholder-secret"


class _Endpoint:
    id = "main"


def test_llm_narrator_on_the_happy_path_attributes_the_returned_model() -> None:
    """**正常路径**：假 gateway 返回合规 JSON ⇒ 归因面用**返回名**、digest 由正文重算。"""
    gateway = _Gateway(json.dumps(_BODY, ensure_ascii=False))
    narrator = llm_narrator(
        gateway=gateway,
        credentials=_Resolver(),
        endpoint=_Endpoint(),
        model_name="declared-model",
        credential_ref="LLM_MAIN_KEY",
    )
    admission = narrator("prompt")

    assert len(gateway.calls) == 1, "gateway 必须被真的调用一次"
    assert admission.author == "model:main/dsv4-flash-vision", admission.author
    assert admission.returned_model == "dsv4-flash-vision"
    assert admission.digest == narrative_digest(_BODY)
    assert set(admission.sections) == set(_BODY)
    # 声明名与返回名不同时**两者都可见**（同名漂移必须可见，AGENTS.md §4）
    assert "declared-model" not in admission.author
    assert admission.returned_model != "declared-model"


def test_llm_narrator_names_a_malformed_or_incomplete_response() -> None:
    """畸形 / 缺键 ⇒ 点名拒绝（不把空叙述当成功）。"""
    for content, needle in (
        ("not json", "not a JSON object"),
        (json.dumps({**_BODY, "review": ""}), "review"),
        (json.dumps({**_BODY, "review": "scored 4 of 5"}), "'4'"),
    ):
        narrator = llm_narrator(
            gateway=_Gateway(content),
            credentials=_Resolver(),
            endpoint=_Endpoint(),
            model_name="declared-model",
            credential_ref="LLM_MAIN_KEY",
        )
        with pytest.raises(NarrativeError) as raised:
            narrator("prompt")
        assert needle in str(raised.value), (needle, str(raised.value))


def test_llm_narrator_refuses_without_a_resolvable_credential() -> None:
    """凭据拿不到 ⇒ `NarratorUnavailable`（装配面问题，不是模型问题）。"""

    class _Missing:
        def resolve(self, _ref: str) -> Any:
            raise RuntimeError("no such credential")

    narrator = llm_narrator(
        gateway=_Gateway(json.dumps(_BODY)),
        credentials=_Missing(),
        endpoint=_Endpoint(),
        model_name="declared-model",
        credential_ref="LLM_MAIN_KEY",
    )
    with pytest.raises(NarratorUnavailable) as raised:
        narrator("prompt")
    assert "LLM_MAIN_KEY" in str(raised.value)
