"""调度定义域（GOAL-003 EC-03）：可写的 schedule 定义 + 运行事实。

与 `ops_view.ScheduleEntry`（只读静态事实）的关系：

- `ScheduleDefinition` 是**可写的配置**：name / job / interval / enabled；执行体仍是
  `services/api/scheduler.py` 的进程内守护线程——本域不调度、不执行，只定义"该跑什么、
  多久跑一次、开不开"。
- `ScheduleRuntime` 是**本进程的运行事实**（since process start）：last_run_at /
  run_count / last_outcome / next_due_at / 是否有执行体。进程重启后归零是诚实的
  语义（它是观测事实，不是配置）；配置保存在 store 里。

`job` 是受控词表（`ScheduleJob`）：新增定义只能绑定既有执行体类型，不能凭空造一个
没有执行体的作业——读面用 `executor_attached` 如实标注。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from packages.domain.core import Timestamp

MIN_INTERVAL_SECONDS = 1.0
MAX_INTERVAL_SECONDS = 86400.0
MAX_NOTE_LENGTH = 200

_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,40}$")


def validate_schedule_name(name: str) -> None:
    """名字契约的唯一实现（domain 构造与 registry 写面校验共用，避免两份正则漂移）。"""
    if _NAME_RE.fullmatch(name) is None:
        raise ValueError(
            "schedule name must match ^[a-z][a-z0-9_]{2,40}$ "
            "(lowercase, no dashes; e.g. outbox_relay_fast)"
        )


class ScheduleJob(StrEnum):
    """受控作业词表：每一项对应一个真实执行体（进程内守护线程）。"""

    LEASE_RECOVERY = "lease_recovery"
    OUTBOX_RELAY = "outbox_relay"
    RETENTION = "retention"
    WORKER_REAPER = "worker_reaper"


JOB_PURPOSE: dict[ScheduleJob, str] = {
    ScheduleJob.LEASE_RECOVERY: "恢复过期 lease 并推进 LOST 转换",
    ScheduleJob.OUTBOX_RELAY: "中继 transactional outbox 事件",
    ScheduleJob.RETENTION: "按 retention policy 清理 artifact",
    ScheduleJob.WORKER_REAPER: "把心跳过期的 worker 标记为 LOST",
}


@dataclass(frozen=True, slots=True)
class ScheduleDefinition:
    """一条可写调度定义；`builtin` 标记平台内置（不可删、名字保留）。"""

    name: str
    job: ScheduleJob
    interval_seconds: float
    enabled: bool = True
    builtin: bool = False
    note: str = ""

    def __post_init__(self) -> None:
        validate_schedule_name(self.name)
        if not MIN_INTERVAL_SECONDS <= self.interval_seconds <= MAX_INTERVAL_SECONDS:
            raise ValueError(
                f"interval_seconds must be within [{MIN_INTERVAL_SECONDS}, "
                f"{MAX_INTERVAL_SECONDS}], got {self.interval_seconds}"
            )
        if len(self.note) > MAX_NOTE_LENGTH:
            raise ValueError(f"note must be <= {MAX_NOTE_LENGTH} characters")


@dataclass(frozen=True, slots=True)
class ScheduleRuntime:
    """一条定义的本进程运行事实；`executor_attached=False` 表示当前没有执行体。"""

    name: str
    executor_attached: bool
    run_count: int = 0
    last_run_at: Timestamp | None = None
    last_outcome: str | None = None
    next_due_at: Timestamp | None = None
    last_error: str | None = None

    @property
    def last_outcome_or_unknown(self) -> str:
        return self.last_outcome if self.last_outcome is not None else "UNKNOWN"


# 平台内置四条定义（与 services/api/app.py 的守护线程默认值一致）；
# 首次启动时写入 store，之后启停/interval 由写面决定。
BUILTIN_SCHEDULES: tuple[ScheduleDefinition, ...] = (
    ScheduleDefinition(
        name=ScheduleJob.LEASE_RECOVERY.value,
        job=ScheduleJob.LEASE_RECOVERY,
        interval_seconds=30.0,
        builtin=True,
    ),
    ScheduleDefinition(
        name=ScheduleJob.OUTBOX_RELAY.value,
        job=ScheduleJob.OUTBOX_RELAY,
        interval_seconds=5.0,
        builtin=True,
    ),
    ScheduleDefinition(
        name=ScheduleJob.RETENTION.value,
        job=ScheduleJob.RETENTION,
        interval_seconds=3600.0,
        builtin=True,
    ),
    ScheduleDefinition(
        name=ScheduleJob.WORKER_REAPER.value,
        job=ScheduleJob.WORKER_REAPER,
        interval_seconds=15.0,
        builtin=True,
    ),
)

BUILTIN_NAMES: frozenset[str] = frozenset(item.name for item in BUILTIN_SCHEDULES)
