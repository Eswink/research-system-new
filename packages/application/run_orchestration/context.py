"""RunOrchestration 的执行上下文 DTO（trace 关联 + 冻结快照）。"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports.resource_catalog import (
    CatalogSnapshot,
    PreflightContext,
    ProjectSettings,
)
from packages.domain.protocols import (
    CompiledRunPlan,
    PreflightReport,
    ProtocolDefinition,
)
from packages.domain.run import ResearchRun


@dataclass(frozen=True, slots=True)
class RunContext:
    """单次执行的上下文（trace 关联 + 冻结快照）。"""

    protocol: ProtocolDefinition
    plan: CompiledRunPlan
    report: PreflightReport
    run: ResearchRun
    catalog: CatalogSnapshot
    project: ProjectSettings
    preflight: PreflightContext
    trace_id: str

    @property
    def frozen_manifest_digest(self) -> str:
        assert self.run.manifest_digest is not None
        return str(self.run.manifest_digest)