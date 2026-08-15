"""Artifact export bundle use case（M9）。

把一次实验运行的 domain 记录（ExperimentRun + ReproducibilityAudit）与
其全部 Artifact 内容打包为内容寻址 bundle artifact，写入同一个
ArtifactStore（复用内容持久化职责）；解包时全链 digest 复核。

bundle 二进制格式（确定性）：
    magic: 8B "RSEXPORT\x01\n"
    manifest: canonical JSON bytes + \n
    entries（按 artifact_id 排序）:
        id_len: 4B big-endian + id bytes
        digest: 64B hex（sha256）
        size: 8B big-endian + content bytes

manifest 字段：export_id / experiment_run_id / audit_digest /
artifact entries（id, digest, size, media_type）。manifest 参与
bundle digest；任何内容篡改都会被 unpack/verify 检出。
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest, ID, Timestamp
from packages.domain.enums import ArtifactState
from packages.domain.reproducibility import ReproducibilityAudit
from packages.domain.serialization import canonical_json_bytes

MAGIC = b"RSEXPORT\x01\n"
_DIGEST_HEX_LEN = 64


@dataclass(frozen=True, slots=True)
class BundleEntry:
    artifact_id: str
    digest_hex: str
    size_bytes: int
    media_type: str


@dataclass(frozen=True, slots=True)
class ExportBundleManifest:
    export_id: str
    experiment_run_id: str
    audit_digest: str | None
    created_at: Timestamp
    entries: tuple[BundleEntry, ...]


def build_export_bundle(
    run_id: ID,
    audit: ReproducibilityAudit | None,
    *,
    export_id: str,
    artifacts: ArtifactStore,
) -> str:
    """打包 run 的全部输出 artifact → bundle artifact，返回 bundle id。"""
    refs = [artifact.id for artifact in artifacts.list_refs()]
    if not refs:
        raise InvalidInputError("no artifacts to export")
    entries: list[BundleEntry] = []
    contents: dict[str, bytes] = {}
    for artifact_id in sorted(refs):
        artifact = _artifact_by_id(artifacts, artifact_id)
        if artifact.state is ArtifactState.DELETED_TOMBSTONE:
            continue
        content = artifacts.get(artifact_id)
        entries.append(
            BundleEntry(
                artifact_id=artifact_id,
                digest_hex=artifact.digest.hex_value,
                size_bytes=len(content),
                media_type=artifact.media_type,
            )
        )
        contents[artifact_id] = content
    if not entries:
        raise InvalidInputError("no readable artifacts to export")
    manifest = ExportBundleManifest(
        export_id=export_id,
        experiment_run_id=str(run_id.value),
        audit_digest=str(audit.audit_digest) if audit and audit.audit_digest else None,
        created_at=Timestamp.now(),
        entries=tuple(entries),
    )
    bundle_bytes = _encode_bundle(manifest, contents)
    bundle_artifact = Artifact(
        id=f"{export_id}:bundle",
        digest=Digest.of_bytes(bundle_bytes),
        size_bytes=len(bundle_bytes),
        media_type="application/vnd.research-os.export-bundle",
        created_by="export_bundle",
        classification="export_bundle",
        retention_policy=None,
        state=ArtifactState.ACTIVE,
    )
    artifacts.put(bundle_artifact, bundle_bytes)
    return bundle_artifact.id


def decode_export_bundle(
    artifacts: ArtifactStore, bundle_id: str
) -> tuple[ExportBundleManifest, dict[str, bytes]]:
    """解包 bundle 并逐条 digest 复核；篡改/损坏抛 InvalidInputError。"""
    content = artifacts.get(bundle_id)
    manifest, entries = _decode_bundle(content)
    for entry in manifest.entries:
        payload = entries[entry.artifact_id]
        actual = Digest.of_bytes(payload).hex_value
        if actual != entry.digest_hex:
            raise InvalidInputError(
                f"bundle entry {entry.artifact_id!r} digest mismatch: "
                f"expected {entry.digest_hex}, got {actual}"
            )
        if len(payload) != entry.size_bytes:
            raise InvalidInputError(
                f"bundle entry {entry.artifact_id!r} size mismatch"
            )
    return manifest, entries


def _artifact_by_id(artifacts: ArtifactStore, artifact_id: str) -> Artifact:
    for artifact in artifacts.list_refs():
        if artifact.id == artifact_id:
            return artifact
    raise InvalidInputError(f"unknown artifact id: {artifact_id}")


def _encode_bundle(
    manifest: ExportBundleManifest, contents: dict[str, bytes]
) -> bytes:
    manifest_json = canonical_json_bytes(_manifest_payload(manifest)) + b"\n"
    parts = [MAGIC, manifest_json]
    for entry in manifest.entries:
        payload = contents[entry.artifact_id]
        id_bytes = entry.artifact_id.encode("utf-8")
        parts.append(struct.pack(">I", len(id_bytes)))
        parts.append(id_bytes)
        parts.append(entry.digest_hex.encode("ascii"))
        parts.append(struct.pack(">Q", len(payload)))
        parts.append(payload)
    return b"".join(parts)


def _decode_bundle(content: bytes) -> tuple[ExportBundleManifest, dict[str, bytes]]:
    if not content.startswith(MAGIC):
        raise InvalidInputError("invalid export bundle magic")
    offset = len(MAGIC)
    newline = content.index(b"\n", offset)
    manifest_json = content[offset:newline]
    offset = newline + 1
    payload = json.loads(manifest_json.decode("utf-8"))
    entries: list[BundleEntry] = []
    contents: dict[str, bytes] = {}
    for entry_payload in payload["entries"]:
        if offset + 4 > len(content):
            raise InvalidInputError("truncated export bundle")
        (id_len,) = struct.unpack(">I", content[offset : offset + 4])
        offset += 4
        artifact_id = content[offset : offset + id_len].decode("utf-8")
        offset += id_len
        digest_hex = content[offset : offset + _DIGEST_HEX_LEN].decode("ascii")
        offset += _DIGEST_HEX_LEN
        (size,) = struct.unpack(">Q", content[offset : offset + 8])
        offset += 8
        if offset + size > len(content):
            raise InvalidInputError("truncated export bundle entry")
        contents[artifact_id] = content[offset : offset + size]
        offset += size
        entries.append(
            BundleEntry(
                artifact_id=artifact_id,
                digest_hex=digest_hex,
                size_bytes=size,
                media_type=str(entry_payload["media_type"]),
            )
        )
    if offset != len(content):
        raise InvalidInputError("trailing bytes in export bundle")
    return (
        ExportBundleManifest(
            export_id=str(payload["export_id"]),
            experiment_run_id=str(payload["experiment_run_id"]),
            audit_digest=payload.get("audit_digest"),
            created_at=Timestamp(
                datetime.fromisoformat(str(payload["created_at"]).replace("Z", "+00:00"))
            ),
            entries=tuple(entries),
        ),
        contents,
    )


def _manifest_payload(manifest: ExportBundleManifest) -> dict[str, Any]:
    return {
        "export_id": manifest.export_id,
        "experiment_run_id": manifest.experiment_run_id,
        "audit_digest": manifest.audit_digest,
        "created_at": manifest.created_at.value.isoformat().replace("+00:00", "Z"),
        "entries": [
            {
                "artifact_id": entry.artifact_id,
                "digest": entry.digest_hex,
                "size_bytes": entry.size_bytes,
                "media_type": entry.media_type,
            }
            for entry in manifest.entries
        ],
    }