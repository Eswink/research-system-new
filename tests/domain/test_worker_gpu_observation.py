"""M17 WP1 domain tests: bounded WorkerGpuObservation + probe digest.

Fail-closed contract: any out-of-bounds / malformed field refuses
construction; the observation is pure data (no provider SDK types).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from packages.domain.core import Timestamp
from packages.domain.workers import (
    GPU_CAPABILITY,
    MAX_GPU_DEVICE_NAME_LENGTH,
    WorkerGpuObservation,
    WorkerRegistration,
    gpu_probe_digest,
)


def _observation(**overrides: object) -> WorkerGpuObservation:
    base: dict[str, object] = {
        "device_name": "NVIDIA GeForce RTX 4060 Laptop GPU",
        "device_count": 1,
        "driver_version": "581.80",
        "cuda_runtime_version": "12.8",
        "total_vram_bytes": 8_585_216_000,
        "framework": "torch-2.9.1+cu128",
        "probed_at": Timestamp(datetime(2026, 9, 2, tzinfo=timezone.utc)),
        "probe_digest": "0123456789abcdef",
    }
    base.update(overrides)
    return WorkerGpuObservation(**base)  # type: ignore[arg-type]


def test_gpu_capability_is_single_token() -> None:
    assert GPU_CAPABILITY == "gpu"


def test_observation_json_roundtrip_preserves_facts() -> None:
    observation = _observation()
    assert WorkerGpuObservation.from_json_dict(observation.to_json_dict()) == observation


def test_digest_is_stable_and_field_sensitive() -> None:
    kwargs: dict[str, object] = {
        "device_name": "GPU A",
        "device_count": 1,
        "driver_version": "581.80",
        "cuda_runtime_version": "12.8",
        "total_vram_bytes": 8_585_216_000,
        "framework": "torch-2.9.1",
    }
    first = gpu_probe_digest(**kwargs)  # type: ignore[arg-type]
    assert first == gpu_probe_digest(**kwargs)  # type: ignore[arg-type]
    assert len(first) == 16
    changed = dict(kwargs, total_vram_bytes=4_000_000_000)
    assert first != gpu_probe_digest(**changed)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "override",
    [
        {"device_name": ""},
        {"device_name": "x" * (MAX_GPU_DEVICE_NAME_LENGTH + 1)},
        {"device_count": 0},
        {"device_count": -1},
        {"driver_version": ""},
        {"cuda_runtime_version": ""},
        {"total_vram_bytes": 0},
        {"total_vram_bytes": -5},
        {"framework": ""},
        {"probe_digest": ""},
    ],
)
def test_observation_rejects_out_of_bounds_fields(override: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        _observation(**override)


def test_observation_rejects_naive_probed_at() -> None:
    with pytest.raises(ValueError):
        _observation(probed_at=Timestamp(datetime(2026, 9, 2, 0, 0, 0)))  # noqa: DTZ001


@pytest.mark.parametrize(
    "data",
    [
        {},
        "not-a-dict",
        {"device_name": "GPU", "device_count": 1},  # missing fields
    ],
)
def test_observation_decode_is_fail_closed(data: object) -> None:
    with pytest.raises(ValueError):
        WorkerGpuObservation.from_json_dict(data)


def test_registration_gpu_observed_at_requires_observation() -> None:
    with pytest.raises(ValueError, match="gpu_observed_at requires gpu_observation"):
        WorkerRegistration(
            worker_id="w1",
            protocol_version="1",
            runtime_version="0.1.0",
            capabilities=frozenset({"docker"}),
            backend_kinds=frozenset({"DOCKER"}),
            platform="linux/amd64",
            partition_slots=frozenset({0}),
            max_concurrency=1,
            gpu_observed_at=Timestamp.now(),
        )


def test_registration_with_observation_survives_state_transition() -> None:
    observation = _observation()
    registration = WorkerRegistration(
        worker_id="w1",
        protocol_version="1",
        runtime_version="0.1.0",
        capabilities=frozenset({"docker", GPU_CAPABILITY}),
        backend_kinds=frozenset({"DOCKER"}),
        platform="linux/amd64",
        partition_slots=frozenset({0}),
        max_concurrency=1,
        gpu_observation=observation,
    )
    ready = registration.with_state("READY")
    assert ready.gpu_observation == observation
    assert ready.gpu_observed_at is None  # server-side stamp stays registry-owned
