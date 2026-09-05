"""Clean-run harness 依赖定义（M12-R1 WP8；与 clean_run 拆分保持模块规模）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from packages.application.ports import (
    CatalogSnapshot,
    CredentialResolver,
    ModelGateway,
    PreflightContext,
    ProjectSettings,
)
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.budget_ledger import BudgetLedger
from packages.application.ports.eval_report_store import EvalReportStore
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.ports.execution_backend import ExecutionBackend
from packages.application.ports.experiment_store import ExperimentStore
from packages.application.ports.memory_store import MemoryStore
from packages.application.ports.run_store import RunStore
from packages.application.ports.workspace_backend import WorkspaceBackend
from packages.domain.enums import MemoryType
from packages.domain.models import LLMEndpoint, ModelDefinition
from packages.domain.protocols import ProtocolDefinition
from packages.domain.workspace import Workspace


class CleanRunPersistence(Protocol):
    """Durable stores required by a personal-production Reference Run."""

    @property
    def run_store(self) -> RunStore: ...

    @property
    def experiment_store(self) -> ExperimentStore: ...

    @property
    def eval_report_store(self) -> EvalReportStore: ...


@dataclass(frozen=True, slots=True)
class CleanRunDeps:
    """clean-run 的显式依赖（composition root 注入；参数对象）。"""

    protocol: ProtocolDefinition
    catalog: CatalogSnapshot
    project: ProjectSettings
    context: PreflightContext
    execution: ExecutionBackend
    workspaces: WorkspaceBackend
    workspace: Workspace
    artifacts: ArtifactStore
    ledger: EvidenceLedger
    memory: MemoryStore
    budget: BudgetLedger
    persistence: CleanRunPersistence | None = None
    expected_image_digest: str | None = None
    model_gateway: ModelGateway | None = None
    credentials: CredentialResolver | None = None
    endpoint: LLMEndpoint | None = None
    model: ModelDefinition | None = None
    run_id: str | None = None
    workspace_root: object | None = None
    experiment_script: str | None = None
    objective: str = (
        "Compare baseline (TF-IDF + linear classifier) vs candidate "
        "(frozen hash-embedding + linear classifier) on a low-resource "
        "20-class text classification subset"
    )
    memory_kind: MemoryType = MemoryType.NEGATIVE_RESULT
    # M17: GPU slice reuses this harness — resource_profile/hypothesis/
    # plan_name/dataset_path are injectable so no second Experiment Domain
    # is created. Defaults preserve the M12 reference behavior exactly.
    resource_profile: str = "small"
    hypothesis: str = "hash-embedding+linear classifier beats tfidf on low-resource subset"
    plan_name: str = "m12-reference-classification"
    dataset_path: str = "examples/eval/datasets/m12_research_v1.yaml"
    claim_statement: str = (
        "baseline tfidf+linear_softmax outperforms candidate "
        "hash_embedding+linear_softmax on the low-resource subset"
    )
    memory_content: str = (
        "hash-embedding+linear_softmax candidate did not beat "
        "tfidf baseline on low-resource 20-class subset"
    )


__all__ = ["CleanRunDeps", "CleanRunPersistence"]
