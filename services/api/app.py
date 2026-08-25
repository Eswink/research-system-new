"""Control Plane API 应用工厂（inbound entry adapter）。"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from services.api.composition import ApiDeps, assemble
from services.api.errors import register_error_handlers
from services.api.middleware import IdempotencyMiddleware
from services.api.routers import (
    approvals,
    inspection,
    llm_endpoints,
    models,
    run_events,
    runs,
    team_protocol,
)
from services.api.settings import ApiSettings


def create_app(deps: ApiDeps | None = None) -> FastAPI:
    """创建控制面应用；deps 注入（生产 assemble()；测试注入 Fakes）。"""
    version = (
        Path(__file__).resolve().parents[2].joinpath("VERSION").read_text(encoding="utf-8").strip()
    )
    app = FastAPI(
        title="Research OS Control Plane API",
        description="Research Console 控制面：配置 / 探测 / 运行 / 审批 / 审计",
        version=version,
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
    return app
