"""GOAL-20261008-037 EC-03 判据：**跨 run 知识累积** —— 后一轮读到前一轮落库的结论。

靶子（EC-03 (a)(b)(c)(d)）：程序内跑**两轮 run**，第 2 轮经**能力面**（`research_state.read`）
读第 1 轮的落库判词：

1. **真被调用**：第 2 轮的证据链里 `tool_refs` 逐条点名 `("m12_artifact",
   "research_state_read")`（第 1 轮**没有**这条 —— 那时还没有前序 run，能力步在同 run 内
   读的是「前序 run」，第 1 轮构造性地是空集）。
2. **下游消费**（核心）：第 2 轮工具结果的**内容**里出现**第 1 轮**那一条落库判词的
   **逐字**行（`verdict PASS`；按 **run id 归属**区分两轮 —— 不靠顺序猜）。
3. **入口是程序归属**：读结果的 `program_id` == 程序 id、`prior_runs[0].run_id` == 第 1 轮 run id。
4. **反证①**：撤掉 provider 实例 ⇒ 那一轮**恰好一轮**并以 `FAILED` 收敛（程序按失败面
   判停、`STOP_RUN_FAILED`），且判词**点名** provider / 能力 / 工具。
5. **反证②**：把 `research_state.read` 从 `allow` 删掉（内存内副本）⇒ 点名 `POLICY_DENIED`。

**如实边界**（本文件不声称已解决）：读到的结论**影响**了第 2 轮的科学结论**不在范围**
（验收门只判交付物存在）；memory 的跨 run 维度（决策 ④）与跨程序共享**不在本轮**。
**形状显式声明（GOAL-20261009-041）**：成功面助手断言**恰好两轮**；反证①断言
**恰好一轮 + 失败面判停** —— 两形态各自被断言，没有容错回退。
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from packages.domain.core import ID
from services.api.app import create_app
from tests.e2e.cross_run_support import (
    CAPABILITY,
    CONSUME_CONTRACT,
    CONSUME_OUTPUT,
    PROTOCOL,
    PROVIDER,
    TOOL_ID,
    cross_run_deps,
    run_ids_of,
    tool_evidence_of_run,
)
from tests.e2e.program_advance_support import advance, create_program, read_program

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


def _two_round_program(deps: Any) -> tuple[TestClient, str]:
    """建程序 + 推进两次（第 2 轮由第 1 轮的落库判词驱动）。

    **断言形态是「恰好两轮」**：本助手只服务**成功面**的用例（后一轮读前一轮的结论）。
    第 1 轮若以 `FAILED` 收敛 ⇒ 程序按**失败面**判停、没有第 2 轮 ⇒ 这里直接判红
    （失败面由 `test_missing_provider_is_named_not_silent` 与
    `test_program_stop_reasons_are_decidable.py` 覆盖，不用本助手）。
    """
    client = TestClient(create_app(deps)).__enter__()
    program = create_program(client, max_runs=3, protocol=PROTOCOL, continue_on=["PASS"])
    program_id = str(program["id"])
    advance(client, program_id)
    second = advance(client, program_id)
    assert second["started_run_id"], second
    detail = read_program(client, program_id)
    indices = [row["program_index"] for row in detail["runs"]]
    assert indices == [1, 2], ("成功面必须是**恰好两轮**（失败轮会按失败面判停）", indices)
    return client, program_id


def _tool_payload(client: TestClient, run_id: str) -> dict[str, Any]:
    """第 2 轮那次工具调用的**结果内容**（经既有制品读面，不经内部对象）。"""
    rows = tool_evidence_of_run(client, run_id)
    assert len(rows) == 1, ("本轮应当恰有一条该工具的证据", rows)
    artifact_id = str(rows[0]["artifact_id"])
    response = client.get(f"/artifacts/{artifact_id}/content")
    assert response.status_code == 200, (artifact_id, response.text[:200])
    return dict(json.loads(response.content.decode("utf-8")))


def test_the_second_round_reads_the_first_rounds_recorded_verdicts() -> None:
    """主路：第 2 轮经能力面读到第 1 轮的落库结论（逐字 + 归属可复核）。"""
    client, program_id = _two_round_program(cross_run_deps())
    try:
        first, second = run_ids_of(client, program_id)
        payload = _tool_payload(client, second)
        assert payload["program_id"] == program_id
        assert payload["run_id"] == second
        prior = payload["prior_runs"]
        assert [row["run_id"] for row in prior] == [first], prior
        assert prior[0]["program_index"] == 1
        assert prior[0]["state"] == "SUCCEEDED"
        assert "PASS" in prior[0]["verdicts"], (
            "第 1 轮落库的**判决值**必须逐字出现在第 2 轮读到的东西里"
            "（与 `review.read` 同一取值口径：`ReviewFinding.verdict`）",
            prior,
        )
        assert prior[0]["reviewed_by"] == "gate:reviewer_a", prior
        assert prior[0]["manifest_digest"], "前序 run 的冻结事实应当同批可见"
    finally:
        client.__exit__(None, None, None)


def test_the_evidence_chain_names_the_tool_and_the_two_rounds_are_distinguishable() -> None:
    """工具证据逐条点名 provider / 工具；第 1 轮的读结果是**构造性空集**。"""
    client, program_id = _two_round_program(cross_run_deps())
    try:
        first, second = run_ids_of(client, program_id)
        first_rows = tool_evidence_of_run(client, first)
        second_rows = tool_evidence_of_run(client, second)
        assert first_rows and second_rows, ("两轮都应留下该工具的调用证据", first_rows, second_rows)
        assert first_rows[0]["tool_refs"] == [PROVIDER, TOOL_ID]
        assert second_rows[0]["tool_refs"] == [PROVIDER, TOOL_ID]
        assert first_rows[0]["artifact_id"] != second_rows[0]["artifact_id"], (
            "两轮的读结果必须落在**不同**的内容寻址制品上（否则分不清读的是哪一轮）",
        )
        # 第 1 轮构造性地没有前序 run：读结果如实给 0（不是「读不到」）。
        first_payload = _tool_payload(client, first)
        assert first_payload["prior_run_count"] == 0, first_payload
        assert first_payload["prior_runs"] == [], first_payload
    finally:
        client.__exit__(None, None, None)


def test_missing_provider_is_named_not_silent() -> None:
    """反证①：撤掉 provider 实例 ⇒ run 失败且判词点名 provider / 能力 / 工具。

    **受判面收窄 + 理由（GOAL-20261009-041 纪律回溯修复，如实登记）**：本用例原先取**第 2**
    轮那条 run —— 那依赖**旧代码的失真行为**（第 1 轮 FAILED 仍被判「续」⇒ 才有第 2 轮）。
    旧树实测：第 1 轮与第 2 轮的 `run.failed` 正文**逐字相同**（同一条缺 provider 的失败被
    跑了两遍），所以原形态的**额外**信息量 = 「同样的失败在第 2 轮也会报」；
    而这条失败**本来就发生在第 1 轮**里（`consume` 的执行期）。
    现在：受判轮次 **2 → 1**（观测宽度收窄），谓词（点名 provider / 工具 / 能力 +
    必须收敛到 FAILED）逐字保持；**并且**该形态被断言为「**恰好一轮** ⇒ 失败面判停」
    （多出第 2 轮即判红 —— 那正是 GOAL-040 消灭的失真行为）。
    """
    deps = cross_run_deps(omit_provider_capability=True)
    with TestClient(create_app(deps)) as client:
        program = create_program(client, max_runs=3, protocol=PROTOCOL)
        program_id = str(program["id"])
        first = advance(client, program_id)
        run_id = str(first["started_run_id"])
        assert run_id, first
        after = advance(client, program_id)
        assert after["started_run_id"] is None, after
        assert after["decision"]["kind"] == "STOP_RUN_FAILED", after["decision"]
        runs = read_program(client, program_id)["runs"]
        assert [row["program_index"] for row in runs] == [1], (
            "失败面必须是**恰好一轮**（失败停不产生第 2 轮）",
            runs,
        )
        assert runs[0]["state"] == "FAILED", runs
        failed = [
            event
            for event in client.get(f"/runs/{run_id}/events").json()
            if str(event.get("type")) == "run.failed"
        ]
        assert failed, "缺 provider 的 run 必须收敛到 FAILED"
        message = json.dumps(failed[-1], ensure_ascii=False)
        assert PROVIDER in message and TOOL_ID in message and CAPABILITY in message, message


def test_without_grant_the_capability_is_denied_at_preflight_by_name() -> None:
    """反证②：删掉该能力的 `allow`（内存内副本）⇒ **点名该能力**的 `POLICY_DENIED`。

    与 GOAL-036 EC-03 的反证②同一形态：策略面在 **preflight** 就判（那条 finding 就是
    该能力），run 因此不会进入 RUNNING —— 这正是「未放行不得执行」的取证点。
    """
    from adapters.contracts.protocol_loaders import load_protocol
    from packages.application.preflight.preflight import compile_and_preflight
    from services.api.run_execution import ExecutionRequest, execution_inputs

    deps = cross_run_deps(without_grant=True)
    # 应用**在装**（preflight 用 deps 的目录 / 策略面），客户端本身不再使用。
    with TestClient(create_app(deps)):
        inputs = execution_inputs(
            ExecutionRequest(
                deps=deps,
                protocol_path=PROTOCOL,
                run_id=ID("0d031100-0000-4000-8000-0000000000fe"),
                trace_id=None,
                draft_ref=None,
                project_id="example-project",
            )
        )
        protocol = load_protocol(f"examples/protocols/{PROTOCOL}")
        _plan, report = compile_and_preflight(
            protocol, inputs.catalog, inputs.project, inputs.preflight
        )
        assert report.status.value == "FAIL", report.status
        rendered = json.dumps(
            [(finding.code, finding.message, finding.subject_ref) for finding in report.findings],
            ensure_ascii=False,
        )
        assert "POLICY_DENIED" in rendered, rendered
        assert CAPABILITY in rendered, rendered
        assert report.passed is False


def test_the_read_result_is_content_addressed_and_retrievable() -> None:
    """产出可复核：工具结果落在内容寻址制品上，digest 在场（不是只在内存里）。"""
    client, program_id = _two_round_program(cross_run_deps())
    try:
        _first, second = run_ids_of(client, program_id)
        rows = tool_evidence_of_run(client, second)
        artifact_id = str(rows[0]["artifact_id"])
        artifacts = client.get(f"/runs/{second}/artifacts").json()
        matching = [row for row in artifacts if str(row["id"]) == artifact_id]
        assert matching, ("工具结果制品必须在 run 的制品列表里", artifact_id)
        assert matching[0]["digest"], "内容寻址 digest 必须在场"
    finally:
        client.__exit__(None, None, None)


def test_the_protocol_declares_the_contract_it_actually_uses() -> None:
    """一致性：本轮的 `consume` 合约与 GOAL-036 那份**不同名**（交付物可区分）。"""
    assert CONSUME_CONTRACT != "review_consumption_deliverable"
    assert CONSUME_OUTPUT
