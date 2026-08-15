"""实验输出解析纯函数测试（M9）。"""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

from packages.application.experiments.metric_extraction import (
    parse_experiment_result_json,
)
from packages.application.ports.errors import InvalidInputError
from packages.domain.experiments import MetricKind

_RUN_ID = "7a2b3c4d-5e6f-4a5b-9c0d-1e2f3a4b5c6d"


def _payload(**overrides: object) -> str:
    data: dict[str, object] = {
        "experiment_run_id": _RUN_ID,
        "status": "SUCCEEDED",
        "artifact_refs": ["chart.png"],
        "metrics": {"accuracy": 0.91, "note": "stable", "converged": True, "extra": None},
        **overrides,
    }
    return json.dumps(data)


class TestParseExperimentResult:
    def test_valid_payload(self) -> None:
        payload = parse_experiment_result_json(_payload(), expected_run_id=_RUN_ID)
        assert payload.declared_status == "SUCCEEDED"
        assert payload.artifact_refs == ("chart.png",)
        assert [value.metric.name for value in payload.metric_values] == [
            "accuracy",
            "converged",
            "extra",
            "note",
        ]
        accuracy = payload.metric_values[0]
        assert accuracy.metric.kind is MetricKind.NUMBER
        assert accuracy.value == Decimal("0.91")
        assert payload.metrics_digest is not None

    def test_negative_result_status(self) -> None:
        payload = parse_experiment_result_json(
            _payload(status="NEGATIVE_RESULT", failure_ref="p=0.42"),
            expected_run_id=_RUN_ID,
        )
        assert payload.declared_status == "NEGATIVE_RESULT"
        assert payload.failure_ref == "p=0.42"

    def test_run_id_mismatch_rejected(self) -> None:
        with pytest.raises(InvalidInputError):
            parse_experiment_result_json(_payload(), expected_run_id="other-id")

    def test_invalid_json_rejected(self) -> None:
        with pytest.raises(InvalidInputError):
            parse_experiment_result_json("{not json", expected_run_id=_RUN_ID)

    def test_non_object_rejected(self) -> None:
        with pytest.raises(InvalidInputError):
            parse_experiment_result_json("[1,2]", expected_run_id=_RUN_ID)

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(InvalidInputError):
            parse_experiment_result_json(_payload(status="MAYBE"), expected_run_id=_RUN_ID)

    def test_missing_metrics_rejected(self) -> None:
        data = json.loads(_payload())
        del data["metrics"]
        with pytest.raises(InvalidInputError):
            parse_experiment_result_json(json.dumps(data), expected_run_id=_RUN_ID)

    def test_non_list_artifact_refs_rejected(self) -> None:
        with pytest.raises(InvalidInputError):
            parse_experiment_result_json(
                _payload(artifact_refs="chart.png"), expected_run_id=_RUN_ID
            )

    def test_unsupported_metric_value_rejected(self) -> None:
        with pytest.raises(InvalidInputError):
            parse_experiment_result_json(
                _payload(metrics={"nested": {"a": 1}}), expected_run_id=_RUN_ID
            )
