"""SqliteToolProviderRegistry 单元测试（PLAN-20260915-069 WP-C）。

关注两件事：
1. **schema 指纹四字段的往返**（write-through 后读回逐字段相等）；
2. **旧行兼容**：本表是 JSON-blob-per-row，老记录没有这些键 ⇒ 必须按
   "没观测过"（None/False）解码，而不是抛错或凭空补一个 digest。
"""

from __future__ import annotations

import json

from adapters.sqlite.tool_provider_registry import SqliteToolProviderRegistry
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import EffectClass, EndpointHealth, ProviderType
from packages.domain.tool_registry import ProviderRegistration

_D1 = str(Digest.parse("sha256:" + "1" * 64))
_D2 = str(Digest.parse("sha256:" + "2" * 64))


def _registration(**overrides: object) -> ProviderRegistration:
    base: dict[str, object] = {
        "id": "dataset_gateway",
        "kind": ProviderType.REST,
        "capabilities": ["dataset.read"],
        "effect_class": EffectClass.READ_ONLY,
        "pinned_revision": "sha256:" + "a" * 64,
        "transport": "rest",
        "health_check": True,
    }
    base.update(overrides)
    return ProviderRegistration(**base)  # type: ignore[arg-type]


def _observed(
    registration: ProviderRegistration, digest: str, *, detail: str, now: Timestamp
) -> ProviderRegistration:
    """做一次"观测到某个 digest"的健康复核（本文件关心的是它落库后的往返）。"""
    return registration.record_health(
        EndpointHealth.HEALTHY, detail=detail, now=now, observed_schema_digest=digest
    )


def test_schema_digest_fields_round_trip() -> None:
    store = SqliteToolProviderRegistry(":memory:")
    now = Timestamp.now()
    drifted = _observed(
        _observed(_registration(), _D1, detail="baseline", now=now),
        _D2,
        detail="changed",
        now=now,
    )
    store.save_registration(drifted)

    loaded = store.get_registration("dataset_gateway")
    assert loaded.last_schema_digest == _D2
    assert loaded.schema_baseline_digest == _D1
    assert loaded.schema_drift is True
    assert loaded.schema_drift_since is not None
    assert loaded == drifted


def test_a_row_written_before_the_digest_fields_existed_still_decodes() -> None:
    """旧行（无 digest 键）必须按"没观测过"解码——不能抛错，也不能补一个假值。"""
    store = SqliteToolProviderRegistry(":memory:")
    # 手写"历史形态"的行：这是加字段之前那一版的键集（没有 schema_* 四键）。
    legacy_payload = {
        "id": "dataset_gateway",
        "kind": "REST",
        "capabilities": ["dataset.read"],
        "effect_class": "READ_ONLY",
        "pinned_revision": "sha256:" + "a" * 64,
        "transport": "rest",
        "protocol_version": None,
        "network_domains": [],
        "health_check": True,
        "state": "ACTIVE",
        "registered_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "approved_at": "2026-01-01T00:00:00+00:00",
        "revoked_at": None,
        "revoked_reason": None,
        "last_health": "HEALTHY",
        "health_detail": "legacy",
        "health_checked_at": "2026-01-01T00:00:00+00:00",
    }
    store._conn.execute(
        """
        INSERT INTO tool_provider_registrations
            (provider_id, state, pinned_revision, registration_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "dataset_gateway",
            "ACTIVE",
            legacy_payload["pinned_revision"],
            json.dumps(legacy_payload),
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00",
        ),
    )

    decoded = store.get_registration("dataset_gateway")
    assert decoded.last_schema_digest is None
    assert decoded.schema_baseline_digest is None
    assert decoded.schema_drift is False
    assert decoded.schema_drift_since is None
    assert decoded.last_health == "HEALTHY"  # 其它字段不受影响
    assert decoded.state == "ACTIVE"
    assert decoded.credential_ref is None  # 加字段前的老行 → "没声明过凭据"


def test_list_returns_every_drifted_registration() -> None:
    store = SqliteToolProviderRegistry(":memory:")
    now = Timestamp.now()
    for provider_id, digest in (("a_provider", _D1), ("b_provider", _D2)):
        store.save_registration(
            _observed(
                _observed(_registration(id=provider_id), _D1, detail="baseline", now=now),
                digest,
                detail="changed",
                now=now,
            )
        )

    drifted = {item.id: item.schema_drift for item in store.list_registrations()}
    assert drifted == {"a_provider": False, "b_provider": True}


def test_endpoint_env_round_trips_and_legacy_rows_stay_undeclared() -> None:
    """PLAN-20260915-072：端点来源**声明**入库往返；旧行（无该键）解码为"未声明"。

    注意存的是**变量名**：端点值永远不入库（解析发生在进程边界）。
    """
    store = SqliteToolProviderRegistry(":memory:")
    declared = _registration(endpoint_env="DATASET_GATEWAY_ENDPOINT")
    store.save_registration(declared)
    assert store.get_registration("dataset_gateway") == declared
    assert store.get_registration("dataset_gateway").endpoint_env == "DATASET_GATEWAY_ENDPOINT"

    legacy = _registration(id="legacy_gateway")
    store.save_registration(legacy)
    payload = json.loads(
        str(
            store._conn.execute(  # noqa: SLF001 - 直接改行，模拟"加字段之前写下的行"
                "SELECT registration_json FROM tool_provider_registrations WHERE provider_id = ?",
                ("legacy_gateway",),
            ).fetchone()[0]
        )
    )
    payload.pop("endpoint_env", None)
    store._conn.execute(  # noqa: SLF001 - 同上
        "UPDATE tool_provider_registrations SET registration_json = ? WHERE provider_id = ?",
        (json.dumps(payload), "legacy_gateway"),
    )
    store._conn.commit()  # noqa: SLF001

    assert store.get_registration("legacy_gateway").endpoint_env is None


def test_credential_ref_round_trips_and_legacy_rows_stay_undeclared() -> None:
    """PLAN-20260915-074：凭据**声明**入库往返；旧行（无该键）解码为"未声明"。

    注意存的是**引用名**：凭据值永远不入库（判定走 CredentialResolver.has，
    取值只发生在进程边界）。
    """
    store = SqliteToolProviderRegistry(":memory:")
    declared = _registration(credential_ref="DATASET_GATEWAY_TOKEN")
    store.save_registration(declared)
    assert store.get_registration("dataset_gateway") == declared
    assert store.get_registration("dataset_gateway").credential_ref == "DATASET_GATEWAY_TOKEN"

    # 声明随 spec() 进入目录面（否则注册面写了、探测面看不到——cycle 10 的教训）
    assert store.get_registration("dataset_gateway").spec().credential_ref == (
        "DATASET_GATEWAY_TOKEN"
    )

    legacy = _registration(id="legacy_gateway")
    store.save_registration(legacy)
    payload = json.loads(
        str(
            store._conn.execute(  # noqa: SLF001 - 直接改行，模拟"加字段之前写下的行"
                "SELECT registration_json FROM tool_provider_registrations WHERE provider_id = ?",
                ("legacy_gateway",),
            ).fetchone()[0]
        )
    )
    payload.pop("credential_ref", None)
    store._conn.execute(  # noqa: SLF001 - 同上
        "UPDATE tool_provider_registrations SET registration_json = ? WHERE provider_id = ?",
        (json.dumps(payload), "legacy_gateway"),
    )
    store._conn.commit()  # noqa: SLF001

    assert store.get_registration("legacy_gateway").credential_ref is None
