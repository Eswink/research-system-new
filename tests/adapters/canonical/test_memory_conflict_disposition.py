"""GOAL-20261011-051 EC-02 判据：**带着未消解的冲突**是第五种可判定的处置。

**为什么单列**：规模门对 `tests/**` 同样生效（单文件 ≤ 450 行），而
`test_memory_read_dispositions.py` 承载序 10/13/17/18 四轮的读面判据 ⇒ 本轮的冲突面单列
（与全仓既有的「行为独立即单列」手法一致）。

**靶子**：`contradictions` **可声明、可落库、读面逐条披露**（序 13），但**处置面看不见它** ——
实跑（修前）：一条声明冲突的记录与一条干净记录**处置完全相同**（都 `USE`），冲突只出现在
`reason` 的**后缀**里；消费端只按 `disposition` 分派 ⇒ 有冲突的那条**不落任何一组**。

**四向反证**：① 有冲突必**不**报 `USE`（且点名 id）；② 无冲突**不得**凭空说有冲突；
③ 五态常量两两不等（分派面分得开）；④ 并存时**优先级固定**（已取代 > 已过期 > 有冲突）。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from adapters.canonical.memory_read import (
    DISPOSITION_ANNOTATE,
    DISPOSITION_CONFLICTED,
    DISPOSITION_SKIP,
    DISPOSITION_SUPERSEDED,
    DISPOSITION_USE,
    memory_read,
)
from adapters.fakes import FakeMemoryStore
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal

_EPOCH = datetime(2026, 10, 11, tzinfo=timezone.utc)


def _moment(days: int) -> str:
    return (_EPOCH + timedelta(days=days)).isoformat()


def _record(
    memory_id: str,
    *,
    expires_at: datetime | None = None,
    review_after: datetime | None = None,
    supersedes: list[str] | None = None,
    contradictions: list[str] | None = None,
) -> MemoryWriteProposal:
    """一条**待提交**的记忆（经既有 §8 写入门链落到 store ⇒ 与产品路径同一形态）。"""
    return MemoryWriteProposal(
        id=memory_id,
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content=f"内容 {memory_id}",
        provenance="test:goal042",
        confidence=0.9,
        scope="project",
        supersedes=list(supersedes or ()),
        contradictions=list(contradictions or ()),
        expires_at=Timestamp(expires_at) if expires_at is not None else None,
        review_after=Timestamp(review_after) if review_after is not None else None,
    )


def _store(*records: MemoryWriteProposal) -> FakeMemoryStore:
    """把记录**真的提交**进 store（deny-by-default 的来源先登记 —— 与产品路径同一形态）。"""
    store = FakeMemoryStore(allowed_sources=("test:goal042",))
    for record in records:
        store.commit(record)
    return store


def _first(payload: dict[str, object]) -> dict[str, object]:
    """读面载荷里的第一条记忆（类型化取值：读面契约里 `memories` 是对象数组）。"""
    rows = payload["memories"]
    assert isinstance(rows, list) and rows, rows
    item = rows[0]
    assert isinstance(item, dict), item
    return item


def _rows_by_id(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    rows = payload["memories"]
    assert isinstance(rows, list), rows
    out: dict[str, dict[str, object]] = {}
    for item in rows:
        assert isinstance(item, dict), item
        out[str(item["memory_id"])] = item
    return out


class TestAConflictingRecordIsNoLongerPlainlyUsed:
    """GOAL-20261011-051 EC-02：**带着未消解的冲突**是第五种可判定的处置。

    **靶子**：`contradictions` **可声明、可落库、读面逐条披露**（序 13），但**处置面看不见它** ——
    实跑：一条声明冲突的记录与一条干净记录**处置完全相同**（都 `USE`），冲突只出现在 `reason`
    的**后缀**里；消费端只按 `disposition` 分派 ⇒ 有冲突的那条**不落任何一组**（被照用放行）。

    本类钉住四件事：① 处置**不再是** `USE`；② 判词**点名**冲突 id 与「未自动消解」；
    ③ 与既有四态**可区分**（五个常量互不相等，且理由不同）；④ **无冲突 ⇒ 逐字不变**。
    """

    def test_a_conflicting_record_is_flagged_not_plainly_used(self) -> None:
        """有冲突 ⇒ `CONFLICTED`（**不是** `USE`），理由**点名**冲突 id 与「未自动消解」。"""
        payload = memory_read(
            _store(_record("m-c", contradictions=["memory:earlier-claim"])),
            {"now": _moment(0)},
        )
        row = _first(payload)
        assert row["disposition"] == DISPOSITION_CONFLICTED, row
        assert row["disposition"] != DISPOSITION_USE, "带着未消解冲突的记录不得被当成照用"
        reason = str(row["reason"])
        assert "memory:earlier-claim" in reason, ("必须点名冲突的 id", reason)
        assert "未自动消解" in reason, ("必须说明未自动消解（不越权替人判断）", reason)

    def test_no_conflict_keeps_the_previous_answer_verbatim(self) -> None:
        """**反证臂**：无冲突 ⇒ 处置 `USE`、理由**逐字**与改动前相同（且载荷不带冲突味）。"""
        payload = memory_read(_store(_record("m-clean")), {"now": _moment(0)})
        row = _first(payload)
        assert row["disposition"] == DISPOSITION_USE, row
        assert row["reason"] == "未声明时效或未到 ⇒ 照用（未声明不得被当成已到期）", row
        assert "冲突" not in str(row["reason"]), ("无冲突不得凭空说有冲突", row)

    def test_the_five_dispositions_are_distinct_constants(self) -> None:
        """**五态互不混用**：五个常量两两不等（否则分派面会把两件事读成同一件）。"""
        values = {
            DISPOSITION_USE,
            DISPOSITION_ANNOTATE,
            DISPOSITION_SKIP,
            DISPOSITION_SUPERSEDED,
            DISPOSITION_CONFLICTED,
        }
        assert len(values) == 5, ("五个处置必须互不相同", sorted(values))

    def test_conflict_and_review_due_are_distinguishable(self) -> None:
        """**同类不同因**：待复核与有冲突**都**要看，但**理由是两回事**（判词分得开）。"""
        due = memory_read(
            _store(_record("m-due", review_after=_EPOCH - timedelta(days=1))), {"now": _moment(0)}
        )
        conflicted = memory_read(
            _store(_record("m-c", contradictions=["m-x"])), {"now": _moment(0)}
        )
        assert _first(due)["disposition"] == DISPOSITION_ANNOTATE, due
        assert _first(conflicted)["disposition"] == DISPOSITION_CONFLICTED, conflicted
        assert "复核" in str(_first(due)["reason"]), _first(due)
        assert "冲突" in str(_first(conflicted)["reason"]), _first(conflicted)

    def test_the_priority_order_is_fixed_and_declared(self) -> None:
        """**并存优先级固定**：已取代 > 已过期 > 有冲突 > 待复核 > 照用（逐条实测）。"""
        # 已取代 + 有冲突 ⇒ 以**取代**为先（一条已被替代的记录，「谁和它冲突」已无实际意义）
        superseded_and_conflicted = memory_read(
            _store(
                _record("m-old", contradictions=["m-y"]),
                _record("m-new", supersedes=["m-old"]),
            ),
            {"now": _moment(0)},
        )
        rows = _rows_by_id(superseded_and_conflicted)
        assert rows["m-old"]["disposition"] == DISPOSITION_SUPERSEDED, rows["m-old"]
        # 已过期 + 有冲突 ⇒ 以**过期**为先（「不参与后续行为」比「要人看」更彻底），但两者都点名
        expired_and_conflicted = memory_read(
            _store(_record("m-e", expires_at=_EPOCH - timedelta(days=1), contradictions=["m-z"])),
            {"now": _moment(0)},
        )
        row = _first(expired_and_conflicted)
        assert row["disposition"] == DISPOSITION_SKIP, row
        assert "已过" in str(row["reason"]) and "冲突" in str(row["reason"]), (
            "两个理由都要点名（读者要能看全）",
            row,
        )
