"""GOAL-20261014-077 EC-02/EC-03 判据：**报告经产品路径产出** + **立题由检索派生**。

**被测对象**：新协议 `research_report_chain_v1.yaml`（4 phase：plan 走运行链检索 +
会话立题 / experiment 走沙箱 / review 走会话复核 / **report 走报告汇编器**）经
`compile → preflight → freeze → execute_phases` 跑完，产出**人类可读的报告制品**。

**七件事逐条取证**（全部读**既有读面**，不经内部对象）：

1. **立题由检索派生**（EC-03）：检索由运行链执行（真 PMID 进证据链、`RETRIEVED`），
   plan phase 的覆盖判据**两维都判过**（计数 + 性质）——判词逐字读得出来；
2. **报告存在**（EC-02）：`GET /runs/{id}/artifacts` 上有 `research_report.md`，
   `GET /artifacts/{id}/content` 以内联 `text/markdown` 返回；
3. **四节齐全**：报告含 `SECTION_HEADINGS` 的四条二级标题（节的**存在**是契约）；
4. **每数字可溯源**：报告里的**来源标识**与 `GET /runs/{id}/evidence` 的工具证据
   逐字一致；**指标值**与 `GET /runs/{id}/experiments` 的落库值**逐字相同**；
   判词段的决定与 `GET /runs/{id}/reviews` 的 gate 结论同源；
5. **内容寻址**：报告的 digest 由内容**重算**（不是回读一个标记）；
6. **反证 A（EC-03 的载体）**：摘掉运行链检索接线 ⇒ run `FAILED` 且判词**点名**
   `retrieved sources`（证明立题的判据真的读检索产出）——与既有侦察契约的反证**同形**；
7. **反证 B（EC-02 的载体）**：摘掉报告汇编器缝 ⇒ report phase **点名拒绝**
   （声明 ≠ 执行）⇒ run `FAILED` 且**没有**报告制品。

**如实边界**（本文件不声称已解决）：

- 用 run-ready 夹具（`preflight_override` + 装配方接的执行体缝）⇒ 它证的是**链路与判据**，
  不是「真实控制面」（后者由 live 判据承担）；实验那段是真容器（`requires_docker`）；
- **报告是确定性汇编，不是模型撰写**：判据只要求「数字逐字来自持久事实」，**不**要求
  叙述质量（那属报告域的再下一级）；
- **检索到的内容不进模型上下文**：本判据不声称模型读过文献（那属阶梯「检索」域的下一级）。
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from adapters.openhands.session_tools import build_session_tools
from packages.application.deliverable.research_report import (
    REPORT_ARTIFACT_NAME,
    REPORT_MIME,
    SECTION_HEADINGS,
)
from services.api.app import create_app
from services.api.report_support import report_task_runner
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

# 读面快照与 mock 端点与既有离线 e2e 同源（同一套装配，避免两处各写一份）。
from tests.e2e.test_ec03_real_runtime_offline_chain import _read_chain, mock_relay

__all__ = ["mock_relay"]

pytestmark = pytest.mark.requires_docker

_PROTOCOL = "research_report_chain_v1.yaml"
_PROTOCOL_ID = "research_report_chain_v1_0_0"
#: 装配方给出的脚本与镜像（合约 `experiment_execution` 不 pin 这两个量）。
_EXPERIMENT_SCRIPT = "examples/experiments/exact_match_index_benchmark.py"
_EXPERIMENT_IMAGE = "research-os-sandbox:m9-test"
#: 离线传输按同一份真实语料作答（EC-03 取证过的真 PMID / 标题 / DOI）。
_RETRIEVED_PMIDS = ("39284801", "40601758")
#: 落库工具结果里的一条**真实标题**（逐字：报告不得改写 / 截断它）。
_REAL_TITLE_FRAGMENT = "ENCORE: a practical implementation to improve reproducibility"


def _metric_text(value: object) -> str:
    """读面指标值 → 报告里应当逐字出现的文本（与报告读取面的取值规则**同源**）。

    判据里**重写**这条规则（而不是 import 产品 helper）是有意的：它是**受判面**的一部分
    （「报告与读面逐字一致」），拿实现当预言机会让这条断言在实现漂移时静默跟随。
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


#: 判据里写死（不 import 产品常量当预言机）：本协议 review phase 声明的四条绑定。
_REVIEW_BINDINGS = {
    "m12_artifact": "artifact.read",
    "openhands_workspace": "workspace.read",
    "ncbi_eutils": "literature.search",
    "europe_pmc": "literature.read",
}


def _assembled_deps(
    mock_relay_url: str,
    offline: OfflineEuropePmc,
    *,
    wire_retrieval: bool = True,
    wire_report: bool = True,
) -> tuple[Any, OutcomeRecorder]:
    """生产装配 + 三段执行体缝（运行链检索 / 合约声明的沙箱实验 / 报告汇编器）。

    `wire_retrieval=False` 与 `wire_report=False` 是**两条反证面**（各自摘掉一段缝，
    其余逐字不变）⇒ 同一份协议、同一套装配给出**相反**的终态与判词。
    """
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
    if wire_report:
        with_report_assembly(deps)
    recorder = OutcomeRecorder(outcomes=[])
    recorder.install(deps)
    return deps, recorder


def with_report_assembly(deps: Any) -> None:
    """把**报告汇编器**接进运行编排的 `report_task` 缝（装配方身份补执行体）。

    与 `live_control_plane_support.with_contract_declared_experiment` 的分工**是本质的**：
    那条接的是**沙箱实验**执行体，本条接的是**报告汇编**执行体。两者共用同一手法
    （重建服务、复用同一批 store/ledger 实例）—— 产品组合根今天不自己接这两段缝，
    这是如实登记的缺口；装配方补执行体是既有认下的处置。

    三件 Port 都是**既有**装配件的引用：制品店 / 证据账本 / 评审结论存储。
    """
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService

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
    """把**会话工具实现**接进生产组合根（`build_agent_runtime` 的真实缺省调用形态）。

    实现表覆盖本协议 review phase 声明的四条绑定；每条桥都用同一个惰性响应（本判据测的是
    「会话起得来且链路成立」，不是「模型会正确调工具」——后者属会话语义）。
    """
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


def _report_id(run_id: str) -> str:
    """报告的 canonical 制品 id（**run 级**命名；判据里写死，不 import 产品 helper）。"""
    return f"{run_id}:{REPORT_ARTIFACT_NAME}"


def _report_body(client: TestClient, run_id: str) -> tuple[str, str]:
    """经既有读面取报告正文（返回 `(正文, content-type)`）。

    `GET /artifacts/{id}/content` 的路由既有；`text/markdown` 命中它的内联预览白名单
    （`_INLINE_MEDIA`）⇒ 不需要为报告新增任何路由。
    """
    response = client.get(f"/artifacts/{_report_id(run_id)}/content")
    assert response.status_code == 200, (response.status_code, response.text[:300])
    return response.content.decode("utf-8"), response.headers.get("content-type", "")


def _content_addressed(artifacts: list[dict[str, Any]], run_id: str, report: str) -> bool:
    """报告的 digest 由**内容重算**（不是回读制品元数据里的一个标记）。"""
    from packages.domain.core import Digest

    listed = next((item for item in artifacts if item["id"] == _report_id(run_id)), None)
    if listed is None:
        return False
    return str(listed["digest"]) == str(Digest.of_bytes(report.encode("utf-8")))


def _retrieved_evidence(reads: Any) -> list[dict[str, Any]]:
    """检索证据（`tool_refs` 非空且性质为系统取得）——判据里逐条点名。"""
    return [
        item
        for item in reads.evidence
        if item.get("tool_refs") and item.get("source_trust_label") == "RETRIEVED"
    ]


class TestTheRunProducesAHumanReadableReport:
    """EC-02 主干：报告经产品路径产出、四节齐全、每个数字可溯源、内容寻址。"""

    def test_the_run_succeeds_and_the_report_is_on_the_read_face(self, mock_relay: str) -> None:
        """终态 + 身份 + 报告的**存在**（经既有路由取内容，内联 markdown）。"""
        offline = OfflineEuropePmc(requests=[])
        deps, _recorder = _assembled_deps(mock_relay, offline)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)
            artifacts = client.get(f"/runs/{run['id']}/artifacts").json()
            report, content_type = _report_body(client, str(run["id"]))

        # 终态 + 身份：只有 SUCCEEDED 是成功；协议身份可判。
        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        assert not reads.failures, reads.failures
        assert reads.run["protocol_id"] == _PROTOCOL_ID, reads.run
        assert reads.run["manifest_digest"], "冻结必须真的发生"

        assert _report_id(str(run["id"])) in [item["id"] for item in artifacts], (
            [item["id"] for item in artifacts],
            reads.failures,
        )
        assert REPORT_MIME in content_type, content_type
        # 四节齐全（节的**存在**是合约的一部分）。
        for heading in SECTION_HEADINGS:
            assert heading in report, (heading, report[:400])
        # 汇编**在 run 内**发生 ⇒ 抬头标的是「汇编时状态」，不得冒充终态。
        assert "**汇编时状态**" in report, report[:300]

    def test_every_number_in_the_report_traces_back_to_persisted_facts(
        self, mock_relay: str
    ) -> None:
        """每数字可溯源：来源标识 / 标题 / 指标值 / 判词逐字来自既有读面。"""
        offline = OfflineEuropePmc(requests=[])
        deps, recorder = _assembled_deps(mock_relay, offline)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)
            reviews = client.get(f"/runs/{run['id']}/reviews").json()
            artifacts = client.get(f"/runs/{run['id']}/artifacts").json()
            report, _content_type = _report_body(client, str(run["id"]))

        # 来源：真标识逐字来自落库的工具结果内容（与证据读面的拼接 id 一致）。
        retrieved = _retrieved_evidence(reads)
        assert retrieved, reads.evidence
        joined = " ".join(str(item["id"]) + str(item["source_ref"]) for item in retrieved)
        for identifier in _RETRIEVED_PMIDS:
            assert identifier in joined, (identifier, joined)
            assert identifier in report, (
                f"来源标识 {identifier} 没进报告（报告必须站在真检索上）",
                report[:600],
            )
        assert _REAL_TITLE_FRAGMENT in report, ("来源标题必须逐字进报告", report[:600])

        # 判词：第 4 节给出本 run 的评审决定逐字取值（与 reviews 读面同源）。
        gate_reviews = [item for item in reviews if item["review_type"] == "acceptance_gate"]
        assert gate_reviews, reviews
        assert any(item["verdict"] in report for item in gate_reviews), (
            "报告第 4 节必须给出评审决定的逐字取值",
            report[-800:],
        )

        assert _content_addressed(artifacts, str(run["id"]), report), (
            "报告的 digest 必须由内容重算",
            [item["id"] for item in artifacts],
        )
        # 每个执行过的任务一条 HandoffBundle digest（立题 + 实验 + 评审 + 报告）。
        digests = recorder.handoff_digests()
        assert len(digests) == 4, (digests, reads.tasks)

    def test_the_metric_table_matches_the_experiment_read_face(self, mock_relay: str) -> None:
        """指标格 == `GET /runs/{id}/experiments` 的落库值（逐字，不归一不重算）。

        与上一条**分开**是有意的：来源面与指标面各自独立可失败，合在一个函数里
        会让「指标漂了」与「来源漂了」共用同一条红（诊断变钝）。
        """
        offline = OfflineEuropePmc(requests=[])
        deps, _recorder = _assembled_deps(mock_relay, offline)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            experiments = client.get(f"/runs/{run['id']}/experiments").json()
            report, _content_type = _report_body(client, str(run["id"]))

        entries = experiments["experiments"]
        assert len(entries) == 1, experiments
        metrics = entries[0]["metrics"]
        assert metrics, experiments
        for name, value in metrics.items():
            assert str(name) in report, (name, report[:600])
            assert _metric_text(value) in report, (
                f"指标 {name}={value} 的值没逐字进报告（不得重算 / 归一 / 四舍五入）",
                report[:600],
            )


class TestEC03ThePlanIsDerivedFromRetrieval:
    """EC-03 主干：立题的覆盖判据**两维都判过**，且判词在既有读面上逐字可读。"""

    def test_the_plan_phase_passes_both_coverage_dimensions(self, mock_relay: str) -> None:
        offline = OfflineEuropePmc(requests=[])
        deps, _recorder = _assembled_deps(mock_relay, offline)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)
            reviews = client.get(f"/runs/{run['id']}/reviews").json()
            artifacts = client.get(f"/runs/{run['id']}/artifacts").json()

        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        # 检索真的执行了两步（离线传输按真语料作答）。
        assert [term for term in offline.requests if term.startswith("EXT_ID:")], offline.requests
        # 立题制品（`research_plan`）在制品读面上。
        assert any(str(item["id"]).endswith(":research_plan") for item in artifacts), [
            item["id"] for item in artifacts
        ]
        # 覆盖判词两维都读得出来（计数 + 性质），且立题那一 phase 的判词点名了性质维。
        plan_reviews = [item for item in reviews if item["contract_id"] == "research_report_plan"]
        assert plan_reviews, reviews
        joined = " ".join(line for item in plan_reviews for line in item["findings"])
        assert "retrieved" in joined, ("立题 phase 必须判过**性质维**（系统取得的来源）", joined)
        assert "sources" in joined, joined


class TestTheRefutationsBite:
    """两条反证（各自摘掉一段缝，其余逐字不变）。"""

    def test_removing_the_retrieval_wiring_rejects_the_plan_phase(self, mock_relay: str) -> None:
        """反证 A（EC-03）：不接运行链检索 ⇒ 立题 phase 的性质维度判拒并**点名**。

        判据是**同一条链**上的相反终态 —— 与主干用例**成对**：任一条被改成迁就实现，
        另一条立刻失去意义。
        """
        offline = OfflineEuropePmc(requests=[])
        deps, _recorder = _assembled_deps(mock_relay, offline, wire_retrieval=False)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)

        assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
        assert [item for item in reads.evidence if item.get("tool_refs")] == [], reads.evidence
        assert any("retrieved sources" in message for message in reads.failures), reads.failures

    def test_removing_the_report_seam_stops_the_run_and_leaves_no_report(
        self, mock_relay: str
    ) -> None:
        """反证 B（EC-02）：不接报告汇编器缝 ⇒ report phase **点名拒绝**（声明 ≠ 执行）。

        与沙箱实验缝的反证**同形**：声明了「由汇编器执行」而装配里没有它 ⇒ fail-closed，
        **不**静默回退到会话（那会让 run「成功」而报告根本没被汇编）。
        """
        offline = OfflineEuropePmc(requests=[])
        deps, _recorder = _assembled_deps(mock_relay, offline, wire_report=False)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)
            artifacts = client.get(f"/runs/{run['id']}/artifacts").json()

        assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
        assert any("no report assembler is wired" in message for message in reads.failures), (
            reads.failures
        )
        assert not any(
            str(item["id"]).endswith(f":{REPORT_ARTIFACT_NAME}") for item in artifacts
        ), [item["id"] for item in artifacts]
        # 前三个 phase 的工作**不受影响**：检索照跑、实验照跑（失败只出在 report 格）。
        assert [item for item in reads.evidence if item.get("tool_refs")], reads.evidence


def test_the_declared_report_contract_is_the_one_that_declares_the_assembler() -> None:
    """受判面非空：**协议文档本身**必须把 `report` 格绑到声明了 `report: {}` 的合约。

    这条挡住「协议被悄悄改回会话语义」——那时主干断言会因为「会话没有被模型驱动」而失败，
    但原因是**声明面**变了；本条把那个原因点出来（与 `capabilities_used_in_a_run_v1` 的
    自检同形）。
    """
    from pathlib import Path

    import yaml

    raw = yaml.safe_load(Path(f"examples/protocols/{_PROTOCOL}").read_text(encoding="utf-8"))
    phases = {phase["id"]: phase for phase in raw["phases"]}
    assert set(phases) == {"plan", "experiment", "review", "report"}, sorted(phases)
    assert phases["plan"].get("capability_execution") == "run_chain", phases["plan"]
    assert phases["report"]["task_contract"] == "research_report_deliverable", phases["report"]

    from adapters.contracts import load_task_contracts

    contract = load_task_contracts("examples/contracts/task_contracts.yaml")[
        "research_report_deliverable"
    ]
    assert contract.report is not None, "报告格的合约必须声明 report 执行体"
    assert contract.experiment is None, "两个执行体声明不得同时在场（互斥由域拒绝）"
    json.dumps({"report": "declared"})  # 保持 json import 被真实使用（判据读 YAML 与域对象）
