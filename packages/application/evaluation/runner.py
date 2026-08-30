"""M11 EvalRunner：确定性评测编排（显式输入、隔离、异常不转 PASS）。

约束：
- 输入经显式 resolver（输入物缺失 → INFRA_ERROR，绝不判 PASS）；
- scorer 抛出的任何异常转换为 INFRA_ERROR finding（catch-and-PASS 被
  结构性禁止：FAIL 只能由 scorer 以结构化 finding 产生）；
- 不同 Run 之间零共享可变状态；同一冻结条件 + 同一输入 → 相同报告
  digest（generated_at/report_id 不参与 digest）；
- case 计数与输入引用全量对账，跳过/丢弃 case 在 input_accounting 可见。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from packages.application.evaluation.scorer_types import (
    V1,
    InvariantPredicate,
    ScorerContext,
    ScorerFn,
    ScorerInput,
    make_finding,
)
from packages.application.evaluation.scorers import resolve_scorer
from packages.application.observability.attributes import MetricKind, MetricName, MetricSample
from packages.application.observability.scope import operation, record_metric_safely
from packages.application.observability.signals import (
    CorrelationRef,
    OperationOutcome,
    OperationScope,
)
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.domain.eval_gate import GateConfig, compute_verdict
from packages.domain.eval_result import (
    EvalFindingStatus,
    EvalReport,
    EvalResult,
    FrozenConditions,
    ScorerFinding,
)
from packages.domain.eval_spec import EvalCase, EvalDataset, case_digest
from packages.domain.serialization import digest_of

_MISSING_SCORER = "input_resolution"


@dataclass(frozen=True, slots=True)
class RunRequest:
    """一次评测运行的完整冻结输入。"""

    dataset: EvalDataset
    config: GateConfig
    mode: str
    system_version: str
    inputs: Mapping[str, object] = field(default_factory=dict)
    evidence: Mapping[str, Mapping[str, str]] = field(default_factory=dict)
    predicates: Mapping[str, InvariantPredicate] = field(default_factory=dict)
    runtime_scorers: Mapping[tuple[str, str], ScorerFn] = field(default_factory=dict)
    report_id: str | None = None
    generated_at: str | None = None


@dataclass(frozen=True, slots=True)
class RunnerOutcome:
    report: EvalReport
    input_accounting: Mapping[str, int]
    missing_inputs: tuple[str, ...]


def run_evaluation(
    request: RunRequest,
    *,
    telemetry: TelemetrySink | None = None,
) -> RunnerOutcome:
    """执行一次评测并产出完整 EvalReport。

    M15:可选 telemetry——EVAL_RUN span + INFRA_ERROR/missing 计数 metric;
    纯函数语义不变(报告 digest 与 telemetry 无关)。
    """
    with operation(
        telemetry,
        scope=OperationScope.EVAL_RUN,
        name="eval.run",
        correlation=CorrelationRef(
            eval_run_id=request.report_id or f"eval:{request.dataset.id}:{request.mode}"
        ),
    ) as op:
        outcome = _run_evaluation_impl(request)
        _note_eval_counters(telemetry, outcome)
        op.set_outcome(OperationOutcome.OK, extra=_eval_span_extras(outcome))
        return outcome


def _infra_error_count(outcome: RunnerOutcome) -> int:
    return sum(
        1
        for result in outcome.report.results
        for finding in result.scorer_findings
        if finding.status is EvalFindingStatus.INFRA_ERROR
    )


def _eval_span_extras(outcome: RunnerOutcome) -> dict[str, object]:
    return {
        "verdict": outcome.report.gate_verdict.value,
        "dataset_digest": outcome.report.frozen_conditions.dataset_digest,
        "scorer_count": len(outcome.report.frozen_conditions.scorer_versions),
    }


def _note_eval_counters(telemetry: TelemetrySink | None, outcome: RunnerOutcome) -> None:
    """INFRA_ERROR 与 missing-evaluation 独立计数(绝不折算进正常趋势)。"""
    infra_errors = _infra_error_count(outcome)
    if infra_errors:
        record_metric_safely(
            telemetry,
            lambda: MetricSample(
                name=MetricName.EVAL_INFRA_ERRORS,
                kind=MetricKind.COUNTER,
                value=infra_errors,
            ),
        )
    missing = len(outcome.missing_inputs)
    if missing:
        record_metric_safely(
            telemetry,
            lambda: MetricSample(
                name=MetricName.EVAL_MISSING_EVALUATIONS,
                kind=MetricKind.COUNTER,
                value=missing,
            ),
        )


def _run_evaluation_impl(request: RunRequest) -> RunnerOutcome:
    dataset = request.dataset
    results: list[EvalResult] = []
    accounting: dict[str, int] = {}
    missing: list[str] = []
    for case in dataset.sorted_cases():
        accounting[case.input_ref] = accounting.get(case.input_ref, 0) + 1
        results.append(_run_case(request, case, missing))
    frozen = _build_frozen(request, accounting)
    report = EvalReport(
        report_id=request.report_id or f"eval:{dataset.id}:{request.mode}",
        generated_at=request.generated_at or "offline",
        mode=request.mode,
        scope=dataset.cases[0].scope,
        gate_verdict=compute_verdict(request.config, tuple(results)),
        frozen_conditions=frozen,
        results=tuple(results),
    )
    return RunnerOutcome(
        report=report,
        input_accounting=dict(accounting),
        missing_inputs=tuple(missing),
    )


def _run_case(request: RunRequest, case: EvalCase, missing: list[str]) -> EvalResult:
    actual = request.inputs.get(case.input_ref)
    if actual is None:
        missing.append(case.input_ref)
        return EvalResult(
            case_id=case.id,
            case_version=case.version,
            case_digest=case_digest(case),
            scope=case.scope,
            input_ref=case.input_ref,
            scorer_findings=(_missing_input_finding(case),),
        )
    findings = _invoke_scorers(request, case, actual)
    return EvalResult(
        case_id=case.id,
        case_version=case.version,
        case_digest=case_digest(case),
        scope=case.scope,
        input_ref=case.input_ref,
        scorer_findings=findings,
    )


def _invoke_scorers(
    request: RunRequest, case: EvalCase, actual: object
) -> tuple[ScorerFinding, ...]:
    scorer_input = ScorerInput(
        actual=actual,
        evidence_sources=request.evidence.get(case.input_ref, {}),
    )
    context = ScorerContext(case=case, input=scorer_input, predicates=request.predicates)
    findings: list[ScorerFinding] = []
    for scorer_ref in case.scorer_refs:
        key = (scorer_ref.scorer_id, scorer_ref.version.text)
        fn = request.runtime_scorers.get(key)
        if fn is None:
            try:
                fn = resolve_scorer(scorer_ref.scorer_id, scorer_ref.version.text)
            except KeyError:
                findings.append(
                    make_finding(
                        scorer_ref.scorer_id,
                        context,
                        EvalFindingStatus.INFRA_ERROR,
                        f"scorer {scorer_ref.scorer_id}@{scorer_ref.version.text} unavailable",
                    )
                )
                continue
        try:
            findings.append(fn(context))
        except Exception as exc:  # noqa: BLE001 - 评测设施故障不得判为被评对象失败
            findings.append(
                make_finding(
                    scorer_ref.scorer_id,
                    context,
                    EvalFindingStatus.INFRA_ERROR,
                    f"scorer exception: {type(exc).__name__}: {exc}",
                )
            )
    return tuple(findings)


def _missing_input_finding(case: EvalCase) -> ScorerFinding:
    return ScorerFinding(
        scorer_id=_MISSING_SCORER,
        scorer_version=V1,
        case_id=case.id,
        status=EvalFindingStatus.INFRA_ERROR,
        detail=f"input {case.input_ref} not provided",
    )


def _build_frozen(request: RunRequest, accounting: Mapping[str, int]) -> FrozenConditions:
    dataset = request.dataset
    input_digests = {
        ref: str(digest_of(request.inputs[ref])) for ref in accounting if ref in request.inputs
    }
    return FrozenConditions(
        dataset_id=dataset.id,
        dataset_version=dataset.version,
        dataset_digest=dataset.digest(),
        gate_config_id=request.config.id,
        gate_config_version=request.config.version,
        gate_config_digest=request.config.digest(),
        system_version=request.system_version,
        scorer_versions=_collect_scorer_versions(dataset),
        input_digests=input_digests,
        rubric_digest=digest_of([
            {
                "case_id": case.id,
                "rubric": [
                    {
                        "id": rubric.id,
                        "dimension": rubric.dimension,
                        "description": rubric.description,
                        "scale": rubric.scale,
                    }
                    for rubric in case.rubric
                ],
            }
            for case in dataset.sorted_cases()
        ]),
    )


def _collect_scorer_versions(dataset: EvalDataset) -> dict[str, str]:
    versions: dict[str, str] = {}
    for case in dataset.cases:
        for ref in case.scorer_refs:
            versions[ref.scorer_id] = ref.version.text
    return versions
