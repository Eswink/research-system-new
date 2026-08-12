"""FakeEndpointStore：LLMEndpoint 配置内存存储（CRUD + 错误注入）。"""

from __future__ import annotations

from adapters.fakes.base import FakeBase
from packages.domain.models import LLMEndpoint


class FakeEndpointStore(FakeBase):
    """list/get/save/delete；未知 endpoint 抛 KeyError（与真实实现一致）。"""

    def __init__(self, initial: tuple[LLMEndpoint, ...] = ()) -> None:
        super().__init__("endpoint_store")
        self._endpoints: dict[str, LLMEndpoint] = {item.id: item for item in initial}

    def list_endpoints(self) -> list[LLMEndpoint]:
        self._enter("list_endpoints", "")
        self._record("list_endpoints", "", result=str(len(self._endpoints)))
        return list(self._endpoints.values())

    def get_endpoint(self, endpoint_id: str) -> LLMEndpoint:
        self._enter("get_endpoint", endpoint_id)
        if endpoint_id not in self._endpoints:
            self._record("get_endpoint", endpoint_id, error="KeyError")
            raise KeyError(f"endpoint not found: {endpoint_id!r}")
        self._record("get_endpoint", endpoint_id, result=endpoint_id)
        return self._endpoints[endpoint_id]

    def save_endpoint(self, endpoint: LLMEndpoint) -> None:
        self._enter("save_endpoint", endpoint.id)
        self._endpoints[endpoint.id] = endpoint
        self._record("save_endpoint", endpoint.id)

    def delete_endpoint(self, endpoint_id: str) -> None:
        self._enter("delete_endpoint", endpoint_id)
        if endpoint_id not in self._endpoints:
            self._record("delete_endpoint", endpoint_id, error="KeyError")
            raise KeyError(f"endpoint not found: {endpoint_id!r}")
        del self._endpoints[endpoint_id]
        self._record("delete_endpoint", endpoint_id)
