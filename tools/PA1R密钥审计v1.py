"""Canary audit with counted surfaces and real dump/archive positive controls.

Only a deliberately generated ignored audit configuration is read. Never print
secret values or matched excerpts. This is a scoped leak test, not a claim that
all possible unknown credentials are absent from arbitrary content.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import subprocess
import tarfile
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import docker
import psycopg


def variants(value: str) -> tuple[bytes, ...]:
    raw = value.encode("utf-8")
    return (raw, value.encode("utf-16-le"), quote(value, safe="").encode(), base64.b64encode(raw))


def matching(data: bytes, secrets: list[str]) -> list[int]:
    return [index for index, value in enumerate(secrets) if any(v in data for v in variants(value))]


def command(args: list[str], *, cwd: Path, data: bytes | None = None) -> bytes:
    result = subprocess.run(args, cwd=cwd, input=data, capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(f"audit command failed: {args[0]} (exit {result.returncode})")
    return result.stdout


def files_under(root: Path) -> list[Path]:
    result: list[Path] = []
    for here, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {".git", ".venv", "node_modules", "__pycache__"}]
        result.extend(Path(here) / f for f in files)
    return result


def expanded_tar(data: bytes) -> list[bytes]:
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        return [archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()]


def git_contents(repo: Path) -> list[bytes]:
    raw = command(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=repo)
    paths = sorted(set(raw.decode("utf-8").strip("\0").split("\0")))
    content = [(repo / p).read_bytes() for p in paths if (repo / p).is_file()]
    objects = command(["git", "rev-list", "--objects", "--all"], cwd=repo)
    ids = sorted({line.split(b" ", 1)[0] for line in objects.splitlines()})
    raw_objects = command(["git", "cat-file", "--batch"], cwd=repo, data=b"\n".join(ids) + b"\n")
    stream = io.BytesIO(raw_objects)
    while header := stream.readline():
        _, kind, size = header.strip().split()
        item = stream.read(int(size))
        assert stream.read(1) == b"\n"
        if kind == b"blob":
            content.append(item)
    return content


def positive_dump(config: dict[str, Any], container: str, repo: Path, values: list[str]) -> bytes:
    database = "pa1r_canary_control"
    options = dict(host="127.0.0.1", port=22432, user="research_os", password=config["source_password"])
    with psycopg.connect(**options, dbname="postgres", autocommit=True) as admin:
        admin.execute(psycopg.sql.SQL("CREATE DATABASE {}").format(psycopg.sql.Identifier(database)))
        try:
            with psycopg.connect(**options, dbname=database) as conn:
                conn.execute("CREATE TABLE canary_control (value TEXT NOT NULL)")
                for value in values:
                    conn.execute("INSERT INTO canary_control VALUES (%s)", (value,))
            dumped = command(["docker", "exec", container, "pg_dump", "-U", "research_os", "-d", database, "-Fc"], cwd=repo)
            return command(["docker", "exec", "-i", container, "pg_restore", "-f", "-"], cwd=repo, data=dumped)
        finally:
            admin.execute(psycopg.sql.SQL("DROP DATABASE {}").format(psycopg.sql.Identifier(database)))


def audit(repo: Path, evidence: Path, version: str) -> dict[str, Any]:
    config = json.loads((evidence / f"续审私有配置{version}.json").read_text(encoding="utf-8"))
    source, restored = evidence / f"封存源码{version}", evidence / f"恢复源码{version}"
    values = [config[k] for k in ("source_password", "restore_password", "enrollment", "llm_canary")]
    assert len(set(values)) == 4 and all(len(v) >= 32 for v in values)
    buckets: dict[str, list[bytes]] = {key: [] for key in ("Git", "backups", "logs", "telemetry", "Artifact", "exports")}
    buckets["Git"] = git_contents(repo)
    for path in files_under(evidence):
        if path.suffix == ".log":
            buckets["logs"].append(path.read_bytes())
    for root in (source, restored):
        for key, folder in (("Artifact", "artifacts-blobs"), ("telemetry", "otel"), ("exports", "exports")):
            buckets[key].extend(p.read_bytes() for p in files_under(root / "data" / folder))
    client = docker.from_env()
    container = client.containers.get(config["project"] + "-postgres-1")
    was_running = container.status == "running"
    if not was_running:
        container.start()
    try:
        for _ in range(30):
            if container.exec_run(["pg_isready", "-U", "research_os"]).exit_code == 0:
                break
            time.sleep(1)
        for path in (source / "data" / "backups").glob("*.dump"):
            buckets["backups"].append(command(["docker", "exec", "-i", container.name, "pg_restore", "-f", "-"], cwd=repo, data=path.read_bytes()))
        for path in (source / "data" / "backups").glob("*.tar.gz"):
            buckets["backups"].extend(expanded_tar(path.read_bytes()))
        control = positive_dump(config, container.name, repo, values)
        assert matching(control, values) == [0, 1, 2, 3], "PostgreSQL positive control failed"
    finally:
        if not was_running:
            container.stop(timeout=3)
        client.close()
    archive_buffer = io.BytesIO()
    with tarfile.open(fileobj=archive_buffer, mode="w:gz") as archive:
        for index, value in enumerate(values):
            payload = value.encode()
            member = tarfile.TarInfo(str(index))
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))
    assert sorted({i for b in expanded_tar(archive_buffer.getvalue()) for i in matching(b, values)}) == [0, 1, 2, 3]
    results = {}
    for name, buffers in buckets.items():
        assert buffers and sum(map(len, buffers)) > 0, f"empty audit surface: {name}"
        # Each surface also uses a positive encoded-byte control, without putting
        # intentional leak content into business artifacts or evidence archives.
        assert matching(b"control=" + values[0].encode(), values) == [0]
        hits = sum(bool(matching(buffer, values)) for buffer in buffers)
        results[name] = {"objects": len(buffers), "bytes": sum(map(len, buffers)), "hit_objects": hits, "positive_control": True}
    result = {"scope": "four unique ephemeral audit canaries; current tracked/untracked files and all reachable Git blobs",
              "fingerprints": [hashlib.sha256(v.encode()).hexdigest()[:12] for v in values],
              "surfaces": results, "postgres_positive_canaries": 4, "archive_positive_canaries": 4,
              "verdict": "PASS" if all(r["hit_objects"] == 0 for r in results.values()) else "FAIL"}
    (evidence / "密钥六面审计v1.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-version", default="v4")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = audit(root, root / "scratch" / "PA1R闭环v1" / ("续审" + args.candidate_version), args.candidate_version)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["verdict"] == "PASS" else 1)
