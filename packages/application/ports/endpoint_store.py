"""EndpointStore Port：LLMEndpoint 配置存储。"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.models import LLMEndpoint


@runtime_checkable
class EndpointStore(Protocol):
    """LLMEndpoint 存储；CRUD 语义由实现保证。"""

    def list_endpoints(self) -> list[LLMEndpoint]: ...

    def get_endpoint(self, endpoint_id: str) -> LLMEndpoint: ...

    def save_endpoint(self, endpoint: LLMEndpoint) -> None: ...

    def delete_endpoint(self, endpoint_id: str) -> None: ...
