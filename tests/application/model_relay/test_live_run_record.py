"""live run 记录的诚实规则（GOAL-008 EC-04）。

四条：skip 不是 PASS、缺必填指纹项降级、provider 项缺失只登记、结论不可越级。
"""

from __future__ import annotations

import pytest

from packages.application.model_relay.live_run_record import (
    LiveRunRecord,
    build_live_run_record,
    not_verified_live_run_record,
)
from packages.domain.enums import ModelReproducibilityVerdict

_ENDPOINT_DIGEST = "sha256:" + "a" * 64
_SUITE_DIGEST = "sha256:" + "b" * 64


def _verified(**overrides: object) -> LiveRunRecord:
    facts: dict[str, object] = {
        "run_id": "run-live-ec04",
        "terminal_state": "SUCCEEDED",
        "endpoint_config_digest": _ENDPOINT_DIGEST,
        "returned_model_identifier": "agnes-2.5-flash",
        "probe_suite_digest": _SUITE_DIGEST,
        "system_fingerprint": "fp-live-1",
        "safe_response_metadata": (("x-request-id", "req-live-1"),),
        "model_tokens": 128,
        "usage_entries": 1,
        "artifact_ids": ("artifact-live-1",),
        "evidence_ids": ("evidence-live-1",),
    }
    facts.update(overrides)
    return build_live_run_record(**facts)  # type: ignore[arg-type]


class TestSkipIsNotAPass:
    """无凭据时的记录：说清楚「没跑」，且**不**出现在「通过」的位置。"""

    def test_skip_record_is_not_verified_and_names_the_credential_ref(self) -> None:
        record = not_verified_live_run_record(
            run_id="run-live-ec04",
            reason="live run skipped: credential not resolvable",
            credential_ref="LLM_MAIN_KEY",
        )
        assert record.is_verified is False
        assert record.verdict is ModelReproducibilityVerdict.NOT_VERIFIED
        assert "LLM_MAIN_KEY" in (record.reason or "")
        assert record.reached_terminal_state is False

    def test_skip_record_lists_every_fingerprint_field_as_missing(self) -> None:
        """没跑就没有指纹：全部登记为缺失，**留白不算干净**。"""
        record = not_verified_live_run_record(run_id="run-x", reason="skipped: no credential")
        assert "endpoint_config_digest" in record.missing_fields
        assert "probe_suite_digest" in record.missing_fields
        assert record.endpoint_config_digest is None

    def test_skip_record_must_name_a_reason(self) -> None:
        with pytest.raises(ValueError, match="why the run did not happen"):
            not_verified_live_run_record(run_id="run-x", reason="")

    def test_not_verified_record_cannot_be_constructed_without_a_reason(self) -> None:
        with pytest.raises(ValueError, match="skip is not a pass"):
            LiveRunRecord(
                run_id="run-x",
                terminal_state="DRAFT",
                verdict=ModelReproducibilityVerdict.NOT_VERIFIED,
            )


class TestFingerprintHonesty:
    """必填项缺 ⇒ 降级；provider 项缺 ⇒ 登记但不降级。"""

    @pytest.mark.parametrize(
        "field",
        ["endpoint_config_digest", "returned_model_identifier", "probe_suite_digest"],
    )
    def test_missing_required_field_degrades_to_not_verified(self, field: str) -> None:
        record = _verified(**{field: None})
        assert record.is_verified is False
        assert record.verdict is ModelReproducibilityVerdict.NOT_VERIFIED
        assert field in record.missing_fields
        assert field in (record.reason or ""), "降级原因必须点名缺失的字段"

    def test_non_terminal_run_is_not_verified(self) -> None:
        record = _verified(terminal_state="RUNNING")
        assert record.verdict is ModelReproducibilityVerdict.NOT_VERIFIED
        assert "not terminal" in (record.reason or "")

    @pytest.mark.parametrize("field", ["system_fingerprint", "safe_response_metadata"])
    def test_missing_provider_field_is_recorded_without_degrading(self, field: str) -> None:
        """provider 是否给出不归我们管：如实登记缺口，结论仍是「可重复配置」。"""
        record = _verified(**{field: None if field == "system_fingerprint" else ()})
        assert record.verdict is ModelReproducibilityVerdict.REPEATABLE_CONFIGURATION
        assert record.is_verified is True
        assert field in record.missing_fields


class TestVerifiedRecord:
    def test_verified_record_carries_the_facts(self) -> None:
        record = _verified()
        assert record.verdict is ModelReproducibilityVerdict.REPEATABLE_CONFIGURATION
        assert record.reached_terminal_state is True
        assert record.missing_fields == ()
        payload = record.to_payload()
        assert payload["verdict"] == "REPEATABLE_CONFIGURATION"
        assert payload["model_tokens"] == 128
        assert payload["artifact_ids"] == ["artifact-live-1"]
        assert payload["safe_response_metadata"] == {"x-request-id": "req-live-1"}

    def test_payload_surfaces_the_gaps_to_a_reader(self) -> None:
        payload = _verified(system_fingerprint=None).to_payload()
        assert payload["missing_fields"] == ["system_fingerprint"]
        assert payload["system_fingerprint"] is None

    def test_negative_usage_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be negative"):
            _verified(model_tokens=-1)
