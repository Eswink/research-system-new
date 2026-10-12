"""GOAL-20261012-059（序 27）：**时限链在产品面上可达** —— EC-03 的**产品路径**判据。

**为什么单列**：`tests/adapters/sqlite/test_program_nudge_bound_reachability.py` 判的是
「界能不能落库 / DTO 有没有这个键」（**声明面 + 落库面**）；本文件判**第三段**：
经**既有 HTTP 面**建程序、声明界、推进 ⇒ 出口**真的收到**信号。

**判的是什么（改动前做不到的形态）**：

- **界可声明**：`POST /projects/{id}/programs` 带 `gate_nudge_after_seconds` ⇒ 回执回显；
- **界可读回**：`GET /programs/{id}` 披露该声明（**经落库**，不是进程内回显）；
- **出口真的收到**：注入一个记录型出口 ⇒ 停在闸门那一次推进里，出口**收到了**一条通知
  （含 `declared_bound_seconds` = 声明值）—— 这正是「出口从不被注入」的反面；
- **缺省逐字不变**：不声明界 ⇒ 推进照样停闸门，但**出口为空**（不报超期）。

**如实边界**：本文件不判「真实外发」（明确不做）；出口是**进程内 seam**，注入的是记录型实现。
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.e2e.program_advance_support import advance, create_program, program_deps, read_program

_WAIT_FOR_APPROVAL = "WAIT_FOR_APPROVAL"
BOUND = 1


class _RecordingSink:
    """记录型出口（判「信号真的到了出口」的可复核证据）。"""

    def __init__(self) -> None:
        self.seen: list[Any] = []

    def nudge(self, notice: Any) -> None:
        self.seen.append(notice)

    @property
    def calls(self) -> tuple[object, ...]:
        return tuple(self.seen)


def _program_id(recent: dict[str, Any]) -> str:
    return str(recent["id"])


def test_the_declared_bound_round_trips_through_the_http_face() -> None:
    """EC-03 (a)：**界可声明**（建程序回执回显）+ **可读回**（读面披露，经落库）。"""
    with TestClient(create_app(program_deps())) as client:
        program = create_program(
            client, max_runs=3, human_gate_at_index=1, gate_nudge_after_seconds=BOUND
        )
        assert program["gate_nudge_after_seconds"] == BOUND, (
            "建程序回执必须回显界（此前该键不在 DTO 上）",
            program,
        )
        detail = read_program(client, _program_id(program))
        assert detail["gate_nudge_after_seconds"] == BOUND, (
            "读面必须披露界（经落库读回，不是进程内回显）",
            detail,
        )


def test_the_undeclared_bound_reads_back_as_none() -> None:
    """EC-03 反证臂①：**未声明** ⇒ 读面 `None`（既有行为逐字不变；**不**伪造成 0）。"""
    with TestClient(create_app(program_deps())) as client:
        program = create_program(client, max_runs=3, human_gate_at_index=1)
        assert program["gate_nudge_after_seconds"] is None, program
        assert read_program(client, _program_id(program))["gate_nudge_after_seconds"] is None


def test_an_injected_sink_receives_the_overdue_signal_on_the_product_path() -> None:
    """EC-03 (b)：**出口真的收到**信号 —— 产品面上（不是进程内直调驱动）。

    注入方式与判据同形（`ApiDeps.nudges`）；界声明为 1 秒、推进发生在 1 秒之后
    （`waited_since` = 上一轮 run 的 `updated_at`）⇒ 必超期。
    """
    import time

    sink = _RecordingSink()
    deps = program_deps()
    deps.nudges = sink
    with TestClient(create_app(deps)) as client:
        program = create_program(
            client, max_runs=3, human_gate_at_index=1, gate_nudge_after_seconds=BOUND
        )
        assert advance(client, _program_id(program))["decision"]["kind"] == "START"
        time.sleep(1.2)  # 让 waited_since（上一轮 run 的 updated_at）真的越过 1 秒界
        second = advance(client, _program_id(program))
        assert second["decision"]["kind"] == _WAIT_FOR_APPROVAL, second
        assert len(sink.seen) == 1, (
            "超期信号必须**真的交到注入的出口**（此前组合根从不注入 ⇒ 这条恒空）",
            sink.seen,
        )
        notice = sink.seen[0]
        assert notice.declared_bound_seconds == BOUND, notice
        assert notice.index == 1, notice
        assert any("nudge delivered" in item for item in second["decision"]["cited_facts"]), (
            "交付事实必须可读（判词点名）",
            second["decision"],
        )


def test_without_a_declared_bound_the_sink_stays_empty() -> None:
    """EC-03 反证臂②：**未声明界** ⇒ 推进照停闸门，但出口**为空**（不报超期）。

    与上一条配对（同一装配 / 同一注入）：唯一差别是**不发** `gate_nudge_after_seconds`。
    """
    import time

    sink = _RecordingSink()
    deps = program_deps()
    deps.nudges = sink
    with TestClient(create_app(deps)) as client:
        program = create_program(client, max_runs=3, human_gate_at_index=1)
        assert advance(client, _program_id(program))["decision"]["kind"] == "START"
        time.sleep(1.2)
        second = advance(client, _program_id(program))
        assert second["decision"]["kind"] == _WAIT_FOR_APPROVAL, second
        assert sink.seen == [], ("未声明界不得报超期（缺省形态逐字不变）", sink.seen)
        assert not any("nudge" in item for item in second["decision"]["cited_facts"]), (
            second["decision"]
        )
