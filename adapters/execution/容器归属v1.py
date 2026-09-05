"""Narrow reclamation of execution containers belonging to superseded sessions."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from docker.errors import NotFound

_PREFIX = "io.research-os."
_NAME_PREFIX = "/research-os-exec-"


def _ref(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ContainerOwnership:
    owner_id: str
    generation: int
    authority_ref: str

    def __post_init__(self) -> None:
        if not self.owner_id or not self.authority_ref or self.generation < 1:
            raise ValueError("container ownership requires an authoritative positive generation")

    def labels(self) -> dict[str, str]:
        return {
            _PREFIX + "kind": "execution",
            _PREFIX + "owner": _ref(self.owner_id),
            _PREFIX + "authority": _ref(self.authority_ref),
            _PREFIX + "generation": str(self.generation),
        }


def _superseded(labels: dict[str, str], owner: ContainerOwnership) -> bool:
    expected = owner.labels()
    for key in ("kind", "owner", "authority"):
        label = _PREFIX + key
        if labels.get(label) != expected[label]:
            return False
    raw_generation = labels.get(_PREFIX + "generation", "")
    if not raw_generation.isdecimal():
        return False
    return 0 < int(raw_generation) < owner.generation


def reclaim_superseded(api: Any, owner: ContainerOwnership, image_id: str) -> int:
    """Remove only positively identified older-generation execution containers.

    Both stopped and running old containers have lost session authority. Names,
    immutable image IDs, owner namespace and generation are checked together;
    foreign, current, future-generation and legacy-unlabelled containers stay.
    Unexpected Engine failures propagate: a new worker must not claim through
    a failed reclamation. A concurrently removed container is already clean.
    """
    if not image_id.startswith("sha256:"):
        raise ValueError("reclamation requires an immutable image identity")
    removed = 0
    for summary in api.containers(all=True):
        if not _superseded(summary.get("Labels") or {}, owner):
            continue
        try:
            details = api.inspect_container(summary["Id"])
            labels = details.get("Config", {}).get("Labels") or {}
            if not _superseded(labels, owner):
                continue
            if details.get("Image") != image_id:
                continue
            if not str(details.get("Name", "")).startswith(_NAME_PREFIX):
                continue
            api.remove_container(summary["Id"], force=True)
            removed += 1
        except NotFound:
            continue
    return removed
