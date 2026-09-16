"""ops 调度写面的支持面（GOAL-003 EC-03 / PLAN-066）。

集中四件事：

- **registry 取用**：`registry_of` 未装配 → 503（不降级成"假装有调度面"）；
- **静态回落事实**：未装配 store 时，读面仍如实给出进程内守护线程的构造默认值
  （就是 EC-03 之前的 `_SCHEDULES`），只是 `management_available=False`；
- **DTO 投影**：定义（配置）与运行事实（本进程观测）合成一行，缺事实就是 null；
- **异常翻译**：`KeyError` → 404，名称/终态冲突 → 409，取值域 → 422。
"""

from __future__ import annotations

from typing import Any

from packages.application.ops.schedule_registry import ScheduleRegistry
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.schedule_store import ScheduleStore
from packages.domain.core import Timestamp
from packages.domain.ops_view import ScheduleEntry
from packages.domain.schedules import JOB_PURPOSE, ScheduleDefinition, ScheduleJob, ScheduleRuntime
from services.api.composition import ApiDeps
from services.api.dto.ops_schedules import ScheduleEntryDto, ScheduleJobDto
from services.api.errors import ApiError

REGISTRY_UNAVAILABLE_REASON = "调度定义读面不可用（控制面未装配 schedule store）"

SCHEDULE_NOTE = (
    "执行体仍是进程内守护线程：定义只决定 enabled/interval（下一轮生效），"
    "trigger 调用与定时 pass 相同的函数并写下同一份运行事实；新增定义只能绑定既有 "
    "job 词表——控件不新增执行路径，没有执行体的作业会在读面标注 executor_attached=false。"
)

#: 未装配 store 时的回落事实（守护线程构造默认值；只读、不可管理）。
FALLBACK_ENTRIES: tuple[ScheduleEntry, ...] = (
    ScheduleEntry(
        name="lease_recovery",
        interval_seconds=30.0,
        purpose="恢复过期 lease 并推进 LOST 转换",
        enabled=True,
    ),
    ScheduleEntry(
        name="outbox_relay",
        interval_seconds=5.0,
        purpose="中继 transactional outbox 事件",
        enabled=True,
    ),
    ScheduleEntry(
        name="retention",
        interval_seconds=3600.0,
        purpose="按 retention policy 清理 artifact",
        enabled=True,
    ),
    ScheduleEntry(
        name="worker_reaper",
        interval_seconds=15.0,
        purpose="标记心跳过期 worker 为 LOST",
        enabled=True,
    ),
)

#: 名称/终态冲突类消息片段（其余 InvalidInputError 视为取值域 → 422）。
_CONFLICT_FRAGMENTS = (
    "already exists",
    "cannot be deleted",
    "is disabled",
    "no executor attached",
)


def build_registry(store: ScheduleStore) -> ScheduleRegistry:
    """装配读/写共用的 registry（内置定义补齐：存在的不覆盖）。

    守护线程与 HTTP 写面必须拿到**同一个**实例，否则 trigger 会找不到执行体。
    """
    registry = ScheduleRegistry(store)
    registry.ensure_builtins()
    return registry


def registry_of(deps: ApiDeps) -> Any:
    registry = getattr(deps, "schedule_registry", None)
    if registry is None:
        raise ApiError(503, "Schedule Registry Unavailable", REGISTRY_UNAVAILABLE_REASON)
    return registry


def iso(value: Timestamp | None) -> str | None:
    return None if value is None else value.value.isoformat()


def job_dtos() -> list[ScheduleJobDto]:
    return [ScheduleJobDto(job=job.value, purpose=JOB_PURPOSE[job]) for job in ScheduleJob]


def fallback_dto(entry: ScheduleEntry) -> ScheduleEntryDto:
    """静态回落：无运行事实、无执行体标注（诚实：这些数字本来就不存在）。"""
    return ScheduleEntryDto(
        name=entry.name,
        job=entry.name,
        interval_seconds=entry.interval_seconds,
        purpose=entry.purpose,
        enabled=entry.enabled,
    )


def entry_dto(definition: ScheduleDefinition, runtime: ScheduleRuntime) -> ScheduleEntryDto:
    """定义（配置真相）+ 运行事实（本进程观测）→ 一行。"""
    return ScheduleEntryDto(
        name=definition.name,
        job=definition.job.value,
        interval_seconds=definition.interval_seconds,
        purpose=JOB_PURPOSE.get(definition.job, definition.job.value),
        enabled=definition.enabled,
        builtin=definition.builtin,
        note=definition.note,
        executor_attached=runtime.executor_attached,
        run_count=runtime.run_count,
        last_run_at=iso(runtime.last_run_at),
        last_outcome=runtime.last_outcome,
        last_error=runtime.last_error,
        next_due_at=iso(runtime.next_due_at),
    )


def translate(error: Exception) -> ApiError:
    """域/端口异常 → HTTP：未知 → 404；名称/终态冲突 → 409；取值域 → 422。"""
    if isinstance(error, KeyError):
        name = error.args[0] if error.args else "schedule"
        return ApiError(404, "Schedule Not Found", f"unknown schedule: {name}")
    message = str(error)
    if isinstance(error, InvalidInputError):
        if any(fragment in message for fragment in _CONFLICT_FRAGMENTS):
            return ApiError(409, "Schedule Conflict", message)
        return ApiError(422, "Invalid Schedule Definition", message)
    return ApiError(500, "Schedule Failure", message)
