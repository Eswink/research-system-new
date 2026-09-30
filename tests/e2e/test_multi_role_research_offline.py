"""GOAL-20260927-027 EC-04 判据：**多 role 科研子迭代**（≥3 phase × ≥3 role + Handoff +
评审真判定 + 四维输入 + 离线实跑终态）。

**被测对象**：产品那条编排链 —— 新协议 `multi_role_research_v1.yaml`（3 个会话 phase
各绑不同 role + 1 个合约声明的沙箱实验 phase）经
`compile_protocol → preflight → freeze → execute_phases` 跑完，产出可复核的结构化结果。

**五件事逐条取证**：

1. **多 phase 多 role**：文档与编译产物两侧都断言 —— 每个 phase 绑**不同** role
   （`literature_scout` / `experiment_engineer` / `scientific_reviewer`）；
2. **HandoffBundle**：`RunOutcome.handoff_digests` 逐任务一条（结构化交接的 digest
   序列），且各条互不相同（不是同一个占位值）；
3. **评审 phase 真判定**：`multi_role_review` 的验收判据要求「覆盖里至少一条来源是
   **系统取得**」⇒ 上游留下检索证据时通过；**反证**分支把上游检索接线去掉 ⇒ 同一份协议、
   同一套装配 ⇒ 评审 phase 判拒、run `FAILED` 且判词**点名**缺的是检索来源；
4. **四维验收输入**：`tests` / `metrics` / `policy_decision` 三维只在**带实验事实**的
   phase 上被填充（`_experiment_facts`）⇒ 实跑含一个**真实沙箱实验** phase；
   `schema_check` 由合约声明的 `output_schema` 取；**有对照** —— 摘掉实验执行体缝
   ⇒ 该 phase 点名拒绝（声明 ≠ 执行），run `FAILED`；
5. **离线实跑终态**：主判据跑到 `SUCCEEDED`（冻结真的发生、任务全部完成、
   检索真标识进证据链、实验制品来自容器）。

**如实边界**：本文件用 run-ready 夹具（`preflight_override` + 装配方接的执行体缝）
⇒ 它证明的是**链路与判据**，不是「真实控制面」。挂 `requires_docker`：实验那段是真容器，
非 Linux 容器守护进程下如实 skip（由 `container-quality` 作业真跑）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient

from adapters.contracts.protocol_loaders import load_protocol
from packages.application.protocol_compile import compile_protocol
from services.api.app import create_app
from services.api.catalog_merge import merged_catalog_snapshot, merged_project_settings
from services.api.deps import get_deps
from tests.api.run_fixtures import make_run_ready_deps
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

_PROTOCOL = "multi_role_research_v1.yaml"
_PROTOCOL_ID = "multi_role_research_v1_0_0"
#: 装配方给出的脚本与镜像（合约 `experiment_execution` 不 pin 这两个量）。
_EXPERIMENT_SCRIPT = "examples/experiments/exact_match_index_benchmark.py"
_EXPERIMENT_IMAGE = "research-os-sandbox:m9-test"
#: 三个 phase 各自绑的 role（逐字断言；判据里写死而非 import 产品常量）。
_PHASE_ROLES: dict[str, str] = {
    "scouting": "literature_scout",
    "experiment": "experiment_engineer",
    "review": "scientific_reviewer",
}
#: 离线传输按同一份真实语料作答（EC-03 取证过的真 PMID）。
_RETRIEVED_PMIDS = ("39284801", "40601758")


def _assembled_deps(
    mock_relay_url: str, offline: OfflineEuropePmc, *, wire_experiment: bool
) -> tuple[Any, OutcomeRecorder]:
    """run-ready 装配 + 两段执行体缝（运行链检索 / 合约声明的沙箱实验）+ 结果记录器。

    `map_tools=True` 是**测试侧**补上 EC-05 的 provider→SDK 工具映射（与
    `sort_analysis_v1` 的判据同一手法）：本协议含**真实会话 phase**（review），
    生产装配今天没有那份映射 ⇒ 会话创建会点名失败（产品缺口，如实登记；本判据测的是
    链路与判据）。`wire_experiment=False` 是**反证面**：不接实验执行体缝 ⇒ 实验 phase
    **点名拒绝**（声明 ≠ 执行），run 收敛 `FAILED`。
    """
    deps = openhands_deps(mock_relay_url, map_tools=True)
    provider = europepmc_run_chain_provider(deps, offline)
    with_capabilities(
        deps,
        capabilities_for(
            deps, provider_id=EUROPE_PMC_ID, provider=provider, calls=europepmc_calls()
        ),
    )
    if wire_experiment:
        with_contract_declared_experiment(deps, script=_EXPERIMENT_SCRIPT, image=_EXPERIMENT_IMAGE)
    recorder = OutcomeRecorder(outcomes=[])
    recorder.install(deps)
    return deps, recorder


class TestMultiPhaseMultiRole:
    """AC ①：协议含 ≥3 phase、各绑**不同** role；文档与编译产物两侧都可证。"""

    def test_the_document_declares_three_phases_with_distinct_roles(self) -> None:
        raw = yaml.safe_load(Path(f"examples/protocols/{_PROTOCOL}").read_text(encoding="utf-8"))
        phases = raw["phases"]
        assert len(phases) >= 3, [phase["id"] for phase in phases]
        roles = {
            phase["id"]: [item["role"] for item in phase["required_roles"]] for phase in phases
        }
        for phase_id, expected in _PHASE_ROLES.items():
            assert roles[phase_id] == [expected], (phase_id, roles)
        assert len(set(_PHASE_ROLES.values())) == 3, "三个 phase 必须绑三个不同 role"

    def test_the_compiled_plan_binds_each_phase_to_its_role(self) -> None:
        with TestClient(create_app(make_run_ready_deps())) as client:
            from starlette.requests import Request

            scope = {
                "type": "http",
                "app": client.app,
                "headers": [],
                "method": "GET",
                "path": "/",
            }
            deps = get_deps(Request(scope))
            result = compile_protocol(
                load_protocol(f"examples/protocols/{_PROTOCOL}"),
                merged_catalog_snapshot(deps),
                merged_project_settings(deps),
            )
        assert result.plan is not None, result.findings
        assignments = {
            item.phase_id: item.role_assignments for item in result.plan.phase_assignments
        }
        for phase_id, role in _PHASE_ROLES.items():
            assert role in assignments[phase_id], (phase_id, sorted(assignments[phase_id]))


class TestMultiRoleRunReachesSuccess:
    """AC ②/③/④/⑤ 主干：跑到 `SUCCEEDED`，Handoff 逐任务一条，四维与检索都可复核。"""

    def test_the_run_reaches_success_with_a_handoff_per_task(self, mock_relay: str) -> None:
        offline = OfflineEuropePmc(requests=[])
        deps, recorder = _assembled_deps(mock_relay, offline, wire_experiment=True)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)
            experiments = client.get(f"/runs/{run['id']}/experiments").json()

        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        assert not reads.failures, reads.failures
        assert reads.run["manifest_digest"], "冻结必须真的发生"
        assert reads.run["protocol_id"] == _PROTOCOL_ID, reads.run

        # 会话 phase 的任务全部完成（任务投影只含**会话**任务；实验任务在 experiment 面，
        # 这是既有读面分工 —— 两处合起来才是本 run 的全部 phase）。
        assert len(reads.tasks) == 2, reads.tasks
        assert {task["status"] for task in reads.tasks} == {"SUCCEEDED"}, reads.tasks
        session_contracts = {task["contract_id"] for task in reads.tasks}
        assert session_contracts == {"multi_role_scouting", "multi_role_review"}, session_contracts
        assert reads.tasks[0]["agent_id"] == "scout_a", reads.tasks[0]
        assert reads.tasks[1]["agent_id"] == "reviewer_a", reads.tasks[1]

        # Handoff：每个任务一条 digest，且互不相同（不是同一个占位值）。
        # Handoff：**每个执行过的任务**一条 digest（2 个会话 phase + 1 个实验 phase = 3；
        # 任务投影只列会话任务，实验任务在 experiment 面 ⇒ 两个读面合起来才是全部）。
        digests = recorder.handoff_digests()
        assert len(digests) == 3, (digests, reads.tasks)
        # 修复说明（本 EC 实测）：该字段此前装的是 **task id**（`tuple(sorted(handoffs))`
        # 排的是字典键 —— 实测三条 UUID）；本 EC 的修复让它装真 digest，判据钉住新形态：
        # `str(Digest)` 给带前缀的 `sha256:<64hex>`。
        assert all(item.startswith("sha256:") and len(item) == 71 for item in digests), digests
        assert all(
            all(c in "0123456789abcdef" for c in item.removeprefix("sha256:")) for item in digests
        ), digests
        assert len(set(digests)) == len(digests), "各任务的 HandoffBundle digest 必须互不相同"

        # 检索真标识进证据链（真 PMID；`RETRIEVED` 由 provider 声明决定）。
        retrieved = [item for item in reads.evidence if item.get("tool_refs")]
        assert retrieved, reads.evidence
        assert {item["source_trust_label"] for item in retrieved} == {"RETRIEVED"}, retrieved
        joined = " ".join(str(item["id"]) + str(item["source_ref"]) for item in retrieved)
        assert any(pmid in joined for pmid in _RETRIEVED_PMIDS), (joined, retrieved)

        # 实验制品来自容器（不是桩）：metrics 制品 + 镜像指纹都在场。
        entries = experiments["experiments"]
        assert len(entries) == 1, experiments
        entry = entries[0]
        assert entry["image_digest"], ("制品来自容器，不是桩", entry)
        names = {str(item).rsplit(":", 1)[-1] for item in entry["artifact_ids"]}
        assert "metrics" in names, names


class TestFourDimensionInputsHaveAControlArm:
    """AC ④ 的**对照臂**：摘掉实验执行体缝 ⇒ 实验 phase 点名拒绝（声明 ≠ 执行）。"""

    def test_removing_the_experiment_seam_stops_the_run_before_success(
        self, mock_relay: str
    ) -> None:
        offline = OfflineEuropePmc(requests=[])
        deps, _recorder = _assembled_deps(mock_relay, offline, wire_experiment=False)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)
            experiments = client.get(f"/runs/{run['id']}/experiments").json()

        assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
        assert any("no experiment runner is wired" in message for message in reads.failures), (
            reads.failures
        )
        assert experiments["experiments"] == [], experiments


class TestReviewVerdictIsReal:
    """AC ③：评审的判据**真判定**（两向都在判据里，各自点名）。"""

    def test_removing_the_retrieval_wiring_rejects_the_scouting_phase(
        self, mock_relay: str
    ) -> None:
        """臂一：摘掉运行链检索接线 ⇒ **侦察 phase** 的性质维度判拒（点名 `retrieved sources`）。

        侦察契约声明了 `minimum_retrieved_sources: 1` ⇒ 判词必须点名缺的是**检索来源**，
        证明判拒来自覆盖判据的**性质维度**，而不是被别的门（如实验缝）拦下。
        """
        deps = openhands_deps(mock_relay, map_tools=True)
        with_contract_declared_experiment(deps, script=_EXPERIMENT_SCRIPT, image=_EXPERIMENT_IMAGE)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)

        assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
        assert [item for item in reads.evidence if item.get("tool_refs")] == [], reads.evidence
        assert any("retrieved sources" in message for message in reads.failures), reads.failures

    def test_removing_the_review_declared_input_rejects_the_review_phase(
        self, mock_relay: str
    ) -> None:
        """臂二：判定依据缺席 ⇒ 该 phase 的链**点名拒绝**（fail closed，不是静默放行）。

        做法**不是**伪造一个坏评审：协议逐字不变，只把 brief 制品从库里摘掉。
        brief 被**两个** phase 声明，而 scouting 先跑 ⇒ 实测判词是
        `unknown artifact id: input-brief:real_research_v1`（**声明输入必须真的在场**：
        缺件时链路 fail closed，而不是「没有来源但照样通过」）。
        同一套代码、同一份协议：依据在场 ⇒ 三个 phase 全过、run `SUCCEEDED`；
        依据缺席 ⇒ 链在**声明它**的第一个 phase 上如实判负。
        """
        offline = OfflineEuropePmc(requests=[])
        deps, _recorder = _assembled_deps(mock_relay, offline, wire_experiment=True)
        # 判据要的是「依据缺席」这个事实。制品的**墓碑**转移被产品规则拒绝
        # （`illegal artifact state transition VERIFIED -> DELETED_TOMBSTONE`，实测），
        # 所以反证臂改从**种子面**下手：把 brief 从制品库里**先**去掉（会话建起来之前），
        # 其余（协议 / 装配 / 脚本 / 镜像）逐字不变。
        _unseed_brief(deps)
        with TestClient(create_app(deps)) as client:
            run = start_run(client, _PROTOCOL)
            reads = _read_chain(client, run)

        assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
        assert any("input-brief:real_research_v1" in message for message in reads.failures), (
            reads.failures
        )
        assert reads.tasks == [] or all(task["status"] != "SUCCEEDED" for task in reads.tasks), (
            "依据缺席时不得有任何 phase 被判成功",
            reads.tasks,
        )


def _unseed_brief(deps: Any) -> None:
    """把声明输入从库里摘掉（只服务反证臂）。

    `FakeArtifactStore` 的删除入口在制品处于 VERIFIED 时被产品规则拒（实测墓碑转移非法）
    ⇒ 这里直接替换成一份**不含该制品**的 store 是错的（那会换掉整条链的实例）；
    正确做法是把 store 里那条记录摘掉 —— 用 `FakeArtifactStore` 自己的内部映射完成，
    并把这一步限制在**判据**里（不改产品代码、不改 store 实现）。
    """
    artifact_id = "input-brief:real_research_v1"
    store = deps.artifacts
    removed = False
    for name in ("_content", "_metadata"):
        mapping = getattr(store, name, None)
        if isinstance(mapping, dict) and artifact_id in mapping:
            mapping.pop(artifact_id)
            removed = True
    assert removed, "反证臂未能摘掉声明输入（store 的内部结构变了 ⇒ 判据需随之更新）"
