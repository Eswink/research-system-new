"""GOAL-010 EC-04：run 终止时落下的运行时指纹事实（四要素 + 缺项点名）。

判据的射程：**这一层**决定「观测 → 事件 payload」的映射与两态结论；读面呈现由
`tests/api/test_run_fingerprint_read_face.py` 判，会话层观测来源由
`tests/adapters/openhands/test_model_observation.py` 判。

三条不许越过的线（与 PLAN-20260921-130 的诚实边界一一对应）：

1. **没有观测 ⇒ 没有事实**（返回 `None`，不发事件）；
2. **缺必填项 ⇒ 不许报 `REPEATABLE_CONFIGURATION`**（AC-2）；
3. **单值槽位不替多值做主**：观测到多个不同 model 名 ⇒ 单值留 `None`（缺项），
   多值本身原样带上（藏起来等于把「观测到不一致」读成「没观测到」）。
"""

from __future__ import annotations

from packages.application.model_relay.observation import RunSessionObservation
from packages.application.run_orchestration.runtime_fingerprint import runtime_fingerprint_payload

#: 端点头 / probe 版本在判据里只是"非空且照原样带出"的字符串（digest 的构造不是本层的事）。
_ENDPOINT = "sha256:endpoint-config"
_OBSERVED = "relay-model-alpha"


def _payload(*observations: RunSessionObservation, state: str = "SUCCEEDED") -> dict[str, object]:
    payload = runtime_fingerprint_payload(
        run_id="run-1", terminal_state=state, observations=observations
    )
    assert payload is not None, "本用例的前提是有观测"
    return payload


def _observation(endpoint: str | None = _ENDPOINT, *names: str) -> RunSessionObservation:
    return RunSessionObservation(
        endpoint_config_digest=endpoint, observed_model_identifiers=tuple(names)
    )


def test_no_observation_means_no_fact() -> None:
    """没有观测 ⇒ `None`：读面因此保持冻结占位，而不是拿到一条空记录。"""
    assert (
        runtime_fingerprint_payload(run_id="run-1", terminal_state="SUCCEEDED", observations=())
        is None
    )


def _missing(payload: dict[str, object]) -> list[str]:
    """payload 里的缺项列表（判据按类型收窄一次，后面直接当字符串列表用）。"""
    names = payload["missing_fields"]
    assert isinstance(names, list), names
    return [name for name in names if isinstance(name, str)]


def test_the_observed_name_becomes_the_returned_model_identifier() -> None:
    """返回 model 名 = **本次 run 的观测值**；端点头与 probe 版本照原样带出。"""
    payload = _payload(_observation(_ENDPOINT, _OBSERVED))
    assert payload["returned_model_identifier"] == _OBSERVED
    assert payload["endpoint_config_digest"] == _ENDPOINT
    assert isinstance(payload["probe_suite_digest"], str) and payload["probe_suite_digest"]
    assert payload["observed_model_identifiers"] == [_OBSERVED]
    assert payload["verdict"] == "REPEATABLE_CONFIGURATION"


def test_one_wire_carries_two_sessions_observing_the_same_name() -> None:
    """同一 model 名被两个会话观测到 ⇒ 仍是**一个**值（不是"多值"）。"""
    payload = _payload(_observation(_ENDPOINT, _OBSERVED), _observation(_ENDPOINT, _OBSERVED))
    assert payload["returned_model_identifier"] == _OBSERVED
    assert payload["observed_model_identifiers"] == [_OBSERVED]
    assert payload["verdict"] == "REPEATABLE_CONFIGURATION"


def test_two_different_observed_names_do_not_collapse_into_one() -> None:
    """观测到多个不同值 ⇒ 单值留 `None`（缺项）、结论降级，**且多值不被藏起来**。"""
    payload = _payload(_observation(_ENDPOINT, _OBSERVED, "relay-model-beta"))
    assert payload["returned_model_identifier"] is None
    assert payload["observed_model_identifiers"] == ["relay-model-alpha", "relay-model-beta"]
    assert "returned_model_identifier" in _missing(payload)
    assert payload["verdict"] == "NOT_VERIFIED"


def test_a_missing_required_fact_downgrades_the_conclusion() -> None:
    """缺必填项（这里：会话没有执行目标 ⇒ 端点头缺）⇒ **不许**报可重复配置。"""
    payload = _payload(_observation(None, _OBSERVED))
    assert payload["endpoint_config_digest"] is None
    assert "endpoint_config_digest" in _missing(payload)
    assert "returned_model_identifier" not in _missing(payload)
    assert payload["verdict"] == "NOT_VERIFIED"


def test_the_event_never_carries_unmeasured_usage_counters() -> None:
    """本层拿不到 usage/制品的真值 ⇒ **不发布**那些记录键（0 不是实测值）。"""
    payload = _payload(_observation(_ENDPOINT, _OBSERVED))
    for key in ("model_tokens", "usage_entries", "artifact_ids", "evidence_ids"):
        assert key not in payload, key
    assert payload["run_id"] == "run-1"
    assert payload["terminal_state"] == "SUCCEEDED"
