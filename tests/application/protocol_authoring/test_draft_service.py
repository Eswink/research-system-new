"""DraftService 校验与模板目录测试（PLAN-20260908-033 AC-03/AC-07）。

覆盖：合法协议 YAML 通过；schema 违规可定位；重复键拒绝；体积限制；
模板目录只读受控来源；零副作用（纯函数，不触任何 store 写路径）。
"""

from __future__ import annotations

import pytest

from packages.application.protocol_authoring import (
    DraftService,
    DraftTemplates,
    InMemoryProtocolDraftStore,
    ProtocolDraftValidationError,
)
from packages.application.protocol_authoring.service import (
    DraftTemplateSource,
    ProtocolDraftSizeError,
    validate_yaml_document,
)

_VALID = """id: sort_analysis_v1_0_1
version: 0.4.0
phases:
  - id: execution
    strategy: single_agent
    required_roles:
      - {role: experiment_engineer, min_instances: 1, max_instances: 1}
    task_contract: sort_analysis_execution
    timeout_seconds: 120
  - id: review
    strategy: single_agent
    depends_on: [execution]
    required_roles:
      - {role: scientific_reviewer, min_instances: 1, max_instances: 1}
    task_contract: sort_analysis_review
    gate: QUALITY_GATE
"""


def test_valid_protocol_yaml_passes() -> None:
    result = validate_yaml_document(_VALID)
    assert result.ok is True
    assert result.protocol_id == "sort_analysis_v1_0_1"
    assert result.phase_count == 2
    assert result.protocol_digest is not None
    assert result.protocol_digest.startswith("sha256:")


def test_schema_violation_is_locatable() -> None:
    bad = _VALID.replace("id: sort_analysis_v1_0_1", "id: Bad ID With Spaces")
    result = validate_yaml_document(bad)
    assert result.ok is False
    codes = {issue.code for issue in result.issues}
    assert "SCHEMA_INVALID" in codes
    assert any("id" in issue.path for issue in result.issues)


def test_unknown_field_rejected_by_schema() -> None:
    bad = _VALID + "objectives:\n  - id: obj_x\n    statement: hack the schema\n"
    result = validate_yaml_document(bad)
    assert result.ok is False


def test_duplicate_key_rejected() -> None:
    # 顶级重复键：strict loader 必须拒绝（后键覆盖前键是静默数据丢失）
    base = "id: a_v1_0_1\nversion: 0.4.0\nphases: []\n"
    dup = base + "version: 9.9.9\n"
    result = validate_yaml_document(dup)
    assert result.ok is False
    assert any(issue.code == "YAML_PARSE" for issue in result.issues)
    assert any("duplicate key" in issue.message for issue in result.issues)

    # phase 内重复键同样拒绝
    text_with_dup = _VALID.replace(
        "    timeout_seconds: 120\n",
        "    timeout_seconds: 120\n    timeout_seconds: 999\n",
        1,
    )
    dup_result = validate_yaml_document(text_with_dup)
    assert dup_result.ok is False
    assert any(issue.code == "YAML_PARSE" for issue in dup_result.issues)


def test_non_mapping_yaml_rejected() -> None:
    result = validate_yaml_document("- just\n- a\n- list\n")
    assert result.ok is False
    assert result.issues[0].code == "SCHEMA_TYPE"


def test_size_limit_enforced() -> None:
    from packages.application.protocol_authoring.service import MAX_YAML_BYTES

    huge = "# pad\n" * (MAX_YAML_BYTES // 4)
    with pytest.raises(ProtocolDraftSizeError):
        validate_yaml_document(huge)


def test_templates_only_from_registered_sources() -> None:
    templates = DraftTemplates((
        DraftTemplateSource("sort", "Sort 分析", "2-phase 参考", "sort_analysis_v1.yaml"),
    ))
    listed = templates.list()
    assert len(listed) == 1
    body = templates.get("sort")
    assert body is not None
    assert "sort_analysis_v1_0_1" in body.yaml_text
    assert body.source == "examples/protocols/sort_analysis_v1.yaml"
    assert templates.get("missing") is None


def test_draft_service_create_rejects_invalid() -> None:
    store = InMemoryProtocolDraftStore()
    templates = DraftTemplates(())
    service = DraftService(store, templates)
    with pytest.raises(ProtocolDraftValidationError):
        service.create(name="bad", yaml_text="not: a: protocol", idempotency_key="k1")
    record = service.create(name="ok", yaml_text=_VALID, idempotency_key="k2")
    assert record.revision == 1
    assert service.get(record.draft_id) is not None


def test_draft_service_save_validates_before_store() -> None:
    store = InMemoryProtocolDraftStore()
    service = DraftService(store, DraftTemplates(()))
    record = service.create(name="ok", yaml_text=_VALID, idempotency_key="k1")
    with pytest.raises(ProtocolDraftValidationError):
        service.save(
            record.draft_id,
            yaml_text="invalid: [",
            expected_revision=1,
            idempotency_key="k2",
        )
    # 校验失败的保存不产生新修订
    assert len(service.list_revisions(record.draft_id)) == 1
