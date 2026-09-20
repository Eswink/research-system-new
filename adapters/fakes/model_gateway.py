"""FakeModelGateway：可控模型网关（无网络；OpenAI-compatible 语义最小面）。"""

from __future__ import annotations

from dataclasses import dataclass

from adapters.fakes.base import FakeBase
from packages.application.ports.credential_resolver import SecretValue
from packages.application.ports.errors import PortTimeoutError, TransientPortError
from packages.application.ports.model_gateway import (
    CompletionRequest,
    CompletionResult,
    ModelsListResult,
)
from packages.domain.enums import FailureCategory
from packages.domain.models import EndpointProbeSnapshot, LLMEndpoint


@dataclass(frozen=True, slots=True)
class FakeModelGatewayOptions:
    """FakeModelGateway 注入选项（参数对象，规避构造参数爆发）。

    - 故障注入（fail_timeout / fail_transient）：首调抛 PortError。
    - 失败快照注入（auth_fails / stream_fails / tool_fails / structured_fails）：
      探测返回 ok=False 快照而非异常，模拟"探测到不支持"的语义。
    - malformed_result：complete 返回缺 content 的结果。
    - no_usage：probe 快照不报告 usage。
    """

    model_ids: tuple[str, ...] = ("model-alpha", "model-beta")
    #: probe / complete 回报的模型标识（EC-05 漂移判据用它造「一致 / 漂移」两种夹具；
    #: 默认值 = 既有硬编码值，既有用例行为不变）。
    returned_model_name: str = "model-alpha"
    fail_timeout: bool = False
    fail_transient: bool = False
    malformed_result: bool = False
    auth_fails: bool = False
    stream_fails: bool = False
    tool_fails: bool = False
    structured_fails: bool = False
    no_usage: bool = False


class FakeModelGateway(FakeBase):
    """ModelGateway 实现；支持结果形态注入与故障注入。

    错误注入统一走 FakeBase 脚本机制：fail_timeout / fail_transient 在
    构造时预置为每个方法的首调失败脚本；运行时可按序补充 set_script。
    失败快照注入与 usage 开关是结果形态注入，与故障注入语义分离。
    """

    _FAULT_METHODS = ("list_models", "complete", "probe_endpoint", "probe_connectivity")

    def __init__(self, options: FakeModelGatewayOptions | None = None) -> None:
        super().__init__("model_gateway")
        opts = options or FakeModelGatewayOptions()
        self._model_ids = opts.model_ids
        self._returned_model_name = opts.returned_model_name
        self._malformed = opts.malformed_result
        self._auth_fails = opts.auth_fails
        self._stream_fails = opts.stream_fails
        self._tool_fails = opts.tool_fails
        self._structured_fails = opts.structured_fails
        self._no_usage = opts.no_usage
        if opts.fail_timeout:
            fault: PortTimeoutError | TransientPortError | None = PortTimeoutError(
                "fake gateway timeout",
                failure_category=FailureCategory.MODEL_TIMEOUT,
            )
        elif opts.fail_transient:
            fault = TransientPortError(
                "fake gateway transient failure",
                failure_category=FailureCategory.MODEL_RELAY_UNAVAILABLE,
            )
        else:
            fault = None
        if fault is not None:
            for method in self._FAULT_METHODS:
                self.set_script(method, [fault])

    def _probe_failure(self, category: FailureCategory, message: str) -> EndpointProbeSnapshot:
        return EndpointProbeSnapshot(
            ok=False,
            error_category=category,
            error_message_redacted=message,
        )

    def _ok_probe(self) -> EndpointProbeSnapshot:
        return EndpointProbeSnapshot(
            ok=True,
            returned_model_name=self._returned_model_name,
            system_fingerprint="fp_1",
            safe_response_metadata={"x-request-id": "req-1"} if not self._no_usage else {},
            usage_reported=not self._no_usage,
        )

    def list_models(self, endpoint: LLMEndpoint, credential: SecretValue) -> ModelsListResult:
        self._enter("list_models", endpoint.id)
        self._record("list_models", endpoint.id, result="2")
        return ModelsListResult(model_ids=self._model_ids)

    def complete(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> CompletionResult:
        summary = f"{endpoint.id}/{request.model}"
        self._enter("complete", summary)
        if self._malformed:
            result = CompletionResult(usage_reported=True)
            self._record("complete", summary, result="malformed")
            return result
        result = CompletionResult(
            content="pong",
            returned_model_name=self._returned_model_name,
            system_fingerprint="fp_1",
            usage_reported=True,
            safe_response_metadata={"x-request-id": "req-1"},
        )
        self._record("complete", summary, result="ok")
        return result

    def probe_endpoint(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> EndpointProbeSnapshot:
        summary = f"{endpoint.id}/{request.model}"
        self._enter("probe_endpoint", summary)
        if request.stream and self._stream_fails:
            result = self._probe_failure(
                FailureCategory.EXECUTION_FAILURE, "stream interrupted ***REDACTED***"
            )
        elif request.tools and self._tool_fails:
            result = self._probe_failure(
                FailureCategory.MODEL_INCOMPATIBLE, "HTTP 400: tools unsupported"
            )
        elif request.response_format and self._structured_fails:
            result = self._probe_failure(
                FailureCategory.MODEL_INCOMPATIBLE, "HTTP 422: response_format unsupported"
            )
        else:
            result = self._ok_probe()
        self._record("probe_endpoint", summary, result=str(result.ok))
        return result

    def probe_connectivity(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
    ) -> EndpointProbeSnapshot:
        self._enter("probe_connectivity", endpoint.id)
        if self._auth_fails:
            result = self._probe_failure(FailureCategory.MODEL_AUTH, "401 ***REDACTED***")
        else:
            result = EndpointProbeSnapshot(ok=True)
        self._record("probe_connectivity", endpoint.id, result=str(result.ok))
        return result
