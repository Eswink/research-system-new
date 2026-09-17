"""API 面：装配来源登记 + 重启后的重建续跑入口（GOAL-003 cycle 20 / PLAN-20260915-083）。

三件事必须从 HTTP 面成立（否则"重启后能续跑"只是库内能力）：

1. `POST /projects/{id}/runs` 真的把**协议来源**写进 canonical run 行（重建的唯一入口）；
2. 没有本进程上下文、来源又不可解析时，`POST /runs/{id}/resume` 明说重建被拒的原因，
   而不是含糊地报"没有续跑"；
3. 编排服务没装配时同样诚实拒绝（不伪装）。

GOAL-004 cycle 1 追加第四件：**冻结正文**（`protocol_body`）随 run 落 canonical，
重建不再依赖那份外部来源文件还在——同一组用例同时证明"文件消失后仍能重建"与
"换一份正文会被拒绝"。
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.core import ID, Digest
from packages.domain.protocol_source import ProtocolBody, ProtocolSource
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from services.api.run_resume import rebuild_and_resume

_PROTOCOL = "m12_reference_research_v1.yaml"
_DEMO_PROTOCOL = "console_demo_research_v1.yaml"
_PROTOCOLS_DIR = Path(__file__).resolve().parents[2] / "examples" / "protocols"


@contextmanager
def _temp_protocol(source_name: str) -> Iterator[tuple[str, Path]]:
    """受控模板的临时副本：真实文件，用完即删——用来量"来源消失后还能不能重建"。"""
    name = f"frozen-body-{uuid.uuid4().hex}.yaml"
    path = _PROTOCOLS_DIR / name
    path.write_text((_PROTOCOLS_DIR / source_name).read_text(encoding="utf-8"), encoding="utf-8")
    try:
        yield name, path
    finally:
        path.unlink(missing_ok=True)


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


def _canonical(client: TestClient, run_id: str) -> ResearchRun:
    """canonical 读面：有 run store 走 store，基础装配（无 store）走注册表。"""
    deps = _deps(client)
    if deps.runs_store is not None:
        return cast(ResearchRun, deps.runs_store.get_run(run_id))
    return cast(ResearchRun, deps.run_registry[run_id])


def _start_demo_run(client: TestClient, protocol_path: str) -> ResearchRun:
    """用受控模板跑一次真 run（Fake runtime 快速终态），返回 canonical 行。"""
    cast(Any, client.app).state.deps.credentials.register("LLM_MAIN_KEY", "sk-demo-key-0001")
    response = client.post(
        "/projects/example-project/runs",
        json={"protocol_path": protocol_path},
        headers={"Idempotency-Key": f"frozen-{uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    return _canonical(client, response.json()["id"])


def _park(run: ResearchRun, **overrides: object) -> ResearchRun:
    """以既有 run 的冻结事实构造"同一条 run 的停车态"。

    保留原 id 不是细节：语义 digest 覆盖 `run_id`，换一个 id 就不再是"这条 run"，
    重建时会因为 digest 对不上被诚实拒绝（这正是校验在起作用，不是可以绕开的噪声）。
    """
    base: dict[str, object] = {
        "id": run.id,
        "project_id": run.project_id,
        "protocol_id": run.protocol_id,
        "state": ResearchRunState.State.PAUSED,
        "manifest_digest": run.manifest_digest,
        "manifest_semantic_digest": run.manifest_semantic_digest,
        "protocol_source": run.protocol_source,
        "protocol_body": run.protocol_body,
    }
    base.update(overrides)
    return ResearchRun(**base)  # type: ignore[arg-type]


def _save_parked(client: TestClient, parked: ResearchRun) -> str:
    deps = _deps(client)
    deps.run_registry[parked.id.value] = parked
    if deps.runs_store is not None:
        deps.runs_store.save_run(parked)
    return parked.id.value


def test_a_started_run_freezes_the_protocol_body(run_ready_client: TestClient) -> None:
    """正文随 run 落 canonical（AC-01）：digest 等于那份被解析字节的 sha256，读面可见。"""
    stored = _start_demo_run(run_ready_client, _DEMO_PROTOCOL)
    expected = (_PROTOCOLS_DIR / _DEMO_PROTOCOL).read_text(encoding="utf-8")

    assert stored.protocol_body is not None, "启动时必须冻结被解析的那份正文"
    assert stored.protocol_body.text == expected
    assert stored.protocol_body.digest == Digest.of_bytes(expected.encode("utf-8"))

    detail = run_ready_client.get(f"/runs/{stored.id.value}").json()
    assert detail["protocol_body_digest"] == str(stored.protocol_body.digest)


def test_a_run_is_rebuilt_from_its_frozen_body_after_the_source_file_is_gone(
    client: TestClient,
) -> None:
    """来源文件消失 ⇒ 重建入口仍走得通（AC-02，cycle 1 的核心判据）。

    判据落在"重建**装配**成功"上：`continuation == "REBUILT"` 意味着装配链从冻结正文
    重新解析、编译、预检、过语义校验并交付了续跑——退一步（没有冻结正文）就是
    `NONE` + "protocol file not found"（见本文件另一条用例）。已跑完的 run 重新续跑
    会落到"没有剩余工作"的分支（发现见 RECHECK-084 W-2），不在本用例的判据内。
    """
    with _temp_protocol(_DEMO_PROTOCOL) as (name, path):
        started = _start_demo_run(client, name)
        assert started.state == "SUCCEEDED"
        assert started.protocol_body is not None
        parked = _park(started, protocol_source=ProtocolSource(protocol_path=name))
    assert not path.exists(), "临时模板已删除：重建不得再依赖这份文件"

    run_id = _save_parked(client, parked)
    deps = _deps(client)
    assert deps.runs is not None and deps.runs.has_paused_context(run_id) is False, (
        "本进程没有暂停上下文 ⇒ 只能走重建入口"
    )

    payload = _post(client, f"/runs/{run_id}/resume").json()

    assert payload["continuation"] == "REBUILT", payload
    assert "rebuilt from the recorded protocol source" in payload["note"]


def test_a_swapped_frozen_body_is_refused(client: TestClient) -> None:
    """换一份自洽但不同的正文 ⇒ 语义漂移，重建被拒（AC-03a：冻结 ≠ 放行）。"""
    with _temp_protocol(_DEMO_PROTOCOL) as (name, _path):
        started = _start_demo_run(client, name)
        assert started.protocol_body is not None
        swapped_text = started.protocol_body.text.replace("version: 0.4.0", "version: 0.4.1")
        assert swapped_text != started.protocol_body.text, "替身正文必须真的不同"
        parked = _park(
            started,
            protocol_source=ProtocolSource(protocol_path=name),
            protocol_body=ProtocolBody.of(swapped_text),
        )

    deps = _deps(client)
    run_id = _save_parked(client, parked)
    before = len(deps.workflow.task_identities(run_id))

    payload = _post(client, f"/runs/{run_id}/resume").json()

    assert payload["continuation"] == "NONE", payload
    assert "rebuild refused" in payload["note"]
    assert "drifted" in payload["note"], "拒绝原因点名语义漂移"
    assert payload["manifest_digest"] == str(started.manifest_digest), "拒绝不得重盖冻结引用"
    assert len(deps.workflow.task_identities(run_id)) == before, "拒绝时一次都不执行"


def test_a_run_without_a_frozen_body_names_both_missing_facts(
    run_ready_client: TestClient,
) -> None:
    """旧 run（无冻结正文）+ 来源不可解析 ⇒ 拒绝原因同时点名两条事实（AC-03b）。"""
    client = run_ready_client
    legacy = _park(
        ResearchRun(
            id=ID.generate(),
            project_id="example-project",
            protocol_id="test_protocol",
            state=ResearchRunState.State.PAUSED,
        ),
        manifest_digest=Digest.parse("sha256:" + "0" * 64),
        manifest_semantic_digest=None,
        protocol_source=ProtocolSource(protocol_path="examples/protocols/does-not-exist.yaml"),
        protocol_body=None,
    )
    run_id = _save_parked(client, legacy)

    payload = _post(client, f"/runs/{run_id}/resume").json()

    assert payload["continuation"] == "NONE"
    assert "no frozen protocol body" in payload["note"], "点名缺的第一条事实"
    assert "protocol file not found" in payload["note"], "点名缺的第二条事实（来源不可解析）"
