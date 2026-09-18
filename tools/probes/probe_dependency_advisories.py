"""Dependency advisory re-check against OSV (GOAL-20260918-005 EC-01 ①).

Why this exists: the sealed Mimosa scan's dependency phase reported "1 package hit
1 advisory" with an empty `packages` array, i.e. no attribution. This probe resolves
the attributable part of that claim by querying OSV for every locked package
(`uv.lock` = PyPI, `pnpm-lock.yaml` = npm) and printing a JSON record with package /
version / advisory id / summary / aliases / source url plus the lockfile digests
actually queried. Absence of hits is recorded as such and is NOT an assertion that
the project is safe (see the consuming audit record).

The probe contains no network code: it builds the OSV query payloads and merges the
responses back into a record. The single outbound step is an operator-supplied
`curl` against the pinned public endpoint, recorded verbatim in the audit document:

    # build (one batch per line, batches of 500)
    python tools/probes/probe_dependency_advisories.py --root . > batches.jsonl
    # query (published, versioned public API; no credentials, no personal data)
    curl -s -X POST https://api.osv.dev/v1/querybatch \
         -H 'Content-Type: application/json' --data @batch-1.json > response-1.json
    # merge
    python tools/probes/probe_dependency_advisories.py --root . \
         --responses response-1.json > record.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tomllib
from datetime import datetime, timezone
from typing import Any

import yaml

BATCH_SIZE = 500
OSV_URL = "https://api.osv.dev/v1/querybatch"


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def load_uv_lock(path: str) -> list[tuple[str, str]]:
    with open(path, "rb") as handle:
        data = tomllib.load(handle)
    return [(str(item["name"]), str(item["version"])) for item in data.get("package", [])]


def load_pnpm_lock(path: str) -> list[tuple[str, str]]:
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    packages: list[tuple[str, str]] = []
    for key in (data.get("packages") or {}):
        name, _sep, _peer = str(key).partition("(")
        head, sep, tail = name.rpartition("@")
        if not sep or not head:
            continue
        packages.append((head, tail))
    return packages


def build_queries(ecosystem: str, packages: list[tuple[str, str]]) -> list[dict[str, Any]]:
    return [
        {"package": {"name": name, "ecosystem": ecosystem}, "version": version}
        for name, version in sorted(set(packages))
    ]


def load_queries(root: str) -> list[dict[str, Any]]:
    pypi = load_uv_lock(os.path.join(root, "uv.lock"))
    npm = load_pnpm_lock(os.path.join(root, "pnpm-lock.yaml"))
    return build_queries("PyPI", pypi) + build_queries("npm", npm)


def collect_hits(
    queries: list[dict[str, Any]], results: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for query, result in zip(queries, results):
        vulns = result.get("vulns") or []
        if not vulns:
            continue
        hits.append(
            {
                "package": query["package"]["name"],
                "version": query["version"],
                "ecosystem": query["package"]["ecosystem"],
                "advisories": [
                    {
                        "id": vuln.get("id"),
                        "aliases": vuln.get("aliases", []),
                        "summary": vuln.get("summary"),
                        "details": (vuln.get("details") or "")[:400],
                        "published": vuln.get("published"),
                        "modified": vuln.get("modified"),
                        "severity": vuln.get("severity", []),
                        "url": "https://osv.dev/vulnerability/" + str(vuln.get("id")),
                    }
                    for vuln in vulns
                ],
            }
        )
    return hits


def emit_batches(queries: list[dict[str, Any]]) -> None:
    for start in range(0, len(queries), BATCH_SIZE):
        json.dump({"queries": queries[start : start + BATCH_SIZE]}, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    print(
        f"built {len(queries)} queries in {-(-len(queries) // BATCH_SIZE)} batch(es)",
        file=sys.stderr,
    )


def load_responses(paths: list[str], expected: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            results.extend(json.load(handle).get("results", []))
    if len(results) != expected:
        raise SystemExit(f"response/query mismatch: {len(results)} results for {expected} queries")
    return results


def lockfile_summary(root: str) -> dict[str, Any]:
    uv_packages = load_uv_lock(os.path.join(root, "uv.lock"))
    npm_packages = load_pnpm_lock(os.path.join(root, "pnpm-lock.yaml"))
    return {
        "uv.lock": {
            "sha256": sha256_file(os.path.join(root, "uv.lock")),
            "packages": len(set(uv_packages)),
        },
        "pnpm-lock.yaml": {
            "sha256": sha256_file(os.path.join(root, "pnpm-lock.yaml")),
            "packages": len(set(npm_packages)),
        },
    }


def build_record(
    root: str, queries: list[dict[str, Any]], hits: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "schemaVersion": "researchos-dependency-advisory-recheck/v1",
        "queriedAt": datetime.now(timezone.utc).isoformat(),
        "endpoint": OSV_URL,
        "lockfiles": lockfile_summary(root),
        "queries": {
            "total": len(queries),
            "byEcosystem": {
                "PyPI": len([q for q in queries if q["package"]["ecosystem"] == "PyPI"]),
                "npm": len([q for q in queries if q["package"]["ecosystem"] == "npm"]),
            },
        },
        "hitCount": len(hits),
        "hits": hits,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root")
    parser.add_argument(
        "--responses",
        action="append",
        default=[],
        help="OSV querybatch response files, in batch order; omit to print payload batches",
    )
    args = parser.parse_args()

    queries = load_queries(args.root)
    if not args.responses:
        emit_batches(queries)
        return 0

    results = load_responses(args.responses, len(queries))
    hits = collect_hits(queries, results)
    record = build_record(args.root, queries, hits)
    json.dump(record, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    for hit in hits:
        ids = ", ".join(str(item["id"]) for item in hit["advisories"])
        print(f"HIT {hit['ecosystem']} {hit['package']}@{hit['version']} -> {ids}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
