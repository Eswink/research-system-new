"""实验产物入库辅助（M9）：工作区文件 → 内容寻址 Artifact。

纯函数（显式依赖 ArtifactStore），供 ExperimentExecutor 使用。
内容持久化归 ArtifactStore；本模块不拥有 Evidence/Claim truth。
"""

from __future__ import annotations

from pathlib import Path

from packages.application.experiments.metric_extraction import (
    ExperimentResultPayload,
    parse_experiment_result_json,
)
from packages.application.experiments.types import MEDIA_OCTET, RESULT_FILE
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest
from packages.domain.enums import ArtifactState


def read_result_payload(
    workspace_path: Path, expected_run_id: ID
) -> ExperimentResultPayload | None:
    result_path = workspace_path / RESULT_FILE
    if not result_path.exists():
        return None
    raw = result_path.read_bytes()
    return parse_experiment_result_json(raw, expected_run_id=str(expected_run_id.value))


def store_log_artifact(
    store: ArtifactStore,
    run_id: ID,
    workspace_path: Path,
    filename: str,
    declared_digest: Digest | None,
) -> str | None:
    path = workspace_path / filename
    if not path.exists():
        return None
    content = path.read_bytes()
    actual = Digest.of_bytes(content)
    if declared_digest is not None and actual != declared_digest:
        raise InvalidInputError(
            f"{filename} content digest {actual} diverges from "
            f"execution-recorded digest {declared_digest}"
        )
    return store_file_artifact(
        store,
        run_id,
        path,
        classification="execution_log",
        media_type="text/plain",
    )


def store_referenced_artifacts(
    store: ArtifactStore,
    run_id: ID,
    workspace_path: Path,
    refs: tuple[str, ...],
) -> tuple[str, ...]:
    stored: list[str] = []
    for ref in refs:
        path = (workspace_path / ref).resolve()
        try:
            path.relative_to(workspace_path.resolve())
        except ValueError:
            raise InvalidInputError(f"artifact ref escapes workspace: {ref!r}") from None
        if not path.is_file():
            raise InvalidInputError(f"artifact ref missing: {ref!r}")
        stored.append(
            store_file_artifact(store, run_id, path, classification="experiment_artifact")
        )
    return tuple(stored)


def store_file_artifact(
    store: ArtifactStore,
    run_id: ID,
    path: Path,
    *,
    classification: str,
    media_type: str = MEDIA_OCTET,
) -> str:
    content = path.read_bytes()
    artifact_id = f"{run_id.value}:{path.name}"
    artifact = Artifact(
        id=artifact_id,
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type=media_type,
        created_by="experiment_executor",
        classification=classification,
        state=ArtifactState.ACTIVE,
    )
    store.put(artifact, content)
    return artifact_id
