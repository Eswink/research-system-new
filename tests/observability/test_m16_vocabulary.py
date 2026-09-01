"""M16 WP4 telemetry vocabulary audit: cardinality + privacy boundaries.

Proves the distributed-execution vocabulary increments stay closed-set and
cannot carry worker tokens, raw worker ids, bundle contents, or unbounded
values (mirrors the M15 canary approach at the vocabulary level).
"""

from __future__ import annotations

import pytest

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


def test_bundle_content_never_survives_attribute_sanitization() -> None:
    """F-9: workspace-bundle content cannot ride the closed attribute vocabulary.

    sanitize_attributes keeps only closed-set keys, so an arbitrary content key
    is dropped outright; metric labels additionally fold out-of-domain values.
    Value-level secret redaction for the surviving keys is proven end-to-end by
    the OTLP byte-scan canary (test_privacy_canary), which now covers the M16
    worker/remote-execution channels too.
    """
    sanitized = sanitize_attributes({"bundle_content": _BUNDLE_MARK})
    assert "bundle_content" not in sanitized  # non-vocabulary key dropped
    folded = sanitize_metric_labels({"rejection_reason": _BUNDLE_MARK})
    assert folded["rejection_reason"] == "other"  # out-of-domain value folded


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


def test_no_second_remote_exec_usage_namespace() -> None:
    """M16 re-audit F-5: remote execution has no dedicated usage namespace.

    Its wall clock is server-measured (RemoteExecutionBackend.compute_usage_summary
    ["elapsed_seconds"], asserted in tests/adapters/execution/test_remote_backend.py)
    and flows through the single experiment path; a
    `usage:{run}:remote-exec:{task}` counter would be a second truth.
    """
    import packages.application.experiments.budget_entries as budget_entries

    assert not hasattr(budget_entries, "remote_execution_entries")
    assert "remote_execution_entries" not in budget_entries.__all__
    # the experiment path is the sole WALL_CLOCK producer for executions
    assert "experiment_entries" in budget_entries.__all__
