"""GOAL-20261009-042 EC-03 判据：**记忆时效门**（研究循环按 `disposition` 改变行为）。

靶子：`RunChainCall.memory_validity_gate` 声明后，本步按**上一步读面给的 `disposition`**
分派 —— 三态**互不混用**、逐条点名，且**未声明门 ⇒ 既有行为逐字节不变**：

| 读面处置 | 本步做什么 | 可读通道 |
| --- | --- | --- |
| `SKIP`（已过期） | **不执行**工具（provider **零调用**） | `CapabilityStepOutcome.skipped` |
| `ANNOTATE`（待复核） | **照常执行** | `CapabilityStepOutcome.annotations`（**不同通道**） |
| `USE` | 照用 | 两条通道都**空**（不得凭空加标记） |

**两向反证**：该跳过时**必跳过**（provider 不被调用）；不该跳过时**不跳**（待复核照常
执行、只走标注通道）；**未声明门** ⇒ 即便读面带 `SKIP` 也照常执行（缺省逐字节不变）；
**fail closed**：`memories` 缺字段 / 取值未知 ⇒ 点名，不得被读成「没有记忆」。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from packages.application.ports.errors import InvalidInputError
from packages.application.run_orchestration.phase_capabilities import (
    CapabilityStepOutcome,
    RunChainCall,
)
from packages.application.run_orchestration.phase_capability_triggers import (
    MEMORY_ANNOTATE,
    MEMORY_SKIP,
    MEMORY_SUPERSEDED,
    MEMORY_USE,
    memory_gate_verdict,
    memory_step_gate,
)

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

_SOURCE = "test:goal042-gate"
_EPOCH = "2026-10-09T00:00:00+00:00"


def _row(memory_id: str, disposition: str) -> dict[str, Any]:
    """读面形态的一行记忆（与 `memory_read` 的产物同形）。"""
    validity = {
        MEMORY_SKIP: "EXPIRED",
        MEMORY_ANNOTATE: "REVIEW_DUE",
        MEMORY_USE: None,
        # GOAL-20261010-050 EC-03：**已取代**与**已过期**处置相同、**理由不同**。
        MEMORY_SUPERSEDED: None,
    }[disposition]
    return {
        "memory_id": memory_id,
        "disposition": disposition,
        "validity": validity,
        "reason": f"{memory_id} 的理由",
    }


def _payload(*rows: dict[str, Any]) -> dict[str, Any]:
    return {"now": _EPOCH, "memory_count": len(rows), "memories": list(rows)}


def _first(payload: Mapping[str, Any]) -> dict[str, Any]:
    """载荷里的第一条记忆（类型化取值 —— 读面契约里 `memories` 是对象数组）。"""
    rows = payload["memories"]
    assert isinstance(rows, list) and rows, rows
    item = rows[0]
    assert isinstance(item, dict), item
    return dict(item)


class TestTheGateIsTriStateAndNeverMixed:
    """三态 → 三处置：**互不混用**（按 `disposition` 的**值**分派，不靠措辞）。"""

    def test_an_expired_memory_skips_the_step_and_names_every_record(self) -> None:
        verdict, notes = memory_gate_verdict(_payload(_row("m-old", MEMORY_SKIP)), "memory_read")
        assert verdict == MEMORY_SKIP, verdict
        assert len(notes) == 1, notes
        assert "m-old" in notes[0] and "EXPIRED" in notes[0], ("逐条点名 id 与状态", notes)
        assert "m-old 的理由" in notes[0], ("逐条带理由", notes)

    def test_a_record_due_for_review_is_annotated_not_skipped(self) -> None:
        verdict, notes = memory_gate_verdict(
            _payload(_row("m-due", MEMORY_ANNOTATE)), "memory_read"
        )
        assert verdict == MEMORY_ANNOTATE, ("待复核不是过期：不得落 SKIP", verdict)
        assert verdict != MEMORY_SKIP
        assert "m-due" in notes[0] and "REVIEW_DUE" in notes[0], notes

    def test_all_usable_records_leave_both_channels_empty(self) -> None:
        verdict, notes = memory_gate_verdict(_payload(_row("m-ok", MEMORY_USE)), "memory_read")
        assert verdict == MEMORY_USE, verdict
        assert notes == (), ("照用不得凭空加标记", notes)

    def test_an_expiry_dominates_a_due_review(self) -> None:
        verdict, notes = memory_gate_verdict(
            _payload(_row("m-old", MEMORY_SKIP), _row("m-due", MEMORY_ANNOTATE)), "memory_read"
        )
        assert verdict == MEMORY_SKIP, ("过期是更强的状态", verdict)
        assert "m-old" in notes[0], notes

    def test_an_empty_read_result_is_use_not_skip(self) -> None:
        """**反证（不该红时不红）**：0 条记忆 ⇒ `USE`（不得当成「全部过期」）。"""
        verdict, notes = memory_gate_verdict(_payload(), "memory_read")
        assert verdict == MEMORY_USE, verdict
        assert notes == (), notes


class TestTheGateFailsClosedAndNamesWhatIsMissing:
    """缺字段 / 形态不符 / 取值未知 ⇒ **点名**（不得静默降级成「没有记忆」）。"""

    def test_a_missing_memories_list_is_named(self) -> None:
        with pytest.raises(InvalidInputError, match="carries no 'memories' list"):
            memory_gate_verdict({"run_id": "r-1"}, "memory_read")

    def test_a_non_object_entry_is_named(self) -> None:
        with pytest.raises(InvalidInputError, match="is not an object"):
            memory_gate_verdict(_payload("not-an-object"), "memory_read")  # type: ignore[arg-type]

    def test_an_unknown_disposition_is_named(self) -> None:
        row = {"memory_id": "m-x", "disposition": "MAYBE", "validity": None, "reason": "?"}
        with pytest.raises(InvalidInputError, match="unknown disposition"):
            memory_gate_verdict(_payload(row), "memory_read")


class TestTheDeclarationDefaultKeepsTheOldBehaviour:
    """**未声明门 ⇒ 逐字节不变**：即便读面带 `SKIP`，本步也**照常执行**、两通道都空。"""

    def test_without_the_declaration_nothing_is_skipped_or_annotated(self) -> None:
        call = RunChainCall(provider_id="p", tool_id="memory_read", capability="memory.read")
        assert call.memory_validity_gate is False, call
        decision = memory_step_gate(call, _payload(_row("m-old", MEMORY_SKIP)))
        assert decision.skip is False, ("未声明门 ⇒ 不跳过", decision)
        assert decision.notes == (), ("未声明门 ⇒ 不产生任何标注", decision)

    def test_with_the_declaration_the_verdict_drives_the_step(self) -> None:
        call = RunChainCall(
            provider_id="p",
            tool_id="memory_read",
            capability="memory.read",
            memory_validity_gate=True,
        )
        assert memory_step_gate(call, _payload(_row("m-old", MEMORY_SKIP))).skip is True
        due = memory_step_gate(call, _payload(_row("m-due", MEMORY_ANNOTATE)))
        assert due.skip is False and due.notes, ("待复核 ⇒ 不跳过且带标注", due)


def test_the_declaration_defaults_to_false_so_legacy_calls_are_unchanged() -> None:
    """既有声明的**形态不变**：不传该字段 ⇒ `False`（缺省路径逐字节不变）。"""
    call = RunChainCall(provider_id="p", tool_id="t", capability="c")
    assert call.memory_validity_gate is False, call


def test_the_step_outcome_carries_both_channels_separately() -> None:
    """两条通道**互不混用**：`skipped` 与 `annotations` 各自独立携带。"""
    outcome = CapabilityStepOutcome(
        skipped=("tool t skipped: expired m-old",),
        annotations=("tool t annotated: m-due",),
    )
    assert outcome.skipped and outcome.annotations, outcome
    assert outcome.skipped != outcome.annotations, outcome


class TestASupersededMemoryStopsTheStepWithItsOwnReason:
    """GOAL-20261010-050 EC-03：**已取代**进消费端 —— 处置同「跳过」，**理由各自点名**。

    这是本 GOAL 的**消费面**判据：只把新态写进读面载荷**不算**「被用上」——
    研究循环的时效门必须**真的按它分派**，且读者能看出这一步是「过期」还是「被取代」。
    """

    def test_a_superseded_record_skips_the_step(self) -> None:
        """被取代 ⇒ 本步**不执行**（与已过期同一处置）。"""
        call = RunChainCall(
            provider_id="p",
            tool_id="memory_read",
            capability="memory.read",
            memory_validity_gate=True,
        )
        decision = memory_step_gate(call, _payload(_row("m-old", MEMORY_SUPERSEDED)))
        assert decision.skip is True, decision

    def test_the_two_reasons_are_named_separately(self) -> None:
        """**两因不混用**：同时有过期与被取代 ⇒ 判词**分别点名**（不共用一句、不并成一格）。"""
        call = RunChainCall(
            provider_id="p",
            tool_id="memory_read",
            capability="memory.read",
            memory_validity_gate=True,
        )
        decision = memory_step_gate(
            call,
            _payload(_row("m-exp", MEMORY_SKIP), _row("m-sup", MEMORY_SUPERSEDED)),
        )
        joined = " ".join(decision.notes)
        assert "expired" in joined and "superseded" in joined, (
            "两个理由都要点名（否则读者分不出是哪一种不适用）",
            decision.notes,
        )
        assert "m-exp" in joined and "m-sup" in joined, decision.notes

    def test_a_superseded_only_step_names_that_reason(self) -> None:
        """只有被取代 ⇒ 判词**只**报那一因（**不得**凭空说「过期」）。"""
        call = RunChainCall(
            provider_id="p",
            tool_id="memory_read",
            capability="memory.read",
            memory_validity_gate=True,
        )
        decision = memory_step_gate(call, _payload(_row("m-sup", MEMORY_SUPERSEDED)))
        joined = " ".join(decision.notes)
        assert "superseded" in joined, decision.notes
        assert "expired" not in joined, ("不得凭空说「过期」", decision.notes)
