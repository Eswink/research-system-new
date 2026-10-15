"""GOAL-20261014-078 EC-02 判据：**检索内容经产品路径到达下游会话**。

**它补哪一格**：GOAL-078 EC-01 证了「接缝在树 + 两个组合根接线」；但「接线了」不等于
「经产品路径的实跑里，下游会话**真的拿到了**上游取回的内容」。本文件把后者变成事实。

**取证面 = 会话 spec，不是内部对象**：`AgentSessionSpec.context_snapshot` 就是
「这次会话拿到的上下文」本身。判据读它（经一个**记录型 runtime**包装 —— 与
`OutcomeRecorder` 同一手法：装配方包装、**不改产品代码**、原样透传），
按 **`task_contract.id`**（声明事实）索引自己关心的那两个会话，**不按顺序猜 phase**。

**两向写在同一次实跑上**（用**既有**协议 `research_report_chain_v1`，不新造协议）：

| phase | 执行体 | 期望 |
| --- | --- | --- |
| `plan` | 运行链检索 + 会话 | 会话开始时检索**还没跑** ⇒ `selected_refs` **空且点名**（反证臂） |
| `experiment` | 沙箱（不建会话） | — |
| `review` | 会话（**下游**） | 应看到 plan 格取回的内容 ⇒ `selected_refs` **非空**（正向臂） |

⇒ 「非空」与「空且点名」是**同一条链上的两个相反读数**，任一条被改成迁就实现，
另一条立刻失去意义。

**逐条对应（不是「非空」了事）**：`selected_refs` 里的每个 `tool-result:` 制品 id
必须能在 `GET /runs/{id}/evidence` 里找到，且那条证据的 `source_trust_label`
**恰为** `RETRIEVED` —— 于是「这是检索内容」不是自称，而是与读面同源的**性质事实**。

**如实边界**（本文件不声称已解决）：

- 用 run-ready 夹具（`preflight_override` + 装配方接的执行体缝）⇒ 它证的是**链路与装配**，
  与 GOAL-011/027/029/077 的离线判据同一条路径；真容器那段挂 `requires_docker`；
- **不判模型行为**：判的是「内容进了会话规格」这一事实，**不**判模型读了它
  （那需要观测面，属阶梯的再下一级）；
- **不判内容质量**：进上下文的是**有界摘录**（§10），判据只判「进了哪些、从哪来、
  是否系统取得」。
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from adapters.openhands.session_tools import build_session_tools
from packages.application.ports.agent_runtime import AgentSessionHandle, AgentSessionSpec
from services.api.app import create_app
from services.api.runtime_support import build_agent_runtime, resolve_runtime_selection
from tests.e2e.literature_chain_support import (
    EUROPE_PMC_ID,
    OfflineEuropePmc,
    capabilities_for,
    europepmc_calls,
    europepmc_run_chain_provider,
    with_capabilities,
)
from tests.e2e.live_control_plane_support import with_contract_declared_experiment
from tests.e2e.live_run_support import openhands_deps, start_run

# 读面快照与 mock 端点与既有离线 e2e 同源（同一套装配，避免两处各写一份）。
from tests.e2e.test_ec03_real_runtime_offline_chain import _read_chain, mock_relay

__all__ = ["mock_relay"]

pytestmark = pytest.mark.requires_docker

_PROTOCOL = "research_report_chain_v1.yaml"
#: 装配方给出的脚本与镜像（合约 `experiment_execution` 不 pin 这两个量）。
_EXPERIMENT_SCRIPT = "examples/experiments/exact_match_index_benchmark.py"
_EXPERIMENT_IMAGE = "research-os-sandbox:m9-test"
#: **上游**（它自己开工时检索还没跑）与**下游**（应看到上游取回的）两个会话各自的合约 id。
_UPSTREAM_CONTRACT = "research_report_plan"
_DOWNSTREAM_CONTRACT = "multi_role_review"
#: 判据里写死（不 import 产品常量当预言机）：本协议 review phase 声明的四条绑定。
_REVIEW_BINDINGS = {
    "m12_artifact": "artifact.read",
    "openhands_workspace": "workspace.read",
    "ncbi_eutils": "literature.search",
    "europe_pmc": "literature.read",
}
#: 制品命名的固定前缀（工具结果；与 `tool_evidence._spilled_artifact_id` 同源）。
_TOOL_RESULT_PREFIX = "tool-result:"


class SessionSpecRecorder:
    """记录每次 `create_session` 的 **spec**（装配方包装；产品代码零改动）。

    为什么必须包在 runtime 上而不是读内部对象：`AgentSessionSpec` 是**产品路径**交给
    runtime 的那份事实本身 —— 判据读它，判的就是「会话拿到了什么」，不是「装配器返回了什么」。
    其余方法经 `__getattr__` **原样透传**（本包装只观察、不改行为）。
    """

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.specs: dict[str, AgentSessionSpec] = {}

    def create_session(self, spec: AgentSessionSpec) -> AgentSessionHandle:
        self.specs[spec.task_contract.id] = spec
        return self._inner.create_session(spec)  # type: ignore[no-any-return]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def context_of(self, contract_id: str) -> Any:
        """该合约那次会话的 `context_snapshot`（没有那次会话 ⇒ 判据自己点名失败）。"""
        spec = self.specs.get(contract_id)
        assert spec is not None, (
            f"本 run 没有为合约 {contract_id} 创建会话（已记录的合约：{sorted(self.specs)}）"
        )
        return spec.context_snapshot


def _assembled_deps(
    mock_relay_url: str, offline: OfflineEuropePmc
) -> tuple[Any, SessionSpecRecorder]:
    """产品装配 + 三段执行体缝（运行链检索 / 沙箱实验 / 报告汇编）+ **spec 记录器**。

    与 `test_research_report_arc_offline._assembled_deps` 同一手法（同一批产品对象、
    `map_tools=False` 走真实缺省装配），差别只有一个：runtime 外再包一层记录器。
    """
    deps = openhands_deps(mock_relay_url, map_tools=False)
    provider = europepmc_run_chain_provider(deps, offline)
    with_capabilities(
        deps,
        capabilities_for(
            deps, provider_id=EUROPE_PMC_ID, provider=provider, calls=europepmc_calls()
        ),
    )
    with_contract_declared_experiment(deps, script=_EXPERIMENT_SCRIPT, image=_EXPERIMENT_IMAGE)
    _attach_session_tools(deps)
    with_report_assembly(deps)
    with_retrieval_context(deps)
    recorder = SessionSpecRecorder(deps.runs._deps.runtime)
    _replace_runtime(deps, recorder)
    return deps, recorder


def with_retrieval_context(deps: Any) -> None:
    """把**检索内容 → 会话上下文**的装配器接进编排依赖（与两个产品组合根同一处装配决策）。

    **为什么必须在判据里接**（如实登记）：run-ready 夹具
    （`tests/api/run_fixtures.make_run_ready_deps`）不经产品组合根，因此它**不带**
    组合根里那一行 `retrieval_context=...`（与 `capabilities` / `experiment_task` /
    `report_task` 三条缝同一形态 —— 那三条也由装配方补）。接线用的是**产品件本身**
    （`services/api/retrieval_context_support.retrieval_context_builder`），本处不复制实现。
    """
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.retrieval_context_support import retrieval_context_builder

    deps.runs = RunOrchestrationService(
        replace(
            deps.runs._deps,
            retrieval_context=retrieval_context_builder(
                artifacts=deps.artifacts, ledger=deps.ledger
            ),
        )
    )


def with_report_assembly(deps: Any) -> None:
    """把**报告汇编器**接进运行编排的 `report_task` 缝（与 GOAL-077 同一条装配面）。"""
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.report_support import report_task_runner

    old = deps.runs
    assert old is not None
    deps.runs = RunOrchestrationService(
        replace(
            old._deps,
            report_task=report_task_runner(
                artifacts=deps.artifacts,
                ledger=deps.ledger,
                review_findings=deps.review_findings,
            ),
        )
    )


def _attach_session_tools(deps: Any) -> None:
    """出厂形态的会话工具注册面（本协议 review phase 声明的四条绑定）。"""
    from dataclasses import replace

    from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.assembly import policy_bindings
    from services.api.settings import ApiSettings

    invokers = {
        tool_name: (lambda arguments, conversation=None, _n=tool_name: f"{_n} ok")
        for tool_name in _REVIEW_BINDINGS.values()
    }
    settings = ApiSettings(
        agent_runtime="openhands",
        allow_localhost_endpoints=True,
        workspace_allow_host_shell=True,
    )
    policy = EndpointUrlPolicy(allow_localhost=True)
    runtime = build_agent_runtime(
        settings,
        credentials=deps.credentials,
        policy_evaluator=policy_bindings().get("policy_evaluator"),
        budget_ledger=deps.budget,
        register_session_tools=build_session_tools(invokers),
    )
    deps.runs = RunOrchestrationService(replace(deps.runs._deps, runtime=runtime))
    deps.runtime_selection = resolve_runtime_selection(settings)
    deps.endpoint_url_policy = policy


def _replace_runtime(deps: Any, recorder: SessionSpecRecorder) -> None:
    """把记录器装成编排服务实跑的 runtime（重建服务、复用同一批 Port 实例）。"""
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService

    deps.runs = RunOrchestrationService(replace(deps.runs._deps, runtime=recorder))


def _retrieved_artifact_ids(reads: Any) -> set[str]:
    """证据读面上**系统取得**的证据所指向的制品 id（`source_trust_label` 是既有列）。"""
    return {
        str(item["artifact_id"])
        for item in reads.evidence
        if item.get("source_trust_label") == "RETRIEVED" and item.get("artifact_id")
    }


def _all_artifact_ids(reads: Any) -> set[str]:
    """证据读面上**全部**证据的制品 id（含声明输入与自产件 —— 反证用）。"""
    return {str(item["artifact_id"]) for item in reads.evidence if item.get("artifact_id")}


class TestTheDownstreamSessionSeesTheRetrievedContent:
    """正向臂：下游会话的 spec 带上上游取回的检索内容（逐条与读面对应）。"""

    def test_the_downstream_context_is_not_empty_and_traces_to_retrieved_evidence(
        self, mock_relay: str
    ) -> None:
        offline = OfflineEuropePmc(requests=[])
        deps, recorder = _assembled_deps(mock_relay, offline)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)

        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        context = recorder.context_of(_DOWNSTREAM_CONTRACT)
        assert context is not None, "下游会话必须带上检索上下文（EC-01 的接线若断了 ⇒ 这里是 None）"
        refs = list(context.selected_refs)
        assert refs, ("下游会话的 selected_refs 必须非空（上游确实取回了两条检索证据）", context)

        # 逐条：每个 ref 都是工具结果制品，且能在**检索证据**里找到（性质 RETRIEVED）。
        retrieved = _retrieved_artifact_ids(reads)
        assert retrieved, ("读面上必须有系统取得的证据（否则本判据在空集上恒真）", reads.evidence)
        for ref in refs:
            assert str(ref).startswith(_TOOL_RESULT_PREFIX), (ref, refs)
            assert str(ref) in retrieved, (
                "下游上下文的每个 ref 都必须指向**系统取得**的证据",
                ref,
                sorted(retrieved),
            )
        # 上下文的内容也带性质标签与内容寻址摘要（不是裸 id 列表）。
        assert context.trust_labels == ["RETRIEVED"], context.trust_labels
        assert context.retrieval_digest, context
        assert context.token_allocation > 0, context

    def test_the_mock_retrieval_actually_ran(self, mock_relay: str) -> None:
        """前置事实：本 run 的检索**真的执行了**（否则正向臂可能是空转）。"""
        offline = OfflineEuropePmc(requests=[])
        deps, recorder = _assembled_deps(mock_relay, offline)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)

        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        assert [term for term in offline.requests if term.startswith("EXT_ID:")], offline.requests
        context = recorder.context_of(_DOWNSTREAM_CONTRACT)
        assert context is not None and context.selected_refs, context


class TestTheUpstreamSessionGetsNothing:
    """反证臂：**上游**会话开工时检索还没跑 ⇒ 集合为空**且点名**。

    这一条与正向臂**成对**：它把「上下文非空」从「所有会话都非空」这种平凡读数里
    拉出来 —— 上下文是**按时刻**装配的（上游开始时确实没有内容），不是一次性全量注入。
    """

    def test_the_upstream_context_is_empty_and_named(self, mock_relay: str) -> None:
        offline = OfflineEuropePmc(requests=[])
        deps, recorder = _assembled_deps(mock_relay, offline)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)

        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        context = recorder.context_of(_UPSTREAM_CONTRACT)
        assert context is not None, "上游会话也应当带上（空的）上下文 —— 空集合也要能判"
        assert list(context.selected_refs) == [], (
            "上游会话开工时检索尚未执行 ⇒ 其上下文必须为空",
            context,
        )
        assert context.retrieval_digest is None, context
        assert context.token_allocation == 0, context
        # 两个会话的上下文**不同**（不是同一个对象被复用）——「按时刻装配」的直接读数。
        downstream = recorder.context_of(_DOWNSTREAM_CONTRACT)
        assert downstream is not context, "两个 phase 的上下文必须是各自装配的"
        assert list(downstream.selected_refs) != list(context.selected_refs), (
            "上游空、下游非空 ⇒ 两者不得相同",
            context,
            downstream,
        )


class TestOnlyThisRunsRetrievedContentEnters:
    """射程边界：进上下文的是**本 run 系统取得**的内容，不是「证据链里的一切」。"""

    def test_the_refs_are_a_subset_of_retrieved_and_not_of_everything(
        self, mock_relay: str
    ) -> None:
        offline = OfflineEuropePmc(requests=[])
        deps, recorder = _assembled_deps(mock_relay, offline)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)

        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        context = recorder.context_of(_DOWNSTREAM_CONTRACT)
        assert context is not None
        refs = {str(ref) for ref in context.selected_refs}
        retrieved = _retrieved_artifact_ids(reads)
        everything = _all_artifact_ids(reads)
        assert refs <= retrieved, (sorted(refs - retrieved), sorted(retrieved))
        # **非平凡**：证据链里确实还有**别的**来源（声明输入 / 自产件）没进上下文 ——
        # 没有这一条，「refs ⊆ retrieved」可能只是因为两者都不存在。
        assert everything - retrieved, (
            "本 run 的证据链里应当还有非检索来源（声明输入 / 自产件）",
            sorted(everything),
        )
        assert not (refs & (everything - retrieved)), (
            "非检索来源（声明输入 / 自产件 / 报告）**不得**进上下文",
            sorted(refs & (everything - retrieved)),
        )


def test_the_seam_is_the_one_that_was_wired() -> None:
    """受判面自检：装配器真的接在**编排依赖**上（不是只存在于测试里）。

    没有这一条，「上下文非空」可能只是测试自己塞进去的。判的是**产品装配点**：
    `OrchestrationDependencies.retrieval_context` 非空，且它由两个组合根装配。
    """
    from services.api.composition import assemble
    from services.api.settings import ApiSettings

    deps = assemble(ApiSettings(db_path=":memory:"))
    try:
        assert deps.runs is not None
        assert deps.runs._deps.retrieval_context is not None, (
            "产品组合根必须接上检索上下文装配器（否则本文件的断言只证了测试装配）"
        )
    finally:
        deps.close()


class TestWhatEnteredTheContextIsReadableAftheFact:
    """GOAL-20261014-078 EC-03：**「进了什么」在既有读面上可复核**（HTTP 面端到端）。

    取证面是**既有路由** `GET /runs/{id}/artifacts` —— 上下文制品按 **task 前缀**命名，
    因此它天然落在 run 作用域里（**零新路由、零新 DTO、零快照改动**）。
    读到的载荷必须**自足**：run 标识、逐条标识 / 证据 id / 制品 id / 摘录都在里面。
    """

    def _context_payloads(self, client: TestClient, run_id: str) -> dict[str, Any]:
        """读面上该 run 的上下文制品 → `{artifact_id: payload}`（只经既有路由）。"""
        artifacts = client.get(f"/runs/{run_id}/artifacts").json()
        ids = [
            str(item["id"]) for item in artifacts if str(item["id"]).endswith(":retrieval_context")
        ]
        return {
            artifact_id: json.loads(
                client.get(f"/artifacts/{artifact_id}/content").content.decode("utf-8")
            )
            for artifact_id in ids
        }

    def test_the_context_is_on_the_read_face_and_matches_the_session(self, mock_relay: str) -> None:
        offline = OfflineEuropePmc(requests=[])
        deps, recorder = _assembled_deps(mock_relay, offline)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)
            payloads = self._context_payloads(client, str(run["id"]))

        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        # 两个会话 phase 各一件（实验/报告格不建会话 ⇒ 不写 —— 见实现里的分派）。
        assert len(payloads) == 2, sorted(payloads)
        # 下游非空、上游空且带理由（与 EC-02 的两向一致 —— 读面**印证**会话 spec）。
        non_empty = [p for p in payloads.values() if p["entries"]]
        empty = [p for p in payloads.values() if not p["entries"]]
        assert len(non_empty) == 1 and len(empty) == 1, payloads
        assert empty[0].get("reason"), ("空集合必须在读面上带理由", empty[0])
        # 载荷自足：run 标识 + 逐条四列在场。
        for payload in payloads.values():
            assert payload["run_id"] == str(run["id"]), payload
            for entry in payload["entries"]:
                for key in ("identifier", "evidence_id", "artifact_id", "shown"):
                    assert entry.get(key), (key, entry)

    def test_the_read_face_value_is_the_assembly_value(self, mock_relay: str) -> None:
        """**同源**：读面制品的 digest == 该 run 那次会话的 `retrieval_digest`。

        这条把「读面读到的」与「会话拿到的」钉成同一份事实 —— 不是分别算两次再比，
        而是**同一份字节**：写盘字节就是 `retrieval_digest` 的源（见实现）。
        """
        offline = OfflineEuropePmc(requests=[])
        deps, recorder = _assembled_deps(mock_relay, offline)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)
            artifacts = client.get(f"/runs/{run['id']}/artifacts").json()

        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        context = recorder.context_of(_DOWNSTREAM_CONTRACT)
        assert context is not None and context.selected_refs, context
        listed = [
            str(item["digest"])
            for item in artifacts
            if str(item["id"]).endswith(":retrieval_context")
        ]
        assert str(context.retrieval_digest) in listed, (
            "会话拿到的 `retrieval_digest` 必须**在场于**读面制品的 digest 里（同源）",
            context.retrieval_digest,
            listed,
        )
