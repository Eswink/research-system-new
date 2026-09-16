"""ScheduleRegistry：调度定义（可写）与运行事实（本进程观测）的唯一权威。

分工（GOAL-003 EC-03 的核心口径）：

```text
定义（持久化，可写）        ScheduleStore ← POST/PATCH 写面
执行体（进程内守护线程）    services/api/scheduler.py —— 每轮问 due(job)，跑完 record()
手动触发                    trigger(name) —— 调用与守护线程**同一个** pass 函数
运行事实（本进程）          run_count / last_run_at / last_outcome / next_due_at
```

**不新造调度器**：本类不做等待、不起线程；`due()` 只回答"现在该跑哪些定义"，
并把它们的下次到期时间推进（reserve），由调用方（既有守护线程）执行。

**写面必须被读面消费**：`enabled=False` 的定义不出现在 `due()` 里，读面的
`run_count` 因此停止增长——这是可证伪的证据，而不是响应体里的自述。
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, replace

from packages.application.ports.errors import InvalidInputError
from packages.application.ports.schedule_store import ScheduleStore
from packages.domain.core import Timestamp
from packages.domain.schedules import (
    BUILTIN_NAMES,
    BUILTIN_SCHEDULES,
    MAX_INTERVAL_SECONDS,
    MAX_NOTE_LENGTH,
    MIN_INTERVAL_SECONDS,
    ScheduleDefinition,
    ScheduleJob,
    ScheduleRuntime,
    validate_schedule_name,
)

#: 一次 pass 的结果口径（读面直接呈现；失败必须留痕，不伪装成功）。
OUTCOME_OK = "OK"
OUTCOME_FAILED = "FAILED"


@dataclass(slots=True)
class _Facts:
    run_count: int = 0
    last_run_at: Timestamp | None = None
    last_outcome: str | None = None
    last_error: str | None = None


class ScheduleRegistry:
    """线程安全：守护线程与 HTTP 请求线程并发访问（定义读写 + 事实回写）。"""

    def __init__(
        self,
        store: ScheduleStore,
        *,
        now: Callable[[], Timestamp] = Timestamp.now,
    ) -> None:
        self._store = store
        self._now = now
        self._lock = threading.Lock()
        self._executors: dict[ScheduleJob, Callable[[], object]] = {}
        self._facts: dict[str, _Facts] = {}
        self._next_due: dict[str, Timestamp] = {}

    # ── 执行体注册（守护线程启动时；进程内每个 job 至多一个执行体） ──

    def register_executor(self, job: ScheduleJob, run_pass: Callable[[], object]) -> None:
        with self._lock:
            self._executors[job] = run_pass

    def has_executor(self, job: ScheduleJob) -> bool:
        with self._lock:
            return job in self._executors

    # ── 定义（写面） ──

    def ensure_builtins(self) -> list[str]:
        """补齐缺失的平台内置定义（存在的不覆盖：启停/interval 由运维决定）。"""
        created: list[str] = []
        for definition in BUILTIN_SCHEDULES:
            if self._store.get_definition(definition.name) is None:
                self._store.save_definition(definition)
                created.append(definition.name)
        return created

    def definitions(self) -> list[ScheduleDefinition]:
        return sorted(self._store.list_definitions(), key=lambda item: item.name)

    def get(self, name: str) -> ScheduleDefinition | None:
        return self._store.get_definition(name)

    def create(
        self,
        *,
        name: str,
        job: ScheduleJob | str,
        interval_seconds: float,
        enabled: bool = True,
        note: str = "",
    ) -> ScheduleDefinition:
        """登记一条定义；名字冲突/保留名/取值非法 → `InvalidInputError`（控制面 409/422）。"""
        if name in BUILTIN_NAMES or self._store.get_definition(name) is not None:
            raise InvalidInputError(f"schedule name already exists: {name}")
        _validate(name, interval_seconds, note)
        definition = ScheduleDefinition(
            name=name,
            job=_coerce_job(job),
            interval_seconds=interval_seconds,
            enabled=enabled,
            builtin=False,
            note=note,
        )
        self._store.save_definition(definition)
        return definition

    def update(
        self,
        name: str,
        *,
        enabled: bool | None = None,
        interval_seconds: float | None = None,
    ) -> ScheduleDefinition:
        """启停 / 改 interval（作业类型不可变——那会把执行体绑定换掉）。未知 → `KeyError`。"""
        current = self._store.get_definition(name)
        if current is None:
            raise KeyError(name)
        if interval_seconds is not None:
            _validate(name, interval_seconds, current.note)
        updated = replace(
            current,
            enabled=current.enabled if enabled is None else enabled,
            interval_seconds=current.interval_seconds
            if interval_seconds is None
            else interval_seconds,
        )
        self._store.save_definition(updated)
        with self._lock:
            self._next_due.pop(name, None)
        return updated

    def delete(self, name: str) -> None:
        """删除自定义定义；内置定义不可删（执行体仍在，删掉只会让事实无主）。"""
        current = self._store.get_definition(name)
        if current is None:
            raise KeyError(name)
        if current.builtin:
            raise InvalidInputError(f"builtin schedule cannot be deleted: {name}")
        self._store.delete_definition(name)
        with self._lock:
            self._facts.pop(name, None)
            self._next_due.pop(name, None)

    # ── 执行体接口 ──

    def due(self, job: ScheduleJob) -> list[ScheduleDefinition]:
        """本 job 中"已启用且到期"的定义；返回即推进 `next_due`（reserve，不重复交付）。"""
        now = self._now()
        claimed: list[ScheduleDefinition] = []
        with self._lock:
            for definition in self._store.list_definitions():
                if definition.job is not job or not definition.enabled:
                    continue
                due_at = self._next_due.get(definition.name)
                if due_at is not None and due_at.value > now.value:
                    continue
                self._next_due[definition.name] = _plus(now, definition.interval_seconds)
                claimed.append(definition)
        return claimed

    def next_wait_seconds(self, job: ScheduleJob, fallback: float) -> float:
        """下一次可能到期的等待秒数。

        `fallback` 是守护线程**自身**的 interval，它始终是候选值——所以守护线程的节奏
        下界是"自己多久轮询一次"，定义只决定每轮**是否真的跑**（`due()` 授予与否）。

        **尚未预约的定义（`due_at is None`：刚创建 / 刚被重新启用）不参与候选**：
        定义"下一轮生效"，不能反过来让守护线程在进程启动瞬间抢跑（首版这里塞了 0.1，
        结果是四个守护线程在 app 起来的 100ms 后同时开跑，与启动期的其他初始化写并发，
        在共享连接上互相打断事务——见 RECHECK-066 W-9）。
        """
        now = self._now()
        candidates = [fallback]
        with self._lock:
            for definition in self._store.list_definitions():
                if definition.job is not job or not definition.enabled:
                    continue
                due_at = self._next_due.get(definition.name)
                if due_at is None:
                    continue
                candidates.append(max(0.1, (due_at.value - now.value).total_seconds()))
        return min(candidates)

    def record(self, name: str, *, outcome: str, error: str | None = None) -> ScheduleRuntime:
        """回写一次 pass 的事实（守护线程与 trigger 共用）。"""
        definition = self._store.get_definition(name)
        if definition is None:
            raise KeyError(name)
        now = self._now()
        with self._lock:
            facts = self._facts.setdefault(name, _Facts())
            facts.run_count += 1
            facts.last_run_at = now
            facts.last_outcome = outcome
            facts.last_error = error
            self._next_due[name] = _plus(now, definition.interval_seconds)
        return self.runtime(name)

    def trigger(self, name: str) -> ScheduleRuntime:
        """手动触发一次：与守护线程调用**同一个** pass 函数并回写同一份事实。

        未知 → `KeyError`（404）；无执行体 / 已停用 → `InvalidInputError`（409）。
        """
        definition = self._store.get_definition(name)
        if definition is None:
            raise KeyError(name)
        if not definition.enabled:
            raise InvalidInputError(f"schedule is disabled: {name}")
        with self._lock:
            runner = self._executors.get(definition.job)
        if runner is None:
            raise InvalidInputError(f"no executor attached for job {definition.job.value}: {name}")
        try:
            runner()
        except Exception as exc:  # noqa: BLE001 — 失败要留痕并如实返回，不伪装成功
            return self.record(name, outcome=OUTCOME_FAILED, error=str(exc))
        return self.record(name, outcome=OUTCOME_OK)

    # ── 读面 ──

    def runtime(self, name: str) -> ScheduleRuntime:
        definition = self._store.get_definition(name)
        if definition is None:
            raise KeyError(name)
        with self._lock:
            facts = self._facts.get(name, _Facts())
            next_due = self._next_due.get(name)
            attached = definition.job in self._executors
        return ScheduleRuntime(
            name=name,
            executor_attached=attached,
            run_count=facts.run_count,
            last_run_at=facts.last_run_at,
            last_outcome=facts.last_outcome,
            next_due_at=next_due if definition.enabled else None,
            last_error=facts.last_error,
        )

    def runtime_all(self) -> dict[str, ScheduleRuntime]:
        return {definition.name: self.runtime(definition.name) for definition in self.definitions()}


def _plus(now: Timestamp, seconds: float) -> Timestamp:
    from datetime import timedelta

    return Timestamp(now.value + timedelta(seconds=seconds))


def _coerce_job(job: ScheduleJob | str) -> ScheduleJob:
    """词表校验的唯一实现：控制面传来的字符串在域边界收敛成枚举。

    DTO 层不 import domain（架构门禁 `api-dto-purity`），所以词表校验落在本层；
    未知作业 → `InvalidInputError` 并**点名合法词表**（控制面 422 的文本据此可读）。
    """
    if isinstance(job, ScheduleJob):
        return job
    try:
        return ScheduleJob(job)
    except ValueError as exc:
        legal = ", ".join(member.value for member in ScheduleJob)
        raise InvalidInputError(f"unknown schedule job: {job} (valid: {legal})") from exc


def _validate(name: str, interval_seconds: float, note: str) -> None:
    """取值域校验：非法 → `InvalidInputError`（控制面 422），消息点名原因。"""
    try:
        validate_schedule_name(name)
    except ValueError as exc:
        raise InvalidInputError(str(exc)) from exc
    if not MIN_INTERVAL_SECONDS <= interval_seconds <= MAX_INTERVAL_SECONDS:
        raise InvalidInputError(
            f"interval_seconds must be within [{MIN_INTERVAL_SECONDS}, {MAX_INTERVAL_SECONDS}]"
        )
    if len(note) > MAX_NOTE_LENGTH:
        raise InvalidInputError(f"note must be <= {MAX_NOTE_LENGTH} characters")
