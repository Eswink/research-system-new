"""Assemble a local Personal Production Release Record from verified evidence.

Never promotes a dirty source tree or a partial gate result. The record refers
to the immutable code commit, not the later documentation-only evidence commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import docker
import psycopg
import yaml


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root).decode("utf-8").strip()


def database_truth(config: dict[str, Any]) -> dict[str, Any]:
    client = docker.from_env()
    container = client.containers.get(config["project"] + "-restore-postgres")
    was_running = container.status == "running"
    if not was_running:
        container.start()
    try:
        for _ in range(30):
            if container.exec_run(["pg_isready", "-U", "research_os"]).exit_code == 0:
                break
            time.sleep(1)
        with psycopg.connect(host="127.0.0.1", port=22433, dbname="research_os", user="research_os",
                            password=config["restore_password"], autocommit=True) as conn:
            versions = [r[0] for r in conn.execute("SELECT version FROM migration_version ORDER BY version")]
            columns = conn.execute("SELECT table_name,column_name,data_type FROM information_schema.columns WHERE table_schema='public' ORDER BY 1,2").fetchall()
            workers = conn.execute("SELECT worker_id,protocol_version,runtime_version FROM workers ORDER BY worker_id").fetchall()
            runtime = conn.execute("SHOW server_version").fetchone()[0]
            leases = conn.execute("SELECT count(*) FROM leases").fetchone()[0]
        assert versions == list(range(1, 13)) and leases == 0
        assert workers and all(w[1:] == ("1", "0.4.0") for w in workers)
        return {"runtime": runtime, "migrations": versions, "public_tables": len({r[0] for r in columns}),
                "schema_sha256": hashlib.sha256(json.dumps(columns, sort_keys=True).encode()).hexdigest(),
                "worker_protocol": "1", "worker_runtime": "0.4.0", "workers_checked": len(workers),
                "active_leases": leases}
    finally:
        if not was_running:
            container.stop(timeout=3)
        client.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-version", default="release-v1")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    evidence = root / "scratch" / "PA1R闭环v1"
    run_evidence = evidence / ("续审" + args.candidate_version)
    source = run_evidence / ("封存源码" + args.candidate_version)
    restored = run_evidence / ("恢复源码" + args.candidate_version)
    revision = git(source, "rev-parse", "HEAD")
    assert revision == git(restored, "rev-parse", "HEAD")
    assert not git(source, "status", "--porcelain") and not git(restored, "status", "--porcelain")
    rebuild = read_json(run_evidence / "重建恢复演练结果v2.json")
    faults = read_json(run_evidence / "故障续验证据v2.json")
    hygiene = read_json(run_evidence / "密钥六面审计v1.json")
    quality = read_json(evidence / "质量门禁_m0v1.json")
    assert rebuild["result"] == "PASS_FOR_RESTORE_AND_INTERRUPTED_REPLAY"
    restart = faults["gpu"]["restart"]
    assert restart["cleanup_verdict"] == "PASS" and not restart["operator_cleanup_required"]
    assert restart["new_attempt_settled_state"] == "SUCCEEDED"
    assert restart["old_container_removed_seconds_after_kill"] < 60
    assert faults["gpu"]["large_vram"]["peak_bytes"] > 2**31
    assert hygiene["verdict"] == "PASS" and quality["passed"]
    assert Path(quality["source"]).resolve() == source.resolve()
    config = read_json(run_evidence / ("续审私有配置" + args.candidate_version + ".json"))
    registry = yaml.safe_load((source / "UPSTREAM_COMPONENTS.yaml").read_text(encoding="utf-8"))
    gpu = next(c for c in registry["components"] if c["id"] == "research_os_gpu_base_image")
    assert gpu["resolution"]["application_image_digest"] == config["image_id"]
    lock = tomllib.loads((source / "uv.lock").read_text(encoding="utf-8"))
    package_names = ["openhands-sdk", "fastapi", "psycopg", "docker", "opentelemetry-api", "mcp"]
    script = "import importlib.metadata as m,json,platform; print(json.dumps({'python':platform.python_version(),'packages':{k:m.version(k) for k in " + repr(package_names) + "}}))"
    output = subprocess.check_output(["uv", "run", "--frozen", "--no-sync", "python", "-B", "-c", script], cwd=source)
    installed = json.loads(output)
    for package, version in installed["packages"].items():
        assert any(p["name"] == package and p["version"] == version for p in lock["package"])
    client = docker.from_env()
    try:
        images = {name: client.api.inspect_container(config["project"] + suffix)["Image"]
                  for name, suffix in (("postgres", "-postgres-1"), ("collector", "-otel-collector-1"))}
        images["gpu"] = config["image_id"]
        engine = client.version()["Version"]
    finally:
        client.close()
    witnesses = [run_evidence / f for f in ("重建恢复演练结果v2.json", "实际恢复闭包v2.json", "故障续验证据v2.json", "密钥六面审计v1.json")]
    witnesses.append(evidence / "质量门禁_m0v1.json")
    record = {"record_kind": "PERSONAL_PRODUCTION_RELEASE", "version": (source / "VERSION").read_text().strip(),
              "validated_at_utc": datetime.now(timezone.utc).isoformat(), "code_revision": revision,
              "code_tree": git(source, "rev-parse", "HEAD^{tree}"), "source_checkout_clean": True,
              "restore_checkout_clean": True, "database": database_truth(config), "runtime": installed,
              "docker_engine": engine, "oci_images": images, "gpu_base": gpu["resolution"]["base_index_digest"],
              "lockfiles": {p: sha(source / p) for p in ("uv.lock", "pnpm-lock.yaml", "UPSTREAM_COMPONENTS.yaml")},
              "migration_files": {p.name: sha(p) for p in (source / "adapters/postgres/migrations").glob("*.sql")},
              "evidence": {str(p.relative_to(root)): sha(p) for p in witnesses},
              "audit_runs": rebuild, "pa1r": "PASS", "personal_production_baseline": "COMPLETE",
              "boundaries": ["single-user, local GPU across process/network gateway", "live paid LLM not exercised", "unconfigured monetary cost remains unavailable", "no external publish; M18/M19 remain deferred"]}
    path = root / "docs" / "operations" / "PA1R发布记录v1.json"
    if path.exists():
        raise RuntimeError("release record exists; create a new version rather than overwrite")
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
