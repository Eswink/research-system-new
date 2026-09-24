"""GOAL-014 EC-02（用户判词 A）：验收门**四维输入面**接线的离线判据（零出网、不起容器）。

判的是「接通」这件事本身，逐维各自有正反两面——正是 `F-11` 的四维饥饿面：

| 维 | 接的是什么（事实来源） | 反面（未接通时仍是既有的恒判词） |
| --- | --- | --- |
| `SCHEMA_VALID` | 合约声明的 `output_schema`（仓内 `schemas/`） | `schema validator unavailable` |
| `TEST_PASSES` | 实验**自报产物**的字节（报告 / `stderr.log`） | `no test results provided` |
| `METRIC_THRESHOLD` | 域实体字段 `ExperimentRunResult.metrics` | `metric … missing` |
| `POLICY_COMPLIANT` | 执行期**已经执行过**的逐能力决定 | `policy decision unknown` |

两条纪律写进判据：**值必须从事实算出**（去掉事实 ⇒ 判拒并**点名**是哪条判据缺什么），
且**缺维不得被算成通过**（缺省必须落到上表右列那句既有判词）。

判据**不**复用被测实现当预言机的地方：期望的判词逐字写在断言里（`no test results
provided` 等来自 `packages/domain/acceptance.py`，是既有口径）。
"""

from __future__ import annotations

from decimal import Decimal

from adapters.fakes import FakeArtifactStore
from packages.application.experiments.types import ExperimentExecutionOutcome
from packages.application.run_orchestration.evaluation_gate import (
    EvaluationInputs,
    evaluate_task_gate,
)
from packages.application.run_orchestration.experiment_gate_inputs import (
    metric_inputs,
    recorded_policy_decision,
    reported_tests,
)
from packages.application.run_orchestration.output_schema_check import output_schema_check_for
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest
from packages.domain.enums import (
    AcceptanceCriterionType,
    ComparisonOperator,
    PolicyDecision,
)
from packages.domain.experiments import (
    ExperimentRun,
    ExperimentRunResult,
    MetricValue,
    metric_value_from_raw,
)
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, TaskContract

_RUN_ID = "3f1c6a8e-9b2d-4f3a-8c5e-1a2b3c4d5e6f"
_REPORT = f"{_RUN_ID}:experiment_result.json"
_STDERR = f"{_RUN_ID}:stderr.log"
_METRICS = f"{_RUN_ID}:metrics"


def _task() -> ResearchTask:
    return ResearchTask(id=ID.generate(), run_id=ID(_RUN_ID))


def _contract(criteria: list[AcceptanceCriterion], schema: str | None = None) -> TaskContract:
    return TaskContract(
        id="experiment_execution",
        version="1.0.0",
        purpose="gate input face criteria",
        output_schema=schema,
        acceptance_criteria=criteria,
    )


def _store(report: str | None, stderr: str | None) -> FakeArtifactStore:
    """制品店：内容寻址（digest 由内容算出，不是写死的常量）。"""
    store = FakeArtifactStore()
    for artifact_id, text in ((_REPORT, report), (_STDERR, stderr)):
        if text is None:
            continue
        content = text.encode("utf-8")
        store.put(
            Artifact(
                id=artifact_id,
                digest=Digest.of_bytes(content),
                size_bytes=len(content),
                media_type="application/json",
                created_by="experiment_executor",
            ),
            content,
        )
    return store


def _result(metrics: dict[str, object] | None) -> ExperimentRunResult:
    values: tuple[MetricValue, ...] = (
        tuple(metric_value_from_raw(name, value) for name, value in sorted(metrics.items()))
        if metrics is not None
        else ()
    )
    return ExperimentRunResult(
        execution_run_id="exec-1",
        image_digest="sha256:" + "0" * 64,
        metrics=values,
        artifact_refs=(_REPORT,),
    )


def _outcome(
    result: ExperimentRunResult | None,
    *,
    report: str | None = None,
    stderr: str | None = None,
    decisions: dict[str, PolicyDecision] | None = None,
) -> ExperimentExecutionOutcome:
    run = ExperimentRun(id=ID(_RUN_ID), plan_id=ID.generate(), result=result)
    return ExperimentExecutionOutcome(
        run=run,
        stdout_artifact_id=None,
        stderr_artifact_id=_STDERR if stderr is not None else None,
        result_artifact_id=_REPORT if report is not None else None,
        policy_decisions=decisions or {},
    )


_REPORT_OK = '{"status": "SUCCEEDED", "metrics": {"n_items": 800}}'


def _verdict(
    criteria: list[AcceptanceCriterion],
    *,
    schema: str | None = None,
    outcome: ExperimentExecutionOutcome | None = None,
    store: FakeArtifactStore | None = None,
    artifacts: dict[str, object] | None = None,
) -> tuple[bool, str]:
    inputs = EvaluationInputs(
        structured_output=(
            {
                "experiment_run_id": _RUN_ID,
                "status": "SUCCEEDED",
                "artifact_refs": ["metrics"],
                "metrics": {"n_items": 800},
            }
            if schema is not None
            else {}
        ),
        artifacts=artifacts or {},
        schema_check=output_schema_check_for(schema),
        metrics=metric_inputs(None if outcome is None else outcome.run.result),
        tests={} if outcome is None else reported_tests(outcome, store),
        policy_decision=recorded_policy_decision(
            {} if outcome is None else outcome.policy_decisions
        ),
    )
    gate = evaluate_task_gate(_task(), _contract(criteria, schema), inputs, reviewer="gate:test")
    return gate.passed, "; ".join(item.reason for item in gate.evaluations)


def test_schema_face_is_taken_from_the_contract_declared_schema() -> None:
    """`SCHEMA_VALID`：回调按合约声明的 schema 名取，且**真的**按 schema 判。"""
    check = output_schema_check_for("experiment_run_output_v1")
    assert check is not None, "出厂 schema 名必须解析得到校验器"
    assert (
        check({"experiment_run_id": "x", "status": "SUCCEEDED", "artifact_refs": [], "metrics": {}})
        is None
    )
    violation = check({"experiment_run_id": "x", "status": "NOT_A_STATUS"})
    assert violation and "NOT_A_STATUS" in violation, violation

    ok, reasons = _verdict(
        [AcceptanceCriterion(type=AcceptanceCriterionType.SCHEMA_VALID)],
        schema="experiment_run_output_v1",
    )
    assert ok, reasons


def test_schema_face_stays_fail_closed_for_an_unknown_schema() -> None:
    """反面：schema 名在目录里不存在 ⇒ **不是**算过，而是既有的 `unavailable` 判词。"""
    assert output_schema_check_for("no_such_output_v1") is None
    ok, reasons = _verdict(
        [AcceptanceCriterion(type=AcceptanceCriterionType.SCHEMA_VALID)],
        schema="no_such_output_v1",
    )
    assert not ok and "schema validator unavailable" in reasons, reasons


def test_metric_face_is_taken_from_the_experiment_entity() -> None:
    """`METRIC_THRESHOLD`：指标来自域实体字段，缺指标时**点名**缺哪一个。"""
    outcome = _outcome(_result({"n_items": 800, "ratio": Decimal("7990.0")}))
    expect = {"n_items": Decimal(800), "ratio": Decimal("7990.0")}
    assert metric_inputs(outcome.run.result) == expect

    criterion = AcceptanceCriterion(
        type=AcceptanceCriterionType.METRIC_THRESHOLD,
        metric="n_items",
        operator=ComparisonOperator.GTE,
        threshold=Decimal(100),
    )
    ok, reasons = _verdict([criterion], outcome=outcome)
    assert ok, reasons

    missing = AcceptanceCriterion(
        type=AcceptanceCriterionType.METRIC_THRESHOLD,
        metric="not_reported",
        operator=ComparisonOperator.GTE,
        threshold=Decimal(1),
    )
    ok, reasons = _verdict([missing], outcome=outcome)
    assert not ok and "metric not_reported missing" in reasons, reasons


def test_policy_face_records_the_executed_decisions_without_re_judging() -> None:
    """`POLICY_COMPLIANT`：判的是**执行期已发生**的那组决定的保守合成。"""
    assert recorded_policy_decision({}) is None, "没有求值过 ⇒ 未知（fail-closed）"
    assert (
        recorded_policy_decision({"artifact.write": PolicyDecision.ALLOW}) is PolicyDecision.ALLOW
    )
    mixed = {
        "artifact.write": PolicyDecision.ALLOW,
        "code.execute": PolicyDecision.ALLOW_WITH_CONSTRAINTS,
    }
    assert recorded_policy_decision(mixed) is PolicyDecision.ALLOW_WITH_CONSTRAINTS, (
        "任一能力带约束 ⇒ 报带约束（最不宽松的那一个说了算）"
    )

    criterion = AcceptanceCriterion(type=AcceptanceCriterionType.POLICY_COMPLIANT)
    ok, reasons = _verdict(
        [criterion],
        outcome=_outcome(_result(None), decisions={"code.execute": PolicyDecision.ALLOW}),
    )
    assert ok and "policy decision ALLOW" in reasons, reasons

    ok, reasons = _verdict([criterion], outcome=_outcome(_result(None), decisions={}))
    assert not ok and "policy decision unknown" in reasons, reasons


def test_tests_face_is_computed_from_the_experiment_artifacts() -> None:
    """`TEST_PASSES`：每一项都由**产物字节**算出，且名字里带出处。"""
    criterion = [AcceptanceCriterion(type=AcceptanceCriterionType.TEST_PASSES)]
    outcome = _outcome(_result({"n_items": 800}), report=_REPORT_OK, stderr="")
    store = _store(_REPORT_OK, "")
    assert reported_tests(outcome, store) == {
        "experiment_result.json:declared_status_SUCCEEDED": True,
        "experiment_result.json:metrics_declared": True,
        "stderr.log:empty": True,
    }
    ok, reasons = _verdict(criterion, outcome=outcome, store=store)
    assert ok and "all tests pass" in reasons, reasons


def test_tests_face_reports_unknown_when_the_self_report_is_absent() -> None:
    """反面一：**没有**自报产物 ⇒ 诚实结论是「没有可判的结果」（不是伪造一组 False）。"""
    outcome = _outcome(_result({"n_items": 800}), report=None, stderr=None)
    assert reported_tests(outcome, _store(None, None)) == {}
    ok, reasons = _verdict(
        [AcceptanceCriterion(type=AcceptanceCriterionType.TEST_PASSES)], outcome=outcome
    )
    assert not ok and "no test results provided" in reasons, reasons


def test_tests_face_names_each_failing_self_reported_item() -> None:
    """反面二：自报内容**在但不合格** ⇒ 逐项**具名**判否（判词点名到具体那一项）。"""
    report = '{"status": "NEGATIVE_RESULT", "metrics": {}}'
    outcome = _outcome(_result({"n_items": 800}), report=report, stderr="Traceback: boom")
    checks = reported_tests(outcome, _store(report, "Traceback: boom"))
    assert checks == {
        "experiment_result.json:declared_status_SUCCEEDED": False,
        "experiment_result.json:metrics_declared": False,
        "stderr.log:empty": False,
    }
    ok, reasons = _verdict(
        [AcceptanceCriterion(type=AcceptanceCriterionType.TEST_PASSES)],
        outcome=outcome,
        store=_store(report, "Traceback: boom"),
    )
    assert not ok, reasons
    for name in checks:
        assert name in reasons, (name, reasons)


def test_removing_the_self_report_makes_the_gate_reject_and_name_the_criteria() -> None:
    """EC-02 的**反证 (b)**：去掉实验自报产物 ⇒ 判拒，且**点名**每条判据缺什么。

    同一套代码、同一组合约：事实在场 ⇒ 全过；把**自报面**（`metrics` 制品 + 报告）抽掉
    ⇒ 门判拒并把「缺的是 `ARTIFACT_EXISTS(metrics)`」与「缺的是自报测试结果」两句话
    逐字写进判词。这就是「接通的是真实事实，不是喂门通过」的可复跑证明。
    """
    criteria = [
        AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS, artifact="metrics"),
        AcceptanceCriterion(type=AcceptanceCriterionType.TEST_PASSES),
        AcceptanceCriterion(type=AcceptanceCriterionType.POLICY_COMPLIANT),
    ]
    decision = {"code.execute": PolicyDecision.ALLOW_WITH_CONSTRAINTS}
    with_facts = _outcome(
        _result({"n_items": 800}), report=_REPORT_OK, stderr="", decisions=decision
    )
    ok, reasons = _verdict(
        criteria,
        outcome=with_facts,
        store=_store(_REPORT_OK, ""),
        artifacts={"metrics": object(), _METRICS: object()},
    )
    assert ok, reasons

    without_facts = _outcome(_result(None), report=None, stderr=None)
    ok, reasons = _verdict(criteria, outcome=without_facts, store=_store(None, None), artifacts={})
    assert not ok, reasons
    assert "artifact metrics missing" in reasons, reasons
    assert "no test results provided" in reasons, reasons
    assert "policy decision unknown" in reasons, reasons
