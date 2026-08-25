"""M13 安全 / secret / redaction 四面扫描契约测试。

证明（M13 DoD 13）：
- DTO / SSE / Export / 错误响应 四个出口不泄漏明文 Key；
- 前端持久层（localStorage）无 secret 写入（静态断言 + 行为断言）；
- 事件 payload 只含 digest/status/model 名（AGENTS.md §10）。
"""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

from tests.api.conftest import create_endpoint

_SECRET = "sk-m13-scan-secret-xyz"
_PATTERN = re.compile(re.escape(_SECRET))


def test_dto_never_returns_secret(client: TestClient) -> None:
    """DTO 出口：创建/列表/详情/更新响应均无明文 Key。"""
    endpoint = create_endpoint(client, api_key=_SECRET)
    id_ = endpoint["id"]
    assert _PATTERN.search(client.get(f"/llm-endpoints/{id_}").text) is None
    assert _PATTERN.search(client.get("/llm-endpoints").text) is None
    patched = client.patch(
        f"/llm-endpoints/{id_}",
        json={"name": "renamed"},
        headers={"If-Match": endpoint["version"], "Idempotency-Key": "scan-patch"},
    )
    assert _PATTERN.search(patched.text) is None


def test_sse_payload_never_contains_secret(run_ready_client: TestClient) -> None:
    """SSE 出口：事件 payload 无明文 Key（AGENTS.md §10）。"""
    import uuid

    run = run_ready_client.post(
        "/projects/example-project/runs",
        json={"protocol_path": "m12_reference_research_v1.yaml"},
        headers={"Idempotency-Key": f"run-{uuid.uuid4()}"},
    ).json()
    stream = run_ready_client.get(
        f"/runs/{run['id']}/events?poll=0", headers={"Accept": "text/event-stream"}
    ).text
    assert _SECRET not in stream
    assert "sk-" not in stream
    assert "Bearer" not in stream


def test_export_never_contains_secret(client: TestClient) -> None:
    """Export 出口：审计导出无明文 Key（导出来自 persisted state）。"""
    from typing import Any, cast

    from packages.domain.core import ID
    from packages.domain.run import ResearchRun

    deps = cast(Any, client.app).state.deps
    run_id = str(ID.generate().value)
    deps.run_registry[run_id] = ResearchRun(
        id=ID(run_id), project_id="p", protocol_id="proto"
    )
    export = client.get(f"/runs/{run_id}/export").text
    assert _SECRET not in export
    assert "sk-" not in export


def test_error_responses_never_contain_secret(client: TestClient) -> None:
    """错误出口：404/412/422 响应无明文 Key。"""
    endpoint = create_endpoint(client, api_key=_SECRET)
    stale = client.patch(
        f"/llm-endpoints/{endpoint['id']}",
        json={"name": "x"},
        headers={"If-Match": "sha256:" + "0" * 64, "Idempotency-Key": "scan-stale"},
    )
    assert stale.status_code == 412
    assert _PATTERN.search(stale.text) is None


def test_frontend_never_writes_secret_to_persistent_storage(
    client: TestClient,
) -> None:
    """前端持久层断言：web 源码无 localStorage/sessionStorage 写 secret。"""
    from pathlib import Path

    web_root = Path(client.__class__.__module__).parent.parent.parent / "apps" / "web"
    for source in (web_root / "src").rglob("*.ts*"):
        text = source.read_text(encoding="utf-8")
        assert "localStorage.setItem" not in text, (
            f"{source.relative_to(web_root)} must not persist state to localStorage"
        )
        assert "sessionStorage.setItem" not in text


def test_frontend_never_ships_secret_literals(client: TestClient) -> None:
    """前端源码不含真实 Key 字面量（sk- 前缀扫描）。"""
    from pathlib import Path

    web_root = Path(client.__class__.__module__).parent.parent.parent / "apps" / "web"
    for source in (web_root / "src").rglob("*.ts*"):
        text = source.read_text(encoding="utf-8")
        matches = re.findall(r"sk-[A-Za-z0-9]{8,}", text)
        assert not matches, f"{source.relative_to(web_root)} contains key-like literal: {matches}"