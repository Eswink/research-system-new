"""历史 Run 快照迁移 CLI（M14 debt closure, WP-A）。

一键运营迁移：python tools/snapshot_migrate.py [--db PATH] [--pg-dsn DSN] [--dry-run|--apply]

- --dry-run（默认）：只扫描并输出 LegacyMigrationPlan，不写库。
- --apply：执行迁移（re-freeze 写回；fork 创建新 run，原 run 保持只读）。
- --db：SQLite RunStore 数据库路径（默认 scratch/tmp/legacy_runs.db）。
- --pg-dsn：可选；提供时使用 PostgresRunStore（生产 canonical state）。

refreeze 回调：加载 protocol + catalog + project + preflight context →
compile_and_preflight → freeze_manifest → 返回 (digest, semantic_digest)。
preflight 使用 Fake 凭据/策略 seam（本工具是运维 backfill，不执行真实
run；真实凭据校验由调用方在正式 run 路径负责）。

不泄漏 credentials；只输出 run_id/action/digest 摘要。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapters.fakes import FakeCredentialResolver, FakePolicyEvaluator
from adapters.fakes.budget_ledger import FakeBudgetLedger
from packages.application.ports import CatalogSnapshot, ProjectSettings
from packages.application.ports.resource_catalog import PreflightContext
from packages.application.ports.run_store import RunStore
from packages.application.preflight.preflight import (
    ManifestFreezeError,
    compile_and_preflight,
    freeze_manifest,
)
from packages.application.run_orchestration.snapshot_migration import (
    LegacyMigrationPlan,
    RefreezeCallback,
    apply_migration,
    plan_legacy_migration,
)
from packages.domain.enums import EndpointHealth
from packages.domain.run import ResearchRun
from services.api.catalog import load_catalog_snapshot, load_project_settings

_PROTOCOL_DIR = Path("examples/protocols")


def _load_protocol_path(protocol_id: str) -> str:
    """Map run.protocol_id to a protocol file under examples/protocols/.

    Legacy runs store protocol_id as the protocol's identity; the catalog
    convention maps `console_demo_research_v1` → `console_demo_research_v1.yaml`.
    Unknown protocols raise (the operator must supply a mapping).
    """
    for suffix in (".yaml", ".yml"):
        candidate = _PROTOCOL_DIR / f"{protocol_id}{suffix}"
        if candidate.is_file():
            return str(candidate)
    raise FileNotFoundError(f"no protocol file for {protocol_id!r}; provide protocol mapping")


def _build_refreeze(
    catalog: CatalogSnapshot,
    project: ProjectSettings,
    preflight_context: PreflightContext,
) -> RefreezeCallback:
    """Return a RefreezeCallback bound to catalog/project/preflight context."""

    def refreeze(run: ResearchRun) -> tuple[str, str]:
        from adapters.contracts.protocol_loaders import load_protocol

        protocol = load_protocol(_load_protocol_path(run.protocol_id))
        plan, report = compile_and_preflight(protocol, catalog, project, preflight_context)
        if plan is None or report.status.value == "FAIL":
            raise ManifestFreezeError(
                f"cannot refreeze {run.id.value}: preflight failed ({report.status.value})"
            )
        manifest = freeze_manifest(run.id.value, plan, report, preflight_context)
        return str(manifest.digest()), str(manifest.semantic_digest())

    return refreeze


def _open_store(args: argparse.Namespace) -> RunStore:
    if args.pg_dsn:
        from adapters.postgres.db import migrate as pg_migrate
        from adapters.postgres.run_store import PostgresRunStore

        pg_migrate(args.pg_dsn)
        return PostgresRunStore(dsn=args.pg_dsn)
    from adapters.sqlite.run_store import SqliteRunStore

    return SqliteRunStore(db_path=args.db)


def _render(plan: LegacyMigrationPlan) -> None:
    print(f"migrated: {plan.migrated_count}")
    for item in plan.runs:
        detail = ""
        if item.new_digest and item.new_semantic_digest:
            detail = f" -> {item.new_digest[:16]}... / {item.new_semantic_digest[:16]}..."
        print(f"  {item.action:10s} {item.run_id}  {item.reason}{detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Legacy ResearchRun snapshot migration")
    parser.add_argument("--db", default="scratch/tmp/legacy_runs.db", help="SQLite db path")
    parser.add_argument("--pg-dsn", default=None, help="PostgreSQL DSN (uses PostgresRunStore)")
    parser.add_argument("--project-id", default=None, help="filter by project (default all)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", help="scan only (default)")
    group.add_argument("--apply", action="store_true", help="execute migration")
    args = parser.parse_args(argv)

    catalog = load_catalog_snapshot()
    project = load_project_settings()
    credentials = FakeCredentialResolver()
    # backfill 语义校验：凭据可解析即可（refreeze 不执行 run，不发起真实
    # 调用）；真实凭据校验由正式 run 路径负责。与 M13 PG E2E seam 一致。
    credentials.register("LLM_MAIN_KEY", "sk-backfill-placeholder")
    preflight_context = PreflightContext(
        catalog=catalog,
        project=project,
        credentials=credentials,
        endpoint_health={eid: EndpointHealth.HEALTHY for eid in catalog.endpoints},
        provider_health={pid: True for pid in catalog.tool_providers},
        workspace_available={wid: True for wid in catalog.workspaces},
        budget_ledger=FakeBudgetLedger(),
        policy_evaluator=FakePolicyEvaluator(),
    )

    store = _open_store(args)
    try:
        runs = store.list_runs(args.project_id)
        plan = plan_legacy_migration(tuple(runs))
        if args.apply:
            refreeze = _build_refreeze(catalog, project, preflight_context)
            plan = apply_migration(plan, store, refreeze)
        _render(plan)
    finally:
        close = getattr(store, "close", None)
        if close is not None:
            close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
