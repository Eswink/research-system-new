"""ModelStore Port：ModelDefinition 配置存储（M13 控制面引入）。

职责：运行时 ModelDefinition CRUD（wizard discover/add、probe 后保存能力断言）。
非职责：不做模型选择 / eligibility / probe 编排（application use case）；
不存储 probe 结果（每次 probe 实时执行，结果由调用方消费）。

M14 PostgreSQL canonical state 落地时，本 Port 是配置面的持久化接缝；
M13 控制面以 SQLite / InMemory 实现（与 EndpointStore 同族，非 M14 承诺）。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.models import ModelDefinition


@runtime_checkable
class ModelStore(Protocol):
    """ModelDefinition 存储；CRUD 语义由实现保证。"""

    def list_models(self) -> list[ModelDefinition]: ...

    def get_model(self, model_id: str) -> ModelDefinition: ...

    def save_model(self, model: ModelDefinition) -> None: ...

    def delete_model(self, model_id: str) -> None: ...
