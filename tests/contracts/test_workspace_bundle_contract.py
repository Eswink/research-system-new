"""M16 WP3 WorkspaceBackend bundle contract (Fake + File).

Shared export/import semantics both implementations must satisfy:
export yields a canonical bundle; importing with a digest that does not match
the materialized/known snapshot fails closed. Deep integrity (traversal,
symlink, truncation) is covered in the File-specific suite.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workspace_backend import WorkspaceBackend
from packages.domain.workspace import Workspace
from tests.contracts.fixtures import workspace
from tests.contracts.registry import PORT_IMPLEMENTATIONS

_FACTORIES: list[Callable[[], object]] = list(PORT_IMPLEMENTATIONS["workspace_backend"])


def _snapshotted(factory: Callable[[], object]) -> tuple[WorkspaceBackend, Workspace]:
    backend: WorkspaceBackend = factory()  # type: ignore[assignment]
    ws = workspace()
    backend.create_workspace(ws)
    lease = backend.acquire_lease(ws, "session-1")
    backend.snapshot(lease)
    return backend, ws


@pytest.mark.parametrize("factory", _FACTORIES)
def test_export_bundle_returns_bytes(factory: Callable[[], object]) -> None:
    backend, ws = _snapshotted(factory)
    lease = backend.acquire_lease(ws, "session-1")
    snapshot = backend.snapshot(lease)
    bundle = backend.export_bundle(lease, snapshot)
    assert isinstance(bundle, bytes) and len(bundle) > 0


@pytest.mark.parametrize("factory", _FACTORIES)
def test_import_bundle_unknown_digest_rejected(factory: Callable[[], object]) -> None:
    backend, ws = _snapshotted(factory)
    lease = backend.acquire_lease(ws, "session-1")
    snapshot = backend.snapshot(lease)
    bundle = backend.export_bundle(lease, snapshot)
    with pytest.raises(InvalidInputError):
        backend.import_bundle("ws-import", bundle, "sha256:" + "ee" * 32)
