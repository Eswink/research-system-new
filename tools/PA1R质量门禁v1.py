"""Run serial PA-1R quality gates against a dedicated disposable test database.

The test DB is separate from all audit source/restore DBs; destructive fixtures
cannot truncate research evidence. Volumes are retained, containers stopped.
"""

from __future__ import annotations

import argparse
import json
import secrets
import subprocess
import time
import uuid
from pathlib import Path

import docker

from PA1R运行演练v1 import os_env


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--mode", choices=["targeted", "m0"], default="targeted")
    parser.add_argument("--candidate-version", default="v4")
    args = parser.parse_args()
    source = args.source.resolve()
    root = Path(__file__).resolve().parents[1]
    evidence = root / "scratch" / "PA1R闭环v1"
    evidence.mkdir(parents=True, exist_ok=True)
    password = secrets.token_urlsafe(32)
    name = "pa1r-quality-" + uuid.uuid4().hex[:10]
    client = docker.from_env()
    container = client.containers.run(
        "postgres:16-alpine", name=name, detach=True,
        environment={"POSTGRES_USER": "research_os", "POSTGRES_DB": "research_os", "POSTGRES_PASSWORD": password},
        ports={"5432/tcp": ("127.0.0.1", 22434)},
        labels={"pa1r.audit": "quality-isolated"},
    )
    collector = None
    env = os_env()
    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", RESEARCHOS_OTEL_ENABLED="false",
               RESEARCHOS_POSTGRES_DSN=f"postgresql://research_os:{password}@127.0.0.1:22434/research_os",
               RESEARCHOS_REQUIRE_POSTGRES="1")
    prefix = ["uv", "run", "--frozen", "--no-sync"]
    if args.mode == "targeted":
        commands = [
            [*prefix, "ruff", "check", "packages", "adapters", "services", "tests"],
            [*prefix, "ruff", "format", "--check", "packages", "adapters", "services", "tests"],
            [*prefix, "mypy"],
            [*prefix, "pytest", "-q", "tests/application", "tests/api", "tests/worker", "tests/tooling",
             "tests/postgres", "tests/adapters/test_重连事务边界v1.py",
             "tests/adapters/execution/test_重放计量v1.py", "tests/adapters/execution/test_容器归属v1.py", "--tb=short"],
            [*prefix, "python", "-B", ".cursor/skills/cursor-framework-check/scripts/run_all_checks.py", "--profile", "framework", "--keep-going"],
        ]
    else:
        config_path = evidence / ("续审" + args.candidate_version) / ("续审私有配置" + args.candidate_version + ".json")
        config = json.loads(config_path.read_text(encoding="utf-8"))
        collector = client.containers.get(config["project"] + "-otel-collector-1")
        collector.start()
        env.update(RESEARCHOS_OTEL_COLLECTOR_ENDPOINT="http://127.0.0.1:22418", RESEARCHOS_REQUIRE_COLLECTOR="1")
        commands = [[*prefix, "python", "-B", ".cursor/skills/cursor-framework-check/scripts/run_all_checks.py", "--profile", "m0", "--keep-going"]]
    results = []
    try:
        for _ in range(30):
            if container.exec_run(["pg_isready", "-U", "research_os"]).exit_code == 0:
                break
            time.sleep(1)
        for index, command in enumerate(commands, 1):
            result = subprocess.run(command, cwd=source, env=env, capture_output=True, timeout=580)
            output = (result.stdout + result.stderr).replace(password.encode(), b"[REDACTED]")
            log = evidence / f"质量门禁_{args.mode}_{index}v1.log"
            log.write_bytes(output)
            results.append({"command": command, "exit_code": result.returncode, "log": log.name})
            print(f"gate {index}/{len(commands)}: exit={result.returncode}; {log.name}", flush=True)
            if result.returncode:
                print(output.decode("utf-8", errors="replace")[-10000:], flush=True)
        summary = {"source": str(source), "mode": args.mode, "isolated_test_database": name,
                   "results": results, "passed": all(r["exit_code"] == 0 for r in results)}
        (evidence / f"质量门禁_{args.mode}v1.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if summary["passed"] else 1
    finally:
        container.stop(timeout=3)
        if collector is not None:
            collector.stop(timeout=3)
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
