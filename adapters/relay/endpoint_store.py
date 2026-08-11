"""LLMEndpoint 存储实现。

YamlEndpointStore：从 YAML 加载并写回（UTF-8）。
MemoryEndpointStore：进程内存储（测试/组合用）。
两者都复用 LLMEndpoint 域不变量。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from adapters.contracts.base import load_flat_collection, load_yaml
from packages.domain.circuit_breaker import CircuitBreakerConfig
from packages.domain.models import EndpointDiscoveryConfig, LLMEndpoint


def _parse_discovery(raw: dict[str, Any] | None) -> EndpointDiscoveryConfig | None:
    if not raw:
        return None
    return EndpointDiscoveryConfig(
        enabled=bool(raw.get("enabled", False)),
        allow_models=tuple(str(item) for item in (raw.get("allow_models") or [])),
    )


def _parse_circuit_breaker(raw: dict[str, Any] | None) -> CircuitBreakerConfig | None:
    if not raw:
        return None
    return CircuitBreakerConfig(
        failure_threshold=int(raw.get("failure_threshold", 5)),
        open_timeout_seconds=int(raw.get("open_timeout_seconds", 60)),
        half_open_max_probes=int(raw.get("half_open_max_probes", 1)),
    )


class MemoryEndpointStore:
    """内存实现；CRUD 语义显式、可测试。"""

    def __init__(self, initial: list[LLMEndpoint] | None = None) -> None:
        self._endpoints: dict[str, LLMEndpoint] = {item.id: item for item in (initial or [])}

    def list_endpoints(self) -> list[LLMEndpoint]:
        return list(self._endpoints.values())

    def get_endpoint(self, endpoint_id: str) -> LLMEndpoint:
        try:
            return self._endpoints[endpoint_id]
        except KeyError as exc:
            raise KeyError(f"endpoint not found: {endpoint_id!r}") from exc

    def save_endpoint(self, endpoint: LLMEndpoint) -> None:
        self._endpoints[endpoint.id] = endpoint

    def delete_endpoint(self, endpoint_id: str) -> None:
        if endpoint_id not in self._endpoints:
            raise KeyError(f"endpoint not found: {endpoint_id!r}")
        del self._endpoints[endpoint_id]


class YamlEndpointStore:
    """YAML 文件实现：加载现有文件，保存时写回（UTF-8）。"""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._endpoints = self._load()

    def _load(self) -> dict[str, LLMEndpoint]:
        if not self._path.exists():
            return {}
        data = load_yaml(str(self._path))
        section = data.get("llm_endpoints") if isinstance(data, dict) else None
        if not isinstance(section, dict) or not section:
            return {}
        raw_collection = load_flat_collection(
            str(self._path), "llm_endpoints", "llm-endpoint.schema.json"
        )
        endpoints: dict[str, LLMEndpoint] = {}
        for key, raw in raw_collection.items():
            endpoints[key] = LLMEndpoint(
                id=raw["id"],
                name=raw["name"],
                protocol=raw["protocol"],
                base_url=raw["base_url"],
                credential_ref=raw["credential_ref"],
                enabled=raw.get("enabled", True),
                request_timeout_seconds=raw.get("request_timeout_seconds", 60),
                max_retries=raw.get("max_retries", 3),
                concurrency_limit=raw.get("concurrency_limit", 4),
                discovery=_parse_discovery(raw.get("discovery")),
                circuit_breaker=_parse_circuit_breaker(raw.get("circuit_breaker")),
            )
        return endpoints

    def list_endpoints(self) -> list[LLMEndpoint]:
        return list(self._endpoints.values())

    def get_endpoint(self, endpoint_id: str) -> LLMEndpoint:
        try:
            return self._endpoints[endpoint_id]
        except KeyError as exc:
            raise KeyError(f"endpoint not found: {endpoint_id!r}") from exc

    def save_endpoint(self, endpoint: LLMEndpoint) -> None:
        self._endpoints[endpoint.id] = endpoint
        self._persist()

    def delete_endpoint(self, endpoint_id: str) -> None:
        if endpoint_id not in self._endpoints:
            raise KeyError(f"endpoint not found: {endpoint_id!r}")
        del self._endpoints[endpoint_id]
        self._persist()

    def _persist(self) -> None:
        payload: dict[str, dict[str, object]] = {"llm_endpoints": {}}
        for endpoint_id, endpoint in self._endpoints.items():
            record: dict[str, object] = {
                "id": endpoint.id,
                "name": endpoint.name,
                "protocol": endpoint.protocol,
                "base_url": endpoint.base_url,
                "credential_ref": endpoint.credential_ref,
                "enabled": endpoint.enabled,
                "request_timeout_seconds": endpoint.request_timeout_seconds,
                "max_retries": endpoint.max_retries,
                "concurrency_limit": endpoint.concurrency_limit,
            }
            if endpoint.discovery is not None:
                record["discovery"] = {
                    "enabled": endpoint.discovery.enabled,
                    "allow_models": list(endpoint.discovery.allow_models),
                }
            if endpoint.circuit_breaker is not None:
                record["circuit_breaker"] = {
                    "failure_threshold": endpoint.circuit_breaker.failure_threshold,
                    "open_timeout_seconds": endpoint.circuit_breaker.open_timeout_seconds,
                    "half_open_max_probes": endpoint.circuit_breaker.half_open_max_probes,
                }
            payload["llm_endpoints"][endpoint_id] = record
        with self._path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=True)
