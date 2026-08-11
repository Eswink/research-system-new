"""YAML / 内存 EndpointStore 测试。"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from adapters.relay.endpoint_store import MemoryEndpointStore, YamlEndpointStore
from packages.domain.circuit_breaker import CircuitBreakerConfig
from packages.domain.models import EndpointDiscoveryConfig, LLMEndpoint

ENDPOINT = LLMEndpoint(
    id="main",
    name="Main Relay",
    protocol="OPENAI_COMPATIBLE",
    base_url="https://relay.example.com/api/v1",
    credential_ref="llm_main_key",
)


class TestMemoryEndpointStore:
    def test_save_and_get(self) -> None:
        store = MemoryEndpointStore()
        store.save_endpoint(ENDPOINT)
        assert store.get_endpoint("main") == ENDPOINT

    def test_list_returns_all(self) -> None:
        other = LLMEndpoint(
            id="secondary",
            name="Secondary",
            protocol="OPENAI_COMPATIBLE",
            base_url="https://relay2.example.com/v1",
            credential_ref="llm_secondary_key",
        )
        store = MemoryEndpointStore(initial=[ENDPOINT, other])
        assert {item.id for item in store.list_endpoints()} == {"main", "secondary"}

    def test_get_missing_raises(self) -> None:
        store = MemoryEndpointStore()
        with pytest.raises(KeyError):
            store.get_endpoint("missing")

    def test_delete_removes(self) -> None:
        store = MemoryEndpointStore(initial=[ENDPOINT])
        store.delete_endpoint("main")
        assert store.list_endpoints() == []

    def test_delete_missing_raises(self) -> None:
        store = MemoryEndpointStore()
        with pytest.raises(KeyError):
            store.delete_endpoint("missing")

    def test_save_requires_valid_llm_endpoint_invariants(self) -> None:
        store = MemoryEndpointStore()
        with pytest.raises(ValueError):
            store.save_endpoint(
                LLMEndpoint(
                    id="bad",
                    name="Bad",
                    protocol="OPENAI_COMPATIBLE",
                    base_url="not-a-url",
                    credential_ref="k",
                )
            )


class TestYamlEndpointStore:
    def test_loads_existing_file(self, tmp_path: Path) -> None:
        path = tmp_path / "llm_endpoints.yaml"
        path.write_text(
            yaml.safe_dump(
                {
                    "llm_endpoints": {
                        "main": {
                            "name": "Main Relay",
                            "protocol": "OPENAI_COMPATIBLE",
                            "base_url": "https://relay.example.com/api/v1",
                            "credential_ref": "llm_main_key",
                        }
                    }
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        store = YamlEndpointStore(path)
        assert store.get_endpoint("main").base_url == "https://relay.example.com/api/v1"

    def test_missing_file_starts_empty(self, tmp_path: Path) -> None:
        store = YamlEndpointStore(tmp_path / "absent.yaml")
        assert store.list_endpoints() == []

    def test_save_persists_to_disk(self, tmp_path: Path) -> None:
        path = tmp_path / "llm_endpoints.yaml"
        store = YamlEndpointStore(path)
        store.save_endpoint(ENDPOINT)
        reloaded = YamlEndpointStore(path)
        assert reloaded.get_endpoint("main").id == "main"

    def test_delete_persists_to_disk(self, tmp_path: Path) -> None:
        path = tmp_path / "llm_endpoints.yaml"
        store = YamlEndpointStore(path)
        store.save_endpoint(ENDPOINT)
        store.delete_endpoint("main")
        reloaded = YamlEndpointStore(path)
        assert reloaded.list_endpoints() == []

    def test_discovery_round_trip(self, tmp_path: Path) -> None:
        path = tmp_path / "llm_endpoints.yaml"
        endpoint = LLMEndpoint(
            id="main",
            name="Main Relay",
            protocol="OPENAI_COMPATIBLE",
            base_url="https://relay.example.com/api/v1",
            credential_ref="llm_main_key",
            discovery=EndpointDiscoveryConfig(enabled=True, allow_models=("model-alpha",)),
        )
        store = YamlEndpointStore(path)
        store.save_endpoint(endpoint)
        reloaded = YamlEndpointStore(path).get_endpoint("main")
        assert reloaded.discovery is not None
        assert reloaded.discovery.enabled is True
        assert reloaded.discovery.allow_models == ("model-alpha",)

    def test_circuit_breaker_round_trip(self, tmp_path: Path) -> None:
        path = tmp_path / "llm_endpoints.yaml"
        endpoint = LLMEndpoint(
            id="main",
            name="Main Relay",
            protocol="OPENAI_COMPATIBLE",
            base_url="https://relay.example.com/api/v1",
            credential_ref="llm_main_key",
            circuit_breaker=CircuitBreakerConfig(
                failure_threshold=7, open_timeout_seconds=120, half_open_max_probes=2
            ),
        )
        store = YamlEndpointStore(path)
        store.save_endpoint(endpoint)
        reloaded = YamlEndpointStore(path).get_endpoint("main")
        assert reloaded.circuit_breaker is not None
        assert reloaded.circuit_breaker.failure_threshold == 7
        assert reloaded.circuit_breaker.open_timeout_seconds == 120
        assert reloaded.circuit_breaker.half_open_max_probes == 2
