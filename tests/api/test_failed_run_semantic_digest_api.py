"""失败 run 与冻结事件的语义 digest（GOAL-004 cycle 4 = EC-04）。

判据（四项，全部从 HTTP 面成立）：

1. **同判据**：执行期失败收敛的 `FAILED` run 行与成功路径用同一个断言成立——
   `manifest_semantic_digest` 非空、`sha256:` 前缀、且 `!= manifest_digest`（语义 digest
   排除冻结时刻）；
2. **事件相等**：`manifest.frozen` payload 的 `semantic_digest` 等于 run 行的值；
3. **重放一致**：只凭事件链（`FrozenManifestRefs.from_payload`）重建出的四项冻结引用与
   canonical 行完全相同；
4. **真的被消费**：同一个漂移守卫（`assert_semantics_frozen`）用它放行、也用它拒绝——
   换一个语义 digest ⇒ 重建被拒并点名 `drifted`。

诚实边界：preflight 被拒的 run 从未冻结 ⇒ 语义 digest 保持 None（不伪造引用）。
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi.testclient import TestClient

from packages.domain.core import ID, Digest
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from services.api.run_execution import FrozenManifestRefs

_FAILING_PROTOCOL = "m12_reference_research_v1.yaml"
_SUCCESS_PROTOCOL = "console_demo_research_v1.yaml"
_NEVER_FROZEN_PROTOCOL = "sort_analysis_v1.yaml"
#: 冻结之后**优雅**收敛 FAILED 的协议（失败来自任务结果登记，不是执行期抛 ValueError）。
_GRACEFUL_FAILURE_PROTOCOL = "real_retrieval_research_v1.yaml"


def _deps(client: TestClient) -> Any:
    return cast(Any, client.app).state.deps


def _canonical(client: TestClient, run_id: str) -> ResearchRun:
    """canonical 读面：有 run store 走 store，基础装配（无 store）走注册表。"""
    deps = _deps(client)
    if deps.runs_store is not None:
        return cast(ResearchRun, deps.runs_store.get_run(run_id))
    return cast(ResearchRun, deps.run_registry[run_id])


def _start(client: TestClient, protocol_path: str) -> ResearchRun:
    response = client.post(
        "/projects/example-project/runs",
        json={"protocol_path": protocol_path},
        headers={"Idempotency-Key": f"digest-{uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    return _canonical(client, response.json()["id"])


def _assert_frozen_semantic_digest(row: ResearchRun) -> None:
    """成功路径与失败收敛路径**共用**的判据（同判据 = 同一个断言函数）。"""
    assert row.manifest_digest is not None, "冻结过 manifest 的 run 必须带快照 digest"
    assert row.manifest_semantic_digest is not None, "冻结过的 run 必须带语义 digest"
    assert str(row.manifest_semantic_digest).startswith("sha256:")
    assert row.manifest_semantic_digest != row.manifest_digest, "语义 digest 排除冻结时刻"


def _frozen_payload(client: TestClient, run_id: str) -> dict[str, Any]:
    events = client.get(f"/runs/{run_id}/events").json()
    frozen = [item for item in events if item["type"] == "manifest.frozen"]
    assert len(frozen) == 1, "一次冻结只发一条事件"
    return cast(dict[str, Any], frozen[0]["payload"])


def test_a_failed_run_carries_the_frozen_semantic_digest(run_ready_client: TestClient) -> None:
    """收敛 `FAILED` 的 run 行带语义 digest，且读面如实暴露（EC-04 核心判据）。

    这条 run 在执行期失败（冻结已经发生）——旧行为只补回快照 digest 与定价引用，
    语义 digest 缺失 ⇒ `assert_semantics_frozen` 直接拒绝重建。
    """
    row = _start(run_ready_client, _FAILING_PROTOCOL)
    assert row.state == "FAILED", "本夹具里该协议冻结成功、执行期收敛 FAILED"

    _assert_frozen_semantic_digest(row)

    detail = run_ready_client.get(f"/runs/{row.id.value}").json()
    assert detail["manifest_semantic_digest"] == str(row.manifest_semantic_digest)


def test_the_success_path_meets_the_same_criterion(client: TestClient) -> None:
    """成功路径用**同一个判据函数**（同一条断言在两个装配夹具上成立）。

    失败收敛那一条走 `run_ready_client`（preflight 通过 ⇒ 真的冻结过），成功路径走基础
    夹具（受控模板全链成功）——两处调用的判据是同一个 `_assert_frozen_semantic_digest`。
    """
    _deps(client).credentials.register("LLM_MAIN_KEY", "sk-demo-key-0001")
    first = _start(client, _SUCCESS_PROTOCOL)
    second = _start(client, _SUCCESS_PROTOCOL)

    assert first.state == "SUCCEEDED" and second.state == "SUCCEEDED"
    _assert_frozen_semantic_digest(first)
    _assert_frozen_semantic_digest(second)
    # 语义 digest 覆盖 run_id ⇒ 同协议的两条 run 不可能共用一份冻结语义（不是常量）。
    assert first.manifest_semantic_digest != second.manifest_semantic_digest


def test_the_frozen_event_carries_the_same_semantic_digest(run_ready_client: TestClient) -> None:
    """事件用例：`manifest.frozen` payload 的语义 digest 与 run 行相等。"""
    row = _start(run_ready_client, _FAILING_PROTOCOL)

    payload = _frozen_payload(run_ready_client, row.id.value)

    assert payload["digest"] == str(row.manifest_digest)
    assert payload["semantic_digest"] == str(row.manifest_semantic_digest)


def test_the_run_row_is_replayable_from_the_event_chain(run_ready_client: TestClient) -> None:
    """重放一致性：只凭事件链重建 run 行的冻结引用 ⇒ 与 canonical 行相同。

    重建走的是产品代码里同一个映射（`FrozenManifestRefs.from_payload` +
    `ResearchRun.with_manifest`），不是用例自己拼字段——否则"可重放"只是测试的声明。
    """
    row = _start(run_ready_client, _FAILING_PROTOCOL)
    payload = _frozen_payload(run_ready_client, row.id.value)

    rebuilt = FrozenManifestRefs.from_payload(payload).apply(
        ResearchRun(
            id=row.id,
            project_id=row.project_id,
            protocol_id=row.protocol_id,
            state=ResearchRunState.State.FAILED,
        )
    )

    assert rebuilt.manifest_digest == row.manifest_digest
    assert rebuilt.manifest_semantic_digest is not None, "重放出来的语义 digest 不能是空值"
    assert rebuilt.manifest_semantic_digest == row.manifest_semantic_digest
    assert rebuilt.pricing_version == row.pricing_version
    assert rebuilt.pricing_digest == row.pricing_digest


def test_a_failed_run_without_a_freeze_event_has_no_semantic_digest(
    run_ready_deps: Any,
) -> None:
    """诚实边界：preflight 被拒 ⇒ 从未冻结 ⇒ 语义 digest 保持 None（不伪造引用）。

    GOAL-012 EC-01：`sort_analysis_v1` 在**策略显式允许**下今天会冻结（见
    `tests/api/test_runs_api.py::test_start_run_warn_preflight_freezes_on_the_explicit_policy_allowance`）。
    本用例把该允许**撤掉**（`code.execute` 判 `DENY`）⇒ 回到「预检拒 ⇒ 永不冻结」的形态，
    这条边界语义因此被**更精确**地钉住（而不是删掉它）。
    """
    from dataclasses import replace

    from adapters.fakes.policy_evaluator import FakePolicyEvaluator
    from packages.domain.enums import PolicyDecision
    from services.api.app import create_app

    evaluator = FakePolicyEvaluator()
    evaluator.set_decision("code.execute", PolicyDecision.DENY)
    override = run_ready_deps.preflight_override
    assert override is not None, "run-ready 装配必须注入 preflight override"
    run_ready_deps.preflight_override = replace(override, policy_evaluator=evaluator)
    with TestClient(create_app(run_ready_deps)) as client:
        row = _start(client, _NEVER_FROZEN_PROTOCOL)

    assert row.state == "FAILED"
    assert row.manifest_digest is None
    assert row.manifest_semantic_digest is None


def test_a_graceful_failure_still_carries_the_frozen_refs(run_ready_client: TestClient) -> None:
    """与上一条成对：失败**优雅**收敛（任务结果登记失败、不抛 ValueError）时同样保住冻结引用。

    两条失败收敛路径对 canonical 行必须给同一个答案：冻结过就是冻结过。缺字节 digest ⇒
    读面把这条 run 判成「从未冻结」（rebuild REFUSED, missing=[manifest_digest]），
    `assert_semantics_frozen` 也跟着拒绝重建——那是记录不全，不是没冻结（GOAL-011 cycle 10）。
    """
    row = _start(run_ready_client, _GRACEFUL_FAILURE_PROTOCOL)

    assert row.state == "FAILED", "本夹具里该协议冻结成功、随后在执行期收敛 FAILED"
    _assert_frozen_semantic_digest(row)

    rebuild = run_ready_client.get(f"/runs/{row.id.value}").json()["rebuild"]
    assert rebuild["status"] == "SELF_CONTAINED", rebuild
    assert rebuild["missing"] == [], rebuild


def test_a_legacy_freeze_event_without_a_semantic_digest_stays_empty() -> None:
    """旧事件形态（payload 只有 `digest`）⇒ 回填路径落到 None，**不伪造**语义 digest。

    GOAL-005 cycle 6 = EC-06：这条 from-event 回填分支此前没有用例（既有 restart 用例
    的 run 行自带语义 digest，走不到这里）。判据是结构性的：`from_payload` 对缺失键
    一律"当作没有这一项"，`apply` 只落它真的读到的引用。
    """
    legacy_payload = {"digest": "sha256:" + "0" * 64, "run_id": str(uuid.uuid4())}

    refs = FrozenManifestRefs.from_payload(legacy_payload)
    applied = refs.apply(
        ResearchRun(
            id=ID(legacy_payload["run_id"]),
            project_id="example-project",
            protocol_id="test_protocol",
            state=ResearchRunState.State.PAUSED,
        )
    )

    assert refs.semantic_digest is None, "旧事件没有这项 ⇒ 不猜"
    assert applied.manifest_digest is not None, "字节 digest 该落就落"
    assert applied.manifest_semantic_digest is None, "不伪造语义 digest"


def test_a_legacy_freeze_event_leaves_the_row_naming_the_missing_fact(
    run_ready_client: TestClient,
) -> None:
    """同一行的读面必须**点名**缺的事实（历史行不再是含糊的 None）：EC-06 (b) 的判据。

    这条把"事件形态的历史行"一路走到 HTTP 读面：run 行只有字节 digest → 读面
    `rebuild.status=REFUSED` 且 `missing` 点名 `manifest_semantic_digest`。
    """
    client = run_ready_client
    legacy_payload = {"digest": "sha256:" + "0" * 64, "run_id": str(ID.generate().value)}
    run_id = str(legacy_payload["run_id"])
    parked = FrozenManifestRefs.from_payload(legacy_payload).apply(
        ResearchRun(
            id=ID(run_id),
            project_id="example-project",
            protocol_id="test_protocol",
            state=ResearchRunState.State.PAUSED,
        )
    )
    deps = _deps(client)
    deps.run_registry[run_id] = parked
    deps.runs_store.save_run(parked)

    rebuild = client.get(f"/runs/{run_id}").json()["rebuild"]

    assert rebuild["status"] == "REFUSED", rebuild
    assert rebuild["missing"][0] == "manifest_semantic_digest", "点名缺的第一条事实"
    assert "protocol_body" in rebuild["missing"], "旧行同样没有冻结正文（第二条事实）"


def _park(row: ResearchRun, **overrides: object) -> ResearchRun:
    """以既有 run 的冻结事实构造"同一条 run 的停车态"。

    定价引用必须一并复制：语义 digest 覆盖它们，缺一个字段就会被漂移守卫判成漂移
    （那是守卫在起作用，不是可以绕开的噪声）。
    """
    base: dict[str, object] = {
        "id": row.id,
        "project_id": row.project_id,
        "protocol_id": row.protocol_id,
        "state": ResearchRunState.State.PAUSED,
        "manifest_digest": row.manifest_digest,
        "manifest_semantic_digest": row.manifest_semantic_digest,
        "pricing_version": row.pricing_version,
        "pricing_digest": row.pricing_digest,
        "protocol_source": row.protocol_source,
        "protocol_body": row.protocol_body,
    }
    base.update(overrides)
    return ResearchRun(**base)  # type: ignore[arg-type]


def _save_parked(client: TestClient, parked: ResearchRun) -> str:
    deps = _deps(client)
    deps.run_registry[parked.id.value] = parked
    deps.runs_store.save_run(parked)
    return parked.id.value


def _resume(client: TestClient, run_id: str) -> dict[str, Any]:
    response = client.post(
        f"/runs/{run_id}/resume",
        headers={"Idempotency-Key": f"resume-{uuid.uuid4()}"},
    )
    assert response.status_code == 200, response.text
    return cast(dict[str, Any], response.json())


def test_the_converged_digest_is_what_the_drift_guard_consumes(
    run_ready_client: TestClient,
) -> None:
    """语义 digest 不是装饰：带着它，失败 run 的重建不再被"没有语义 digest"挡住。

    判据只落在**冻结语义守卫**上（不点名断言后续执行结果）：这条 run 的协议在执行期
    会再次失败，那是另一条缺口（RECHECK-082 W-3 / EC-06），不在本用例判据内。
    """
    row = _start(run_ready_client, _FAILING_PROTOCOL)
    deps = _deps(run_ready_client)
    assert deps.runs is not None and deps.runs.has_paused_context(row.id.value) is False, (
        "本进程没有暂停上下文 ⇒ 只能走重建入口"
    )
    run_id = _save_parked(run_ready_client, _park(row))

    payload = _resume(run_ready_client, run_id)

    note = str(payload["note"])
    assert "lacks a semantic digest" not in note, "守卫不再因缺少语义 digest 拒绝"
    assert "drifted" not in note, "引用没换过，不该判成漂移"
    assert "task contract" in note, "重建已经走到执行（该协议的执行期失败，见 EC-06）"


def test_a_wrong_semantic_digest_is_refused_as_drift(run_ready_client: TestClient) -> None:
    """反方向：换一个语义 digest ⇒ 同一个守卫判漂移并拒绝（不是"塞了值就放行"）。"""
    row = _start(run_ready_client, _FAILING_PROTOCOL)
    parked = _park(row, manifest_semantic_digest=Digest.parse("sha256:" + "0" * 64))
    run_id = _save_parked(run_ready_client, parked)

    payload = _resume(run_ready_client, run_id)

    assert payload["continuation"] == "NONE", payload
    assert "rebuild refused" in str(payload["note"])
    assert "drifted" in str(payload["note"]), "拒绝原因点名语义漂移"
