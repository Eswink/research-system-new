"""Ownership proof is required before killing any stale execution container."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest
from docker.errors import APIError

from adapters.execution.容器归属v1 import ContainerOwnership, reclaim_superseded

IMAGE = "sha256:" + "a" * 64
OWNER = ContainerOwnership("worker-a", 3, "http://gateway-a")


class _Engine:
    def __init__(self, details: list[dict[str, Any]]) -> None:
        self.details = {item["Id"]: item for item in details}
        self.removed: list[str] = []

    def containers(self, **_: Any) -> list[dict[str, Any]]:
        return [
            {"Id": key, "Labels": item["Config"]["Labels"]} for key, item in self.details.items()
        ]

    def inspect_container(self, container_id: str) -> dict[str, Any]:
        return self.details[container_id]

    def remove_container(self, container_id: str, *, force: bool) -> None:
        assert force is True
        self.removed.append(container_id)


def _container(name: str, owner: ContainerOwnership = OWNER, **extra: Any) -> dict[str, Any]:
    return {
        "Id": name,
        "Name": "/research-os-exec-" + name,
        "Image": IMAGE,
        "Config": {"Labels": owner.labels()},
        **extra,
    }


def test_reclaims_running_and_stopped_older_sessions_only() -> None:
    old = replace(OWNER, generation=2)
    engine = _Engine([
        _container("old-running", old, State={"Running": True}),
        _container("old-stopped", old, State={"Running": False}),
        _container("current"),
        _container("future", replace(OWNER, generation=4)),
        _container("other-owner", replace(old, owner_id="worker-b")),
        _container("other-authority", replace(old, authority_ref="http://gateway-b")),
        _container("other-image", old, Image="sha256:" + "b" * 64),
        _container("other-name", old, Name="/unrelated-work"),
        _container("unlabelled", old, Config={"Labels": {}}),
    ])
    assert reclaim_superseded(engine, OWNER, IMAGE) == 2
    assert engine.removed == ["old-running", "old-stopped"]


def test_reclamation_engine_failure_does_not_silently_allow_new_claims() -> None:
    class Broken(_Engine):
        def remove_container(self, container_id: str, *, force: bool) -> None:
            raise APIError("engine refused cleanup")

    engine = Broken([_container("old", replace(OWNER, generation=2))])
    with pytest.raises(APIError):
        reclaim_superseded(engine, OWNER, IMAGE)


@pytest.mark.parametrize("generation", ["", "-1", "0", "2.5", "NaN"])
def test_malformed_generation_is_not_ownership_proof(generation: str) -> None:
    item = _container("invalid")
    item["Config"]["Labels"]["io.research-os.generation"] = generation
    engine = _Engine([item])
    assert reclaim_superseded(engine, OWNER, IMAGE) == 0
