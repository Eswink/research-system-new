"""草稿修订 → 运行链集成测试（PLAN-20260908-033 AC-04 服务端面）。

核心不变量：启动使用草稿修订时，服务端加载该不可变修订正文并走与
path 完全相同的 Compile → Preflight → Freeze 链；随后草稿再保存新修订
不能改写已冻结运行的 manifest（冻结摘要来自启动时刻的修订 1）。
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi.testclient import TestClient

# 与既有 run 测试同源的冻结场景（m12 参考协议；run_ready 装配可 PASS）
_VALID_YAML = open("examples/protocols/m12_reference_research_v1.yaml", encoding="utf-8").read()

# 编辑版：追加注释行（schema 校验仍通过；用于证明修订 2 不改写冻结运行）
_EDITED_YAML = _VALID_YAML + "\n# edited after freeze\n"


def _create_draft(client: TestClient, name: str) -> dict[str, Any]:
    response = client.post(
        "/projects/example-project/protocol-drafts",
        json={"name": name, "yaml_text": _VALID_YAML},
        headers={"Idempotency-Key": f"draft-{uuid.uuid4()}"},
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def test_start_run_from_draft_revision_uses_frozen_text(run_ready_client: TestClient) -> None:
    """草稿修订启动 → 冻结 manifest；后续草稿变化不改写冻结运行。"""
    draft = _create_draft(run_ready_client, "freeze ref")
    draft_id = draft["draft_id"]

    started = run_ready_client.post(
        "/projects/example-project/runs",
        json={"draft_id": draft_id, "draft_revision": 1},
        headers={"Idempotency-Key": f"run-{uuid.uuid4()}"},
    )
    assert started.status_code == 200, started.text
    run = cast(dict[str, Any], started.json())
    assert run["manifest_digest"] is not None
    assert run["manifest_digest"].startswith("sha256:")
    frozen_digest = run["manifest_digest"]

    # 草稿保存修订 2（正文变化）→ 冻结运行的 manifest 必须不变
    saved = run_ready_client.put(
        f"/protocol-drafts/{draft_id}",
        json={"yaml_text": _EDITED_YAML, "expected_revision": 1},
        headers={"Idempotency-Key": f"save-{uuid.uuid4()}", "If-Match": "1"},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["revision"] == 2

    fetched = run_ready_client.get(f"/runs/{run['id']}")
    assert fetched.status_code == 200
    after = cast(dict[str, Any], fetched.json())
    assert after["manifest_digest"] == frozen_digest

    # 冻结事件中的 digest 也不变（canonical 事件链不可改写）
    events = run_ready_client.get(f"/runs/{run['id']}/events").json()
    frozen_events = [e for e in events if e["type"] == "manifest.frozen"]
    assert len(frozen_events) == 1
    assert frozen_events[0]["payload"]["digest"] == frozen_digest


def test_start_run_with_missing_draft_revision_404(run_ready_client: TestClient) -> None:
    response = run_ready_client.post(
        "/projects/example-project/runs",
        json={"draft_id": "pdraft_missing", "draft_revision": 9},
        headers={"Idempotency-Key": f"run-{uuid.uuid4()}"},
    )
    assert response.status_code == 404, response.text


def test_start_run_with_partial_draft_reference_422(run_ready_client: TestClient) -> None:
    response = run_ready_client.post(
        "/projects/example-project/runs",
        json={"draft_id": "pdraft_x"},
        headers={"Idempotency-Key": f"run-{uuid.uuid4()}"},
    )
    assert response.status_code == 422, response.text


def test_start_run_with_both_sources_422(run_ready_client: TestClient) -> None:
    draft = _create_draft(run_ready_client, "ambiguous")
    response = run_ready_client.post(
        "/projects/example-project/runs",
        json={
            "protocol_path": "m12_reference_research_v1.yaml",
            "draft_id": draft["draft_id"],
            "draft_revision": 1,
        },
        headers={"Idempotency-Key": f"run-{uuid.uuid4()}"},
    )
    assert response.status_code == 422, response.text
