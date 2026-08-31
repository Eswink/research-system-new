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


class NetProxy:
    """Forwarding loopback proxy; `blackhole` simulates a network partition."""

    def __init__(self, target_host: str, target_port: int) -> None:
        self._target = (target_host, target_port)
        self._blackholed = threading.Event()
        self._stopping = threading.Event()
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

    def blackhole(self) -> None:
        self._blackholed.set()

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
        try:
            upstream = socket.create_connection(self._target, timeout=5)
            upstream.settimeout(0.2)
            client.settimeout(0.2)
            while not self._stopping.is_set():
                if self._blackholed.is_set():
                    self._stall(client)
                    return
                if not self._pump(client, upstream) and not self._pump(upstream, client):
                    self._sleep()
        except OSError:
            pass
        finally:
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
        """Hold the client open but silent (partition: bytes never flow)."""
        client.settimeout(0.2)
        while not self._stopping.is_set():
            try:
                if client.recv(65536) == b"":
                    return
            except socket.timeout:
                continue
            except OSError:
                return

    def _sleep(self) -> None:
        self._stopping.wait(0.05)
