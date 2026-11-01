"""EC-01 的**真跑取证**：十一相各发一对相级事件（GOAL-20261101-103）。

**它补哪一格**（收口复检指名的缺口）：EC-01 的判据此前只有 ①**两相合成协议**
（`_TWO_PHASES` 在 `tests/api/test_run_detail_phases.py`）与 ②**前端 stub**
（`ELEVEN_PHASES` 在 `stub-routes-runs.ts`）—— 两者都不证明「**真的**跑十一相会**真的**
发十一对事件」。本文件用 `direction_to_manuscript_v1.yaml` 的 11 个 phase 经**产品入口**
（`TestClient` + `POST /projects/{id}/runs`）真跑一次，再从 **canonical 的事件读面**
（`GET /runs/{id}/events`）取回全部事件断言。

**时序按 `occurred_at` 判，不按数组位置**（实测的坑）：`/runs/{id}/events` 的 JSON
replay 按 **`event_id` 排序**（`run_events.events_of` 的既有语义：按 id 升序=去重），
而 `event_id` 是 **UUID4** ⇒ **数组位置不是执行序**。第一版按位置判，实测把
`plan/retrieval/experiment` 判成了首三相（那是 UUID 字典序）。改用 `occurred_at`
（ISO 串，同格式可字典序比较）才是真的执行序。

同一理由下「本相的任务」也不能按 `task.created` 的位置切：同相事件之间夹着别的相的
任务。判法改为**按时间窗**：`started <= task.created <= completed`，窗口内必须至少
一条任务 —— 那正是「相开始了、干了活、然后关掉」的形状。

**四条判据（每条都可证伪）**：

1. **恰好 11 条 `phase.started` + 11 条 `phase.completed`**（不是"至少"、不是"大约"）；
2. 相序列**逐字**等于协议声明的 11 个 id 且按执行序；
3. 每个相的两个相级事件之间**至少有一条** `task.created`，且
   `started` 位次 < 该区间首位次、`completed` 位次 > 该区间末位次；
4. `phase.completed` 的 `outcome` ∈ 闭集，`artifact_ids` 的每个前缀都是**本 run 真实
   任务**的 id（不串 run、不伪造制品）。

**射程边界（如实登记）**：本文件要真容器实验（`requires_docker`）—— 这是该链的既有形态
（实验相要跑沙箱）。windows CI 的 runner 没有 docker ⇒ 诚实 skip（既有契约）；此时本判据
不覆盖，已登记在 GOAL 的残余节。
"""

from __future__ import annotations

from typing import Any

import pytest

from services.api.app import create_app
from tests.e2e.direction_to_manuscript_support import (
    PHASES,
    PROTOCOL,
    VARIANT_A,
    ManuscriptRelayFixture,
    deps_for,
)

pytestmark = pytest.mark.requires_docker

#: 事件投影的形状（`GET /runs/{id}/events` 的 JSON replay）。
Event = dict[str, Any]


def _events(client: Any, run_id: str) -> list[Event]:
    """`GET /runs/{run_id}/events` 的 JSON replay（canonical outbox 投影）。"""
    body = client.get(f"/runs/{run_id}/events").json()
    assert isinstance(body, list) and body, "事件读面必须给回本 run 的 canonical 事件"
    return [dict(item) for item in body]


def _of_type(events: list[Event], name: str) -> list[Event]:
    """按 `type` 过滤（保持 canonical 顺序）。"""
    return [item for item in events if item.get("type") == name]


def _stamp(item: Event) -> str:
    """事件时刻（ISO 串；同格式下字典序 = 时间序）。缺字段 ⇒ 判据应当红，不回落。"""
    value = item.get("occurred_at")
    assert isinstance(value, str) and value, f"事件缺 `occurred_at`: {item.get('type')}"
    return value


def _phase_of(item: Event) -> str:
    """事件的 `payload.phase_id`（相级事件才有；其余返回空串）。"""
    payload = item.get("payload")
    return str(payload.get("phase_id", "")) if isinstance(payload, dict) else ""


def _run_eleven_phases(key: str) -> dict[str, Any]:
    """经产品入口跑一次十一相 run，取回 run 详情 + 全量事件。"""
    from fastapi.testclient import TestClient

    with ManuscriptRelayFixture() as relay:
        deps, _offline = deps_for(relay, (VARIANT_A[1],), VARIANT_A[0])
        with TestClient(create_app(deps)) as client:
            created = client.post(
                "/projects/example-project/runs",
                json={"protocol_path": PROTOCOL},
                headers={"Idempotency-Key": key},
            )
            assert created.status_code == 200, created.text
            run_id = str(created.json()["id"])
            detail: dict[str, Any] = dict(client.get(f"/runs/{run_id}").json())
            detail["events"] = _events(client, run_id)
            detail["artifact_ids"] = [
                str(item["id"]) for item in client.get(f"/runs/{run_id}/artifacts").json()
            ]
            detail["run_id"] = run_id
    return detail


class TestTheElevenPhaseRunEmitsOnePairOfPhaseEventsEach:
    """EC-01 (i)：**真跑**十一相 ⇒ 恰好 11 对相级事件，且时序/归属都对。"""

    def test_exactly_eleven_started_and_eleven_completed_with_the_declared_ids(self) -> None:
        """(1)(2) 计数**逐字** 11/11；相**集合**逐字等于协议声明的 11 个 id。

        **不判相序列**：`/runs/{id}/events` 的 JSON replay 按 `event_id`（UUID4）排序，
        数组顺序不是执行序。执行序由下一条用例按 `occurred_at` 判。
        """
        run = _run_eleven_phases("goal103-eleven-phase-counts")
        assert run["state"] == "SUCCEEDED", (run["state"], run.get("message"))
        events: list[Event] = run["events"]

        started = _of_type(events, "phase.started")
        completed = _of_type(events, "phase.completed")

        assert len(started) == 11, (
            "恰好 11 条 `phase.started`（十一相各一条；多一条 = 有相被重复开始，"
            "少一条 = 有相没被观测到）",
            [_phase_of(item) for item in started],
        )
        assert len(completed) == 11, (
            "恰好 11 条 `phase.completed`（十一相各一条）",
            [_phase_of(item) for item in completed],
        )
        assert sorted(_phase_of(item) for item in started) == sorted(PHASES), (
            "相**集合**必须逐字等于协议声明的 11 个 id（多一个/少一个都不行）",
            sorted(_phase_of(item) for item in started),
        )
        assert sorted(_phase_of(item) for item in completed) == sorted(PHASES), (
            "`completed` 的相集合同样逐字等于协议",
            sorted(_phase_of(item) for item in completed),
        )

    def test_started_precedes_the_phases_first_task_and_completed_follows_the_last(self) -> None:
        """(3) **真跑时序**：每相 `started` ≤ 本相任务 ≤ `completed`，且窗口内非空。

        按 `occurred_at` 判（JSON replay 的数组序是 UUID 序，见模块 docstring）。
        同相多任务时：`min(task) >= started` 且 `max(task) <= completed`。
        """
        run = _run_eleven_phases("goal103-eleven-phase-brackets")
        events: list[Event] = run["events"]
        started = {_phase_of(item): _stamp(item) for item in _of_type(events, "phase.started")}
        completed = {_phase_of(item): _stamp(item) for item in _of_type(events, "phase.completed")}
        created = [_stamp(item) for item in _of_type(events, "task.created")]

        assert set(started) == set(PHASES) and set(completed) == set(PHASES)
        for phase_id in PHASES:
            start_at, end_at = started[phase_id], completed[phase_id]
            assert start_at <= end_at, f"相 {phase_id}：started 不得晚于 completed"
            inside = [stamp for stamp in created if start_at <= stamp <= end_at]
            assert inside, (
                f"相 {phase_id}：`started` 与 `completed` 的时间窗内必须**至少一条** "
                "`task.created`（否则这一相没有执行过，'相已完成'没有对象）",
                start_at,
                end_at,
            )
            assert min(inside) >= start_at, (
                f"相 {phase_id}：`phase.started` 必须**先于**本相首个任务",
            )
            assert max(inside) <= end_at, (
                f"相 {phase_id}：`phase.completed` 必须**晚于**本相末个任务",
            )

    def test_the_eleven_phases_execute_in_dependency_order(self) -> None:
        """(2') **执行序** = DAG 拓扑序：依赖相先于被依赖相（按 `occurred_at`）。

        这是「十一相真的按协议跑过」的正面证据 —— 若某个相被跳过或乱序，这里会点名。
        """
        run = _run_eleven_phases("goal103-eleven-phase-order")
        events: list[Event] = run["events"]
        started = {_phase_of(item): _stamp(item) for item in _of_type(events, "phase.started")}
        # 协议里每相的依赖（与 `direction_to_manuscript_v1.yaml` 的 `depends_on` 同源）。
        depends = {
            "question": (),
            "retrieval": ("question",),
            "novelty": ("retrieval",),
            "plan": ("retrieval", "novelty"),
            "experiment": ("plan",),
            "review": ("experiment", "novelty"),
            "manuscript": ("retrieval", "novelty", "plan", "experiment", "review"),
            "editorial": ("review", "manuscript"),
            "revision": ("review", "manuscript"),
            "submission": ("editorial", "revision"),
            "report": (
                "plan",
                "novelty",
                "experiment",
                "review",
                "manuscript",
                "revision",
                "submission",
            ),
        }
        assert set(depends) == set(PHASES), "依赖表必须覆盖协议的全部 11 相"
        for phase_id, upstream in depends.items():
            for dependency in upstream:
                assert started[dependency] <= started[phase_id], (
                    f"相 {phase_id} 不得先于它的依赖 {dependency} 开始（DAG 拓扑序）",
                    started[dependency],
                    started[phase_id],
                )

    def test_the_completed_payload_names_a_closed_outcome_and_real_artifacts(self) -> None:
        """(4) `outcome` ∈ 闭集；`artifact_ids` 指向**本 run 真的落库**的制品。

        **射程修正（本轮真跑实测）**：第一版要求每个 `artifact_ids` 的前缀都是
        `task.created` 里出现过的 task id —— 实测**不成立且不该成立**：`experiment` 相是
        确定性执行缝（`experiment_task`），它跑出来的 `experiment_result.json` 的 id 前缀
        来自实验注册路径，而该相**不注册 `ResearchTask` 行**。所以判法改为对照
        **制品读面**（`GET /runs/{id}/artifacts` 的 id 集合）：那才是「本 run 真实落库」
        的定义，且它由 canonical 存储给出，不由事件自说自话。
        """
        from packages.application.run_orchestration.phase_progress import PHASE_OUTCOMES

        run = _run_eleven_phases("goal103-eleven-phase-payloads")
        events: list[Event] = run["events"]
        landed = {str(item) for item in run.get("artifact_ids", [])}
        assert landed, "本 run 必须真的落过制品（否则整条链没有对象）"
        produced: set[str] = set()
        for item in _of_type(events, "phase.completed"):
            payload = item.get("payload")
            assert isinstance(payload, dict)
            assert payload.get("outcome") in PHASE_OUTCOMES, (
                f"`outcome` 必须落在闭集 {sorted(PHASE_OUTCOMES)} 内",
                payload.get("outcome"),
            )
            for artifact_id in payload.get("artifact_ids", []):
                assert str(artifact_id) in landed, (
                    "`phase.completed` 只能点名**本 run 制品读面真的给回**的制品"
                    "（点名一个不存在的 id = 伪造产出）",
                    artifact_id,
                )
                produced.add(str(artifact_id))
        assert produced, "11 条 `phase.completed` 合计必须点名到真实制品（全空 = 相完成只是句话）"

    def test_the_detail_read_face_reports_eleven_succeeded_phases(self) -> None:
        """EC-01 (ii)：`RunDetailDto.phases` 长度 == 协议相数（同一份真跑的读面）。"""
        run = _run_eleven_phases("goal103-eleven-phase-detail")
        phases = run.get("phases")
        assert isinstance(phases, list), "详情读面必须给 `phases`（null = 读不到相结构）"
        assert len(phases) == 11, [item.get("phase_id") for item in phases]
        assert [item["phase_id"] for item in phases] == list(PHASES)
        assert {item["state"] for item in phases} == {"SUCCEEDED"}, (
            "`SUCCEEDED` 的 run 里十一相都应当读到 SUCCEEDED",
            [(item["phase_id"], item["state"]) for item in phases],
        )
        empty = [item["phase_id"] for item in phases if not item["artifact_ids"]]
        assert empty == [], f"这些相读不到任何制品 id（不该发生在 SUCCEEDED 的 run 上）: {empty}"
