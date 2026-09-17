"""ResearchRun 域实体。

ResearchRun 是 Project 下的一次研究执行单元，持有运行生命周期状态。
状态集合与迁移表来自 packages.domain.run_state.ResearchRunState
（docs/reliability/RUN_STATE_MACHINE.md）；实体不可变，状态迁移通过
transition() 构造新实例，旧实例保留历史证据。

Canonical State 边界：ResearchRun 状态是业务真相，OpenHands
Conversation / runtime checkpoint / logs 均不是（AGENTS.md §6）。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.domain.core import ID, Digest, Timestamp
from packages.domain.protocol_source import ProtocolSource
from packages.domain.run_state import ResearchRunState


@dataclass(frozen=True, slots=True)
class ResearchRun:
    """Project 下的一次研究执行单元。

    manifest_digest 在 RunManifest 冻结后写入；为空表示尚未冻结。
    manifest_semantic_digest 是排除 frozen_at 的语义 digest，供 resume 时
    校验 plan/catalog/契约未漂移（WORKFLOW_RELIABILITY.md §8）；为空表示
    旧快照无语义校验能力，resume 必须拒绝而非静默放行。
    protocol_source 是"这份 run 由哪份协议装配"的冻结事实（路径或草稿修订）；
    为空表示该 run 早于来源登记（旧快照）——重启后的续跑**必须拒绝**，因为
    没有来源就无法重建 plan（GOAL-003 cycle 20）。
    """

    id: ID
    project_id: str
    protocol_id: str
    state: str = ResearchRunState.State.DRAFT
    manifest_digest: Digest | None = None
    manifest_semantic_digest: Digest | None = None
    # M15 定价冻结引用（BLOCKER-6）：RunManifest 冻结时写入；None = 该 run
    # 未冻结 pricing 引用（遗留 run 显式表达，投影绝不回落当期价表）。
    pricing_version: str | None = None
    pricing_digest: str | None = None
    # GOAL-003 cycle 20：装配来源。逐字段复制必须包含——漏掉任何一个字段都会
    # 在状态迁移时静默丢失冻结语义（本字段丢失 ⇒ 重启后续跑失去唯一装配入口）。
    protocol_source: ProtocolSource | None = None
    created_at: Timestamp = field(default_factory=Timestamp.now)
    updated_at: Timestamp = field(default_factory=Timestamp.now)

    def __post_init__(self) -> None:
        if not self.project_id:
            raise ValueError("project_id must not be empty")
        if not self.protocol_id:
            raise ValueError("protocol_id must not be empty")

    def transition(self, event: str) -> ResearchRun:
        """应用状态机迁移，返回携带新状态的新实例。

        非法迁移抛 InvalidTransitionError；terminal 状态无出边，
        天然不可回退。逐字段复制必须包含定价冻结引用——漏掉任何一个
        字段都会在状态迁移时静默丢失冻结语义。
        """
        next_state = ResearchRunState.transition(self.state, event)
        return ResearchRun(
            id=self.id,
            project_id=self.project_id,
            protocol_id=self.protocol_id,
            state=next_state,
            manifest_digest=self.manifest_digest,
            manifest_semantic_digest=self.manifest_semantic_digest,
            pricing_version=self.pricing_version,
            pricing_digest=self.pricing_digest,
            protocol_source=self.protocol_source,
            created_at=self.created_at,
            updated_at=Timestamp.now(),
        )

    def with_manifest(
        self,
        digest: Digest,
        semantic_digest: Digest | None = None,
        *,
        pricing_version: str | None = None,
        pricing_digest: str | None = None,
    ) -> ResearchRun:
        """记录冻结后的 Manifest digest（含语义 digest），状态不变。

        定价引用参数缺省时**保留本实例已有引用**（不静默丢弃）；冻结路径
        显式传入 manifest 携带的引用。
        """
        return ResearchRun(
            id=self.id,
            project_id=self.project_id,
            protocol_id=self.protocol_id,
            state=self.state,
            manifest_digest=digest,
            manifest_semantic_digest=semantic_digest,
            pricing_version=(
                pricing_version if pricing_version is not None else self.pricing_version
            ),
            pricing_digest=pricing_digest if pricing_digest is not None else self.pricing_digest,
            protocol_source=self.protocol_source,
            created_at=self.created_at,
            updated_at=Timestamp.now(),
        )

    def with_protocol_source(self, source: ProtocolSource | None) -> ResearchRun:
        """登记/保留装配来源（状态与其他冻结引用不变）；None 表示不覆盖既有值。"""
        return ResearchRun(
            id=self.id,
            project_id=self.project_id,
            protocol_id=self.protocol_id,
            state=self.state,
            manifest_digest=self.manifest_digest,
            manifest_semantic_digest=self.manifest_semantic_digest,
            pricing_version=self.pricing_version,
            pricing_digest=self.pricing_digest,
            protocol_source=source if source is not None else self.protocol_source,
            created_at=self.created_at,
            updated_at=Timestamp.now(),
        )

    @property
    def is_terminal(self) -> bool:
        return self.state in ResearchRunState.terminal()
