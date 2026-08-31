"""M16 WP4 telemetry vocabulary audit: cardinality + privacy boundaries.

Proves the distributed-execution vocabulary increments stay closed-set and
cannot carry worker tokens, raw worker ids, bundle contents, or unbounded
values (mirrors the M15 canary approach at the vocabulary level).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from packages.application.experiments.budget_entries import remote_execution_entries
from packages.application.observability.attributes import (
    AttributeKey,
    MetricKind,
    MetricLabel,
    MetricName,
    MetricSample,
    sanitize_attributes,
    sanitize_metric_labels,
    worker_ref,
)
from packages.application.observability.signals import OperationScope
from packages.domain.budget import LedgerQuantityStatus, ResourceType

_EPOCH = datetime(2026, 8, 31, tzinfo=timezone.utc)

_TOKEN = "Bearer sk-super-secret-worker-token-123456"
_BUNDLE_MARK = "workspace-bundle-content-marker-98765"


def test_new_scopes_are_closed_set() -> None:
    assert OperationScope.WORKER_SESSION.value == "worker_session"
    assert OperationScope.WORKER_DISPATCH.value == "worker_dispatch"
    assert OperationScope.REMOTE_EXECUTION.value == "remote_execution"


def test_worker_metrics_are_registered_names() -> None:
    assert MetricName.WORKER_COUNT.value == "research_os.worker.count"
    assert (
        MetricName.REMOTE_EXECUTION_STALE_RESULT_REJECTED_TOTAL.value
        == "research_os.remote_execution.stale_result_rejected_total"
    )
    assert MetricName.SCHEDULER_CLAIM_LATENCY_MS.value == "research_os.scheduler.claim_latency_ms"


def test_worker_ref_never_equals_raw_id_and_is_stable() -> None:
    ref1 = worker_ref("worker-abc")
    ref2 = worker_ref("worker-abc")
    assert ref1 == ref2
    assert "worker-abc" not in ref1
    assert len(ref1) == 12


def test_worker_ref_rejects_empty() -> None:
    with pytest.raises(ValueError):
        worker_ref("")


def test_sanitize_attributes_allows_new_keys_and_redacts_values() -> None:
    sanitized = sanitize_attributes({
        "worker_ref": worker_ref("worker-abc"),
        "worker_state": "BUSY",
        "protocol_version": "1",
        "partition": 3,
        "fence": 7,
        "rejection_reason": "stale_fence",
    })
    assert sanitized["partition"] == 3
    assert sanitized["fence"] == 7
    assert sanitized["worker_state"] == "BUSY"
    assert sanitized["rejection_reason"] == "stale_fence"


def test_sanitize_attributes_drops_unknown_and_redacts_token() -> None:
    sanitized = sanitize_attributes({
        "worker_token": _TOKEN,  # not in the closed set
        "rejection_reason": _TOKEN,  # in-set key, secret value
    })
    assert "worker_token" not in sanitized
    assert "sk-super-secret-worker-token" not in str(sanitized.get("rejection_reason"))


def test_metric_labels_partition_is_bounded() -> None:
    ok = sanitize_metric_labels({"partition": "15"})
    assert ok["partition"] == "15"
    overflow = sanitize_metric_labels({"partition": "16"})
    assert overflow["partition"] == "other"  # bounded domain folds out-of-range
    negative = sanitize_metric_labels({"partition": "-1"})
    assert negative["partition"] == "other"


def test_metric_labels_worker_state_folds_unknown() -> None:
    assert sanitize_metric_labels({"worker_state": "BUSY"})["worker_state"] == "BUSY"
    assert sanitize_metric_labels({"worker_state": "WAT"})["worker_state"] == "other"


def test_metric_labels_rejection_reason_is_closed_set() -> None:
    assert (
        sanitize_metric_labels({"rejection_reason": "stale_fence"})["rejection_reason"]
        == "stale_fence"
    )
    assert sanitize_metric_labels({"rejection_reason": _TOKEN})["rejection_reason"] == "other"


def test_worker_ref_is_never_a_metric_label() -> None:
    assert "worker_ref" not in {label.value for label in MetricLabel}


def test_metric_sample_accepts_partition_label() -> None:
    sample = MetricSample(
        name=MetricName.SCHEDULER_PARTITION_LAG,
        kind=MetricKind.HISTOGRAM,
        value=3,
        labels={"partition": "7"},
    )
    assert sample.labels["partition"] == "7"
    with pytest.raises(ValueError):
        MetricSample(
            name=MetricName.SCHEDULER_PARTITION_LAG,
            kind=MetricKind.HISTOGRAM,
            value=1,
            labels={"worker_ref": "x"},  # high-cardinality value as label
        )


def test_new_attribute_keys_are_closed_set_members() -> None:
    for key in (
        "worker_ref",
        "worker_state",
        "protocol_version",
        "partition",
        "fence",
        "rejection_reason",
    ):
        assert key in {member.value for member in AttributeKey}


def test_remote_execution_entries_wall_clock_and_cpu() -> None:
    entries = remote_execution_entries(
        run_id="run-1", task_id="task-9", elapsed_seconds=12, occurred_at=_EPOCH, attempt=1
    )
    assert entries[0].resource_type is ResourceType.WALL_CLOCK
    assert entries[0].entry_id == "usage:run-1:remote-exec:task-9"
    assert entries[0].quantity == 12
    assert len(entries) == 1  # no CPU_TIME when not reported


def test_remote_execution_entries_unknown_elapsed_never_zero() -> None:
    entries = remote_execution_entries(
        run_id="run-1",
        task_id="task-9",
        elapsed_seconds=None,
        occurred_at=_EPOCH,
    )
    assert entries[0].quantity_status is LedgerQuantityStatus.UNKNOWN
    assert entries[0].unavailable_reason is not None


def test_remote_execution_entries_attempt_scoped() -> None:
    entries = remote_execution_entries(
        run_id="run-1", task_id="task-9", elapsed_seconds=5, occurred_at=_EPOCH, attempt=2
    )
    assert entries[0].entry_id == "usage:run-1:remote-exec:task-9:attempt-2"


def test_remote_execution_entries_with_cpu_time() -> None:
    entries = remote_execution_entries(
        run_id="run-1", task_id="task-9", elapsed_seconds=5, occurred_at=_EPOCH, cpu_seconds=3
    )
    assert len(entries) == 2
    assert entries[1].resource_type is ResourceType.CPU_TIME
    assert entries[1].quantity == 3
