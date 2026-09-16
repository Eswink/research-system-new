"""EC-04：SIGTERM 后阻塞中的网关读必须被有界放弃（PLAN-20260915-067）。

两种证据：

1. **进程内**（所有平台）：`WorkerClient._call` 在停机宽限期到期后放弃在途调用，
   抛 `WorkerDrainAbort`；**未停机时不做任何缩短**——同一条阻塞读照常跑完（反证，
   证明上界来自停机窗口而不是"给所有调用更短的超时"）。
2. **真实 SIGTERM**（POSIX）：起真 worker 子进程，网关是一个"接受连接但永不响应"的
   黑洞，`SIGTERM` 之后进程必须在 `drain_seconds + ε` 内退出。Windows 的
   `Popen.terminate()` 是 TerminateProcess（不是信号），代表不了 SIGTERM 语义，
   因此该用例在 Windows 上 skip —— Linux 证据由 CI 的 quality-ubuntu-latest 与
   容器复验提供（见 RECHECK-051 F-1 对同一限制的记录）。
"""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx
import pytest

from adapters.worker.client import WorkerClient, WorkerClientConfig, WorkerDrainAbort

ROOT = Path(__file__).resolve().parents[2]

#: 阻塞读的模拟时长：足够长到"没有放弃就一定等满"，又不至于拖慢套件。
_BLOCK_SECONDS = 1.5


class _BlockingTransport(httpx.BaseTransport):
    """接受请求后睡 `_BLOCK_SECONDS` 才回——模拟"连上了但永不响应"的读。

    回包形状按 register() 的握手契约给（`session_token` + `registration_generation`），
    这样"未停机 ⇒ 照常跑完"的反证可以走到解析成功那一步。
    """

    def __init__(self, block_seconds: float = _BLOCK_SECONDS) -> None:
        self._block_seconds = block_seconds
        self.calls = 0

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        time.sleep(self._block_seconds)
        body = {"session_token": "session-token-for-tests", "registration_generation": 1}
        return httpx.Response(200, json=body, request=request)


def _config(*, drain_seconds: float, request_timeout: float = 30.0) -> WorkerClientConfig:
    return WorkerClientConfig(
        base_url="http://gateway.invalid",
        enrollment_secret="enrollment-secret-for-tests",
        worker_id="worker-1",
        request_timeout_seconds=request_timeout,
        drain_seconds=drain_seconds,
    )


def test_blocked_read_is_abandoned_after_the_drain_window() -> None:
    """停机 + 宽限期到期 ⇒ 放弃在途调用（不再等客户端 30s 超时）。"""

    stop = {"flag": False}
    transport = _BlockingTransport()
    client = WorkerClient(_config(drain_seconds=0.3), transport, should_stop=lambda: stop["flag"])
    threading.Timer(0.1, lambda: stop.update(flag=True)).start()

    started = time.monotonic()
    with pytest.raises(WorkerDrainAbort, match="drain window"):
        client.register()
    elapsed = time.monotonic() - started
    # 明确小于"等满阻塞读"（_BLOCK_SECONDS）——下限不写死，只证明它真的被放弃了。
    assert elapsed < _BLOCK_SECONDS, elapsed
    assert transport.calls == 1  # 请求确实发出去了，被放弃的是"等待返回"


def test_no_shutdown_never_shortens_a_blocked_read() -> None:
    """反证：没有停机请求时，同一条阻塞读照常跑完（上界只来自停机窗口）。"""

    stop = {"flag": False}
    transport = _BlockingTransport()
    client = WorkerClient(_config(drain_seconds=0.1), transport, should_stop=lambda: stop["flag"])

    started = time.monotonic()
    body = client.register()
    elapsed = time.monotonic() - started
    assert body["session_token"]
    assert elapsed >= _BLOCK_SECONDS, elapsed  # 没有被 drain_seconds 截断


def test_client_without_should_stop_keeps_the_direct_semantics() -> None:
    """未注入 `should_stop`（测试/一次性脚本）⇒ 逐字保持原有调用语义。"""

    transport = _BlockingTransport(block_seconds=0.0)
    client = WorkerClient(_config(drain_seconds=0.1), transport)
    assert client.register()["session_token"] == "session-token-for-tests"


def test_second_call_after_the_deadline_aborts_without_waiting() -> None:
    """一旦停机，后续调用不再各等一个宽限期（同一个 deadline，只armed一次）。"""

    stop = {"flag": False}
    transport = _BlockingTransport(block_seconds=5.0)
    client = WorkerClient(_config(drain_seconds=0.2), transport, should_stop=lambda: stop["flag"])
    stop["flag"] = True

    started = time.monotonic()
    with pytest.raises(WorkerDrainAbort):
        client.register()
    assert time.monotonic() - started < 1.0


def test_drain_seconds_env_knob_has_a_default_and_a_range() -> None:
    """AC-06：默认值存在、非法值明确报错（不静默取默认）。"""

    from services.worker.__main__ import _drain_seconds

    original = os.environ.get("RESEARCHOS_WORKER_DRAIN_SECONDS")
    try:
        os.environ.pop("RESEARCHOS_WORKER_DRAIN_SECONDS", None)
        assert _drain_seconds() == 5.0
        os.environ["RESEARCHOS_WORKER_DRAIN_SECONDS"] = "2.5"
        assert _drain_seconds() == 2.5
        os.environ["RESEARCHOS_WORKER_DRAIN_SECONDS"] = "0"
        with pytest.raises(ValueError, match="within"):
            _drain_seconds()
        os.environ["RESEARCHOS_WORKER_DRAIN_SECONDS"] = "soon"
        with pytest.raises(ValueError, match="must be a number"):
            _drain_seconds()
    finally:
        if original is None:
            os.environ.pop("RESEARCHOS_WORKER_DRAIN_SECONDS", None)
        else:
            os.environ["RESEARCHOS_WORKER_DRAIN_SECONDS"] = original


# ── 真实 SIGTERM（POSIX）────────────────────────────────────────────────────


class _BlackholeGateway:
    """接受 TCP 连接、读完请求后永不响应——"连上了但读不到东西"的网关。"""

    def __init__(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(8)
        self.port = int(self._sock.getsockname()[1])
        self._conns: list[socket.socket] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        while not self._stop.is_set():
            try:
                conn, _ = self._sock.accept()
            except OSError:
                return
            self._conns.append(conn)  # 读走请求但从不回包

    def close(self) -> None:
        self._stop.set()
        for conn in self._conns:
            conn.close()
        self._sock.close()


def _worker_env(gateway_url: str, drain_seconds: str) -> dict[str, str]:
    return {
        **os.environ,
        "RESEARCHOS_WORKER_GATEWAY_URL": gateway_url,
        "RESEARCHOS_WORKER_ENROLLMENT_SECRET": "enrollment-secret-for-tests",
        "RESEARCHOS_WORKER_EXECUTION_BACKEND": "deterministic",
        "RESEARCHOS_WORKER_DRAIN_SECONDS": drain_seconds,
        "PYTHONPATH": str(ROOT),
        "PYTHONUNBUFFERED": "1",
    }


def _start_worker(gateway_url: str, drain_seconds: str) -> tuple[subprocess.Popen[str], float]:
    """起 worker 子进程并等到它进入网关调用（读到 'worker: starting'）。"""
    proc = subprocess.Popen(
        [sys.executable, "-m", "services.worker", "--worker-id", "worker-drain-test"],
        cwd=ROOT,
        env=_worker_env(gateway_url, drain_seconds),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    started = time.monotonic()
    assert proc.stdout is not None
    for _ in range(200):
        line = proc.stdout.readline()
        if "worker: starting" in line:
            time.sleep(0.5)  # 让 register() 真的进到阻塞读里
            return proc, started
        if proc.poll() is not None:
            raise AssertionError(f"worker exited before starting: {line!r}")
    raise AssertionError("worker never printed 'worker: starting'")


#: Windows 的 `Popen.terminate()` 是 TerminateProcess（不是信号），代表不了 SIGTERM 语义，
#: 因此真实信号用例只在 POSIX 上跑；Linux 证据由 CI 的 quality-ubuntu-latest 与容器复验提供。
_SIGTERM_ONLY = pytest.mark.skipif(os.name == "nt", reason="needs real SIGTERM (POSIX)")


@_SIGTERM_ONLY
def test_sigterm_exits_within_the_drain_window_while_blocked_in_a_read() -> None:
    """修复前：退出上界 = 客户端超时 30s；修复后：drain_seconds + ε。"""

    gateway = _BlackholeGateway()
    proc: subprocess.Popen[str] | None = None
    try:
        proc, _ = _start_worker(f"http://127.0.0.1:{gateway.port}", "1.0")
        assert proc.poll() is None  # 此刻它正阻塞在 register() 的读上
        signalled = time.monotonic()
        proc.send_signal(signal.SIGTERM)
        assert proc.wait(timeout=20) == 0
        elapsed = time.monotonic() - signalled
        assert elapsed < 5.0, f"worker took {elapsed:.1f}s to exit after SIGTERM"
    finally:
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)
        gateway.close()


@_SIGTERM_ONLY
def test_drain_window_governs_the_bound_not_a_fixed_cap() -> None:
    """宽限期是**配置**而不是写死的常数：把它调大，进程就不在 5s 处退出。

    这条是"上界来自停机窗口"的反证——如果实现里塞了一个固定的短上界，这里会失败。
    """

    gateway = _BlackholeGateway()
    proc: subprocess.Popen[str] | None = None
    try:
        proc, _ = _start_worker(f"http://127.0.0.1:{gateway.port}", "30")
        proc.send_signal(signal.SIGTERM)
        time.sleep(6.0)
        assert proc.poll() is None, "worker exited early — a fixed cap replaced drain_seconds"
    finally:
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)
        gateway.close()
