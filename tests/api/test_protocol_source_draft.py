"""协议来源草稿修订测试（PLAN-20260910-037 WP-B）。

validate / compile / preflight / dry-run 四端点接受不可变草稿修订引用，
与受控模板 path 二选一；错误语义同 runs start（422/404）。
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi.testclient import TestClient

_VALID_DRAFT_YAML = open(
    "examples/protocols/m12_reference_research_v1.yaml", encoding="utf-8"
).read()

_ANALYSIS_HEADERS: dict[str, str] = {}


def _create_draft(client: TestClient, name: str) -> dict[str, Any]:
    response = client.post(
        "/projects/example-project/protocol-drafts",
        json={"name": name, "yaml_text": _VALID_DRAFT_YAML},
        headers={"Idempotency-Key": f"draft-{uuid.uuid4()}"},
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def _ref(draft: dict[str, Any]) -> dict[str, Any]:
    return {"draft_id": draft["draft_id"], "draft_revision": draft["revision"]}


def test_draft_revision_validate_compile_preflight_dryrun(client: TestClient) -> None:
    draft = _create_draft(client, "wpb-draft")
    validate = client.post("/protocols/validate", json=_ref(draft), headers=_ANALYSIS_HEADERS)
    assert validate.status_code == 200, validate.text
    assert validate.json()["successful"] is True
    compile_preflight = client.post(
        "/projects/example-project/compile", json=_ref(draft), headers=_ANALYSIS_HEADERS
    )
    assert compile_preflight.status_code == 200, compile_preflight.text
    # 与 path 流一致：离线 fixture 的 endpoint health 可为三态（PASS/WARN/FAIL）
    assert compile_preflight.json()["status"] in {"PASS", "WARN", "FAIL"}
    preflight = client.post(
        "/projects/example-project/preflight", json=_ref(draft), headers=_ANALYSIS_HEADERS
    )
    assert preflight.status_code == 200, preflight.text
    dry_run = client.post(
        "/projects/example-project/dry-run", json=_ref(draft), headers=_ANALYSIS_HEADERS
    )
    assert dry_run.status_code == 200, dry_run.text
    assert dry_run.json()["role_counts"]


def test_draft_revision_immutability_compile_tracks_saved_revision(client: TestClient) -> None:
    """修订不可变：保存新修订后，旧修订引用的编译结果不受新正文影响。"""
    draft = _create_draft(client, "wpb-immutable")
    old = client.post("/protocols/validate", json=_ref(draft), headers=_ANALYSIS_HEADERS)
    assert old.status_code == 200
    old_digest = old.json()["protocol_digest"]
    edited = client.put(
        f"/protocol-drafts/{draft['draft_id']}",
        json={"yaml_text": _VALID_DRAFT_YAML + "\n# edited\n", "expected_revision": 1},
        headers={"Idempotency-Key": f"edit-{uuid.uuid4()}", "If-Match": "1"},
    )
    assert edited.status_code == 200, edited.text
    revalidated = client.post("/protocols/validate", json=_ref(draft), headers=_ANALYSIS_HEADERS)
    assert revalidated.json()["protocol_digest"] == old_digest


def test_draft_source_and_path_are_mutually_exclusive(client: TestClient) -> None:
    draft = _create_draft(client, "wpb-ambiguous")
    response = client.post(
        "/protocols/validate",
        json={"path": "m12_reference_research_v1.yaml", **_ref(draft)},
        headers=_ANALYSIS_HEADERS,
    )
    assert response.status_code == 422
    assert "Ambiguous" in response.text


def test_missing_protocol_source_is_422(client: TestClient) -> None:
    response = client.post("/protocols/validate", json={}, headers=_ANALYSIS_HEADERS)
    assert response.status_code == 422


def test_incomplete_draft_reference_is_422(client: TestClient) -> None:
    response = client.post(
        "/protocols/validate", json={"draft_id": "pdraft_x"}, headers=_ANALYSIS_HEADERS
    )
    assert response.status_code == 422
    assert "both required" in response.text


def test_unknown_draft_revision_is_404(client: TestClient) -> None:
    response = client.post(
        "/protocols/validate",
        json={"draft_id": "pdraft_missing", "draft_revision": 1},
        headers=_ANALYSIS_HEADERS,
    )
    assert response.status_code == 404
    assert "Draft Revision Not Found" in response.text
