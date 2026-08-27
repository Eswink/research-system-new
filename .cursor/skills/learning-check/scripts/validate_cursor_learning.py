#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import yaml


def _discover_root() -> Path:
    explicit = os.environ.get("CURSOR_FRAMEWORK_ROOT")
    if explicit:
        return Path(explicit).resolve()
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "VERSION").is_file() and (
            candidate / ".cursor" / "framework.json"
        ).is_file():
            return candidate
    raise RuntimeError("Cannot locate repository root (VERSION + .cursor/framework.json)")


ROOT = _discover_root()
CURSOR = ROOT / ".cursor"
ERRORS = []
ID_RE = re.compile(r"LEARN-\d{8}-\d{3}")
TARGETS = {"RULE", "SKILL", "HOOK", "VALIDATOR", "EVAL", "KNOWLEDGE", "MEMORY", "ADR"}
ACTIVE = {"PROPOSED", "CLUSTERED", "REPLAYING", "REVIEWING"}
RELS = {"followed_by", "gates", "requires", "may_require", "conflicts_with", "supersedes"}


def err(x):
    ERRORS.append(x)


def load_yaml(p: Path) -> dict[str, Any]:
    try:
        v = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if not isinstance(v, dict):
            raise TypeError("expected mapping")
        return v
    except Exception as exc:
        err(f"invalid yaml {p.relative_to(ROOT)}: {exc}")
        return {}


def repo_ref_exists(v: str) -> bool:
    p = Path(v)
    return not p.is_absolute() and ".." not in p.parts and (ROOT / p).exists()


def acyclic(relations):
    g = {}
    for r in relations:
        if r.get("type") == "requires":
            g.setdefault(str(r.get("from")), set()).add(str(r.get("to")))
    visiting = set()
    done = set()

    def visit(n, trail):
        if n in done:
            return
        if n in visiting:
            err("requires cycle: " + " -> ".join(trail + [n]))
            return
        visiting.add(n)
        for x in g.get(n, set()):
            visit(x, trail + [n])
        visiting.remove(n)
        done.add(n)

    for n in g:
        visit(n, [])


framework = json.loads((CURSOR / "framework.json").read_text(encoding="utf-8"))
registry = load_yaml(CURSOR / "learning/REGISTRY.yaml")
relations_doc = load_yaml(CURSOR / "learning/SKILL_RELATIONS.yaml")
if registry.get("schema_version") != 1:
    err("learning registry schema_version must be 1")
if relations_doc.get("schema_version") != 1:
    err("skill relation schema_version must be 1")
if registry.get("framework_version") != framework.get("framework_version"):
    err("learning registry framework_version mismatch")
skills = {p.parent.name for p in (CURSOR / "skills").rglob("SKILL.md")}
relations = list(relations_doc.get("relations") or [])
seen = set()
for r in relations:
    a, b, k = str(r.get("from")), str(r.get("to")), str(r.get("type"))
    if a not in skills or b not in skills:
        err(f"bad skill relation: {r}")
    if k not in RELS:
        err(f"unsupported relation type: {k}")
    key = (a, b, k)
    if key in seen:
        err(f"duplicate skill relation: {key}")
    seen.add(key)
acyclic(relations)
registry_by_id = {}
for e in registry.get("entries") or []:
    lid = str(e.get("id") or "")
    if not ID_RE.fullmatch(lid):
        err(f"bad registry id: {lid}")
    if lid in registry_by_id:
        err(f"duplicate registry id: {lid}")
    registry_by_id[lid] = e
    if not repo_ref_exists(str(e.get("file") or "")):
        err(f"registry entry missing file: {lid}")
files = {}
for folder in ("inbox", "accepted", "rejected"):
    for p in (CURSOR / "learning" / folder).glob("LEARN-*.yaml"):
        d = load_yaml(p)
        lid = str(d.get("id") or "")
        if lid in files:
            err(f"duplicate learning id: {lid}")
        files[lid] = (p, d, folder)
for lid, (p, d, folder) in files.items():
    status = str(d.get("status") or "")
    ok = (
        (folder == "inbox" and status in ACTIVE)
        or (folder == "accepted" and status in {"ACCEPTED", "SUPERSEDED"})
        or (folder == "rejected" and status == "REJECTED")
    )
    if not ok:
        err(f"{lid} status {status} inconsistent with folder {folder}")
    entry = registry_by_id.get(lid)
    if not entry:
        err(f"proposal missing registry entry: {lid}")
    else:
        if entry.get("status") != status:
            err(f"registry/proposal status mismatch: {lid}")
        if entry.get("file") != p.relative_to(ROOT).as_posix():
            err(f"registry/proposal file mismatch: {lid}")
    for key in (
        "summary",
        "severity",
        "source_refs",
        "occurrences",
        "problem",
        "proposal",
        "replay",
    ):
        if not d.get(key):
            err(f"{lid} missing {key}")
    proposal = d.get("proposal") or {}
    occurrences = list(d.get("occurrences") or [])
    tasks = [str(x.get("task_ref") or "") for x in occurrences if isinstance(x, dict)]
    if proposal.get("target_type") not in TARGETS:
        err(f"{lid} invalid target type")
    if status == "ACCEPTED":
        if d.get("severity") == "NORMAL" and len(set(tasks)) < 2:
            err(f"{lid} normal promotion requires >=2 independent task occurrences")
        if (
            d.get("severity") == "SECURITY_CRITICAL"
            and not str((d.get("problem") or {}).get("reproduction") or "").strip()
        ):
            err(f"{lid} critical security promotion requires deterministic reproduction")
        replay = d.get("replay") or {}
        if (
            not replay.get("before_cases")
            or not replay.get("after_cases")
            or not str(replay.get("before_result") or "").strip()
            or not str(replay.get("after_result") or "").strip()
        ):
            err(f"{lid} accepted promotion requires complete before/after replay")
        paths = list(proposal.get("target_paths") or [])
        if not paths:
            err(f"{lid} accepted promotion requires target_paths")
        for ref in paths:
            if not repo_ref_exists(str(ref)):
                err(f"{lid} promoted target path does not exist: {ref}")
        validation = d.get("validation") or {}
        if (
            validation.get("result") != "PASS"
            or not validation.get("commands")
            or not validation.get("evidence_refs")
        ):
            err(f"{lid} accepted promotion requires deterministic validation PASS with evidence")
        for ref in validation.get("evidence_refs") or []:
            if not repo_ref_exists(str(ref)):
                err(f"{lid} validation evidence ref missing: {ref}")
        for approval in d.get("approvals") or []:
            if approval.get("hard_gate") != "PASS":
                err(f"{lid} scoped approval failed: {approval.get('reviewer')}")
            if not repo_ref_exists(str(approval.get("ref") or "")):
                err(f"{lid} approval ref missing: {approval.get('ref')}")
        promotion = d.get("promotion") or {}
        if not str(promotion.get("authorization_ref") or "").strip():
            err(f"{lid} accepted promotion requires explicit authorization_ref")
        if not str(promotion.get("promoted_at") or "").strip():
            err(f"{lid} accepted promotion missing promoted_at")
        for k in ("promoted_digest", "regression_digest"):
            if not re.fullmatch(r"[0-9a-f]{64}", str(promotion.get(k) or "")):
                err(f"{lid} invalid {k}")
for lid in registry_by_id:
    if lid not in files:
        err(f"registry points to missing proposal: {lid}")
if ERRORS:
    for e in ERRORS:
        print("ERROR:", e)
    print(f"FAILED: {len(ERRORS)} learning integrity error(s)")
    raise SystemExit(1)
print(f"PASS: learning system validated; {len(files)} proposal(s), {len(relations)} relation(s)")
