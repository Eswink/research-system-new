"""WorkerHarness: real cross-process distributed topology (M16 WP4).

Starts the worker gateway (uvicorn) on an ephemeral loopback port backed by
real PostgreSQL adapters, and spawns genuine `python -m services.worker`
subprocesses. Core evidence comes from separate OS processes, not one Python
object graph (M16 plan §16, in the shape of tests/postgres/worker_cross_process.py).
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from types import TracebackType
from typing import Any

import uvicorn

from adapters.postgres.artifact_store import PostgresArtifactStore
from adapters.postgres.execution_job_queue import PostgresExecutionJobQueue
from adapters.postgres.worker_registry import PostgresWorkerRegistry
from adapters.postgres.workflow_engine import PostgresWorkflowEngine
from adapters.relay.registry_credential_resolver import RegistryCredentialResolver
from packages.application.ports.execution_job_queue import ExecutionJobRequest
from packages.domain.workspace import ExecutionSpec
from services.api.worker_gateway.app import create_worker_app
from services.api.worker_gateway.deps import WorkerGatewayDeps
from services.api.worker_gateway.settings import WorkerGatewaySettings

_ENROLLMENT = "distributed-e2e-enrollment"

# M16 re-audit F-2: the worker process must hold ZERO database credentials.
# These keys are stripped from the inherited environment so the cross-process
# E2E is genuine boundary evidence (the worker code never reads them anyway).
_DB_CREDENTIAL_KEYS = ("RESEARCHOS_POSTGRES_DSN", "DATABASE_URL")


def worker_child_env(
    gateway_url: str,
    worker_id: str,
    *,
    base_env: dict[str, str] | None = None,
    env_extra: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build the worker subprocess environment: gateway identity only, no DB."""
    env = dict(base_env if base_env is not None else os.environ)
    for key in _DB_CREDENTIAL_KEYS:
        env.pop(key, None)
    env.update({
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
        "RESEARCHOS_WORKER_GATEWAY_URL": gateway_url,
        "RESEARCHOS_WORKER_ENROLLMENT_SECRET": _ENROLLMENT,
        "RESEARCHOS_WORKER_ID": worker_id,
    })
    if env_extra:
        env.update(env_extra)
    return env


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class WorkerHarness:
    """Gateway server + subprocess worker fleet over real PostgreSQL."""

    def __init__(self, dsn: str, *, lease_ttl_seconds: int = 2, stale_seconds: float = 3.0) -> None:
        self.dsn = dsn
        creds = RegistryCredentialResolver()
        creds.register("WORKER_ENROLLMENT_SECRET", _ENROLLMENT)
        blob_dir = Path(tempfile.mkdtemp(prefix="m16-harness-blobs-"))
        # Gateway-side adapters: used ONLY from the uvicorn event-loop thread.
        self.gw_registry = PostgresWorkerRegistry(dsn=dsn)
        self.gw_workflow = PostgresWorkflowEngine(dsn=dsn, lease_ttl_seconds=lease_ttl_seconds)
        self.gw_job_queue = PostgresExecutionJobQueue(dsn=dsn)
        self.gw_artifacts = PostgresArtifactStore(dsn=dsn, blob_dir=blob_dir)
        # Test-side adapters: separate connections for the test thread, mirroring
        # how a real scheduler process owns its own connections.
        self.registry = PostgresWorkerRegistry(dsn=dsn)
        self.workflow = PostgresWorkflowEngine(dsn=dsn, lease_ttl_seconds=lease_ttl_seconds)
        self.job_queue = PostgresExecutionJobQueue(dsn=dsn)
        self.settings = WorkerGatewaySettings(
            enrollment_credential_ref="WORKER_ENROLLMENT_SECRET",
            heartbeat_interval_seconds=1.0,
            stale_threshold_seconds=stale_seconds,
        )
        self.app = create_worker_app(
            WorkerGatewayDeps(
                registry=self.gw_registry,
                credentials=creds,
                settings=self.settings,
                workflow=self.gw_workflow,
                job_queue=self.gw_job_queue,
                artifacts=self.gw_artifacts,
            )
        )
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None
        self._lease_sched: Any | None = None
        self._reaper_sched: Any | None = None
        self._sched_workflow: PostgresWorkflowEngine | None = None
        self._sched_registry: PostgresWorkerRegistry | None = None
        self._lease_ttl = lease_ttl_seconds
        self.workers: list[subprocess.Popen[bytes]] = []
        self.port = _free_port()

    @property
    def gateway_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def start_gateway(self) -> None:
        import logging

        logging.basicConfig(level=logging.WARNING)
        config = uvicorn.Config(
            self.app, host="127.0.0.1", port=self.port, log_level="warning", lifespan="off"
        )
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, name="worker-gateway", daemon=True)
        self._thread.start()
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if self._server.started:
                return
            time.sleep(0.05)
        raise RuntimeError("worker gateway did not start")

    def start_schedulers(
        self, *, lease_interval: float = 0.5, reaper_interval: float = 0.5
    ) -> None:
        """Run the Control Plane self-healing loops (lease recovery + worker reaper).

        In production these daemon threads live in the API process (M14/M16);
        the harness hosts them the same way so failover scenarios converge fast.
        """
        from services.api.scheduler import LeaseRecoveryScheduler, WorkerReaperScheduler

        # dedicated connections for the scheduler threads (mirrors a real
        # scheduler process owning its own adapters)
        self._sched_workflow = PostgresWorkflowEngine(
            dsn=self.dsn, lease_ttl_seconds=self._lease_ttl
        )
        self._sched_registry = PostgresWorkerRegistry(dsn=self.dsn)
        self._lease_sched = LeaseRecoveryScheduler(
            self._sched_workflow, interval_seconds=lease_interval
        )
        self._reaper_sched = WorkerReaperScheduler(
            self._sched_registry,
            stale_threshold_seconds=self.settings.stale_threshold_seconds,
            interval_seconds=reaper_interval,
        )
        self._lease_sched.start()
        self._reaper_sched.start()

    def stop_schedulers(self) -> None:
        if self._lease_sched is not None:
            self._lease_sched.stop()
        if self._reaper_sched is not None:
            self._reaper_sched.stop()
        self._lease_sched = None
        self._reaper_sched = None
        if self._sched_workflow is not None:
            self._sched_workflow.close()
        if self._sched_registry is not None:
            self._sched_registry.close()
        self._sched_workflow = None
        self._sched_registry = None

    def spawn_worker(
        self, worker_id: str, *, env_extra: dict[str, str] | None = None
    ) -> subprocess.Popen[bytes]:
        env = worker_child_env(self.gateway_url, worker_id, env_extra=env_extra)
        proc = subprocess.Popen(
            [sys.executable, "-B", "-m", "services.worker", "--worker-id", worker_id],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=str(Path(__file__).resolve().parents[2]),
        )
        self.workers.append(proc)
        return proc

    def seed_job(self, *, command: str = "echo hi", idem: str, partition: int | None = 0) -> str:
        """Enqueue one EXECUTION job on the canonical queue; return task_id."""
        from uuid import uuid4

        return self.job_queue.enqueue(
            ExecutionJobRequest(
                spec=ExecutionSpec(backend_kind="DOCKER", command=command),
                run_id=str(uuid4()),
                capability="docker",
                idempotency_key=idem,
                partition=partition,
            )
        )

    def stop_workers(self) -> None:
        for proc in self.workers:
            if proc.poll() is None:
                proc.terminate()
        for proc in self.workers:
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        self.workers.clear()

    def stop_gateway(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=10)
        self._server = None
        self._thread = None

    def close(self) -> None:
        self.stop_workers()
        self.stop_schedulers()
        self.stop_gateway()
        self.registry.close()
        self.workflow.close()
        self.job_queue.close()
        self.gw_registry.close()
        self.gw_workflow.close()
        self.gw_job_queue.close()
        self.gw_artifacts.close()

    def __enter__(self) -> "WorkerHarness":
        self.start_gateway()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
