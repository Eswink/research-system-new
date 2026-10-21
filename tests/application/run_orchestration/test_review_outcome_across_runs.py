"""GOAL-20261022-093 判据（二）：**跨 run 端到端** —— 真程序两轮，第二轮读到第一轮的面板。

**它补哪一格**（EC-04）：`test_review_outcome_in_prompt.py` 证的是「读取层 + 渲染器 +
第一轮零回归」；本条证**程序归属那条链**真的把两轮连起来 —— 第二轮的 `run_id` 经
`program_id` 反查到第一轮（**不是**靠数组位置猜、也不是本 run 自己）。

**为什么单列**：判据文件受 450 行硬上限（`tests/**` 同样算），而程序面的装配比纯视图的
长一倍；共享夹具在 `review_outcome_support.py`。

**如实边界**：本文件不声称「模型据此改了」—— 那是 live 判据 + 人评。它判的是
「上一轮被判成什么」在**第二轮开工前**经产品闭包读得到、且**恰指向前一轮**。
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from packages.application.run_orchestration.retrieval_prompt import (
    REVIEW_OUTCOME_SECTION_TITLE,
    compose_prompt,
)
from services.api.app import create_app
from tests.application.run_orchestration.review_outcome_support import (
    GLM,
    KIMI,
    product_read,
    splitting,
    write_findings,
)

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


def _wire_program(deps: Any, store: Any) -> None:
    """把产品闭包装进**程序面**装配（跨 run 那条链用它）。"""
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.review_outcome_support import review_outcome_builder

    inner = deps.runs._deps
    ports = {"runs_store": deps.runs_store, "review_findings": store}
    deps.runs = RunOrchestrationService(
        replace(inner, review_outcome=review_outcome_builder(ports))
    )


def _advance_twice(deps: Any) -> tuple[Any, str, str, Any]:
    """建程序 → 推进两次；返回 `(client, 第一轮 id, 第二轮 id, store)`（调用方负责关闭）。"""
    from tests.e2e.cross_run_support import (
        PROTOCOL as CROSS_PROTOCOL,
    )
    from tests.e2e.cross_run_support import (
        run_ids_of,
    )
    from tests.e2e.program_advance_support import advance, create_program

    store = deps.review_findings
    assert store is not None, "本装配必须带 review_findings（判词要落库才读得到）"
    _wire_program(deps, store)
    client = TestClient(create_app(deps)).__enter__()
    program = create_program(client, max_runs=3, protocol=CROSS_PROTOCOL)
    first = advance(client, str(program["id"]))
    assert first["started_run_id"] is not None, first
    run_ids = run_ids_of(client, str(program["id"]))
    assert run_ids, run_ids
    first_run_id = run_ids[0]
    write_findings(store, first_run_id, splitting())
    second = advance(client, str(program["id"]))
    assert second["started_run_id"] is not None, second
    second_run_id = str(second["started_run_id"])
    assert second_run_id != first_run_id, "第二轮必须是另一个 run"
    return client, first_run_id, second_run_id, store


def test_a_two_round_program_carries_the_first_rounds_panel_to_the_second() -> None:
    """(EC-04) 真程序两轮：第二轮的前序**恰是第一轮**，且第一轮的分歧可读。"""
    from tests.e2e.cross_run_support import cross_run_deps

    deps = cross_run_deps()
    client, first_run_id, second_run_id, _store = _advance_twice(deps)
    try:
        view = product_read(deps, second_run_id)
    finally:
        client.__exit__(None, None, None)

    assert view.prior_run_id == first_run_id, (
        f"第二轮的前序必须是第一轮（读到 {view.prior_run_id}）"
    )
    # 真实 run 自己也有验收门判词 ⇒ 断言「注入的那两票在里面」，不断言总数。
    assert view.voters >= 2, view.votes
    assert "REJECT" in {entry.verdict for entry in view.dissent}, view.dissent
    assert {GLM, KIMI} <= set(view.targets), view.targets
    assert REVIEW_OUTCOME_SECTION_TITLE in compose_prompt("PURPOSE", review_outcome=view)


def test_a_prior_rounds_unattributable_findings_are_named_not_faked() -> None:
    """(EC-03 跨 run 面) 第一轮只落了**不可归因**的判词 ⇒ 点名那一轮，**不**伪造结论。

    与上一条只差「第一轮的判词有没有 `reviewer_model`」⇒ 读数必须变。做法是给第一轮
    **再补一条无模型的判词**并把可归因的那两条挪走 —— 挪不动（store 只追加），因此改为
    在**读取入口**上取证：同一组记录，去掉 `reviewer_model` 就是「读不到可归因判词」。
    这条链的两个端点（`for_program` 取前序 / `for_run` 取判词）与上一条**同源**。
    """
    from packages.application.run_orchestration.review_outcome import build_review_outcome
    from tests.e2e.cross_run_support import cross_run_deps

    deps = cross_run_deps()
    store = deps.review_findings
    assert store is not None
    client, first_run_id, second_run_id, _ = _advance_twice(deps)
    try:
        # 一个**只**把第一轮判词改成「无模型」的读取面（包装同一 store，不改产品）。
        class _Stripped:
            def for_run(self, run_id: str) -> tuple[Any, ...]:
                from dataclasses import replace as _replace

                return tuple(
                    _replace(item, finding=_replace(item.finding, reviewer_model=None))
                    for item in store.for_run(run_id)
                )

        view = build_review_outcome(deps.runs_store, _Stripped(), run_id=second_run_id)
    finally:
        client.__exit__(None, None, None)

    assert view.prior_run_id == first_run_id, view.prior_run_id
    assert view.voters == 0, f"不可归因的判词不得计票：{view.votes}"
    assert view.advisory is None, "读不到可归因判词时不得编出一个结论"
    assert "no attributable" in view.reason, view.reason
    assert str(first_run_id) in view.reason, "理由必须点名是哪一轮读不到"
    assert view.empty is True, "⇒ 提示词里没有那一段（不留空壳）"
