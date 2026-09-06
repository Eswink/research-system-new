"""Behavior tests for the fixed-target Compose loopback proxy."""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROXY_PATH = ROOT / "infra" / "docker" / "research" / "loopback_proxy.py"


def _load_proxy() -> ModuleType:
    if not PROXY_PATH.is_file():
        pytest.fail("loopback proxy module is missing")
    spec = importlib.util.spec_from_file_location("research_loopback_proxy", PROXY_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_forward_accepts_fixed_mapping() -> None:
    proxy = _load_proxy()

    forward = proxy.parse_forward("8000=api:8000")

    assert forward.listen_port == 8000
    assert forward.target_host == "api"
    assert forward.target_port == 8000


@pytest.mark.parametrize(
    "value",
    ("", "8000", "zero=api:8000", "0=api:8000", "8000=:8000", "8000=api:70000"),
)
def test_parse_forward_rejects_invalid_mapping(value: str) -> None:
    proxy = _load_proxy()

    with pytest.raises(ValueError, match="forward mapping"):
        proxy.parse_forward(value)


async def _echo(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    data = await reader.read(4096)
    writer.write(data)
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def _round_trip(proxy: ModuleType) -> None:
    target = await asyncio.start_server(_echo, "127.0.0.1", 0)
    target_socket = target.sockets[0]
    target_port = cast(tuple[str, int], target_socket.getsockname())[-1]
    mapping = proxy.Forward(0, "127.0.0.1", target_port)
    servers = await proxy.start_servers((mapping,))
    listen_socket = servers[0].sockets[0]
    listen_port = cast(tuple[str, int], listen_socket.getsockname())[-1]
    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", listen_port)
        writer.write(b"research-compose-proxy")
        await writer.drain()
        assert await reader.read(4096) == b"research-compose-proxy"
        writer.close()
        await writer.wait_closed()
    finally:
        for server in servers:
            server.close()
        await asyncio.gather(*(server.wait_closed() for server in servers))
        target.close()
        await target.wait_closed()


def test_proxy_forwards_bytes_to_declared_target() -> None:
    proxy: Any = _load_proxy()

    asyncio.run(_round_trip(proxy))
