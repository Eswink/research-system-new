"""GOAL-20261031-102 EC-03：投稿包的**装配面**判据（结构化字段 + 两条反证臂）。

**它补哪一格**：产品入口那侧（`tests/e2e/test_direction_to_manuscript_product_path.py`）
判「五件制品经产品路径产出 + 正臂成立」；本文件判**判据自己能被按压红**：

- (ii) 反证：`author_contributions.md` 列一个本 run 没分派的角色 ⇒ 点名判红；
- (iii) 反证：`data_availability.md` 编造一个 digest ⇒ 点名判红；
- (iv) 反证：`has_conflict` 不是布尔 / COI 渲染没有结构化块 ⇒ 点名判红；
- 两种「空」：本 run 没有投稿会话产物 ⇒ 不装配（不是失败）；
- 坏声明（信缺失 / 布尔写成字符串 / 陈述为空）⇒ 报告任务 FAILED 且逐项点名。

夹具与 `test_revision_closure.py` 同一缝（`execute_report_task` + `test_manuscript_assembly`
的种面）；协议正文用**两相最小协议**（`research_director` + `domain_researcher`），
使「分派面」在判据里可穷举。
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from adapters.fakes.artifact_store import FakeArtifactStore
from packages.application.run_orchestration.report_task import (
    ReportTaskDeps,
    execute_report_task,
)
from packages.application.run_orchestration.submission_assembly import (
    SubmissionError,
    parse_coii_fields,
    parse_submission_statement,
    validate_contribution_roles,
    validate_inventory_digests,
)
from packages.application.run_orchestration.submission_renderers import (
    COI_NAME,
    CONTRIBUTIONS_NAME,
    COVER_LETTER_NAME,
    DATA_AVAILABILITY_NAME,
    SUPPLEMENTARY_NAME,
)
from packages.domain.core import ID
from packages.domain.protocol_source import ProtocolBody
from packages.domain.tasks import ResearchTask
from tests.application.test_manuscript_assembly import (
    _assets,
    _link,
    _put,
    _report_contract,
    _Reviews,
    _seed_narrative,
)

#: 两相最小协议正文（分派面在判据里可穷举：`research_director` + `domain_researcher`）。
_MINI_PROTOCOL = """id: mini_protocol_0_1_0
version: 0.1.0
phases:
  - id: question
    name: Question
    strategy: single_agent
    required_roles:
      - {role: research_director, min_instances: 1, max_instances: 1}
  - id: retrieval
    name: Retrieval
    strategy: single_agent
    required_roles:
      - {role: domain_researcher, min_instances: 1, max_instances: 1}
"""


def _statement_reply() -> str:
    """投稿会话的受控回复（布尔字段 + 一句查过什么的陈述）。"""
    block = json.dumps(
        {
            "submission_package": {
                "cover_letter": "This study asks what grounding the plan changes.",
                "conflict_of_interest": {
                    "has_conflict": False,
                    "statement": "The authors checked funding and employment for this run.",
                },
            }
        },
        ensure_ascii=False,
    )
    return "The submission statement follows.\n\n```json\n" + block + "\n```\n"


def _run_submission(
    *, reply: str | None = _statement_reply()
) -> tuple[Any, FakeArtifactStore, str]:
    """种入正文 + 记录 + 投稿会话产物，跑一次报告任务；`reply=None` ⇒ 不种投稿产物。"""
    run_id = ID.generate()
    store, ledger = _assets(run_id.value)
    _seed_narrative(store, ledger, run_id.value)
    if reply is not None:
        artifact = _put(
            store,
            f"{run_id.value}:submission:task-s:submission_package",
            {"content": reply, "declared_artifact": "submission_package"},
            "execution_result",
            run_id.value,
        )
        _link(ledger, artifact, tool=False, run_id=run_id.value)
    deps = ReportTaskDeps(artifacts=store, ledger=ledger, reviews=_Reviews(), manuscript=True)
    from packages.application.run_orchestration.task_executor import SessionSpecContext
    from packages.domain.enums import ActivationPolicy, ModelBindingMode, RoleCategory
    from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition

    context = SessionSpecContext(
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
        run=_run_of(run_id),
    )
    result = execute_report_task(
        deps,
        ResearchTask(id=ID.generate(), run_id=run_id),
        _report_contract(),
        context,
        "trace-1",
    )
    return result, store, run_id.value


def _run_of(run_id: ID) -> Any:
    """带**冻结协议正文**的 run 实体（分派面从 run 自己的正文读，不从磁盘）。"""
    from packages.domain.run import ResearchRun

    return ResearchRun(
        id=run_id,
        project_id="p-1",
        protocol_id="mini_protocol_0_1_0",
        state="SUCCEEDED",
        protocol_body=ProtocolBody.of(_MINI_PROTOCOL),
    )


def test_the_five_artifacts_are_assembled_and_registered() -> None:
    """正臂：五件制品落库（run 级 id），信的正文**逐字**来自会话产物。"""
    result, store, run_id = _run_submission()
    assert result.outcome == "SUCCEEDED", result.message
    for name in (
        COVER_LETTER_NAME,
        CONTRIBUTIONS_NAME,
        COI_NAME,
        DATA_AVAILABILITY_NAME,
        SUPPLEMENTARY_NAME,
    ):
        assert store.meta(f"{run_id}:{name}") is not None, name
    letter = store.get(f"{run_id}:{COVER_LETTER_NAME}").decode("utf-8")
    assert "This study asks what grounding the plan changes." in letter, letter[:300]


def test_contributions_derive_from_the_run_dispatch() -> None:
    """(ii) 正臂：列出的 CRediT 术语 ⊆ 本 run 分派（最小协议 ⇒ 恰好两个术语）。"""
    result, store, run_id = _run_submission()
    assert result.outcome == "SUCCEEDED", result.message
    body = store.get(f"{run_id}:{CONTRIBUTIONS_NAME}").decode("utf-8")
    assert "`research_director`" in body and "`domain_researcher`" in body
    assert "Conceptualization" in body and "Investigation" in body
    # 最小协议没有别的角色 ⇒ 不该出现别的 CRediT 术语。
    assert "Supervision" not in body, body


def test_the_read_face_refuses_an_invented_credit_role() -> None:
    """(ii) 反证：列一个分派没覆盖的 CRediT 术语 ⇒ 点名判红。"""
    with pytest.raises(SubmissionError, match="never carried"):
        validate_contribution_roles(["Software"], dispatched=["research_director"])


def test_the_read_face_refuses_a_fabricated_digest() -> None:
    """(iii) 反证：编造一个 digest ⇒ 点名判红。"""
    with pytest.raises(SubmissionError, match="does not carry"):
        validate_inventory_digests(["sha256:deadbeef"], inventory=["sha256:aa55"])


def test_the_conflict_field_is_read_as_a_field() -> None:
    """(iv) 正臂：COI 渲染里有结构化块，且字段与会话声明逐字段一致。"""
    result, store, run_id = _run_submission()
    assert result.outcome == "SUCCEEDED", result.message
    rendered = store.get(f"{run_id}:{COI_NAME}").decode("utf-8")
    has_conflict, statement = parse_coii_fields(rendered)
    assert has_conflict is False and "checked funding" in statement
    envelope = json.dumps({
        "content": _statement_reply(),
        "declared_artifact": "submission_package",
    })
    declared = parse_submission_statement(envelope)
    assert rendered and declared.has_conflict is False


def test_a_non_boolean_conflict_field_is_refused() -> None:
    """(iv) 反证：`has_conflict` 写成字符串 ⇒ 点名（字段不是散文）。"""
    bad = json.dumps({
        "submission_package": {
            "cover_letter": "x",
            "conflict_of_interest": {"has_conflict": "no", "statement": "y"},
        }
    })
    with pytest.raises(SubmissionError, match="must be a boolean"):
        parse_submission_statement(bad)


def test_a_prose_only_conflict_rendering_is_refused() -> None:
    """(iv) 反证：渲染成纯散文（没有结构化块）⇒ 点名。"""
    with pytest.raises(SubmissionError, match="no structured block"):
        parse_coii_fields("# Conflicts of Interest\n\nWe declare nothing.\n")


def test_a_run_without_a_submission_artifact_assembles_nothing() -> None:
    """两种「空」：没有投稿产物 ⇒ 五件都不产（不是失败，也不补造）。"""
    result, store, run_id = _run_submission(reply=None)
    assert result.outcome == "SUCCEEDED", result.message
    assert store.meta(f"{run_id}:{COVER_LETTER_NAME}") is None
    assert store.meta(f"{run_id}:{SUPPLEMENTARY_NAME}") is None


def test_a_submission_without_the_cover_letter_is_refused_by_name() -> None:
    """坏声明：信缺失 ⇒ 报告任务 FAILED 且点名（不产一份空壳投稿包）。"""
    bad = json.dumps(
        {
            "submission_package": {
                "conflict_of_interest": {"has_conflict": False, "statement": "y"},
            }
        },
        ensure_ascii=False,
    )
    result, store, run_id = _run_submission(reply=bad)
    assert result.outcome == "FAILED", result.message
    assert "cover_letter" in result.message, result.message
    assert store.meta(f"{run_id}:{COVER_LETTER_NAME}") is None


def test_a_submission_with_an_empty_statement_is_refused_by_name() -> None:
    """坏声明：`statement` 为空 ⇒ FAILED（声明要说出查过什么）。"""
    bad = json.dumps(
        {
            "submission_package": {
                "cover_letter": "x",
                "conflict_of_interest": {"has_conflict": False, "statement": "  "},
            }
        },
        ensure_ascii=False,
    )
    result, _store, _run_id = _run_submission(reply=bad)
    assert result.outcome == "FAILED", result.message
    assert "statement" in result.message, result.message


def test_the_availability_rows_are_the_run_inventory() -> None:
    """数据可得性的行 = 本 run 装配时点的制品清单（id + digest 两列都在）。"""
    result, store, run_id = _run_submission()
    assert result.outcome == "SUCCEEDED", result.message
    body = store.get(f"{run_id}:{DATA_AVAILABILITY_NAME}").decode("utf-8")
    narrative_id = f"{run_id}:manuscript_narrative"
    assert f"`{narrative_id}`" in body, body[:400]
    meta = store.meta(narrative_id)
    assert meta is not None and str(meta.digest) in body
