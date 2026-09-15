"""Loopback TCP proxy with per-connection blackhole control (M16 WP4).

A minimal, dependency-free proxy in the shape of
tests/observability/fault_collector.py: it listens on an ephemeral loopback
port, forwards bytes to a target, and can drop/blackhole connections (bytes
stop flowing both ways while the TCP connections stay open) to simulate a
network partition for a single worker.
"""

from __future__ import annotations

import socket
import threading
import time


class NetProxy:
    """Forwarding loopback proxy; `blackhole` simulates a network partition."""

    def __init__(self, target_host: str, target_port: int) -> None:
        self._target = (target_host, target_port)
        self._blackholed = threading.Event()
        self._stopping = threading.Event()
        self._lock = threading.Lock()
        self._live_connections = 0
        self._stalled_connections = 0
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        listener.listen(8)
        listener.settimeout(0.2)
        self._listener = listener
        self._threads: list[threading.Thread] = []
        self.port = int(listener.getsockname()[1])

    @property
    def blackholed(self) -> bool:
        return self._blackholed.is_set()

    def start(self) -> None:
        acceptor = threading.Thread(target=self._accept_loop, name="net-proxy-accept", daemon=True)
        acceptor.start()
        self._threads.append(acceptor)

    def blackhole(self, timeout: float = 2.0) -> None:
        """Start the partition; returns once no byte can transit.

        The pump only checks the flag between iterations, so a connection already
        blocked in `recv` would still forward the next bytes to arrive — the
        partition would be "soon" rather than "now". Waiting for every live
        connection to reach the stall keeps the fault honest for callers that
        assert bytes do not flow right after this call.
        """
        self._blackholed.set()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                if self._stalled_connections >= self._live_connections:
                    return
            time.sleep(0.01)

    def restore(self) -> None:
        self._blackholed.clear()

    def stop(self) -> None:
        self._stopping.set()
        self._blackholed.set()
        try:
            self._listener.close()
        except OSError:
            pass

    def _accept_loop(self) -> None:
        while not self._stopping.is_set():
            try:
                client, _addr = self._listener.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            worker = threading.Thread(
                target=self._pipe, args=(client,), name="net-proxy-conn", daemon=True
            )
            worker.start()
            self._threads.append(worker)

    def _pipe(self, client: socket.socket) -> None:
        upstream: socket.socket | None = None
        with self._lock:
            self._live_connections += 1
        try:
            upstream = socket.create_connection(self._target, timeout=5)
            upstream.settimeout(0.2)
            client.settimeout(0.2)
            while not self._stopping.is_set():
                if self._blackholed.is_set():
                    self._stall(client)
                    # `restore()` must actually restore: fall back into the pump
                    # loop so bytes blocked during the partition (still in the
                    # socket buffer, never consumed) flow again once it heals.
                    continue
                # Pump BOTH directions every iteration. A recv timeout is not
                # "closed" — short-circuiting on the client direction would
                # strand the upstream response and hang the client.
                alive_in = self._pump(client, upstream)
                alive_out = self._pump(upstream, client)
                if not alive_in or not alive_out:
                    return
        except OSError:
            pass
        finally:
            with self._lock:
                self._live_connections -= 1
            for sock in (client, upstream):
                if sock is not None:
                    try:
                        sock.close()
                    except OSError:
                        pass

    def _pump(self, src: socket.socket, dst: socket.socket) -> bool:
        try:
            data = src.recv(65536)
        except socket.timeout:
            return True
        except OSError:
            return False
        if not data:
            return False
        try:
            dst.sendall(data)
        except OSError:
            return False
        return True

    def _stall(self, client: socket.socket) -> None:
        """Hold the connection open but silent until the partition heals.

        Bytes the client sent are **peeked, never consumed**: the partition is
        "packets do not flow", not "bytes are thrown away". Consuming them would
        make the request unrecoverable after `restore()` (the client would wait
        out its full HTTP timeout with the request already swallowed), which is
        a different fault than a network partition and would strand callers that
        are correctly written — e.g. a worker blocked in a gateway request cannot
        honor SIGTERM until that read returns.

        Byte accounting for `blackhole()`: this loop is the point at which the
        partition becomes effective for the connection.
        """
        with self._lock:
            self._stalled_connections += 1
        client.settimeout(0.2)
        try:
            while not self._stopping.is_set() and self._blackholed.is_set():
                try:
                    if client.recv(65536, socket.MSG_PEEK) == b"":
                        return
                except socket.timeout:
                    continue
                except OSError:
                    return
        finally:
            with self._lock:
                self._stalled_connections -= 1

    def _sleep(self) -> None:
        self._stopping.wait(0.05)
