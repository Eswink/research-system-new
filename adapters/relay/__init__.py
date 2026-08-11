"""OpenAI-compatible Model Relay adapter。

实现 packages/application/model_relay 内层 Ports：httpx 传输、SSE 解析、
env credential resolver、YAML/内存 endpoint store。
"""

from adapters.relay.credential_resolver import EnvCredentialResolver
from adapters.relay.endpoint_store import MemoryEndpointStore, YamlEndpointStore
from adapters.relay.gateway import OpenAIChatGateway

__all__ = [
    "EnvCredentialResolver",
    "MemoryEndpointStore",
    "OpenAIChatGateway",
    "YamlEndpointStore",
]
