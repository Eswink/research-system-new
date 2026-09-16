"""Tool provider 健康复核的 schema 指纹与漂移（PLAN-20260915-069 / EC-02 剩余子句）。

从 `test_tool_registrations_api.py` 拆出（该文件触及 450 行硬上限）：本文件只放
"复核记下提供方声明的 schema 指纹、并与基线比对漂移"这一族，注册/批准/吊销的生命周期
用例留在原文件。

三条口径（都在用例里钉住）：

1. 漂移是**状态**（当前观测 vs 基线），不是"这次 vs 上次"——否则 A→B→B 会让告警自己消失；
2. **未观测到 digest 不得清除漂移**（未知 ≠ 无变化）；
3. `approve` 是唯一的"我看见了并接受"动作 ⇒ 重设基线、清除漂移。
"""

from __future__ import annotations

from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.core import Digest
from packages.domain.enums import EndpointHealth
from packages.domain.tools import ToolHealthReport, ToolProviderSpec
from services.api.app import create_app
from tests.api.test_tool_registrations_api import _headers, _register

_D1 = Digest.parse("sha256:" + "1" * 64)
_D2 = Digest.parse("sha256:" + "2" * 64)


class _ScriptedProvider:
    """按剧本返回 digest 的最小探测替身。

    `FakeToolProvider` 的 digest 由它自己的目录推导（要改目录才能改 digest），
    而漂移口径需要精确编排"这次观测到 A / 这次观测到 B / 这次**没观测到**"，
    所以这里用一个可直接写剧本的替身；健康三态固定 HEALTHY，让焦点留在 digest 上。
    """

    def __init__(self, script: list[Digest | None]) -> None:
        self._script = list(script)
        self.calls = 0

    def check_health(self, provider: ToolProviderSpec) -> ToolHealthReport:
        digest = self._script[min(self.calls, len(self._script) - 1)]
        self.calls += 1
        return ToolHealthReport(
            provider_id=provider.id,
            status=EndpointHealth.HEALTHY,
            observed_schema_digest=digest,
            detail="scripted probe",
        )


def _probe_client(script: list[Digest | None]) -> TestClient:
    from tests.api.conftest import make_base_deps

    deps = make_base_deps()
    deps.tool_providers = {"dataset_gateway": _ScriptedProvider(script)}
    return TestClient(create_app(deps))


def _health(client: TestClient, seed: str) -> dict[str, Any]:
    response = client.post(
        "/tool-provider-registrations/dataset_gateway/health-check",
        headers=_headers(seed),
    )
    assert response.status_code == 200, response.text
    return cast(dict[str, Any], response.json())


def _approved(client: TestClient) -> None:
    _register(client)
    approved = client.post(
        "/tool-provider-registrations/dataset_gateway/approve", headers=_headers("approve")
    )
    assert approved.status_code == 200, approved.text


def test_health_check_records_the_schema_digest_and_flags_drift() -> None:
    """漂移判据是**当前观测 vs 基线**，不是"这次 vs 上次"。

    若是后者，A→B 报漂移、B→B 立刻改口"没漂移"——告警会在下一次复核后自己消失，
    而提供方仍然不是当初那个。本用例第三次复核观测到的仍是 B，漂移必须仍为真。
    """
    with _probe_client([_D1, _D2, _D2]) as client:
        _approved(client)

        first = _health(client, "health-baseline")
        assert first["schema_baseline_digest"] == str(_D1)
        assert first["last_schema_digest"] == str(_D1)
        assert first["schema_drift"] is False
        assert first["schema_drift_since"] is None

        changed = _health(client, "health-drift")
        assert changed["last_schema_digest"] == str(_D2)
        assert changed["schema_baseline_digest"] == str(_D1)  # 基线不随观测移动
        assert changed["schema_drift"] is True
        assert changed["schema_drift_since"] is not None

        again = _health(client, "health-still-drifted")
        assert again["schema_drift"] is True
        assert again["schema_drift_since"] == changed["schema_drift_since"]

        listed = {
            item["id"]: item
            for item in client.get("/tool-provider-registrations").json()["registrations"]
        }
        assert listed["dataset_gateway"]["last_schema_digest"] == str(_D2)
        assert listed["dataset_gateway"]["schema_drift"] is True


def test_drift_clears_when_the_schema_returns_to_the_baseline() -> None:
    """回到基线 ⇒ 漂移清除（状态语义：判据是"现在还是不是当初那个"）。"""
    with _probe_client([_D1, _D2, _D1]) as client:
        _approved(client)
        _health(client, "health-baseline")
        drifted = _health(client, "health-drift")
        assert drifted["schema_drift"] is True

        restored = _health(client, "health-restored")
        assert restored["last_schema_digest"] == str(_D1)
        assert restored["schema_drift"] is False
        assert restored["schema_drift_since"] is None


def test_observation_without_a_digest_neither_sets_nor_clears_drift() -> None:
    """**未知 ≠ 无漂移**：这次探测没拿到 digest 时，基线与漂移标志都不许动。

    把"没观测到"读成"没变化"会抹掉已经发现的漂移——这是本口径里最危险的一步。
    """
    with _probe_client([_D1, _D2, None]) as client:
        _approved(client)
        _health(client, "health-baseline")
        drifted = _health(client, "health-drift")
        assert drifted["schema_drift"] is True

        observed = _health(client, "health-no-digest")
        assert observed["last_schema_digest"] == str(_D2)  # 上一次观测值保留
        assert observed["schema_baseline_digest"] == str(_D1)
        assert observed["schema_drift"] is True
        assert observed["schema_drift_since"] == drifted["schema_drift_since"]
        # 但这次复核本身照常留痕（没观测到 digest ≠ 没做复核）
        assert observed["last_health"] == "HEALTHY"
        assert observed["health_checked_at"] is not None


def test_approve_accepts_the_current_schema_as_the_new_baseline() -> None:
    """批准是唯一的"我看见了并接受"动作 ⇒ 漂移在这里解除、基线换成当前形态。"""
    with _probe_client([_D1, _D2]) as client:
        _register(client)
        _health(client, "health-before-approve-baseline")
        drifted = _health(client, "health-before-approve-drift")
        assert drifted["state"] == "PENDING"
        assert drifted["schema_drift"] is True

        approved = client.post(
            "/tool-provider-registrations/dataset_gateway/approve", headers=_headers("approve")
        )
        assert approved.status_code == 200, approved.text
        payload = approved.json()
        assert payload["state"] == "ACTIVE"
        assert payload["schema_drift"] is False
        assert payload["schema_drift_since"] is None
        assert payload["schema_baseline_digest"] == str(_D2)
        assert payload["last_schema_digest"] == str(_D2)


def test_registration_without_a_digest_capable_kind_reports_null_honestly() -> None:
    """没有 schema 概念的 kind 诚实为 null（不是空串、不是假值，也不是"无漂移"）。"""
    with _probe_client([_D1]) as client:
        _register(client, id="native_tools", kind="NATIVE", transport=None)
        response = client.post(
            "/tool-provider-registrations/native_tools/health-check",
            headers=_headers("health-native"),
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["last_health"] == "HEALTHY"
        assert payload["last_schema_digest"] is None
        assert payload["schema_baseline_digest"] is None
        assert payload["schema_drift"] is False
