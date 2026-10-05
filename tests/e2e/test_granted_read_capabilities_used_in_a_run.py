"""GOAL-20261006-031 EC-01(e) 判据：**本轮放行的读能力真的被一次 run 用上**。

**它补的是什么**：EC-01(a) 把 6 条只读能力逐条放行（`policy.yaml` 的 `allow`），但
**放行 ≠ 被用** —— 放行只让策略求值从 `DENY` 变 `ALLOW`；「真的被调用、产出真的被下游
消费」是另一件事，必须另有证据。本文件把这条落差收成机械事实（与 GOAL-030 EC-01 同手法，
对象换成**本轮新放行**的能力）。

**被测对象**：`examples/protocols/granted_reads_used_in_a_run_v1.yaml`（本轮新增）经
`compile → preflight → freeze → execute_phases` 跑完 —— 两个 phase 都由**运行链**执行：

  * `probe`：`run.read` / `budget.read`（**两条本轮新放行**）各一次；
  * `review`：`claim.read`（**本轮新放行**）与 `evidence.read`（既有放行）读本 run 的
    claim relation / 证据投影 —— 两者的**返回内容**里含 `probe` 两条工具证据的 id
    ⇒ 上游产出**被下游消费**（两条各是一次独立的下游消费读数）。

**装配与读面辅助在 `tests/e2e/granted_reads_support.py`**（规模门禁：本文件 ≤ 450 行）；
那里的模块 docstring 记录**建档实测的两条结构事实**（`run.read` 读不到本 run 自己；
预算预留的 scope 是 `phase:*`），本判据按它们设计。

**五件事逐条取证**（全部读**既有读面**，不经内部对象）：

1. **真被调用**：三条新放行能力（`run.read` / `budget.read` / `claim.read`）各有一条工具
   证据，`tool_refs` 逐条点名 `("m12_artifact", <tool_id>)` —— **逐条**在场，缺一即判红并
   点名缺哪条（MEM-160）。
2. **产出可复核**：工具证据的 `artifact_id` 是 `tool-result:` 命名的内容寻址制品，
   在 `GET /runs/{id}/artifacts` 读面上取得到且 digest 在场。
3. **下游消费**（本判据的核心）：`review` 的 `claim.read` **与** `evidence.read` 的
   **返回内容**里各含 `probe` 两条工具证据的 id。它与「两个 phase 都调了工具」**不是同一
   件事**：后者只证明调了两遍。
4. **反证点名**：撤掉 provider 实例 ⇒ run 失败且判词点名 provider / 能力 / 工具
   （`TestAMissingImplementationIsNamed`）。
5. **实跑终态**：跑到 `SUCCEEDED`，且 `manifest_digest` 在场（冻结真的发生）。

**如实边界**（本文件不声称已解决）：

- 三条读的是**本次 run 自己的 canonical 状态**（既存 run 行 / 预算账本 / claim relation），
  **不是外部检索** —— 本判据**不**声称该协议做过文献检索，也**不**声称读结果影响了
  交付物的科学结论（验收门只判产物存在与来源覆盖）。
- 只做 **3 条**新放行能力（`run.read` / `budget.read` / `claim.read`）：
  `deliverable.read` / `experiment.read` / `experiment_plan.read` 需要 run 已经产出交付物 /
  已登记实验事实，本协议不构造它们；它们的**放行面**由
  `tests/application/preflight/test_release_expansion_is_read_only.py` 逐条受判。
  **本文件不声称「6 条全部被用」**（如实登记在 GOAL 的 `W31-1`）。
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from tests.e2e.granted_reads_support import (
    EVIDENCE_READ,
    PROBE_PHASE,
    PROBE_RELEASED,
    PROTOCOL,
    PROVIDER,
    REVIEW_PHASE,
    REVIEW_RELEASED,
    SEEDED_RUN_ID,
    TOOL_IDS,
    app,
    assembled_deps,
    calls,
    content_of,
    deps_without_grant,
    preflight_report,
    tool_evidence,
    upstream_evidence_ids,
)
from tests.e2e.live_run_support import start_run as _start
from tests.e2e.test_ec03_real_runtime_offline_chain import _read_chain, mock_relay

__all__ = ["mock_relay"]

_PROTOCOL = PROTOCOL


class TestTheNewlyGrantedCapabilitiesAreReallyCalled:
    """① 三条**本轮新放行**能力**都真的被调用**（调用证据逐条在场）。"""

    def test_each_newly_granted_capability_leaves_a_call_evidence(self, mock_relay: str) -> None:
        """**主判据**：三条各留一条工具证据，`tool_refs` 逐条点名（缺哪条点名哪条）。

        逐 phase 分开取证据（`probe` 两条 / `review` 一条）—— 单键索引在跨 phase 同名工具时
        会**后写覆盖前写**（GOAL-030 EC-01 实测过的掩蔽形态）。
        """
        deps = assembled_deps(mock_relay)
        with TestClient(app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))

        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        probe_tools = tool_evidence(reads, phase=PROBE_PHASE)
        review_tools = tool_evidence(reads, phase=REVIEW_PHASE)
        missing_probe = [
            capability for capability in PROBE_RELEASED if TOOL_IDS[capability] not in probe_tools
        ]
        assert missing_probe == [], (
            "probe 声明的两条新放行能力必须有调用证据（缺哪条点名哪条）",
            missing_probe,
            sorted(probe_tools),
        )
        missing_review = [
            capability for capability in REVIEW_RELEASED if TOOL_IDS[capability] not in review_tools
        ]
        assert missing_review == [], (
            "review 声明的**新放行**能力必须有调用证据（缺哪条点名哪条）",
            missing_review,
            sorted(review_tools),
        )

    def test_the_run_is_really_frozen(self, mock_relay: str) -> None:
        """实跑终态的前置：冻结真的发生（否则「跑通」可能只是没执行）。"""
        deps = assembled_deps(mock_relay)
        with TestClient(app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))

        assert reads.run["manifest_digest"], reads.run
        assert "manifest.frozen" in reads.types, sorted(reads.types)


class TestTheOutputIsReviewableDownTheReadFace:
    """② 上游产出**可复核**：工具结果落在内容寻址制品上，读面取得到。"""

    def test_each_result_is_a_content_addressed_artifact(self, mock_relay: str) -> None:
        deps = assembled_deps(mock_relay)
        with TestClient(app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))

        scoped: dict[str, tuple[str, ...]] = {
            PROBE_PHASE: PROBE_RELEASED,
            REVIEW_PHASE: REVIEW_RELEASED,
        }
        for phase, capabilities in scoped.items():
            by_tool = tool_evidence(reads, phase=phase)
            assert by_tool, (phase, by_tool)
            for capability in capabilities:
                item = by_tool[TOOL_IDS[capability]]
                assert str(item["artifact_id"]).startswith("tool-result:"), (capability, item)
                assert item["content_digest"], (capability, item)
                assert item["source_origin"].startswith(f"tool:{TOOL_IDS[capability]}:"), (
                    capability,
                    item,
                )


class TestTheDownstreamPhaseConsumesIt:
    """③ **下游消费**：`review` 的两条 reader 返回内容各含 `probe` 的工具证据 id。"""

    def test_the_evidence_read_result_carries_the_upstream_evidence_ids(
        self, mock_relay: str
    ) -> None:
        """`evidence.read`（既有放行）的返回内容含上游两条工具证据 id。"""
        deps = assembled_deps(mock_relay)
        with TestClient(app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))

            upstream = upstream_evidence_ids(reads)
            downstream = tool_evidence(reads, phase=REVIEW_PHASE)[TOOL_IDS[EVIDENCE_READ]]
            payload = content_of(client, str(downstream["artifact_id"]))

        consumed = {str(item.get("id")) for item in payload.get("evidence", [])}
        assert consumed, (
            "下游 `evidence.read` 的返回内容必须非空（否则「消费」无从谈起）",
            payload,
        )
        missing = sorted(upstream - consumed)
        assert missing == [], (
            "下游 `evidence.read` 的返回内容必须含上游工具证据的 id（否则『调了但没人用』）",
            missing,
            sorted(consumed),
        )

    def test_the_claim_read_result_carries_the_upstream_evidence_ids(self, mock_relay: str) -> None:
        """**本条新放行**的 `claim.read` 的返回内容也含上游工具证据 id（第二条消费读数）。

        它读的是**本 run 的 claim 及其 relation**（`run_id` 过滤）—— probe 的工具证据挂在
        同一 run 的 claim 上 ⇒ 返回的 relations 里必然出现那两个证据 id。
        """
        deps = assembled_deps(mock_relay)
        with TestClient(app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))

            upstream = upstream_evidence_ids(reads)
            downstream = tool_evidence(reads, phase=REVIEW_PHASE)[TOOL_IDS["claim.read"]]
            payload = content_of(client, str(downstream["artifact_id"]))

        relation_ids = {
            str(relation.get("evidence_id"))
            for claim in payload.get("claims", [])
            for relation in claim.get("relations", [])
        }
        assert relation_ids, (
            "下游 `claim.read` 必须读到本 run 的 claim relation（否则「消费」无从谈起）",
            payload,
        )
        missing = sorted(upstream - relation_ids)
        assert missing == [], (
            "下游 `claim.read` 的 relations 必须含上游工具证据的 id（否则『调了但没人用』）",
            missing,
            sorted(relation_ids),
        )

    def test_the_upstream_reads_returned_real_canonical_facts(self, mock_relay: str) -> None:
        """上游读的是**真实存在的 canonical 事实**（不是空壳）：逐字段可判。

        `run.read` 读的是种进 `RunStore` 的那条 run 行（`SEEDED_RUN_ID`）—— 逐字段与
        我们写进去的事实一致；`budget.read` 读的是 canonical 预算账本快照：**本 run 的
        preflight 预留**（`scope=phase:*`）必须在场（受判面非空）。
        """
        deps = assembled_deps(mock_relay)
        with TestClient(app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))
            by_tool = tool_evidence(reads, phase=PROBE_PHASE)
            run_payload = content_of(client, str(by_tool[TOOL_IDS["run.read"]]["artifact_id"]))
            budget_payload = content_of(
                client, str(by_tool[TOOL_IDS["budget.read"]]["artifact_id"])
            )

        assert run_payload["run_id"] == SEEDED_RUN_ID, run_payload
        assert run_payload["project_id"] == "example-project", run_payload
        assert run_payload["state"] == "SUCCEEDED", run_payload
        assert run_payload["manifest_digest"], run_payload
        # 预算：本 run 的 phase 预留必须在场（「读到真东西」的判据，不是「调用成功」）。
        assert budget_payload["reservations"], (
            "budget.read 必须读到本 run 的 phase 预留（否则『读到了空账本』）",
            budget_payload,
        )
        assert all(
            str(item["scope"]).startswith("phase:") for item in budget_payload["reservations"]
        ), budget_payload


class TestAMissingImplementationIsNamed:
    """④ 反证：缺 provider 实例 ⇒ run 失败并**点名**（不得静默继续）。"""

    def test_removing_the_provider_instance_fails_and_names_it(self, mock_relay: str) -> None:
        deps = assembled_deps(mock_relay, omit_provider=True)
        with TestClient(app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))

        assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
        assert reads.failures, "失败必须带判词（点名缺的是什么）"
        joined = " ".join(reads.failures)
        assert PROVIDER in joined, ("缺实现必须**点名 provider**", reads.failures)
        assert "has no registered instance" in joined, (
            "判词必须说明是「装配里没有实例」（而不是把失败归到别处）",
            reads.failures,
        )
        capabilities = (*PROBE_RELEASED, *REVIEW_RELEASED)
        assert any(capability in joined for capability in capabilities), (
            "判词必须点名具体能力/工具（否则无法判断缺的是哪一条）",
            reads.failures,
        )
        assert [item for item in reads.evidence if item.get("tool_refs")] == [], reads.evidence


class TestAMissingGrantIsRefusedInTheRun:
    """④b 反证（EC-01(d)① 的**run 级**读数）：删掉一条放行 ⇒ run **被拒且点名**。

    与 `test_release_expansion_is_read_only.py::TestBothRefutationDirectionsBite` 的
    「删掉一条放行 ⇒ 求值回落 `default_effect`」**不是同一件事**：那条读的是求值器的
    返回值，本条读的是**一次 run 的终态与判词** —— 判据口径指名要求它在 run 里可见
    （`POLICY_DENIED` 判词逐字），而不是只在求值器上成立。

    **建档实测（写在这里，免得后来者以为读错了）**：run 级消息
    （`run.failed` / `task.failed` 的 message）**只带 finding 代号** ——
    `preflight failed: POLICY_DENIED`；**逐能力**的点名在 preflight 报告上
    （`policy denied capability budget.read: used default policy effect`，`subject_ref`
    指向该 phase）。因此本条判据**两个面都断言**：run 面判终态 + 代号逐字，preflight 面
    判能力名逐字 —— 只读 run 面会漏掉「点名了哪条能力」这一半，只读 preflight 面会漏掉
    「run 真的被拒」这一半。run 级消息**不**逐字点名能力是**产品现状**（本文只如实记录，
    不改产品、也不把断言放宽成「包含代号即可」）。
    """

    def test_removing_a_grant_stops_the_run_and_names_the_capability(self, mock_relay: str) -> None:
        deps = deps_without_grant(mock_relay, "budget.read")
        with TestClient(app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))

        assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
        joined = " ".join(reads.failures)
        assert "POLICY_DENIED" in joined, (
            "run 级判词必须逐字带 `POLICY_DENIED`（不是静默跳过那条能力）",
            reads.failures,
        )

    def test_the_preflight_face_names_the_capability_that_lost_its_grant(
        self, mock_relay: str
    ) -> None:
        """**逐能力**点名（run 级消息只带代号 ⇒ 这一半必须单独取证）。"""
        from packages.domain.protocols import PreflightFindingCode

        report = preflight_report(deps_without_grant(mock_relay, "budget.read"))
        denied = [
            finding
            for finding in report.findings
            if finding.code == PreflightFindingCode.POLICY_DENIED.value
        ]
        assert denied, ("被删放行的能力必须在 preflight 报告里判 `POLICY_DENIED`", report.findings)
        messages = [finding.message for finding in denied]
        assert any("budget.read" in message for message in messages), (
            "preflight 判词必须**逐字点名**被拒的能力",
            messages,
        )
        assert report.status.value == "FAIL", report.status

    def test_the_granted_run_is_not_failing_for_this_reason(self, mock_relay: str) -> None:
        """反面对照：不裁剪放行时**同一读数**里没有 `POLICY_DENIED`（本条判据不空转）。"""
        deps = assembled_deps(mock_relay)
        with TestClient(app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))

        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        assert "POLICY_DENIED" not in " ".join(reads.failures), reads.failures

    def test_the_same_report_passes_when_the_grant_is_present(self, mock_relay: str) -> None:
        """反面对照（preflight 面）：放行在场时同一读数判绿且无 `POLICY_DENIED`。"""
        report = preflight_report(assembled_deps(mock_relay))
        assert report.passed, report.status
        assert "POLICY_DENIED" not in {finding.code for finding in report.findings}, [
            (finding.code, finding.message) for finding in report.findings
        ]


class TestTheJudgeItselfBites:
    """⑤ 判据自检：受判面非空 + 本判据真的咬得住（承 MEM-156 / MEM-159）。"""

    def test_the_declared_call_set_covers_the_newly_granted_capabilities(self) -> None:
        """受判面的**前提**：判据写死的三条与装配声明**逐字一致**（否则在空集上恒真）。"""
        declared_calls = calls()
        declared = {call.capability for call in declared_calls}
        for capability in (*PROBE_RELEASED, *REVIEW_RELEASED):
            assert capability in declared, (capability, sorted(declared))
        assert TOOL_IDS["run.read"] in {call.tool_id for call in declared_calls}, declared_calls

    def test_omitting_one_capability_is_detectable(self) -> None:
        """反向：少一条能力的证据 ⇒ 「逐条在场」断言能抓到它。"""
        by_tool: dict[str, dict[str, Any]] = {
            TOOL_IDS["run.read"]: {},
            TOOL_IDS["budget.read"]: {},
        }
        missing = [
            capability for capability in REVIEW_RELEASED if TOOL_IDS[capability] not in by_tool
        ]
        assert missing == ["claim.read"], missing

    def test_the_protocol_declares_the_newly_granted_capabilities(self) -> None:
        """受判面非空：**协议文档本身**必须声明那三条能力 + `run_chain`（不靠代码转述）。"""
        from pathlib import Path

        import yaml

        raw = yaml.safe_load(Path(f"examples/protocols/{_PROTOCOL}").read_text(encoding="utf-8"))
        phases = {phase["id"]: phase for phase in raw["phases"]}
        assert set(phases) == {PROBE_PHASE, REVIEW_PHASE}, sorted(phases)
        probe = phases[PROBE_PHASE]
        assert probe.get("capability_execution") == "run_chain", probe
        assert set(probe["required_capabilities"]) == set(PROBE_RELEASED), probe[
            "required_capabilities"
        ]
        review = phases[REVIEW_PHASE]
        assert review.get("capability_execution") == "run_chain", review
        assert set(review["required_capabilities"]) == {
            *REVIEW_RELEASED,
            EVIDENCE_READ,
        }, review["required_capabilities"]

    def test_the_protocol_capabilities_are_exactly_the_granted_ones(self) -> None:
        """三条能力在**真实策略面**上都是 `ALLOW`（放行是本判据的前提，不是巧合）。"""
        from packages.application.policy.native import NativePolicyEvaluator
        from packages.application.ports.policy_evaluator import PolicyRequest
        from packages.application.preflight.policy_check import policy_scope_for
        from packages.domain.enums import PolicyDecision
        from services.api.catalog import load_policy_definition

        policy = load_policy_definition()
        assert policy is not None
        evaluator = NativePolicyEvaluator(policy)
        for capability in (*PROBE_RELEASED, *REVIEW_RELEASED):
            outcome = evaluator.evaluate(
                PolicyRequest(
                    actor="goal031:run-check",
                    capability=capability,
                    action="execute",
                    scope=policy_scope_for(capability),
                    resource=capability,
                )
            )
            assert outcome.decision is PolicyDecision.ALLOW, (capability, outcome)
            assert outcome.reason == "matched allow rule", (capability, outcome.reason)
