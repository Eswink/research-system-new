"""Run 存取辅助（M13-R1 WP-M1）。

M13-R1 修复：run_registry（内存 dict）在 API 重启后丢失全部 run 状态，
且 /runs/{id}/events 被内存注册表 gate 挡住（事件已持久仍 404）。
读取路径 runs_store（SQLite）优先、run_registry 兼容回退（测试注入）；
写入路径双写（注册表 + 持久化）。
"""

from __future__ import annotations

from packages.domain.run import ResearchRun
from services.api.composition import ApiDeps
from services.api.errors import ApiError


def get_run_or_error(deps: ApiDeps, run_id: str) -> ResearchRun:
    """run 读取：runs_store 优先（重启后可恢复），注册表兼容回退。"""
    if deps.runs_store is not None:
        try:
            return deps.runs_store.get_run(run_id)
        except KeyError:
            pass
    run = deps.run_registry.get(run_id)
    if run is None:
        raise ApiError(404, "Not Found", f"run not found: {run_id}")
    return run


def save_run(deps: ApiDeps, run: ResearchRun) -> None:
    """run 写入：注册表（测试兼容）+ 持久化（重启恢复）。"""
    deps.run_registry[run.id.value] = run
    if deps.runs_store is not None:
        deps.runs_store.save_run(run)
