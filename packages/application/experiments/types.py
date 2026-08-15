"""Experiment 执行 use case 的输入输出类型与执行契约常量（M9）。"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from packages.domain.core import ID, Digest
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
