"""Worker CLI entrypoint (M16): `python -m services.worker`.

Reads gateway connection + identity from the environment, builds a
DockerExecutionBackend (the worker's local sandbox), installs a SIGTERM drain
handler, and runs the worker loop. Machine-readable stdout lines support the
cross-process E2E harness (WP4).
"""

from __future__ import annotations

import argparse
import os
import signal
import sys

from adapters.execution.docker_backend import DockerExecutionBackend
from adapters.worker.client import WorkerClient, WorkerClientConfig
from services.worker.deterministic_backend import DeterministicExecutionBackend
from services.worker.loop import WorkerLoop, WorkerLoopConfig

_STOP = {"flag": False}


def _install_drain_handler() -> None:
    def _handler(_signum: int, _frame: object) -> None:
        _STOP["flag"] = True
        print("worker: drain requested", flush=True)  # noqa: T201

    signal.signal(signal.SIGTERM, _handler)


def _build_config(worker_id: str) -> WorkerClientConfig:
    caps = tuple(
        x for x in os.environ.get("RESEARCHOS_WORKER_CAPABILITIES", "docker").split(",") if x
    )
    backends = tuple(
        x for x in os.environ.get("RESEARCHOS_WORKER_BACKEND_KINDS", "DOCKER").split(",") if x
    )
    raw_slots = os.environ.get("RESEARCHOS_WORKER_PARTITION_SLOTS", "").strip()
    if raw_slots:
        slots = tuple(int(x) for x in raw_slots.split(",") if x.strip().isdigit())
    else:
        slots = tuple(range(16))  # default: cover every partition bucket
    return WorkerClientConfig(
        base_url=os.environ["RESEARCHOS_WORKER_GATEWAY_URL"],
        enrollment_secret=os.environ["RESEARCHOS_WORKER_ENROLLMENT_SECRET"],
        worker_id=worker_id,
        protocol_version=os.environ.get("RESEARCHOS_WORKER_PROTOCOL_VERSION", "1"),
        platform=os.environ.get("RESEARCHOS_WORKER_PLATFORM", "unknown/unknown"),
        capabilities=caps,
        backend_kinds=backends,
        partition_slots=slots,
        max_concurrency=int(os.environ.get("RESEARCHOS_WORKER_MAX_CONCURRENCY", "1")),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="services.worker")
    parser.add_argument("--worker-id", default=os.environ.get("RESEARCHOS_WORKER_ID", "worker-1"))
    parser.add_argument("--max-iterations", type=int, default=None)
    args = parser.parse_args(argv)

    _install_drain_handler()
    config = _build_config(args.worker_id)
    loop_config = WorkerLoopConfig(max_iterations=args.max_iterations)
    # Deterministic no-shell backend unless RESEARCHOS_WORKER_EXECUTION_BACKEND
    # explicitly selects the real Docker sandbox (E2E gate default = deterministic;
    # the real-Docker remote E2E is requires_docker-marked).
    execution_backend = os.environ.get("RESEARCHOS_WORKER_EXECUTION_BACKEND", "deterministic")
    if execution_backend == "docker":
        backend: object = DockerExecutionBackend()
    elif execution_backend == "deterministic":
        backend = DeterministicExecutionBackend()
    else:
        raise ValueError(f"unknown RESEARCHOS_WORKER_EXECUTION_BACKEND: {execution_backend}")
    print(f"worker: starting id={args.worker_id}", flush=True)  # noqa: T201
    with WorkerClient(config) as client:
        loop = WorkerLoop(client, backend, config=loop_config, should_stop=lambda: _STOP["flag"])  # type: ignore[arg-type]
        completed = loop.run()
    print(f"worker: stopped completed={completed}", flush=True)  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
