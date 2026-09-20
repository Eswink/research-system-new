"""EC-04 的离线判据：门控、零出站、skip ≠ PASS（GOAL-008 / PLAN-20260920-118）。

这些判据**不开网络、不需要凭据**，是默认 CI 能跑的那一半。live 那一半在
`tests/e2e/test_ec04_live_first_run.py`（`requires_live_llm`，无凭据如实 skip）。
"""

from __future__ import annotations

import socket
from dataclasses import replace
from unittest import mock

import pytest

from adapters.relay.credential_resolver import EnvCredentialResolver
from packages.application.model_relay.live_run_gate import (
    evaluate_live_run_gate,
    skip_record_for_gate,
)
from packages.domain.enums import ModelReproducibilityVerdict
from services.api.runtime_support import FAKE_RUNTIME, OPENHANDS_RUNTIME
from tests.contracts.fixtures import endpoint

_CREDENTIAL_REF = "llm_main_key"
_RUN_ID = "run-ec04-offline"


def _resolver(**values: str) -> EnvCredentialResolver:
    return EnvCredentialResolver(environment=dict(values))


def _gate(*, runtime: str, resolver: EnvCredentialResolver) -> object:
    return evaluate_live_run_gate(
        credentials=resolver,
        endpoint=replace(endpoint(), credential_ref=_CREDENTIAL_REF),
        agent_runtime=runtime,
        live_agent_runtime=OPENHANDS_RUNTIME,
    )


class TestGateIsClosedByDefault:
    """默认门是关的：默认 runtime 是 Fake，默认无凭据。"""

    def test_unset_runtime_closes_the_gate_even_with_a_credential(self) -> None:
        gate = _gate(runtime="", resolver=_resolver(**{_CREDENTIAL_REF: "present"}))
        assert gate.open is False  # type: ignore[attr-defined]
        assert "not configured" in gate.reason  # type: ignore[attr-defined]

    def test_fake_runtime_closes_the_gate(self) -> None:
        """Fake 跑出来的不是 live run：显式配 Fake 也必须关门。"""
        gate = _gate(runtime=FAKE_RUNTIME, resolver=_resolver(**{_CREDENTIAL_REF: "present"}))
        assert gate.open is False  # type: ignore[attr-defined]
        assert FAKE_RUNTIME in gate.reason  # type: ignore[attr-defined]

    def test_missing_credential_closes_the_gate_and_names_the_ref(self) -> None:
        gate = _gate(runtime=OPENHANDS_RUNTIME, resolver=_resolver())
        assert gate.open is False  # type: ignore[attr-defined]
        assert _CREDENTIAL_REF in gate.reason  # type: ignore[attr-defined]
        assert gate.credential_ref == _CREDENTIAL_REF  # type: ignore[attr-defined]

    def test_empty_credential_value_closes_the_gate(self) -> None:
        """变量存在但为空 == 不可解析（与 `has` 的语义一致）。"""
        gate = _gate(runtime=OPENHANDS_RUNTIME, resolver=_resolver(**{_CREDENTIAL_REF: ""}))
        assert gate.open is False  # type: ignore[attr-defined]

    def test_closed_gate_names_every_unmet_condition(self) -> None:
        """只报一条会让操作者多跑一个来回 ⇒ 未满足的条件必须都点名。"""
        gate = _gate(runtime="", resolver=_resolver())
        assert "not configured" in gate.reason  # type: ignore[attr-defined]
        assert _CREDENTIAL_REF in gate.reason  # type: ignore[attr-defined]


class TestGateOpensOnlyWithBothConditions:
    def test_open_with_live_runtime_and_resolvable_credential(self) -> None:
        gate = _gate(runtime=OPENHANDS_RUNTIME, resolver=_resolver(**{_CREDENTIAL_REF: "present"}))
        assert gate.open is True  # type: ignore[attr-defined]

    def test_gate_never_materialises_the_credential(self) -> None:
        """门只问「能不能」（`has`），不物化明文（`resolve` 才会要值）。"""

        class _ResolveForbidden:
            def has(self, credential_ref: str) -> bool:
                return True

            def resolve(self, credential_ref: str) -> object:
                raise AssertionError("the gate must not resolve the credential value")

        gate = evaluate_live_run_gate(
            credentials=_ResolveForbidden(),  # type: ignore[arg-type]
            endpoint=replace(endpoint(), credential_ref=_CREDENTIAL_REF),
            agent_runtime=OPENHANDS_RUNTIME,
            live_agent_runtime=OPENHANDS_RUNTIME,
        )
        assert gate.open is True


class TestZeroOutboundWhileClosed:
    """门关着时**不出网**：网络被拔掉也能判门、也能产出 skip 记录。"""

    def test_gate_and_skip_record_work_with_networking_disabled(self) -> None:
        def _no_network(*args: object, **kwargs: object) -> object:
            raise AssertionError("the closed gate must not open a socket")

        with mock.patch.object(socket, "socket", _no_network):
            gate = _gate(runtime="", resolver=_resolver())
            record = skip_record_for_gate(_RUN_ID, gate)  # type: ignore[arg-type]

        assert gate.open is False  # type: ignore[attr-defined]
        assert record.verdict is ModelReproducibilityVerdict.NOT_VERIFIED


class TestSkipIsNotAPass:
    def test_skip_record_is_not_verified_and_names_the_credential(self) -> None:
        gate = _gate(runtime=OPENHANDS_RUNTIME, resolver=_resolver())
        record = skip_record_for_gate(_RUN_ID, gate)  # type: ignore[arg-type]
        assert record.is_verified is False
        assert record.verdict is ModelReproducibilityVerdict.NOT_VERIFIED
        assert _CREDENTIAL_REF in (record.reason or "")

    def test_skip_record_registers_every_fingerprint_field_as_missing(self) -> None:
        gate = _gate(runtime="", resolver=_resolver())
        record = skip_record_for_gate(_RUN_ID, gate)  # type: ignore[arg-type]
        assert "endpoint_config_digest" in record.missing_fields
        assert record.model_tokens == 0 and record.usage_entries == 0

    def test_open_gate_is_not_a_skip(self) -> None:
        gate = _gate(runtime=OPENHANDS_RUNTIME, resolver=_resolver(**{_CREDENTIAL_REF: "present"}))
        with pytest.raises(ValueError, match="not a skip"):
            skip_record_for_gate(_RUN_ID, gate)  # type: ignore[arg-type]


class TestGateExistenceInTheDefaultSuite:
    """门控存在性：live 用例带 `requires_live_llm`，默认门只走 skip 路径。"""

    def test_live_first_run_module_is_marked_requires_live_llm(self) -> None:
        from tests.e2e import test_ec04_live_first_run

        # 单个 module 级 mark 时 pytestmark 是 MarkDecorator，多个时才是 list
        raw = test_ec04_live_first_run.pytestmark
        marks = {mark.name for mark in (raw if isinstance(raw, list) else [raw])}
        assert "requires_live_llm" in marks, "live 用例必须在默认门里被 skip 掉"

    def test_live_first_run_module_needs_no_network_at_import(self) -> None:
        def _no_network(*args: object, **kwargs: object) -> object:
            raise AssertionError("importing the live module must not open a socket")

        with mock.patch.object(socket, "socket", _no_network):
            from tests.e2e import test_ec04_live_first_run

        assert callable(test_ec04_live_first_run.test_live_first_run_reaches_a_terminal_state)
