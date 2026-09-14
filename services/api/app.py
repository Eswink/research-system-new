"""Control Plane API 应用工厂（inbound entry adapter）。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI

from services.api.composition import ApiDeps, assemble
from services.api.errors import register_error_handlers
from services.api.middleware import IdempotencyMiddleware
from services.api.routers import (
    approvals,
    artifacts,
    budget_forecast,
    deliverable,
    experiments,
    inspection,
    library,
    lineage,
    llm_endpoints,
    memory,
    models,
    notifications,
    operations,
    ops_view,
    projects,
    protocol_drafts,
    run_events,
    runs,
    team_custom,
    team_protocol,
    tool_providers,
)
from services.api.scheduler import (
    LeaseRecoveryScheduler,
    OutboxRelayScheduler,
    RetentionScheduler,
    WorkerReaperScheduler,
)
from services.api.settings import ApiSettings


def _register_health_route(app: FastAPI, deps: ApiDeps, version: str) -> None:
    """WP-A（PLAN-040）：`GET /health` 组成摘要（无秘密、无内容采样）。

    composition: canonical state 落点（postgres=PG 组成 / sqlite=开发组成）；
    pricing_degraded: 定价表加载降级可见（M15 可观测原则：配置损坏不得零信号）。
    """

    @app.get("/health", tags=["health"], include_in_schema=True)
    async def health() -> dict[str, str | bool]:
        from services.api.assembly import last_pricing_error

        return {
            "status": "ok",
            "version": version,
            "composition": "postgres" if getattr(deps, "_pg_connection", None) else "sqlite",
            "pricing_degraded": last_pricing_error() is not None,
        }


def _start_lease_scheduler(deps: ApiDeps) -> LeaseRecoveryScheduler | None:
    try:
        workflow = deps.runs._deps.workflow  # type: ignore[union-attr]
        sched = LeaseRecoveryScheduler(
            workflow, interval_seconds=30.0, telemetry=getattr(deps, "telemetry", None)
        )
        sched.start()
        return sched
    except Exception:
        return None


def _start_outbox_scheduler(deps: ApiDeps) -> "OutboxRelayScheduler | None":
    try:
        if not getattr(deps, "outbox_relay_enabled", False):
            return None

        sched = OutboxRelayScheduler(
            deps.runs._deps.workflow,  # type: ignore[union-attr]
            deps.events,
            interval_seconds=5.0,
            telemetry=getattr(deps, "telemetry", None),
        )
        sched.start()
        return sched
    except Exception:
        return None


def _start_retention_scheduler(deps: ApiDeps) -> "RetentionScheduler | None":
    if deps.artifacts is None:
        return None
    try:
        sched = RetentionScheduler(deps.artifacts, interval_seconds=3600.0)
        sched.start()
        return sched
    except Exception:
        return None


def _start_worker_reaper(deps: ApiDeps) -> "WorkerReaperScheduler | None":
    """M16 re-audit F-3: LOST detection must run in the production Control Plane.

    Gated on `deps.worker_registry`（PLAN-040 WP-A 起两条组成都提供：PG 与
    SQLite 开发路径）；the reaper flips heartbeat-expired workers to LOST from
    server time — it does not release leases (that stays
    `recover_expired_leases`, single authority).
    """
    registry = getattr(deps, "worker_registry", None)
    if registry is None:
        return None
    try:
        sched = WorkerReaperScheduler(
            registry,
            stale_threshold_seconds=30.0,
            interval_seconds=15.0,
            telemetry=getattr(deps, "telemetry", None),
        )
        sched.start()
        return sched
    except Exception:
        return None


def _stop_schedulers(
    reaper: "WorkerReaperScheduler | None",
    retention: "RetentionScheduler | None",
    outbox: "OutboxRelayScheduler | None",
    lease: "LeaseRecoveryScheduler | None",
) -> None:
    """Reverse-order daemon shutdown; a failing stop must not block the rest."""
    for sched in (reaper, retention, outbox):
        if sched is not None:
            try:
                sched.stop()
            except Exception:
                pass
    if lease is not None:
        lease.stop()


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Start/stop schedulers if workflow available (WP-E: lease recovery + PG outbox relay).

    M15: shutdown 时有界 flush/停 telemetry provider(FailSafe 吞错,不阻断停机)。
    M16 re-audit F-3: the worker reaper daemon joins the production lifecycle.
    """
    deps: ApiDeps | None = getattr(app.state, "deps", None)
    lease_sched: LeaseRecoveryScheduler | None = None
    outbox_sched: OutboxRelayScheduler | None = None
    retention_sched: RetentionScheduler | None = None
    reaper_sched: WorkerReaperScheduler | None = None
    telemetry = getattr(deps, "telemetry", None) if deps is not None else None
    if deps is not None and deps.runs is not None:
        lease_sched = _start_lease_scheduler(deps)
        outbox_sched = _start_outbox_scheduler(deps)
        retention_sched = _start_retention_scheduler(deps)
        reaper_sched = _start_worker_reaper(deps)
    yield
    _stop_schedulers(reaper_sched, retention_sched, outbox_sched, lease_sched)
    if telemetry is not None:
        shutdown = getattr(telemetry, "shutdown", None)
        if callable(shutdown):
            try:
                shutdown()
            except Exception:
                pass


def create_app(deps: ApiDeps | None = None) -> FastAPI:
    """创建控制面应用；deps 注入（生产 assemble()；测试注入 Fakes）。"""
    version = (
        Path(__file__).resolve().parents[2].joinpath("VERSION").read_text(encoding="utf-8").strip()
    )
    app = FastAPI(
        title="Research OS Control Plane API",
        description="Research Console 控制面：配置 / 探测 / 运行 / 审批 / 审计",
        version=version,
        lifespan=_lifespan,
    )
    resolved = deps if deps is not None else assemble(ApiSettings.from_env())
    app.state.deps = resolved
    _register_health_route(app, resolved, version)
    register_error_handlers(app)
    app.add_middleware(IdempotencyMiddleware)
    app.include_router(llm_endpoints.router)
    app.include_router(models.router)
    app.include_router(team_protocol.router)
    app.include_router(team_custom.router)
    app.include_router(runs.router)
    app.include_router(runs.projects_router)
    app.include_router(projects.router)
    app.include_router(run_events.router)
    app.include_router(approvals.router)
    app.include_router(inspection.router)
    app.include_router(operations.router)
    app.include_router(experiments.router)
    app.include_router(protocol_drafts.router)
    app.include_router(artifacts.router)
    app.include_router(memory.router)
    app.include_router(notifications.router)
    app.include_router(tool_providers.router)
    app.include_router(deliverable.router)
    app.include_router(lineage.router)
    app.include_router(library.router)
    app.include_router(ops_view.router)
    app.include_router(budget_forecast.router)
    return app
