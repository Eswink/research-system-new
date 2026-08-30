"""可编程故障 collector(真实 socket,fault-injection 用)。

模式:
- "ok":正常 200;
- "500":每次导出返回 500;
- "slow":延迟 `slow_seconds` 后 200(OTLP timeout 注入);
- "blackhole":接受连接后长期不响应(生命周期上界测试用);
- "hangup":接受连接后立即断开(网络中断);
- "restart":stop→start 窗口内的请求连接拒绝(collector 重启);
- "refused":不启动服务(collector down)。

端口在首次 `start()` 后固定并在 `restart_window()` 内复用:原先每次
`start()` 都绑 port 0 拿新端口,重启后 sink 仍指向已死端口,"exporter 重启"
场景因此退化成第二次"collector down",无法观测恢复(M15 复审发现)。
"""

from __future__ import annotations

import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_BLACKHOLE_HOLD_SECONDS = 600.0


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
        if mode == "blackhole":
            # 接受并持有连接,永不响应(有限 sleep 以免线程永久泄漏)
            self.server.blackhole_gate.wait(_BLACKHOLE_HOLD_SECONDS)
            return
        if mode == "slow":
            time.sleep(self.server.slow_seconds)
        self.send_response(200)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


class _FaultServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port: int = 0) -> None:
        super().__init__(("127.0.0.1", port), _FaultHandler)
        self.mode = "ok"
        self.slow_seconds = 1.5
        self.requests = 0
        self.blackhole_gate = threading.Event()


class FaultyCollector:
    """真实 socket 故障注入 collector;进程内自清理,端口跨重启稳定。"""

    def __init__(self) -> None:
        self._server: _FaultServer | None = None
        self._thread: threading.Thread | None = None
        self._port: int = 0
        self._mode: str = "ok"
        self._slow_seconds: float = 1.5

    @property
    def endpoint(self) -> str:
        """稳定 endpoint:首次 start 后端口固定,重启后不变。"""
        assert self._port, "collector must be started before reading endpoint"
        return f"http://127.0.0.1:{self._port}"

    @property
    def requests(self) -> int:
        return self._server.requests if self._server else 0

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        if self._server is not None:
            self._server.mode = mode
            if mode != "blackhole":
                self._server.blackhole_gate.set()

    def set_slow_seconds(self, seconds: float) -> None:
        self._slow_seconds = seconds
        if self._server is not None:
            self._server.slow_seconds = seconds

    def start(self) -> None:
        if self._server is not None:
            return
        self._server = _FaultServer(self._port)
        self._port = int(self._server.server_address[1])
        self._server.mode = self._mode
        self._server.slow_seconds = self._slow_seconds
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is None:
            return
        self._server.blackhole_gate.set()
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        self._server = None
        self._thread = None

    @contextmanager
    def restart_window(self) -> Iterator[None]:
        """模拟 collector 重启:停服务,调用方完成动作后在**同一端口**恢复。"""
        self.stop()
        try:
            yield
        finally:
            self.start()
