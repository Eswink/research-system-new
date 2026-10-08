"""GOAL-20261008-037 EC-04 判据：**编排步的 at-least-once + 幂等**（与中断重入）。

口径（AGENTS.md §7）：投递语义只能是 **at-least-once + idempotency + deduplication**；
**不得**宣称「恰好一次」（本文件不断言它，**明确否认**）。

四条各自可判（全部经**既有 HTTP 面**）：

1. **同键重放**：同一个 `Idempotency-Key` 重放推进 ⇒ 响应**逐字节相同**、程序内 run 数
   不变、决策数不变（不重复副作用）—— 这是 at-least-once 之上的幂等面。
2. **不同键 = 新的推进**：换一个键重放 ⇒ 按事实再判一次（此处第 1 轮已 `SUCCEEDED` 且
   判词命中规则 ⇒ `CONTINUE`，起第 2 轮）—— 幂等**不等于**拒绝新事实。
3. **崩溃窗口（DEDUP）**：上一条 `CONTINUE` 认领的 run **没有落库** ⇒ 再推进必须落
   `DEDUP` 且**不产生第二个 run**（点名人工/重试）。
4. **重启重入**：换一个应用实例（同一 canonical 面）⇒ 推进仍能读事实并落决策
   （状态从 canonical 重建，不依赖进程内记忆）。
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

from packages.domain.core import Timestamp
from packages.domain.program import ProgramDecision, ProgramDecisionKind
from services.api.app import create_app
from tests.e2e.cross_run_support import PROTOCOL, cross_run_deps
from tests.e2e.program_advance_support import create_program, read_program

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


def _advance_with(client: TestClient, program_id: str, key: str) -> tuple[int, dict[str, Any]]:
    response = client.post(f"/programs/{program_id}/advance", headers={"Idempotency-Key": key})
    assert response.status_code == 200, response.text
    return response.status_code, dict(response.json())


def test_replaying_the_same_key_is_byte_identical_and_does_not_duplicate() -> None:
    """同键重放：响应逐字节相同 + run 数 / 决策数都不变（不重复副作用）。"""
    deps = cross_run_deps()
    with TestClient(create_app(deps)) as client:
        program = create_program(client, max_runs=3, protocol=PROTOCOL)
        program_id = str(program["id"])
        key = f"advance-{uuid.uuid4()}"
        _status, first = _advance_with(client, program_id, key)
        after_first = read_program(client, program_id)
        _status, replay = _advance_with(client, program_id, key)
        after_replay = read_program(client, program_id)
        assert replay == first, "同键重放必须返回同一次推进的结果"
        assert after_replay["run_count"] == after_first["run_count"] == 1
        assert len(after_replay["decisions"]) == len(after_first["decisions"]) == 1


def test_a_different_key_advances_on_the_new_facts() -> None:
    """不同键 = 新的推进（幂等不等于拒绝新事实）：第 1 轮判过 ⇒ 起第 2 轮。"""
    deps = cross_run_deps()
    with TestClient(create_app(deps)) as client:
        program = create_program(client, max_runs=3, protocol=PROTOCOL)
        program_id = str(program["id"])
        _status, first = _advance_with(client, program_id, f"a-{uuid.uuid4()}")
        _status, second = _advance_with(client, program_id, f"b-{uuid.uuid4()}")
        assert first["decision"]["kind"] == "START"
        assert second["decision"]["kind"] == "CONTINUE"
        assert second["started_run_id"] != first["started_run_id"]
        assert read_program(client, program_id)["run_count"] == 2


def test_the_crash_window_yields_dedup_without_a_second_run() -> None:
    """崩溃窗口：认领的 run 未落库 ⇒ `DEDUP`，**不产生第二个 run**（点名人工/重试）。"""
    deps = cross_run_deps()
    with TestClient(create_app(deps)) as client:
        program = create_program(client, max_runs=3, protocol=PROTOCOL)
        program_id = str(program["id"])
        _status, first = _advance_with(client, program_id, f"a-{uuid.uuid4()}")
        first_run_id = str(first["started_run_id"])
        # 手工制造「决策已落、run 未落库」的形态（等价于启动面返回后进程崩了）。
        store = deps.program_store
        assert store is not None
        ghost = str(uuid.uuid4())
        store.record_decision(
            ProgramDecision(
                program_id=program_id,
                after_index=1,
                kind=ProgramDecisionKind.CONTINUE,
                reason="（测试预置）上一条沿用了真实形态的 CONTINUE",
                cited_run_id=ghost,
                cited_facts=("verdict PASS",),
                decided_at=Timestamp.now(),
            )
        )
        _status, result = _advance_with(client, program_id, f"c-{uuid.uuid4()}")
        assert result["decision"]["kind"] == "DEDUP", result
        assert result["decision"]["cited_run_id"] == ghost
        assert result["started_run_id"] is None
        detail = read_program(client, program_id)
        assert detail["run_count"] == 1
        assert [row["run_id"] for row in detail["runs"]] == [first_run_id]


def test_a_restarted_process_rebuilds_from_canonical_and_does_not_repeat() -> None:
    """重启重入：换一个应用实例（同一 canonical 面）⇒ 仍能读事实、落决策、不重复副作用。"""
    deps = cross_run_deps()
    with TestClient(create_app(deps)) as client:
        program = create_program(client, max_runs=3, protocol=PROTOCOL)
        program_id = str(program["id"])
        _status, first = _advance_with(client, program_id, f"a-{uuid.uuid4()}")
    # 「重启」：新应用实例（同一 deps ⇒ 同一 canonical 面；进程内记忆不参与判定）。
    with TestClient(create_app(deps)) as restarted:
        detail = read_program(restarted, program_id)
        assert detail["run_count"] == 1, "程序状态必须从 canonical 读出来（不靠进程内记忆）"
        _status, second = _advance_with(restarted, program_id, f"b-{uuid.uuid4()}")
        assert second["decision"]["kind"] == "CONTINUE"
        assert second["started_run_id"] != first["started_run_id"]
        assert read_program(restarted, program_id)["run_count"] == 2


def test_the_wording_stays_at_least_once_plus_idempotency_and_dedup() -> None:
    """口径守卫：本 GOAL 的记录与本文件只用 at-least-once + 幂等 + 去重的表述。

    **明确否认**「恰好一次」；本文件不断言它，也不把机制说成它。机械面另有既有判据
    （`tests/architecture/python/test_delivery_semantics_wording.py`）负责逐条分类。
    """
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    files = (
        root
        / ".cursor"
        / "plans"
        / "goals"
        / "GOAL-20261008-037-research-program-orchestration-and-cross-run-knowledge.md",
        root / "tests" / "e2e" / "test_program_idempotency_on_the_run_path.py",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "at-least-once" in text, path
        assert "idempotency" in text or "幂等" in text, path
        assert "恰好一次" in text, (
            f"{path} 必须**明写否认**「恰好一次」的口径（只允许 at-least-once + "
            "idempotency + deduplication）"
        )
