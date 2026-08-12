"""run_endpoint_test use case 测试（fake gateway 注入，无真实网络）。"""

from __future__ import annotations

from adapters.fakes import FakeCredentialResolver, FakeModelGateway, FakeModelGatewayOptions
from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
from packages.application.model_relay.probe import run_endpoint_test
from packages.domain.enums import FailureCategory
from packages.domain.models import EndpointProbeSnapshot

from .relay_fixtures import ENDPOINT, LOCALHOST_ENDPOINT


class TestRunEndpointTest:
    def test_success(self) -> None:
        gateway = FakeModelGateway()
        result = run_endpoint_test(
            gateway=gateway,
            credential_resolver=FakeCredentialResolver({"llm_main_key": "sk-test-token"}),
            endpoint=ENDPOINT,
            model_name="model-alpha",
        )
        assert result.ok
        assert result.returned_model_name == "model-alpha"
        assert result.error_category is None

    def test_auth_failure_is_machine_readable(self) -> None:
        gateway = FakeModelGateway(FakeModelGatewayOptions(auth_fails=True))
        result = run_endpoint_test(
            gateway=gateway,
            credential_resolver=FakeCredentialResolver({"llm_main_key": "sk-test-token"}),
            endpoint=ENDPOINT,
            model_name="model-alpha",
        )
        assert not result.ok
        assert result.error_category is FailureCategory.MODEL_AUTH

    def test_exception_redacted(self) -> None:
        class RaisingGateway(FakeModelGateway):
            def probe_endpoint(self, *args: object, **kwargs: object) -> EndpointProbeSnapshot:
                raise RuntimeError("Authorization: Bearer sk-super-secret-token-12345678 boom")

        result = run_endpoint_test(
            gateway=RaisingGateway(),
            credential_resolver=FakeCredentialResolver({"llm_main_key": "sk-test-token"}),
            endpoint=ENDPOINT,
            model_name="model-alpha",
        )
        assert not result.ok
        assert result.error_message is not None
        assert "sk-super-secret-token-12345678" not in result.error_message

    def test_credential_missing_is_configuration(self) -> None:
        result = run_endpoint_test(
            gateway=FakeModelGateway(),
            credential_resolver=FakeCredentialResolver({}),
            endpoint=ENDPOINT,
            model_name="model-alpha",
        )
        assert not result.ok
        assert result.error_category is FailureCategory.CONFIGURATION

    def test_url_policy_violation_is_configuration(self) -> None:
        result = run_endpoint_test(
            gateway=FakeModelGateway(),
            credential_resolver=FakeCredentialResolver({"llm_main_key": "sk-test-token"}),
            endpoint=LOCALHOST_ENDPOINT,
            model_name="model-alpha",
            url_policy=EndpointUrlPolicy(),
        )
        assert not result.ok
        assert result.error_category is FailureCategory.CONFIGURATION

    def test_url_policy_allowed_with_override(self) -> None:
        result = run_endpoint_test(
            gateway=FakeModelGateway(),
            credential_resolver=FakeCredentialResolver({"llm_main_key": "sk-test-token"}),
            endpoint=LOCALHOST_ENDPOINT,
            model_name="model-alpha",
            url_policy=EndpointUrlPolicy(allow_localhost=True),
        )
        assert result.ok
