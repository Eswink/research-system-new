"""OpenAIChatGateway probe 与 retry 离线测试（httpx.MockTransport）。"""

from __future__ import annotations

import httpx
import pytest

from adapters.relay.gateway import RelayHTTPError
from packages.application.ports import CompletionRequest
from packages.domain.enums import FailureCategory

from .relay_fakes import (
    CREDENTIAL,
    ENDPOINT,
    RETRY_ENDPOINT,
    gateway,
    json_response,
)


class TestProbeEndpoint:
    def test_success_snapshot(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return json_response(
                {
                    "model": "model-alpha",
                    "system_fingerprint": "fp_1",
                    "choices": [{"message": {"role": "assistant", "content": "pong"}}],
                },
                headers={"x-request-id": "req-probe"},
            )

        snapshot = gateway(handler).probe_endpoint(
            ENDPOINT,
            CREDENTIAL,
            CompletionRequest(model="model-alpha", messages=[{"role": "user", "content": "pong"}]),
        )
        assert snapshot.ok is True
        assert snapshot.returned_model_name == "model-alpha"
        assert snapshot.system_fingerprint == "fp_1"
        assert snapshot.safe_response_metadata["x-request-id"] == "req-probe"

    def test_failure_snapshot_no_raise(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return json_response({"error": {"message": "rate limited"}}, status=429)

        snapshot = gateway(handler).probe_endpoint(
            ENDPOINT,
            CREDENTIAL,
            CompletionRequest(model="model-alpha", messages=[{"role": "user", "content": "pong"}]),
        )
        assert snapshot.ok is False
        assert snapshot.error_category is FailureCategory.MODEL_RATE_LIMIT

    def test_network_error_snapshot(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connect failed")

        snapshot = gateway(handler).probe_endpoint(
            ENDPOINT,
            CREDENTIAL,
            CompletionRequest(model="model-alpha", messages=[{"role": "user", "content": "pong"}]),
        )
        assert snapshot.ok is False
        assert snapshot.error_category is FailureCategory.EXECUTION_FAILURE

    def test_timeout_snapshot(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timed out", request=request)

        snapshot = gateway(handler).probe_endpoint(
            ENDPOINT,
            CREDENTIAL,
            CompletionRequest(model="model-alpha", messages=[{"role": "user", "content": "pong"}]),
        )
        assert snapshot.ok is False
        assert snapshot.error_category is FailureCategory.MODEL_TIMEOUT

    def test_malformed_json_body_snapshot(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="<html>not json</html>")

        snapshot = gateway(handler).probe_endpoint(
            ENDPOINT,
            CREDENTIAL,
            CompletionRequest(model="model-alpha", messages=[{"role": "user", "content": "pong"}]),
        )
        assert snapshot.ok is False
        assert snapshot.error_category is FailureCategory.MODEL_INCOMPATIBLE

    def test_malformed_sse_snapshot(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="data: {not-json}\n\n")

        snapshot = gateway(handler).probe_endpoint(
            ENDPOINT,
            CREDENTIAL,
            CompletionRequest(
                model="model-alpha", messages=[{"role": "user", "content": "pong"}], stream=True
            ),
        )
        assert snapshot.ok is False
        assert snapshot.error_category is FailureCategory.MODEL_INCOMPATIBLE

    def test_usage_reported_passthrough(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return json_response({
                "choices": [{"message": {"role": "assistant", "content": "pong"}}],
                "usage": {"total_tokens": 6},
            })

        snapshot = gateway(handler).probe_endpoint(
            ENDPOINT,
            CREDENTIAL,
            CompletionRequest(model="model-alpha", messages=[{"role": "user", "content": "pong"}]),
        )
        assert snapshot.ok is True
        assert snapshot.usage_reported is True

    def test_usage_not_reported_when_absent(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return json_response({
                "choices": [{"message": {"role": "assistant", "content": "pong"}}]
            })

        snapshot = gateway(handler).probe_endpoint(
            ENDPOINT,
            CREDENTIAL,
            CompletionRequest(model="model-alpha", messages=[{"role": "user", "content": "pong"}]),
        )
        assert snapshot.ok is True
        assert snapshot.usage_reported is False


class TestProbeConnectivity:
    def test_success(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/v1/models"
            return json_response({"object": "list", "data": [{"id": "m"}]})

        snapshot = gateway(handler).probe_connectivity(ENDPOINT, CREDENTIAL)
        assert snapshot.ok is True

    def test_auth_failure(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return json_response({"error": {"message": "unauthorized"}}, status=401)

        snapshot = gateway(handler).probe_connectivity(ENDPOINT, CREDENTIAL)
        assert snapshot.ok is False
        assert snapshot.error_category is FailureCategory.MODEL_AUTH

    def test_network_failure(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("unreachable")

        snapshot = gateway(handler).probe_connectivity(ENDPOINT, CREDENTIAL)
        assert snapshot.ok is False
        assert snapshot.error_category is FailureCategory.EXECUTION_FAILURE


class TestRetry:
    def test_rate_limit_retried_until_exhausted(self) -> None:
        attempts: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            attempts.append(1)
            return json_response({"error": {"message": "rate limited"}}, status=429)

        with pytest.raises(RelayHTTPError) as exc_info:
            gateway(handler).list_models(RETRY_ENDPOINT, CREDENTIAL)
        assert len(attempts) == 3
        assert exc_info.value.category is FailureCategory.MODEL_RATE_LIMIT

    def test_auth_error_not_retried(self) -> None:
        attempts: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            attempts.append(1)
            return json_response({"error": {"message": "bad key"}}, status=401)

        with pytest.raises(RelayHTTPError) as exc_info:
            gateway(handler).list_models(RETRY_ENDPOINT, CREDENTIAL)
        assert len(attempts) == 1
        assert exc_info.value.category is FailureCategory.MODEL_AUTH

    def test_success_after_retry(self) -> None:
        attempts: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            attempts.append(1)
            if len(attempts) == 1:
                return json_response({"error": {"message": "rate limited"}}, status=429)
            return json_response({"object": "list", "data": [{"id": "m"}]})

        result = gateway(handler).list_models(RETRY_ENDPOINT, CREDENTIAL)
        assert len(attempts) == 2
        assert result.model_ids == ("m",)
