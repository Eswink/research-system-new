"""Usage 真实接线（M12-R1 WP6）：真实事件 → UsageLedger → Budget 闭环。

验证：
- ModelUsage 从 CompletionResult.usage 明细归集（不再手工 1200/800）；
- provider 不返回 usage → 显式 UNKNOWN，不伪造数字；
- ToolUsage 从 ToolResultRecord 计数；
- EvaluationUsage 从 EvalReport 实际 cases/scorer_calls（deterministic 无虚构 LLM）；
- retry 重放不 double-count（ledger.append 拒绝重复 entry_id）；
- re-eval 追加独立 entry（不漏账）。
"""

from __future__ import annotations

import pytest

from adapters.fakes import FakeBudgetLedger
from packages.application.experiments.usage_collection import (
    UsageCollection,
    collect_usage,
    record_collected_usage,
)
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.model_gateway import CompletionResult
from packages.domain.core import Digest, Timestamp, Version
from packages.domain.enums import QualityGateVerdict, ToolResultStatus
from packages.domain.eval_result import (
    EvalFindingStatus,
    EvalReport,
    EvalResult,
    FrozenConditions,
    ScorerFinding,
)
from packages.domain.eval_spec import EvalScope
from packages.domain.experiments import ExperimentRunResult
from packages.domain.tools import ToolResultRecord

RUN_ID = "12121212-2222-4333-8444-555555555555"


def _completion(*, with_usage: bool = True) -> CompletionResult:
    if with_usage:
        return CompletionResult(
            content="ok",
            returned_model_name="muse-spark-1.2-contributor",
            usage_reported=True,
            prompt_tokens=1200,
            completion_tokens=800,
            total_tokens=2000,
        )
    return CompletionResult(
        content="ok",
        returned_model_name="muse-spark-1.2-contributor",
        usage_reported=False,
        usage_unavailable_reason="provider did not return usage",
    )


def _tool_result(tool_id: str = "literature_search") -> ToolResultRecord:
    return ToolResultRecord(
        task_id="task-1",
        attempt=1,
        operation_key="op-1",
        tool_id=tool_id,
        status=ToolResultStatus.SUCCEEDED,
        output_digest=Digest.of_bytes(b"result"),
        recorded_at=Timestamp.now(),
    )


def _experiment_result() -> ExperimentRunResult:
    return ExperimentRunResult(execution_run_id="exec-1", image_digest="sha256:image")


def _eval_report(report_id: str = "eval:m12") -> EvalReport:
    return EvalReport(
        report_id=report_id,
        generated_at="offline",
        mode="OFFLINE_FAKE",
        scope=EvalScope.WORKFLOW,
        gate_verdict=QualityGateVerdict.PASS,
        frozen_conditions=FrozenConditions(
            dataset_id="m12_research_v1",
            dataset_version=Version("1.0.0"),
            dataset_digest=Digest.of_bytes(b"ds"),
            gate_config_id="gate",
            gate_config_version=Version("1.0.0"),
            gate_config_digest=Digest.of_bytes(b"gate"),
            system_version="0.4.0",
            scorer_versions={"exact_match": "1.0.0"},
            input_digests={},
        ),
        results=(
            EvalResult(
                case_id="case-1",
                case_version=Version("1.0.0"),
                case_digest=Digest.of_bytes(b"case"),
                scope=EvalScope.WORKFLOW,
                input_ref="input://m12/task_completion",
                scorer_findings=(
                    ScorerFinding(
                        scorer_id="exact_match",
                        scorer_version=Version("1.0.0"),
                        case_id="case-1",
                        status=EvalFindingStatus.PASS,
                        detail="ok",
                    ),
                ),
            ),
        ),
    )


class TestUsageCollection:
    def test_model_usage_from_real_completion(self) -> None:
        closure_input, summary = collect_usage(
            UsageCollection(
                run_id=RUN_ID,
                model_id="research_alpha",
                model_completions=(_completion(),),
            )
        )
        assert summary.model_tokens == 2000
        assert summary.model_requests == 1
        usage = closure_input.model_usage[0]
        assert usage.prompt_tokens == 1200
        assert usage.completion_tokens == 800
        assert usage.calls == 1
        assert usage.model_id == "research_alpha"

    def test_missing_usage_is_unknown_not_fabricated(self) -> None:
        closure_input, summary = collect_usage(
            UsageCollection(
                run_id=RUN_ID,
                model_id="research_alpha",
                model_completions=(_completion(with_usage=False),),
            )
        )
        assert summary.model_usage_unknown is True
        usage = closure_input.model_usage[0]
        # 不伪造 1200：tokens 归零 + 调用方可见 UNKNOWN 语义
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.calls == 1

    def test_tool_usage_counts_real_results(self) -> None:
        closure_input, summary = collect_usage(
            UsageCollection(
                run_id=RUN_ID,
                tool_results=(_tool_result(), _tool_result(), _tool_result("literature_read")),
            )
        )
        assert summary.tool_requests == 3
        assert closure_input.tool_usage == (
            __import__(
                "packages.application.experiments.budget_closure", fromlist=["ToolUsage"]
            ).ToolUsage(tool_id="literature_read", requests=1),
            __import__(
                "packages.application.experiments.budget_closure", fromlist=["ToolUsage"]
            ).ToolUsage(tool_id="literature_search", requests=2),
        )

    def test_evaluation_usage_from_actual_report(self) -> None:
        closure_input, summary = collect_usage(
            UsageCollection(run_id=RUN_ID, eval_report=_eval_report())
        )
        assert summary.eval_cases == 1
        assert summary.eval_scorer_calls == 1
        eval_usage = closure_input.evaluation_usage[0]
        assert eval_usage.cases == 1
        assert eval_usage.scorer_calls == 1
        # deterministic scorer：不虚构 LLM evaluation usage（无 token 入账）
        assert summary.model_tokens == 0
        assert summary.model_requests == 0

    def test_retry_does_not_double_count(self) -> None:
        ledger = FakeBudgetLedger()
        collection = UsageCollection(
            run_id=RUN_ID,
            model_id="research_alpha",
            model_completions=(_completion(),),
            tool_results=(_tool_result(),),
        )
        first = record_collected_usage(ledger, collection)
        # retry 重放同一事件：重复 entry_id → 拒绝（at-least-once 语义不漏不重）
        with pytest.raises(InvalidInputError, match="duplicate"):
            record_collected_usage(ledger, collection)
        snapshot = ledger.snapshot()
        assert first.model_tokens == 2000
        model_entries: list[object] = [
            entry
            for entry in snapshot.entries
            if entry.entry_id.startswith(f"usage:{RUN_ID}:model:")
        ]
        assert len(model_entries) == 2  # tokens + calls

    def test_re_evaluation_appends_independent_entries(self) -> None:
        ledger = FakeBudgetLedger()
        record_collected_usage(
            ledger,
            UsageCollection(run_id=RUN_ID, eval_report=_eval_report("eval:m12:run-1")),
        )
        record_collected_usage(
            ledger,
            UsageCollection(run_id=RUN_ID, eval_report=_eval_report("eval:m12:run-2")),
        )
        entries = [
            entry
            for entry in ledger.snapshot().entries
            if entry.entry_id.startswith(f"usage:{RUN_ID}:eval:")
        ]
        assert len(entries) == 2  # 两次评测各一条，不漏账
        assert entries[0].entry_id != entries[1].entry_id
