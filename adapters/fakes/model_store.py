"""FakeModelStore：ModelDefinition 内存存储（测试/组合用）。"""

from __future__ import annotations

from adapters.fakes.base import FakeBase
from packages.domain.models import ModelDefinition


class FakeModelStore(FakeBase):
    """list/get/save/delete；未知 model 抛 KeyError（与真实实现一致）。"""

    def __init__(self, initial: tuple[ModelDefinition, ...] = ()) -> None:
        super().__init__("model_store")
        self._models: dict[str, ModelDefinition] = {item.id: item for item in initial}

    def list_models(self) -> list[ModelDefinition]:
        self._enter("list_models", "")
        self._record("list_models", "", result=str(len(self._models)))
        return list(self._models.values())

    def get_model(self, model_id: str) -> ModelDefinition:
        self._enter("get_model", model_id)
        if model_id not in self._models:
            self._record("get_model", model_id, error="KeyError")
            raise KeyError(f"model not found: {model_id!r}")
        self._record("get_model", model_id, result=model_id)
        return self._models[model_id]

    def save_model(self, model: ModelDefinition) -> None:
        self._enter("save_model", model.id)
        self._models[model.id] = model
        self._record("save_model", model.id)

    def delete_model(self, model_id: str) -> None:
        self._enter("delete_model", model_id)
        if model_id not in self._models:
            self._record("delete_model", model_id, error="KeyError")
            raise KeyError(f"model not found: {model_id!r}")
        del self._models[model_id]
        self._record("delete_model", model_id)