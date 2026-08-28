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
    experiments,
    inspection,
    llm_endpoints,
    models,
    run_events,
    runs,
    team_protocol,
)
from services.api.scheduler import (
    LeaseRecoveryScheduler,
    OutboxRelayScheduler,
    RetentionScheduler,
)
from services.api.settings import ApiSettings


def _start_lease_scheduler(deps: ApiDeps) -> LeaseRecoveryScheduler | None:
    try:
        workflow = deps.runs._deps.workflow  # type: ignore[union-attr]
        sched = LeaseRecoveryScheduler(workflow, interval_seconds=30.0)
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


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Start/stop schedulers if workflow available (WP-E: lease recovery + PG outbox relay)."""
    deps: ApiDeps | None = getattr(app.state, "deps", None)
    lease_sched: LeaseRecoveryScheduler | None = None
    outbox_sched: OutboxRelayScheduler | None = None
    retention_sched: RetentionScheduler | None = None
    if deps is not None and deps.runs is not None:
        lease_sched = _start_lease_scheduler(deps)
        outbox_sched = _start_outbox_scheduler(deps)
        retention_sched = _start_retention_scheduler(deps)
    yield
    if retention_sched is not None:
        try:
            retention_sched.stop()
        except Exception:
            pass
    if outbox_sched is not None:
        try:
            outbox_sched.stop()
        except Exception:
            pass
    if lease_sched is not None:
        lease_sched.stop()


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
    app.state.deps = deps if deps is not None else assemble(ApiSettings.from_env())
    register_error_handlers(app)
    app.add_middleware(IdempotencyMiddleware)
    app.include_router(llm_endpoints.router)
    app.include_router(models.router)
    app.include_router(team_protocol.router)
    app.include_router(runs.router)
    app.include_router(runs.projects_router)
    app.include_router(run_events.router)
    app.include_router(approvals.router)
    app.include_router(inspection.router)
    app.include_router(experiments.router)
    return app
