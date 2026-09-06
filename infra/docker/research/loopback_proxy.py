"""Fixed-target TCP proxy for loopback-only Compose host access.

The proxy receives no credentials and accepts targets only from its startup
arguments. It bridges Docker Desktop host-published ports to services that
remain on the internal Research OS network.
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from functools import partial

_BUFFER_SIZE = 64 * 1024


@dataclass(frozen=True, slots=True)
class Forward:
    """One local TCP listener and its fixed internal destination."""

    listen_port: int
    target_host: str
    target_port: int


def _port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise ValueError("forward mapping ports must be integers") from exc
    if not 1 <= port <= 65535:
        raise ValueError("forward mapping ports must be between 1 and 65535")
    return port


def parse_forward(value: str) -> Forward:
    """Parse `listen_port=target_host:target_port` without arbitrary defaults."""
    try:
        listen, target = value.split("=", maxsplit=1)
        target_host, target_port = target.rsplit(":", maxsplit=1)
    except ValueError as exc:
        raise ValueError("forward mapping must be listen_port=target_host:target_port") from exc
    if not target_host or any(character.isspace() for character in target_host):
        raise ValueError("forward mapping target host must be non-empty and contain no whitespace")
    return Forward(_port(listen), target_host, _port(target_port))


async def _pump(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    while data := await reader.read(_BUFFER_SIZE):
        writer.write(data)
        await writer.drain()


async def _proxy_connection(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    *,
    forward: Forward,
) -> None:
    try:
        target_reader, target_writer = await asyncio.open_connection(
            forward.target_host, forward.target_port
        )
    except OSError:
        writer.close()
        await writer.wait_closed()
        return
    tasks = (
        asyncio.create_task(_pump(reader, target_writer)),
        asyncio.create_task(_pump(target_reader, writer)),
    )
    _, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    target_writer.close()
    writer.close()
    await asyncio.gather(target_writer.wait_closed(), writer.wait_closed())


async def start_servers(forwards: Sequence[Forward]) -> tuple[asyncio.AbstractServer, ...]:
    """Start one listener per fixed mapping and return controllable servers."""
    if not forwards:
        raise ValueError("at least one forward mapping is required")
    servers: list[asyncio.AbstractServer] = []
    for forward in forwards:
        handler = partial(_proxy_connection, forward=forward)
        server = await asyncio.start_server(handler, "0.0.0.0", forward.listen_port)
        servers.append(server)
    return tuple(servers)


async def serve(forwards: Sequence[Forward]) -> None:
    """Serve all fixed mappings until the process receives termination."""
    servers = await start_servers(forwards)
    for forward in forwards:
        print(  # noqa: T201 - container lifecycle evidence, contains no credentials
            f"loopback-proxy: {forward.listen_port} -> {forward.target_host}:{forward.target_port}",
            flush=True,
        )
    await asyncio.gather(*(server.serve_forever() for server in servers))


def parse_args(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Forward fixed TCP ports into Compose internals")
    parser.add_argument("--listen", action="append", required=True, type=parse_forward)
    return parser.parse_args(arguments)


def main(arguments: Sequence[str] | None = None) -> int:
    args = parse_args(arguments)
    asyncio.run(serve(tuple(args.listen)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
