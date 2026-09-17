"""API 面：装配来源登记 + 重启后的重建续跑入口（GOAL-003 cycle 20 / PLAN-20260915-083）。

三件事必须从 HTTP 面成立（否则"重启后能续跑"只是库内能力）：

1. `POST /projects/{id}/runs` 真的把**协议来源**写进 canonical run 行（重建的唯一入口）；
2. 没有本进程上下文、来源又不可解析时，`POST /runs/{id}/resume` 明说重建被拒的原因，
   而不是含糊地报"没有续跑"；
3. 编排服务没装配时同样诚实拒绝（不伪装）。
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.core import ID
from packages.domain.protocol_source import ProtocolSource
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from services.api.run_resume import rebuild_and_resume

_PROTOCOL = "m12_reference_research_v1.yaml"


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _post(client: TestClient, path: str) -> Any:
    return client.post(path, headers={"Idempotency-Key": f"k-{uuid.uuid4()}"})


def test_starting_a_run_records_its_protocol_source(run_ready_client: TestClient) -> None:
    """来源随 run 落 canonical：重启后的重建入口靠的就是这一条事实。"""
    started = _post(
        run_ready_client,
        "/projects/example-project/runs",
    )
    assert started.status_code in (200, 422), "无 body 时按既有 422 语义拒绝"

    response = run_ready_client.post(
        "/projects/example-project/runs",
        json={"protocol_path": _PROTOCOL},
        headers={"Idempotency-Key": f"run-{uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    deps = _deps(run_ready_client)
    stored = deps.runs_store.get_run(response.json()["id"])

    assert stored.protocol_source == ProtocolSource(protocol_path=_PROTOCOL)
    # 该 run 在本夹具里收敛到 FAILED（ValueError 收敛分支），来源仍必须落行——
    # 失败收敛路径丢的是语义 digest（见 RECHECK-083 W-1），不是装配来源。
    assert stored.state == "FAILED"


def test_a_completed_run_carries_the_frozen_semantic_digest(client: TestClient) -> None:
    """成功的 run 必须把**冻结语义 digest** 过 HTTP 边界（漂移校验只认 run 行上这一条）。

    cycle 20 之前 `RunOutcome` 不带它，于是任何 API 启动的 run 都过不了 resume 的
    漂移校验——旧 resume 路径（进程内上下文）恰好绕开了这项检查，所以直到本轮
    重建入口才暴露。
    """
    credentials = cast(Any, client.app).state.deps.credentials
    credentials.register("LLM_MAIN_KEY", "sk-demo-key-0001")
    response = client.post(
        "/projects/example-project/runs",
        json={"protocol_path": "console_demo_research_v1.yaml"},
        headers={"Idempotency-Key": f"digest-{uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    stored = _deps(client).run_registry[response.json()["id"]]

    assert stored.state == "SUCCEEDED"
    assert stored.manifest_digest is not None
    assert stored.manifest_semantic_digest is not None
    assert stored.manifest_semantic_digest != stored.manifest_digest, "语义 digest 排除冻结时刻"


def test_resume_reports_why_a_rebuild_was_refused(run_ready_client: TestClient) -> None:
    """来源不可解析 ⇒ resume 明说重建被拒（含原因），并如实保持"无续跑"。"""
    deps = _deps(run_ready_client)
    run_id = str(ID.generate().value)
    parked = ResearchRun(
        id=ID(run_id),
        project_id="example-project",
        protocol_id="test_protocol",
        state=ResearchRunState.State.PAUSED,
        manifest_digest=None,
        protocol_source=ProtocolSource(protocol_path="examples/protocols/does-not-exist.yaml"),
    )
    deps.run_registry[run_id] = parked
    deps.runs_store.save_run(parked)

    resumed = _post(run_ready_client, f"/runs/{run_id}/resume")

    assert resumed.status_code == 200
    body = resumed.json()
    assert body["dispatch"] == "RELEASED"
    assert body["continuation"] == "NONE"
    assert "rebuild refused" in body["note"]
    assert "frozen manifest digest" in body["note"], "原因点名缺的是哪条事实"


def test_a_run_without_a_recorded_source_says_so(run_ready_client: TestClient) -> None:
    """早于来源登记的旧 run：拒绝原因点名"没有来源"，不猜协议、不换一份协议。"""
    deps = _deps(run_ready_client)
    run_id = str(ID.generate().value)
    legacy = ResearchRun(
        id=ID(run_id),
        project_id="example-project",
        protocol_id="test_protocol",
        state=ResearchRunState.State.PAUSED,
    )
    deps.run_registry[run_id] = legacy
    deps.runs_store.save_run(legacy)

    payload = _post(run_ready_client, f"/runs/{run_id}/resume").json()

    assert payload["continuation"] == "NONE"
    assert "no recorded protocol source" in payload["note"]


def test_without_an_orchestration_service_the_rebuild_refuses(run_ready_client: TestClient) -> None:
    """编排服务未装配 ⇒ 直接拒绝（不假装能重建）。"""
    deps = _deps(run_ready_client)
    attempt = rebuild_and_resume(
        replace(deps, runs=None),
        ResearchRun(
            id=ID.generate(),
            project_id="example-project",
            protocol_id="test_protocol",
            state=ResearchRunState.State.PAUSED,
            protocol_source=ProtocolSource(protocol_path=_PROTOCOL),
        ),
    )

    assert attempt.resumed is False
    assert attempt.refusal is not None and "not configured" in attempt.refusal
