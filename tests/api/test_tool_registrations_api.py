"""Tool Provider 注册/治理写面测试（G15 / PLAN-20260915-060，EC-05）。

写面是**被消费**的，不是又一个只能写不能读的表：

    PENDING  → 不进目录（preflight 仍报 TOOL_UNAVAILABLE）
    ACTIVE   → 进目录（compile 的 provider_ids 出现该 id；preflight 不再报
               TOOL_UNAVAILABLE，且因为注册 pin 被合入 tool_pack_digests，
               非 NATIVE provider 也不再报 SUPPLY_CHAIN_UNPINNED）
    REVOKED  → 终态退出目录（回到 TOOL_UNAVAILABLE）

信任级别由状态推导：注册方无法声明 BUILT_IN/VERIFIED；pin 必须是
`sha256:<hex>`（可漂移的 tag/分支名一律 422）。
"""

from __future__ import annotations

from itertools import count
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from adapters.fakes.tool_provider import FakeToolProvider
from services.api.app import create_app

PIN = "sha256:" + "a" * 64
REPIN = "sha256:" + "c" * 64
_SEQ = count(1)

# 只被"用户注册的 provider"覆盖的能力：examples 契约里的三个 provider 都不声明
# dataset.read（见 examples/config/tool_providers.yaml），因此它的可用性完全由
# 注册面状态决定——这就是本文件的消费证明。
_DRAFT_YAML = """id: dataset_provider_registration_v1_0_0
version: 0.4.0
phases:
  - id: ingest
    name: Dataset Ingest
    strategy: single_agent
    required_roles:
      - {role: experiment_engineer, min_instances: 1, max_instances: 1}
    required_capabilities:
      - dataset.read
    outputs: [source_set]
    timeout_seconds: 120
"""


def _body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "id": "dataset_gateway",
        "kind": "REST",
        "capabilities": ["dataset.read"],
        "pinned_revision": PIN,
        "transport": "rest",
        "health_check": True,
    }
    body.update(overrides)
    return body


def _headers(seed: str) -> dict[str, str]:
    """幂等键带自增后缀：同一路径的多次调用不能命中 replay（否则测的是缓存）。"""
    return {"Idempotency-Key": f"plan060-{seed}-{next(_SEQ)}"}


def _register(client: TestClient, **overrides: Any) -> dict[str, Any]:
    response = client.post(
        "/tool-provider-registrations",
        json=_body(**overrides),
        headers=_headers(f"reg-{overrides.get('id', 'dataset_gateway')}"),
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def _catalog_ids(client: TestClient) -> set[str]:
    payload = client.get("/tool-providers").json()
    return {item["id"] for item in payload["providers"]}


def _draft_ref(client: TestClient, name: str) -> dict[str, Any]:
    created = client.post(
        "/projects/example-project/protocol-drafts",
        json={"name": name, "yaml_text": _DRAFT_YAML},
        headers=_headers(f"draft-{name}"),
    )
    assert created.status_code == 201, created.text
    draft = cast(dict[str, Any], created.json())
    return {"draft_id": draft["draft_id"], "draft_revision": draft["revision"]}


def _preflight_codes(client: TestClient, ref: dict[str, Any], state: str) -> set[str]:
    response = client.post(
        "/projects/example-project/preflight",
        json=ref,
        headers=_headers(f"preflight-{state}"),
    )
    assert response.status_code == 200, response.text
    return {finding["code"] for finding in response.json()["findings"]}


def test_register_requires_pinned_digest(client: TestClient) -> None:
    """pin 必须是内容寻址 digest：可漂移字面量（tag/分支名）拒绝为 422。"""
    response = client.post(
        "/tool-provider-registrations",
        json=_body(pinned_revision="v1.2.3"),
        headers=_headers("drifting-pin"),
    )
    assert response.status_code == 422, response.text
    assert "digest" in response.json()["detail"]

    empty = client.post(
        "/tool-provider-registrations",
        json=_body(id="no_caps", capabilities=[]),
        headers=_headers("no-caps"),
    )
    assert empty.status_code == 422


def test_register_rejects_reserved_and_duplicate_ids(client: TestClient) -> None:
    """内置目录占用的 id 不影子覆盖；重复登记 409（不改写既有行）。"""
    reserved = client.post(
        "/tool-provider-registrations",
        json=_body(id="openhands_workspace", kind="NATIVE"),
        headers=_headers("reserved"),
    )
    assert reserved.status_code == 409, reserved.text
    assert "built-in catalog" in reserved.json()["detail"]

    _register(client)
    duplicate = client.post(
        "/tool-provider-registrations",
        json=_body(pinned_revision=REPIN),
        headers=_headers("duplicate"),
    )
    assert duplicate.status_code == 409, duplicate.text
    stored = client.get("/tool-provider-registrations").json()["registrations"]
    assert [item["pinned_revision"] for item in stored] == [PIN]


def test_pending_is_invisible_until_approved(client: TestClient) -> None:
    """PENDING 只表示已登记：目录里没有它，批approve 之后才以 USER_APPROVED 出现。"""
    registered = _register(client)
    assert registered["state"] == "PENDING"
    assert registered["trust_level"] == "UNTRUSTED"
    assert registered["catalog_active"] is False
    assert "dataset_gateway" not in _catalog_ids(client)

    approved = client.post(
        "/tool-provider-registrations/dataset_gateway/approve", headers=_headers("approve")
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["state"] == "ACTIVE"
    assert approved.json()["trust_level"] == "USER_APPROVED"
    assert approved.json()["catalog_active"] is True

    catalog = {item["id"]: item for item in client.get("/tool-providers").json()["providers"]}
    assert catalog["dataset_gateway"]["trust_level"] == "USER_APPROVED"
    assert catalog["dataset_gateway"]["capabilities"] == ["dataset.read"]


def test_double_approve_conflicts(client: TestClient) -> None:
    _register(client)
    first = client.post(
        "/tool-provider-registrations/dataset_gateway/approve", headers=_headers("approve-1")
    )
    assert first.status_code == 200
    second = client.post(
        "/tool-provider-registrations/dataset_gateway/approve", headers=_headers("approve-2")
    )
    assert second.status_code == 409, second.text
    assert "PENDING" in second.json()["detail"]


def test_revoke_is_terminal_and_removes_from_catalog(client: TestClient) -> None:
    _register(client)
    client.post("/tool-provider-registrations/dataset_gateway/approve", headers=_headers("appr"))
    assert "dataset_gateway" in _catalog_ids(client)

    revoked = client.post(
        "/tool-provider-registrations/dataset_gateway/revoke",
        json={"reason": "上游 MCP server 被替换，未通过复核"},
        headers=_headers("revoke"),
    )
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["state"] == "REVOKED"
    assert revoked.json()["trust_level"] == "REVOKED"
    assert revoked.json()["catalog_active"] is False
    assert "dataset_gateway" not in _catalog_ids(client)

    again = client.post(
        "/tool-provider-registrations/dataset_gateway/revoke",
        json={"reason": "再来一次"},
        headers=_headers("revoke-again"),
    )
    assert again.status_code == 409, again.text
    patched = client.patch(
        "/tool-provider-registrations/dataset_gateway",
        json={"capabilities": ["dataset.read", "statistics.execute"]},
        headers=_headers("patch-revoked"),
    )
    assert patched.status_code == 409, patched.text


def test_update_repins_and_rejects_nonchanging_patch(client: TestClient) -> None:
    _register(client)
    updated = client.patch(
        "/tool-provider-registrations/dataset_gateway",
        json={"pinned_revision": REPIN, "capabilities": ["dataset.read", "statistics.execute"]},
        headers=_headers("repin"),
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["pinned_revision"] == REPIN
    assert updated.json()["capabilities"] == ["dataset.read", "statistics.execute"]

    empty = client.patch(
        "/tool-provider-registrations/dataset_gateway",
        json={},
        headers=_headers("empty-patch"),
    )
    assert empty.status_code == 422
    missing = client.patch(
        "/tool-provider-registrations/absent_provider",
        json={"capabilities": ["dataset.read"]},
        headers=_headers("patch-missing"),
    )
    assert missing.status_code == 404


def test_unknown_kind_and_effect_class_are_422(client: TestClient) -> None:
    bad_kind = client.post(
        "/tool-provider-registrations",
        json=_body(kind="SORCERY"),
        headers=_headers("bad-kind"),
    )
    assert bad_kind.status_code == 422
    bad_effect = client.post(
        "/tool-provider-registrations",
        json=_body(id="odd_effect", effect_class="CATACLYSM"),
        headers=_headers("bad-effect"),
    )
    assert bad_effect.status_code == 422


def test_preflight_consumes_approved_registration(client: TestClient) -> None:
    """最强消费证明：同一份协议在 pending/approved/revoked 下的 preflight 结论不同。"""
    ref = _draft_ref(client, "provider-registration-pending")
    assert "TOOL_UNAVAILABLE" in _preflight_codes(client, ref, "unregistered")

    _register(client)
    assert "TOOL_UNAVAILABLE" in _preflight_codes(client, ref, "pending")

    client.post("/tool-provider-registrations/dataset_gateway/approve", headers=_headers("appr-2"))
    approved = _preflight_codes(client, ref, "approved")
    assert "TOOL_UNAVAILABLE" not in approved
    # 注册的 pin 就是 preflight 看到的 pin；健康不可证明只是警示（不阻断）。
    assert "SUPPLY_CHAIN_UNPINNED" not in approved
    assert "TOOL_HEALTH_UNPROVEN" in approved

    client.post(
        "/tool-provider-registrations/dataset_gateway/revoke",
        json={"reason": "复核不通过"},
        headers=_headers("revoke-2"),
    )
    assert "TOOL_UNAVAILABLE" in _preflight_codes(client, ref, "revoked")


def test_health_check_writes_fact_visible_to_read_face() -> None:
    """健康复核写下的必须是读面看到的同一事实（一条探测路径，不做两套真相）。"""
    from tests.api.conftest import make_base_deps

    deps = make_base_deps()
    probe = FakeToolProvider()
    deps.tool_providers = {"dataset_gateway": probe}
    with TestClient(create_app(deps)) as client:
        _register(client)
        client.post("/tool-provider-registrations/dataset_gateway/approve", headers=_headers("a"))

        healthy = client.post(
            "/tool-provider-registrations/dataset_gateway/health-check",
            headers=_headers("health-ok"),
        )
        assert healthy.status_code == 200, healthy.text
        assert healthy.json()["last_health"] == "HEALTHY"
        catalog = {item["id"]: item for item in client.get("/tool-providers").json()["providers"]}
        assert catalog["dataset_gateway"]["health"] == "HEALTHY"

        probe.fail_health("dataset_gateway")
        rechecked = client.post(
            "/tool-provider-registrations/dataset_gateway/health-check",
            headers=_headers("health-fail"),
        )
        assert rechecked.json()["last_health"] == "OPEN_CIRCUIT"
        catalog = {item["id"]: item for item in client.get("/tool-providers").json()["providers"]}
        assert catalog["dataset_gateway"]["health"] == "OPEN_CIRCUIT"


def test_health_check_without_instance_is_unknown_with_reason(client: TestClient) -> None:
    """没有任何可探测实例时诚实 UNKNOWN + 原因，不伪装健康。"""
    _register(client)
    response = client.post(
        "/tool-provider-registrations/dataset_gateway/health-check", headers=_headers("hc")
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["last_health"] == "UNKNOWN"
    assert body["health_detail"]


def test_native_registration_probes_structurally_healthy(client: TestClient) -> None:
    _register(
        client,
        id="local_notes_tool",
        kind="NATIVE",
        transport=None,
        capabilities=["note.write"],
    )
    response = client.post(
        "/tool-provider-registrations/local_notes_tool/health-check", headers=_headers("native")
    )
    assert response.status_code == 200, response.text
    assert response.json()["last_health"] == "HEALTHY"


def test_registry_absence_is_honest_503_and_read_reason() -> None:
    """未装配注册表：写面 503，读面 200 + management_available=false + 原因。"""
    from tests.api.conftest import make_base_deps

    deps = make_base_deps()
    deps.tool_provider_registry = None
    with TestClient(create_app(deps)) as client:
        listed = client.get("/tool-provider-registrations")
        assert listed.status_code == 200
        assert listed.json()["management_available"] is False
        assert listed.json()["management_reason"]
        assert listed.json()["registrations"] == []

        written = client.post(
            "/tool-provider-registrations", json=_body(), headers=_headers("no-store")
        )
        assert written.status_code == 503, written.text
        catalog = client.get("/tool-providers").json()
        assert catalog["management_available"] is False
        assert catalog["management_reason"]


def test_mcp_registration_requires_transport(client: TestClient) -> None:
    response = client.post(
        "/tool-provider-registrations",
        json=_body(id="mcp_reader", kind="MCP", transport=None),
        headers=_headers("mcp-no-transport"),
    )
    assert response.status_code == 422, response.text


@pytest.mark.parametrize("kind", ["NATIVE", "REST", "MCP", "CLI", "REMOTE_WORKER"])
def test_all_provider_kinds_are_registrable(client: TestClient, kind: str) -> None:
    provider_id = f"kind_{kind.lower()}"
    registered = _register(client, id=provider_id, kind=kind, transport="rest")
    assert registered["kind"] == kind
    assert registered["state"] == "PENDING"
