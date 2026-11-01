"""相级进度读面的 HTTP 形状（GOAL-20261101-103 EC-01）。

**事实来源**（三份，全部只读，不新增迁移、不新增表）：

1. **相结构**：`run.protocol_body`（run 自己冻结的那份协议正文，GOAL-004 cycle 1）。
   **不读磁盘上"现在的"那份协议**——那份可能已经变了，而这条 run 是用旧字节装配的。
   这也是 `run_execution_view` 的同一条纪律（读面回读 run 记得的那份事实）。
2. **任务状态**：`RunProjection.list_tasks(run_id)`（canonical 投影，与
   `GET /runs/{id}/tasks` 同一份读）。
3. **相级事件**：outbox 里的 `phase.started` / `phase.completed`（EC-01 新发的）。
   它们提供 `started_at` / `completed_at` 两个**时刻**；「相有没有跑完」这件事**不**由
   「有没有收到 completed 事件」判 —— 有任务状态可判时以任务状态为准（见 `_state`）。
   理由：事件可能因为旧 run、或因为执行循环在 completed 之前失败而不存在，那不等于
   任务没跑；而任务状态是 canonical。

**四态推导（`PHASE_STATES` 闭集）**，按此顺序：

- 本相**没有**任何任务（协议声明的相但未分派）⇒ `PENDING`；
- 本相任务全部处于 `CREATED` / `QUEUED`（**还没被领走**）⇒ `PENDING`。这一格是本轮
  实测发现的语义缝：把它们算进 `RUNNING` 会让「排在那儿还没轮到」被读成「正在跑」；
- 有任务 `FAILED` / `DEAD_LETTER` ⇒ `FAILED`（失败优先于「还有一半在跑」：它已经坏了）；
- 有任务未到终态 ⇒ `RUNNING`；
- 其余（全部终态、无失败）⇒ `SUCCEEDED`。

**`protocol_body` 缺失 ⇒ `None`**（不是 `[]`）：旧 run 没有冻结正文 ⇒ 相结构**读不到**，
与「协议里没有相」是两件事，读面必须分得开。
"""

from __future__ import annotations

from typing import Any

from services.api.dto.runs import PhaseProgressDto
from services.api.protocol_source import parse_frozen_protocol

#: 已到终态的任务状态（与 `ResearchTaskState.terminal()` 同集合；此处按**取值**比较，
#: 避免让读面依赖状态机内部表）。
_TERMINAL = frozenset({"SUCCEEDED", "FAILED", "DEAD_LETTER", "CANCELLED"})
#: **还没开始跑**的状态：任务行存在，但它没有被任何派发方领走或执行。
#: 这一格是本轮实测发现的语义缝：把它算进 `RUNNING` 会让「排在那儿还没轮到」被读成
#: 「正在跑」——两者的出路完全不同（一个要等，一个已经在动）。`QUEUED` 同理：
#: 它已经进队但仍未执行。
_NOT_STARTED = frozenset({"CREATED", "QUEUED"})
#: 终态里**算失败**的那几个（`CANCELLED` 不是失败：它可能是用户取消整条 run）。
_FAILED = frozenset({"FAILED", "DEAD_LETTER"})


def _phase_state(statuses: list[str]) -> str:
    """一个相的状态（四态闭集；见模块 docstring 的推导规则）。

    顺序有意义：先判「有没有真的开始」（全部 `_NOT_STARTED` ⇒ `PENDING`），再判失败
    （失败优先于"还有一半在跑" —— 一个相里既有失败又有未完成时，读面给 `FAILED` 更
    诚实：它已经坏了，不是"还在努力"）。
    """
    if not statuses:
        return "PENDING"
    if all(status in _NOT_STARTED for status in statuses):
        return "PENDING"
    if any(status in _FAILED for status in statuses):
        return "FAILED"
    if any(status not in _TERMINAL for status in statuses):
        return "RUNNING"
    return "SUCCEEDED"


def _phase_definitions(run: Any) -> list[tuple[str, str, tuple[str, ...]]]:
    """冻结协议正文 → `[(phase_id, strategy, contract_ids)]`（**按协议声明顺序**）。

    `contract_ids` 取自 phase 的 `task_contracts`（含 `task_contract` 那一条 —— 域对象
    在 `__post_init__` 里已经把它并进去）⇒ 一个相声明多个合约时逐条给出，不挑一个。
    """
    body = getattr(run, "protocol_body", None)
    if body is None:
        return []
    protocol = parse_frozen_protocol(body)
    return [
        (phase.id, str(phase.strategy), tuple(phase.task_contracts)) for phase in protocol.phases
    ]


def _event_times(projection: Any, run_id: str) -> dict[str, tuple[str | None, str | None]]:
    """本 run 的相级事件 → `{phase_id: (started_at, completed_at)}`（取**最后**一条）。"""
    from packages.domain.events import EventType

    times: dict[str, tuple[str | None, str | None]] = {}
    if projection is None:
        return times
    for envelope in projection.events(run_id):
        if envelope.event_type not in (EventType.PHASE_STARTED, EventType.PHASE_COMPLETED):
            continue
        phase_id = envelope.payload.get("phase_id")
        if not isinstance(phase_id, str) or not phase_id:
            continue
        started, completed = times.get(phase_id, (None, None))
        stamp = envelope.occurred_at.value.isoformat()
        if envelope.event_type is EventType.PHASE_STARTED:
            started = stamp
        else:
            completed = stamp
        times[phase_id] = (started, completed)
    return times


def _task_to_contract(rows: tuple[tuple[Any, Any], ...]) -> dict[str, str]:
    """`{task_id: contract_id}`（相归属的唯一依据：任务行上的合约）。"""
    return {task.id.value: contract.id for task, contract in rows}


def _artifact_owner(artifact_id: str, task_ids: set[str]) -> str | None:
    """制品 → 产出它的 task id（命名约定 `{task_id}:{name}`；不属于任何任务 ⇒ `None`）。

    与 `routers/artifacts.py::_task_prefixed` 同一条约定（那一条判的是「是不是本 run
    的」；这一条判「是本 run 里**哪个任务**的」）。取不到 ⇒ `None`，不猜。
    """
    prefix = artifact_id.split(":", 1)[0]
    return prefix if prefix in task_ids else None


def _produced_by_task(store: Any, task_ids: set[str]) -> dict[str, set[str]]:
    """`{task_id: {artifact ids}}`（只取命名约定能归属到本 run 任务的制品）。

    用 `list_refs()`（既有读面）而不是 evidence 反查：evidence 扫描是
    `_run_artifact_ids` 的做法（它要回答「本 run 有哪些制品」），这里只要「谁产出的」，
    按**标识前缀**一次扫描即可，不引入 N+1 的证据链回读。`store` 为 `None` ⇒ 空表
    （读面照常给相结构与状态，只是制品列表为空 —— 这是如实的缺口，不编造）。
    """
    owned: dict[str, set[str]] = {}
    if store is None:
        return owned
    for artifact in store.list_refs():
        task_id = _artifact_owner(str(artifact.id), task_ids)
        if task_id is not None:
            owned.setdefault(task_id, set()).add(str(artifact.id))
    return owned


def run_phases_dto(run: Any, projection: Any, store: Any = None) -> list[PhaseProgressDto] | None:
    """run → `RunDetailDto.phases`；**没有冻结协议正文 ⇒ `None`**（见模块 docstring）。"""
    body = getattr(run, "protocol_body", None)
    if body is None:
        return None
    definitions = _phase_definitions(run)
    run_id = run.id.value
    rows: tuple[tuple[Any, Any], ...] = projection.list_tasks(run_id) if projection else ()
    by_contract: dict[str, list[str]] = {}
    for task, contract in rows:
        by_contract.setdefault(contract.id, []).append(task.status)
    owner = _task_to_contract(rows)
    by_owner = _produced_by_task(store, set(owner))
    times = _event_times(projection, run_id)
    phases: list[PhaseProgressDto] = []
    for phase_id, strategy, contracts in definitions:
        statuses = [s for cid in contracts for s in by_contract.get(cid, [])]
        produced: set[str] = set()
        for task_id, ids in by_owner.items():
            if owner[task_id] in contracts:
                produced.update(ids)
        started, completed = times.get(phase_id, (None, None))
        phases.append(
            PhaseProgressDto(
                phase_id=phase_id,
                strategy=strategy,
                state=_phase_state(statuses),
                artifact_ids=sorted(produced),
                started_at=started,
                completed_at=completed,
            )
        )
    return phases


__all__ = ["run_phases_dto"]
