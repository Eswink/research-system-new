"""Experiment 执行 use case 的输入输出类型与执行契约常量（M9）。"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path

from packages.domain.core import ID, Digest
from packages.domain.enums import PolicyDecision
from packages.domain.experiments import ExperimentPlan, ExperimentRun
from packages.domain.workspace import Workspace, WorkspaceLease

WorkspaceDirResolver = Callable[[WorkspaceLease], Path]

STDOUT_LOG = "stdout.log"
STDERR_LOG = "stderr.log"
RESULT_FILE = "experiment_result.json"

MEDIA_JSON = "application/json"
MEDIA_OCTET = "application/octet-stream"


@dataclass(frozen=True, slots=True)
class ExperimentExecutionRequest:
    """一次实验执行的输入；plan 必须处于 PREREGISTERED（调用方负责）。"""

    plan: ExperimentPlan
    run_id: ID
    command: str
    workspace: Workspace
    agent_session_id: str
    seed: int | None = None
    resource_profile: str | None = None
    environment: Mapping[str, str] = field(default_factory=dict)
    code_digest: Digest | None = None
    timeout_seconds: int | None = None


@dataclass(frozen=True, slots=True)
class ExperimentExecutionOutcome:
    """执行结果聚合：终态 ExperimentRun + 落库 artifact id。"""

    run: ExperimentRun
    stdout_artifact_id: str | None = None
    stderr_artifact_id: str | None = None
    result_artifact_id: str | None = None
    #: GOAL-014 EC-02（A/c）：执行期**真的求值并执行**的逐能力策略决定（capability → decision）
    #: ——**如实记录已发生的事实**，不是在这里再判一次。治理包装未运行（裸 `ExperimentExecutor`）
    #: 或走了幂等复用分支时为空映射 ⇒ 验收门的 `POLICY_COMPLIANT` 维持 `policy decision unknown`。
    policy_decisions: Mapping[str, PolicyDecision] = field(default_factory=dict)


def with_policy_decisions(
    outcome: ExperimentExecutionOutcome,
    decisions: Mapping[str, PolicyDecision],
) -> ExperimentExecutionOutcome:
    """把**执行期已经发生**的逐能力策略决定附加到结果上（**只记录事实**，不再判定）。

    `decisions` 由 `GovernedExperimentExecutor._enforce_policy` 原样给出（它已经在那里
    求值并强制）；本函数不读策略、不做第二次裁决，只把那次求值的结果带出执行体，
    好让验收门的 `POLICY_COMPLIANT` 有**事实来源**而不是「unknown」。空映射 = 治理包装
    没有运行（裸执行体）⇒ 该判据维持 fail-closed。
    """
    return replace(outcome, policy_decisions=dict(decisions))
