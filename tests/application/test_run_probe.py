"""run_probe use case 与 discovery 测试（fake gateway 注入，无真实网络）。"""

from __future__ import annotations

import pytest

from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
from packages.application.model_relay.probe import ProbeOptions, run_probe
from packages.application.model_relay.suite import DiscoveredModels, default_probe_suite
from packages.domain.enums import CapabilitySource, FailureCategory, ModelCapability

from .relay_fakes import (
    ENDPOINT,
    LOCALHOST_ENDPOINT,
    MODEL,
    FakeCredentialResolver,
    FakeGateway,
    MissingCredentialResolver,
)


class TestRunProbe:
    def test_full_probe_detects_capabilities(self) -> None:
        gateway = FakeGateway()
        result, assertions = run_probe(
            gateway=gateway,
            credential_resolver=FakeCredentialResolver(),
            endpoint=ENDPOINT,
            model=MODEL,
            options=ProbeOptions(suite=default_probe_suite()),
        )
        assert result.ok
        assert ModelCapability.CHAT in result.observed_capabilities
        assert ModelCapability.STREAMING in result.observed_capabilities
        assert ModelCapability.TOOL_CALLING_NATIVE in result.observed_capabilities
        assert ModelCapability.STRUCTURED_OUTPUT_NATIVE in result.observed_capabilities
        assert ModelCapability.USAGE_REPORTING in result.observed_capabilities
        assert ModelCapability.SYSTEM_FINGERPRINT in result.observed_capabilities
        assert ModelCapability.CHAT in assertions
        assert assertions[ModelCapability.CHAT].probe_version == "probe-suite-v1"

    def test_streaming_failure_not_fatal_and_recorded(self) -> None:
        gateway = FakeGateway(stream_fails=True)
        result, assertions = run_probe(
            gateway=gateway,
            credential_resolver=FakeCredentialResolver(),
            endpoint=ENDPOINT,
            model=MODEL,
            options=ProbeOptions(suite=default_probe_suite()),
        )
        assert result.ok
        assert ModelCapability.STREAMING not in result.observed_capabilities
        failures = {f.capability: f for f in result.capability_failures}
        assert ModelCapability.STREAMING in failures
        assert failures[ModelCapability.STREAMING].error_category is (
            FailureCategory.EXECUTION_FAILURE
        )

    def test_tool_and_structured_failures_recorded(self) -> None:
        gateway = FakeGateway(tool_fails=True, structured_fails=True)
        result, _ = run_probe(
            gateway=gateway,
            credential_resolver=FakeCredentialResolver(),
            endpoint=ENDPOINT,
            model=MODEL,
            options=ProbeOptions(suite=default_probe_suite()),
        )
        assert result.ok
        failures = {f.capability: f for f in result.capability_failures}
        assert failures[ModelCapability.TOOL_CALLING_NATIVE].error_category is (
            FailureCategory.MODEL_INCOMPATIBLE
        )
        assert failures[ModelCapability.STRUCTURED_OUTPUT_NATIVE].error_category is (
            FailureCategory.MODEL_INCOMPATIBLE
        )

    def test_no_usage_reporting(self) -> None:
        gateway = FakeGateway(no_usage=True)
        result, _ = run_probe(
            gateway=gateway,
            credential_resolver=FakeCredentialResolver(),
            endpoint=ENDPOINT,
            model=MODEL,
            options=ProbeOptions(suite=default_probe_suite()),
        )
        assert result.ok
        assert ModelCapability.USAGE_REPORTING not in result.observed_capabilities

    def test_auth_failure_aborts_probe(self) -> None:
        gateway = FakeGateway(auth_fails=True)
        result, assertions = run_probe(
            gateway=gateway,
            credential_resolver=FakeCredentialResolver(),
            endpoint=ENDPOINT,
            model=MODEL,
            options=ProbeOptions(suite=default_probe_suite()),
        )
        assert not result.ok
        assert result.error_category is FailureCategory.MODEL_AUTH
        assert assertions == {}
        assert result.capability_failures == ()

    def test_credential_missing_aborts_probe(self) -> None:
        result, assertions = run_probe(
            gateway=FakeGateway(),
            credential_resolver=MissingCredentialResolver(),
            endpoint=ENDPOINT,
            model=MODEL,
            options=ProbeOptions(suite=default_probe_suite()),
        )
        assert not result.ok
        assert result.error_category is FailureCategory.CONFIGURATION
        assert assertions == {}

    def test_url_policy_violation_aborts_probe(self) -> None:
        result, _ = run_probe(
            gateway=FakeGateway(),
            credential_resolver=FakeCredentialResolver(),
            endpoint=LOCALHOST_ENDPOINT,
            model=MODEL,
            options=ProbeOptions(url_policy=EndpointUrlPolicy()),
        )
        assert not result.ok
        assert result.error_category is FailureCategory.CONFIGURATION


class TestDiscoveredModels:
    def test_source_is_discovered(self) -> None:
        discovered = DiscoveredModels(model_ids=("model-alpha",))
        assert discovered.source is CapabilitySource.DISCOVERED

    def test_non_discovered_source_rejected(self) -> None:
        with pytest.raises(ValueError):
            DiscoveredModels(model_ids=("m",), source=CapabilitySource.PROBED)
