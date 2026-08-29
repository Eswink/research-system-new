"""M15 ledger corrections 测试:quantity_status 不变量、全保真 round-trip、
streaming unknown-vs-zero、attempt-scoped entry ids、失败路径记账。"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from adapters.relay.parsing import stream_result
from adapters.sqlite.budget_ledger import SqliteBudgetLedger
from packages.application.experiments.budget_entries import (
    ExperimentUsage,
    ModelUsage,
    experiment_entries,
    model_entries,
)
from packages.domain.budget import (
    LedgerCostStatus,
    LedgerQuantityStatus,
    ResourceType,
    UsageLedgerEntry,
)
from tests.contracts.fixtures import research_task

_UTC = timezone.utc
_NOW = datetime(2026, 8, 29, 12, 0, 0, tzinfo=_UTC)


def _entry(**overrides: object) -> UsageLedgerEntry:
    base: dict[str, object] = {
        "entry_id": "entry-1",
        "resource_type": ResourceType.MODEL_TOKENS,
        "quantity": 100,
        "unit": "tokens",
        "cost_status": LedgerCostStatus.KNOWN,
        "estimated_cost_minor": 7,
        "source": "llm",
        "occurred_at": _NOW,
    }
    base.update(overrides)
    return UsageLedgerEntry(**base)  # type: ignore[arg-type]


def test_unknown_quantity_requires_reason() -> None:
    with pytest.raises(ValueError, match="unavailable_reason"):
        _entry(quantity_status=LedgerQuantityStatus.UNKNOWN)
    entry = _entry(
        quantity_status=LedgerQuantityStatus.UNKNOWN,
        unavailable_reason="provider did not report usage",
    )
    assert entry.quantity_status is LedgerQuantityStatus.UNKNOWN
    assert entry.attempt == 1


def test_attempt_must_be_positive() -> None:
    with pytest.raises(ValueError, match="attempt"):
        _entry(attempt=0)


def test_sqlite_roundtrip_preserves_all_fields() -> None:
    ledger = SqliteBudgetLedger(":memory:")
    entry = _entry(
        currency="EUR",
        agent_id="agent-1",
        tool_id="tool-1",
        quantity_status=LedgerQuantityStatus.UNKNOWN,
        unavailable_reason="streaming response carried no usage chunk",
        attempt=3,
    )
    ledger.record_usage(entry)
    (decoded,) = ledger.snapshot().entries
    assert decoded.currency == "EUR"
    assert decoded.agent_id == "agent-1"
    assert decoded.tool_id == "tool-1"
    assert decoded.quantity_status is LedgerQuantityStatus.UNKNOWN
    assert decoded.unavailable_reason is not None
    assert decoded.attempt == 3


def test_legacy_rows_decode_as_known_attempt_one() -> None:
    ledger = SqliteBudgetLedger(":memory:")
    entry = _entry()
    ledger.record_usage(entry)
    (decoded,) = ledger.snapshot().entries
    assert decoded.quantity_status is LedgerQuantityStatus.KNOWN
    assert decoded.unavailable_reason is None
    assert decoded.attempt == 1


def test_streaming_result_without_usage_sets_unavailable_reason() -> None:
    result = stream_result(["partial"], [None], [None], [False], {})
    assert result.usage_reported is False
    assert result.usage_unavailable_reason is not None
    assert result.prompt_tokens is None


def test_streaming_result_with_usage_has_no_reason() -> None:
    result = stream_result(["partial"], [None], [None], [True], {})
    assert result.usage_reported is True
    assert result.usage_unavailable_reason is None


def test_model_usage_unknown_maps_to_quantity_unknown() -> None:
    entries = model_entries(
        "run-1",
        (
            ModelUsage(
                model_id="relay-model",
                prompt_tokens=0,
                completion_tokens=0,
                usage_unavailable_reason="streaming response carried no usage chunk",
            ),
        ),
        _NOW,
        task_id=None,
        agent_id=None,
    )
    tokens_entry = entries[0]
    assert tokens_entry.quantity_status is LedgerQuantityStatus.UNKNOWN
    assert tokens_entry.unavailable_reason is not None
    assert tokens_entry.quantity == 0
    assert tokens_entry.entry_id == "usage:run-1:model:relay-model"


def test_attempt_scoped_entry_ids_append_on_retry() -> None:
    first = model_entries("run-1", (ModelUsage(model_id="m"),), _NOW, task_id=None, agent_id=None)
    retry = model_entries(
        "run-1",
        (ModelUsage(model_id="m", attempt=2),),
        _NOW,
        task_id=None,
        agent_id=None,
    )
    assert first[0].entry_id == "usage:run-1:model:m"
    assert retry[0].entry_id == "usage:run-1:model:m:attempt-2"


def test_experiment_unknown_elapsed_gets_quantity_unknown() -> None:
    entries = experiment_entries("run-1", (ExperimentUsage(run_id="exec-1"),), _NOW, task_id=None)
    entry = entries[0]
    assert entry.quantity_status is LedgerQuantityStatus.UNKNOWN
    assert entry.unavailable_reason == "elapsed_seconds not observed"


def test_failure_path_records_attempt_scoped_unknown_entry() -> None:
    """失败/重试耗尽 → attempt 作用域 UNKNOWN 条目(不伪造 turn 消耗)。"""

    from packages.application.run_orchestration.usage_recording import record_attempt_usage

    ledger = SqliteBudgetLedger(":memory:")
    research = research_task()
    record_attempt_usage(ledger, research, 2, "retry budget exhausted")
    (entry,) = ledger.snapshot().entries
    assert entry.entry_id == f"usage:{research.id.value}:turns:attempt-2"
    assert entry.quantity == 0
    assert entry.quantity_status is LedgerQuantityStatus.UNKNOWN
    assert entry.unavailable_reason == "retry budget exhausted"
    assert entry.attempt == 2


def test_cancellation_records_unknown_run_entry() -> None:
    from packages.application.run_orchestration.usage_recording import record_cancelled_usage

    ledger = SqliteBudgetLedger(":memory:")
    record_cancelled_usage(ledger, "run-1", 3)
    (entry,) = ledger.snapshot().entries
    assert entry.entry_id == "usage:run-1:cancelled:3"
    assert entry.quantity == 3
    assert entry.quantity_status is LedgerQuantityStatus.UNKNOWN
