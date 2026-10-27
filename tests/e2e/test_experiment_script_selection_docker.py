"""GOAL-20261027-098 EC-03 的**容器面**取证：计划选中的脚本真的在沙箱里跑。

**它补哪一格**：`tests/application/test_experiment_script_comes_from_the_plan.py` 判的是
**派发面**（`assembly.script` 换成了计划点名的那个 —— 即 `_governed_executor` 会复制进
沙箱工作区的文件）。它**不出容器**，证明的是「选中的是哪个」，不是「容器里跑的就是它」。

本文件把那一格接到**既有** `DockerExecutionBackend`：同一个 `sandbox_experiment_runner` +
同一个 `docker_experiment_assembly`，只把计划写成两份（一份点名
`exact_match_index_benchmark.py`、一份点名 `sort_analysis_baseline.py`），然后判
**容器产出的指标** —— 两个脚本测的量不同（去重：`duplicates_found`；排序：
`worst_case_comparisons`），所以「跑的是哪一个」在**读数**上分得开。

**为什么不能只靠派发面**：`assembly.script` 是**输入**，容器读数才是**输出**。若复制脚本
那一步出偏差（本轮就有一个真缺陷长在同类位置：`with_novelty` 读不存在的字段），派发面
判据会照绿。本条把两端钉在一起。

**如实边界**：`requires_docker` —— 没有 Linux 容器的守护进程就**如实 skip**（**skip 不是
PASS**）。零出网（脚本纯标准库、语料自生成）；容器只挂它自己的工作区。

**取证**：`.cursor/plans/goals/evidence/GOAL-20261027-098-ec03-container-run.txt`
（**追加**写盘 —— 一次抖动不该盖掉上一次的成功读数）。"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest

from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.evidence_ledger import FakeEvidenceLedger
from packages.application.experiments.design_from_plan import plan_artifact_id
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest
from packages.domain.enums import ActivationPolicy, ArtifactState, ModelBindingMode, RoleCategory
from packages.domain.evidence import (
    Claim,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
)
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from packages.domain.tasks import ExperimentExecutionSpec, ResearchTask

pytestmark = pytest.mark.requires_docker

_EVIDENCE = Path(".cursor/plans/goals/evidence/GOAL-20261027-098-ec03-container-run.txt")
_EXACT_MATCH = "examples/experiments/exact_match_index_benchmark.py"
_SORT_BASELINE = "examples/experiments/sort_analysis_baseline.py"
#: 每个脚本**独有**的指标名 ⇒ 用它判「容器里跑的是哪一个」。
_SIGNATURE = {_EXACT_MATCH: "duplicates_found", _SORT_BASELINE: "worst_case_comparisons"}
_IMAGE = "research-os-sandbox:m9-test"


#: 写盘开关（缺省**不写**，见 `_write_evidence` 的 docstring）。
_EVIDENCE_SWITCH = "RESEARCHOS_EC03_EVIDENCE"


def _write_evidence(entry: str, readings: dict[str, Any]) -> None:
    """读数**追加**落盘 —— 但**只在显式打开开关时**。

    **为什么不无条件写**（本轮实测的坑，代价是一次作废的 m0）：取证文件是**受判文件**，
    而本判据在 m0 里会执行（`container-quality` 作业）。无条件追加 ⇒ **门在跑的时候改了树**
    ⇒ 见证自己判 `tree changed during the run: True` ⇒ 那次终态行作废。这与我本轮
    为 GOAL-097 修的「判词归档也是受判文件」是同一条纪律，只是这次踩在自己身上。

    ⇒ 取证由**显式一次**采集（`RESEARCHOS_EC03_EVIDENCE=1`），日常门跑只读不写。
    """
    import os

    if not os.environ.get(_EVIDENCE_SWITCH):
        return
    _EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    lines: list[str] = []
    if not _EVIDENCE.exists():
        lines.append("# GOAL-20261027-098 EC-03 container run readings")
    lines += ["", f"## {entry} @ {stamp}", ""]
    lines += [f"- `{key}`: {value}" for key, value in readings.items()]
    lines.append("")
    with _EVIDENCE.open("a", encoding="utf-8", newline=chr(10)) as handle:
        handle.write(chr(10).join(lines))


def _store() -> Any:
    """实验存储（`GET /runs/{id}/experiments` 读的就是它）。"""
    from adapters.fakes.experiment_store import FakeExperimentStore

    return FakeExperimentStore()


def _spec() -> SessionSpecContext:
    """实验工程师的会话上下文（与 `test_sandbox_experiment_seam_docker` 同形）。"""
    return SessionSpecContext(
        role=RoleDefinition(
            id="experiment_engineer",
            role_type="experiment_engineer",
            category=RoleCategory.EXPERIMENT,
            activation_default=ActivationPolicy.ALWAYS,
        ),
        agent=AgentSpec(
            id="engineer",
            role="experiment_engineer",
            model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="model-1"),
        ),
        frozen_manifest_digest="manifest-digest",
        frozen_tool_set=(),
        declared_input_artifacts=(),
        run_chain_tool_ids=(),
    )


def _seed_plan(artifacts: Any, ledger: Any, script: str, run_id: str, task_id: str) -> None:
    """把一份**点名了脚本**的计划登记进本 run 的证据链（= 它对本 run「在场」）。"""
    content = json.dumps(
        {"experiment_design": {"arms": {"only": {}}, "script": script}}, ensure_ascii=False
    ).encode("utf-8")
    artifact_id = plan_artifact_id(task_id)
    artifacts.put(
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            storage_uri=None,
            created_by="agent:research_director",
            source_refs=[f"task:{task_id}"],
            classification="execution_result",
        ),
        content,
    )
    artifacts.mark(artifact_id, ArtifactState.VERIFIED)
    evidence = Evidence(
        id="evidence:plan:ec03-container",
        source_ref=f"tool:{artifact_id}",
        content_digest="0" * 64,
        extracted_by="agent:research_director",
        artifact_id=artifact_id,
        run_id=run_id,
    )
    claim = Claim(id="claim:plan:ec03-container", statement=f"plan {artifact_id}")
    ledger.register_evidence(evidence)
    ledger.register_claim(claim)
    ledger.attach_relation(
        EvidenceRelation(
            claim_id=claim.id,
            evidence_id=evidence.id,
            relation=EvidenceRelationType.SUPPORTS,
        )
    )


def _empty_contract() -> Any:
    """契约声明了实验、但**不 pin 脚本**（`experiment: {}` 的既有语义）。

    `declared_or_assembled` 里契约 pin 最强；若它非空，计划的选择会被（正确地）跳过。
    那条优先级已由派发面判据逐档钉住 ⇒ 本条让契约缺席，才测得到「计划的选择能到达容器」。
    """
    from dataclasses import replace

    from tests.application.test_experiment_parameters import _contract

    return replace(_contract(), experiment=ExperimentExecutionSpec())


def _run_with_plan(script: str, tag: str, experiment_store: Any) -> dict[str, Any]:
    """种一份点名 `script` 的计划，跑一次**真容器**，返回读数。"""
    from services.api.assembly import policy_bindings
    from services.api.experiment_support import (
        docker_experiment_assembly,
        sandbox_experiment_runner,
    )

    artifacts, ledger = FakeArtifactStore(), FakeEvidenceLedger()
    task = ResearchTask(id=ID.generate(), run_id=ID.generate(), attempt=1)
    _seed_plan(artifacts, ledger, script, str(task.run_id.value), str(task.id.value))
    policy = policy_bindings().get("policy_evaluator")
    assert policy is not None, "examples/config/policy.yaml must be loadable"
    runner = sandbox_experiment_runner(
        docker_experiment_assembly(
            artifacts=artifacts,
            ledger=ledger,
            policy=policy,
            script=None,
            image=_IMAGE,
            experiment_store=experiment_store,
            design_source="plan",
        )
    )
    result = runner(task, _empty_contract(), _spec(), f"trace-ec03-container-{tag}")
    readings: dict[str, Any] = {
        "selected_script": script,
        "outcome": str(result.outcome),
        "message": str(result.message)[:200],
    }
    outcome = result.experiment_outcome
    if outcome is not None and outcome.run.result is not None:
        record = outcome.run.result
        readings["experiment_run_state"] = str(outcome.run.state)
        readings["metric_names"] = sorted({item.metric.name for item in record.metrics})
        readings["image_digest"] = str(record.image_digest)[:24]
        readings["admitted_evidence"] = (
            len(result.experiment_admission.evidence)
            if (result.experiment_admission is not None)
            else 0
        )
    _write_evidence(f"plan-selects-{tag}", readings)
    return readings


def test_the_plan_selected_script_is_what_runs_in_the_container() -> None:
    """**容器面**：计划点名 A ⇒ 容器产出 A 的指标；点名 B ⇒ 产出 B 的指标。"""
    store = _store()
    exact = _run_with_plan(_EXACT_MATCH, "exact-match", store)
    sort = _run_with_plan(_SORT_BASELINE, "sort-baseline", store)

    for readings in (exact, sort):
        assert readings["outcome"] == "SUCCEEDED", readings
        assert readings.get("experiment_run_state") == "SUCCEEDED", readings
        assert readings.get("image_digest"), readings
        assert readings.get("admitted_evidence", 0) >= 1, readings

    exact_metrics = set(exact["metric_names"])
    sort_metrics = set(sort["metric_names"])
    # 每个脚本**自己的**签名指标在场，**别个的**不在场 ⇒ 容器里跑的确是指名那个。
    assert _SIGNATURE[_EXACT_MATCH] in exact_metrics, exact_metrics
    assert _SIGNATURE[_SORT_BASELINE] not in exact_metrics, exact_metrics
    assert _SIGNATURE[_SORT_BASELINE] in sort_metrics, sort_metrics
    assert _SIGNATURE[_EXACT_MATCH] not in sort_metrics, sort_metrics
