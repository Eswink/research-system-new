"""Regression tests for stale GPU container cleanup after worker hard-kill."""

from __future__ import annotations

from typing import Any

from docker.errors import APIError

from adapters.execution.gpu_probe import (
    _run_probe_container,
    _sweep_stale_containers,
)

_TARGET_IMAGE = "research-os-gpu-sandbox:m17-v1"
_TARGET_ID = "sha256:target"


class _SweepApi:
    def __init__(self) -> None:
        self.removed: list[str] = []

    def containers(
        self,
        *,
        all: bool,
        filters: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        assert all is True
        if filters and "image" in filters:
            raise APIError("invalid filter 'image'")
        return [
            {
                "Id": "stopped-exec",
                "ImageID": _TARGET_ID,
                "Names": ["/research-os-exec-deadbeef"],
                "State": "exited",
            },
            {
                "Id": "stopped-probe",
                "ImageID": _TARGET_ID,
                "Names": ["/research-os-gpu-probe-deadbeef"],
                "State": "exited",
            },
            {
                "Id": "running-exec",
                "ImageID": _TARGET_ID,
                "Names": ["/research-os-exec-livefeed"],
                "State": "running",
            },
            {
                "Id": "foreign-name",
                "ImageID": _TARGET_ID,
                "Names": ["/user-owned-container"],
                "State": "exited",
            },
            {
                "Id": "foreign-image",
                "ImageID": "sha256:other",
                "Names": ["/research-os-exec-other"],
                "State": "exited",
            },
        ]

    def inspect_image(self, image: str) -> dict[str, object]:
        assert image == _TARGET_IMAGE
        return {"Id": _TARGET_ID}

    def remove_container(self, container_id: str, *, force: bool) -> None:
        assert force is True
        self.removed.append(container_id)


class _ProbeApi(_SweepApi):
    def __init__(self) -> None:
        super().__init__()
        self.created: dict[str, object] = {}

    def containers(
        self,
        *,
        all: bool,
        filters: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        assert all is True
        return []

    def create_container(self, **kwargs: object) -> dict[str, str]:
        self.created = dict(kwargs)
        return {"Id": "probe-id"}

    def start(self, container_id: str) -> None:
        assert container_id == "probe-id"

    def inspect_container(self, container_id: str) -> dict[str, object]:
        assert container_id == "probe-id"
        return {"State": {"Running": False, "ExitCode": 0}}

    def kill(self, container_id: str) -> None:
        raise AssertionError(f"unexpected kill: {container_id}")


class _Client:
    def __init__(self, api: Any) -> None:
        self.api = api


def test_stale_sweep_avoids_unsupported_image_filter_and_removes_only_owned_stopped() -> None:
    api = _SweepApi()

    _sweep_stale_containers(_Client(api), _TARGET_IMAGE)

    assert sorted(api.removed) == ["stopped-exec", "stopped-probe"]


def test_probe_container_has_owned_name_for_crash_recovery(tmp_path: Any) -> None:
    api = _ProbeApi()

    container_id = _run_probe_container(
        _Client(api),
        type("Config", (), {"image": _TARGET_IMAGE, "probe_timeout_seconds": 1.0})(),
        tmp_path,
        lambda _seconds: None,
        lambda: 0.0,
    )

    assert container_id == "probe-id"
    assert str(api.created["name"]).startswith("research-os-gpu-probe-")
