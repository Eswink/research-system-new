"""M11 EvalDataset 文件加载器（adapter 边界：文件 I/O 与 JSON Schema 校验）。

遵循 adapters/contracts/base.py 基建：UTF-8 读取、jsonschema Draft202012
校验、ContractLoadError 错误模型。dataset 声明 digest 与实际内容的
freeze 校验由 application registry 完成（本模块只保证格式合法）。
"""

from __future__ import annotations

from typing import Any

from adapters.contracts.base import (
    ContractLoadError,
    load_json_schema,
    load_yaml,
    validate_instance,
)
from packages.application.evaluation.registry import dataset_from_dict
from packages.domain.eval_spec import EvalDataset

_DATASET_SCHEMA = "eval-dataset.schema.json"


def load_eval_dataset(relative_path: str) -> EvalDataset:
    """加载并校验一个 dataset 文件，构造冻结的 EvalDataset。"""

    data = load_yaml(relative_path)
    validate_instance(load_json_schema(_DATASET_SCHEMA), data, relative_path)
    if not isinstance(data, dict):
        raise ContractLoadError(f"{relative_path} must be a mapping")
    dataset_id = relative_path.rsplit("/", 1)[-1].removesuffix(".yaml")
    payload: dict[str, Any] = {**data, "id": dataset_id}
    try:
        return dataset_from_dict(payload, str(data["digest"]))
    except ValueError as exc:
        raise ContractLoadError(f"invalid dataset at {relative_path}: {exc}") from exc
