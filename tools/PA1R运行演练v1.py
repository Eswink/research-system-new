"""PA-1R sealed-source reconstruction and real restore/research drill.

Credentials are generated locally, kept in ignored private configuration, and
never printed. Services are owned subprocess trees; teardown retains DB volumes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import docker
import httpx
import psycopg

from PA1R恢复闭包v1 import check_run, table_counts

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "scratch" / "PA1R闭环v1"
SOURCE = EVIDENCE / "封存源码v2"
RESTORED = EVIDENCE / "恢复源码v2"
PRIVATE = EVIDENCE / "续审私有配置v2.json"
MANIFEST = EVIDENCE / "源码清单v2.json"
OS_KEYS = {"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "HOME", "USERPROFILE",
           "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA", "TEMP", "TMP", "TMPDIR",
           "DOCKER_HOST", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH", "DOCKER_CONTEXT",
           "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "PROGRAMDATA"}
REVISION: str | None = None
PROCESSES: dict[str, subprocess.Popen[bytes]] = {}
LOG_HANDLES: list[Any] = []


def write_json(name: str, payload: Any) -> None:
    (EVIDENCE / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                               encoding="utf-8")


def os_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key.upper() in OS_KEYS}
    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", UV_LINK_MODE="copy")
    return env


def run(args: list[str], cwd: Path, name: str, env: dict[str, str] | None = None,
        timeout: int = 300) -> bytes:
    result = subprocess.run(args, cwd=cwd, env=env or os_env(), capture_output=True,
                            timeout=timeout, check=False, shell=False)
    (EVIDENCE / f"{name}.log").write_bytes(result.stdout + result.stderr)
    print(f"{name}: exit={result.returncode}", flush=True)
    if result.returncode != 0:
        raise RuntimeError(f"{name} failed; inspect its redacted audit log")
    return result.stdout


def uv_python(*args: str) -> list[str]:
    return ["uv", "run", "--frozen", "--no-sync", "python", "-B", *args]


def prepare() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    if SOURCE.exists() or RESTORED.exists() or PRIVATE.exists():
        raise RuntimeError("v2 target already exists; do not overwrite evidence")
    if REVISION:
        for target in (SOURCE, RESTORED):
            run(["git", "clone", "--no-hardlinks", "--no-checkout", str(ROOT), str(target)], ROOT, target.name+"克隆")
            run(["git", "checkout", "--detach", REVISION], target, target.name+"检出")
            assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=target).decode().strip() == REVISION
    raw = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=SOURCE if REVISION else ROOT)
    paths = sorted(set(raw.decode("utf-8").strip("\0").split("\0")))
    paths = [s for s in paths if not s.startswith(("scratch/", "data/", "docs/history-session/"))]
    files = []
    for name in paths:
        src = (SOURCE if REVISION else ROOT) / name
        if src.is_symlink() or not src.is_file():
            raise RuntimeError(f"unsupported source member: {name}")
        data = src.read_bytes()
        files.append({"path": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
        for target in (SOURCE, RESTORED):
            dst = target / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not REVISION:
                dst.write_bytes(data)
            else:
                assert dst.read_bytes() == data
    payload = {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
               "kind": "IMMUTABLE_GIT_REVISION" if REVISION else "UNRELEASED_WORKTREE_SNAPSHOT", "revision": REVISION, "files": files}
    write_json(MANIFEST.name, payload)
    for i, target in enumerate((SOURCE, RESTORED), 1):
        run(["uv", "lock", "--check"], target, f"冻结锁校验v2_{i}")
        run(["uv", "sync", "--frozen", "--dev"], target, f"冻结Python安装v2_{i}")
    run(["cmd", "/c", "pnpm install --frozen-lockfile"], SOURCE, "冻结前端安装v2")
    finish_prepare()


def finish_prepare() -> None:
    if PRIVATE.exists():
        raise RuntimeError("private runtime already created; refuse overwrite")
    files = json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]
    for target in (SOURCE, RESTORED):
        for item in files:
            assert hashlib.sha256((target / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    for i in (1, 2):
        run(["docker", "buildx", "build", "--load", "--no-cache", "--provenance=false",
             "--platform", "linux/amd64", "--build-arg", "SOURCE_DATE_EPOCH=0", "-f",
             "adapters/execution/sandbox/Dockerfile.gpu", "-t",
             f"research-os-gpu-sandbox:pa1r-v2-{i}", "."], SOURCE, f"GPU镜像复建v2_{i}")
    client = docker.from_env()
    ids = [client.api.inspect_image(f"research-os-gpu-sandbox:pa1r-v2-{i}")["Id"] for i in (1, 2)]
    client.close()
    assert ids[0] == ids[1]
    write_json("镜像重建证据v2.json", {"image_ids": ids, "equal": True})
    config = {"project": "pa1rv2-" + uuid.uuid4().hex[:8],
              "source_password": secrets.token_urlsafe(32),
              "restore_password": secrets.token_urlsafe(32),
              "enrollment": secrets.token_urlsafe(32), "llm_canary": secrets.token_urlsafe(32),
              "image_id": ids[0], "source_runs": [], "restored_runs": []}
    write_json(PRIVATE.name, config)
    print(f"sealed_files={len(files)}; no inherited .env/data/venv; private values withheld", flush=True)


def environment(config: dict[str, Any], restored: bool = False) -> dict[str, str]:
    env = os_env()
    for line in (SOURCE / ".env.example").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    root, port = (RESTORED, 22433) if restored else (SOURCE, 22432)
    password = config["restore_password" if restored else "source_password"]
    dsn = f"postgresql://research_os:{password}@127.0.0.1:{port}/research_os"
    env.update(RESEARCHOS_POSTGRES_PASSWORD=password, RESEARCHOS_POSTGRES_HOST_PORT=str(port),
               RESEARCHOS_DATABASE_URL=dsn, RESEARCHOS_POSTGRES_DSN=dsn,
               WORKER_ENROLLMENT_SECRET=config["enrollment"],
               RESEARCHOS_WORKER_ENROLLMENT_SECRET=config["enrollment"],
               LLM_MAIN_KEY=config["llm_canary"], RESEARCHOS_OTEL_ENABLED="true",
               RESEARCHOS_OTEL_HOST_PORT="22418", RESEARCHOS_OTEL_ENDPOINT="http://127.0.0.1:22418",
               RESEARCHOS_ARTIFACT_BLOB_DIR=str(root / "data/artifacts-blobs"),
               RESEARCHOS_WORKER_GATEWAY_PORT="22891" if restored else "22881",
               RESEARCHOS_WORKER_GATEWAY_URL="http://127.0.0.1:" + ("22891" if restored else "22881"))
    env.pop("RESEARCHOS_WORKER_ARTIFACT_BLOB_DIR", None)
    return env


def conn_for(config: dict[str, Any], restored: bool = False) -> psycopg.Connection[Any]:
    return psycopg.connect(host="127.0.0.1", port=22433 if restored else 22432,
                          dbname="research_os", user="research_os",
                          password=config["restore_password" if restored else "source_password"],
                          autocommit=True, connect_timeout=3)


def start_process(name: str, args: list[str], cwd: Path, env: dict[str, str]) -> None:
    log = (EVIDENCE / f"{name}进程v2.log").open("ab")
    LOG_HANDLES.append(log)
    PROCESSES[name] = subprocess.Popen(args, cwd=cwd, env=env, stdout=log,
                                       stderr=subprocess.STDOUT, shell=False)


def stop_process(name: str) -> None:
    process = PROCESSES.pop(name, None)
    if process is not None and process.poll() is None:
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        process.wait(timeout=15)


def wait_http(port: int) -> None:
    deadline = time.monotonic() + 45
    with httpx.Client(trust_env=False, timeout=1) as client:
        while time.monotonic() < deadline:
            try:
                if client.get(f"http://127.0.0.1:{port}/openapi.json").status_code == 200:
                    return
            except httpx.TransportError:
                pass
            time.sleep(0.5)
    raise RuntimeError(f"service {port} failed to start")


def start_services(config: dict[str, Any], restored: bool = False) -> None:
    prefix = "恢复" if restored else "源"
    root = RESTORED if restored else SOURCE
    env = environment(config, restored)
    api_port, gateway_port = (22810, 22891) if restored else (22800, 22881)
    start_process(prefix + "API", ["uv", "run", "--frozen", "--no-sync", "uvicorn", "--factory",
                                  "services.api.app:create_app", "--host", "127.0.0.1",
                                  "--port", str(api_port)], root, env)
    wait_http(api_port)
    start_process(prefix + "Gateway", uv_python("-m", "services.api.worker_gateway"), root, env)
    wait_http(gateway_port)
    worker_env = {key: value for key, value in env.items() if key.upper() in OS_KEYS
                  or key in ("PYTHONUTF8", "PYTHONIOENCODING")
                  or key.startswith(("RESEARCHOS_WORKER_", "RESEARCHOS_OTEL_"))}
    worker_id = config["project"] + ("-restore" if restored else "-source")
    start_process(prefix + "Worker", uv_python("-m", "services.worker", "--worker-id", worker_id),
                  root, worker_env)
    deadline = time.monotonic() + 120
    with conn_for(config, restored) as conn:
        while time.monotonic() < deadline:
            row = conn.execute("SELECT state,gpu_observation_json FROM workers WHERE worker_id=%s",
                               (worker_id,)).fetchone()
            if row and row[0] == "READY" and row[1]:
                write_json(prefix + "Worker身份v2.json", {"worker_id": worker_id, "gpu": row[1]})
                print(prefix + "Worker: READY with real GPU probe", flush=True)
                return
            time.sleep(1)
    raise RuntimeError("real GPU worker did not become ready")


def research_run(config: dict[str, Any], name: str, restored: bool = False,
                 resume_id: str | None = None) -> dict[str, Any]:
    root = RESTORED if restored else SOURCE
    run_id = resume_id or str(uuid.uuid4())
    observations = set()
    with ThreadPoolExecutor(max_workers=1) as pool:
        work = pool.submit(run, uv_python("tools/personal_reference_workflow.py", "--run-id",
                           run_id, "--timeout", "240"), root, name,
                           environment(config, restored), 280)
        with conn_for(config, restored) as conn:
            while not work.done():
                rows = conn.execute(
                    "SELECT t.task_id,t.status,r.run_id IS NOT NULL FROM tasks t "
                    "LEFT JOIN runs r ON r.run_id=t.run_id WHERE t.run_id=%s", (run_id,)
                ).fetchall()
                observations.update(rows)
                time.sleep(0.1)
        stdout = work.result()
    write_json(name + "运行中状态.json", {"run_id": run_id, "observations": sorted(observations),
                "missing_canonical_run_observed": any(not row[2] for row in observations)})
    assert observations and all(row[2] for row in observations), "Task appeared before canonical Run"
    payload = json.loads(stdout)
    assert payload["budget_entries"] == 3
    with conn_for(config, restored) as conn:
        closure = check_run(conn, root / "data/artifacts-blobs", run_id)
    write_json(name + ".json", {"cli": payload, "closure": closure})
    export_root = root / "data" / "exports"
    export_root.mkdir(parents=True, exist_ok=True)
    with httpx.Client(trust_env=False, timeout=15) as api:
        for suffix in ("export", "usage", "cost", "telemetry"):
            response = api.get(f"http://127.0.0.1:{22810 if restored else 22800}/runs/{run_id}/{suffix}")
            response.raise_for_status()
            (export_root / f"{run_id}_{suffix}.json").write_bytes(response.content)
        response = api.get(f"http://127.0.0.1:{22810 if restored else 22800}/evaluations/trend?dataset_id=m17_gpu_v1")
        response.raise_for_status()
        (export_root / "评测趋势v1.json").write_bytes(response.content)
    config["restored_runs" if restored else "source_runs"].append(run_id)
    write_json(PRIVATE.name, config)
    print(name + ": canonical closure verified", flush=True)
    return closure


def interrupt_research(config: dict[str, Any]) -> None:
    run_id = str(uuid.uuid4())
    start_process("中断研究", uv_python("tools/personal_reference_workflow.py", "--run-id", run_id,
                                       "--timeout", "240"), SOURCE, environment(config))
    deadline = time.monotonic() + 70
    with conn_for(config) as conn:
        while time.monotonic() < deadline:
            row = conn.execute("SELECT t.task_id,t.status,r.run_json->>'state',"
                               "r.run_json->>'manifest_digest' FROM tasks t JOIN runs r "
                               "ON r.run_id=t.run_id WHERE t.run_id=%s", (run_id,)).fetchone()
            if row and row[1] == "LEASED":
                assert row[2] == "RUNNING" and row[3]
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("no admitted leased task observed before orchestrator kill")
        stop_process("中断研究")
        deadline = time.monotonic() + 80
        while time.monotonic() < deadline:
            state = conn.execute("SELECT status FROM tasks WHERE task_id=%s", (row[0],)).fetchone()
            if state and state[0] == "SUCCEEDED":
                break
            time.sleep(0.3)
        else:
            raise RuntimeError("worker did not complete detached experiment")
        parent = conn.execute("SELECT run_json->>'state' FROM runs WHERE run_id=%s", (run_id,)).fetchone()
        assert parent[0] == "RUNNING"
    config["interrupted_run"] = {"run_id": run_id, "task_id": row[0], "manifest_digest": row[3]}
    write_json(PRIVATE.name, config)
    write_json("中断恢复前证据v4.json", config["interrupted_run"])
    print("orchestrator killed mid-job; worker completed; canonical Run remains RUNNING", flush=True)


def clean_restore(config: dict[str, Any], client: Any) -> dict[str, Any]:
    project = config["project"]
    source_container = project + "-postgres-1"
    backup_dir = SOURCE / "data/backups"
    run(uv_python("tools/backup.py", "--container", source_container, "--blob-root",
                  "data/artifacts-blobs", "--out", "data/backups", "--keep", "7", "--verify",
                  "--sample", "100"), SOURCE, "实际备份v2", environment(config))
    manifest_path = next(backup_dir.glob("manifest-*.json"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dump, archive = backup_dir / manifest["dump"], backup_dir / manifest["artifacts"]
    name, volume = project + "-restore-postgres", project + "-restore-pgdata"
    client.volumes.create(name=volume, labels={"pa1r.audit": project})
    client.containers.run("postgres:16-alpine", name=name, detach=True,
                          environment={"POSTGRES_DB": "research_os", "POSTGRES_USER": "research_os",
                                       "POSTGRES_PASSWORD": config["restore_password"]},
                          ports={"5432/tcp": ("127.0.0.1", 22433)},
                          volumes={volume: {"bind": "/var/lib/postgresql/data", "mode": "rw"}},
                          labels={"pa1r.audit": project})
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        try:
            with conn_for(config, True) as conn:
                before = table_counts(conn)
            break
        except psycopg.OperationalError:
            time.sleep(1)
    else:
        raise RuntimeError("clean restore DB failed to start")
    assert before == {}, "restore target must have no public tables"
    run(uv_python("tools/restore.py", "--container", name, "--dump", str(dump),
                  "--artifact-archive", str(archive), "--blob-target", "data/artifacts-blobs"),
        RESTORED, "实际恢复v2", environment(config, True))
    with conn_for(config) as source_conn, conn_for(config, True) as target_conn:
        source_counts, target_counts = table_counts(source_conn), table_counts(target_conn)
        assert source_counts == target_counts
        from psycopg import sql
        table_hashes = {}
        for table in source_counts:
            query = sql.SQL("SELECT row_to_json(t) FROM {} t").format(sql.Identifier(table))
            def table_digest(connection):
                rows = [json.dumps(row[0], sort_keys=True, default=str) for row in connection.execute(query)]
                return hashlib.sha256("\n".join(sorted(rows)).encode()).hexdigest()
            left, right = table_digest(source_conn), table_digest(target_conn)
            assert left == right, f"restore row mismatch: {table}"
            table_hashes[table] = left
        closures = [check_run(target_conn, RESTORED / "data/artifacts-blobs", rid)
                    for rid in config["source_runs"]]
    result = {"empty_target_before": before, "table_counts": target_counts, "table_hashes": table_hashes, "closures": closures,
              "dump": str(dump.relative_to(ROOT)), "archive": str(archive.relative_to(ROOT)),
              "dump_sha256": hashlib.sha256(dump.read_bytes()).hexdigest(),
              "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}
    write_json("实际恢复闭包v2.json", result)
    return result


def drill() -> None:
    config = json.loads(PRIVATE.read_text(encoding="utf-8"))
    for port in (22432, 22433, 22418, 22800, 22810, 22881, 22891):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", port))
    project = config["project"]
    client = docker.from_env()
    try:
        run(["docker", "compose", "-p", project, "-f", "docker-compose.personal.yml", "up", "-d",
             "--build", "--wait", "--wait-timeout", "60"], SOURCE, "正式部署v2", environment(config))
        start_services(config)
        research_run(config, "干净研究运行v2")
        collector = client.containers.get(project + "-otel-collector-1")
        collector.stop(timeout=3)
        collector.reload()
        assert collector.status == "exited"
        research_run(config, "Collector停机研究运行v2")
        collector.start()
        interrupt_research(config)
        # Quiesce writers for the paired backup; preserve every owned volume.
        for key in ("源Worker", "源Gateway", "源API"):
            stop_process(key)
        clean_restore(config, client)
        start_services(config, True)
        pending = config["interrupted_run"]
        closure = research_run(config, "中断后跨恢复重放v4", True, pending["run_id"])
        assert closure["manifest_digest"] == pending["manifest_digest"]
        assert closure["tasks"][0][0] == pending["task_id"]
        research_run(config, "恢复后研究运行v2", True)
        write_json("重建恢复演练结果v2.json", {"result": "PASS_FOR_RESTORE_AND_INTERRUPTED_REPLAY",
                   "source_runs": config["source_runs"], "restored_runs": config["restored_runs"],
                   "interrupted_replay": closure,
                   "note": "Not a release or complete PA-1R verdict"})
    finally:
        for key in list(PROCESSES):
            stop_process(key)
        for log in LOG_HANDLES:
            log.close()
        for name in (project + "-postgres-1", project + "-otel-collector-1", project + "-restore-postgres"):
            try:
                client.containers.get(name).stop(timeout=3)
            except docker.errors.NotFound:
                pass
        client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "finish-prepare", "drill"])
    parser.add_argument("--candidate-version", default="v4")
    parser.add_argument("--revision", default=None, help="Exact local Git commit to clone and verify")
    args = parser.parse_args()
    REVISION = args.revision
    if args.candidate_version != "v2":
        EVIDENCE = EVIDENCE / ("续审" + args.candidate_version)
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        SOURCE = EVIDENCE / ("封存源码" + args.candidate_version)
        RESTORED = EVIDENCE / ("恢复源码" + args.candidate_version)
        PRIVATE = EVIDENCE / ("续审私有配置" + args.candidate_version + ".json")
        MANIFEST = EVIDENCE / ("源码清单" + args.candidate_version + ".json")
    {"prepare": prepare, "finish-prepare": finish_prepare, "drill": drill}[args.mode]()
