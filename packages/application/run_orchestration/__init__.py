"""RunOrchestration 应用层 Use Case（M7 Reliable Vertical Slice）。

RunOrchestrationService 把 M2 Compile/Preflight/Freeze、M4 Team Resolution、
M5 Ports/Fakes、M6 AgentRuntime 与领域产物链串成端到端 ResearchRun 执行。
只依赖 Port 契约与 domain 类型；不 import adapters。
"""

from packages.application.run_orchestration.commands import (
    CancelRunCommand,
    ResumeRunCommand,
    StartRunCommand,
)
from packages.application.run_orchestration.context import RunContext
from packages.application.run_orchestration.evaluation_gate import (
    EvaluationInputs,
    GateOutcome,
    evaluate_task_gate,
    verify_claim_with_evidence,
)
from packages.application.run_orchestration.experiment_task import (
    ExperimentTaskDeps,
    execute_experiment_task,
)
from packages.application.run_orchestration.handoff_builder import (
    HandoffPayload,
    build_handoff,
)
from packages.application.run_orchestration.memory_promotion import (
    MemoryPromotionContext,
    promote_memory_from_registration,
)
from packages.application.run_orchestration.phase_runner import (
    PhaseRunnerDeps,
    RunOutcome,
    TaskOutcome,
    execute_phases,
)
from packages.application.run_orchestration.result_handler import (
    ResultRegistration,
    register_session_result,
)
from packages.application.run_orchestration.service import (
    OrchestrationDependencies,
    RunOrchestrationService,
    SessionSpec,
)
from packages.application.run_orchestration.task_executor import (
    ExecutionDeps,
    ResumeManifestMismatchError,
    SessionSpecContext,
    TaskExecutionResult,
    execute_task,
)

__all__ = [
    "CancelRunCommand",
    "EvaluationInputs",
    "ExecutionDeps",
    "ExperimentTaskDeps",
    "GateOutcome",
    "HandoffPayload",
    "MemoryPromotionContext",
    "OrchestrationDependencies",
    "PhaseRunnerDeps",
    "ResumeManifestMismatchError",
    "ResumeRunCommand",
    "ResultRegistration",
    "RunContext",
    "RunOrchestrationService",
    "RunOutcome",
    "SessionSpec",
    "SessionSpecContext",
    "StartRunCommand",
    "TaskExecutionResult",
    "TaskOutcome",
    "build_handoff",
    "evaluate_task_gate",
    "execute_experiment_task",
    "execute_phases",
    "execute_task",
    "promote_memory_from_registration",
    "register_session_result",
    "verify_claim_with_evidence",
]
