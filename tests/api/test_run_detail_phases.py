"""`RunDetailDto.phases`：相级进度的**读面**（GOAL-20261101-103 EC-01）。

**它封住的失败形态**：`phase.started` / `phase.completed` 都发了，但读面不披露 ⇒ 前端
仍然只能显示"这条 run 是 RUNNING"。事件是**写给消费者**的，不是写给自己看的。

判据分三层（缺一层就有假绿的空间）：

1. **相结构取自 run 自己冻结的协议正文**，不是磁盘上"现在的"那份。判法：把冻结正文
   改成只有两相，磁盘那份仍有十一相 ⇒ 读面必须只给两相。这一条同时证明"改磁盘协议
   不会漂移读面"。
2. **状态四态推导**（`PHASE_STATES` 闭集）逐态各一条；
3. **`protocol_body` 缺失 ⇒ `None`**（不是 `[]`）：旧 run 的相结构**读不到**，与"协议里
   没有相"是两件事。
"""

from __future__ import annotations

from typing import Any

import pytest

from packages.domain.core import ID, Digest
from packages.domain.protocol_source import ProtocolBody
from packages.domain.run import ResearchRun
from services.api.dto.runs import PHASE_STATES
from services.api.run_phase_view import run_phases_dto

_RUN_ID = "5b6c7d8e-9f0a-4b1c-8d2e-3f4a5b6c7d8e"

_TWO_PHASES = """
id: probe_protocol_v0_1_0
version: 0.1.0
phases:
  - id: question
    strategy: single_agent
    required_roles:
      - {role: research_director, min_instances: 1, max_instances: 1}
    task_contract: research_question_proposal
    outputs: [research_question]
  - id: plan
    strategy: map_reduce
    required_roles:
      - {role: research_director, min_instances: 1, max_instances: 1}
    task_contract: research_plan_proposal
    outputs: [research_plan]
"""


def _body(text: str = _TWO_PHASES) -> ProtocolBody:
    return ProtocolBody(text=text, digest=Digest.of_bytes(text.encode("utf-8")))


def _run(*, body: Any = "default") -> ResearchRun:
    """`body` 缺省给冻结正文；显式传 `None` ⇒ 构造一条**没有冻结正文**的 run。"""
    if body == "default":
        body = _body()
    return ResearchRun(
        id=ID(_RUN_ID),
        project_id="example-project",
        protocol_id="probe_protocol",
        protocol_body=body,
    )


class _Task:
    def __init__(self, task_id: str, status: str) -> None:
        self.id = ID(task_id)
        self.status = status


class _Contract:
    def __init__(self, contract_id: str) -> None:
        self.id = contract_id


class _Projection:
    """最小实时投影：只实现本读面用到的 `list_tasks` / `events`。"""

    def __init__(
        self, rows: list[tuple[_Task, _Contract]], events: list[Any] | None = None
    ) -> None:
        self._rows = rows
        self._events = events or []

    def list_tasks(self, run_id: str) -> tuple[tuple[_Task, _Contract], ...]:
        assert run_id == _RUN_ID
        return tuple(self._rows)

    def events(self, run_id: str) -> tuple[Any, ...]:
        assert run_id == _RUN_ID
        return tuple(self._events)


class _Artifact:
    def __init__(self, artifact_id: str) -> None:
        self.id = artifact_id


class _Store:
    def __init__(self, ids: list[str]) -> None:
        self._artifacts = [_Artifact(item) for item in ids]

    def list_refs(self) -> tuple[_Artifact, ...]:
        return tuple(self._artifacts)


def _rows(*statuses: str) -> list[tuple[_Task, _Contract]]:
    """按顺序给 question / plan 两相各派一个任务（合约名与协议逐字对应）。"""
    contracts = ["research_question_proposal", "research_plan_proposal"]
    return [
        (_Task(str(ID.generate().value), status), _Contract(contracts[index]))
        for index, status in enumerate(statuses)
    ]


# ------------------------------------------------------------------ 相结构来自冻结正文


def test_the_phase_count_comes_from_the_frozen_protocol_body_not_the_disk_file() -> None:
    """**相结构只认 run 冻结的那份字节**：磁盘上的十一相协议与它无关。"""
    phases = run_phases_dto(_run(), _Projection(_rows("CREATED", "CREATED")), _Store([]))

    assert phases is not None
    assert [phase.phase_id for phase in phases] == ["question", "plan"], (
        "冻结正文只有两相（`direction_to_manuscript_v1.yaml` 有十一相，但那是磁盘上的）"
    )
    assert [phase.strategy for phase in phases] == ["single_agent", "map_reduce"]


def test_a_run_without_a_frozen_body_reports_none_not_an_empty_list() -> None:
    """`protocol_body is None` ⇒ `None`。`[]` 会被读成"协议里没有相"，那是另一件事。"""
    assert run_phases_dto(_run(body=None), _Projection([]), _Store([])) is None


# ----------------------------------------------------------------------------- 四态推导


@pytest.mark.parametrize(
    ("question_status", "expected"),
    [
        # 未终态 ⇒ PENDING（相里的任务还没到终态）
        ("CREATED", "PENDING"),
        ("RUNNING", "RUNNING"),
        # 终态且无失败 ⇒ SUCCEEDED
        ("SUCCEEDED", "SUCCEEDED"),
        # FAILED / DEAD_LETTER 都算失败（死信不是成功）
        ("FAILED", "FAILED"),
        ("DEAD_LETTER", "FAILED"),
        # CANCELLED 不是失败（可能是用户取消了整条 run）
        ("CANCELLED", "SUCCEEDED"),
    ],
)
def test_the_phase_state_follows_the_canonical_task_statuses(
    question_status: str, expected: str
) -> None:
    """状态由**任务 canonical 状态**推出，不由"有没有收到 completed 事件"推。

    第二相的任务固定 `CREATED` ⇒ 它独立地给出 `PENDING`：两相各自判，不互相污染。
    """
    phases = run_phases_dto(_run(), _Projection(_rows(question_status, "CREATED")), _Store([]))

    assert phases is not None
    assert [phase.state for phase in phases] == [expected, "PENDING"]
    assert expected in PHASE_STATES


def test_a_phase_without_any_task_is_pending() -> None:
    """协议声明的相但一条任务都没分派 ⇒ `PENDING`（不跳过这个相）。"""
    phases = run_phases_dto(_run(), _Projection([]), _Store([]))

    assert phases is not None
    assert len(phases) == 2, "未分派的相仍然要出现在读面上（否则进度条会少一格）"
    assert [phase.state for phase in phases] == ["PENDING", "PENDING"]


# ------------------------------------------------------------------- 事件时刻与真实制品


def test_the_event_times_are_read_from_the_phase_events() -> None:
    """`started_at` / `completed_at` 来自相级事件（读面不自己造时刻）。"""
    from packages.domain.core import Timestamp
    from packages.domain.events import EventEnvelope, EventType, digest_of_payload

    def envelope(event_type: EventType, phase_id: str, payload_extra: dict[str, object]) -> Any:
        payload = {"phase_id": phase_id, **payload_extra}
        return EventEnvelope(
            event_id=f"e-{event_type.value}-{phase_id}",
            event_type=event_type,
            schema_version="1",
            occurred_at=Timestamp.now(),
            actor="system:test",
            scope=f"run:{_RUN_ID}",
            payload=payload,
            payload_digest=digest_of_payload(payload),
            run_id=_RUN_ID,
        )

    events = [
        envelope(
            EventType.PHASE_STARTED, "question", {"strategy": "single_agent", "contract_ids": []}
        ),
        envelope(
            EventType.PHASE_COMPLETED, "question", {"outcome": "SUCCEEDED", "artifact_ids": []}
        ),
    ]
    phases = run_phases_dto(_run(), _Projection(_rows("SUCCEEDED", "CREATED"), events), _Store([]))

    assert phases is not None
    assert phases[0].started_at is not None
    assert phases[0].completed_at is not None
    assert phases[1].started_at is None, "第二相没有事件 ⇒ 时刻为空（不补造）"
    assert phases[1].completed_at is None


def test_the_artifact_list_is_scoped_to_the_phase_that_produced_it() -> None:
    """制品按**产出它的任务**归到相（命名约定 `{task_id}:{name}`；未归属的不进任一相）。"""
    rows = _rows("SUCCEEDED", "SUCCEEDED")
    question_task = rows[0][0].id.value
    store = _Store([
        f"{question_task}:research_question",
        "not-a-task-id:something_else",
    ])

    phases = run_phases_dto(_run(), _Projection(rows), store)

    assert phases is not None
    assert phases[0].artifact_ids == [f"{question_task}:research_question"]
    assert phases[1].artifact_ids == [], "第二相没产出任何制品 ⇒ 空列表（不把第一相的制品复制过来）"


def test_no_artifact_store_still_yields_phases_with_empty_lists() -> None:
    """没有制品存储 ⇒ 相结构与状态照常给，制品列表为空（**如实的缺口**，不编造）。"""
    phases = run_phases_dto(_run(), _Projection(_rows("SUCCEEDED", "SUCCEEDED")), None)

    assert phases is not None
    assert [phase.artifact_ids for phase in phases] == [[], []]
    assert [phase.state for phase in phases] == ["SUCCEEDED", "SUCCEEDED"]


def test_the_phase_states_vocabulary_matches_the_documented_closed_set() -> None:
    """DTO 导出的 `PHASE_STATES` 就是四态闭集（不得悄悄加第五个值）。"""
    assert PHASE_STATES == ("PENDING", "RUNNING", "SUCCEEDED", "FAILED")


def test_the_detail_route_publishes_the_phases_and_the_list_route_does_not() -> None:
    """**哪条路径披露什么**是显式的（与 `execution` 同一条 N+1 纪律）。

    判法按 AST 读：`_detail_dto` 里 `phases` 必须由 `with_execution` 门控 ——
    「列表路径不带相进度」这件事不能靠巧合。
    """
    import ast
    from pathlib import Path

    source = Path("services/api/routers/runs.py").read_bytes().decode("utf-8")
    tree = ast.parse(source)
    gate = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.IfExp)
        and isinstance(node.body, ast.Call)
        and getattr(node.body.func, "id", "") == "run_phases_dto"
    ]
    assert gate, "`run_phases_dto(...)` 必须出现在一个三元表达式里（按 with_execution 门控）"
