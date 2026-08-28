"""历史 Run 快照迁移 use case（M14 debt 收口）。

背景：`manifest_semantic_digest=None` 的旧快照（M14 之前 SQLite 时代或
早期产物）不可 resume——`convergence.assert_semantics_frozen` 安全拒绝
（ManifestFreezeError）。本 use case 提供显式、可审计的运营迁移路径，
不改变默认行为：

- `plan_legacy_migration(runs)`：纯函数，扫描缺失 digest 的 run，产出
  `LegacyMigrationPlan`（每个 run 标注 re-freeze / fork / keep 建议）。
- `RefreezeCallback`：调用方注入的"重新冻结"闭包（加载 protocol →
  compile_and_preflight → freeze_manifest），返回新的 digest 对。
  依赖注入保持本模块不依赖具体 loader/catalog 装配。
- `apply_migration(plan, store, refreeze)`：执行迁移，幂等（重复调用
  不再产生新迁移）。

安全边界（与 convergence.py 一致）：未迁移的旧快照仍然拒绝 resume；
迁移工具是显式 opt-in 运营动作，不是自动 backfill。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from packages.application.ports.run_store import RunStore
from packages.domain.run import ResearchRun


@dataclass(frozen=True, slots=True)
class RunMigrationDecision:
    """单个 run 的迁移决策。"""

    run_id: str
    action: str  # "re-freeze" | "fork" | "keep"
    reason: str
    new_digest: str | None = None
    new_semantic_digest: str | None = None


@dataclass(frozen=True, slots=True)
class LegacyMigrationPlan:
    """一次扫描的迁移计划（dry-run 与 apply 共用）。"""

    runs: tuple[RunMigrationDecision, ...] = ()
    migrated_count: int = 0

    @property
    def needs_action(self) -> bool:
        return any(item.action in ("re-freeze", "fork") for item in self.runs)


class RefreezeCallback(Protocol):
    """调用方注入的重新冻结闭包。

    输入旧 run（用于 run_id/project_id/protocol_id），输出冻结后的
    digest 对。失败（例如 protocol 已不可加载）应抛 ManifestFreezeError。
    """

    def __call__(self, run: ResearchRun) -> tuple[str, str]: ...


def _needs_migration(run: ResearchRun) -> bool:
    return run.manifest_digest is None or run.manifest_semantic_digest is None


def _classify(run: ResearchRun) -> RunMigrationDecision:
    """单 run 迁移分类（plan_legacy_migration 的纯函数辅助）。

    - 缺失 digest 且 state 为 DRAFT/COMPILING/PREFLIGHT（未冻结）：keep，
      原因"未冻结 run 无需迁移（重新走 start_run 即重新冻结）"。
    - 缺失 semantic digest 但有 manifest_digest（旧冻结快照）：re-freeze，
      原因"旧快照可重算语义 digest 后恢复 resume 能力"。
    - 缺失 manifest_digest 且 state 为 RUNNING/PAUSED（异常状态）：fork，
      原因"冻结信息缺失，必须 fork-run 才能继续；原 run 保留只读历史"。
    - terminal 状态（SUCCEEDED/FAILED/CANCELLED）缺失 digest：keep，
      原因"终态 run 不可 resume，无需迁移（保留只读历史）"。
    """
    run_id = run.id.value
    if not _needs_migration(run):
        return RunMigrationDecision(run_id=run_id, action="keep", reason="already migrated")
    if run.state in ("DRAFT", "COMPILING", "PREFLIGHT", "READY"):
        return RunMigrationDecision(
            run_id=run_id, action="keep", reason="unfrozen run; re-run start_run to freeze"
        )
    if run.state in ("SUCCEEDED", "FAILED", "CANCELLED"):
        return RunMigrationDecision(
            run_id=run_id, action="keep", reason="terminal run is read-only; no resume needed"
        )
    if run.manifest_digest is not None and run.manifest_semantic_digest is None:
        return RunMigrationDecision(
            run_id=run_id,
            action="re-freeze",
            reason="legacy frozen snapshot; recompute semantic digest",
        )
    return RunMigrationDecision(
        run_id=run_id,
        action="fork",
        reason="missing frozen manifest; fork-run required to continue",
    )


def plan_legacy_migration(runs: tuple[ResearchRun, ...]) -> LegacyMigrationPlan:
    """扫描 run 列表，产出迁移计划（不写库）。"""
    return LegacyMigrationPlan(runs=tuple(_classify(run) for run in runs))


def apply_migration(
    plan: LegacyMigrationPlan,
    store: RunStore,
    refreeze: RefreezeCallback,
) -> LegacyMigrationPlan:
    """执行迁移计划（幂等）。

    - re-freeze：调用 refreeze 重算 digest 对 → save_run 写回。
    - fork：refreeze 后创建新 run（新 id、新 digest 对、state=READY），
      原 run 保持不动（只读历史）。
    - keep：跳过。
    重复 apply 同一 plan：already migrated 的 run 不在 plan 中（plan 由
    plan_legacy_migration 重新扫描生成），因此天然幂等。
    """
    migrated = [_apply_one(decision, store, refreeze) for decision in plan.runs]
    return LegacyMigrationPlan(
        runs=tuple(migrated),
        migrated_count=sum(1 for item in migrated if item.action in ("re-freeze", "fork")),
    )


def _apply_one(
    decision: RunMigrationDecision,
    store: RunStore,
    refreeze: RefreezeCallback,
) -> RunMigrationDecision:
    """执行单个迁移决策（apply_migration 的辅助；幂等）。"""
    if decision.action == "keep":
        return decision
    run = store.get_run(decision.run_id)
    if not _needs_migration(run):
        # 并发/重复执行：已被其他调用迁移，视为已处理
        return RunMigrationDecision(run_id=run.id.value, action="keep", reason="already migrated")
    digest, semantic_digest = refreeze(run)
    if decision.action == "re-freeze":
        store.save_run(_with_digests(run, digest, semantic_digest))
        return RunMigrationDecision(
            run_id=run.id.value,
            action="re-freeze",
            reason=decision.reason,
            new_digest=digest,
            new_semantic_digest=semantic_digest,
        )
    forked = _fork_run(run, digest, semantic_digest)
    store.save_run(forked)
    return RunMigrationDecision(
        run_id=forked.id.value,
        action="fork",
        reason=f"fork of {run.id.value}",
        new_digest=digest,
        new_semantic_digest=semantic_digest,
    )


def _with_digests(run: ResearchRun, digest: str, semantic_digest: str) -> ResearchRun:
    from packages.domain.core import Digest

    return ResearchRun(
        id=run.id,
        project_id=run.project_id,
        protocol_id=run.protocol_id,
        state=run.state,
        manifest_digest=Digest.parse(digest),
        manifest_semantic_digest=Digest.parse(semantic_digest),
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


def _fork_run(run: ResearchRun, digest: str, semantic_digest: str) -> ResearchRun:
    from packages.domain.core import ID, Digest, Timestamp

    return ResearchRun(
        id=ID.generate(),
        project_id=run.project_id,
        protocol_id=run.protocol_id,
        state="READY",
        manifest_digest=Digest.parse(digest),
        manifest_semantic_digest=Digest.parse(semantic_digest),
        created_at=Timestamp.now(),
        updated_at=Timestamp.now(),
    )
