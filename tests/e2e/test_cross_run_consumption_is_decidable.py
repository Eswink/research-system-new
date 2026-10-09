"""GOAL-20261008-038 EC-04 判据：**跨轮消费可判定**（两轮实跑 + 两向反证）。

靶子（EC-04 (a)(b)(c)）：程序跑**两轮 run**，第 2 轮交付物**声明并真的携带**第 1 轮落库的结论 ——

- 第 1 轮：结构上**没有前序 run** ⇒ `CUSTOM_EVALUATOR` 判**不适用**（判过 + 点名理由，
  与「有前序但未携带」严格区分；判成判负会让每个程序的第一轮必然失败）；
- 第 2 轮：`meta_review.prior_verdict`（合约用 `metric` 声明的路径）与第 1 轮落库的判决值
  **逐字一致** ⇒ 判过，判词**点名来源 run id 与逐字值**。

三态逐条（全部读**既有读面** `GET /runs/{id}/reviews`，不经内部对象）：

1. **消费成立**：第 2 轮的判词里出现「与前序结论逐字一致」，且**来源 run id = 第 1 轮**、
   逐字值 = 第 1 轮的落库判决值。
2. **反证①（未携带）**：第 2 轮产物**带的是另一个值** ⇒ 判负且**两侧值都点名**。
3. **反证②（路径缺失）**：声明路径在本轮产物里**不存在** ⇒ 求值器**点名**（配置错误形态）。

**如实边界**（本文件不声称已解决）：判据只证「本轮产物**携带**了前序结论且与来源逐字一致」；
**未**证「因为读了它才这么写」（因果不可判 —— 那是过程面事实，已登记为本 GOAL 的残余）。

**两形态显式声明（GOAL-20261009-041 纪律回溯修复）**：`_two_rounds` 只服务**成功面**
（断言**恰好两轮** `[1, 2]`）；`_failing_round` 只服务**失败面**（断言**恰好一轮** `[1]`
且第 2 次推进落 `STOP_RUN_FAILED`）。两个助手各自**断言自己那一面**，调用方按它要观测的
形态择优 —— **不存在**「至少一轮」式的容错回退。
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.e2e.cross_run_support import PROTOCOL, cross_run_deps
from tests.e2e.program_advance_support import advance, create_program, read_program

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

_ACCEPT_LINE = "与前序结论逐字一致"
_MISMATCH_LINE = "不一致"
_MISSING_PATH_LINE = "在本轮产物里缺失"


def _custom_lines(client: TestClient, run_id: str) -> list[str]:
    """该 run 的验收结论里 `CUSTOM_EVALUATOR` 那一条的判词（经既有读面取）。"""
    reviews = client.get(f"/runs/{run_id}/reviews").json()
    lines = [
        str(line)
        for row in reviews
        for line in row.get("findings", [])
        if "CUSTOM_EVALUATOR" in str(line)
    ]
    assert len(lines) == 1, ("本轮应当恰有一条该判据的判词", run_id, lines)
    return lines


def _two_rounds(deps: Any) -> tuple[TestClient, str, str, str]:
    """建程序 + 推进两次；返回 `(client, 第 1 轮 run id, 第 2 轮 run id, 第 1 轮判词)`。

    **断言形态是「恰好两轮」**（`program_index == [1, 2]`）：本助手只服务**成功面**的
    用例（两轮都跑成、判据在第 2 轮被判定）。**不断言两轮都 SUCCEEDED**：反证臂里
    第 2 轮会因为消费不成立而被门判拒 —— 那正是要观测的形态（判据读的是**判词**，
    不是终态）。**失败面**（第 1 轮就 FAILED ⇒ 程序按失败面判停、**没有**第 2 轮）
    由 `_failing_round` 服务，两形态由调用方**显式声明**，不存在容错回退。
    """
    client = TestClient(create_app(deps)).__enter__()
    program = create_program(client, max_runs=3, protocol=PROTOCOL)
    program_id = str(program["id"])
    advance(client, program_id)
    advance(client, program_id)
    runs = read_program(client, program_id)["runs"]
    indices = [row["program_index"] for row in runs]
    assert indices == [1, 2], ("成功面必须是**恰好两轮**（失败轮会按失败面判停）", indices)
    first, second = str(runs[0]["run_id"]), str(runs[1]["run_id"])
    return client, first, second, _custom_lines(client, first)[0]


def _failing_round(deps: Any) -> tuple[TestClient, str, str]:
    """建程序 + 推进两次；返回 `(client, 第 1 轮 run id, 第 1 轮判词)`。

    **断言形态是「恰好一轮」**：第 1 轮以 `FAILED` 收敛 ⇒ 第 2 次推进走**失败面**
    （`STOP_RUN_FAILED`，缺省不重试）⇒ **没有**第 2 轮。这一形态不是「容忍只有一轮」，
    而是**被断言的受判形态**：多出第 2 轮即判红（那正是 GOAL-040 消灭的失真行为）。
    """
    client = TestClient(create_app(deps)).__enter__()
    program = create_program(client, max_runs=3, protocol=PROTOCOL)
    program_id = str(program["id"])
    advance(client, program_id)
    second = advance(client, program_id)
    runs = read_program(client, program_id)["runs"]
    indices = [row["program_index"] for row in runs]
    assert indices == [1], ("失败面必须是**恰好一轮**（失败停不产生第 2 轮）", indices)
    assert runs[0]["state"] == "FAILED", runs
    assert second["decision"]["kind"] == "STOP_RUN_FAILED", second["decision"]
    return client, str(runs[0]["run_id"]), _custom_lines(client, str(runs[0]["run_id"]))[0]


def test_the_second_rounds_consumption_is_decided_with_the_source_named() -> None:
    """主路：第 2 轮判词 = 消费成立，且**来源 run id = 第 1 轮**、逐字值在场。"""
    client, first, second, _first_line = _two_rounds(cross_run_deps())
    try:
        line = _custom_lines(client, second)[0]
        assert _ACCEPT_LINE in line, line
        assert first in line, ("判词必须点名**来源** run id（可复核性）", line)
        assert "PASS" in line, ("逐字值必须在判词里", line)
    finally:
        client.__exit__(None, None, None)


def test_the_first_round_marks_the_criterion_as_not_applicable_not_failed() -> None:
    """第 1 轮：**结构上无前序** ⇒ 判据不适用（判过 + 点名理由），不是判负。"""
    client, _first, _second, first_line = _two_rounds(cross_run_deps())
    try:
        assert "不适用" in first_line, first_line
        assert "没有前序 run" in first_line, first_line
    finally:
        client.__exit__(None, None, None)


def test_a_mismatching_value_is_rejected_with_both_values_named() -> None:
    """反证①：第 2 轮带的是**另一个值** ⇒ 判负且**两侧值都点名**（门因此判 REJECT）。"""
    from tests.e2e.cross_run_support import CONSUME_CONTRACT

    deps = cross_run_deps()
    # 受控执行体改成携带一个**不是**第 1 轮判决值的值（其余同）。
    deps.runs = _runtime_carrying(deps, CONSUME_CONTRACT, {"prior_verdict": "REVISE"})
    client, first, second, first_line = _two_rounds(deps)
    try:
        line = _custom_lines(client, second)[0]
        assert _MISMATCH_LINE in line, line
        assert "'REVISE'" in line and "'PASS'" in line, ("两侧值都要点名", line)
        assert first in line, ("来源 run id 仍要点名", line)
        assert "不适用" in first_line, "第 1 轮不受本轮产物改动影响（它结构上无前序）"
    finally:
        client.__exit__(None, None, None)


def test_a_missing_declared_path_is_named_as_a_configuration_error() -> None:
    """反证②：声明路径在产物里**不存在** ⇒ **点名**（配置错误形态，不是静默判负）。

    **受判面收窄 + 理由（GOAL-20261009-041 纪律回溯修复，如实登记）**：本用例原先在
    **第 2** 轮取判词 —— 那依赖**旧代码的失真行为**（第 1 轮 FAILED 仍被判「续」⇒
    才有第 2 轮）。旧树实测：第 1 轮与第 2 轮的判词**逐字相同**（同一条配置错误判定被
    跑了两遍），所以原形态的**额外**信息量 = 「该判定在第 2 轮也会报」；
    而**这条判定本来就发生在第 1 轮**（它的产物里就没有那条路径）。
    现在：受判轮次 **2 → 1**（观测宽度收窄），谓词（点名配置错误 + 点名路径名）
    逐字保持；**并且**该形态被断言为「恰好一轮 ⇒ 失败面判停」（多出第 2 轮即判红）。
    """
    from tests.e2e.cross_run_support import CONSUME_CONTRACT

    deps = cross_run_deps()
    deps.runs = _runtime_carrying(deps, CONSUME_CONTRACT, {})
    client, _first, line = _failing_round(deps)
    try:
        assert _MISSING_PATH_LINE in line, line
        assert "meta_review.prior_verdict" in line, ("路径名要点名", line)
    finally:
        client.__exit__(None, None, None)


def _runtime_carrying(deps: Any, contract: str, meta_review: dict[str, object]) -> Any:
    """把受控执行体的 `consume` 交付物换成给定的 `meta_review`（其余走原装配）。"""
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from tests.e2e.cross_run_support import CONSUME_OUTPUT
    from tests.e2e.program_advance_support import PASS_OUTPUT, PRODUCE_CONTRACT
    from tests.e2e.scenario import StructuredOutputAgentRuntime

    inner = deps.runs._deps
    runtime = StructuredOutputAgentRuntime(
        outputs_by_contract={
            PRODUCE_CONTRACT: PASS_OUTPUT,
            contract: {"meta_review": {"covers": CONSUME_OUTPUT["meta_review"], **meta_review}},
        }
    )
    return RunOrchestrationService(replace(inner, runtime=runtime))
