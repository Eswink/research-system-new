"""M13-R1 测试：合并目录（SQLite 用户配置覆盖 examples）+ toolpack digest 接线。

证明（BLOCKER-B3 修复）：
- 用户经 wizard 创建的 endpoint/model 进入 merged catalog（且 dry-run 可见）；
- examples 中未被覆盖的 endpoint/model 仍存在；
- toolpack 契约 digest 如实接入（ncbi_eutils 有 pin）；
- research_mcp 占位已移除（无法诚实 pin 的 provider 不再假装存在）。
"""

from __future__ import annotations

from typing import Any, cast

from fastapi.testclient import TestClient

from tests.api.conftest import create_endpoint


def _create_model(client: TestClient, endpoint_id: str, model_name: str) -> dict[str, Any]:
    response = client.post(
        "/models",
        json={"endpoint_id": endpoint_id, "model_name": model_name, "enabled": True},
        headers={"Idempotency-Key": f"model-{model_name}"},
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def test_merged_catalog_includes_user_configuration(client: TestClient) -> None:
    """用户 endpoint/model 按 id 覆盖进 merged catalog；examples 保留。"""
    from services.api.catalog_merge import merged_catalog_snapshot

    deps = cast(Any, client.app).state.deps
    endpoint = create_endpoint(client, name="user-relay")
    model = _create_model(client, endpoint["id"], "user-model-v1")

    snapshot = merged_catalog_snapshot(deps)
    assert endpoint["id"] in snapshot.endpoints
    assert snapshot.endpoints[endpoint["id"]].base_url == "https://relay.example.com/api/v1"
    assert model["id"] in snapshot.models
    assert snapshot.models[model["id"]].model_name == "user-model-v1"
    # examples 未覆盖项仍存在
    assert "main" in snapshot.endpoints
    assert "research_alpha" in snapshot.models


def test_user_relay_named_main_overrides_example_endpoint(client: TestClient) -> None:
    """Relay 身份覆盖：用户 endpoint 名称 == example endpoint id 时按名称覆盖。

    这是向导配置进入 preflight/run 链的关键路径（example 协议内模型绑定
    经 `main` 解析到用户 relay）。
    """
    from services.api.catalog_merge import merged_catalog_snapshot

    deps = cast(Any, client.app).state.deps
    endpoint = create_endpoint(client, name="main", base_url="http://localtest.me:9999")

    snapshot = merged_catalog_snapshot(deps)
    assert snapshot.endpoints["main"].base_url == "http://localtest.me:9999"
    assert snapshot.endpoints["main"].credential_ref == f"endpoint:{endpoint['id']}"
    assert snapshot.endpoints[endpoint["id"]].base_url == "http://localtest.me:9999"


def test_tool_pack_digests_wired_from_contracts(client: TestClient) -> None:
    """toolpack 契约 digest 如实接入（BLOCKER-B3 供应链 pin 修复）。"""
    from services.api.catalog import load_catalog_snapshot

    snapshot = load_catalog_snapshot()
    digest = snapshot.tool_pack_digests.get("ncbi_eutils")
    assert digest is not None
    assert digest.startswith("sha256:")
    assert len(digest) == len("sha256:") + 64


def test_research_mcp_placeholder_removed(client: TestClient) -> None:
    """无法诚实 pin 的 research_mcp 占位已移除。"""
    from services.api.catalog import load_catalog_snapshot

    snapshot = load_catalog_snapshot()
    assert "research_mcp" not in snapshot.tool_providers
    assert "ncbi_eutils" in snapshot.tool_providers


def test_dry_run_no_longer_reports_unpinned_or_policy_missing(
    client: TestClient, credentials: Any
) -> None:
    """真实接线后 dry-run 不再恒报 SUPPLY_CHAIN_UNPINNED / POLICY_MISSING。"""
    credentials.register("LLM_MAIN_KEY", "sk-demo-key-0001")
    response = client.post(
        "/projects/example-project/dry-run", json={"path": "console_demo_research_v1.yaml"}
    )
    assert response.status_code == 200, response.text
    report = client.post(
        "/projects/example-project/compile", json={"path": "console_demo_research_v1.yaml"}
    ).json()
    codes = {finding["code"] for finding in report["findings"]}
    assert "SUPPLY_CHAIN_UNPINNED" not in codes
    assert "POLICY_MISSING" not in codes
    assert "POLICY_DENIED" not in codes
    assert "ENDPOINT_UNHEALTHY" not in codes
    assert report["status"] in ("PASS", "WARN")
