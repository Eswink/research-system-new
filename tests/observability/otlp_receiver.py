"""In-repo OTLP/HTTP receiver(证据级,真实 socket + 真实 protobuf 解码)。

用途:
- m0 确定性门禁:不需要外部 collector 即可断言真实 OTLP wire bytes
  (隐私 canary 扫描原始 payload,不依赖 vendor UI);
- `requires_collector` 标记的 pinned collector 证据套件之外的确定性替代。

实现:ThreadingHTTPServer 监听 127.0.0.1 临时端口,接收 POST /v1/traces 与
/v1/metrics,保存原始字节并用 opentelemetry-proto 解码;响应真实 protobuf
ServiceResponse(200)。仅绑定 loopback,进程内自清理。
"""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import (
    ExportMetricsServiceRequest,
    ExportMetricsServiceResponse,
)
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
    ExportTraceServiceRequest,
    ExportTraceServiceResponse,
)

_CONTENT_TYPE = "application/x-protobuf"


class _Handler(BaseHTTPRequestHandler):
    server: "_OtlpServer"

    def do_POST(self) -> None:  # noqa: N802 - http.server 命名约定
        length = int(self.headers.get("Content-Length") or 0)
        payload = self.rfile.read(length)
        if self.path == "/v1/traces":
            request = ExportTraceServiceRequest.FromString(payload)
            self.server.traces.append(request)
            body = ExportTraceServiceResponse().SerializeToString()
        elif self.path == "/v1/metrics":
            request = ExportMetricsServiceRequest.FromString(payload)
            self.server.metrics.append(request)
            body = ExportMetricsServiceResponse().SerializeToString()
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.server.payloads.append(payload)
        self.send_response(200)
        self.send_header("Content-Type", _CONTENT_TYPE)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return  # 静默:测试期不产生输出噪声


class _OtlpServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.traces: list[ExportTraceServiceRequest] = []
        self.metrics: list[ExportMetricsServiceRequest] = []
        self.payloads: list[bytes] = []


class OtlpHttpReceiver:
    """进程内 OTLP/HTTP receiver;`start()` 后经 `endpoint` 接收导出。"""

    def __init__(self) -> None:
        self._server = _OtlpServer()
        self._thread: threading.Thread | None = None

    @property
    def endpoint(self) -> str:
        address = self._server.server_address
        return "http://{}:{}".format(str(address[0]), int(address[1]))

    @property
    def traces(self) -> tuple[ExportTraceServiceRequest, ...]:
        return tuple(self._server.traces)

    @property
    def metrics(self) -> tuple[ExportMetricsServiceRequest, ...]:
        return tuple(self._server.metrics)

    @property
    def payloads(self) -> tuple[bytes, ...]:
        """全部原始请求字节(隐私 canary 扫描用)。"""
        return tuple(self._server.payloads)

    @property
    def span_names(self) -> tuple[str, ...]:
        return tuple(
            span.name
            for request in self.traces
            for resource in request.resource_spans
            for scope in resource.scope_spans
            for span in scope.spans
        )

    def start(self) -> None:
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
