"""ToolPack 供应链写面测试（GOAL-003 cycle 2 / EC-02）。

写面是**被消费**的，不是又一个只能写不能读的表：

    install（内容与 pin 自洽）  → state=INSTALLED，digest 合入 catalog.tool_pack_digests
    扩张更新（提交）            → PENDING：**生效版本仍是旧 digest**（未批准不生效）
    approve-update              → 此刻才替换生效 digest
    revoke                      → 终态：digest 退出目录、待批准更新清空

诚实边界（本文件同样要证伪）：内容与 digest 不符 → 422（控制面自己重算，不采信字面量）；
capability 不在平台词表 → 422 并列出未知项；平台自带 pack id → 409（不影子覆盖）；
未知 pack → 404；REVOKED 再处置 → 409；manifest 形状非法 → 422。
"""

from __future__ import annotations

from dataclasses import replace
from itertools import count
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.tools import (
    manifest_document,
    manifest_from_document,
    toolpack_content_digest,
)
from services.api.catalog_merge import merged_catalog_snapshot
from services.api.deps import get_deps

_SEQ = count(1)


def _headers(seed: str) -> dict[str, str]:
    """幂等键带自增后缀：同一路径的多次调用不能命中 replay（否则测的是缓存）。"""
    return {"Idempotency-Key": f"plan064-{seed}-{next(_SEQ)}"}


def manifest_doc(**overrides: Any) -> dict[str, Any]:
    """构造合法 manifest 文档：digest 由域重算（与 API 收到的一致才可能 201）。"""
    document: dict[str, Any] = {
        "id": "lit_pack_v1",
        "version": "1.0.0",
        "source": "fixture://lit-pack",
        "resolved_revision": "rev-1",
        "license": "MIT",
        "tools": [
            {
                "id": "literature_search",
                "name": "literature_search",
                "effect_class": "NETWORK",
                "provider_kind": "REST",
                "capabilities": ["literature.search"],
                "description": "",
            }
        ],
        "skills": [],
        "requested_capabilities": ["literature.search"],
        "network_domains": ["eutils.ncbi.nlm.nih.gov"],
        "credentials": [],
        "signature": None,
        "digest": "sha256:" + "0" * 64,
    }
    document.update(overrides)
    placeholder = manifest_from_document(document)
    return manifest_document(replace(placeholder, digest=toolpack_content_digest(placeholder)))


def _install(client: TestClient, document: dict[str, Any]) -> Any:
    return client.post(
        "/tool-packs/install", json={"manifest": document}, headers=_headers("install")
    )


def _packs(client: TestClient) -> list[dict[str, Any]]:
    payload = client.get("/tool-packs").json()
    return cast("list[dict[str, Any]]", payload["packs"])


def _digests(client: TestClient) -> dict[str, str]:
    """preflight/compile 消费的同一读面（合并目录快照）。"""
    return dict(merged_catalog_snapshot(get_deps(_request(client))).tool_pack_digests)


def _request(client: TestClient) -> Any:
    from starlette.requests import Request

    scope = {"type": "http", "app": client.app, "headers": [], "method": "GET", "path": "/"}
    return Request(scope)


def test_install_binds_content_digest(client: TestClient) -> None:
    """pin 由控制面重算：内容与 digest 不符 → 422；一致 → 201 且 digest 原样回显。"""
    document = manifest_doc()
    tampered = dict(document, resolved_revision="rev-2")
    rejected = _install(client, tampered)
    assert rejected.status_code == 422, rejected.text
    assert "digest mismatch" in rejected.json()["detail"]

    created = _install(client, document)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "installed"
    assert body["pack"]["digest"] == document["digest"]
    assert body["pack"]["catalog_digest_active"] is True


def test_install_rejects_unknown_capability(client: TestClient) -> None:
    """capability 取值域：不在平台词表的名称 → 422 且点名（RECHECK-060 W-2 的书写面修法）。"""
    document = manifest_doc(requested_capabilities=["made.up.capability"])
    response = _install(client, document)
    assert response.status_code == 422, response.text
    assert "made.up.capability" in response.json()["detail"]


def test_install_rejects_builtin_pack_id(client: TestClient) -> None:
    """平台自带 pack（examples/contracts/toolpack_*.yaml）不被影子覆盖。"""
    document = manifest_doc(id="ncbi_eutils_v1")
    response = _install(client, document)
    assert response.status_code == 409, response.text
    assert "reserved" in response.json()["detail"]


def test_expanding_update_is_pending_until_approved(client: TestClient) -> None:
    """扩张不生效：待批准期间目录里仍是旧 digest，approve-update 后才替换。"""
    v1 = manifest_doc(id="expanding_pack_v1")
    assert _install(client, v1).status_code == 201
    v2 = manifest_doc(id="expanding_pack_v1", requested_capabilities=["literature.read"])
    pending = _install(client, v2)
    assert pending.status_code == 201, pending.text
    body = pending.json()
    assert body["status"] == "pending_approval"
    assert body["pack"]["digest"] == v1["digest"]  # 生效版本未变
    assert body["pack"]["pending"]["digest"] == v2["digest"]
    assert body["pack"]["pending"]["diff"]["added_capabilities"] == ["literature.read"]

    approved = client.post(
        "/tool-packs/expanding_pack_v1/approve-update", headers=_headers("approve")
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["pack"]["digest"] == v2["digest"]
    assert approved.json()["pack"]["pending"] is None


def test_approve_update_without_pending_is_conflict(client: TestClient) -> None:
    assert _install(client, manifest_doc()).status_code == 201
    response = client.post("/tool-packs/lit_pack_v1/approve-update", headers=_headers("no-pending"))
    assert response.status_code == 409, response.text


def test_unknown_pack_is_not_found(client: TestClient) -> None:
    approve = client.post("/tool-packs/ghost/approve-update", headers=_headers("ghost-approve"))
    assert approve.status_code == 404
    revoke = client.post(
        "/tool-packs/ghost/revoke", json={"reason": "n/a"}, headers=_headers("ghost-revoke")
    )
    assert revoke.status_code == 404


def test_revoke_is_terminal_and_clears_pending(client: TestClient) -> None:
    v1 = manifest_doc(id="revoked_pack_v1")
    assert _install(client, v1).status_code == 201
    v2 = manifest_doc(id="revoked_pack_v1", requested_capabilities=["literature.read"])
    assert _install(client, v2).json()["status"] == "pending_approval"

    revoked = client.post(
        "/tool-packs/revoked_pack_v1/revoke",
        json={"reason": "license violation"},
        headers=_headers("revoke"),
    )
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["pack"]["state"] == "REVOKED"
    assert revoked.json()["pack"]["pending"] is None

    again = client.post(
        "/tool-packs/revoked_pack_v1/revoke", json={"reason": "again"}, headers=_headers("again")
    )
    assert again.status_code == 409
    reinstall = _install(client, v1)
    assert reinstall.status_code == 409, reinstall.text


def test_same_manifest_is_unchanged_not_an_update(client: TestClient) -> None:
    document = manifest_doc(id="same_pack_v1")
    assert _install(client, document).json()["status"] == "installed"
    again = _install(client, document)
    assert again.status_code == 201, again.text
    assert again.json()["status"] == "unchanged"


def test_installed_digest_is_consumed_by_catalog(client: TestClient) -> None:
    """消费证明：INSTALLED 的 pack 把 digest 写进 preflight/compile 读的同一张表。

    用 `ncbi_eutils_v2`（strip 版本后缀 → provider `ncbi_eutils`）覆盖 examples 基线 pin，
    revoke 后回落到基线 digest——写面的三种状态在**读面**上各不相同。
    """
    document = manifest_doc(id="ncbi_eutils_v2", requested_capabilities=["literature.read"])
    baseline = _digests(client)["ncbi_eutils"]
    assert _install(client, document).status_code == 201
    assert _digests(client)["ncbi_eutils"] == document["digest"]

    v2 = manifest_doc(
        id="ncbi_eutils_v2",
        requested_capabilities=["literature.read", "citation.inspect"],
    )
    assert _install(client, v2).json()["status"] == "pending_approval"
    assert _digests(client)["ncbi_eutils"] == document["digest"]  # 未批准 → 不生效

    client.post(
        "/tool-packs/ncbi_eutils_v2/revoke",
        json={"reason": "superseded"},
        headers=_headers("revoke-ncbi"),
    )
    assert _digests(client)["ncbi_eutils"] == baseline
