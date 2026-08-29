"""可编程故障 collector(真实 socket,fault-injection 用)。

模式:
- "ok":正常 200;
- "500":每次导出返回 500;
- "slow":延迟 `slow_seconds` 后 200(OTLP timeout 注入);
- "hangup":接受连接后立即断开(网络中断);
- "restart":stop→start 窗口内的请求连接拒绝(collector 重启);
- "refused":不启动服务(collector down)。
"""

from __future__ import annotations

import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class _FaultHandler(BaseHTTPRequestHandler):
    server: "_FaultServer"

    def do_POST(self) -> None:  # noqa: N802 - http.server 命名约定
        length = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(length)
        self.server.requests += 1
        mode = self.server.mode
        if mode == "500":
            self.send_response(500)
            self.end_headers()
            return
        if mode == "hangup":
            self.wfile.close()
            self.connection.close()
            return
        if mode == "slow":
            time.sleep(self.server.slow_seconds)
        self.send_response(200)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


class _FaultServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _FaultHandler)
        self.mode = "ok"
        self.slow_seconds = 1.5
        self.requests = 0


class FaultyCollector:
    """真实 socket 故障注入 collector;进程内自清理。"""

    def __init__(self) -> None:
        self._server: _FaultServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def endpoint(self) -> str:
        assert self._server is not None
        address = self._server.server_address
        return "http://{}:{}".format(str(address[0]), int(address[1]))

    @property
    def requests(self) -> int:
        return self._server.requests if self._server else 0

    def set_mode(self, mode: str) -> None:
        assert self._server is not None
        self._server.mode = mode

    def set_slow_seconds(self, seconds: float) -> None:
        assert self._server is not None
        self._server.slow_seconds = seconds

    def start(self) -> None:
        if self._server is not None:
            return
        self._server = _FaultServer()
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        self._server = None
        self._thread = None

    @contextmanager
    def restart_window(self) -> Iterator[None]:
        """模拟 collector 重启:停服务,调用方完成动作后恢复。"""
        self.stop()
        try:
            yield
        finally:
            self.start()
