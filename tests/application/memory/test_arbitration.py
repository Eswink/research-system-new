"""GOAL-20261111-110 EC-01/EC-03（域层）：**仲裁三值闭集**与它的可判依据。

**判什么**：

1. **缺省 = `REQUIRE_HUMAN`**（§9 同姿态）：不声明策略 ⇒ 点名「没有策略」，不产出 winner；
   **自动策略必须显式声明**（`DeclaredPolicy`，且 `REQUIRE_HUMAN` 不是可声明的策略——
   它是没有策略时的结果）；
2. 三策略正例各一条，**依据句机器可读**（点名两边的决定性字段值，不是「某模型认为」）；
3. **反证**（EC-03 的两条）：置信度低于声明阈值 ⇒ 拒自动消解并点名；
   同一对**不能重复消解**由域层已拒（`store.resolve_conflict`）——本文件用真 store
   按压一次，证明域层那道门在仲裁链路的下游仍然咬得住；
4. **可判性的四条缝各点名**：`valid_from` 缺席 / 平手、信任标签缺席 / 越序 / 平手；
5. `TrustLabel` 枚举**逐字未动**（判据读枚举成员集，改枚举即红——`escalation_triggers`）。
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from packages.application.memory.arbitration import (
    AUTO_STRATEGIES,
    OUTCOMES,
    TRUST_RANKING,
    ArbitrationVerdict,
    DeclaredPolicy,
    arbitrate,
)
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType, TrustLabel
from packages.domain.memory import MemoryRecord

_OLDER = Timestamp(value=datetime(2026, 11, 1, tzinfo=timezone.utc))
_NEWER = Timestamp(value=datetime(2026, 11, 10, tzinfo=timezone.utc))


def _record(
    memory_id: str,
    *,
    confidence: float = 0.9,
    valid_from: Timestamp | None = None,
) -> MemoryRecord:
    return MemoryRecord(
        id=memory_id,
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content=f"content of {memory_id}",
        provenance="arbitration-criterion",
        confidence=confidence,
        valid_from=valid_from,
    )


def _pair() -> tuple[MemoryRecord, MemoryRecord]:
    return _record("mem-a", valid_from=_OLDER), _record("mem-b", valid_from=_NEWER)


def test_the_default_is_require_human_by_name() -> None:
    """**缺省**：不声明策略 ⇒ `REQUIRE_HUMAN`，点名「没有策略」，无 winner。"""
    left, right = _pair()
    verdict = arbitrate(left, right)
    assert verdict.outcome == "REQUIRE_HUMAN"
    assert verdict.winner_id is None
    assert "policy" in verdict.missing
    assert "policy declared" in verdict.basis or "no arbitration policy" in verdict.basis


def test_declaring_require_human_is_not_a_strategy() -> None:
    """`REQUIRE_HUMAN` 是**结果**不是策略：声明它必须被点名拒绝（默认语义不可被架空）。"""
    left, right = _pair()
    with pytest.raises(InvalidInputError, match="REQUIRE_HUMAN is the default"):
        DeclaredPolicy(strategy="REQUIRE_HUMAN", min_confidence=0.5)
    with pytest.raises(InvalidInputError, match="declared strategy must be one of"):
        DeclaredPolicy(strategy="SOMETHING_ELSE", min_confidence=0.5)


def test_newer_wins_names_both_stamps() -> None:
    """正例：`NEWER_WINS` 留新者，依据句**点名两个时间戳**（可核验，不是断言）。"""
    left, right = _pair()
    verdict = arbitrate(
        left,
        right,
        policy=DeclaredPolicy(strategy="NEWER_WINS", min_confidence=0.6),
    )
    assert verdict.outcome == "NEWER_WINS"
    assert verdict.winner_id == "mem-b"
    assert "2026-11-10" in verdict.basis and "2026-11-01" in verdict.basis and ">" in verdict.basis


def test_newer_wins_without_stamps_is_named() -> None:
    """反证：任一边 `valid_from` 缺席 ⇒ `REQUIRE_HUMAN` 并点名缺的是谁（不猜）。"""
    left, right = _pair()
    verdict = arbitrate(
        replace(right, valid_from=None),
        left,
        policy=DeclaredPolicy(strategy="NEWER_WINS", min_confidence=0.6),
    )
    assert verdict.outcome == "REQUIRE_HUMAN"
    assert verdict.winner_id is None
    assert any("valid_from" in item and "mem-b" in item for item in verdict.missing)


def test_a_tie_is_not_resolved_automatically() -> None:
    """反证：`valid_from` 平手 ⇒ `REQUIRE_HUMAN`（没有依据就是没有依据）。"""
    left, right = _pair()
    verdict = arbitrate(
        left,
        replace(right, valid_from=_OLDER),
        policy=DeclaredPolicy(strategy="NEWER_WINS", min_confidence=0.6),
    )
    assert verdict.outcome == "REQUIRE_HUMAN"
    assert any("tie" in item for item in verdict.missing)


def test_source_trust_wins_names_both_labels() -> None:
    """正例：`SOURCE_TRUST_WINS` 留高者，依据句点名两个标签。"""
    left, right = _pair()
    verdict = arbitrate(
        left,
        right,
        policy=DeclaredPolicy(strategy="SOURCE_TRUST_WINS", min_confidence=0.6),
        trust_labels={"mem-a": "GENERATED", "mem-b": "VERIFIED_SOURCE"},
    )
    assert verdict.outcome == "SOURCE_TRUST_WINS"
    assert verdict.winner_id == "mem-b"
    assert "VERIFIED_SOURCE" in verdict.basis and "GENERATED" in verdict.basis


def test_missing_or_unknown_labels_are_named() -> None:
    """反证：标签缺席 / 越出声明的序 ⇒ `REQUIRE_HUMAN` 点名（不猜）。"""
    left, right = _pair()
    policy = DeclaredPolicy(strategy="SOURCE_TRUST_WINS", min_confidence=0.6)
    absent = arbitrate(left, right, policy=policy)
    assert absent.outcome == "REQUIRE_HUMAN"
    assert any("trust_label" in item and "mem-a" in item for item in absent.missing)

    unknown = arbitrate(
        left,
        right,
        policy=policy,
        trust_labels={"mem-a": "MADE_UP_LABEL", "mem-b": "VERIFIED_SOURCE"},
    )
    assert unknown.outcome == "REQUIRE_HUMAN"
    assert any("MADE_UP_LABEL" in item for item in unknown.missing)


def test_a_trust_tie_is_not_resolved_automatically() -> None:
    """反证：标签平手 ⇒ `REQUIRE_HUMAN`。"""
    left, right = _pair()
    verdict = arbitrate(
        left,
        right,
        policy=DeclaredPolicy(strategy="SOURCE_TRUST_WINS", min_confidence=0.6),
        trust_labels={"mem-a": "GENERATED", "mem-b": "GENERATED"},
    )
    assert verdict.outcome == "REQUIRE_HUMAN"
    assert any("tie" in item for item in verdict.missing)


def test_confidence_below_the_declared_threshold_refuses_automation() -> None:
    """**反证（EC-03）**：低于声明阈值 ⇒ 拒自动消解并**点名**哪条记录低了多少。"""
    left, right = _pair()
    low = _record("mem-low", confidence=0.4, valid_from=_NEWER)
    verdict = arbitrate(
        low,
        right,
        policy=DeclaredPolicy(strategy="NEWER_WINS", min_confidence=0.6),
    )
    assert verdict.outcome == "REQUIRE_HUMAN"
    assert verdict.winner_id is None
    assert any("0.4" in item and "mem-low" in item and "0.6" in item for item in verdict.missing)


def test_a_declared_policy_with_no_threshold_is_refused() -> None:
    """声明自动策略必须带阈值（`min_confidence` 必填）——无凭据的口子开不出来。"""
    with pytest.raises((InvalidInputError, TypeError)):
        DeclaredPolicy(strategy="NEWER_WINS")  # type: ignore[call-arg]


def test_the_domain_still_refuses_a_second_resolution() -> None:
    """**反证（EC-03）**：同一对不能重复消解——域层那道门在仲裁链路下游仍咬得住。"""
    from datetime import datetime, timezone

    from adapters.fakes.memory_store import FakeMemoryStore
    from packages.application.memory.lifecycle import MemoryLifecycleDeps, resolve_memory_conflict

    store = FakeMemoryStore()
    # 直接摆两条互相指认的记录（绕过门链不是本轮的事——判据判的是「重复消解」）。
    from packages.domain.enums import MemoryTier, MemoryType  # noqa: PLC0415
    from packages.domain.memory import MemoryRecord  # noqa: PLC0415

    store._records["mem-a"] = MemoryRecord(  # noqa: SLF001 - 判据摆件
        id="mem-a",
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content="a",
        provenance="criterion",
        confidence=0.9,
        contradictions=["mem-b"],
    )
    store._records["mem-b"] = MemoryRecord(  # noqa: SLF001
        id="mem-b",
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content="b",
        provenance="criterion",
        confidence=0.9,
    )
    deps = MemoryLifecycleDeps(store=store, publisher=None)
    now = Timestamp(value=datetime.now(tz=timezone.utc))
    first = resolve_memory_conflict(
        deps, "mem-a", "mem-b", resolved_by="criterion", resolved_at=now
    )
    assert any(item.other_id == "mem-b" for item in first.resolutions)
    with pytest.raises(InvalidInputError, match="already resolved"):
        resolve_memory_conflict(
            deps, "mem-a", "mem-b", resolved_by="criterion-again", resolved_at=now
        )


def test_the_trust_label_enum_is_untouched() -> None:
    """`TrustLabel` 枚举逐字未动（成员集与读序的键集同源；改枚举即红）。"""
    members = {label.value for label in TrustLabel}
    assert members == set(TRUST_RANKING), "TrustLabel 成员与仲裁读序的键必须同源"
    assert len(TRUST_RANKING) == len(set(TRUST_RANKING.values())), "读序不得有并列档位"


def test_the_closed_sets_are_consistent() -> None:
    """闭集自洽：结果集三值、自动策略二值、且后者是前者的真子集。"""
    assert OUTCOMES == {"NEWER_WINS", "SOURCE_TRUST_WINS", "REQUIRE_HUMAN"}
    assert AUTO_STRATEGIES == {"NEWER_WINS", "SOURCE_TRUST_WINS"}
    assert AUTO_STRATEGIES < OUTCOMES


def test_require_human_never_carries_a_winner() -> None:
    """`REQUIRE_HUMAN` 与 winner 互斥（域不变量，构造即拒）。"""
    with pytest.raises(InvalidInputError, match="must not name a winner"):
        ArbitrationVerdict(outcome="REQUIRE_HUMAN", winner_id="mem-a", basis="x")
