"""Worker CLI entrypoint (M16): `python -m services.worker`.

Reads gateway connection + identity from the environment, installs a SIGTERM
shutdown handler, and runs the worker loop. Machine-readable stdout lines
support the cross-process E2E harness (WP4).

Shutdown (`SIGTERM`): stop claiming, interrupt in-flight execution, exit
promptly. The in-flight attempt is NOT submitted — its lease is recovered by
the Control Plane (at-least-once), the same path a crashed worker takes. Both
the heartbeat sleep and the reconnect backoff are interruptible, so the process
never waits out a sleep window after a shutdown request.

EC-04: "promptly" also covers a worker blocked in a gateway **read**. The
handler only sets the flag, and PEP 475 resumes the interrupted syscall, so
without more the process waited out the client timeout (30s). The client now
gets `should_stop` and abandons an in-flight call once the drain grace period
(`RESEARCHOS_WORKER_DRAIN_SECONDS`, default 5s) expires — `WorkerDrainAbort`
propagates here and the process exits 0. See `adapters/worker/client.py::_call`.

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
import threading
from pathlib import Path

from adapters.execution.docker_backend import DockerExecutionBackend
from adapters.execution.gpu_probe import GPU_SANDBOX_IMAGE_DEFAULT, GpuProbeConfig, probe_gpu
from adapters.worker.client import WorkerClient, WorkerClientConfig, WorkerDrainAbort
from services.worker.deterministic_backend import DeterministicExecutionBackend
from services.worker.loop import WorkerLoop, WorkerLoopConfig
from services.worker.reconnect import run_with_reconnect
from services.worker.telemetry import build_worker_telemetry

_STOP = {"flag": False}
# Woken by the shutdown handler so no sleep window (heartbeat cadence, reconnect
# backoff) delays process exit after SIGTERM.
_WAKE = threading.Event()
_PROJECT_VERSION_PATH = Path(__file__).resolve().parents[2] / "VERSION"
_DRAIN_SECONDS_DEFAULT = 5.0
_DRAIN_SECONDS_MIN = 0.1
_DRAIN_SECONDS_MAX = 60.0


def _project_version() -> str:
    version = _PROJECT_VERSION_PATH.read_text(encoding="utf-8").strip()
    if not version:
        raise RuntimeError("VERSION must not be empty")
    return version


def _install_drain_handler() -> None:
    def _handler(_signum: int, _frame: object) -> None:
        _STOP["flag"] = True
        _WAKE.set()
        print("worker: drain requested", flush=True)  # noqa: T201

    signal.signal(signal.SIGTERM, _handler)


def _interruptible_sleep(seconds: float) -> None:
    """Sleep, but return as soon as a shutdown was requested."""
    _WAKE.wait(seconds)


def _drain_seconds() -> float:
    """停机后的在途调用宽限期（EC-04）；未设置 → 默认，非法 → 明确报错。"""
    raw = os.environ.get("RESEARCHOS_WORKER_DRAIN_SECONDS", "").strip()
    if not raw:
        return _DRAIN_SECONDS_DEFAULT
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"RESEARCHOS_WORKER_DRAIN_SECONDS must be a number: {raw!r}") from exc
    if not _DRAIN_SECONDS_MIN <= value <= _DRAIN_SECONDS_MAX:
        raise ValueError(
            "RESEARCHOS_WORKER_DRAIN_SECONDS must be within "
            f"[{_DRAIN_SECONDS_MIN}, {_DRAIN_SECONDS_MAX}]: {value}"
        )
    return value


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
        drain_seconds=_drain_seconds(),
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
    with WorkerClient(config, should_stop=lambda: _STOP["flag"]) as client:
        loop = WorkerLoop(
            client,
            backend,  # type: ignore[arg-type]  # concrete backend implements the Port
            config=loop_config,
            should_stop=lambda: _STOP["flag"],
            sleep=_interruptible_sleep,
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
    try:
        completed = run_with_reconnect(
            lambda: _run_attempt(config, backend, loop_config, telemetry, gpu_prober),
            should_stop=lambda: _STOP["flag"],
            sleep=_interruptible_sleep,
        )
    except WorkerDrainAbort as exc:
        # 停机宽限期内没回来的在途调用被放弃：这是有序停机，不是失败。
        print(f"worker: drain abort — {exc}", flush=True)  # noqa: T201
        completed = 0
    print(f"worker: stopped completed={completed}", flush=True)  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
