"""OpenAI-compatible Chat Completions 网关（httpx + tenacity）。

协议基线：OpenAI openapi.yaml v2.3.0 的 `/v1/chat/completions` 与 `/v1/models`。
错误分类 / 重试 / 请求执行在 transport；completion 变体在 completions；
请求/解析细节在 chat_api / responses_api / streaming（规模阈值拆分）。
响应头只采集白名单（Authorization 永不进入结果）；错误消息一律 redacted。
M15 观测:`telemetry` 注入(默认 None);只发 LLM_CALL span + retry metric,
attributes 走闭集词汇,无内容通道(ADR-0026)。
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime, timezone

import httpx

from adapters.relay.completions import complete_any
from adapters.relay.transport import (
    RelayHTTPError,
    decode_json,
    join_url,
    request_with_retries,
)
from packages.application.observability.scope import operation
from packages.application.observability.signals import OperationOutcome, OperationScope
from packages.application.ports import (
    CompletionRequest,
    CompletionResult,
    ModelsListResult,
    SecretValue,
)
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.domain.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerState,
    CircuitBreakerTransitionError,
    apply_failure,
    apply_success,
    apply_tick,
    initial_state,
)
from packages.domain.enums import FailureCategory
from packages.domain.models import EndpointProbeSnapshot, LLMEndpoint

__all__ = [
    "OpenAIChatGateway",
    "RelayHTTPError",
]


class CircuitOpenRelayError(RelayHTTPError):
    """断路器 OPEN:请求未触达网络即被短路。"""


def _outcome_for_category(category: FailureCategory) -> OperationOutcome:
    if category is FailureCategory.MODEL_TIMEOUT:
        return OperationOutcome.TIMEOUT
    return OperationOutcome.FAILED


class OpenAIChatGateway:
    """OpenAI-compatible 网关（httpx + tenacity）。

    支持 chat_completions 与 responses 两种 API 风格（LLMEndpoint.api_style），
    共用 error classification / retry / 脱敏。
    """

    def __init__(
        self,
        transport: httpx.BaseTransport | None = None,
        default_timeout_seconds: float = 60.0,
        telemetry: TelemetrySink | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._client = httpx.Client(transport=transport, timeout=default_timeout_seconds)
        self._telemetry = telemetry
        self._now = now
        # M15 债务清偿:per-endpoint 内存态断路器(仅 endpoint.circuit_breaker
        # 配置存在时启用);无持久化,进程重启重置(如实声明)。
        self._breakers: dict[str, CircuitBreakerState] = {}
        self._breaker_lock = threading.Lock()

    def _breaker_state(self, endpoint_id: str) -> CircuitBreakerState:
        with self._breaker_lock:
            return self._breakers.get(endpoint_id, initial_state())

    def _store_breaker(self, endpoint_id: str, state: CircuitBreakerState) -> None:
        with self._breaker_lock:
            self._breakers[endpoint_id] = state

    def _consult_circuit(self, endpoint: LLMEndpoint) -> str:
        """consult + tick;返回当前状态串(未配置断路器返回 "")。

        OPEN → 抛 `CircuitOpenRelayError`(请求不触达网络)。HALF_OPEN 进入
        计一次探测名额;探测名额耗尽的再次 consult 视为拒绝(迁移错误吞掉)。
        """
        config: CircuitBreakerConfig | None = endpoint.circuit_breaker
        if config is None:
            return ""
        moment = self._now() if self._now is not None else datetime.now(timezone.utc)
        state = self._breaker_state(endpoint.id)
        try:
            state = apply_tick(state, config, moment)
        except CircuitBreakerTransitionError:
            pass  # HALF_OPEN 探测名额耗尽:本次 consult 拒绝
        self._store_breaker(endpoint.id, state)
        if state.is_open:
            raise CircuitOpenRelayError(
                FailureCategory.MODEL_RELAY_UNAVAILABLE,
                "circuit open: endpoint temporarily unavailable",
            )
        return state.state

    def _record_request_outcome(self, endpoint: LLMEndpoint, ok: bool) -> None:
        """请求结果驱动断路器迁移;OPEN 状态下的迟到迁移错误吞掉(并发边界)。"""
        config: CircuitBreakerConfig | None = endpoint.circuit_breaker
        if config is None:
            return
        moment = self._now() if self._now is not None else datetime.now(timezone.utc)
        state = self._breaker_state(endpoint.id)
        try:
            state = apply_success(state, config) if ok else apply_failure(state, config, now=moment)
        except CircuitBreakerTransitionError:
            return
        self._store_breaker(endpoint.id, state)

    def list_models(self, endpoint: LLMEndpoint, credential: SecretValue) -> ModelsListResult:
        url = join_url(endpoint.base_url, "/models")
        with operation(
            self._telemetry,
            scope=OperationScope.LLM_CALL,
            name="llm.list_models",
            attributes={"endpoint_id": endpoint.id},
        ) as op:
            try:
                circuit_state = self._consult_circuit(endpoint)
                response, _attempts = request_with_retries(
                    self._client, "GET", url, endpoint, credential, telemetry=self._telemetry
                )
            except CircuitOpenRelayError:
                op.set_outcome(
                    OperationOutcome.DENIED,
                    FailureCategory.MODEL_RELAY_UNAVAILABLE.value,
                    extra={"endpoint_id": endpoint.id, "circuit_state": "OPEN"},
                )
                raise
            except RelayHTTPError:
                self._record_request_outcome(endpoint, ok=False)
                raise
            self._record_request_outcome(endpoint, ok=True)
            payload = decode_json(response, "models")
            ids = tuple(
                str(item.get("id")) for item in payload.get("data", []) if isinstance(item, dict)
            )
            op.set_outcome(
                OperationOutcome.OK,
                extra={
                    "endpoint_id": endpoint.id,
                    "status_code_class": "2xx",
                    **({"circuit_state": circuit_state} if circuit_state else {}),
                },
            )
            return ModelsListResult(model_ids=ids)

    def complete(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> CompletionResult:
        base_attributes: dict[str, object] = {
            "endpoint_id": endpoint.id,
            "model_id": request.model,
        }
        with operation(
            self._telemetry,
            scope=OperationScope.LLM_CALL,
            name="llm.call",
            attributes=base_attributes,
        ) as op:
            try:
                circuit_state = self._consult_circuit(endpoint)
                if circuit_state:
                    base_attributes = {**base_attributes, "circuit_state": circuit_state}
                result = complete_any(self._client, endpoint, credential, request, self._telemetry)
            except CircuitOpenRelayError as exc:
                op.set_outcome(
                    OperationOutcome.DENIED,
                    failure_category=exc.category.value,
                    extra={**base_attributes, "circuit_state": "OPEN"},
                )
                raise
            except RelayHTTPError as exc:
                self._record_request_outcome(endpoint, ok=False)
                op.set_outcome(
                    _outcome_for_category(exc.category),
                    failure_category=exc.category.value,
                )
                raise
            self._record_request_outcome(endpoint, ok=True)
            extra: dict[str, object] = {**base_attributes, "status_code_class": "2xx"}
            if result.usage_reported and result.total_tokens is not None:
                extra["prompt_tokens"] = result.prompt_tokens or 0
                extra["completion_tokens"] = result.completion_tokens or 0
                extra["total_tokens"] = result.total_tokens
            op.set_outcome(OperationOutcome.OK, extra=extra)
            return result

    def probe_connectivity(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
    ) -> EndpointProbeSnapshot:
        """GET /models 连通性探测：任意失败返回快照，不抛异常。"""
        try:
            self.list_models(endpoint, credential)
        except RelayHTTPError as exc:
            return EndpointProbeSnapshot(
                ok=False,
                error_category=exc.category,
                error_message_redacted=str(exc),
            )
        return EndpointProbeSnapshot(ok=True)

    def probe_endpoint(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> EndpointProbeSnapshot:
        """endpoint 探测：任意失败都返回快照，不抛异常。"""
        try:
            result = self.complete(endpoint, credential, request)
        except RelayHTTPError as exc:
            return EndpointProbeSnapshot(
                ok=False,
                error_category=exc.category,
                error_message_redacted=str(exc),
            )
        return EndpointProbeSnapshot(
            ok=True,
            returned_model_name=result.returned_model_name,
            system_fingerprint=result.system_fingerprint,
            safe_response_metadata=dict(result.safe_response_metadata),
            usage_reported=result.usage_reported,
        )

    def close(self) -> None:
        self._client.close()
