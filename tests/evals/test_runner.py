"""M11 EvalRunner 测试：replay、隔离、异常不转 PASS、输入对账。"""

from __future__ import annotations

from decimal import Decimal

from packages.application.evaluation.runner import (
    RunnerOutcome,
    RunRequest,
    run_evaluation,
)
from packages.application.evaluation.scorer_types import (
    InvariantPredicate,
    ScorerContext,
    ScorerFn,
)
from packages.domain.core import Version
from packages.domain.enums import QualityGateVerdict
from packages.domain.eval_gate import GateConfig
from packages.domain.eval_result import EvalFindingStatus, ScorerFinding
from packages.domain.eval_spec import (
    EvalCase,
    EvalDataset,
    EvalScope,
    ScorerRef,
)


def _case(case_id: str, expected: object) -> EvalCase:
    return EvalCase(
        id=case_id,
        version=Version("1.0.0"),
        scope=EvalScope.UNIT,
        input_ref=f"input://{case_id}",
        expected=expected,
        scorer_refs=(ScorerRef("exact_match", Version("1.0.0")),),
    )


def _dataset() -> EvalDataset:
    return EvalDataset(
        id="runner-ds",
        version=Version("1.0.0"),
        cases=(_case("c1", {"answer": 42}), _case("c2", {"answer": 7})),
    )


def _config() -> GateConfig:
    return GateConfig(id="gate", version=Version("1.0.0"))


def _request(
    *,
    dataset: EvalDataset | None = None,
    config: GateConfig | None = None,
    inputs: dict[str, object] | None = None,
    runtime_scorers: dict[tuple[str, str], ScorerFn] | None = None,
    predicates: dict[str, InvariantPredicate] | None = None,
) -> RunRequest:
    return RunRequest(
        dataset=dataset or _dataset(),
        config=config or _config(),
        mode="OFFLINE_FAKE",
        system_version="0.4.0",
        inputs=inputs
        if inputs is not None
        else {
            "input://c1": {"answer": 42},
            "input://c2": {"answer": 7},
        },
        runtime_scorers=runtime_scorers or {},
        predicates=predicates or {},
    )


def test_replay_same_frozen_conditions_same_digest() -> None:
    first = run_evaluation(_request())
    second = run_evaluation(_request())
    assert first.report.digest() == second.report.digest()
    assert first.report.gate_verdict is QualityGateVerdict.PASS


def test_replay_digest_ignores_report_id_and_timestamp() -> None:
    base = _request()
    a = run_evaluation(
        RunRequest(
            dataset=base.dataset,
            config=base.config,
            mode=base.mode,
            system_version=base.system_version,
            inputs=dict(base.inputs),
            report_id="run-a",
            generated_at="2026-01-01T00:00:00Z",
        )
    )
    b = run_evaluation(
        RunRequest(
            dataset=base.dataset,
            config=base.config,
            mode=base.mode,
            system_version=base.system_version,
            inputs=dict(base.inputs),
            report_id="run-b",
            generated_at="2026-12-31T23:59:59Z",
        )
    )
    assert a.report.digest() == b.report.digest()


def test_missing_input_is_infra_error_not_pass() -> None:
    outcome = run_evaluation(_request(inputs={"input://c1": {"answer": 42}}))
    assert outcome.missing_inputs == ("input://c2",)
    c2 = next(item for item in outcome.report.results if item.case_id == "c2")
    assert c2.scorer_findings[0].status is EvalFindingStatus.INFRA_ERROR
    assert c2.passed is False
    assert outcome.report.gate_verdict is QualityGateVerdict.REVISE


def test_scorer_exception_becomes_infra_error() -> None:
    def exploding(ctx: ScorerContext) -> ScorerFinding:
        raise RuntimeError("boom")

    outcome = run_evaluation(
        _request(
            runtime_scorers={
                ("exact_match", "1.0.0"): exploding,
            }
        )
    )
    assert outcome.report.gate_verdict is QualityGateVerdict.REVISE
    assert all(
        finding.status is EvalFindingStatus.INFRA_ERROR
        for result in outcome.report.results
        for finding in result.scorer_findings
    )


def test_unknown_scorer_version_is_infra_error() -> None:
    future_case = EvalCase(
        id="c3",
        version=Version("1.0.0"),
        scope=EvalScope.UNIT,
        input_ref="input://c3",
        expected={"answer": 1},
        scorer_refs=(ScorerRef("exact_match", Version("9.9.9")),),
    )
    dataset = EvalDataset(
        id="runner-ds",
        version=Version("1.0.0"),
        cases=(future_case,),
    )
    outcome = run_evaluation(
        _request(
            dataset=dataset,
            inputs={"input://c3": {"answer": 1}},
        )
    )
    # registry 中只有 1.0.0，9.9.9 解析失败 → INFRA
    assert outcome.report.gate_verdict is QualityGateVerdict.REVISE
    assert outcome.report.results[0].scorer_findings[0].status is EvalFindingStatus.INFRA_ERROR


def test_failed_output_blocks_gate() -> None:
    outcome = run_evaluation(
        _request(inputs={"input://c1": {"answer": 43}, "input://c2": {"answer": 7}})
    )
    assert outcome.report.gate_verdict is QualityGateVerdict.BLOCK


def test_run_a_does_not_pollute_run_b() -> None:
    good = run_evaluation(_request())
    bad = run_evaluation(_request(inputs={"input://c1": {"answer": 0}}))
    # run B 不改变 run A 的 frozen 结果
    assert good.report.digest() == run_evaluation(_request()).report.digest()
    assert bad.report.gate_verdict is QualityGateVerdict.BLOCK
    assert good.report.gate_verdict is QualityGateVerdict.PASS


def test_input_accounting_covers_all_cases() -> None:
    outcome: RunnerOutcome = run_evaluation(_request())
    assert outcome.input_accounting == {"input://c1": 1, "input://c2": 1}


def test_accounting_reports_case_skip_as_missing() -> None:
    # 只提供一半输入：未提供者记 missing，提供者记 accounting
    outcome = run_evaluation(_request(inputs={"input://c1": {"answer": 42}}))
    assert outcome.input_accounting == {"input://c1": 1, "input://c2": 1}
    assert outcome.missing_inputs == ("input://c2",)


def test_verdict_gate_config_change_is_visible() -> None:
    loose = GateConfig(id="gate", version=Version("1.0.0"))
    tight = GateConfig(
        id="gate",
        version=Version("1.0.0"),
        rules=(),
        min_pass_ratio=Decimal("1.0"),
    )
    outcome = run_evaluation(_request(config=tight))
    # 全 PASS + min_pass_ratio=1.0 → PASS；配置变化必须体现在 digest 差异
    assert outcome.report.gate_verdict is QualityGateVerdict.PASS
    assert loose.digest() != tight.digest()


def test_verdict_min_pass_ratio_blocks_partial_pass() -> None:
    tight = GateConfig(
        id="gate",
        version=Version("1.0.0"),
        min_pass_ratio=Decimal("1.0"),
    )
    outcome = run_evaluation(
        _request(
            config=tight,
            inputs={"input://c1": {"answer": 42}},
        )
    )
    # c2 输入缺失 → INFRA → REVISE（先于 ratio 判定）
    assert outcome.report.gate_verdict is QualityGateVerdict.REVISE
