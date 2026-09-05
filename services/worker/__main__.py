"""Worker CLI entrypoint (M16): `python -m services.worker`.

Reads gateway connection + identity from the environment, installs a SIGTERM
drain handler, and runs the worker loop. Machine-readable stdout lines support
the cross-process E2E harness (WP4).

Execution backend selection (`RESEARCHOS_WORKER_EXECUTION_BACKEND`):
- `deterministic` (DEFAULT): a bounded no-shell test double that fabricates
  deterministic outputs — used by the offline distributed E2E gate ONLY. It
  must not be considered a real execution plane (see
  services/worker/deterministic_backend.py).
- `docker`: the real DockerExecutionBackend sandbox; production composition
  must set this explicitly.
"""

from __future__ import annotations

import argparse
import os
import signal
import sys
import time
from pathlib import Path

from adapters.execution.docker_backend import DockerExecutionBackend
from adapters.execution.gpu_probe import GPU_SANDBOX_IMAGE_DEFAULT, GpuProbeConfig, probe_gpu
from adapters.worker.client import WorkerClient, WorkerClientConfig
from services.worker.deterministic_backend import DeterministicExecutionBackend
from services.worker.loop import WorkerLoop, WorkerLoopConfig
from services.worker.reconnect import run_with_reconnect
from services.worker.telemetry import build_worker_telemetry

_STOP = {"flag": False}
_PROJECT_VERSION_PATH = Path(__file__).resolve().parents[2] / "VERSION"


def _project_version() -> str:
    version = _PROJECT_VERSION_PATH.read_text(encoding="utf-8").strip()
    if not version:
        raise RuntimeError("VERSION must not be empty")
    return version


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
        runtime_version=(
            os.environ.get("RESEARCHOS_WORKER_RUNTIME_VERSION", "").strip() or _project_version()
        ),
        platform=os.environ.get("RESEARCHOS_WORKER_PLATFORM", "unknown/unknown"),
        capabilities=caps,
        backend_kinds=backends,
        partition_slots=slots,
        max_concurrency=int(os.environ.get("RESEARCHOS_WORKER_MAX_CONCURRENCY", "1")),
    )


def _gpu_prober_for(backend_kind: str) -> object | None:
    """M17: the real Docker worker probes its GPU through the real image.

    The prober runs the pinned GPU sandbox image with DeviceRequests (the
    exact path a GPU job takes); a failed probe yields None and the worker
    registers CPU-only. The deterministic test backend never probes.
    """
    if backend_kind != "docker":
        return None
    image = os.environ.get("RESEARCHOS_WORKER_GPU_IMAGE", GPU_SANDBOX_IMAGE_DEFAULT)

    def _prober() -> object:
        return probe_gpu(GpuProbeConfig(image=image))

    return _prober


def _build_backend(execution_backend: str) -> object:
    if execution_backend == "docker":
        image = os.environ.get("RESEARCHOS_WORKER_DOCKER_IMAGE")
        return DockerExecutionBackend(image=image) if image else DockerExecutionBackend()
    if execution_backend == "deterministic":
        return DeterministicExecutionBackend()
    raise ValueError(f"unknown RESEARCHOS_WORKER_EXECUTION_BACKEND: {execution_backend}")


def _run_attempt(
    config: WorkerClientConfig,
    backend: object,
    loop_config: WorkerLoopConfig,
    telemetry: object,
    gpu_prober: object | None,
) -> int:
    with WorkerClient(config) as client:
        loop = WorkerLoop(
            client,
            backend,  # type: ignore[arg-type]  # concrete backend implements the Port
            config=loop_config,
            should_stop=lambda: _STOP["flag"],
            sleep=time.sleep,
            gpu_prober=gpu_prober,  # type: ignore[arg-type]
            telemetry=telemetry,  # type: ignore[arg-type]
        )
        return loop.run()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="services.worker")
    parser.add_argument("--worker-id", default=os.environ.get("RESEARCHOS_WORKER_ID", "worker-1"))
    parser.add_argument("--max-iterations", type=int, default=None)
    args = parser.parse_args(argv)

    _install_drain_handler()
    config = _build_config(args.worker_id)
    loop_config = WorkerLoopConfig(max_iterations=args.max_iterations)
    execution_backend = os.environ.get("RESEARCHOS_WORKER_EXECUTION_BACKEND", "deterministic")
    backend = _build_backend(execution_backend)
    telemetry = build_worker_telemetry(args.worker_id)
    gpu_prober = _gpu_prober_for(execution_backend)
    print(f"worker: starting id={args.worker_id}", flush=True)  # noqa: T201
    completed = run_with_reconnect(
        lambda: _run_attempt(config, backend, loop_config, telemetry, gpu_prober),
        should_stop=lambda: _STOP["flag"],
    )
    print(f"worker: stopped completed={completed}", flush=True)  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
