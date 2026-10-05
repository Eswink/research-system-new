"""GOAL-20261005-030 EC-01 判据：**承接能力真的被一次 run 用上**。

**它补的是什么**：GOAL-029 把承接面扩到 17/46 并让「出厂即可跑」机械化，但**承接面 ≠
被使用** —— 建档勘察逐条分类（`examples/protocols/**` 的能力名去重）实测：GOAL-029 承接的
五条读能力**使用面 = 0**（零协议声明），而已放行的三条读能力**只在会话面上「可能被模型
调用」**、**从无「产出被下游消费」的证据**。本文件把这条落差收成机械事实。

**被测对象**：`examples/protocols/capabilities_used_in_a_run_v1.yaml`（本轮新增）经
`compile → preflight → freeze → execute_phases` 跑完 —— 两个 phase 都由**运行链**执行
三条已放行的承接读能力（`artifact.read` / `evidence.read` / `workspace.read`），且
**下游 phase 消费上游产出**。

**五件事逐条取证**（全部读**既有读面**，不经内部对象）：

1. **真被调用**（(a)+(b) 前半）：三条能力各有一条工具证据，`tool_refs` 逐条点名
   `("m12_artifact", <tool_id>)` —— 三条**都在场**（缺一即判红并点名缺哪条）。
2. **产出可复核**（(b) 中段）：工具证据的 `artifact_id` 是 `tool-result:` 命名的
   内容寻址制品，在 `GET /runs/{id}/artifacts` 读面上**取得到**且 digest 在场。
3. **下游消费**（(b) 后半）——**本判据的核心**：`review` phase 的 `evidence_read`
   **返回内容里含有 `probe` phase 工具证据的 id**。判据读的是 review 那次调用的
   **工具结果内容本身**（`tool-result:` 制品，JSON 解出 `evidence[].id`），断言
   probe 的证据 id 逐字出现在其中 ⇒ 「调了但没人用」在构造上不成立。
   **为什么不是「两个 phase 都调了同一个工具」**：那只证明「调了两遍」；下游**读到**
   上游的产物才是消费。两者的差别正是本 EC 要钉的。
4. **反证点名**（(c)）：删掉一种 provider 的注册实例 ⇒ run **失败**且失败消息**点名**
   缺的 provider / 能力 / 工具（承「点名失败而非静默」）；复原 ⇒ 绿。
5. **实跑终态**（(d)）：跑到 `SUCCEEDED`，且 `manifest_digest` 在场（冻结真的发生）。

**如实边界**（本文件不声称已解决）：

- 三条读的是**本次 run 自己的 canonical 状态**（声明输入制品 / 证据投影 / 工作区视图），
  **不是外部检索** —— 本判据**不**声称该协议做过文献检索，也**不**声称读结果影响了
  交付物的科学结论（验收门只判产物存在与来源覆盖，不判内容质量）。
- **只用已放行的三条**：另五条（`claim.read` / `budget.read` / `deliverable.read` /
  `experiment.read` / `experiment_plan.read`）在 `policy.yaml` 无 `allow` ⇒ 写进
  `required_capabilities` 会打红既有差集判据（属 `D-02(b)` 待拍板）。受限面逐条登记在
  GOAL 记录里，**不以「已承接」冒充「已跑通」**。
- 装配用 run-ready 夹具（`preflight_override` + 装配方声明的运行链步），与 GOAL-011/
  027/029 全部离线判据同一条路径；它证的是**链路与判据**。
"""

from __future__ import annotations

import json
from typing import Any

from fastapi.testclient import TestClient

from adapters.canonical import CanonicalReadProvider
from packages.application.run_orchestration.phase_capabilities import (
    CapabilityDeps,
    RunChainCall,
)
from tests.e2e.live_run_support import (
    openhands_deps as _openhands_deps,
)
from tests.e2e.live_run_support import (
    run_chain_store_ledger as _store_ledger,
)
from tests.e2e.live_run_support import (
    start_run as _start,
)

# 读面快照与 mock 端点与既有离线 e2e 同源（同一套装配，避免两处各写一份）。
from tests.e2e.test_ec03_real_runtime_offline_chain import _read_chain, mock_relay

__all__ = ["mock_relay"]

_PROTOCOL = "capabilities_used_in_a_run_v1.yaml"
#: 本协议声明的三条承接读能力（逐字写死在判据里，不 import 产品常量当预言机）。
_CAPABILITIES = ("artifact.read", "evidence.read", "workspace.read")
#: 能力 → provider 侧 tool id（`adapters/canonical/read_surface.py` 的 `_TOOL_CAPABILITIES`）。
_TOOL_IDS = {
    "artifact.read": "artifact_read",
    "evidence.read": "evidence_read",
    "workspace.read": "workspace_read",
}
_PROVIDER = "m12_artifact"
#: 声明输入（协议 `inputs:` 声明的那份操作者简报；组合根按此 id 种入）。
_BRIEF = "input-brief:real_research_v1"
#: 两个 phase 的 id（判据按它们区分「上游」与「下游」）。
_PROBE_PHASE = "probe"
_REVIEW_PHASE = "review"


def _provider(deps: Any) -> tuple[CanonicalReadProvider, Any, Any]:
    """本轮装配的 canonical 读面 provider（**真实现**，不是替身）。

    `spill_threshold_bytes=1` 是**消费者要求**（与运行链同一条：证据准入会重算 digest，
    而默认 32 KiB 阈值会让小读结果不落盘 ⇒ 准入 fail closed、链拿不到内容）。
    """
    store, ledger = _store_ledger(deps)
    return CanonicalReadProvider(store, ledger, spill_threshold_bytes=1), store, ledger


def _calls(*, omit: str | None = None) -> tuple[RunChainCall, ...]:
    """本协议的运行链调用声明（**逐条对应三条能力**）。

    `artifact_read` 读**声明输入**（内容非空 ⇒ 有真东西可读，不是读空壳）；
    `workspace_read` 与 `evidence_read` 读**本次 run 自己的视图** —— 它们的 `run_id`
    只在执行期存在，因此用 `run_id_argument=True` 由运行时注入（本轮新增的取值来源；
    `RunChainCall` 的既有三类取值都不覆盖「执行期才存在的标识」）。

    `omit` 供**反证臂**用：把某条能力从声明里摘掉（`None` ⇒ 三条全给）。
    """
    calls = [
        RunChainCall(
            provider_id=_PROVIDER,
            tool_id=_TOOL_IDS["artifact.read"],
            capability="artifact.read",
            fixed_arguments={"artifact_id": _BRIEF},
        ),
        RunChainCall(
            provider_id=_PROVIDER,
            tool_id=_TOOL_IDS["evidence.read"],
            capability="evidence.read",
            run_id_argument=True,
        ),
        RunChainCall(
            provider_id=_PROVIDER,
            tool_id=_TOOL_IDS["workspace.read"],
            capability="workspace.read",
            run_id_argument=True,
        ),
    ]
    if omit is None:
        return tuple(calls)
    return tuple(call for call in calls if call.capability != omit)


def _assembled_deps(mock_relay_url: str, *, omit_provider: bool = False) -> Any:
    """run-ready 装配 + 装配方声明的运行链能力步（**同一批产品对象**）。

    `omit_provider=True` 是**反证面**：声明照旧（`calls` 三条都在），但装配里**不给**
    provider 实例 ⇒ 运行链步必须**点名失败**（不是静默跳过那条能力）。
    """
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.assembly import policy_bindings

    deps = _openhands_deps(mock_relay_url, map_tools=False)
    provider, store, ledger = _provider(deps)
    context = deps.preflight_override
    assert context is not None
    spec = context.catalog.tool_providers[_PROVIDER]
    policy = policy_bindings().get("policy_evaluator")
    assert policy is not None, "policy.yaml must be loadable for the run-chain policy check"
    capabilities = CapabilityDeps(
        calls=_calls(),
        providers={} if omit_provider else {spec.id: provider},
        provider_specs={spec.id: spec},
        policy=policy,
        artifacts=store,
        ledger=ledger,
    )
    old = deps.runs
    assert old is not None
    deps.runs = RunOrchestrationService(
        replace(old._deps, runtime=old._deps.runtime, capabilities=capabilities)
    )
    return deps


def _phase_of_task(reads: Any) -> dict[str, str]:
    """`task_id` → phase id（由**该任务的交付物制品名**判）。

    两个 phase 各在自己的交付物名里有独一无二的标识（`probe_report` / `review_decision`，
    合约声明的那一个），因此「哪个 task 属哪个 phase」在读面上可判，不靠调用顺序猜。
    """
    mapping: dict[str, str] = {}
    for artifact_id in _artifact_ids(reads):
        head, _, tail = artifact_id.rpartition(":")
        if tail == "probe_report":
            mapping[head] = _PROBE_PHASE
        elif tail == "review_decision":
            mapping[head] = _REVIEW_PHASE
    return mapping


def _tool_evidence(reads: Any, *, phase: str | None = None) -> dict[str, dict[str, Any]]:
    """`tool_refs` 非空的证据，按 provider 侧 tool id 建索引（读面口径，非内部对象）。

    `phase` 非空时只取该 phase 任务的证据（判定见 `_phase_of_task`）。

    **为什么必须能按 phase 分**（本判据初版的一个真实缺陷，实测抓到）：两个 phase 调
    **同名工具** ⇒ 单键索引会**后写覆盖前写**，于是「上游产出」与「下游产出」在看的人
    眼里变成同一条 —— 「下游是否消费了上游」就被这个覆盖**掩蔽**掉了（承
    `MEM-20260922-160`：不得靠交集/并集掩蔽）。分 phase 索引是这条判据能成立的前提。
    """
    by_task = _phase_of_task(reads)
    by_tool: dict[str, dict[str, Any]] = {}
    for item in reads.evidence:
        refs = item.get("tool_refs") or []
        if len(refs) != 2 or refs[0] != _PROVIDER:
            continue
        task_id = _task_of_evidence(item)
        if phase is not None and by_task.get(task_id) != phase:
            continue
        by_tool[str(refs[1])] = item
    return by_tool


def _task_of_evidence(item: dict[str, Any]) -> str:
    """证据所属任务的标识（工具证据的 `artifact_id` 带 `tool-result:{task_id}:…`）。"""
    parts = str(item.get("artifact_id") or "").split(":")
    return parts[1] if len(parts) > 2 else ""


def _content_of(client: TestClient, artifact_id: str) -> dict[str, Any]:
    """按 artifact id 取**内容**并解析成 JSON 对象（经既有读面，不经内部对象）。

    列表路由（`GET /runs/{id}/artifacts`）只回元数据（`content` 恒为 None：列表视图
    **不伪装已验证**），内容在 `GET /artifacts/{id}/content`。判据要读「下游那次调用
    **返回了什么**」—— 那正是落在这个制品里的字节。
    """
    response = client.get(f"/artifacts/{artifact_id}/content")
    assert response.status_code == 200, (artifact_id, response.status_code, response.text[:200])
    parsed = json.loads(response.content.decode("utf-8"))
    assert isinstance(parsed, dict), ("工具结果内容必须是 JSON 对象", artifact_id, type(parsed))
    return parsed


def _artifact_ids(reads: Any) -> list[str]:
    """该 run 读面上的全部制品 id（列表视图口径）。"""
    payload = reads.artifacts
    entries = payload["artifacts"] if isinstance(payload, dict) else payload
    return [str(item.get("id") or "") for item in entries]


class TestThreeCapabilitiesAreReallyCalled:
    """① 三条承接读能力**都真的被调用**（调用证据逐条在场）。"""

    def test_each_declared_capability_leaves_a_call_evidence(self, mock_relay: str) -> None:
        """**主判据**：三条能力各留下一条工具证据，`tool_refs` 逐条点名。

        受判面 = **三条逐条**（不是「至少一条」）：缺哪条就点名哪条（承 MEM-160：
        不得用交集/并集把缺项掩掉）。
        """
        deps = _assembled_deps(mock_relay)
        with TestClient(_app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))

        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        by_tool = _tool_evidence(reads)
        missing = [
            capability for capability in _CAPABILITIES if _TOOL_IDS[capability] not in by_tool
        ]
        assert missing == [], (
            "声明使用的承接能力必须有调用证据（缺哪条点名哪条）",
            missing,
            sorted(by_tool),
        )
        # **逐 phase**再断言一次：两个 phase 各调一遍三条工具 ⇒ 每个 phase 名下三条都在。
        # 这条让「只有一个 phase 真的调过」不可能冒充「两个 phase 都调过」。
        for phase in (_PROBE_PHASE, _REVIEW_PHASE):
            scoped = _tool_evidence(reads, phase=phase)
            assert sorted(scoped) == sorted(_TOOL_IDS.values()), (phase, sorted(scoped))

    def test_the_run_真的冻结过(self, mock_relay: str) -> None:
        """实跑终态的前置：冻结真的发生（否则「跑通」可能只是没执行）。"""
        deps = _assembled_deps(mock_relay)
        with TestClient(_app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))

        assert reads.run["manifest_digest"], reads.run
        assert "manifest.frozen" in reads.types, sorted(reads.types)


class TestTheOutputIsReviewableDowntheReadFace:
    """② 上游产出**可复核**：工具结果落在内容寻址制品上，读面取得到。"""

    def test_each_result_is_a_content_addressed_artifact(self, mock_relay: str) -> None:
        """三条工具证据各指向一个 `tool-result:` 制品（内容寻址三件套齐备）。"""
        deps = _assembled_deps(mock_relay)
        with TestClient(_app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))

        # 两个 phase 各查一遍：每个 phase 的三条工具结果都必须是内容寻址制品。
        for phase in (_PROBE_PHASE, _REVIEW_PHASE):
            by_tool = _tool_evidence(reads, phase=phase)
            assert by_tool, phase
            for capability in _CAPABILITIES:
                item = by_tool[_TOOL_IDS[capability]]
                assert str(item["artifact_id"]).startswith("tool-result:"), (capability, item)
                assert item["content_digest"], (capability, item)
                assert item["source_origin"].startswith(f"tool:{_TOOL_IDS[capability]}:"), (
                    capability,
                    item,
                )


class TestTheDownstreamPhaseConsumesIt:
    """③ **下游消费**：review 的 `evidence.read` 返回内容里含有 probe 的工具证据 id。

    这是本 EC 的核心断言 —— 它与「两个 phase 都调了同一个工具」**不是同一件事**：
    后者只证明调了两遍，本类证明**下游真的读到了上游留下的东西**。
    """

    def test_the_evidence_read_result_carries_the_upstream_evidence_ids(
        self, mock_relay: str
    ) -> None:
        deps = _assembled_deps(mock_relay)
        with TestClient(_app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))

            # 上游 = `probe` phase 的三条工具证据；下游 = `review` phase 那次
            # `evidence_read` 的**返回内容**（逐个读制品的字节，读面口径）。
            upstream_evidence = _tool_evidence(reads, phase=_PROBE_PHASE)
            upstream = sorted(
                str(upstream_evidence[_TOOL_IDS[capability]]["id"]) for capability in _CAPABILITIES
            )
            assert upstream, "上游必须留下证据（否则本判据在空集上恒真）"

            downstream = _tool_evidence(reads, phase=_REVIEW_PHASE)[_TOOL_IDS["evidence.read"]]
            payload = _content_of(client, str(downstream["artifact_id"]))

        consumed = {str(item.get("id")) for item in payload.get("evidence", [])}
        assert consumed, (
            "下游 `evidence.read` 的返回内容必须非空（否则「消费」无从谈起）",
            payload,
        )
        missing = sorted(set(upstream) - consumed)
        assert missing == [], (
            "下游 `evidence.read` 的返回内容必须含上游工具证据的 id（否则『调了但没人用』）",
            missing,
            sorted(consumed),
        )


class TestAMissingImplementationIsNamed:
    """④ 反证：缺实现 ⇒ run 失败并**点名**（不得静默继续）。"""

    def test_removing_the_provider_instance_fails_and_names_it(self, mock_relay: str) -> None:
        deps = _assembled_deps(mock_relay, omit_provider=True)
        with TestClient(_app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))

        assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
        assert reads.failures, "失败必须带判词（点名缺的是什么）"
        joined = " ".join(reads.failures)
        assert _PROVIDER in joined, (
            "缺实现必须**点名 provider**（不静默跳过那条能力）",
            reads.failures,
        )
        assert "has no registered instance" in joined, (
            "判词必须说明是「装配里没有实例」（而不是把失败归到别处）",
            reads.failures,
        )
        # 点名的粒度到**能力与工具**：缺哪条能力可读。
        assert any(capability in joined for capability in _CAPABILITIES), (
            "判词必须点名具体能力/工具（否则无法判断缺的是哪一条）",
            reads.failures,
        )
        assert [item for item in reads.evidence if item.get("tool_refs")] == [], reads.evidence


class TestTheJudgeItselfBites:
    """⑤ 判据自检：受判面非空 + 本判据真的咬得住（承 MEM-156 / MEM-159）。"""

    def test_the_declared_call_set_covers_the_three_capabilities(self) -> None:
        """受判面的**前提**：判据写死的三条能力与装配声明**逐字一致**（否则在空集上恒真）。"""
        calls = _calls()
        assert [call.capability for call in calls] == list(_CAPABILITIES), calls
        assert {call.tool_id for call in calls} == set(_TOOL_IDS.values()), calls

    def test_omitting_one_capability_is_detectable(self) -> None:
        """反证两向之一：少一条能力的声明 ⇒ 本判据的「逐条在场」断言能抓到它。"""
        by_tool = {_TOOL_IDS["artifact.read"]: {}, _TOOL_IDS["evidence.read"]: {}}
        missing = [
            capability for capability in _CAPABILITIES if _TOOL_IDS[capability] not in by_tool
        ]
        assert missing == ["workspace.read"], missing

    def test_the_protocol_declares_a_run_chain_phase_and_the_three_capabilities(self) -> None:
        """受判面非空：**协议文档本身**必须声明那三条能力 + `run_chain`（不靠产品代码转述）。

        这条挡住「协议被悄悄改回会话语义」——那时本文件的主体断言会因为
        「会话没被模型驱动」而失败，但原因是**声明面变了**，本条把它点出来。
        """
        from pathlib import Path

        import yaml

        raw = yaml.safe_load(Path(f"examples/protocols/{_PROTOCOL}").read_text(encoding="utf-8"))
        phases = {phase["id"]: phase for phase in raw["phases"]}
        assert set(phases) == {_PROBE_PHASE, _REVIEW_PHASE}, sorted(phases)
        for phase_id in (_PROBE_PHASE, _REVIEW_PHASE):
            assert phases[phase_id].get("capability_execution") == "run_chain", phases[phase_id]
            assert set(phases[phase_id]["required_capabilities"]) == set(_CAPABILITIES), (
                phase_id,
                phases[phase_id]["required_capabilities"],
            )


def _app(deps: Any) -> Any:
    from services.api.app import create_app

    return create_app(deps)
