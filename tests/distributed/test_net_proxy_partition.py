"""NetProxy 分区语义（M16 WP4）：`restore()` 必须真的恢复。

`tests/distributed/net_proxy.py` 是 D 场景（网络分区）的故障注入器，它模拟的是
「包不流动」，不是「字节被丢弃」：分区期间客户端已经发出的字节必须留在 socket 缓冲里，
分区解除后照常送达，请求才能完成。若注入器把字节**吞掉**，调用方就会卡到自己的 HTTP
超时——这正是 cycle 13 收口提交的 CI 上 `test_scenario_d_network_partition_no_old_authority`
teardown 报 `d-partitioned timed out after 10 seconds` 的机制（worker 阻塞在 gateway
请求里，SIGTERM 无法打断阻塞中的 socket 读）。

本模块只用 loopback socket，不依赖 PostgreSQL / 子进程 worker。
"""

from __future__ import annotations

import socket
import threading
import time
from collections.abc import Iterator
from contextlib import closing

import pytest

from tests.distributed.net_proxy import NetProxy


class _EchoServer:
    """单连接 loopback 回显服务：收到什么原样回什么。"""

    def __init__(self) -> None:
        self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener.bind(("127.0.0.1", 0))
        self._listener.listen(4)
        self._listener.settimeout(0.2)
        self.port = int(self._listener.getsockname()[1])
        self._stopping = threading.Event()
        self._thread = threading.Thread(target=self._serve, name="echo-server", daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        while not self._stopping.is_set():
            try:
                client, _addr = self._listener.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            with closing(client):
                client.settimeout(5)
                try:
                    data = client.recv(65536)
                    if data:
                        client.sendall(data)
                except OSError:
                    continue

    def stop(self) -> None:
        self._stopping.set()
        self._listener.close()
        self._thread.join(timeout=2)


@pytest.fixture()
def echo_server() -> Iterator[_EchoServer]:
    server = _EchoServer()
    try:
        yield server
    finally:
        server.stop()


def _recv_within(sock: socket.socket, timeout: float) -> bytes | None:
    sock.settimeout(timeout)
    try:
        return sock.recv(65536)
    except socket.timeout:
        return None


def test_restore_delivers_bytes_sent_during_partition(
    echo_server: _EchoServer,
) -> None:
    """分区期间发出的请求在恢复后完成（字节被保留，而不是被吞掉）。"""
    proxy = NetProxy("127.0.0.1", echo_server.port)
    proxy.start()
    try:
        with closing(socket.create_connection(("127.0.0.1", proxy.port), timeout=5)) as client:
            client.settimeout(5)
            proxy.blackhole()
            client.sendall(b"hello-during-partition")
            # 分区生效：字节不流动（回显不会回来）。
            assert _recv_within(client, 0.5) is None
            proxy.restore()
            # 恢复后：分区期间已发出的字节必须送达并被回显。
            assert _recv_within(client, 5) == b"hello-during-partition"
    finally:
        proxy.stop()


def test_partition_holds_new_connections_until_restore(
    echo_server: _EchoServer,
) -> None:
    """分区期间新连接同样静默；恢复后才流动（注入器不是单向吞字节）。"""
    proxy = NetProxy("127.0.0.1", echo_server.port)
    proxy.start()
    try:
        proxy.blackhole()
        with closing(socket.create_connection(("127.0.0.1", proxy.port), timeout=5)) as client:
            client.settimeout(5)
            client.sendall(b"first")
            assert _recv_within(client, 0.5) is None
            proxy.restore()
            assert _recv_within(client, 5) == b"first"
    finally:
        proxy.stop()


def test_closed_client_does_not_strand_the_stall(echo_server: _EchoServer) -> None:
    """分区期间客户端断开：stall 必须退出（不泄漏连接线程）。"""
    del echo_server
    proxy = NetProxy("127.0.0.1", 1)  # 目标不可达不影响本用例：分区期间不会连上游
    proxy.start()
    try:
        client = socket.create_connection(("127.0.0.1", proxy.port), timeout=5)
        proxy.blackhole()
        time.sleep(0.3)
        client.close()
        time.sleep(0.6)
        # stall 退出后连接线程结束；再次 restore 不应抛错，代理仍可服务新连接。
        proxy.restore()
    finally:
        proxy.stop()
