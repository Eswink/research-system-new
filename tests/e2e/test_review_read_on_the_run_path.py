"""GOAL-20261008-036 EC-03 判据：**本 run 的后续 phase 经能力面读到已落库的评审结论**。

靶子（EC-03 (a)(b)(c)(d)）：`review_consumption_v1.yaml` 的两个 phase 都由**运行链**执行 ——

- `produce` 交付 `review_decision` ⇒ 验收门在**求值点**把逐条判词落库
  （GOAL-035 EC-01 的 `ReviewFindingStore`）；
- `consume` 声明的 `review.read` **确定性执行**（`RunChainCall`，`run_id_argument=True`）
  ⇒ 它读到的是**本 run 自己**的落库结论。

**下游消费**（本判据的核心，承 GOAL-031 EC-01(e) 的口径）：工具结果的**内容**里出现
`produce` 那一条落库结论的**逐字判词行**。它与「两个 phase 都调了工具」**不是同一件事** ——
后者只证明调了两遍。

三态逐条取证（全部读**既有读面**，不经内部对象）：

1. **真被调用**：`tool_refs` 逐条点名 `("m12_artifact", "review_read")`，且这条证据属于
   `consume` 任务（按交付物制品名判 phase —— 单键索引会后写覆盖前写，GOAL-030 实测过）。
2. **产出可复核**：工具结果落在 `tool-result:` 命名的内容寻址制品上，`/artifacts/{id}/content`
   读面取得到（digest 在场）。
3. **下游消费**：读到的逐条判词与 `GET /runs/{id}/reviews` 读出的**同一批判词**逐字一致
   （含 `ARTIFACT_EXISTS:` 与 `REVIEW_SCORE: review score 0.95 GTE 0.8`）。
4. **反证两向**：① 撤掉 provider 实例 ⇒ run 失败且判词**点名** provider / 能力 / 工具；
   ② 把 `review.read` 从 `allow` 删掉（内存内副本）⇒ run 失败且点名 `POLICY_DENIED`，
   且 preflight 报告里那条 finding 就是该能力。
5. **实跑终态**：跑到 `SUCCEEDED`，且 `manifest_digest` 在场（冻结真的发生）。

**如实边界**（本文件不声称已解决）：读到的评审结论**内容正确**不在范围（那是评审者的事）；
**多评审者聚合**（GOAL-035 的 `N-3`）仍未收口 —— 本轮只让结论**可读且被读到**；
读结果是否影响了 `meta_review` 的**科学结论**不由本判据把守（验收门只判它存在）。
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.e2e.live_run_support import start_run
from tests.e2e.review_read_support import (
    CAPABILITY,
    CONSUME_PHASE,
    PRODUCE_PHASE,
    PROTOCOL,
    PROVIDER,
    TOOL_ID,
    ChainReads,
    assembled_deps,
    deps_without_grant,
    phase_of_task,
    preflight_report,
    read_chain,
    tool_evidence,
)

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


def _run(deps: Any) -> ChainReads:
    """跑一次 run 并取读面事实（失败消息也在内）。"""
    with TestClient(create_app(deps)) as client:
        return read_chain(client, start_run(client, PROTOCOL))


def _content_of(client: TestClient, artifact_id: str) -> dict[str, Any]:
    """按 artifact id 取**内容**并解析成 JSON 对象（经既有读面，不经内部对象）。"""
    response = client.get(f"/artifacts/{artifact_id}/content")
    assert response.status_code == 200, (artifact_id, response.status_code, response.text[:200])
    parsed = json.loads(response.content.decode("utf-8"))
    assert isinstance(parsed, dict), ("工具结果内容必须是 JSON 对象", artifact_id, type(parsed))
    return parsed


def _recorded_lines(read: ChainReads) -> list[str]:
    """**`produce` 那一条**落库结论的逐字判词（经读面取，按任务归属选，不靠顺序猜）。

    两个 phase 的验收门**都**落库结论 ⇒ 「只有一条」是错的读法；按 `phase_of_task`
    的交付物制品名把 `produce` 任务挑出来。
    """
    produce_tasks = [
        task_id for task_id, phase in phase_of_task(read).items() if phase == PRODUCE_PHASE
    ]
    assert len(produce_tasks) == 1, (produce_tasks, read.reviews)
    matching = [item for item in read.reviews if item.get("task_id") == produce_tasks[0]]
    assert len(matching) == 1, (produce_tasks, read.reviews)
    findings = [str(line) for line in matching[0]["findings"]]
    assert findings, matching[0]
    return findings


class TestTheConsumingPhaseReallyReadsTheRecordedFindings:
    """① 主判据：调用证据 + 内容寻址 + **下游消费**（逐字判词）。"""

    def test_the_run_succeeds_and_is_frozen(self) -> None:
        reads = _run(assembled_deps())
        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.reviews)
        assert reads.run["manifest_digest"], reads.run

    def test_the_capability_leaves_a_call_evidence_in_the_consuming_phase(self) -> None:
        reads = _run(assembled_deps())
        consume_tools = tool_evidence(reads, phase=CONSUME_PHASE)
        assert TOOL_ID in consume_tools, (
            "consume 声明的 review.read 必须有调用证据（缺哪条点名哪条）",
            sorted(consume_tools),
            PRODUCE_PHASE,
            sorted(tool_evidence(reads, phase=PRODUCE_PHASE)),
        )
        item = consume_tools[TOOL_ID]
        assert str(item["artifact_id"]).startswith("tool-result:"), item
        assert item["content_digest"], item
        assert str(item["source_origin"]).startswith(f"tool:{TOOL_ID}:"), item
        assert item["tool_refs"] == [PROVIDER, TOOL_ID], item

    def test_the_read_result_carries_the_verbatim_recorded_verdicts(self) -> None:
        """**下游消费**：工具结果内容含 `produce` 落库的**逐字**判词（不是「调了两遍工具」）。"""
        with TestClient(create_app(assembled_deps())) as client:
            reads = read_chain(client, start_run(client, PROTOCOL))
            item = tool_evidence(reads, phase=CONSUME_PHASE)[TOOL_ID]
            content = _content_of(client, str(item["artifact_id"]))

        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.reviews)
        recorded = _recorded_lines(reads)
        assert any("REVIEW_SCORE: review score 0.95 GTE 0.8" in line for line in recorded), recorded
        returned = [item for item in content.get("reviews", []) if isinstance(item, dict)]
        assert returned, ("工具结果必须带逐条判词（否则下游消费判据在空集上恒真）", content)
        produce_tasks = [
            task_id for task_id, phase in phase_of_task(reads).items() if phase == PRODUCE_PHASE
        ]
        assert len(produce_tasks) == 1, (produce_tasks, content)
        matching = [item for item in returned if item.get("task_id") == produce_tasks[0]]
        assert len(matching) == 1, (produce_tasks, returned)
        read_back = [str(line) for line in matching[0].get("verdicts", [])]
        for line in recorded:
            assert line in read_back, ("读到的判词必须与落库的逐字一致", line, read_back)
        assert content.get("count") == len(returned), content


class TestTheRefutationsBite:
    """② 两向反证（缺实现 / 未放行）—— 两向都必须**点名**，不是静默跳过。"""

    def test_a_missing_provider_is_named(self) -> None:
        """反证①：调用声明照旧，装配不给 provider 实例 ⇒ 失败并点名 provider 与工具 id。"""
        reads = _run(assembled_deps(omit_provider=True))
        assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
        joined = " ".join(reads.failures)
        assert PROVIDER in joined and TOOL_ID in joined, (
            "失败必须点名 provider 与工具 id",
            reads.failures,
        )
        assert not tool_evidence(reads, phase=CONSUME_PHASE), (
            "反证臂不得留下调用证据（否则「没实现」也能假绿）",
            sorted(tool_evidence(reads, phase=CONSUME_PHASE)),
        )

    def test_a_removed_grant_is_named(self) -> None:
        """反证②：把 `review.read` 从 `allow` 删掉（内存内副本）⇒ 点名 `POLICY_DENIED`。"""
        with TestClient(create_app(deps_without_grant())) as client:
            reads = read_chain(client, start_run(client, PROTOCOL))
        assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
        joined = " ".join(reads.failures)
        assert "POLICY_DENIED" in joined, (
            "run 级判词必须逐字带 `POLICY_DENIED`（不是静默跳过那条能力）",
            reads.failures,
        )
        # **如实边界**：run 级那一行只带**代码**（`preflight failed: POLICY_DENIED`），
        # 逐能力点名在**报告**里（下一条测试读它）—— 这是产品既有形态，本轮不改它。

    def test_the_preflight_report_names_the_denied_capability(self) -> None:
        """反证②的**逐能力**面：preflight 报告里那条 finding 就是该能力（不是笼统拒绝）。"""
        report = preflight_report(deps_without_grant())
        denied = [
            finding
            for finding in report.findings
            if finding.code == "POLICY_DENIED" and CAPABILITY in finding.message
        ]
        assert denied, ("被删放行的能力必须在 preflight 报告里判 `POLICY_DENIED`", report.findings)
