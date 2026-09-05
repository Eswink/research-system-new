"""Real CUDA cancellation, timeout, worker fencing, and restart observations."""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import docker
import httpx

import PA1R运行演练v1 as h

VERSION = os.environ.get("PA1R_CANDIDATE_VERSION", "v4")
h.EVIDENCE = h.ROOT / "scratch" / "PA1R闭环v1" / ("续审" + VERSION)
h.SOURCE = h.EVIDENCE / ("封存源码" + VERSION)
h.RESTORED = h.EVIDENCE / ("恢复源码" + VERSION)
h.PRIVATE = h.EVIDENCE / ("续审私有配置" + VERSION + ".json")
sys.path.insert(0, str(h.SOURCE))

from adapters.execution.remote_backend import RemoteExecutionBackend
from adapters.postgres.artifact_store import PostgresArtifactStore
from adapters.postgres.execution_job_queue import PostgresExecutionJobQueue
from packages.domain.workspace import ExecutionSpec

SCRIPT = '''import json, os, time
from pathlib import Path
import torch
assert torch.cuda.is_available()
x = torch.ones((512,512), device="cuda:0")
y = x @ x
torch.cuda.synchronize()
assert y.sum().item() == 512**3
print("PA1R_REAL_CUDA_CHECKSUM=" + str(int(y.sum().item())), flush=True)
start = time.monotonic()
while time.monotonic() - start < 180:
    y = x @ x
    torch.cuda.synchronize()
    time.sleep(0.02)
Path("gpu_runtime_facts.json").write_text(json.dumps({
    "cuda_available": True, "gpu_elapsed_seconds": time.monotonic()-start,
    "peak_gpu_memory_bytes": torch.cuda.max_memory_allocated(),
    "framework_version": torch.__version__, "cuda_runtime_version": torch.version.cuda,
    "gpu_device_name": torch.cuda.get_device_name(0)}), encoding="utf-8")
'''
MARKERS: set[str] = set()


def wait_for(check: Any, timeout: float = 45) -> Any:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = check()
        if value:
            return value
        time.sleep(0.4)
    raise RuntimeError("bounded fault observation did not converge")


def case_spec(name: str) -> ExecutionSpec:
    marker = "pa1rv2-" + name + "-" + uuid.uuid4().hex[:10]
    MARKERS.add(marker)
    workspace = h.SOURCE / "data/故障工作区" / marker
    workspace.mkdir(parents=True)
    (workspace / "cuda_job.py").write_text(SCRIPT.replace("< 180:", "< 90:") if name == "restart" else SCRIPT, encoding="utf-8")
    return ExecutionSpec(backend_kind="DOCKER", command="python cuda_job.py",
                         resource_profile="gpu-small", workspace_path=str(workspace),
                         environment={"PA1R_AUDIT_CASE": marker})


def owned_containers(client: Any, marker: str) -> list[Any]:
    return [c for c in client.containers.list(all=True, filters={"name": "research-os-exec"})
            if f"PA1R_AUDIT_CASE={marker}" in c.attrs["Config"].get("Env", [])]


def wait_real_cuda(client: Any, spec: ExecutionSpec) -> Any:
    marker = spec.environment["PA1R_AUDIT_CASE"]
    def ready() -> Any:
        for container in owned_containers(client, marker):
            if b"PA1R_REAL_CUDA_CHECKSUM=134217728" in container.logs():
                return container
        return None
    return wait_for(ready, 50)


def worker_generation(conn: Any, worker: str) -> int:
    row = conn.execute("SELECT registration_generation FROM workers WHERE worker_id=%s",
                       (worker,)).fetchone()
    return int(row[0]) if row else 0


def lease(conn: Any, task: str) -> Any:
    return conn.execute("SELECT lease_id,fence,worker_id FROM leases WHERE task_id=%s", (task,)).fetchone()


def restart_worker(config: dict[str, Any]) -> None:
    env = h.environment(config)
    child = {k: v for k, v in env.items() if k.upper() in h.OS_KEYS
             or k in ("PYTHONUTF8", "PYTHONIOENCODING")
             or k.startswith(("RESEARCHOS_WORKER_", "RESEARCHOS_OTEL_"))}
    h.start_process("源Worker", h.uv_python("-m", "services.worker", "--worker-id",
                    config["project"] + "-source"), h.SOURCE, child)


def gateway_outage(config: dict[str, Any], conn: Any) -> dict[str, Any]:
    worker = config["project"] + "-source"
    generation = worker_generation(conn, worker)
    pid = h.PROCESSES["源Worker"].pid
    h.stop_process("源Gateway")
    with httpx.Client(trust_env=False, timeout=1) as client:
        try:
            client.get("http://127.0.0.1:22881/openapi.json")
            raise AssertionError("gateway still listening after kill")
        except httpx.TransportError:
            pass
    time.sleep(12)
    assert h.PROCESSES["源Worker"].poll() is None
    h.start_process("源Gateway", h.uv_python("-m", "services.api.worker_gateway"),
                    h.SOURCE, h.environment(config))
    h.wait_http(22881)
    new_generation = wait_for(lambda: worker_generation(conn, worker)
                              if worker_generation(conn, worker) > generation else 0, 70)
    assert h.PROCESSES["源Worker"].pid == pid
    return {"worker_pid_unchanged": True, "generation_before": generation,
            "generation_after": new_generation, "gateway_listener_down_verified": True}


def gpu_faults(config: dict[str, Any], conn: Any, client: Any) -> dict[str, Any]:
    env = h.environment(config)
    artifacts = PostgresArtifactStore(dsn=env["RESEARCHOS_POSTGRES_DSN"],
                                     blob_dir=h.SOURCE / "data/artifacts-blobs")
    jobs = PostgresExecutionJobQueue(dsn=env["RESEARCHOS_POSTGRES_DSN"])
    backend = RemoteExecutionBackend.for_run(str(uuid.uuid4()), job_queue=jobs, artifacts=artifacts)
    results: dict[str, Any] = {}
    try:
        spec = case_spec("cancel")
        task = backend._submit(spec, Path(spec.workspace_path))
        container = wait_real_cuda(client, spec)
        jobs.request_cancel(task)
        outcome = wait_for(lambda: jobs.poll(task), 40)
        assert outcome.status == "CANCELLED" and lease(conn, task) is None
        wait_for(lambda: not owned_containers(client, spec.environment["PA1R_AUDIT_CASE"]))
        results["cancel"] = {"task": task, "real_cuda_checksum": 134217728,
                             "state": outcome.status, "lease_released": True, "container_removed": True}
        h.write_json("GPU故障阶段证据v2.json", results)

        spec = case_spec("timeout")
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(backend.execute, spec, 22)
            wait_real_cuda(client, spec)
            timed = future.result(timeout=45)
        task = timed.run_id.removeprefix("remote-")
        assert timed.status.value == "TIMED_OUT"
        settled = wait_for(lambda: jobs.poll(task), 40)
        assert settled.status == "CANCELLED" and lease(conn, task) is None
        wait_for(lambda: not owned_containers(client, spec.environment["PA1R_AUDIT_CASE"]))
        results["timeout"] = {"task": task, "real_cuda_checksum": 134217728,
                              "caller_state": timed.status.value, "queue_state": settled.status,
                              "lease_released": True, "container_removed": True}
        h.write_json("GPU故障阶段证据v2.json", results)

        spec = case_spec("restart")
        task = backend._submit(spec, Path(spec.workspace_path))
        old = wait_real_cuda(client, spec)
        kill_started = time.monotonic()
        identity = lease(conn, task)
        assert identity is not None
        before = conn.execute("SELECT run_id,run_json FROM runs ORDER BY run_id").fetchall()
        h.stop_process("源Worker")
        h.stop_process("源API")
        old.reload()
        old_running_after_kill = old.status == "running"
        h.start_process("源API", ["uv", "run", "--frozen", "--no-sync", "uvicorn", "--factory",
                          "services.api.app:create_app", "--host", "127.0.0.1", "--port", "22800"],
                          h.SOURCE, env)
        h.wait_http(22800)
        restart_worker(config)
        def old_removed() -> bool:
            try:
                old.reload()
                return False
            except docker.errors.NotFound:
                return True
        wait_for(old_removed, 35)
        removal_seconds = time.monotonic() - kill_started
        assert removal_seconds < 60, "natural 90-second job exit is not cleanup evidence"
        new_identity = wait_for(lambda: current if (current := lease(conn, task))
                                 and current[1] > identity[1] else None, 105)
        try:
            old.reload()
            orphan = old.status == "running"
        except docker.errors.NotFound:
            orphan = False
        after = conn.execute("SELECT run_id,run_json FROM runs ORDER BY run_id").fetchall()
        assert before == after
        assert not orphan, "superseded GPU container remains running"
        settled = wait_for(lambda: jobs.poll(task), 130)
        assert settled.status == "SUCCEEDED"
        assert lease(conn, task) is None
        wait_for(lambda: not owned_containers(client, spec.environment["PA1R_AUDIT_CASE"]))
        results["restart"] = {"task": task, "fence_before": identity[1], "fence_after": new_identity[1],
                              "run_state_preserved_across_api_restart": before == after,
                              "old_gpu_container_running_after_worker_kill": old_running_after_kill,
                              "old_gpu_container_running_after_takeover": orphan,
                              "cleanup_verdict": "FAIL" if orphan else "PASS",
                              "new_attempt_settled_state": settled.status,
                              "operator_cleanup_required": orphan}
        results["restart"]["old_container_removed_seconds_after_kill"] = removal_seconds
        results["restart"]["original_job_minimum_duration_seconds"] = 90
        h.write_json("GPU故障阶段证据v2.json", results)
        spec = case_spec("large-vram")
        script = Path(str(spec.workspace_path)) / "cuda_job.py"
        allocation = "allocation = torch.empty((3 * 1024**3,), dtype=torch.uint8, device='cuda:0'); allocation.zero_()\nx = torch.ones"
        code = SCRIPT.replace("x = torch.ones", allocation).replace("< 180:", "< 1.7:")
        script.write_text(code, encoding="utf-8")
        task = backend._submit(spec, Path(str(spec.workspace_path)))
        settled = wait_for(lambda: jobs.poll(task), 70)
        assert settled.status == "SUCCEEDED" and settled.peak_gpu_memory_bytes > 2**31
        assert settled.gpu_elapsed_seconds is not None
        assert settled.gpu_elapsed_seconds != int(settled.gpu_elapsed_seconds)
        assert lease(conn, task) is None
        wait_for(lambda: not owned_containers(client, spec.environment["PA1R_AUDIT_CASE"]))
        results["large_vram"] = {"task": task, "state": settled.status, "peak_bytes": settled.peak_gpu_memory_bytes, "gpu_seconds": str(settled.gpu_elapsed_seconds), "cleanup": True}
        h.write_json("GPU故障阶段证据v2.json", results)
    finally:
        backend.close()
        jobs.close()
        artifacts.close()
    return results


def main() -> None:
    config = json.loads(h.PRIVATE.read_text(encoding="utf-8"))
    project = config["project"]
    client = docker.from_env()
    results: dict[str, Any] = {}
    try:
        for name in (project + "-postgres-1", project + "-otel-collector-1"):
            client.containers.get(name).start()
        h.start_services(config)
        with h.conn_for(config) as conn:
            results["gateway"] = gateway_outage(config, conn)
            print("Gateway outage/reconnect: observed", flush=True)
            h.write_json("故障续验证据v2.json", results)
            results["gpu"] = gpu_faults(config, conn, client)
    finally:
        for marker in MARKERS:
            for container in owned_containers(client, marker):
                container.remove(force=True)
        results["audit_owned_container_cleanup_finished"] = True
        for key in list(h.PROCESSES):
            h.stop_process(key)
        for handle in h.LOG_HANDLES:
            handle.close()
        for name in (project + "-postgres-1", project + "-otel-collector-1"):
            client.containers.get(name).stop(timeout=3)
        client.close()
        h.write_json("故障续验证据v2.json", results)
    assert results.get("gpu", {}).get("restart", {}).get("cleanup_verdict") == "PASS"
    assert results["gpu"]["large_vram"]["cleanup"]
    print(json.dumps(results, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
