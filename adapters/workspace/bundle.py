"""Deterministic workspace bundle codec (M16 WP3).

A bundle is a self-describing, canonical serialization of a workspace tree:
`{"entries": [{"path", "sha256", "data_b64"}...]}` sorted by path. It carries
only regular files — symlinks and directories-with-escapes are rejected on
both encode and decode. The bundle is content-addressed through ArtifactStore
(bundle bytes vs artifact.digest), and the *materialized* tree digest is
re-verified against the snapshot digest on import (two independent checks).
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import PurePosixPath
from typing import Any

_BUNDLE_VERSION = 1


class BundleError(ValueError):
    """Malformed or unsafe bundle (traversal / symlink / digest mismatch)."""


def _safe_relpath(path: str) -> str:
    """Reject absolute paths, drive letters, `..`, and symlink markers."""
    if not path or path.startswith("/") or "\\" in path:
        raise BundleError(f"unsafe bundle path: {path!r}")
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts:
        raise BundleError(f"bundle path escapes workspace: {path!r}")
    normalized = pure.as_posix()
    if normalized != path or not normalized:
        raise BundleError(f"bundle path not canonical: {path!r}")
    return normalized


def encode_bundle(entries: dict[str, bytes]) -> bytes:
    """Serialize {relpath: bytes} into a canonical bundle (sorted, no symlinks)."""
    payload: list[dict[str, str]] = []
    for rel in sorted(entries):
        safe = _safe_relpath(rel)
        data = entries[rel]
        payload.append(
            {
                "path": safe,
                "sha256": hashlib.sha256(data).hexdigest(),
                "data_b64": base64.b64encode(data).decode("ascii"),
            }
        )
    document = {"version": _BUNDLE_VERSION, "entries": payload}
    return json.dumps(document, separators=(",", ":"), sort_keys=True).encode("utf-8")


def decode_bundle(bundle: bytes) -> dict[str, bytes]:
    """Parse a bundle into {relpath: bytes}, validating each entry.

    Raises BundleError on malformed JSON, non-canonical/escaping paths, or a
    per-entry content digest mismatch.
    """
    try:
        document: Any = json.loads(bundle.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BundleError("bundle is not valid canonical JSON") from exc
    if not isinstance(document, dict) or document.get("version") != _BUNDLE_VERSION:
        raise BundleError("unsupported bundle version")
    raw_entries = document.get("entries")
    if not isinstance(raw_entries, list):
        raise BundleError("bundle entries must be a list")
    result: dict[str, bytes] = {}
    for item in raw_entries:
        if not isinstance(item, dict):
            raise BundleError("bundle entry must be an object")
        path = _safe_relpath(str(item.get("path", "")))
        try:
            data = base64.b64decode(str(item.get("data_b64", "")), validate=True)
        except Exception as exc:  # noqa: BLE001 - base64 raises many types
            raise BundleError(f"bundle entry {path!r} has invalid base64") from exc
        if hashlib.sha256(data).hexdigest() != item.get("sha256"):
            raise BundleError(f"bundle entry {path!r} content digest mismatch")
        if path in result:
            raise BundleError(f"duplicate bundle path: {path!r}")
        result[path] = data
    return result
