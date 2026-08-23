"""M12 Budget Closure 测试：四源用量闭环 + reservation/actual 对账 + 硬限阻断。"""

from __future__ import annotations

from adapters.fakes import FakeBudgetLedger
from packages.application.experiments.budget_closure import (
    BudgetClosureInput,
    BudgetExhaustedError,
    EvaluationUsage,
    ExperimentUsage,
    ModelUsage,
    ToolUsage,
    close_budget,
)
from packages.domain.budget import BudgetPolicy, BudgetReservation, LedgerCostStatus, ResourceType

RUN_ID = "12121212-2222-4333-8444-555555555555"


def _input() -> BudgetClosureInput:
    return BudgetClosureInput(
        run_id=RUN_ID,
        model_usage=(
            ModelUsage(
                model_id="research_alpha",
                prompt_tokens=1200,
                completion_tokens=800,
                calls=3,
                estimated_cost_minor=42,
            ),
        ),
        tool_usage=(ToolUsage(tool_id="literature_search", requests=2),),
        experiment_usage=(
            ExperimentUsage(
                run_id="exp-1",
                image_digest="sha256:" + "ab" * 32,
                elapsed_seconds=45,
            ),
        ),
        evaluation_usage=(
            EvaluationUsage(eval_id="m12_research_v1", cases=10, scorer_calls=10),
        ),
    )


class TestBudgetClosure:
    def test_four_sources_closed_to_ledger(self) -> None:
        ledger = FakeBudgetLedger()
        result = close_budget(ledger, input=_input())
        assert result.total_tokens == 2000
        assert result.tool_requests == 2
        assert result.experiment_runs == 1
        assert result.evaluation_cases == 10
        snapshot = ledger.snapshot()
        entries = snapshot.entries
        # model tokens + model calls + tool + experiment + eval = 5 entries
        assert len(entries) == 5
        by_type = {entry.resource_type for entry in entries}
        assert ResourceType.MODEL_TOKENS in by_type
        assert ResourceType.MODEL_REQUESTS in by_type
        assert ResourceType.TOOL_REQUESTS in by_type
        assert ResourceType.CPU_TIME in by_type

    def test_cost_known_only_when_estimated(self) -> None:
        ledger = FakeBudgetLedger()
        result = close_budget(ledger, input=_input())
        model_entry = next(
            entry
            for entry in result.entries
            if entry.resource_type is ResourceType.MODEL_TOKENS
        )
        assert model_entry.cost_status is LedgerCostStatus.KNOWN
        assert model_entry.estimated_cost_minor == 42
        tool_entry = next(
            entry for entry in result.entries if entry.resource_type is ResourceType.TOOL_REQUESTS
        )
        assert tool_entry.cost_status is LedgerCostStatus.UNKNOWN

    def test_hard_limit_blocks(self) -> None:
        ledger = FakeBudgetLedger()
        policy = BudgetPolicy(id="m12-policy", hard_limits={"model_tokens": 100})
        try:
            close_budget(ledger, input=_input(), policy=policy)
            raise AssertionError("expected BudgetExhaustedError")
        except BudgetExhaustedError as exc:
            assert "model token budget exhausted" in str(exc)
        # 突破硬限 → budget failure，不产生任何 entry（先检查后记账）
        assert ledger.snapshot().entries == ()

    def test_reservation_actual_consistency(self) -> None:
        ledger = FakeBudgetLedger()
        policy = BudgetPolicy(id="m12-policy", hard_limits={"model_tokens": 10000})
        ref = ledger.reserve(
            (
                BudgetReservation(
                    id="budget:m12:model_tokens",
                    scope="phase:execution",
                    resource_type=ResourceType.MODEL_TOKENS,
                    quantity=5000,
                    unit="tokens",
                ),
            ),
            policy,
        )
        result = close_budget(ledger, input=_input(), policy=policy, reservation_ref=ref)
        assert result.reservation_actual_consistent is True

    def test_reservation_exceeded_inconsistent(self) -> None:
        ledger = FakeBudgetLedger()
        policy = BudgetPolicy(id="m12-policy", hard_limits={"model_tokens": 10000})
        ref = ledger.reserve(
            (
                BudgetReservation(
                    id="budget:m12:model_tokens",
                    scope="phase:execution",
                    resource_type=ResourceType.MODEL_TOKENS,
                    quantity=100,
                    unit="tokens",
                ),
            ),
            policy,
        )
        result = close_budget(ledger, input=_input(), policy=policy, reservation_ref=ref)
        assert result.reservation_actual_consistent is False

    def test_duplicate_entry_id_rejected(self) -> None:
        ledger = FakeBudgetLedger()
        close_budget(ledger, input=_input())
        try:
            close_budget(ledger, input=_input())
            raise AssertionError("expected duplicate entry rejection")
        except Exception:
            pass