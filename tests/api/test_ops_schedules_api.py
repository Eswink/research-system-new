"""ops 调度写面测试（GOAL-003 cycle 4 / EC-03）。

写面必须**被读面消费**，所以这里的断言落在事实变化上，不落在响应体自述上：

```text
POST   /ops/schedules                  登记定义（job 词表 / interval / name 校验）
PATCH  /ops/schedules/{name}           启停 / 改 interval
POST   /ops/schedules/{name}/trigger   立即跑一次，写回与定时 pass 相同的事实
```

关键证据：

- `executor_attached` 如实反映本装配里真的有没有执行体（只有 lease 守护线程在本
  装配里跑 ⇒ 其余三项为 false），未跑过的定义 `last_outcome` 为 null —— 不伪造成功；
- `enabled=false` 之后 `ScheduleRegistry.due()`（守护线程每轮读的入口）不再授予该
  定义，trigger 也 409 —— 这是"停用生效"的可证伪证据；
- `trigger` 与定时 pass 共用同一函数（测试里注入计数/失败 pass 证明），失败时 HTTP
  仍 200 但 `last_outcome=FAILED` + `last_error` 留痕。

未装配 schedule store 时的诚实边界（静态回落 + 写面 503）在最后一个用例里证伪。
"""

from __future__ import annotations

from dataclasses import replace
from itertools import count
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.schedules import ScheduleJob
from services.api.app import create_app
from tests.api.conftest import make_app_deps

_SEQ = count(1)

# 受控作业词表在本用例里的镜像（读面必须与 domain 的 ScheduleJob 一致）。
# cycle 19 起多了一个真实执行体：retry_dispatch（停车中的重排由守护线程按时续跑）。
_BUILTIN_NAMES = {
    "lease_recovery",
    "outbox_relay",
    "retention",
    "worker_reaper",
    "retry_dispatch",
}


def _headers(seed: str) -> dict[str, str]:
    """幂等键带自增后缀：同一路径的多次调用不能命中 replay（否则测的是缓存）。"""
    return {"Idempotency-Key": f"plan066-{seed}-{next(_SEQ)}"}


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _schedules(client: TestClient) -> dict[str, dict[str, Any]]:
    payload = client.get("/ops/schedules").json()
    return {item["name"]: item for item in payload["schedules"]}


def _create(
    client: TestClient,
    name: str,
    job: str,
    interval_seconds: float = 60.0,
    **extra: Any,
) -> Any:
    body = {"name": name, "job": job, "interval_seconds": interval_seconds, **extra}
    return client.post("/ops/schedules", json=body, headers=_headers("create"))


def _patch(client: TestClient, name: str, **body: Any) -> Any:
    return client.patch(f"/ops/schedules/{name}", json=body, headers=_headers("patch"))


def _trigger(client: TestClient, name: str) -> Any:
    return client.post(f"/ops/schedules/{name}/trigger", headers=_headers("trigger"))


def test_read_surface_reports_executor_attachment_honestly(client: TestClient) -> None:
    payload = client.get("/ops/schedules").json()
    assert payload["management_available"] is True
    assert payload["management_reason"] is None
    assert payload["note"]

    jobs = {item["job"] for item in payload["jobs"]}
    assert jobs == _BUILTIN_NAMES
    assert all(item["purpose"] for item in payload["jobs"])

    entry = _schedules(client)["worker_reaper"]
    assert entry["builtin"] is True
    # 本装配只跑 lease 守护线程（retention/outbox/reaper 未装配依赖）⇒ 如实为 False
    assert entry["executor_attached"] is False
    assert entry["run_count"] == 0
    # 没跑过就是没有事实：null，而不是编一个成功结论
    assert entry["last_run_at"] is None
    assert entry["last_outcome"] is None
    assert entry["next_due_at"] is None

    assert _schedules(client)["lease_recovery"]["executor_attached"] is True


def test_create_validates_vocabulary_interval_and_names(client: TestClient) -> None:
    unknown_job = _create(client, "relay_fast", "not_a_job")
    assert unknown_job.status_code == 422, unknown_job.text
    assert "worker_reaper" in unknown_job.text  # 422 消息点名合法词表

    assert _create(client, "too_fast", "retention", 0.5).status_code == 422
    assert _create(client, "Bad-Name", "retention").status_code == 422
    assert _create(client, "lease_recovery", "lease_recovery").status_code == 409

    created = _create(client, "relay_fast", "outbox_relay", 60.0, note="e2e")
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["builtin"] is False
    assert body["enabled"] is True
    assert body["interval_seconds"] == 60.0
    assert body["purpose"] == "中继 transactional outbox 事件"
    assert body["executor_attached"] is False  # 本装配没跑 outbox relay：如实标注

    assert _create(client, "relay_fast", "outbox_relay", 90.0).status_code == 409


def test_patch_toggle_is_consumed_by_the_executor_read_surface(client: TestClient) -> None:
    # 先停用内置的 outbox_relay：该 job 下只留被测定义，证据才没有旁路解释
    assert _patch(client, "outbox_relay", enabled=False).status_code == 200
    assert _create(client, "relay_fast", "outbox_relay", 60.0).status_code == 201
    registry = _deps(client).schedule_registry
    assert [item.name for item in registry.due(ScheduleJob.OUTBOX_RELAY)] == ["relay_fast"]

    disabled = _patch(client, "relay_fast", enabled=False)
    assert disabled.status_code == 200, disabled.text
    assert disabled.json()["enabled"] is False
    assert disabled.json()["next_due_at"] is None
    # 守护线程每轮读的就是这个入口：停用后不再授予 ⇒ 下一轮不会产生运行事实
    assert registry.due(ScheduleJob.OUTBOX_RELAY) == []
    assert _trigger(client, "relay_fast").status_code == 409

    resumed = _patch(client, "relay_fast", enabled=True, interval_seconds=120.0)
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["enabled"] is True
    assert resumed.json()["interval_seconds"] == 120.0
    assert _schedules(client)["relay_fast"]["interval_seconds"] == 120.0
    assert [item.name for item in registry.due(ScheduleJob.OUTBOX_RELAY)] == ["relay_fast"]


def test_trigger_runs_registered_pass_and_records_facts(client: TestClient) -> None:
    assert _create(client, "reap_extra", "worker_reaper", 60.0).status_code == 201
    registry = _deps(client).schedule_registry

    def boom() -> None:
        raise RuntimeError("reaper pass exploded")

    registry.register_executor(ScheduleJob.WORKER_REAPER, boom)
    failed = _trigger(client, "reap_extra")
    assert failed.status_code == 200, failed.text  # 请求成功；pass 失败要留痕
    assert failed.json()["run_count"] == 1
    assert failed.json()["last_outcome"] == "FAILED"
    assert failed.json()["last_error"] == "reaper pass exploded"
    assert failed.json()["last_run_at"] is not None

    calls: list[str] = []
    registry.register_executor(ScheduleJob.WORKER_REAPER, lambda: calls.append("pass"))
    ok = _trigger(client, "reap_extra")
    assert ok.status_code == 200, ok.text
    assert calls == ["pass"]  # trigger 跑的就是注册进来的同一条 pass
    assert ok.json()["run_count"] == 2
    assert ok.json()["last_outcome"] == "OK"
    assert ok.json()["last_error"] is None

    assert _trigger(client, "no_such_schedule").status_code == 404
    # 有定义但没有执行体：409（不假装跑过）
    unattached = _trigger(client, "retention")
    assert unattached.status_code == 409, unattached.text
    assert "no executor attached" in unattached.text


def test_write_surface_is_honest_without_registry() -> None:
    deps = replace(make_app_deps(), schedule_registry=None, schedule_store=None)
    client = TestClient(create_app(deps), raise_server_exceptions=False)
    payload = client.get("/ops/schedules").json()
    assert payload["management_available"] is False
    assert payload["management_reason"]
    assert {item["name"] for item in payload["schedules"]} == _BUILTIN_NAMES
    # 回落事实没有运行事实可给：字段是空的，不是编的
    assert all(item["last_outcome"] is None for item in payload["schedules"])

    assert _create(client, "relay_fast", "outbox_relay").status_code == 503
    assert _patch(client, "relay_fast", enabled=False).status_code == 503
    assert _trigger(client, "relay_fast").status_code == 503
