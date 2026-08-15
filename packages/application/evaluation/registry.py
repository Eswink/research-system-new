"""M11 EvalCase/EvalDataset 构造与 freeze digest 校验（纯函数，无 I/O）。

文件加载在 adapters/contracts/eval_loaders.py（遵循仓库 adapter 边界）；
本模块只做 dict → domain 对象构造与 digest 防篡改校验。
约束：
- 声明 digest 与重算不一致时 fail-closed（拒绝运行）；
- case 列表与输入映射的成员一致性在 runner 对账，本模块负责身份。
"""

from __future__ import annotations

from typing import Mapping

from packages.domain.core import Digest, Version
from packages.domain.eval_spec import (
    EvalCase,
    EvalDataset,
    EvalDeterminism,
    EvalScope,
    RubricSpec,
    ScorerRef,
)

_DEFAULT_SCALE = (1, 5)


class DatasetFreezeError(ValueError):
    """dataset 声明内容与 freeze digest 不一致。"""


def dataset_from_dict(data: Mapping[str, object], declared_digest: str) -> EvalDataset:
    """由嵌套 map（key 即 id）构造冻结 dataset 并校验 digest。"""

    dataset = build_dataset(data)
    actual = dataset.digest()
    expected = Digest.parse(declared_digest)
    if actual != expected:
        raise DatasetFreezeError(
            f"dataset {dataset.id} freeze mismatch: declared {expected} != computed {actual}"
        )
    return dataset


def build_dataset(data: Mapping[str, object]) -> EvalDataset:
    """纯构造（不校验 freeze digest）；供工具/离线重算 digest 使用。"""

    dataset_id = _require_str(data, "id")
    version = Version(_require_str(data, "version"))
    description = _require_str(data, "description")
    raw_cases = data.get("cases")
    if not isinstance(raw_cases, dict) or not raw_cases:
        raise ValueError(f"dataset {dataset_id}: cases must be a non-empty mapping")
    cases = tuple(
        _case_from_dict(dataset_id, case_id, _require_mapping(raw_cases, case_id))
        for case_id in sorted(str(key) for key in raw_cases)
    )
    return EvalDataset(
        id=dataset_id,
        version=version,
        cases=cases,
        description=description,
    )


def _case_from_dict(dataset_id: str, case_id: str, data: Mapping[str, object]) -> EvalCase:
    version = Version(_require_str(data, "version"))
    scope = EvalScope(_require_str(data, "scope"))
    input_ref = _require_str(data, "input_ref")
    expected = data.get("expected")
    raw_rubric = data.get("rubric", [])
    if not isinstance(raw_rubric, list):
        raise ValueError(f"dataset {dataset_id} case {case_id}: rubric must be a list")
    rubric = tuple(_rubric_from_dict(item) for item in raw_rubric)
    raw_artifacts = data.get("required_artifact_digests", [])
    if not isinstance(raw_artifacts, list):
        raise ValueError(f"dataset {dataset_id} case {case_id}: artifact digests must be a list")
    required_artifacts = tuple(_require_str_item(raw_artifacts, case_id))
    raw_refs = data.get("scorer_refs")
    if not isinstance(raw_refs, list) or not raw_refs:
        raise ValueError(
            f"dataset {dataset_id} case {case_id}: scorer_refs must be a non-empty list"
        )
    refs = tuple(_scorer_ref_from_dict(item, case_id) for item in raw_refs)
    raw_determinism = data.get("determinism", "DETERMINISTIC")
    if not isinstance(raw_determinism, str):
        raise ValueError(f"dataset {dataset_id} case {case_id}: determinism must be a string")
    determinism = EvalDeterminism(raw_determinism)
    raw_tags = data.get("tags", [])
    if not isinstance(raw_tags, list):
        raise ValueError(f"dataset {dataset_id} case {case_id}: tags must be a list")
    tags = tuple(_require_str_item(raw_tags, case_id))
    provenance = data.get("provenance", "")
    if not isinstance(provenance, str):
        raise ValueError(f"dataset {dataset_id} case {case_id}: provenance must be a string")
    description = data.get("description", "")
    if not isinstance(description, str):
        raise ValueError(f"dataset {dataset_id} case {case_id}: description must be a string")
    return EvalCase(
        id=case_id,
        version=version,
        scope=scope,
        input_ref=input_ref,
        expected=expected,
        rubric=rubric,
        required_artifact_digests=required_artifacts,
        scorer_refs=refs,
        determinism=determinism,
        tags=tags,
        provenance=provenance,
        description=description,
    )


def _rubric_from_dict(item: object) -> RubricSpec:
    if not isinstance(item, dict):
        raise ValueError("rubric entry must be a mapping")
    scale_value = item.get("scale", list(_DEFAULT_SCALE))
    if not isinstance(scale_value, list) or len(scale_value) != 2:
        raise ValueError("rubric scale must be a two-item list")
    if not all(isinstance(value, int) for value in scale_value):
        raise ValueError("rubric scale items must be integers")
    return RubricSpec(
        id=_require_str(item, "id"),
        dimension=_require_str(item, "dimension"),
        description=_require_str(item, "description"),
        scale=(int(scale_value[0]), int(scale_value[1])),
    )


def _scorer_ref_from_dict(item: object, case_id: str) -> ScorerRef:
    if not isinstance(item, dict):
        raise ValueError(f"case {case_id}: scorer_ref must be a mapping")
    return ScorerRef(
        scorer_id=_require_str(item, "scorer_id"),
        version=Version(_require_str(item, "version")),
    )


def _require_str_item(items: list[object], case_id: str) -> tuple[str, ...]:
    if not all(isinstance(item, str) and item for item in items):
        raise ValueError(f"case {case_id}: list items must be non-empty strings")
    return tuple(str(item) for item in items)


def _require_str(data: Mapping[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ValueError(f"field {key!r} must be a string")
    return value


def _require_mapping(data: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"field {key!r} must be a mapping")
    return value
