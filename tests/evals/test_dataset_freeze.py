"""M11 dataset freeze / 防篡改测试：改内容、缺版本、删 case、重复 case。"""

from __future__ import annotations

import pathlib

import pytest
import yaml

from adapters.contracts.base import ContractLoadError
from adapters.contracts.eval_loaders import load_eval_dataset
from packages.application.evaluation.registry import (
    DatasetFreezeError,
    build_dataset,
    dataset_from_dict,
)

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_UNIT_PATH = "examples/eval/datasets/unit_v1.yaml"


def _unit_payload() -> dict[str, object]:
    data = yaml.safe_load((_ROOT / _UNIT_PATH).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return {**data, "id": "unit_v1"}


def _first_case(payload: dict[str, object]) -> tuple[str, dict[str, object]]:
    cases = payload["cases"]
    assert isinstance(cases, dict)
    case_id = sorted(str(key) for key in cases)[0]
    case = cases[case_id]
    assert isinstance(case, dict)
    return case_id, case


def test_unit_dataset_loads_with_freeze_digest() -> None:
    dataset = load_eval_dataset(_UNIT_PATH)
    assert dataset.id == "unit_v1"
    assert dataset.version.text == "1.0.0"
    assert len(dataset.cases) == 5
    assert any("canary" in case.tags for case in dataset.cases)


def test_integration_dataset_loads() -> None:
    dataset = load_eval_dataset("examples/eval/datasets/integration_v1.yaml")
    assert dataset.id == "integration_v1"
    assert len(dataset.cases) == 2


def test_changed_case_content_is_rejected() -> None:
    payload = _unit_payload()
    _, case = _first_case(payload)
    case["expected"] = {"answer": 43}
    with pytest.raises(DatasetFreezeError):
        dataset_from_dict(payload, str(payload["digest"]))


def test_removed_case_is_rejected() -> None:
    payload = _unit_payload()
    cases = payload["cases"]
    assert isinstance(cases, dict)
    del cases[sorted(str(key) for key in cases)[-1]]
    with pytest.raises(DatasetFreezeError):
        dataset_from_dict(payload, str(payload["digest"]))


def test_added_case_is_rejected() -> None:
    payload = _unit_payload()
    case_id, case = _first_case(payload)
    cases = payload["cases"]
    assert isinstance(cases, dict)
    cases[f"{case_id}_sneaky"] = {**case, "version": "1.0.1"}
    with pytest.raises(DatasetFreezeError):
        dataset_from_dict(payload, str(payload["digest"]))


def test_version_change_is_rejected() -> None:
    payload = _unit_payload()
    payload["version"] = "1.0.1"
    with pytest.raises(DatasetFreezeError):
        dataset_from_dict(payload, str(payload["digest"]))


def test_missing_dataset_version_is_rejected() -> None:
    payload = _unit_payload()
    del payload["version"]
    with pytest.raises(ValueError, match="version"):
        build_dataset(payload)


def test_corrupt_digest_literal_is_rejected() -> None:
    payload = _unit_payload()
    with pytest.raises(ValueError, match="digest literal"):
        dataset_from_dict(payload, "not-a-digest")


def test_loader_rejects_schema_violation() -> None:
    with pytest.raises(ContractLoadError, match="scope"):
        load_eval_dataset("tests/evals/fixtures/dataset_bad_scope.yaml")


def test_loader_rejects_missing_file() -> None:
    with pytest.raises(ContractLoadError, match="file not found"):
        load_eval_dataset("tests/evals/fixtures/does_not_exist.yaml")
