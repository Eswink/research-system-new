"""GOAL-028 EC-03 判据：**默认装配上的完整科研子迭代**（合并 EC-01/EC-02 的验收）。

**与 EC-01 判据的差别（本文件的实质）**：`test_tool_binding_on_the_default_assembly.py`
证的是「声明式映射**机制**成立」（用它自带的**最小**协议：两 phase、无 run-chain、
无实验、无评审门）；本文件跑**真实那条**协议 `multi_role_research_v1.yaml`
（scouting 走 run-chain 检索 → experiment 走沙箱容器 → review 带质量门），
五件事**全部**要成立。

**五件事逐条取证**：

1. **默认装配实跑**：走 `build_agent_runtime` 的真实缺省（**非** `map_tools=True`），
   装配方给会话工具实现 ⇒ run 到 `SUCCEEDED`，`manifest_digest` 在场；
2. **检索 phase 的真标识 + `RETRIEVED`**：由 provider 声明的 `network_domains` 决定
   （唯一判定点，不由本步自称）；
3. **实验 phase 的真 metrics**：容器制品 + `image_digest` 在场；
4. **交付物与覆盖来源的 claim relation**：`GET /runs/{id}/evidence` 真读得到四列；
5. **HandoffBundle 的 digest 序列**：逐任务一条 `sha256:<64hex>`、互不相同。

**反证臂**：摘掉上游检索接线 ⇒ 侦察 phase 的**性质维度**判拒（判词点名 `retrieved sources`）
⇒ run `FAILED` —— 评审真的能判不通过。

**如实边界**：与 EC-03 的既有判据同一条 —— 用 run-ready 夹具（受控 pin + 装配方接的
执行体缝）⇒ 证的是**链路与判据**；实验那段是真容器（`requires_docker`）。
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from adapters.openhands.session_tools import build_session_tools
from services.api.app import create_app
from services.api.runtime_support import build_agent_runtime, resolve_runtime_selection
from tests.e2e.literature_chain_support import (
    EUROPE_PMC_ID,
    OfflineEuropePmc,
    OutcomeRecorder,
    capabilities_for,
    europepmc_calls,
    europepmc_run_chain_provider,
    with_capabilities,
)
from tests.e2e.live_control_plane_support import with_contract_declared_experiment
from tests.e2e.live_run_support import openhands_deps, start_run

# 复用既有离线 e2e 的 mock 端点与读面（同一套装配，避免两处各写一份）。
from tests.e2e.test_ec03_real_runtime_offline_chain import _read_chain, mock_relay

__all__ = ["mock_relay"]

pytestmark = pytest.mark.requires_docker

_PROTOCOL = "multi_role_research_v1.yaml"
_PROTOCOL_ID = "multi_role_research_v1_0_0"
_EXPERIMENT_SCRIPT = "examples/experiments/exact_match_index_benchmark.py"
_EXPERIMENT_IMAGE = "research-os-sandbox:m9-test"
#: 判据里写死（不 import 产品常量当预言机）：本协议 review phase 声明的四条绑定。
_EXPECTED_BINDINGS = {
    "m12_artifact": "artifact.read",
    "openhands_workspace": "workspace.read",
    "ncbi_eutils": "literature.search",
    "europe_pmc": "literature.read",
}
#: 离线传输按同一份真实语料作答（承 EC-03 取证过的真 PMID）。
_RETRIEVED_PMIDS = ("39284801", "40601758")


def _production_deps(
    mock_relay_url: str, offline: OfflineEuropePmc, *, wire_retrieval: bool
) -> tuple[Any, OutcomeRecorder]:
    """**生产装配** + 运行链检索 + 沙箱实验缝 + 结果记录器（**不**用 `map_tools` 后门）。"""
    deps = openhands_deps(mock_relay_url, map_tools=False)
    if wire_retrieval:
        provider = europepmc_run_chain_provider(deps, offline)
        with_capabilities(
            deps,
            capabilities_for(
                deps, provider_id=EUROPE_PMC_ID, provider=provider, calls=europepmc_calls()
            ),
        )
    with_contract_declared_experiment(deps, script=_EXPERIMENT_SCRIPT, image=_EXPERIMENT_IMAGE)
    _attach_session_tools(deps)
    recorder = OutcomeRecorder(outcomes=[])
    recorder.install(deps)
    return deps, recorder


def _attach_session_tools(deps: Any) -> None:
    """把**会话工具实现**接进生产组合根（`build_agent_runtime` 的真实缺省调用形态）。

    实现表覆盖**本协议声明的四条绑定**的目标工具名；每条桥都用同一个惰性响应
    （本判据测的是「会话起得来且链路成立」，不是「模型会正确调工具」——后者属会话语义）。
    """
    from dataclasses import replace

    from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.assembly import policy_bindings
    from services.api.settings import ApiSettings

    invokers = {
        tool_name: (lambda arguments, conversation=None, _n=tool_name: f"{_n} ok")
        for tool_name in _EXPECTED_BINDINGS.values()
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


class TestTheRealProtocolRunsOnTheDefaultAssembly:
    """AC-1 + AC-2 ①②④⑤：默认装配跑到终态，逐相位产出可复核。"""

    def test_the_run_reaches_success_and_every_phase_is_checkable(self, mock_relay: str) -> None:
        offline = OfflineEuropePmc(requests=[])
        deps, recorder = _production_deps(mock_relay, offline, wire_retrieval=True)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)
            experiments = client.get(f"/runs/{run['id']}/experiments").json()

        # ① 默认装配实跑（不靠 map_tools 后门）：会话必须真起得来、run 真到终态。
        assert not any("is not registered" in message for message in reads.failures), (
            "生产装配下会话没建起来 ⇒ provider→SDK 映射没生效",
            reads.failures,
        )
        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        assert reads.run["protocol_id"] == _PROTOCOL_ID, reads.run
        assert reads.run["manifest_digest"], "冻结必须真的发生"

        # ② 检索 phase：真标识 + `RETRIEVED`（性质由 provider 声明决定）。
        retrieved = [item for item in reads.evidence if item.get("tool_refs")]
        assert retrieved, reads.evidence
        assert {item["source_trust_label"] for item in retrieved} == {"RETRIEVED"}, retrieved
        joined = " ".join(str(item["id"]) + str(item["source_ref"]) for item in retrieved)
        assert any(pmid in joined for pmid in _RETRIEVED_PMIDS), (joined, retrieved)

        # ③ 实验 phase：容器制品 + 镜像指纹（真 metrics，不是桩）。
        entries = experiments["experiments"]
        assert len(entries) == 1, experiments
        assert entries[0]["image_digest"], ("制品来自容器", entries[0])
        names = {str(item).rsplit(":", 1)[-1] for item in entries[0]["artifact_ids"]}
        assert "metrics" in names, names

        # ④ 读面四列（交付物与其覆盖来源之间的 claim relation 经读面可见）。
        for item in retrieved:
            for column in ("id", "source_ref", "content_digest", "source_trust_label"):
                assert item.get(column), (column, item)

        # ⑤ HandoffBundle 的 digest 序列：逐任务一条、互不相同。
        digests = recorder.handoff_digests()
        assert len(digests) == 3, (digests, reads.tasks)
        assert all(item.startswith("sha256:") and len(item) == 71 for item in digests), digests
        assert len(set(digests)) == len(digests), "各任务的 HandoffBundle digest 必须互不相同"


class TestTheDeclaredBindingsCoverTheSessionFace:
    """AC-1 的前提：**真的会开会话**的 phase，其会话工具面必须全被绑定。"""

    def test_every_provider_in_a_session_phase_face_is_bound(self) -> None:
        """只对**会话 phase** 断言绑定覆盖。

        为什么把 `experiment` 排除在外（如实说明，不是放宽）：那个 phase 的合约声明了
        `experiment: {}`（「由既有沙箱实验后端跑一次实验」）⇒ 派发按**契约声明**走
        `dispatch_experiment`（`phase_runner` 的既有语义：`contract.experiment is not None`
        就派给沙箱），**根本不创建会话** ⇒ 它的会话工具面在实际运行里**从不被消费**。
        对「从不被消费的面」要求绑定会给协议加一行没有语义的声明。
        **判据因此按 phase 的 `strategy` 分流**：`single_agent` 走会话（必须全绑），
        `deterministic` 走执行体（不适用）。
        """
        from adapters.contracts.protocol_loaders import load_protocol
        from packages.application.protocol_compile import compile_protocol
        from packages.application.run_orchestration.session_resolution import (
            session_tool_bindings,
            session_tool_face,
        )
        from packages.domain.protocols import PhaseStrategy
        from services.api.catalog import load_catalog_snapshot, load_project_settings

        protocol = load_protocol(f"examples/protocols/{_PROTOCOL}")
        result = compile_protocol(protocol, load_catalog_snapshot(), load_project_settings())
        assert result.plan is not None, result.findings
        session_phases = 0
        for phase in result.plan.phases:
            face = session_tool_face(result.plan, phase.id)
            if phase.strategy is not PhaseStrategy.SINGLE_AGENT:
                continue
            if not face:
                continue  # 全被 run-chain 排除（scouting）⇒ 无会话工具需要绑定
            session_phases += 1
            bound = dict(session_tool_bindings(result.plan, phase.id))
            assert set(face) <= set(bound), (phase.id, sorted(set(face) - set(bound)))
        assert session_phases == 1, ("本协议恰有一个带会话面的 phase", session_phases)

    def test_the_review_phase_binds_exactly_the_expected_pairs(self) -> None:
        from adapters.contracts.protocol_loaders import load_protocol
        from packages.application.protocol_compile import compile_protocol
        from packages.application.run_orchestration.session_resolution import session_tool_bindings
        from services.api.catalog import load_catalog_snapshot, load_project_settings

        protocol = load_protocol(f"examples/protocols/{_PROTOCOL}")
        result = compile_protocol(protocol, load_catalog_snapshot(), load_project_settings())
        assert result.plan is not None, result.findings
        assert dict(session_tool_bindings(result.plan, "review")) == _EXPECTED_BINDINGS


class TestTheReviewCanActuallyReject:
    """AC-2 ③：评审**真能判不通过**（反证分支 —— 摘掉上游检索接线 ⇒ 判拒 ⇒ FAILED）。"""

    def test_removing_the_retrieval_wiring_rejects_the_scouting_phase(
        self, mock_relay: str
    ) -> None:
        offline = OfflineEuropePmc(requests=[])
        deps, _recorder = _production_deps(mock_relay, offline, wire_retrieval=False)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)

        assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
        assert [item for item in reads.evidence if item.get("tool_refs")] == [], reads.evidence
        assert any("retrieved sources" in message for message in reads.failures), reads.failures
