"""M17 WP5a tests: GPU_TIME ledger entries (first real consumer of the enum).

- measured GPU seconds → a GPU_TIME entry with KNOWN quantity, UNKNOWN cost
  (never 0, reason recorded), idempotent entry id distinct from CPU_TIME;
- no measured GPU time → no GPU_TIME entry at all (no fabrication);
- summarize() reports gpu_seconds.
"""

from __future__ import annotations

from datetime import datetime, timezone

from packages.application.experiments.budget_entries import (
    ExperimentUsage,
    experiment_entries,
    summarize,
)
from packages.domain.budget import LedgerCostStatus, LedgerQuantityStatus, ResourceType

_NOW = datetime(2026, 9, 2, tzinfo=timezone.utc)


def test_gpu_time_entry_created_from_measured_seconds() -> None:
    entries = experiment_entries(
        "run-1",
        (
            ExperimentUsage(
                run_id="exec-1",
                elapsed_seconds=42,
                gpu_elapsed_seconds=31,
                peak_gpu_memory_bytes=123_456,
            ),
        ),
        _NOW,
        task_id="task-1",
    )
    gpu = [e for e in entries if e.resource_type is ResourceType.GPU_TIME]
    cpu = [e for e in entries if e.resource_type is ResourceType.CPU_TIME]
    assert len(gpu) == 1 and len(cpu) == 1
    entry = gpu[0]
    assert entry.quantity == 31
    assert entry.unit == "seconds"
    assert entry.quantity_status is LedgerQuantityStatus.KNOWN
    # 诚实记账：无定价源 → 成本 UNKNOWN，绝不写 0
    assert entry.cost_status is LedgerCostStatus.UNKNOWN
    assert entry.estimated_cost_minor is None
    assert entry.actual_cost_minor is None
    assert entry.unavailable_reason == ExperimentUsage.GPU_COST_UNAVAILABLE_REASON
    assert entry.entry_id.endswith(":gpu")
    assert entry.task_id == "task-1"


def test_no_gpu_measurement_creates_no_gpu_time_entry() -> None:
    entries = experiment_entries(
        "run-1",
        (ExperimentUsage(run_id="exec-1", elapsed_seconds=42),),
        _NOW,
        task_id=None,
    )
    assert not [e for e in entries if e.resource_type is ResourceType.GPU_TIME]


def test_gpu_entry_id_does_not_collide_with_cpu_entry() -> None:
    entries = experiment_entries(
        "run-1",
        (ExperimentUsage(run_id="exec-1", elapsed_seconds=9, gpu_elapsed_seconds=7),),
        _NOW,
        task_id=None,
    )
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_attempt_scoping_extends_gpu_entry_id() -> None:
    first = experiment_entries(
        "run-1", (ExperimentUsage(run_id="exec-1", gpu_elapsed_seconds=7),), _NOW, None
    )
    retry = experiment_entries(
        "run-1", (ExperimentUsage(run_id="exec-1", gpu_elapsed_seconds=7, attempt=2),), _NOW, None
    )
    assert first[1].entry_id != retry[1].entry_id
    assert retry[1].entry_id.endswith(":attempt-2")


def test_summarize_reports_gpu_seconds() -> None:
    entries = experiment_entries(
        "run-1",
        (ExperimentUsage(run_id="exec-1", elapsed_seconds=5, gpu_elapsed_seconds=3),),
        _NOW,
        None,
    )
    summary = summarize(entries)
    assert summary.gpu_seconds == 3
    assert summary.experiment_seconds == 5
