"""ops 调度写面（GOAL-003 EC-03 / PLAN-066）。

```text
GET    /ops/schedules                  定义（可写配置）+ 每项运行事实（本进程观测）
POST   /ops/schedules                  登记一条定义（job 取自平台词表）
PATCH  /ops/schedules/{name}           启停 / 改 interval
POST   /ops/schedules/{name}/trigger   手动触发一次 pass（立即执行，不等下一个 tick）
```

**被消费**：`enabled`/`interval_seconds` 由守护线程每一轮从同一份定义读出
（`ScheduleRegistry.due`），`trigger` 调用守护线程注册的**同一个** pass 函数
（`ScheduleRegistry.trigger`）——所以"写面生效"的证据是读面事实变化
（`run_count` 增长 / 停用后冻结），不是响应体自述。

诚实边界：未装配 schedule store → 读面回落静态事实并 `management_available=false`，
写面 503；未知 name → 404；内置名被占用 / 已停用 / 无执行体 → 409；
name 形状、interval 越界、job 不在词表 → 422。trigger 若 pass 失败仍返回 200，
但 `last_outcome=FAILED` + `last_error` 如实留痕（不伪装成功）。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from services.api.deps import get_deps
from services.api.dto.ops_schedules import (
    ScheduleCreateDto,
    ScheduleEntryDto,
    SchedulesViewDto,
    ScheduleUpdateDto,
)
from services.api.errors import ApiError
from services.api.schedule_support import (
    FALLBACK_ENTRIES,
    REGISTRY_UNAVAILABLE_REASON,
    SCHEDULE_NOTE,
    entry_dto,
    fallback_dto,
    job_dtos,
    registry_of,
    translate,
)

router = APIRouter(tags=["ops-schedules"])


def _dto_of(registry: Any, name: str) -> ScheduleEntryDto:
    definition = registry.get(name)
    if definition is None:
        raise ApiError(404, "Schedule Not Found", f"unknown schedule: {name}")
    return entry_dto(definition, registry.runtime(name))


@router.get("/ops/schedules", response_model=SchedulesViewDto)
def list_ops_schedules(request: Request) -> SchedulesViewDto:
    """调度定义 + 运行事实；未装配 store 时回落静态事实并说明原因。"""
    deps = get_deps(request)
    registry = getattr(deps, "schedule_registry", None)
    if registry is None:
        return SchedulesViewDto(
            schedules=[fallback_dto(entry) for entry in FALLBACK_ENTRIES],
            jobs=job_dtos(),
            note=SCHEDULE_NOTE,
            management_available=False,
            management_reason=REGISTRY_UNAVAILABLE_REASON,
        )
    return SchedulesViewDto(
        schedules=[
            entry_dto(definition, registry.runtime(definition.name))
            for definition in registry.definitions()
        ],
        jobs=job_dtos(),
        note=SCHEDULE_NOTE,
        management_available=True,
    )


@router.post("/ops/schedules", response_model=ScheduleEntryDto, status_code=201)
def create_ops_schedule(request: Request, body: ScheduleCreateDto) -> ScheduleEntryDto:
    """登记一条定义：name 不得重复、不得占用内置名（409）；取值域非法 → 422。

    新增定义绑定既有 job 词表：有执行体则立刻纳入该守护线程的下一轮 pass；
    没有执行体（例如本装配不跑 outbox relay）也照实登记，读面
    `executor_attached=false` 说明它暂时不会被跑。
    """
    registry = registry_of(get_deps(request))
    try:
        registry.create(
            name=body.name,
            job=body.job,
            interval_seconds=body.interval_seconds,
            enabled=body.enabled,
            note=body.note,
        )
    except Exception as exc:  # noqa: BLE001 — 逐类翻译成 HTTP，不吞成 500
        raise translate(exc) from exc
    return _dto_of(registry, body.name)


@router.patch("/ops/schedules/{name}", response_model=ScheduleEntryDto)
def update_ops_schedule(request: Request, name: str, body: ScheduleUpdateDto) -> ScheduleEntryDto:
    """启停 / 改 interval：下一轮守护线程读定义时生效（写面被读面消费）。"""
    registry = registry_of(get_deps(request))
    try:
        registry.update(name, enabled=body.enabled, interval_seconds=body.interval_seconds)
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return _dto_of(registry, name)


@router.post("/ops/schedules/{name}/trigger", response_model=ScheduleEntryDto)
def trigger_ops_schedule(request: Request, name: str) -> ScheduleEntryDto:
    """立即执行一次该定义对应的 pass，并写回与定时 pass 相同的运行事实。

    未知 name → 404；已停用 / 该作业无执行体 → 409。pass 自身失败不改变 HTTP 状态
    （请求成功了），但 `last_outcome=FAILED` 与 `last_error` 会落在响应里。
    """
    registry = registry_of(get_deps(request))
    try:
        registry.trigger(name)
    except Exception as exc:  # noqa: BLE001
        raise translate(exc) from exc
    return _dto_of(registry, name)
