"""重建能力读面的 HTTP 形状（GOAL-005 cycle 6 = EC-06）。

判据在应用层（`packages.application.run_orchestration.rebuild_readiness`）；这里只做
"领域事实 → DTO"的映射，让控制面读面与 `/resume` 的拒绝文案取自**同一个分类器**。
"""

from __future__ import annotations

from packages.application.run_orchestration.rebuild_readiness import rebuild_readiness
from packages.domain.run import ResearchRun
from services.api.dto.runs import RebuildReadinessDto


def rebuild_readiness_dto(run: ResearchRun) -> RebuildReadinessDto:
    """run 行 → 重建能力读面（任何状态都给；只读记录，不动状态）。"""
    readiness = rebuild_readiness(run)
    return RebuildReadinessDto(status=readiness.status, missing=list(readiness.missing))
